/**
 * **Match me** — one person at a time, yes or no, and nothing else.
 *
 * ## Two buttons, and no swipe
 *
 * [#231](https://github.com/Raketa02/Raketa/issues/231) §3 decided against the gesture, and
 * **not on cost**: `RadiusSlider` already drags on the built-in `PanResponder` at zero new
 * dependencies. The argument is that *Show them again* was struck, leaving `PASS_SUPPRESS` at
 * thirty days per account with nothing that reverses one — so a swipe would put the cheapest
 * gesture in the app on the most durable act in the feature, and it would flatten the 1:2
 * ratio the layout uses to say which answer is which. **No `react-native-gesture-handler` and
 * no `react-native-reanimated` are added for this**, and the exit animation stays a *leaving*
 * animation rather than a promise of a drag (`DeckStage`).
 *
 * ## What this screen holds, and what it refuses to
 *
 * The card in flight is **route-local**, which `playSession` refuses to hold by name: *"which
 * card is showing is derived from the dealt list minus the one leaving — never held here"*. So
 * the whole of this screen's memory is three `useState`s — the ids answered in **this** deal,
 * the one on its way out, and whichever card the sheet is open over.
 *
 * `answered` is **keyed by the deal it belongs to** rather than cleared when a new one lands.
 * The two are the same behaviour in the happy case and different in the one that matters: a
 * deal replaced while a card is mid-flight cannot leave a stale id behind, because an id from
 * another `search_id` is *derived* as not applying — the same discipline that lets a line-up's
 * invalidity come off its origin instead of a synchronisation somebody has to remember.
 *
 * ## Answering is optimistic, and a refusal puts the card back
 *
 * §20.5 records [#228](https://github.com/Raketa02/Raketa/issues/228) §12 making both actions
 * optimistic *"so the next card is already there to receive"* the focus that moves onto it. The
 * card therefore leaves on the press rather than on the response — and a **failure returns
 * it**, which is what keeps `retryTarget`'s rule true here: the retry is the control the player
 * already pressed, and it cannot be that control if the person it was about is gone.
 *
 * **Offline is not a failure.** `networkMode: 'online'` holds the write until the connection
 * returns, so the card stays gone and the amber sentence says the act resumes. The deck keeps
 * that pause deliberately: `features/challenges/` alone sets `networkMode: 'always'`, because a
 * challenge's answer window is derived *at send*, and neither a yes nor a pass derives anything
 * from the moment it lands.
 *
 * ## A spent deal deals again, and only a fresh empty deal is an ending
 *
 * The entry deal is the one effect on this screen, guarded on the sport already dealt for —
 * §G6 bug #5 is *"rendering the screen mutates state"*, and the fix it names is to key an act
 * on a moment rather than on a render. Arriving is a moment and changing sport is a moment.
 * Answering the last card of a deal is a third, and it re-deals from the **answer's own
 * handler** for the same reason. `domain/deckHand` is where the three ways of having no card
 * are kept apart, so *the screen runs out of cards long before the pool does* is arithmetic
 * rather than a rule this file remembers.
 *
 * ## What is deliberately not here
 *
 * **A searching latch.** `SearchingLatch` holds a *count* long enough to read
 * ([#269](https://github.com/Raketa02/Raketa/issues/269)); a deal has no count to print and
 * lands on a card, so a floor over it would be a screen held in front of an answer that is
 * already there.
 *
 * **A mode.** The deck has none — `SearchEnvelope.mode` is null exactly here — so it reads the
 * player's own declaration, and the interstitial is what makes that readable.
 *
 * **Anywhere for the prompt sheet to send anybody.** A deal raises questions like a search
 * does and the sheet answers them here now
 * ([#287](https://github.com/Raketa02/Raketa/issues/287)) — but a deal replaces the card in
 * place, so there is no push for the sheet to stand in front of. It stands in front of the
 * card that has already arrived, and closing it is the whole of where anybody goes.
 *
 * **`REFRESH_YOUR_TIMES`.** Its *yes* hands the player back to the week grid and this screen
 * has none, so the deal drops it before it reaches here (`use-cases/dealDeck`). What that
 * leaves is a sheet whose only answer is *carry on*.
 *
 * **A second sheet for a question already answered here.** A deal is not a press — the entry
 * deal is an effect and a spent hand deals again on its own — so a question keyed by the
 * **deal** would be re-asked every ten cards for as long as the condition holds, which on
 * `KEEP_THESE_TIMES` is every deal of the visit. What is remembered instead is the sport and
 * the question (`domain/raisedPrompt`), and answered once is answered for the visit.
 *
 * That memory is what makes the **first unasked** prompt the one to draw rather than the first
 * one: every later list starts with the same leading code, so a screen that took `prompts[0]`
 * and then found it answered would go silent for the rest of the visit with a second question
 * standing behind it. One deal still asks at most one question — the deal that took an answer
 * is held for exactly that, so answering does not promote the next one onto the same card.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { sportLabel, useSkillRatings } from '@/features/onboarding/types';
import { useProfileSurface } from '@/features/player_profile/types';
import { ShellScreen } from '@/features/shell/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { playerName } from '@/shared/formatting/playerName';
import { showToast } from '@/shared/store/toast.store';
import { Button, Note, behindOverlay, moveAccessibilityFocus, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Candidate } from '../domain/candidate';
import { deckStanding } from '../domain/deckHand';
import { findAGameStanding } from '../domain/findAGame';
import {
  NOTHING_ASKED,
  alsoAsked,
  firstUnasked,
  type AskedQuestions,
} from '../domain/raisedPrompt';
import { differsFromProfile } from '../domain/workingWeek';
import { useDealDeck, useOutstandingInterest, useSayNo, useSayYes } from '../hooks/useDeck';
import { usePlayPreferences } from '../store/playPreferences.store';
import { usePlaySession } from '../store/playSession.store';
import type { DeckAsk } from '../use-cases/dealDeck';

import { DeckStage } from './DeckStage';
import { DeclarationInterstitial } from './DeclarationInterstitial';
import { PlaySegment } from './PlaySegment';
import { PromptSheet } from './PromptSheet';
import { SportChips } from './SportChips';
import { DeckCard } from './candidate/DeckCard';
import {
  DEALING_LABEL,
  DEAL_AGAIN_LABEL,
  DECK_FOOTER,
  MATCH_ME_TITLE,
  NOBODY_IN_RANGE_TITLE,
  NO_RATED_SPORT_LINE,
  SEEN_EVERYBODY_TITLE,
  WIDEN_IN_YOU,
  interestToast,
  mutualToast,
  outgoingYeses,
  passedToast,
} from './deckPresentation';
import { playErrorMessage } from './playErrorMessage';
import { poolDescription } from './searchPresentation';
import { WhyFitSheet } from './whyfit/WhyFitSheet';

/**
 * The ids answered in one deal, **with the deal they were answered in**.
 *
 * The pair rather than a bare list: a `search_id` is what makes an answer belong somewhere,
 * and a list on its own would carry ids from a deal that has been replaced.
 */
interface Answered {
  readonly searchId: string;
  readonly playerIds: readonly string[];
}

const NOTHING_ANSWERED: Answered = { searchId: '', playerIds: [] };

export function DeckScreen() {
  const profileSurface = useProfileSurface();
  const ratings = useSkillRatings();
  const interest = useOutstandingInterest();

  const sport = usePlayPreferences((state) => state.sport);
  const chooseSport = usePlayPreferences((state) => state.chooseSport);
  const week = usePlaySession((state) => state.week);

  const deal = useDealDeck();
  const yes = useSayYes();
  const no = useSayNo();

  const [answered, setAnswered] = useState<Answered>(NOTHING_ANSWERED);
  const [leaving, setLeaving] = useState<string | undefined>(undefined);
  const [explaining, setExplaining] = useState<Candidate | undefined>(undefined);

  /**
   * The questions already answered **on this visit**, and the deal that took the last answer.
   *
   * Two facts because they bound two different things, and dropping either one breaks a
   * different case. `asked` is what stops a question being put again by the next deal —
   * `domain/raisedPrompt` is where that key and its reasons live. `answeredOnThisDeal` is what
   * stops the *next* question being put by the same one: answering promotes whatever was
   * behind it, and a second sheet opening onto the first one closing is the stack the response
   * ordering exists to prevent. One deal asks at most one question.
   */
  const [asked, setAsked] = useState<AskedQuestions>(NOTHING_ASKED);
  const [answeredOnThisDeal, setAnsweredOnThisDeal] = useState<string | undefined>(undefined);

  /** The body of the card on screen — where focus goes when the next one arrives (§20.5). */
  const body = useRef<View>(null);
  /** Whether anybody has been answered, so the first card is not taken from the header. */
  const answeredSomebody = useRef(false);

  const profile = profileSurface.data;
  const dealt = deal.data;
  const rated = useMemo(() => (ratings.data ?? []).map((rating) => rating.sport), [ratings.data]);
  const standing = findAGameStanding(rated, sport, profile?.playIntents ?? {});
  const onThisSport = standing.kind === 'no-rated-sport' ? undefined : standing.sport;
  const sportName = onThisSport === undefined ? undefined : sportLabel(onThisSport);

  /**
   * **The ask, or the absence of one** — the one place *may a deal run* is decided.
   *
   * Built as a value rather than spelled once in a guard and once in a `disabled`, which is
   * the shape `mayFinish` and Find a game's own ask exist to refuse.
   */
  const ask: DeckAsk | undefined =
    standing.kind === 'searchable' && profile !== undefined
      ? {
          sport: standing.sport,
          // `undefined` omits the override entirely rather than sending a grid the profile
          // already holds. A deck reached without passing through Find a game has no working
          // copy at all, and that is the same ask: run it on my profile's week.
          sentWeek: week !== undefined && differsFromProfile(week, profile.week) ? week : undefined,
          quotes: { sportName: sportLabel(standing.sport), profileWeek: profile.week },
        }
      : undefined;

  /**
   * Deal, and forget nothing about why.
   *
   * A ref rather than a `useCallback`, so the effect below depends on the **ask** and not on
   * a function identity that changes every render — and so the re-deal fired from an answer
   * reads the current ask rather than the one captured when the card was drawn.
   */
  const dealAgain = useRef<() => void>(() => undefined);
  dealAgain.current = () => {
    if (ask === undefined) return;
    setAnswered(NOTHING_ANSWERED);
    deal.mutate(ask);
  };

  /**
   * Deal on arrival, and again when the sport changes — **once each**.
   *
   * The guard is the sport already dealt for, held in a ref: a re-render caused by the
   * response landing must not read as a new reason to deal. A refusal leaves the guard set,
   * because *nothing in Play retries without the player asking* — the retry is the *Deal
   * again* control under the sentence.
   */
  const dealtFor = useRef<Sport | undefined>(undefined);
  // The **sport**, not the whole ask: the ask is rebuilt on every render — it reads the
  // working copy — and an effect keyed on it would deal once per keystroke on the week grid.
  // What decides whether a deal is owed is which sport this is, and that is a string.
  const askableSport = ask?.sport;
  useEffect(() => {
    if (askableSport === undefined || dealtFor.current === askableSport) return;
    dealtFor.current = askableSport;
    dealAgain.current();
  }, [askableSport]);

  const answeredHere =
    dealt !== undefined && answered.searchId === dealt.envelope.searchId ? answered.playerIds : [];
  const hand = dealt === undefined ? undefined : deckStanding(dealt, answeredHere);
  const showing = hand?.kind === 'card' ? hand.candidate : undefined;

  /**
   * Move focus onto the card that arrived.
   *
   * §E3's first finding is that focus is destroyed on every render and nothing restores it, so
   * a listener who answers a card is dropped at the root with no idea what happened. **Never
   * onto the first card**: arriving on a screen is the platform's own announcement, and taking
   * focus off it would talk over the thing that says where you are.
   */
  useEffect(() => {
    if (!answeredSomebody.current || showing === undefined) return;
    moveAccessibilityFocus(body);
  }, [showing]);

  /**
   * A spent deal deals again, from the act that spent it.
   *
   * Answering the last card is a moment; a render in which the list happens to be empty is
   * not, and dealing from one would put a recording write behind every re-render of a screen
   * whose deal came back short.
   */
  useEffect(() => {
    if (hand?.kind !== 'spent' || deal.isPending) return;
    dealAgain.current();
  }, [hand?.kind, deal.isPending]);

  /**
   * **The question this deal raised, and the beat it is asked in.**
   *
   * One question per deal and never a stack of them, for Find a game's reason: the response
   * orders them in the vocabulary's own order precisely so a client drawing the first one it
   * understands draws the same one twice for the same search. It is the first **unasked** one
   * rather than the first one, which is the half a per-visit memory makes load-bearing — see
   * `firstUnasked`. What reaches here is already filtered to the ones a screen with no week
   * grid can honour (`use-cases/dealDeck`).
   *
   * The beat is **as soon as the deal lands**, because there is no wait to lift and nothing to
   * push: the sheet stands in front of the card that has already arrived, which is the whole of
   * this screen's arrangement.
   */
  const raised =
    dealt === undefined || onThisSport === undefined
      ? undefined
      : firstUnasked(dealt.prompts, onThisSport, asked);
  const question =
    raised === undefined || onThisSport === undefined || dealt === undefined
      ? undefined
      : { raised, sport: onThisSport, deal: dealt.envelope.searchId };
  const asking = question !== undefined && answeredOnThisDeal !== question.deal;

  const outstandingHere = onThisSport === undefined ? 0 : (interest.data?.[onThisSport] ?? 0);
  const readError = profileSurface.error ?? ratings.error;
  const answerPaused = yes.isPaused || no.isPaused || deal.isPaused;
  const answerError = yes.error ?? no.error;

  /** The card has finished leaving: it is gone, the buttons unlock, and the deck advances. */
  const cardLeft = (searchId: string, playerId: string) => {
    setLeaving(undefined);
    answeredSomebody.current = true;
    setAnswered((held) =>
      held.searchId === searchId
        ? { searchId, playerIds: [...held.playerIds, playerId] }
        : { searchId, playerIds: [playerId] },
    );
  };

  /** A refusal puts the card back, so the retry is the button that was pressed. */
  const cardReturned = (playerId: string) => {
    setLeaving(undefined);
    setAnswered((held) => ({
      ...held,
      playerIds: held.playerIds.filter((gone) => gone !== playerId),
    }));
  };

  /**
   * One answer: the card leaves, the write goes, and the toast says which answer it was.
   *
   * The two arms differ in exactly one thing a player can see — **a mutual is told to both
   * sides** — so the sentence is chosen from the response rather than from the press.
   */
  const answer = (said: 'yes' | 'no', candidate: Candidate) => {
    if (leaving !== undefined || dealt === undefined || onThisSport === undefined) return;

    const name = playerName({ kind: 'player', nickname: candidate.card.nickname });
    const card = {
      sport: onThisSport,
      playerId: candidate.playerId,
      searchId: dealt.envelope.searchId,
    };

    setLeaving(candidate.playerId);

    if (said === 'no') {
      no.mutate(card, {
        onSuccess: () => showToast({ message: passedToast(name) }),
        onError: () => cardReturned(candidate.playerId),
      });
      return;
    }

    yes.mutate(card, {
      onSuccess: ({ mutual }) =>
        showToast({
          message: mutual ? mutualToast(name) : interestToast(name),
          tone: mutual ? 'ok' : 'base',
        }),
      onError: () => cardReturned(candidate.playerId),
    });
  };

  return (
    <>
      {/* The sheet is a **sibling** of the screen it covers, never a child: `behindOverlay`
          hides everything inside the element carrying it, and an overlay rendered in there
          would hide itself along with the screen. */}
      <View style={s.root} {...behindOverlay(explaining !== undefined || asking)}>
        <ShellScreen title={MATCH_ME_TITLE}>
          <PlaySegment active="match" outstanding={outstandingHere} />

          {standing.kind === 'no-rated-sport' && ratings.isSuccess ? (
            <Note>{NO_RATED_SPORT_LINE}</Note>
          ) : null}

          {standing.kind === 'no-rated-sport' ? null : (
            <SportChips rated={rated} selected={standing.sport} onChoose={chooseSport} />
          )}

          {/* The same question Find a game asks, because the deck is refused by the same code:
              it has no mode, so it reads the declaration. */}
          {standing.kind === 'undeclared' && sportName !== undefined ? (
            <DeclarationInterstitial sport={standing.sport} sportName={sportName} />
          ) : null}

          {readError !== null ? (
            <Note variant="coral" accessibilityRole="alert">
              {recoveryMessage(readError)}
            </Note>
          ) : null}

          {/* Paused, not failed: `networkMode: 'online'` holds a write rather than refusing
              it, so an offline player would otherwise watch nothing happen. */}
          {answerPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

          {/* The failed answer's sentence sits above the card it is about — which is back on
              screen, because a refusal returns it. */}
          {answerError !== null ? (
            <Note variant="coral" accessibilityRole="alert">
              {playErrorMessage(answerError)}
            </Note>
          ) : null}

          {deal.error !== null ? (
            <View style={s.failure}>
              <Note variant="coral" accessibilityRole="alert">
                {playErrorMessage(deal.error)}
              </Note>
              <Button
                label={DEAL_AGAIN_LABEL}
                variant="secondary"
                onPress={() => dealAgain.current()}
              />
            </View>
          ) : null}

          {deal.isPending && !answerPaused ? (
            <ActivityIndicator accessibilityLabel={DEALING_LABEL} color={theme.color.muted} />
          ) : null}

          {showing === undefined || dealt === undefined ? null : (
            <View style={s.deck}>
              <DeckStage
                // Keyed by the person, so the arrival runs once per card rather than once per
                // render, and the ref below always points at what is on screen.
                key={showing.playerId}
                leaving={leaving === showing.playerId}
                onLeft={() => cardLeft(dealt.envelope.searchId, showing.playerId)}
              >
                <DeckCard
                  candidate={showing}
                  envelope={dealt.envelope}
                  bodyRef={body}
                  answering={leaving !== undefined}
                  onPass={() => answer('no', showing)}
                  onAccept={() => answer('yes', showing)}
                  onWhyFit={() => setExplaining(showing)}
                />
              </DeckStage>

              {DECK_FOOTER.map((line) => (
                <Text key={line} style={s.footer}>
                  {line}
                </Text>
              ))}
            </View>
          )}

          {hand === undefined ||
          hand.kind === 'card' ||
          hand.kind === 'spent' ||
          dealt === undefined ||
          sportName === undefined ? null : (
            <Note
              title={hand.kind === 'seen-everybody' ? SEEN_EVERYBODY_TITLE : NOBODY_IN_RANGE_TITLE}
            >
              <Text style={s.body}>{poolDescription({ ...dealt.pool, sportName })}</Text>
              <Text style={s.body}>{outgoingYeses(outstandingHere)}</Text>
              {/* *Widen in You* survives here and on no other Play surface — and it is gated,
                  because a player already at their own ceiling cannot give what it asks for. */}
              {hand.kind === 'nobody-in-range' && !dealt.envelope.radiusClamp ? (
                <Text style={s.body}>{WIDEN_IN_YOU}</Text>
              ) : null}
            </Note>
          )}
        </ShellScreen>
      </View>

      {/* A **sibling** for `WhyFitSheet`'s reason — a `Modal` presents in its own window, and
          the screen root behind it says so itself. It carries the sport because the decline
          route takes one on every prompt, and only this screen knows which chip was dealt on.

          It stays mounted after it is answered rather than only while it is up: `visible`
          going false is what returns focus to the card, and a sheet that unmounted instead
          would drop a listener at the top of the screen. The re-deal unmounts it, which is
          correct — the question it was asking belonged to a deal nobody is holding.

          `key` is the **question**, so one sheet is one question and the *answered once* guard
          inside it cannot outlive the thing it was asked about. Deliberately not the deal: the
          deal is what decides whether to ask at all, and it is read one line down. */}
      {question === undefined ? null : (
        <PromptSheet
          key={`${question.sport}:${question.raised.prompt}`}
          visible={asking}
          raised={question.raised}
          sport={question.sport}
          returnFocusTo={body}
          onAnswered={() => {
            setAsked((held) => alsoAsked(held, question.sport, question.raised.prompt));
            setAnsweredOnThisDeal(question.deal);
          }}
        />
      )}

      {explaining === undefined || dealt === undefined ? null : (
        <WhyFitSheet
          visible
          onClose={() => setExplaining(undefined)}
          candidate={explaining}
          envelope={dealt.envelope}
          name={playerName({ kind: 'player', nickname: explaining.card.nickname })}
          returnFocusTo={body}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  deck: { gap: theme.space.sm, paddingTop: theme.space.xs },
  footer: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  body: { ...theme.type.tiny, color: theme.color.ink },
  failure: { gap: theme.space.sm },
});

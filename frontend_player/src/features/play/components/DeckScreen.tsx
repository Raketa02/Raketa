/**
 * **Players** — the deck, one person at a time, yes or no, and the whole of the tab.
 *
 * ## A tab of its own, with a toggle and a chip for a header
 *
 * The deck lived under Play as *Match me*, a segment deep, behind a declaration, and it looked
 * like a form. It is the second tab now
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1): Players opens on the deck every time — the shell keeps no per-tab history, and the held
 * deal is what makes that cheap — and **there is no title row**. The header is the *Deck | Radar*
 * toggle, Deck filled, in the header's lead slot, and the **chip** in the right slot — *2 want to
 * play you*, `pool.want_to_play_you` off the deal, and not drawn at nought (§4). The toggle is
 * **component state and not two routes** — Radar is a pane with one muted line until it is built
 * (§9), and a route would make it somewhere the tab could open on. *Try the radar* on the ending
 * flips it.
 *
 * **Sport chips only when there is a choice.** A player rated in one sport sees the mock
 * exactly; rated in two or more gets the row under the toggle, reading and writing the same
 * browsed sport Play's chips do; rated in none sees *Rate a sport first*.
 *
 * **No declaration is read, asked for, or needed** (§2). `POST /deck` scores every deal under
 * one ruler for every viewer, declared or not, so nobody is asked to declare fun or competitive
 * on Players, and the intent term stands down on every card as the surface's own gap.
 *
 * ## A swipe is an answer, and the buttons remain the path
 *
 * The card under the thumb drags right for *Let's play* and left for *Not today*; the stamps
 * fade in with the drag and are full at the threshold, past which a release commits (§3). That
 * is `DeckStage`'s, on the responder the app already drags with. What this screen owns is the
 * **decision**: the stage asks `onAnswer(said)` on a committed release, and the answer is
 * `taken` — the card flies, the write goes — or `withheld`, which is the one case the client
 * pre-empts the server on: **no yeses to give**, and a card that carries no `inclusion_reason`,
 * settles back with a toast saying the ceiling (`domain/yesBudget`). A liker's card flies
 * whatever the count, because a yes that closes a mutual is never outstanding. The three round
 * buttons below the stage do the same two things and one more — **i** opens the record sheet,
 * as the long press on the card does — and they are never removed: a screen reader consumes the
 * drag, so the buttons are the accessible path.
 *
 * **The stamp and the card leaving are the feedback.** The pass toast and the one-sided yes
 * toast retire; what survives of them is the spoken result, announced for every answer, and
 * the one toast left is a mutual naming no chat. A mutual naming a challenge is the yes screen,
 * pushed by the mutation (`hooks/useDeck`).
 *
 * ## What this screen holds, and what it refuses to
 *
 * The card in flight is **route-local**, which `playSession` refuses to hold by name: *"which
 * card is showing is derived from the dealt list minus the one leaving — never held here"*. So
 * the whole of this screen's memory is four `useState`s — which pane the toggle is on, the card
 * on its way out, whichever card the record sheet is open over, and whichever the Fit sheet is.
 *
 * **The ids answered are not among them.** They belong to the deal rather than to the screen,
 * and the deal outlives the screen (`hooks/useDeck`), so a list held here would put every
 * answered card back on screen the moment the route remounted. Held inside the deal, an answer
 * cannot outlive the deal it was given on **by construction**.
 *
 * ## The counter is true, and the next hand is asked for at two
 *
 * *8 left · 12 yeses to give* floats over the card's foot: `remaining + unanswered` off the deal
 * and `cap − outstanding` off the interest read, both counting down as the player answers (§5).
 * When two unanswered cards remain the next hand is asked for and **appended** to the held deal,
 * so the two cards behind the top one are always real people and the join is invisible. A hand
 * answered out with nothing appended — the pool said nobody was left, or the ask failed — deals
 * again on its own, and only a hand that comes back **empty** is an ending. Both are effects on
 * a hand *becoming* short rather than on a render that finds it so (§G6 bug #5's rule), and
 * neither fires while a deal is in flight or a refusal is standing: nothing in Play retries
 * without the player asking, and the retry is *Deal again* under the sentence.
 *
 * ## Answering is optimistic, and a refusal puts the card back
 *
 * §20.5 records [#228](https://github.com/Raketa02/Raketa/issues/228) §12 making both actions
 * optimistic *"so the next card is already there to receive"* the focus that moves onto it. The
 * card therefore leaves on the press rather than on the response — and a **failure returns
 * it**, which is what keeps `retryTarget`'s rule true here: the retry is the control the player
 * already pressed, and it cannot be that control if the person it was about is gone. A `409`
 * at the ceiling returns the card exactly as any refusal does: the pre-empt is a courtesy and the
 * server stays the authority.
 *
 * **Offline is not a failure.** `networkMode: 'online'` holds the write until the connection
 * returns, so the card stays gone and the amber sentence says the act resumes.
 *
 * ## Two endings, and Show them again
 *
 * *You have seen everybody* — people in range, all passed, asked, dealt or cooling off — draws
 * the radius and how long a yes lives, then **Show them again** and **Try the radar**. The reset
 * is `POST /deck/reset` for this sport and then a deal with nothing answered on it
 * (`useResetDeck` resets the held entry rather than appending to it, because a reset re-deals
 * people the deal has recorded as answered). *Nobody in range* keeps its sentence and *widen it
 * in You*, without the reset, which would deal nobody (§5).
 *
 * ## What is deliberately not here
 *
 * **A searching latch.** `SearchingLatch` holds a *count* long enough to read; a deal has no
 * count to print and lands on a card, so a floor over it would be a screen held in front of an
 * answer that is already there.
 *
 * **A mode, a declaration, or a week.** The deck has no mode — `SearchEnvelope.mode` is null
 * exactly here — reads no declaration (§2), and is reached from a tab of its own, so the deal
 * runs on the profile's week (§1) and the screen reads no working copy.
 *
 * **The question a deal raised** is asked over the card that has already arrived, by
 * `PromptSheet`, at most one per deal and never twice in a visit (`domain/raisedPrompt`);
 * `REFRESH_YOUR_TIMES` is dropped before it reaches here, because its *yes* is a week grid this
 * screen does not have (`use-cases/dealDeck`). An appended hand is a new deal and may raise the
 * same question, which the visit's memory answers before the sheet can.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { sportLabel, useSkillRatings } from '@/features/onboarding/types';
import { useProfileSurface } from '@/features/player_profile/types';
import { PlayerRecordSheet } from '@/features/player_record/types';
import { ShellScreen } from '@/features/shell/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { playerName } from '@/shared/formatting/playerName';
import { showToast } from '@/shared/store/toast.store';
import {
  Button,
  Note,
  Segment,
  announce,
  behindOverlay,
  moveAccessibilityFocus,
  theme,
} from '@/shared/ui';

import type { Candidate } from '../domain/candidate';
import {
  cardKey,
  cardsLeft,
  deckStanding,
  isTheCard,
  wantsTheNextHand,
  type AnsweredCard,
  type DealtCard,
} from '../domain/deckHand';
import { sportOnScreen } from '../domain/findAGame';
import { firstUnasked } from '../domain/raisedPrompt';
import { socialTagOverlap } from '../domain/socialTagOverlap';
import { yesWithheld, yesesToGive } from '../domain/yesBudget';
import {
  useDeal,
  useDeckProgress,
  useResetDeck,
  useSayNo,
  useSayYes,
  type DeckQuestion,
} from '../hooks/useDeck';
import { useOutstandingInterest } from '../hooks/useInterest';
import { usePlayPreferences } from '../store/playPreferences.store';
import { usePlaySession } from '../store/playSession.store';

import { DeckAnswers } from './DeckAnswers';
import { DeckEnding } from './DeckEnding';
import { DeckPill } from './DeckPill';
import { DeckStage, type DeckExit, type DragVerdict } from './DeckStage';
import { PromptSheet } from './PromptSheet';
import { SportChips } from './SportChips';
import { DeckCard } from './candidate/DeckCard';
import {
  DEALING_LABEL,
  DEAL_AGAIN_LABEL,
  NO_RATED_SPORT_LINE,
  PANE_LABEL,
  RADAR_LINE,
  deckCounter,
  passedAnnouncement,
  wantToPlayYouChip,
  yesOutcome,
  type PlayersPane,
} from './deckPresentation';
import { CAP_REACHED_SENTENCE, playErrorMessage } from './playErrorMessage';
import { poolDescription } from './searchPresentation';
import { WhyFitSheet } from './whyfit/WhyFitSheet';

/** The card on its way out, and **which answer sent it there** — the direction it leaves in. */
interface Leaving {
  readonly card: AnsweredCard;
  readonly said: DeckExit;
}

export function DeckScreen() {
  const profileSurface = useProfileSurface();
  const ratings = useSkillRatings();
  const interest = useOutstandingInterest();

  const sport = usePlayPreferences((state) => state.sport);
  const chooseSport = usePlayPreferences((state) => state.chooseSport);

  const yes = useSayYes();
  const no = useSayNo();
  const progress = useDeckProgress();

  /** Which pane the toggle is on. Deck on every mount, which is what *opens on Deck* means. */
  const [pane, setPane] = useState<PlayersPane>('deck');
  const [leaving, setLeaving] = useState<Leaving | undefined>(undefined);
  /** The person the record sheet is open over — the **i**, or the long press. */
  const [reading, setReading] = useState<Candidate | undefined>(undefined);
  /** The pairing the Fit sheet is open over — reached from the record's own row. */
  const [explaining, setExplaining] = useState<Candidate | undefined>(undefined);

  /**
   * The questions already answered **on this visit**, and the deal that took the last answer.
   *
   * Two facts because they bound two different things, and dropping either one breaks a
   * different case. `asked` is what stops a question being put again by the next hand —
   * `domain/raisedPrompt` is where that key and its reasons live. `answeredOnThisDeal` is what
   * stops the *next* question being put by the same one: answering promotes whatever was
   * behind it, and a second sheet opening onto the first one closing is the stack the response
   * ordering exists to prevent. One deal asks at most one question.
   */
  const asked = usePlaySession((state) => state.askedQuestions);
  const recordAsked = usePlaySession((state) => state.recordAsked);
  const [answeredOnThisDeal, setAnsweredOnThisDeal] = useState<string | undefined>(undefined);

  /** The body of the card on screen — where focus goes when the next one arrives (§20.5). */
  const body = useRef<View>(null);
  /** Whether anybody has been answered, so the first card is not taken from the header. */
  const answeredSomebody = useRef(false);

  const profile = profileSurface.data;
  const rated = useMemo(() => (ratings.data ?? []).map((rating) => rating.sport), [ratings.data]);
  /**
   * The sport the deck is on: the one the player chose, or the first they are rated in — and
   * `undefined` for a player rated in none, which is the screen's one standing short of a deal.
   * Not `findAGameStanding`: that reads the declaration too, and the deck no longer does.
   */
  const onThisSport = sportOnScreen(rated, sport);
  const sportName = onThisSport === undefined ? undefined : sportLabel(onThisSport);

  /**
   * **The question, or the absence of one** — the one place *may a deal run* is decided.
   *
   * `under` is the half that never reaches the wire: the radius is resolved backend-side, and
   * a deal held without it in its key would answer a widened radius with the deal that ran
   * before it — which is this screen's own *Widen in You* advice being ignored by this screen
   * (`hooks/searchKeys`).
   */
  const dealQuestion: DeckQuestion | undefined =
    onThisSport !== undefined && profile !== undefined
      ? {
          ask: {
            sport: onThisSport,
            quotes: { sportName: sportLabel(onThisSport), profileWeek: profile.week },
          },
          under: { radiusKm: profile.searchRadiusKm },
        }
      : undefined;

  /**
   * **The deal itself — dealt on the first ask for it, and found on every later one.**
   *
   * Keyed by the question (`hooks/useDeck`), asking it twice is the same question and is
   * answered from what is already held; `refetch()` is the next hand, appended.
   */
  const deal = useDeal(dealQuestion);
  const reset = useResetDeck(dealQuestion);
  const dealt = deal.data;
  /** A deal is in flight. `isFetching` rather than `isPending`, which is also *nothing asked*. */
  const dealing = deal.isFetching;
  const dealAgain = () => void deal.refetch();

  const hand = dealt === undefined ? undefined : deckStanding(dealt, dealt.answered);
  const showing = hand?.kind === 'card' ? hand.card : undefined;
  const behind = hand?.kind === 'card' ? hand.behind : [];

  /**
   * Move focus onto the card that arrived.
   *
   * §E3's first finding is that focus is destroyed on every render and nothing restores it, so
   * a listener who answers a card is dropped at the root with no idea what happened. **Never
   * onto the first card**: arriving on a screen is the platform's own announcement, and taking
   * focus off it would talk over the thing that says where you are.
   */
  const showingId = showing?.candidate.playerId;
  useEffect(() => {
    if (!answeredSomebody.current || showingId === undefined) return;
    moveAccessibilityFocus(body);
  }, [showingId]);

  /**
   * The next hand at two, and a spent hand dealt again — from the act that made it so.
   *
   * Answering down to two is a moment, and so is answering the last card; a render in which
   * the list happens to be short is not, and dealing from one would put a recording write
   * behind every re-render of a screen whose deal came back short. A refusal stops both:
   * *nothing in Play retries without the player asking*, and the retry is *Deal again*.
   */
  const { refetch } = deal;
  const wantsMore =
    dealt !== undefined && (hand?.kind === 'spent' || wantsTheNextHand(dealt, dealt.answered));
  useEffect(() => {
    if (!wantsMore || dealing || deal.isError) return;
    void refetch();
  }, [wantsMore, dealing, deal.isError, refetch]);

  /**
   * **The question this deal raised, and the beat it is asked in.**
   *
   * One question per deal and never a stack of them: the response orders them in the
   * vocabulary's own order precisely so a client drawing the first one it understands draws
   * the same one twice for the same search. It is the first **unasked** one rather than the
   * first one, which is the half a per-visit memory makes load-bearing — see `firstUnasked`.
   * The beat is **as soon as the hand lands**: the sheet stands in front of the card that has
   * already arrived, which is the whole of this screen's arrangement.
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

  /** Where this sport stands against its cap — the counter's second half, and the ending's days. */
  const standingHere = onThisSport === undefined ? undefined : interest.data?.[onThisSport];
  const give = standingHere === undefined ? undefined : yesesToGive(standingHere);
  const left = dealt === undefined ? undefined : cardsLeft(dealt, dealt.answered);
  const waiting = dealt?.pool.wantToPlayYou ?? 0;

  const readError = profileSurface.error ?? ratings.error;
  const answerPaused = yes.isPaused || no.isPaused || deal.fetchStatus === 'paused';
  const answerError = yes.error ?? no.error;

  /** The card has finished leaving: it is gone, the buttons unlock, and the deck advances. */
  const cardLeft = (card: DealtCard) => {
    setLeaving(undefined);
    answeredSomebody.current = true;
    progress.cardLeft({ searchId: card.searchId, playerId: card.candidate.playerId });
  };

  /** A refusal puts the card back, so the retry is the button that was pressed. */
  const cardReturned = (card: DealtCard) => {
    setLeaving(undefined);
    progress.cardReturned({ searchId: card.searchId, playerId: card.candidate.playerId });
  };

  /**
   * One answer: taken, or withheld.
   *
   * Taken, the card leaves, the write goes, and the spoken result follows — on the press for a
   * pass, and on the reply for a yes, because **a mutual is told to both sides** and only the
   * reply knows. Withheld is the ceiling: no yeses to give, on a card that carries no
   * `inclusion_reason` — the card settles, a toast says the ceiling, and nothing is sent
   * (`domain/yesBudget`). The same function answers the drag and the buttons, so the two paths
   * cannot disagree about who may fly.
   */
  const answer = (said: DeckExit, card: DealtCard): DragVerdict => {
    if (leaving !== undefined || onThisSport === undefined) return 'withheld';

    const { candidate } = card;
    if (said === 'yes' && yesWithheld({ give, inclusionReason: candidate.inclusionReason })) {
      showToast({ message: CAP_REACHED_SENTENCE });
      return 'withheld';
    }

    const name = playerName({ kind: 'player', nickname: candidate.card.nickname });
    const write = { sport: onThisSport, playerId: candidate.playerId, searchId: card.searchId };

    setLeaving({ card: write, said });

    if (said === 'no') {
      announce(passedAnnouncement(name));
      no.mutate(write, { onError: () => cardReturned(card) });
      return 'taken';
    }

    yes.mutate(write, {
      // Which of the three a yes earned is the copy module's to decide (ADR-0154, ADR-0169 §3):
      // a one-sided yes is spoken, a mutual naming no chat is the one toast left, and a mutual
      // naming a challenge is the yes screen — pushed by the mutation's own success handler
      // (`hooks/useDeck`) and not from here, since this callback is dropped the moment the deck
      // is left and the reply may land after it has been.
      onSuccess: (reply) => {
        const outcome = yesOutcome(name, reply);
        if (outcome.kind === 'announce') announce(outcome.message);
        if (outcome.kind === 'toast') showToast({ message: outcome.message, tone: outcome.tone });
      },
      onError: () => cardReturned(card),
    });
    return 'taken';
  };

  const chip =
    waiting > 0 ? <DeckPill tone="volt">{wantToPlayYouChip(waiting)}</DeckPill> : undefined;

  return (
    <>
      {/* The sheets are **siblings** of the screen they cover, never children: `behindOverlay`
          hides everything inside the element carrying it, and an overlay rendered in there
          would hide itself along with the screen. */}
      <View
        style={s.root}
        {...behindOverlay(explaining !== undefined || reading !== undefined || asking)}
      >
        {/* No title row: the toggle is the header, in its lead slot, and the chip is the
            right slot — drawn at one and above. `flex: 1` on the track is what gives its two
            segments a width to share. `fill`, so the stage takes the height the phone gives
            the deck rather than the height a card's content happens to want. */}
        <ShellScreen
          lead={
            <Segment
              selected={pane}
              options={[
                { key: 'deck', label: PANE_LABEL.deck },
                { key: 'radar', label: PANE_LABEL.radar },
              ]}
              onSelect={setPane}
              style={s.toggle}
            />
          }
          right={pane === 'deck' ? chip : undefined}
          fill={pane === 'deck'}
          action={
            pane === 'deck' && showing !== undefined ? (
              <DeckAnswers
                name={playerName({ kind: 'player', nickname: showing.candidate.card.nickname })}
                onPass={() => answer('no', showing)}
                onAccept={() => answer('yes', showing)}
                onRecord={() => setReading(showing.candidate)}
                answering={leaving !== undefined}
              />
            ) : undefined
          }
        >
          {/* The Radar pane: one muted line in a placeholder tab's shape, until it is built. */}
          {pane === 'radar' ? (
            <Text style={s.radar}>{RADAR_LINE}</Text>
          ) : (
            <>
              {onThisSport === undefined && ratings.isSuccess ? (
                <Note>{NO_RATED_SPORT_LINE}</Note>
              ) : null}

              {/* Only when there is a choice: a player rated in one sport sees the mock
                  exactly, and the row would be one chip saying what the card already says. */}
              {onThisSport !== undefined && rated.length >= 2 ? (
                <SportChips rated={rated} selected={onThisSport} onChoose={chooseSport} />
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
                  <Button label={DEAL_AGAIN_LABEL} variant="secondary" onPress={dealAgain} />
                </View>
              ) : null}

              {dealing && !answerPaused && showing === undefined ? (
                <ActivityIndicator accessibilityLabel={DEALING_LABEL} color={theme.color.muted} />
              ) : null}

              {showing === undefined ||
              dealt === undefined ||
              sportName === undefined ||
              left === undefined ? null : (
                <View style={s.deck}>
                  <DeckStage
                    // Keyed by the card — the person on the deal they came off — so the arrival
                    // runs once per card rather than once per render, the drag starts from
                    // rest, and the ref below always points at what is on screen.
                    key={cardKey(showing)}
                    leaving={
                      leaving !== undefined && isTheCard(leaving.card, showing)
                        ? leaving.said
                        : undefined
                    }
                    onAnswer={(said) => answer(said, showing)}
                    onLeft={() => cardLeft(showing)}
                    behind={behind.map((card) => (
                      <DeckCard
                        key={cardKey(card)}
                        candidate={card.candidate}
                        envelope={dealt.envelope}
                        sportName={sportName}
                      />
                    ))}
                  >
                    <DeckCard
                      candidate={showing.candidate}
                      envelope={dealt.envelope}
                      sportName={sportName}
                      bodyRef={body}
                      onLongPress={() => setReading(showing.candidate)}
                    />
                  </DeckStage>

                  {/* The counter, floating over the card's foot: what is left in the whole
                      pool, and how many yeses there are to give. */}
                  <View style={s.counter} pointerEvents="none">
                    <DeckPill tone="night">
                      {deckCounter({ left, ...(give === undefined ? {} : { give }) })}
                    </DeckPill>
                  </View>
                </View>
              )}

              {hand?.kind === 'seen-everybody' && dealt !== undefined ? (
                <DeckEnding
                  kind="seen-everybody"
                  radiusKm={dealt.pool.radiusKmUsed}
                  {...(standingHere === undefined ? {} : { ttlDays: standingHere.ttlDays })}
                  onShowThemAgain={() => reset.mutate()}
                  onTryTheRadar={() => setPane('radar')}
                  resetting={reset.isPending}
                  resetError={reset.error}
                />
              ) : null}

              {hand?.kind === 'nobody-in-range' &&
              dealt !== undefined &&
              sportName !== undefined ? (
                <DeckEnding
                  kind="nobody-in-range"
                  pool={poolDescription({ ...dealt.pool, sportName })}
                  // *Widen in You* survives here and on no other Play surface — and it is
                  // gated, because a player already at their own ceiling cannot give what it
                  // asks for.
                  mayWiden={!dealt.envelope.radiusClamp}
                />
              ) : null}
            </>
          )}
        </ShellScreen>
      </View>

      {/* A **sibling** for the prompt sheet's reason — a `Modal` presents in its own window, and
          the screen root behind it says so itself. It carries the sport because the decline
          route takes one on every prompt, and only this screen knows which chip was dealt on.

          It stays mounted after it is answered rather than only while it is up: `visible`
          going false is what returns focus to the card, and a sheet that unmounted instead
          would drop a listener at the top of the screen.

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
            recordAsked(question.sport, question.raised.prompt);
            setAnsweredOnThisDeal(question.deal);
          }}
        />
      )}

      {/* `SH.player` — the record sheet, from the **i** and from the long press, with the
          deck's pairing in hand so *why this Fit* lives behind the sheet's fit row (ADR-0169
          §3). It reads no global state: the subject, the sport, the distance, the reader's own
          area and the overlap all arrive as props, exactly as the builder hands them. Taking
          the fit row hands the deck over to `SH.whyfit`: one sheet at a time. */}
      {reading === undefined || dealt === undefined || onThisSport === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={onThisSport}
          {...(reading.distanceKm === undefined ? {} : { distanceKm: reading.distanceKm })}
          {...(dealt.envelope.myAreaCode === undefined
            ? {}
            : { viewerAreaCode: dealt.envelope.myAreaCode })}
          tagOverlap={socialTagOverlap(reading)}
          pairing={{
            fit: reading.fit,
            onExplain: () => {
              setReading(undefined);
              setExplaining(reading);
            },
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
  toggle: { flex: 1 },
  radar: { ...theme.type.tiny, color: theme.color.muted },
  // The stage takes what the page leaves, and the counter hangs off its foot.
  deck: { flex: 1, paddingBottom: theme.size.chip / 2 },
  counter: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
  },
  failure: { gap: theme.space.sm },
});

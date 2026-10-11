/**
 * **A group's Games tab** — the deck, for the sport the page is on and the kind the switch is on
 * ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2; the mechanics §6–§8).
 *
 * ## Four states, in the order the screens list them
 *
 * 1. **No intent for this sport** — the read's segments are empty, and the one-time question
 *    *Competitive / For fun / Either* replaces the deck until it is answered (A2.1) —
 *    `DeclarationInterstitial`, reporting `DECK`; the answer re-reads the deck, which then has
 *    segments.
 * 2. **Nothing to deal in this segment** — the group's starting cards, exactly as built (*Just you
 *    so far*, *3 of 4*, *Nothing picked right now*), which the group page hands in as `empty`: they
 *    are the group's words about its roster, not the deck's.
 * 3. **The weekly cap** — a slim line above the deck, *Your 2 games this week are booked — showing
 *    next week* (Q73), whenever the read names a capped week of the fortnight.
 * 4. **The deck** — the switch, the stage and the three buttons (mock 1).
 *
 * While the first read is on its way the tab says so with the muted spinner; a read that failed
 * says why and offers the retry, unless the failure is one no retry can mend.
 *
 * ## The switch is the page's, corrected by the intent
 *
 * *Competitive · 7 / For fun · 1* (mock 9) is drawn off the read's segments — only the one the
 * player's intent shows, or both for *Either* — and a press is the page's choice (`onChoose`, the
 * group page's game-intent store, which Friends' switch shares). A choice the intent does not show
 * is read as the segment it does (`useGroupDeck`), so the switch never stands on an empty deck the
 * player could not have wanted.
 *
 * ## The stage was Players', and the card is this feature's
 *
 * `DeckStage` — the pan gesture, the stamps, the fly-off, the arrival, the haptic — with the two
 * cards behind now fading as they shrink (Q90), and `DeckAnswers` under it: ✕ is *Not this time*,
 * the ball is *I'm in*, **i** opens the game's details (A2.2). Both were built for Players' deck and
 * came here with the interstitial in #574, since this is the deck that stays. The stamps are this
 * deck's words, *I'M IN* carrying the share whenever the yes charges at once (Q72).
 *
 * ## Answering: the card flies on the press, and the server settles it
 *
 * A swipe or a button sets the card leaving and sends the answer at once — the Players deck's
 * optimism, for its reason: the next card is already there to receive the thumb. **The card in
 * flight is held here** rather than in the read, so a re-read landing mid-flight cannot pull it off
 * the stage; when it has flown it is dropped from the read (`useDropCard`), and the answer settling
 * re-reads the group's decks for the server's order and counts.
 *
 * **A refusal says why, in a toast, and decides where the card goes** (A2.4, `refusalOutcome`): a
 * reason the player can mend — no saved way to pay, the live-yes cap, a read that failed — puts the
 * card back, and the re-read restores one that had already flown; a game that is over, full or no
 * longer the player's lets it go.
 *
 * ## The fill: the setup first, Undo in front, and the answer read (#555)
 *
 * The moment a yes fills a game is the shell's `FillProvider`, because what it sets going outlives
 * this tab; the deck asks it through `useFillYes`. **A yes with nothing saved** opens the payment
 * setup instead, the card springing back, and lands once the method is — or never, if the sheet is
 * closed. **A yes that moves money** — *Book it now*, any rescue — flies like any other and then
 * counts ten seconds behind *Undo*: its card stays in the read, **hidden** while it counts, so *Undo*
 * deals it back exactly where it was. Every other answer goes on meanwhile; only a second yes that
 * would move money springs back, with a toast — one window at a time. **Every yes's answer** goes
 * to the fill, which raises *It's a game!* or the confirmation of a refused share — a yes the card
 * called a free vote can still be the last one — and the two refusals only it can mend (no method,
 * a payment to confirm) are its, said there rather than here.
 *
 * **Offline is not a refusal.** The answer is held until the connection returns
 * (`networkMode: 'online'`), the card stays gone, and the amber note says the answer resumes.
 */

import { router } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { PlayerRecordSheet } from '@/features/player_record/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';
import {
  behindOverlay,
  courtSeatCount,
  Note,
  Segment,
  theme,
  type SegmentOption,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  anyCountingDown,
  chargesAtOnce,
  refusalOutcome,
  standingCards,
  weekCapOf,
  withOnTop,
  type DeckCard,
  type DeckPerson,
} from '../domain/deck';
import { isRescue, type DealtIn } from '../domain/fill';
import type { GameKind } from '../domain/vocabulary';
import { fortnightOf, gameDayOf, weekdayAt } from '../domain/when';
import { useDeckClock } from '../hooks/useDeckClock';
import { useFillYes } from '../hooks/useFillYes';
import { useAnswerCard, useDropCard, useGroupDeck, useRereadDeck } from '../hooks/useGroupDeck';
import { useLatest } from '../hooks/useLatest';

import { DeckAnswers } from './DeckAnswers';
import { DeckStage, type DeckExit, type DragVerdict } from './DeckStage';
import { DeclarationInterstitial } from './DeclarationInterstitial';
import {
  answerLabels,
  capLine,
  refusalMessage,
  segmentLabel,
  segmentSpoken,
  stampsFor,
} from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { PROPOSALS_COPY } from './proposalsCopy';
import { GameCard } from './GameCard';
import { ReadFailed } from './ReadFailed';
import { gameRoute, rescueRoute } from './proposalRoutes';

const COPY = PROPOSALS_COPY;

/** The top card and the two real cards behind it — never a placeholder. */
const ON_THE_STAGE = 3;

export interface GamesDeckProps {
  readonly groupId: string;
  readonly sport: Sport;
  /** The kind the page's switch last stood on. */
  readonly chosen: GameKind;
  readonly onChoose: (kind: GameKind) => void;
  /** What the tab draws when this segment deals nothing — the group's starting cards. */
  readonly empty: ReactNode;
  /**
   * **The card a notice opened the deck for** (#559; the screens A9) — on top while it is dealt,
   * the rest in the order they were dealt. Absent for a deck opened by the page.
   */
  readonly onTop?: string;
}

/** The card on its way out, and the answer that sent it there. */
interface Leaving {
  readonly card: DeckCard;
  readonly said: DeckExit;
}

export function GamesDeck({ groupId, sport, chosen, onChoose, empty, onTop }: GamesDeckProps) {
  const { read, kind } = useGroupDeck(groupId, sport, chosen);
  const reread = useRereadDeck(groupId);
  const drop = useDropCard(groupId, sport, kind);
  const dealtIn: DealtIn = { groupId, sport, kind };
  const fill = useFillYes(dealtIn);

  const [leaving, setLeaving] = useState<Leaving | undefined>(undefined);
  /** The player whose record is open — a tile's press. */
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  const answer = useAnswerCard<DeckCard>(
    groupId,
    (error: AppError, refused) => {
      const { card } = refused;
      const mended =
        card !== undefined &&
        fill.takesRefusal(error, refused, () => landLater.current('yes', card));
      if (!mended) showToast({ message: refusalMessage(error), tone: 'bad' });
      // A reason the player can mend puts the card back: straight back onto the stage if it is
      // still flying, and through the settling re-read if it has already gone.
      if (mended || refusalOutcome(error.code) === 'returns') {
        setLeaving((held) => (held?.card.proposalId === refused.proposalId ? undefined : held));
      }
    },
    fill.onAnswered,
  );

  const deck = read.data;
  const readAt = read.dataUpdatedAt;
  // The read's instant, moving on while a card counts down — see `useDeckClock`.
  const at = useDeckClock(readAt, deck !== undefined && anyCountingDown(deck.cards, readAt));
  // A yes counting down behind *Undo* keeps its card in the read, hidden until it is sent or undone.
  const standing =
    deck === undefined
      ? []
      : withOnTop(
          standingCards(deck.cards, at).filter((card) => card.proposalId !== fill.counting),
          onTop,
        );
  // The card in flight stays on the stage until it has flown, whatever a re-read says.
  const shown =
    leaving === undefined
      ? standing
      : [leaving.card, ...standing.filter((card) => card.proposalId !== leaving.card.proposalId)];
  const top = shown[0];

  const seatsPerSide = courtSeatCount(sport) / 2;
  const weekday = weekdayAt(at);
  const fortnight = fortnightOf(at);
  const cap =
    deck === undefined || fortnight === undefined
      ? undefined
      : weekCapOf(deck.cappedWeeks, fortnight.thisMonday, fortnight.nextMonday);

  // A rescue's details are its booking's, seen from outside (A4.3); every other card's, the game's.
  const open = (card: DeckCard) =>
    router.push(
      isRescue(card)
        ? rescueRoute(groupId, card.proposalId)
        : gameRoute(groupId, card.proposalId, sport, card.kind),
    );

  /**
   * One answer, from the drag or a button — the two paths cannot disagree about who may fly. A yes
   * with nothing saved waits for the setup, and the card springs back.
   */
  const answerTo = (said: DeckExit, card: DeckCard): DragVerdict => {
    if (leaving !== undefined) return 'withheld';
    if (said === 'yes' && fill.setUpFirst(() => landLater.current('yes', card))) return 'withheld';
    return land(said, card);
  };

  /**
   * The answer given: the card flies, and the yes counts down or is sent. A second yes that would
   * move money while one counts springs back and says why — one window at a time.
   */
  const land = (said: DeckExit, card: DeckCard): DragVerdict => {
    if (leaving !== undefined) return 'withheld';
    if (said === 'yes' && fill.held(card)) {
      showToast({ message: FILL_COPY.undo.oneAtATime });
      return 'withheld';
    }
    setLeaving({ card, said });
    if (said === 'yes' && fill.waits(card)) {
      fill.book(card);
      return 'taken';
    }
    answer.mutate({ proposalId: card.proposalId, said, card });
    return 'taken';
  };

  /** `land` as of the last render — what the setup's `then` and the fill's retry call. */
  const landLater = useLatest(land);

  /**
   * The card has flown: it leaves the read, and the buttons unlock — unless its yes is counting
   * down, when it stays in the read, hidden, for *Undo* to deal back.
   */
  const cardLeft = (card: DeckCard) => {
    const counts = leaving?.said === 'yes' && fill.waits(card);
    setLeaving(undefined);
    if (!counts) drop(card.proposalId);
  };

  if (deck === undefined) {
    return (
      <View style={s.page}>
        {read.error === null ? (
          <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />
        ) : (
          <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
        )}
      </View>
    );
  }

  if (deck.segments.length === 0) {
    return (
      <ScrollView contentContainerStyle={s.page}>
        <DeclarationInterstitial
          sport={sport}
          sportName={sportLabel(sport)}
          onDeclared={() => void reread()}
        />
      </ScrollView>
    );
  }

  const segments: readonly SegmentOption<GameKind>[] = deck.segments.map((segment) => ({
    key: segment.kind,
    label: segmentLabel(segment.kind, segment.count),
    accessibilityLabel: segmentSpoken(segment.kind, segment.count),
  }));

  const above = (
    <>
      <Segment options={segments} selected={kind} onSelect={onChoose} />
      {/* Above the deck and under the switch, which sits under the tabs (A1, A2.1). */}
      {cap === undefined ? null : <Text style={s.cap}>{capLine(cap)}</Text>}
      {answer.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
    </>
  );

  if (top === undefined) {
    return (
      <ScrollView contentContainerStyle={s.page}>
        {above}
        {empty}
      </ScrollView>
    );
  }

  return (
    <>
      <View style={[s.page, s.fill]} {...behindOverlay(reading !== undefined)}>
        {above}

        <View style={s.stage}>
          <DeckStage
            leaving={
              leaving !== undefined && leaving.card.proposalId === top.proposalId
                ? leaving.said
                : undefined
            }
            onAnswer={(said) => answerTo(said, top)}
            onLeft={() => cardLeft(top)}
            stamps={stampsFor(top, chargesAtOnce(top))}
            cards={shown.slice(0, ON_THE_STAGE).map((card, depth) => ({
              key: card.proposalId,
              card: (
                <GameCard
                  card={card}
                  seatsPerSide={seatsPerSide}
                  at={at}
                  day={gameDayOf(card.startsAt, at)}
                  today={weekday}
                  {...(depth === 0
                    ? {
                        onOpen: () => open(card),
                        onPerson: (person: DeckPerson) => setReading(person),
                      }
                    : {})}
                />
              ),
            }))}
          />
        </View>

        <DeckAnswers
          labels={answerLabels(top)}
          onPass={() => answerTo('no', top)}
          onAccept={() => answerTo('yes', top)}
          onRecord={() => open(top)}
          answering={leaving !== undefined}
        />
      </View>

      {/* A sibling of the screen it covers, never a child: `behindOverlay` hides everything
          inside the element carrying it. */}
      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={sport}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  // The group page's own body: the gutter, and the stacked-card step.
  page: { padding: theme.size.gutter, gap: theme.space.sm },
  fill: { flex: 1 },
  // The stage takes what the page leaves between the switch and the buttons.
  stage: { flex: 1, marginBottom: theme.space.sm },
  cap: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});

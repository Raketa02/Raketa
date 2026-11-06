/**
 * **A group's Games tab** — the deck, for the sport the page is on and the kind the switch is on
 * ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2; the mechanics §6–§8).
 *
 * ## Four states, in the order the screens list them
 *
 * 1. **No intent for this sport** — the read's segments are empty, and the one-time question
 *    *Competitive / For fun / Either* replaces the deck until it is answered (A2.1) —
 *    `DeclarationInterstitial`, reporting `DECK`; the answer is followed by finding (below), and the
 *    deck read after it has segments.
 * 2. **Nothing to deal in this segment** — the group's starting cards, exactly as built (*Just you
 *    so far*, *3 of 4*, *Nothing picked right now*), which the group page hands in as `empty`: they
 *    are the group's words about its roster, not the deck's.
 * 3. **The weekly cap** — a slim line above the deck, *Your 2 games this week are booked — showing
 *    next week* (Q73), whenever the read names a capped week of the fortnight.
 * 4. **The deck** — the switch, the stage and the three buttons (mock 1).
 *
 * **Finding** (A2.1 state 5, ADR-0201 §4, #741) follows any intent answer on this tab — the
 * first-time question's or the door's panel's: the group is dealt now and the deck it lands on read
 * (`useFindGames`), and meanwhile `FindingGames` says *Finding for-fun games for you…* where the
 * answer was given — in the question's place, or over the deck's area. Then the switch lands on the
 * kind named, and the deck's own states follow: the cards, or *Nothing picked right now*.
 *
 * While the first read is on its way the tab says so with the muted spinner; a read that failed
 * says why and offers the retry, unless the failure is one no retry can mend.
 *
 * ## A pull reads it again, in every state but the first read's
 *
 * The page draws the control and says what it re-reads (`refreshControl`); the tab puts it on
 * whichever scroller it is in — the question's, the starting card's, a failed read's, which the
 * pull mends as the retry does, and **the deck's**, a scroller with nothing to scroll that is there
 * for the pull: its content is the page's height and no more, so a drag down is the pull's and a
 * drag across is the card's, because the stage claims only a move further across than down
 * (`DeckStage`). A pull re-reads like any other read — see the next section.
 *
 * ## A re-read moves the cards behind the one being read, and never that one
 *
 * Another player's yes reaches this deck on its next read — the player's own answer settling, a
 * pull, a return to the app (the mechanics §6.4) — and the server's order puts the game that gained
 * momentum higher (§8.2). **The card on top stays on top while it is still dealt** (`underThumb`,
 * the card last drawn there), redrawn from the read — its tiles flip to In in place — and the cards
 * behind it take the server's order, so the risen game is the next card up. A notice's card still
 * goes first while it is dealt (`onTop`), and a card *Undo* takes back goes back under the thumb,
 * where it was. A card the read no longer deals leaves, as it always has: the game is over, full or
 * not the player's any more.
 *
 * **A read that set out before an answer reached the server still deals its card**, and now that an
 * answer's re-read lets a read already out land rather than throwing it away (`readAgainInTurn`),
 * such a read lands often. So a card whose answer is on its way is hidden
 * (`useAnswersOnTheirWay`) — unless a refusal put it back (`putBack`), whose answer is pending
 * until its re-read is in — and the card in flight is held here, so no read takes it off the stage.
 *
 * ## The switch is the page's, corrected by the intent
 *
 * *Competitive · 7 / For fun · 1* (mock 9) is drawn off the read's segments, and a press on a live
 * kind is the page's choice (`onChoose`, the group page's game-intent store, which Friends' switch
 * shares). A choice the intent does not show is read as the segment it does (`useGroupDeck`), so the
 * switch never stands on an empty deck the player could not have wanted.
 *
 * ## The kind the intent doesn't want is a door (Q127)
 *
 * **Both kinds are always drawn** (`switchSides`; ADR-0201 §2, #740): the one the intent shows live
 * with its count, or both for *Either*, and the other **dimmed, with no number** — `Segment`'s
 * `door`, the same box and reach. A press on it moves nothing; it opens `KindDoor`, which asks to
 * change the intent for this sport, and its answer lands the switch on the kind tapped and reads the
 * group's decks again. The panel lies **over the deck's area** — the stage and its buttons, or the
 * starting card, one `View` under the switch — so it is no route and takes no height from the cards;
 * what it covers is hidden from a screen reader beside it (`behindOverlay`). It is open while the
 * door tapped is still a door on this sport's read, so a read that now shows that kind closes it,
 * and a change of sport closes it for good.
 *
 * **The answer is written here** (`useDeclarePlayIntent`), not in the panel: the panel can go while
 * the answer is out, and the answer must still land. While it is out the switch is still.
 *
 * ## The stage was Players', and the card is this feature's
 *
 * `DeckStage` — the pan gesture, the stamps, the fly-off, the arrival, the haptic — with the two
 * cards behind now fading as they shrink (Q90), and `DeckAnswers` under it: ✕ is *Not this time*,
 * the ball is *I'm in* on every card, **i** opens the game's details (A2.2). Both were built for
 * Players' deck and came here with the interstitial in #574, since this is the deck that stays. The
 * stamps are this deck's words, each carrying the card's share: *PAY* when the yes charges at once
 * and *I'M IN* on a vote (Q124).
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
import { useEffect, useRef, useState, type ReactElement, type ReactNode } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type RefreshControlProps,
} from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { useDeclarePlayIntent } from '@/features/player_profile/types';
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
  doorPanel,
  findingAfterTheDoor,
  findingAfterTheQuestion,
  intentAnswering,
  refusalOutcome,
  standingCards,
  switchSides,
  weekCapOf,
  withOnTop,
  type DeckCard,
  type DeckPerson,
  type DoorAnswer,
  type DoorPanel,
  type Finding,
} from '../domain/deck';
import { isRescue, type DealtIn } from '../domain/fill';
import type { GameKind } from '../domain/vocabulary';
import { fortnightOf, gameDayOf, weekdayAt } from '../domain/when';
import { useDeckClock } from '../hooks/useDeckClock';
import { useFillYes } from '../hooks/useFillYes';
import {
  useAnswerCard,
  useAnswersOnTheirWay,
  useDropCard,
  useFindGames,
  useGroupDeck,
} from '../hooks/useGroupDeck';
import { useLatest } from '../hooks/useLatest';

import { DeckAnswers } from './DeckAnswers';
import { DeckStage, type DeckExit, type DragVerdict } from './DeckStage';
import { DeclarationInterstitial } from './DeclarationInterstitial';
import { doorSpoken } from './doorPresentation';
import { FindingGames } from './FindingGames';
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
import { KindDoor } from './KindDoor';
import { ReadFailed } from './ReadFailed';
import { gameRoute, rescueRoute } from './proposalRoutes';

const COPY = PROPOSALS_COPY;

/** The top card and the two real cards behind it — never a placeholder. */
const ON_THE_STAGE = 3;

/** Whichever scroller the tab is in — the one the page's pull is on. */
const BODY = 'games-deck-body';

/** The surface a door's answer reports — the deck's, as the first-time question's does. */
const DECLARED_ON = 'DECK';

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
  /**
   * **The page's pull** — drawn by the page and handed to whichever scroller the tab is in, since
   * the tab lays itself out. Absent, nothing pulls.
   */
  readonly refreshControl?: ReactElement<RefreshControlProps>;
}

/** The card on its way out, and the answer that sent it there. */
interface Leaving {
  readonly card: DeckCard;
  readonly said: DeckExit;
}

export function GamesDeck({
  groupId,
  sport,
  chosen,
  onChoose,
  empty,
  onTop,
  refreshControl,
}: GamesDeckProps) {
  const { read, kind } = useGroupDeck(groupId, sport, chosen);
  const drop = useDropCard(groupId, sport, kind);
  const dealtIn: DealtIn = { groupId, sport, kind };
  const fill = useFillYes(dealtIn);

  const [leaving, setLeaving] = useState<Leaving | undefined>(undefined);
  /** The player whose record is open — a tile's press. */
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);
  /** The card on top as last drawn — under the thumb, so a re-read moves the cards behind it. */
  const [underThumb, setUnderThumb] = useState<string | undefined>(undefined);
  /** Cards a refusal put back while their answer is still settling — drawn, not hidden. */
  const [putBack, setPutBack] = useState<ReadonlySet<string>>(() => new Set());
  /** The door the player tapped, on the sport it was tapped on — its panel is open over the deck. */
  const [door, setDoor] = useState<{ readonly sport: Sport; readonly kind: GameKind } | undefined>(
    undefined,
  );
  /** Why the panel's last answer was refused — drawn in the panel until another is given. */
  const [refusal, setRefusal] = useState<AppError | undefined>(undefined);
  // The door's answer is written here rather than in the panel, so it lands — the switch moved,
  // the group read again — when the panel has gone meanwhile (`KindDoor`).
  const declare = useDeclarePlayIntent();
  // Finding, after an intent answer here: the group dealt now, then the deck it lands on read
  // (`useFindGames`) — the area says so meanwhile, and the switch lands once it has.
  const find = useFindGames(groupId, onChoose);
  /** The intent on its way for this sport — nothing on the switch moves while it is. */
  const declaring = pendingOn(sport, declare)?.intent;
  /** The finding under way for this sport — nothing on the switch moves while it is either. */
  const finding = pendingOn(sport, find)?.finding;
  const beginFinding = (after: Finding) => find.mutate({ sport, finding: after });
  // A panel belongs to the sport it was opened on, and a change of sport closes it.
  useEffect(() => {
    setDoor(undefined);
    setRefusal(undefined);
  }, [sport]);
  const onTheirWay = useAnswersOnTheirWay();

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
        setPutBack((held) => new Set(held).add(refused.proposalId));
        setLeaving((held) => (held?.card.proposalId === refused.proposalId ? undefined : held));
      }
    },
    fill.onAnswered,
  );

  const deck = read.data;
  const readAt = read.dataUpdatedAt;
  // The read's instant, moving on while a card counts down — see `useDeckClock`.
  const at = useDeckClock(readAt, deck !== undefined && anyCountingDown(deck.cards, readAt));
  // Hidden from the read: a yes counting down behind *Undo*, kept in it until it is sent or undone,
  // and a card whose answer is on its way, which a read that set out before the answer still deals —
  // unless a refusal put it back.
  const hidden = (card: DeckCard) =>
    card.proposalId === fill.counting ||
    (onTheirWay.has(card.proposalId) && !putBack.has(card.proposalId));
  // The server's order, a notice's card first while it is dealt — and the card under the thumb kept
  // where it is, so a re-read moves the cards behind it and never swaps the one being read.
  const standing =
    deck === undefined
      ? []
      : withOnTop(
          withOnTop(
            standingCards(deck.cards, at).filter((card) => !hidden(card)),
            underThumb,
          ),
          onTop,
        );
  // The card in flight stays on the stage until it has flown, whatever a re-read says.
  const shown =
    leaving === undefined
      ? standing
      : [leaving.card, ...standing.filter((card) => card.proposalId !== leaving.card.proposalId)];
  const top = shown[0];
  useEffect(() => setUnderThumb(top?.proposalId), [top?.proposalId]);

  // *Undo* deals the card it held back where it was — on top, under the thumb again. A yes sent at
  // zero has left the read by then, so a card still in it when the count stops was taken back.
  const counted = useRef<string | null>(null);
  useEffect(() => {
    const was = counted.current;
    counted.current = fill.counting;
    if (was === null || fill.counting !== null) return;
    if (deck?.cards.some((card) => card.proposalId === was) === true) setUnderThumb(was);
  }, [fill.counting, deck]);

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
      showToast({ message: FILL_COPY.undo.oneAtATime, hold: 'read' });
      return 'withheld';
    }
    if (putBack.has(card.proposalId)) setPutBack((held) => without(held, card.proposalId));
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
    // Nothing to pull while the first read is on its way; one that failed pulls as its retry reads.
    return read.error === null ? (
      <View style={s.page}>
        <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />
      </View>
    ) : (
      <ScrollView testID={BODY} contentContainerStyle={s.page} refreshControl={refreshControl}>
        <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
      </ScrollView>
    );
  }

  if (deck.segments.length === 0) {
    return (
      <ScrollView testID={BODY} contentContainerStyle={s.page} refreshControl={refreshControl}>
        {/* The answer's finding stands where the question was, until the deck it lands on is read. */}
        {finding === undefined ? (
          <DeclarationInterstitial
            sport={sport}
            sportName={sportLabel(sport)}
            onDeclared={(intent) => beginFinding(findingAfterTheQuestion(intent, kind))}
          />
        ) : (
          <FindingGames finding={finding} />
        )}
      </ScrollView>
    );
  }

  // Both kinds, always: the one the intent shows live with its count, the other a door (Q127).
  const sides = switchSides(deck.segments);
  const segments: readonly SegmentOption<GameKind>[] = sides.map((side) =>
    side.door
      ? {
          key: side.kind,
          label: COPY.kind[side.kind],
          accessibilityLabel: doorSpoken(side.kind),
          door: true,
        }
      : {
          key: side.kind,
          label: segmentLabel(side.kind, side.count),
          accessibilityLabel: segmentSpoken(side.kind, side.count),
        },
  );
  // Open while the door tapped is still a door on this sport's read — a read that now shows the
  // kind closes it, and a panel opened on another sport is not this one's.
  const panel =
    door === undefined || door.sport !== sport ? undefined : doorPanel(deck.segments, door.kind);

  /**
   * A door opens its panel and moves nothing; a live kind is the page's choice, as ever. While an
   * answer is on its way, or its games are being found, the switch is still: finding lands it.
   */
  const choose = (pressed: GameKind) => {
    if (declaring !== undefined || finding !== undefined) return;
    if (doorPanel(deck.segments, pressed) !== undefined) {
      setRefusal(undefined);
      setDoor({ sport, kind: pressed });
      return;
    }
    setDoor(undefined);
    onChoose(pressed);
  };

  /**
   * The panel's answer, for this sport alone. On landing the panel closes and the tab is finding,
   * as after the first-time question — the group dealt, the deck read, the switch on the kind
   * tapped; a refusal stays in the panel. Handed to this call because the deck outlives the panel —
   * see `KindDoor`.
   */
  const answerTheDoor = (asked: DoorPanel, said: DoorAnswer) => {
    setRefusal(undefined);
    declare.mutate(
      { sport, intent: intentAnswering(asked, said), surface: DECLARED_ON },
      {
        onSuccess: () => {
          setDoor(undefined);
          beginFinding(findingAfterTheDoor(asked));
        },
        onError: (error) => setRefusal(error),
      },
    );
  };

  // Over the deck's area, on its paper: finding after an answer, or the door's panel — never both,
  // since an answer that lands closes the panel.
  const overTheDeck =
    finding !== undefined ? (
      <View style={s.over}>
        <FindingGames finding={finding} />
      </View>
    ) : panel === undefined ? null : (
      <View style={s.over}>
        <KindDoor
          sport={sport}
          panel={panel}
          {...(declaring === undefined ? {} : { answering: declaring })}
          {...(refusal === undefined ? {} : { refusal })}
          onAnswer={(said) => answerTheDoor(panel, said)}
          onClose={() => setDoor(undefined)}
        />
      </View>
    );
  const covered = behindOverlay(panel !== undefined || finding !== undefined);

  const above = (
    <>
      <Segment options={segments} selected={kind} onSelect={choose} />
      {/* Above the deck and under the switch, which sits under the tabs (A1, A2.1). */}
      {cap === undefined ? null : <Text style={s.cap}>{capLine(cap)}</Text>}
      {answer.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
    </>
  );

  if (top === undefined) {
    return (
      <ScrollView
        testID={BODY}
        contentContainerStyle={[s.page, s.grow]}
        refreshControl={refreshControl}
      >
        {above}
        {/* The deck's area, which the door's panel covers — see the module note. */}
        <View style={s.area}>
          <View style={s.under} {...covered}>
            {empty}
          </View>
          {overTheDeck}
        </View>
      </ScrollView>
    );
  }

  return (
    <>
      {/* A scroller with nothing to scroll, there for the pull — see the module note. */}
      <ScrollView
        testID={BODY}
        contentContainerStyle={[s.page, s.grow]}
        refreshControl={refreshControl}
        {...behindOverlay(reading !== undefined)}
      >
        {above}

        {/* The deck's area, which the door's panel covers — see the module note. */}
        <View style={s.area}>
          <View style={s.under} {...covered}>
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
          {overTheDeck}
        </View>
      </ScrollView>

      {/* A sibling of the screen it covers, never a child: `behindOverlay` hides everything
          inside the element carrying it. */}
      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={sport}
          groupId={groupId}
        />
      )}
    </>
  );
}

/** A write's variables while it is on its way for this sport — the switch is still meanwhile. */
function pendingOn<V extends { readonly sport: Sport }>(
  sport: Sport,
  write: { readonly isPending: boolean; readonly variables?: V | undefined },
): V | undefined {
  return write.isPending && write.variables?.sport === sport ? write.variables : undefined;
}

/** The set without one id. */
function without(held: ReadonlySet<string>, proposalId: string): ReadonlySet<string> {
  const next = new Set(held);
  next.delete(proposalId);
  return next;
}

const s = StyleSheet.create({
  // The group page's own body: the gutter, and the stacked-card step.
  page: { padding: theme.size.gutter, gap: theme.space.sm },
  // The page's height at least, so the stage below takes what the switch and the buttons leave.
  grow: { flexGrow: 1 },
  // The deck's area — what the page leaves under the switch, and what the door's panel covers.
  area: { flex: 1 },
  // What the area holds: the stage and the buttons, or the starting card — the page's own step.
  under: { flex: 1, gap: theme.space.sm },
  // The ground of what lies over the deck's area — the paper the cards stand on, covering them.
  over: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.paper },
  // The stage takes what the page leaves between the switch and the buttons.
  stage: { flex: 1, marginBottom: theme.space.sm },
  cap: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});

/**
 * **A group's Games tab** — the deck, for the sport the page is on and the kind its menu stands on
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
 * 3. **The weekly cap** — a slim line above the deck, directly under the tabs, *Your 2 games this
 *    week are booked — showing next week* (Q73), whenever the read names a capped week of the
 *    fortnight; the offline note stands there too.
 * 4. **The deck** — the stage and the three buttons (mock 1), taking the height down to the page's
 *    foot. No switch is drawn above it since #862: the kind is picked in the Games tab's menu.
 *
 * **Finding** (A2.1 state 5, ADR-0201 §4, #741) follows any intent answer on this tab — the
 * first-time question's or the door's panel's: the group is dealt now and the deck it lands on read
 * (`useFindGames`), and meanwhile `FindingGames` says *Finding for-fun games for you…* where the
 * answer was given — in the question's place, or over the deck's area. Then the deck lands on the
 * kind named, and its own states follow: the cards, or *Nothing picked right now*.
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
 * **Unless the card cannot fit the page** (#865; the tab menu log §6.5): a short card shrinks every
 * box on it in proportion, down to its floor, and each card on the stage says how short that is
 * (`onLeast`, `deckCardGeometry`). The stage is laid out at no less than the tallest of them, so on a
 * 320 × 568 phone or at the largest text sizes the scroller's content is the card at its least and
 * the buttons under it, and it scrolls to them — a drag down still the scroller's, a drag across
 * still the card's, as above.
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
 * ## The kind is the page's, picked in the tab's menu and corrected by the intent
 *
 * **The Games tab's menu is the group page's** (#862, PRD #859; tab menu mocks 1 and 3,
 * illustrations), where the switch's *Competitive · 7 / For fun · 1* stood (mock 9): the page draws
 * it off the reads it already holds (`useGamesMenu`, `kindMenuLines`) and hands the deck the kind
 * (`chosen`, the group page's game-intent store) and every line picked (`GamesDeckHandle`). A live
 * kind picked is the page's choice (`onChoose`). A choice the intent does not show is read as the
 * segment it does (`useGroupDeck`), so the deck never stands on an empty kind the player could not
 * have wanted.
 *
 * ## A kind picked swaps the deck in place (#863)
 *
 * **The stack goes out and the other kind's comes in** (the tab menu log §5.1–§5.2; `KindSwap.tsx`
 * draws it, `domain/kindSwap.ts` rules it, `useKindSwap` times it): going out, the deck still draws
 * the kind it leaves, while the kind picked is read from the press; coming in, its stack rises into
 * the same place once that read is in — today's spinner standing in the stack's place until it is —
 * and the stage's own arrival is not run for its cards (`standing`). **Only the cards move**: the
 * stack, the starting card or the swap's spinner stand in one layer, drawn always, and the buttons
 * in another, kept where both kinds deal cards and faded where one side is the starting card. **No
 * answer reaches a stack on the move.** A failed read goes out to today's failure, and a change of
 * sport ends a swap. **Only a pick from the menu moves anything**: a notice's kind and the kind
 * finding lands on are the page's choice made directly, and draw the deck directly.
 *
 * ## The kind the intent doesn't want is a door (Q127)
 *
 * **Both kinds are always in the menu** (`switchSides`; ADR-0201 §2, #740): the one the intent shows
 * live with its count, or both for *Either*, and the other **dimmed, with no number** — a line as
 * tall and as easy to press as the live one. Picked, it moves nothing: the menu closes and this deck
 * opens `KindDoor`, which asks to change the intent for this sport, and its answer lands the deck on
 * the kind tapped and reads the group's decks again. The panel lies **over the deck's area** — the
 * stage and its buttons, or the starting card, one `View` under the cap line — so it is no route and
 * takes no height from the cards; what it covers is hidden from a screen reader beside it
 * (`behindOverlay`). It is open while the door tapped is still a door on this sport's read, so a read
 * that now shows that kind closes it, a live kind picked closes it as the switch's press did, and a
 * change of sport closes it for good. **A door the menu draws is one that opens**: which kind is one
 * is this read's say, or while it is on its way or failed that of the reads the menu is drawn from
 * (`useKindsHeld`), and the panel — and finding after it — lies over the spinner or the failure too.
 *
 * **The answer is written here** (`useDeclarePlayIntent`), not in the panel: the panel can go while
 * the answer is out, and the answer must still land. While it is out, and while finding follows it,
 * the page's menu is still — read off the two mutations' own state (`useGamesMenu`).
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
 *
 * ## What the deck shows is seen (#850, ADR-0208)
 *
 * The page's Games badge counts the cards with somebody In that the player hasn't seen, across both
 * kinds, off this read's ids (`useGamesBadge`). **The deck marks the whole of the kind on screen**,
 * on that kind's own list — every card the read dealt, not only the one on top, and the ones this
 * build cannot draw too (`dealtIds`), which only a visit can clear — whenever they change while the
 * page is in view (`inView`) with nothing over the deck: no player's record, nothing of the fill's,
 * neither the door's panel nor finding over its area. The other kind's cards are never among them,
 * so they stay new until the deck moves there — opening the tab's menu sees nothing (#862); a
 * notice's card is seen as any visit is, once the page has moved the kind to its own. A card that
 * only changed — a join, a new version — keeps its id and stays seen.
 */

import { router } from 'expo-router';
import {
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
  type Ref,
} from 'react';
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
import { behindOverlay, courtSeatCount, Note, theme } from '@/shared/ui';
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
  weekCapOf,
  withOnTop,
  type DeckCard,
  type DeckPerson,
  type DoorAnswer,
  type DoorPanel,
  type Finding,
} from '../domain/deck';
import { isRescue, type DealtIn } from '../domain/fill';
import {
  buttonsMotion,
  stackMotion,
  swapTo,
  takesAnswers,
  type StackDrawn,
} from '../domain/kindSwap';
import { gamesSeen } from '../domain/seen';
import type { GameKind } from '../domain/vocabulary';
import { fortnightOf, gameDayOf, weekdayAt } from '../domain/when';
import { useDeckClock } from '../hooks/useDeckClock';
import { useFill } from '../hooks/useFill';
import { useFillYes } from '../hooks/useFillYes';
import {
  useAnswerCard,
  useAnswersOnTheirWay,
  useDropCard,
  useFindGames,
  useKindsHeld,
} from '../hooks/useGroupDeck';
import { useKindSwap } from '../hooks/useKindSwap';
import { useLatest } from '../hooks/useLatest';
import { useSeeRows } from '../hooks/useSeenRows';

import { DeckAnswers } from './DeckAnswers';
import { DeckStage, type DeckExit, type DragVerdict } from './DeckStage';
import { DeclarationInterstitial } from './DeclarationInterstitial';
import { FindingGames } from './FindingGames';
import {
  ANSWER_LABELS,
  answerLabels,
  capLine,
  refusalMessage,
  stampsFor,
} from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { PROPOSALS_COPY } from './proposalsCopy';
import { GameCard } from './GameCard';
import { KindDoor } from './KindDoor';
import { SwapButtons, SwapStack } from './KindSwap';
import { ReadFailed } from './ReadFailed';
import { gameRoute, rescueRoute } from './proposalRoutes';

const COPY = PROPOSALS_COPY;

/** The top card and the two real cards behind it — never a placeholder. */
const ON_THE_STAGE = 3;

/** Whichever scroller the tab is in — the one the page's pull is on. */
const BODY = 'games-deck-body';

/** The stage's box, laid out at no less than its cards' least height (#865). */
const STAGE = 'games-deck-stage';

/** The surface a door's answer reports — the deck's, as the first-time question's does. */
const DECLARED_ON = 'DECK';

/**
 * **What the page asks the deck** (#862): the Games tab's menu is the page's, and the door's panel
 * and its write are the deck's — so a line picked there is handed here.
 */
export interface GamesDeckHandle {
  /** A line of the tab's menu was picked: a door opens its panel, a live kind is chosen. */
  readonly pick: (kind: GameKind) => void;
}

export interface GamesDeckProps {
  readonly groupId: string;
  readonly sport: Sport;
  /** The kind the page's menu last stood on — corrected by the intent (`useGroupDeck`). */
  readonly chosen: GameKind;
  /** A live kind picked, or the kind finding lands on — the page's choice to keep. */
  readonly onChoose: (kind: GameKind) => void;
  /** What the page's menu asks — see `GamesDeckHandle`. */
  readonly handle?: Ref<GamesDeckHandle>;
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
  /**
   * Whether the page is the screen in view — nothing pushed over it (`useScreenInView`). What the
   * deck shows is seen only while it is (#850).
   */
  readonly inView: boolean;
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
  handle,
  empty,
  onTop,
  refreshControl,
  inView,
}: GamesDeckProps) {
  /** The card on its way off the stage, and its answer — until it has flown. */
  const [leaving, setLeaving] = useState<Leaving | undefined>(undefined);
  // The kind drawn — the one chosen, or while a pick's stack goes out the one it leaves, held while
  // a card of it is still in flight — and the swap under way (#863; see the module note).
  const {
    read,
    kind,
    swap,
    begin: beginSwap,
    end: endSwap,
  } = useKindSwap(groupId, sport, chosen, leaving !== undefined);
  const drop = useDropCard(groupId, sport, kind);
  const dealtIn: DealtIn = { groupId, sport, kind };
  const fill = useFillYes(dealtIn);
  /** What the fill has up over the phone — *It's a game!* or one of its sheets covers the deck. */
  const fillOver = useFill().over;

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
  /**
   * How short each card standing on the stage can get, by its id — the stage is laid out at no less
   * (#865). A card that leaves takes its entry with it.
   */
  const [leasts, setLeasts] = useState<Readonly<Record<string, number>>>({});
  const cardLeast = useCallback(
    (proposalId: string, least: number | undefined) =>
      setLeasts((was) => {
        if (was[proposalId] === least) return was;
        const { [proposalId]: _gone, ...others } = was;
        return least === undefined ? others : { ...others, [proposalId]: least };
      }),
    [],
  );
  // The door's answer is written here rather than in the panel, so it lands — the deck moved,
  // the group read again — when the panel has gone meanwhile (`KindDoor`).
  const declare = useDeclarePlayIntent();
  // Finding, after an intent answer here: the group dealt now, then the deck it lands on read
  // (`useFindGames`) — the area says so meanwhile, and the deck lands once it has.
  const find = useFindGames(groupId, onChoose);
  /** The intent on its way for this sport — a pick moves nothing while it is. */
  const declaring = pendingOn(sport, declare)?.intent;
  /** The finding under way for this sport — a pick moves nothing while it is either. */
  const finding = pendingOn(sport, find)?.finding;
  const beginFinding = (after: Finding) => find.mutate({ sport, finding: after });
  // A panel belongs to the sport it was opened on, and a change of sport closes it — and stops a
  // swap, which was the other sport's deck's.
  useEffect(() => {
    setDoor(undefined);
    setRefusal(undefined);
    endSwap();
  }, [sport, endSwap]);
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
  // The kinds the intent shows: this deck's read's, or — while it is on its way or failed — the
  // reads the page's menu is drawn from (`useKindsHeld`), so a door the menu draws is one that opens.
  const held = useKindsHeld(groupId, sport, chosen);
  const kinds = deck?.segments ?? held;
  // Open while the door tapped is still a door on this sport's read — a read that now shows the
  // kind closes it, and a panel opened on another sport is not this one's.
  const panel =
    kinds === undefined || door === undefined || door.sport !== sport
      ? undefined
      : doorPanel(kinds, door.kind);

  // What the deck shows is seen while it is on screen (#850): every card the read of the kind on
  // screen dealt, whenever they change while the page is in view with nothing over the deck — no
  // record's sheet, nothing of the fill's, neither the door's panel nor finding over its area. On
  // that kind's own list, so a read of one kind never cuts back what was seen on the other.
  useSeeRows(
    groupId,
    sport,
    gamesSeen(kind),
    deck === undefined ? undefined : { onScreen: deck.dealtIds, counted: deck.inCardIds },
    inView &&
      reading === undefined &&
      fillOver === 'none' &&
      panel === undefined &&
      finding === undefined,
  );
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

  // The cards on the stage, and the least height the tallest of them can get to — the stage is laid
  // out at no less, and where the page leaves less the scroller scrolls (#865, see the module note).
  // Until one of them has said, the last height holds — after an answer, a swap, a new deal — so the
  // stage never drops to the page and back.
  const onStage = shown.slice(0, ON_THE_STAGE);
  const said = onStage.flatMap((card) => leasts[card.proposalId] ?? []);
  const lastLeast = useRef(0);
  if (said.length > 0) lastLeast.current = Math.max(...said);
  const least = lastLeast.current;

  // What stands where the stack stands, and how it and the buttons move (#863).
  const stack: StackDrawn =
    deck === undefined ? 'reading' : top === undefined ? 'nothing' : 'cards';
  const buttons = buttonsMotion(swap, stack);
  /** Whether the deck stands as a stack a pick can swap: not today's first spinner, nor a failure. */
  const swappable =
    deck === undefined ? swap !== undefined && read.error === null : deck.segments.length > 0;

  /**
   * A line of the Games tab's menu, picked (`GamesDeckHandle`). A door opens its panel and moves
   * nothing; a live kind is the page's choice, as ever, and shuts a panel left open — as a press on
   * the switch's live kind did. **A live kind other than the one drawn swaps the deck in place**
   * (#863): its stack goes out while the kind picked is read, and comes in once it is; from today's
   * first spinner or a failure there is no stack to move, and the kind is drawn directly. While an
   * answer is on its way, or its games are being found, nothing moves: finding lands it. Which kind
   * is a door is what the menu drew it from (`kinds`), so its panel opens even over this deck's
   * spinner or its failure.
   */
  const pick = (pressed: GameKind) => {
    if (declaring !== undefined || finding !== undefined) return;
    if (kinds !== undefined && doorPanel(kinds, pressed) !== undefined) {
      setRefusal(undefined);
      setDoor({ sport, kind: pressed });
      return;
    }
    setDoor(undefined);
    // Still going out, a pick only changes where the swap lands — the kind going out included.
    if (swappable && (pressed !== kind || swap?.phase === 'out')) {
      const held = buttons === 'kept' || buttons === 'in';
      beginSwap(swapTo(swap, { from: kind, stack, held, kinds }, pressed));
    }
    onChoose(pressed);
  };
  useImperativeHandle(handle, () => ({ pick }));

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
    // No answer reaches a stack on the move — going out, or coming in until it has landed (#863).
    if (leaving !== undefined || !takesAnswers(swap)) return 'withheld';
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

  /**
   * The panel's answer, for this sport alone. On landing the panel closes and the tab is finding,
   * as after the first-time question — the group dealt, the deck read and landed on the kind
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

  // A swap's spinner stands in the stack's place, below; today's stands alone (#863).
  if (deck === undefined && (swap === undefined || read.error !== null)) {
    // Nothing to pull while the first read is on its way; one that failed pulls as its retry reads.
    const waiting =
      read.error === null ? (
        <View style={s.page}>
          <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />
        </View>
      ) : (
        <ScrollView testID={BODY} contentContainerStyle={s.page} refreshControl={refreshControl}>
          <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
        </ScrollView>
      );
    // A door picked in the menu while this kind is read opens over the spinner or the failure, as
    // over the cards (#862) — and so does finding.
    return overTheDeck === null ? (
      waiting
    ) : (
      <View style={s.area}>
        <View style={s.area} {...covered}>
          {waiting}
        </View>
        {overTheDeck}
      </View>
    );
  }

  if (deck !== undefined && deck.segments.length === 0) {
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

  const above = (
    <>
      {/* Above the deck, directly under the tabs (A1, A2.1 state 6; #862). */}
      {cap === undefined ? null : <Text style={s.cap}>{capLine(cap)}</Text>}
      {answer.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
    </>
  );

  // The stage, the starting card, or a swap's spinner, in the layer a swap moves — and the buttons
  // under it, in theirs (#863, `KindSwap`): drawn always, at rest when nothing swaps.
  const stage =
    top !== undefined ? (
      <DeckStage
        standing={swap !== undefined}
        leaving={
          leaving !== undefined && leaving.card.proposalId === top.proposalId
            ? leaving.said
            : undefined
        }
        onAnswer={(said) => answerTo(said, top)}
        onLeft={() => cardLeft(top)}
        stamps={stampsFor(top, chargesAtOnce(top))}
        cards={onStage.map((card, depth) => ({
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
              onLeast={cardLeast}
            />
          ),
        }))}
      />
    ) : stack === 'nothing' ? (
      empty
    ) : null;

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
        <View style={s.deckArea}>
          <View style={s.under} {...covered}>
            <SwapStack
              motion={stackMotion(swap, deck !== undefined)}
              // The stage takes the height the page leaves, and never less than its cards' least;
              // the starting card, its own.
              {...(stack === 'nothing'
                ? {}
                : { style: [s.stage, { minHeight: least }], testID: STAGE })}
              {...(stack === 'reading'
                ? {
                    waiting: (
                      <ActivityIndicator
                        accessibilityLabel={COPY.reading}
                        color={theme.color.muted}
                      />
                    ),
                  }
                : {})}
            >
              {stage}
            </SwapStack>

            {buttons === 'none' ? null : (
              // Nothing here reaches a stack going out. Coming in, the i opens the card coming in,
              // and ✕ and the ball wait for it to land (`answerTo`).
              <SwapButtons motion={buttons} inert={swap?.phase === 'out'}>
                {/* Under a swap's spinner they are kept, answering nothing, with the game's own
                    names — there is no card yet to name them for. */}
                <DeckAnswers
                  labels={top === undefined ? ANSWER_LABELS : answerLabels(top)}
                  onPass={() => {
                    if (top !== undefined) answerTo('no', top);
                  }}
                  onAccept={() => {
                    if (top !== undefined) answerTo('yes', top);
                  }}
                  onRecord={() => {
                    if (top !== undefined && swap?.phase !== 'out') open(top);
                  }}
                  answering={leaving !== undefined}
                />
              </SwapButtons>
            )}
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

/** A write's variables while it is on its way for this sport — a pick moves nothing meanwhile. */
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
  // The page's height at least, so the stage below takes what the cap line and the buttons leave.
  grow: { flexGrow: 1 },
  // The deck's area — what the page leaves under the cap line, and what the door's panel covers.
  area: { flex: 1 },
  // The same, round the stage: as tall as its content at least — the stage at its cards' least and
  // the buttons — so where that is more than the page the scroller's content grows past it and
  // scrolls, and where it is less, the page's height (#865). `flex: 1` would size it from nought.
  deckArea: { flexGrow: 1 },
  // What the area holds: the stage and the buttons, or the starting card — the page's own step.
  under: { flexGrow: 1, gap: theme.space.sm },
  // The ground of what lies over the deck's area — the paper the cards stand on, covering them.
  over: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.paper },
  // The stage takes what the page leaves between the cap line and the buttons, and no less than its
  // cards' least (#865) — a basis of its content, which is that, never of nought.
  stage: { flexGrow: 1, marginBottom: theme.space.sm },
  cap: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});

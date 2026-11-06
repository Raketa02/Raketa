/**
 * **A group's deck, and the rules a card is drawn by** — the Games tab
 * ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2, the mechanics §6–§8,
 * [ADR-0189](../../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)).
 *
 * Pure: what the server dealt, as the mapper reads it, and the handful of decisions the card makes
 * over it. **Nothing the server decides is re-derived here** — the order, the sides, the forecast,
 * the grade and the shades are the read's (`ReadGroupDeck`, #539). What is decided here is only
 * how a card that has been dealt is *drawn*: which side is the top row, whether the ribbon counts
 * down, which tag the court block wears, and whether a yes says *Pay* (Q124).
 *
 * **How many stand on a side is handed in**, as the group page's rules take the court's seats: it
 * is drawn knowledge (`courtSeatCount`, `shared/ui`), and a second table of seats here would be a
 * second answer to it.
 */

import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import type { Weekday } from '@/shared/vocabulary/week';

import {
  GAME_KINDS,
  type CardType,
  type ClubCancelReason,
  type CourtState,
  type DayRange,
  type GameKind,
  type OverlapGrade,
  type OverlapShade,
} from './vocabulary';

/** One person on a card — the reader among them, marked. */
export interface DeckPerson {
  readonly playerId: string;
  readonly isYou: boolean;
  /** Their Name, whole — `undefined` for an account that can no longer be named. */
  readonly name?: string;
  /** Omitted when they have no photograph: the tile draws their poster. */
  readonly photoUrl?: string;
  /** Their published Level in the card's sport — omitted while unrated. */
  readonly level?: number;
  /** They said yes: the **IN** tag, the only tag a dealt card's tile carries (Q69). */
  readonly isIn: boolean;
  /**
   * **Their share was taken** — the *paid* beside a booked game's Level (details 8, #556), and a
   * rescue's players on a *Seat open* card (#545, #557). Absent on a card still filling, where
   * nobody has paid anything and the tile says IN or nothing — and on the reader's own tile on a
   * rescue, which is the seat that opened.
   */
  readonly paid?: boolean;
  /**
   * **The reader's own friend** — the **FRIEND** tag on a tile, *friend* on a Fill in square (#753;
   * Q68, applying since Q128). Present only when they are: nothing on the wire says who else is
   * friends with whom, and a tile with no tag claims nothing.
   */
  readonly friend?: true;
}

/** One cell of the overlap grid. */
export interface OverlapCell {
  readonly day: Weekday;
  readonly range: DayRange;
  readonly shade: OverlapShade;
}

/** The card's people's week — graded, shaded, and the game's own cell ringed. */
export interface Overlap {
  readonly grade: OverlapGrade;
  readonly cells: readonly OverlapCell[];
  readonly game: { readonly day: Weekday; readonly range: DayRange };
}

/** One card, as the reader is dealt it: **their own version** of the game. */
export interface DeckCard {
  readonly proposalId: string;
  readonly type: CardType;
  readonly kind: GameKind;
  /**
   * Who a challenge names — *Kuba challenged you*. Absent on a pick, and on a challenge once its
   * poster withdrew: *The group challenged you*.
   */
  readonly challenger?: { readonly playerId: string; readonly name?: string };
  /** The court hour's start, an instant; games are an hour. */
  readonly startsAt: string;
  /** The club — its name omitted for a club that no longer exists. */
  readonly club: { readonly id: string; readonly name?: string };
  /** What the reader pays if it fills. */
  readonly shareGrosze: number;
  /** When the card leaves unfilled — its book-by, or a rescue's cut-off and then its start. */
  readonly deadline: string;
  /** People In on the whole game, every version counted. */
  readonly inCount: number;
  /** Versions the game was dealt in — above one, the card says how many are In on all of them. */
  readonly versionCount: number;
  /** Nought is *You complete it*. */
  readonly openSeatsAfterYourYes: number;
  readonly court: CourtState;
  /** What the club calls the court — a rescue's, booked already: *· Court 6*. Absent until booked. */
  readonly courtName?: string;
  /**
   * The kind of court the card promises (#677): `true` *Indoor*, `false` *Outdoor*. Absent where the
   * free courts it could be booked on are mixed, which promises neither (Q122).
   */
  readonly indoor?: boolean;
  /** The club's cut-off has already passed: *no free cancellation*. */
  readonly noFreeCancellation: boolean;
  /** The rows are the sides (Q70): the reader's, and the other. A side may be short of a seat. */
  readonly sides: { readonly yours: readonly DeckPerson[]; readonly theirs: readonly DeckPerson[] };
  /** Omitted where the server could not read one — somebody unrated, or nobody facing you yet. */
  readonly forecast?: { readonly pct: number; readonly provisional: boolean };
  readonly overlap: Overlap;
}

/** One side of the *Competitive · N / For fun · N* switch. */
export interface DeckSegment {
  readonly kind: GameKind;
  readonly count: number;
}

/** A week the reader has as many games booked in as they allow — nothing is dealt for it. */
export interface CappedWeek {
  /** Its Monday, `YYYY-MM-DD`, on the club's clock. */
  readonly startsOn: string;
  readonly booked: number;
}

/** A group's Games tab, for one sport and one kind. */
export interface GroupDeck {
  /** Empty while the reader has declared no intent for the sport — the question replaces the deck. */
  readonly segments: readonly DeckSegment[];
  /** Cards where somebody is already In with the reader, across the segments. */
  readonly gamesBadge: number;
  readonly gamesPerWeek: number;
  readonly cappedWeeks: readonly CappedWeek[];
  /** In the order dealt. */
  readonly cards: readonly DeckCard[];
}

// ---------------------------------------------------------------------------
// Which segment the deck is read for
// ---------------------------------------------------------------------------

/**
 * **The kind the deck is on** — the one the player chose, while their intent shows it; otherwise
 * the first segment it does show (the screens A1: *a player whose intent is one kind sees only that
 * segment*). With no segments yet — nothing read, or no intent declared — the choice stands: there
 * is nothing to correct it against.
 */
export function resolveKind(
  chosen: GameKind,
  segments: readonly DeckSegment[] | undefined,
): GameKind {
  const first = segments?.[0];
  if (first === undefined) return chosen;
  return segments?.some((segment) => segment.kind === chosen) === true ? chosen : first.kind;
}

// ---------------------------------------------------------------------------
// The door — the kind the intent does not show (ADR-0201 §2)
// ---------------------------------------------------------------------------

/**
 * **One side of the switch** — a kind the intent shows, with its count, or **the door**: the kind
 * it does not, drawn dimmed with no number, whose press opens the panel rather than the deck.
 */
export type SwitchSide =
  | { readonly kind: GameKind; readonly door: false; readonly count: number }
  | { readonly kind: GameKind; readonly door: true };

/**
 * **Both kinds, always, in the switch's order** (Q127): the read's segments are the kinds the
 * intent shows, so a kind missing from them is the door. With no segments the intent is
 * undeclared, the first-time question stands in the deck's place, and there is no switch.
 */
export function switchSides(segments: readonly DeckSegment[]): readonly SwitchSide[] {
  if (segments.length === 0) return [];
  return GAME_KINDS.map((kind): SwitchSide => {
    const live = segments.find((segment) => segment.kind === kind);
    return live === undefined ? { kind, door: true } : { kind, door: false, count: live.count };
  });
}

/**
 * **What a door's panel says** — the one kind the player plays, their count of it in this group
 * (the number their switch shows, so it is as old as the read), and the kind they tapped.
 */
export interface DoorPanel {
  readonly yours: GameKind;
  readonly count: number;
  readonly tapped: GameKind;
}

/**
 * The panel a press on `tapped` opens — only on a door, `switchSides`' own, so the switch's drawing
 * and the panel cannot disagree about which kind is one. *Either suits me* has no door (Q7), an
 * undeclared sport has no switch, and beside a door stands the one kind the player plays.
 */
export function doorPanel(
  segments: readonly DeckSegment[],
  tapped: GameKind,
): DoorPanel | undefined {
  const sides = switchSides(segments);
  if (!sides.some((side) => side.kind === tapped && side.door)) return undefined;
  const yours = sides.find((side) => !side.door);
  return yours === undefined || yours.door
    ? undefined
    : { yours: yours.kind, count: yours.count, tapped };
}

/** The panel's two answers that change something; *Keep* sends nothing. */
export type DoorAnswer = 'either' | 'tapped';

const INTENT_OF_KIND: Readonly<Record<GameKind, PlayIntent>> = {
  competitive: 'COMPETITIVE',
  forFun: 'FOR_FUN',
};

/** **The intent an answer declares** — *Either suits me*, or the kind tapped alone. */
export function intentAnswering(panel: DoorPanel, answer: DoorAnswer): PlayIntent {
  return answer === 'either' ? 'NO_PREFERENCE' : INTENT_OF_KIND[panel.tapped];
}

// ---------------------------------------------------------------------------
// Finding — after an intent answer on Games (ADR-0201 §4)
// ---------------------------------------------------------------------------

/**
 * **What the tab says while Raketa deals the group, and where the deck lands after** (the screens
 * A2.1 state 5): *Finding for-fun games for you…* names the kind it lands on, and *Finding games for
 * you…* names none — after *Either suits me* on the first-time question, when both kinds arrive.
 */
export interface Finding {
  readonly landsOn: GameKind;
  /** Absent when the answer wanted both kinds and none was tapped. */
  readonly names?: GameKind;
}

/** After the door's panel: the kind tapped, whichever of its two answers. */
export function findingAfterTheDoor(panel: DoorPanel): Finding {
  return { landsOn: panel.tapped, names: panel.tapped };
}

/**
 * After the first-time question: the kind answered — or, for *Either suits me*, no kind named and
 * the deck where the switch already stands (`chosen`), since both kinds are now the player's.
 */
export function findingAfterTheQuestion(intent: PlayIntent, chosen: GameKind): Finding {
  if (intent === 'NO_PREFERENCE') return { landsOn: chosen };
  const kind = KIND_OF_INTENT[intent];
  return { landsOn: kind, names: kind };
}

/** The kind an intent of one kind wants — `INTENT_OF_KIND` read the other way. */
const KIND_OF_INTENT: Readonly<Record<Exclude<PlayIntent, 'NO_PREFERENCE'>, GameKind>> = {
  COMPETITIVE: 'competitive',
  FOR_FUN: 'forFun',
};

// ---------------------------------------------------------------------------
// The rows
// ---------------------------------------------------------------------------

/** A seat on a card: somebody, or a seat a short side leaves empty. */
export type DeckSeat =
  { readonly kind: 'person'; readonly person: DeckPerson } | { readonly kind: 'empty' };

/** One row of tiles — one side — and whether it is the reader's. */
export interface DeckRow {
  readonly yours: boolean;
  readonly seats: readonly DeckSeat[];
}

/**
 * **Where a person stands in their row** — the people In first, then you, then the rest in the
 * order dealt. It is the order every mock draws: *Ania* (In) before *You* in mock 3, *You* before
 * *Ewa* (not In) in mock 4.
 */
function rank(person: DeckPerson): number {
  if (person.isIn) return 0;
  return person.isYou ? 1 : 2;
}

function rowOf(people: readonly DeckPerson[], yours: boolean, seatsPerSide: number): DeckRow {
  const ordered = people
    .map((person, dealt) => ({ person, dealt }))
    .sort((a, b) => rank(a.person) - rank(b.person) || a.dealt - b.dealt)
    .map(({ person }): DeckSeat => ({ kind: 'person', person }));
  const empty = Math.max(0, seatsPerSide - ordered.length);
  return {
    yours,
    seats: [...ordered, ...Array.from({ length: empty }, (): DeckSeat => ({ kind: 'empty' }))],
  };
}

function inOn(people: readonly DeckPerson[]): number {
  return people.filter((person) => person.isIn).length;
}

/**
 * **The two rows, top first** — each a side (Q70), padded to the court's seats. **The side with more
 * people In is the top row; on a tie, yours.** Every mock draws it so: Karol and Zofia, both In, over
 * Ania and you (mock 3); Karol, In, and you over two who have not answered (mock 5); you and Zofia on
 * top when nobody is In (mock 6). Momentum reads first, and a card with none reads from you.
 */
export function rowsOf(
  card: Pick<DeckCard, 'sides'>,
  seatsPerSide: number,
): { readonly top: DeckRow; readonly bottom: DeckRow } {
  const yours = rowOf(card.sides.yours, true, seatsPerSide);
  const theirs = rowOf(card.sides.theirs, false, seatsPerSide);
  return inOn(card.sides.theirs) > inOn(card.sides.yours)
    ? { top: theirs, bottom: yours }
    : { top: yours, bottom: theirs };
}

/** Everybody on a card, as dealt — yours then theirs. */
export function peopleOn(card: Pick<DeckCard, 'sides'>): readonly DeckPerson[] {
  return [...card.sides.yours, ...card.sides.theirs];
}

// ---------------------------------------------------------------------------
// The ribbon, the court block and the stamp
// ---------------------------------------------------------------------------

/** What the ribbon says the card is. */
export type Ribbon =
  | { readonly kind: 'pickedForYou' }
  | { readonly kind: 'challenge'; readonly by?: string }
  | { readonly kind: 'seatOpen' };

/**
 * *Picked for you*, *Kuba challenged you* — or *The group challenged you*, once the poster withdrew
 * or can no longer be named — and a rescue's *Seat open · court booked*.
 */
export function ribbonOf(card: Pick<DeckCard, 'type' | 'challenger'>): Ribbon {
  switch (card.type) {
    case 'PICKED_FOR_YOU':
      return { kind: 'pickedForYou' };
    case 'SEAT_OPEN':
      return { kind: 'seatOpen' };
    case 'CHALLENGE': {
      const by = card.challenger?.name;
      return by === undefined ? { kind: 'challenge' } : { kind: 'challenge', by };
    }
  }
}

/** The court block's one tag. */
export type CourtTag = 'available' | 'bookItNow' | 'booked';

/**
 * **Court available** — your yes is a free vote; **Book it now** — your yes fills the game;
 * **Booked** — a rescue's court, booked already (the screens A2.3). The wire's court state, drawn.
 */
export function courtTagOf(card: Pick<DeckCard, 'court'>): CourtTag {
  return COURT_TAG[card.court];
}

const COURT_TAG: Readonly<Record<CourtState, CourtTag>> = {
  COURT_AVAILABLE: 'available',
  BOOK_IT_NOW: 'bookItNow',
  BOOKED: 'booked',
};

/**
 * **Whether a yes on this card charges at once** — and so whether it says *Pay*, on the stamp and on
 * a button (Q124): *Book it now*, or a rescue. A full game books at once at every club (ADR-0196,
 * #676), so a *Book it now* yes always does. A vote's stamp carries the price too, as *I'm in*.
 */
export function chargesAtOnce(card: Pick<DeckCard, 'type' | 'court'>): boolean {
  return card.type === 'SEAT_OPEN' || card.court === 'BOOK_IT_NOW';
}

/** Whether the reader is In on the card — never on a card the deck deals, once they said yes here. */
export function youAreIn(card: Pick<DeckCard, 'sides'>): boolean {
  return card.sides.yours.some((person) => person.isYou && person.isIn);
}

/** *You complete it* — your yes would leave no seat open, and you have not given it yet. */
export function completesIt(card: Pick<DeckCard, 'openSeatsAfterYourYes' | 'sides'>): boolean {
  return card.openSeatsAfterYourYes === 0 && !youAreIn(card);
}

/**
 * *4 people are In on this game* — only on a game dealt in versions, where the tiles show one
 * version and the count is the whole game's (the mechanics §7). `undefined` on a card dealt once.
 */
export function inAcrossVersions(
  card: Pick<DeckCard, 'versionCount' | 'inCount'>,
): number | undefined {
  return card.versionCount > 1 ? card.inCount : undefined;
}

// ---------------------------------------------------------------------------
// The countdown
// ---------------------------------------------------------------------------

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;

/** A card counts down only when its deadline is closer than this (the mechanics §5.4). */
const COUNTS_DOWN_UNDER = 24 * HOUR;

/** How long a card has, as the ribbon draws it. */
export type Countdown =
  /** A day or more: the ribbon draws nothing. */
  | { readonly kind: 'far' }
  /** *21 h 00* */
  | { readonly kind: 'hours'; readonly hours: number; readonly minutes: number }
  /** *45 min* — under an hour, and coral. */
  | { readonly kind: 'minutes'; readonly minutes: number }
  /** The deadline has passed: the card leaves, silently. */
  | { readonly kind: 'over' };

/**
 * **How long until the deadline, from the instant the deck was read** — never from a clock the
 * read did not fold against, on `durationLeft`'s rule. **It floors**: a deadline is a promise, and
 * 23 h 59 stated as *24 h* is wrong in the direction that costs somebody the game.
 */
export function countdownOf(deadline: string, readAt: number): Countdown {
  const left = Date.parse(deadline) - readAt;
  if (Number.isNaN(left) || left <= 0) return { kind: 'over' };
  if (left >= COUNTS_DOWN_UNDER) return { kind: 'far' };
  if (left < HOUR) return { kind: 'minutes', minutes: Math.floor(left / MINUTE) };
  return {
    kind: 'hours',
    hours: Math.floor(left / HOUR),
    minutes: Math.floor((left % HOUR) / MINUTE),
  };
}

/** Whether any card counts down at this instant — and so whether the deck's clock has to run. */
export function anyCountingDown(cards: readonly DeckCard[], at: number): boolean {
  return cards.some((card) => {
    const countdown = countdownOf(card.deadline, at);
    return countdown.kind === 'hours' || countdown.kind === 'minutes';
  });
}

/**
 * **The cards still standing at this instant** — a card whose deadline has passed leaves silently
 * (the screens A2.3), whether or not the server has swept it yet.
 */
export function standingCards(cards: readonly DeckCard[], readAt: number): readonly DeckCard[] {
  return cards.filter((card) => countdownOf(card.deadline, readAt).kind !== 'over');
}

/**
 * **The card a notice opened the deck for, on top** (#559; the screens A9: *the deck opens with the
 * card on top for You complete it and Challenges*) — the rest in the order they were dealt. While it
 * stands it stays there; once it is no longer dealt — answered, filled, gone — the deck is the
 * server's order again, with nothing to say about it.
 */
export function withOnTop(
  cards: readonly DeckCard[],
  proposalId: string | undefined,
): readonly DeckCard[] {
  const top = cards.find((card) => card.proposalId === proposalId);
  return top === undefined ? cards : [top, ...cards.filter((card) => card !== top)];
}

// ---------------------------------------------------------------------------
// The forecast's fold
// ---------------------------------------------------------------------------

/**
 * **Which way the bar leans** — your side's mean published Level minus theirs, a side short of a
 * seat read as if the empty seat matched its partner (the engine's own *provisional*, the server's
 * note on the forecast).
 *
 * **The fold only.** The percentage is the server's and is printed as served; the wire carries no
 * signed gap for a deck card (`DeckForecastSchema` is `pct` and `provisional`), and 7.11's bar is
 * fed an advantage rather than a percentage. So the fold is read off the Levels the tiles already
 * print — which is where it would land to within a hundredth of a Level, invisible at the bar's
 * scale. `undefined` where anybody on the card is unrated or a side is empty: the server has sent
 * no forecast either, and the bar is not drawn.
 */
export function foldOf(card: Pick<DeckCard, 'sides'>): number | undefined {
  const mean = (side: readonly DeckPerson[]): number | undefined => {
    const levels = side.map((person) => person.level);
    if (levels.length === 0 || levels.some((level) => level === undefined)) return undefined;
    const known = levels as readonly number[];
    return known.reduce((sum, level) => sum + level, 0) / known.length;
  };
  const yours = mean(card.sides.yours);
  const theirs = mean(card.sides.theirs);
  return yours === undefined || theirs === undefined ? undefined : yours - theirs;
}

// ---------------------------------------------------------------------------
// The weekly cap
// ---------------------------------------------------------------------------

/** Which of the deck's two weeks are capped, and how many games fill one. */
export interface WeekCap {
  readonly weeks: 'this' | 'next' | 'both';
  readonly booked: number;
}

/**
 * **The slim line above the deck** — *Your 2 games this week are booked — showing next week* (Q73).
 * `thisMonday` is the Monday of the week the deck was read in, on the platform's calendar; a capped
 * week that is neither this one nor the next is not the deck's fortnight and says nothing.
 */
export function weekCapOf(
  capped: readonly CappedWeek[],
  thisMonday: string,
  nextMonday: string,
): WeekCap | undefined {
  const thisWeek = capped.find((week) => week.startsOn === thisMonday);
  const nextWeek = capped.find((week) => week.startsOn === nextMonday);
  if (thisWeek !== undefined && nextWeek !== undefined) {
    return { weeks: 'both', booked: thisWeek.booked };
  }
  if (thisWeek !== undefined) return { weeks: 'this', booked: thisWeek.booked };
  if (nextWeek !== undefined) return { weeks: 'next', booked: nextWeek.booked };
  return undefined;
}

// ---------------------------------------------------------------------------
// Answering
// ---------------------------------------------------------------------------

/**
 * **The deck without one card** — the card an answer took off it, dropped from the read the moment
 * it has flown, with its segment's count and the badge following it. The next read is the server's
 * and settles both; this is what keeps the counts honest in between.
 */
export function withoutCard(deck: GroupDeck, proposalId: string): GroupDeck {
  const card = deck.cards.find((dealt) => dealt.proposalId === proposalId);
  if (card === undefined) return deck;
  return {
    ...deck,
    cards: deck.cards.filter((dealt) => dealt.proposalId !== proposalId),
    segments: deck.segments.map((segment) =>
      segment.kind === card.kind ? { ...segment, count: Math.max(0, segment.count - 1) } : segment,
    ),
    gamesBadge: card.inCount > 0 ? Math.max(0, deck.gamesBadge - 1) : deck.gamesBadge,
  };
}

/**
 * **What a refused answer does to the card** — `returns` to the deck, because the answer can be
 * given again once the reason is gone (a saved method, a read that failed), or
 * is `gone`, because the game is: over, full, already answered, or no longer one for you.
 *
 * Keyed by the refusal's code; a code this build does not know returns the card, which is the
 * answer that loses nothing.
 */
export type RefusalOutcome = 'returns' | 'gone';

const GONE: ReadonlySet<string> = new Set([
  'proposal_not_found',
  'proposal_is_over',
  'proposal_already_answered',
  'proposal_is_full',
  'no_longer_fits',
  // A rescue's (#545): the first join won, the game is off or under way, or the seat is not
  // offered to this player any more — and a booking they cannot see.
  'seat_just_taken',
  'booking_is_called_off',
  'game_has_started',
  'rescue_not_offered',
  'booking_not_found',
]);

export function refusalOutcome(code: string | undefined): RefusalOutcome {
  return code !== undefined && GONE.has(code) ? 'gone' : 'returns';
}

/**
 * **Why a rescue's seat was refused because the game, or the seat on it, is no longer there** —
 * the reasons the sheet names. Nothing was charged for any of them.
 *
 * A booked game keeps its court: a club cannot close the hour of a booked court, remove it or
 * change its sport (`court_booked_then`, `court_has_bookings`). So a game that is gone was called
 * off — at its cut-off with a seat still empty, or by its club — and the join says which.
 * `CALLED_OFF` is a server that does not say.
 */
export type RescueGoneReason =
  | 'SHORT_AT_THE_CUT_OFF'
  | 'CANCELLED_BY_THE_CLUB'
  | 'CALLED_OFF'
  | 'BOOKING_GONE'
  | 'SEAT_TAKEN'
  | 'GAME_STARTED'
  | 'NOT_OFFERED';

export interface RescueGone {
  readonly reason: RescueGoneReason;
  /** The club's own reason, on its cancel. */
  readonly clubCancelReason?: ClubCancelReason;
}

const RESCUE_GONE: ReadonlyMap<string, RescueGoneReason> = new Map([
  ['booking_is_called_off', 'CALLED_OFF'],
  ['booking_not_found', 'BOOKING_GONE'],
  ['seat_just_taken', 'SEAT_TAKEN'],
  ['game_has_started', 'GAME_STARTED'],
  ['rescue_not_offered', 'NOT_OFFERED'],
]);

/** Why the game is off, as `booking_is_called_off`'s `details.reason` says it. */
const CALLED_OFF_WHY: readonly RescueGoneReason[] = [
  'SHORT_AT_THE_CUT_OFF',
  'CANCELLED_BY_THE_CLUB',
];

const CLUB_CANCEL_REASONS: readonly ClubCancelReason[] = [
  'WEATHER',
  'REPAIR',
  'DOUBLE_BOOKING',
  'OTHER',
];

/**
 * The reason a refused rescue names, or `undefined` for a refusal the toast says. A called-off
 * game's `details` are read and never trusted: a reason this build cannot name is the plain
 * *called off*, and a club's reason it cannot name is no reason.
 */
export function rescueGoneOf(
  code: string | undefined,
  details?: Readonly<Record<string, unknown>>,
): RescueGone | undefined {
  const reason = code === undefined ? undefined : RESCUE_GONE.get(code);
  if (reason === undefined) return undefined;
  if (reason !== 'CALLED_OFF') return { reason };
  const why = CALLED_OFF_WHY.find((known) => known === details?.reason);
  if (why === undefined) return { reason };
  const club = CLUB_CANCEL_REASONS.find((known) => known === details?.club_cancel_reason);
  return why === 'CANCELLED_BY_THE_CLUB' && club !== undefined
    ? { reason: why, clubCancelReason: club }
    : { reason: why };
}

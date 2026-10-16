/**
 * **Every sentence a group's Games deck and a game's details compose from a value** — and every
 * name a control or a region is spoken by. The fixed words are `proposalsCopy.ts`, re-exported
 * here ([#553](https://github.com/Raketa02/Raketa/issues/553)).
 *
 * Two rules sit over it, the app's own:
 *
 * - **A name is said whole, and drawn cut only where a box draws.** The *vs* line and the bar's two
 *   labels are stems (`handleStem`, ADR-0171 §4) because a quarter of a card cannot hold sixty-four
 *   characters; every spoken name — a tile's, the sides', the details' title — carries the Name as
 *   the player gave it.
 * - **A counted phrase goes through `counted()`**, so *1 person is In* is never *1 people are In*.
 */

import { sportLabel } from '@/features/onboarding/types';
import { codeMessage, type AppError } from '@/shared/errors';
import { counted } from '@/shared/formatting/counted';
import { handleStem } from '@/shared/formatting/playerName';
import { formatLevel, formatPercent, formatZloty } from '@/shared/formatting/ratingFormat';
import { dayDate } from '@/shared/date/calendarDay';
import { platformClock, platformDay } from '@/shared/date/platformZone';
import { dayLabel, dayName } from '@/shared/vocabulary/availabilityPresentation';
import { balanceWord } from '@/shared/vocabulary/balancePresentation';
import type { Sport } from '@/shared/vocabulary/sport';
import type { Weekday } from '@/shared/vocabulary/week';

import {
  peopleOn,
  type Countdown,
  type CourtTag,
  type DeckCard,
  type DeckPerson,
  type DeckRow,
  type Overlap,
  type RescueGone,
  type Ribbon,
  type WeekCap,
} from '../domain/deck';
import type { PaymentDue } from '../domain/details';
import { isRescue } from '../domain/fill';
import type { Deadline, YourTime } from '../domain/home';
import type { DayRange, GameKind, ProposalStatus } from '../domain/vocabulary';
import { gameEndsAt, weekdayAt, type GameDay } from '../domain/when';

import type { FactWords } from './GameFacts';
import { HOME_GAME_COPY } from './homeCopy';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = PROPOSALS_COPY;

/** The separator every composed line here uses — the mocks' middle dot. */
const DOT = ' · ';

/** The same dot, for a component that joins two differently drawn words: *Bonarka · no free…*. */
export const LINE_JOIN = DOT;

/** How two people on one side are joined in a drawn line: *Karol + Zofia*. */
const SIDE_JOIN = ' + ';

// ---------------------------------------------------------------------------
// The switch and the lines above the deck
// ---------------------------------------------------------------------------

/** *Competitive · 7* — one side of the switch (mock 9). */
export function segmentLabel(kind: GameKind, count: number): string {
  return `${COPY.kind[kind]}${DOT}${count}`;
}

/** *Competitive, 7 games* — the same segment, spoken. */
export function segmentSpoken(kind: GameKind, count: number): string {
  return `${COPY.kind[kind]}, ${counted(count, 'game', 'games')}`;
}

/**
 * *Your 2 games this week are booked — showing next week* (Q73) — and the two cases the mock does
 * not draw: next week full while this one is not, and both.
 */
export function capLine(cap: WeekCap): string {
  const games = `Your ${counted(cap.booked, 'game', 'games')}`;
  const are = cap.booked === 1 ? 'is' : 'are';
  switch (cap.weeks) {
    case 'this':
      return `${games} this week ${are} booked — showing next week`;
    case 'next':
      return `${games} next week ${are} booked — showing this week`;
    case 'both':
      return `${games} this week and next ${are} booked`;
  }
}

// ---------------------------------------------------------------------------
// The ribbon
// ---------------------------------------------------------------------------

/** *Picked for you* · *Kuba Wiśniewski challenged you* · *The group challenged you* · a rescue's. */
export function ribbonWords(ribbon: Ribbon): string {
  switch (ribbon.kind) {
    case 'pickedForYou':
      return COPY.ribbon.pickedForYou;
    case 'seatOpen':
      return COPY.ribbon.seatOpen;
    case 'challenge':
      return ribbon.by === undefined ? COPY.ribbon.groupChallenged : `${ribbon.by} challenged you`;
  }
}

const pad = (value: number) => String(value).padStart(2, '0');

/** *21 h 00* · *45 min* — or nothing a day or more away. */
export function countdownWords(countdown: Countdown): string | undefined {
  switch (countdown.kind) {
    case 'hours':
      return `${countdown.hours} h ${pad(countdown.minutes)}`;
    case 'minutes':
      return `${countdown.minutes} min`;
    case 'far':
    case 'over':
      return undefined;
  }
}

/** *21 hours 0 minutes left* — the countdown, spoken. */
export function countdownSpoken(countdown: Countdown): string | undefined {
  switch (countdown.kind) {
    case 'hours':
      return `${counted(countdown.hours, 'hour', 'hours')} ${counted(countdown.minutes, 'minute', 'minutes')} left`;
    case 'minutes':
      return `${counted(countdown.minutes, 'minute', 'minutes')} left`;
    case 'far':
    case 'over':
      return undefined;
  }
}

// ---------------------------------------------------------------------------
// The tiles and the sides
// ---------------------------------------------------------------------------

/** A tile's name as drawn — the whole Name, cut short by the box; *You*; or the unknown's `?`. */
export function tileName(person: DeckPerson): string {
  if (person.isYou) return COPY.you;
  return person.name ?? COPY.unnamed;
}

/** A person as a drawn line names them — the stem, or *You*. */
function stem(person: DeckPerson): string {
  if (person.isYou) return COPY.you;
  return person.name === undefined ? COPY.unnamed : handleStem(person.name);
}

/** A person as a sentence names them — whole, or *you*. */
function spoken(person: DeckPerson): string {
  if (person.isYou) return 'you';
  return person.name ?? 'somebody';
}

function peopleIn(row: DeckRow): readonly DeckPerson[] {
  return row.seats.flatMap((seat) => (seat.kind === 'person' ? [seat.person] : []));
}

/**
 * *KAROL + ZOFIA VS ANIA + YOU* — the top row against the bottom one, stems joined; uppercased by
 * the line's style (Q70). An empty seat is not named.
 */
export function vsLine(top: DeckRow, bottom: DeckRow): string {
  const side = (row: DeckRow) => peopleIn(row).map(stem).join(SIDE_JOIN);
  return `${side(top)} ${COPY.versus} ${side(bottom)}`;
}

/** *Karol Tomaszewski and Zofia Bielecka against Ania Kowalska and you* — the sides, spoken. */
export function sidesSpoken(top: DeckRow, bottom: DeckRow): string {
  const side = (row: DeckRow) => peopleIn(row).map(spoken).join(' and ');
  const said = `${side(top)} against ${side(bottom)}`;
  return said.charAt(0).toUpperCase() + said.slice(1);
}

/**
 * The bar's two labels — **your side on the left**, *You* first: *You + Zofia* against
 * *Ania + Ewa* (the screens A2.3, Q70; the game screen's `barLabels` rule).
 */
export function barLabels(rows: readonly [DeckRow, DeckRow]): readonly [string, string] {
  const yours = rows.find((row) => row.yours);
  const theirs = rows.find((row) => !row.yours);
  const you = peopleIn(yours ?? { yours: true, seats: [] });
  const ordered = [...you.filter((one) => one.isYou), ...you.filter((one) => !one.isYou)];
  return [
    ordered.map(stem).join(SIDE_JOIN),
    peopleIn(theirs ?? { yours: false, seats: [] })
      .map(stem)
      .join(SIDE_JOIN),
  ];
}

/**
 * **A tile, spoken** — who, their Level, whether they are In, and where the press goes: *Karol
 * Tomaszewski, level 2,75, In. Opens their record.* Your own tile says what your yes would do.
 */
export function tileLabel(person: DeckPerson, completes: boolean): string {
  const level = person.level === undefined ? [] : [`level ${formatLevel(person.level)}`];
  if (person.isYou) {
    const paid = person.paid === true ? [COPY.paid] : [];
    return [
      COPY.you,
      ...(completes ? [COPY.youCompleteIt.toLowerCase()] : [...level, ...paid]),
    ].join(', ');
  }
  const parts = [
    person.name ?? 'Somebody',
    ...level,
    ...(person.isIn ? [COPY.inSpoken] : []),
    ...(person.paid === true ? [COPY.paid] : []),
  ];
  return parts.join(', ');
}

/** *27 zł · court booked* on the last seat, *27 zł* while more are open — under the open seat. */
export function openSeatUnder(share: string, completes: boolean): string {
  return completes ? `${share}${DOT}${COPY.courtBooked}` : share;
}

/**
 * **The seat a rescue offers you, spoken** — *Your seat: you complete it, 27 zł, court booked* —
 * or *Your seat, 27 zł* while another is open too.
 */
export function openSeatLabel(completes: boolean, share: string): string {
  return completes
    ? `Your seat: ${COPY.youCompleteIt.toLowerCase()}, ${share}, ${COPY.courtBooked}`
    : `Your seat, ${share}`;
}

/** The hint every other tile carries: the press opens the record. */
export const TILE_HINT = 'Opens their record';

/** An empty seat, spoken — a side still short of a player. */
export const EMPTY_SEAT = 'An open seat';

/** *4 people are In on this game* — a game dealt in versions (the mechanics §7). */
export function inOnGameLine(count: number): string {
  return `${counted(count, 'person is', 'people are')} In on this game`;
}

// ---------------------------------------------------------------------------
// The forecast
// ---------------------------------------------------------------------------

/** *87%, very even* — the figure and its word, which the bar's colour never says alone. */
export function forecastSpoken(pct: number, labels: readonly [string, string]): string {
  return `Balance forecast ${formatPercent(pct)}, ${balanceWord(pct).toLowerCase()}: ${labels[0]} against ${labels[1]}`;
}

// ---------------------------------------------------------------------------
// The overlap grid
// ---------------------------------------------------------------------------

function cellName(day: Weekday, range: DayRange): string {
  return `${dayName(day)} ${COPY.range[range]}`;
}

/**
 * **The grid, spoken** — the grade, where everybody is free together, where all but one are, and
 * where the game is: one element, because a listener asks the grid one question — *can we all
 * make it* — and twenty-one cells answer it one square at a time.
 */
export function overlapLabel(overlap: Overlap): string {
  const where = (shade: 'BRIGHT' | 'DIM') =>
    overlap.cells
      .filter((cell) => cell.shade === shade)
      .map((cell) => cellName(cell.day, cell.range));
  const bright = where('BRIGHT');
  const dim = where('DIM');
  return [
    COPY.grade[overlap.grade],
    bright.length === 0 ? 'nobody is free together' : `everybody free on ${bright.join(', ')}`,
    ...(dim.length === 0 ? [] : [`all but one on ${dim.join(', ')}`]),
    `the game is ${cellName(overlap.game.day, overlap.game.range)}`,
  ].join('. ');
}

// ---------------------------------------------------------------------------
// The court block
// ---------------------------------------------------------------------------

/** *Today* · *Tomorrow* · *Saturday* · *Saturday 10 Oct*. */
export function gameDayWords(day: GameDay): string {
  switch (day.kind) {
    case 'today':
      return COPY.today;
    case 'tomorrow':
      return COPY.tomorrow;
    case 'weekday':
      return dayName(day.weekday);
    case 'dated':
      return `${dayName(day.weekday)} ${dayDate(day.day)}`;
  }
}

/** The club's name, or the words for a club the read no longer names. */
export function clubName(card: Pick<DeckCard, 'club'>): string {
  return card.club.name ?? COPY.unknownClub;
}

/**
 * *Indoor* or *Outdoor* — a court's kind as the card words it (#677), or nothing where the read
 * holds none (its free courts are mixed).
 */
export function courtKindWords(indoor: boolean | undefined): 'Indoor' | 'Outdoor' | undefined {
  if (indoor === undefined) return undefined;
  return indoor ? 'Indoor' : 'Outdoor';
}

/**
 * *Saturday 16:00 · Ogrody 33* — the court block's line. Once the court is booked it follows the
 * number in lower case, *· Court 6 · indoor* (#677); before that the kind stands alone, *· Indoor*.
 */
export function courtLine(
  day: GameDay | undefined,
  card: Pick<DeckCard, 'startsAt' | 'club' | 'courtName' | 'indoor'>,
): string {
  const when = [day === undefined ? undefined : gameDayWords(day), platformClock(card.startsAt)]
    .filter((part): part is string => part !== undefined)
    .join(' ');
  const kind = courtKindWords(card.indoor);
  const kindPart =
    kind === undefined ? '' : card.courtName === undefined ? kind : kind.toLowerCase();
  return [when, clubName(card), card.courtName ?? '', kindPart]
    .filter((part) => part !== '')
    .join(DOT);
}

/** *32 zł* */
export function shareWords(card: Pick<DeckCard, 'shareGrosze'>): string {
  return formatZloty(card.shareGrosze);
}

/** The court block, spoken whole: the tag, the share, the day and the club, and the late line. */
export function courtSpoken(
  tag: CourtTag,
  day: GameDay | undefined,
  card: Pick<
    DeckCard,
    'startsAt' | 'club' | 'courtName' | 'indoor' | 'shareGrosze' | 'noFreeCancellation'
  >,
): string {
  return [
    COPY.courtTag[tag],
    shareWords(card),
    courtLine(day, card),
    ...(card.noFreeCancellation ? [COPY.noFreeCancellation] : []),
  ].join(', ');
}

// ---------------------------------------------------------------------------
// The stamps and the answers
// ---------------------------------------------------------------------------

/** Between a stamp's words and its figure — the mocks' middle dot: *I'M IN · 32 zł*. */
export const STAMP_JOIN = ' · ';

/**
 * The stamps a card is swiped under: *I'M IN* — with the price when the yes charges at once (Q72)
 * — and *NOT THIS TIME*.
 */
export function stampsFor(card: DeckCard, charges: boolean) {
  return {
    yes: charges ? { words: COPY.yes, figure: shareWords(card) } : { words: COPY.yes },
    no: { words: COPY.no },
  } as const;
}

/** *I'm in · 27 zł* — a rescue's door: the seat taken at once, the game being booked (A3.1, A4.3). */
export function seatButtonLabel(share: string): string {
  return `${COPY.yes}${DOT}${share}`;
}

/**
 * *I'm in, 27 zł held until the cut-off* — the same door aloud, saying what the share does (Q113):
 * held on the card until the club's cut-off while it is ahead, as every seat's is, and *paid now*
 * after it, when a join is taken at once (the screens A3.1, A4.3, A5.3).
 */
export function seatButtonSpoken(share: string, heldUntilTheCutOff: boolean): string {
  return `${COPY.yes}, ${share} ${heldUntilTheCutOff ? COPY.heldUntilTheCutOff : COPY.paidNow}`;
}

/** The three buttons' names — the game's, where Players names the person. */
export const ANSWER_LABELS = { pass: COPY.no, accept: COPY.yes, record: COPY.details } as const;

/**
 * **The three buttons' names for the card on top** — and on a *Seat open* card, *I'm in* says what
 * the share does, as the rescue's other doors do (`seatButtonSpoken`, Q113): held until the cut-off
 * while it is ahead, paid now after it. The card leaves the deck at its cut-off, so a card the read
 * dealt before it is a card before it.
 */
export function answerLabels(card: Pick<DeckCard, 'type' | 'shareGrosze' | 'noFreeCancellation'>): {
  readonly pass: string;
  readonly accept: string;
  readonly record: string;
} {
  if (!isRescue(card)) return ANSWER_LABELS;
  return { ...ANSWER_LABELS, accept: seatButtonSpoken(shareWords(card), !card.noFreeCancellation) };
}

/**
 * **What a refused answer says** — the route's code over the recovery sentence every screen
 * shares.
 */
export function refusalMessage(error: AppError): string {
  return codeMessage(COPY.refused, error);
}

/**
 * **What the sheet of a rescue that went says** — the reason's own line, or for the club's cancel
 * *The club cancelled this game because of the weather, so nothing was charged.*, with Home's own
 * clause for the club's reason, and none for *Other*.
 */
export function rescueGoneLine({ reason, clubCancelReason }: RescueGone): string {
  if (reason !== 'CANCELLED_BY_THE_CLUB') return COPY.rescueGone.lines[reason];
  const words = COPY.rescueGone.clubCancelled;
  const clause =
    clubCancelReason === undefined
      ? undefined
      : HOME_GAME_COPY.money.clubCancelled[clubCancelReason];
  return `${[words.opening, ...(clause === undefined ? [] : [clause])].join(' ')}, ${words.closing}`;
}

// ---------------------------------------------------------------------------
// A game's details
// ---------------------------------------------------------------------------

/** *Filling · 2 of 4 in* — the status tag while the game fills (the screens A4.2). */
export function fillingStatus(inCount: number, seats: number): string {
  return `${COPY.game.filling}${DOT}${inCount} of ${seats} in`;
}

/** *Karol Tomaszewski, Zofia Bielecka, Ania Kowalska* — the other players, the title. */
export function othersTitle(card: Pick<DeckCard, 'sides'>): string {
  return peopleOn(card)
    .filter((person) => !person.isYou)
    .map((person) => person.name ?? COPY.unnamed)
    .join(', ');
}

/**
 * **The details' status tag** — *Filling · 2 of 4 in* while the game fills, and otherwise the
 * status's own words: *Waiting for one payment*, *Booked*, or how it ended unfilled.
 */
export function detailsStatus(status: ProposalStatus, inCount: number, seats: number): string {
  return status === 'FILLING' ? fillingStatus(inCount, seats) : COPY.game.status[status];
}

/** *Padel · filling* · *Padel · waiting for one payment* — the header's second line. */
export function detailsSubline(sport: Sport, status: ProposalStatus): string {
  return `${sportLabel(sport)}${DOT}${COPY.game.statusInLine[status]}`;
}

/**
 * **The money row's words on a game still filling** — *if it fills · book by Sat 13:00* beside the
 * share while it fills; under it while one payment is awaited (Q111), *Waiting for one payment ·
 * until 14:40 · Nobody pays until it's in*; and nothing once it is booked or over: the share is the
 * share. **The payer reads their own time under it** while it runs — *Confirm your payment by 14:40*,
 * or *Fix your card by 14:40* before the cut-off (Q113) — on a game waiting for their payment, and on
 * one gone back to filling meanwhile.
 */
export function detailsShareWords(
  status: ProposalStatus,
  card: Pick<DeckCard, 'deadline'>,
  deadlineDay: Weekday | undefined,
  payment: PaymentDue = {},
): Pick<FactWords, 'aside' | 'below'> {
  const yours = payment.yours === undefined ? undefined : yourPaymentWords(payment.yours);
  switch (status) {
    case 'FILLING':
      return {
        aside: shareAside(card.deadline, deadlineDay),
        ...(yours === undefined ? {} : { below: yours }),
      };
    case 'WAITING_FOR_A_PAYMENT':
      // The payer reads their own time; everybody else, until when — never whose (Q111).
      return { below: yours ?? paymentAwaitedClauses(payment.dueBy).join(DOT) };
    case 'FILLED':
    case 'EXPIRED':
    case 'WITHDRAWN':
    case 'COURT_HOUR_LOST':
      return {};
  }
}

/** *16:00* and *until 17:00* — games are an hour (`gameEndsAt`). */
export function timeWords(startsAt: string): { readonly from: string; readonly until: string } {
  const from = platformClock(startsAt) ?? '';
  const ends = gameEndsAt(startsAt);
  const end = ends === undefined ? '' : (platformClock(ends) ?? '');
  return { from, until: `${COPY.game.until} ${end}` };
}

/**
 * The details' DAY — *Saturday* over *3 Oct*, and *· next week* once the game is a week or more
 * away, where a weekday alone would name two days (the screens A4.1: *Sunday 20 Sep · next week*).
 */
export function detailsDay(
  day: GameDay,
  startsAt: string,
): { readonly value: string; readonly aside?: string } {
  const value = day.kind === 'dated' ? dayName(day.weekday) : gameDayWords(day);
  const calendar = platformDay(startsAt);
  if (calendar === undefined) return { value };
  const date = dayDate(calendar);
  return { value, aside: day.kind === 'dated' ? `${date}${DOT}${COPY.game.nextWeek}` : date };
}

/** *Fri 16:00* — a moment a line names, on the club's calendar: a book-by, a cut-off. */
export function shortMoment(instant: string): string {
  const weekday = weekdayAt(instant);
  return [weekday === undefined ? undefined : dayLabel(weekday), platformClock(instant)]
    .filter((part): part is string => part !== undefined)
    .join(' ');
}

/**
 * *20:45* · *Sun 00:15* — **a deadline Home names**, on the club's clock: the hour alone when it
 * falls on the read's day, else the weekday with it, as *free to leave until Sun 17:00* writes it
 * (the screens A8).
 */
export function deadlineWords(deadline: Deadline): string {
  return deadline.today ? (platformClock(deadline.at) ?? '') : shortMoment(deadline.at);
}

/**
 * *Waiting for one payment · until 14:40 · Nobody pays until it's in* — **a full game waiting for
 * one player's payment** (Q110, Q111), never whose: Home's line, the details' and *It's a game!*'s
 * clauses, each whole. *until* only while the time is ahead.
 */
export function paymentAwaitedClauses(until: Deadline | undefined): readonly string[] {
  return [
    COPY.game.waitingForOnePayment,
    ...(until === undefined ? [] : [`${COPY.game.until} ${deadlineWords(until)}`]),
    COPY.game.nobodyPaysUntilItsIn,
  ];
}

/**
 * *Confirm your payment by 14:40* — **the payer's own time to pay** (Q109, Q111); *Fix your card by
 * 14:40* when it is their time to fix the card, before the club's cut-off (Q113).
 */
export function yourPaymentWords(time: YourTime): string {
  return `${COPY.game.yourTimeBy[time.window]} ${deadlineWords(time.by)}`;
}

/** *if it fills · book by Sat 13:00* — the money row's aside, off the card's deadline. */
export function shareAside(deadline: string, deadlineDay: Weekday | undefined): string {
  const day = deadlineDay === undefined ? '' : `${dayLabel(deadlineDay)} `;
  return `${COPY.game.ifItFills}${DOT}${COPY.game.bookBy} ${day}${platformClock(deadline) ?? ''}`;
}

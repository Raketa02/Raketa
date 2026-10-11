/**
 * **Home's booked games, and a booked game in detail** — the rules a card and the details are
 * drawn by ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.1, A8; the
 * mechanics §11, §14).
 *
 * Pure, and the server's folds are never re-derived: the status, *needs you*, the sides, the share,
 * whether it was paid and the cut-off are the read's (`GET /home`, `GET /bookings/{id}`, #542). What
 * is decided here is how a booked game is **drawn** — which money line a status takes, how long an
 * ended card stays on Home, which games are *new*, when the Chat door is open, and which result act
 * the details offer.
 *
 * **One clock, the read's.** Every fold here takes `now`, an instant on the server's clock — the
 * read's `read_at` moved on by however long the phone has held it — so the line that says *30 zł ·
 * free to leave until Sat 17:00* becomes *Paid · 30 zł* at that instant by itself, as the wire asks,
 * and never by this phone's idea of the time.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCard } from './deck';
import type {
  CalledOffReason,
  ClubCancelReason,
  GameKind,
  HomeStatus,
  LeavingKind,
  ShareState,
  TimeTo,
  UncountedReason,
} from './vocabulary';
import { GAME_LENGTH_MS, gameDayOf } from './when';

/**
 * *30 zł · free to leave until Sat 17:00*, *Paid · 30 zł* — **the money a booked game carries**.
 * Since Q113 the shares are held on the cards when the game fills and taken at the club's cut-off.
 */
export interface BookedMoney {
  /** Every seat's share, in grosze. */
  readonly shareGrosze: number;
  /** Every seat's share was **taken** — at the cut-off, or at once for a game booked after it. */
  readonly paid: boolean;
  /**
   * **Where the shares stand** (#637, #639): held until the cut-off, the reader's only checked
   * because a hold would not last that long, or taken. Absent while nobody's money is on the game.
   */
  readonly shareState?: ShareState;
  /** When a checked share is held — its Holding time, four days before the cut-off — while ahead. */
  readonly heldFrom?: string;
  /** When the shares are taken — the club's cut-off — or were. Present exactly with `shareState`. */
  readonly takenAt?: string;
  /**
   * The club's cut-off while it was still ahead at the read: leaving before it takes nothing — the
   * hold on the card is let go — so the line says *free to leave until* it (Q113, amending Q99).
   */
  readonly freeToLeaveUntil?: string;
  /** What everybody still in was given back — a game its club cancelled after the cut-off (#637). */
  readonly refundedGrosze?: number;
}

/**
 * **One card on Home** — a game the reader booked, from the moment it filled. The sides are the
 * deck's people, the reader's side first and the reader first on it, each with their *paid*.
 */
export interface HomeGame {
  /** The booking — the same id the game had while it filled. */
  readonly bookingId: string;
  /**
   * The ordinary Game it opened: the result and the forecast are reached by it, and the room by the
   * booking (#577). **Absent while an On request club decides** (#543) — there is no Game until it
   * says yes — and on a request it never accepted.
   */
  readonly gameId?: string;
  /** The pool it filled in — a group's id. */
  readonly groupId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
  readonly status: HomeStatus;
  /** Why it is `CALLED_OFF` — absent on every other status. */
  readonly calledOffReason?: CalledOffReason;
  /** Why the club cancelled it — present with `CANCELLED_BY_THE_CLUB` alone (#547). */
  readonly clubCancelReason?: ClubCancelReason;
  /** Why it is `UNCOUNTED` with nobody disagreeing about a score — absent otherwise. */
  readonly uncountedReason?: UncountedReason;
  /** Seats somebody left and nobody has taken yet — *1 seat open* (#544). */
  readonly openSeats: number;
  /**
   * A result to enter, a score waiting on the reader's agreement, a seat open in their game — or a
   * report of their not coming, theirs to dispute while its day runs (#560).
   */
  readonly needsYou: boolean;
  /** The court hour's start; games are an hour. */
  readonly startsAt: string;
  readonly club: DeckCard['club'];
  /** What the club calls the court — *Court 2*. Absent while an On request club decides. */
  readonly courtName?: string;
  readonly sides: DeckCard['sides'];
  readonly money: BookedMoney;
  /**
   * **When the On request club must answer** (Q98) — while the game waits for it, and only while
   * that deadline was ahead at the read. Absent on every other status, and from an older server.
   */
  readonly answerBy?: string;
  /**
   * **A full game gone back to filling before it was booked** (#624, Q106) — a player left while
   * the club decided, or a yes was taken back. *Seat open* while it fills, nobody paid; *Called off*
   * once its last moment to book passes first. Absent on every booked game, and from an older server.
   */
  readonly fillingAgain?: FillingAgain;
  /**
   * **When the payment the game waits for is due** (#625, #626; Q111) — one player's share was
   * refused, and their seat is theirs alone until then: *Waiting for one payment · until 14:40*.
   * Never whose. Present on `WAITING_FOR_A_PAYMENT` alone, and absent from an older server.
   */
  readonly paymentDueBy?: string;
  /**
   * **The reader's own refused share, and their time to pay** (#625, #626; Q111) — *Confirm your
   * payment by 14:40*, beside their *To confirm* row — on a game waiting for it, or one gone back to
   * filling meanwhile. Absent for everybody else, from the moment it runs out, and from an older
   * server.
   */
  readonly yourPaymentDueBy?: string;
  /**
   * **What that time is for** (#638; Q113) — to fix the card, refused before the club's cut-off
   * where nothing is taken (*Fix your card by 14:40*), or to pay, after it. Only the payer's words
   * change by it. Absent while no time runs, and from an older server.
   */
  readonly timeTo?: TimeTo;
}

/** How a full game gone back to filling is booked once it is full again — the line's last clause. */
export interface FillingAgain {
  /** *Kazimierz Padel is asked again when it's full* — an On request club; else *books when it's full*. */
  readonly clubConfirms: boolean;
}

/** **Home** — the reader's booked games, soonest first, and how many need them. */
export interface Home {
  /** The instant every status and money line was folded against, on the server's clock. */
  readonly readAt: string;
  /** Home's badge: the cards that need the reader, and every payment they have to confirm. */
  readonly needingYou: number;
  readonly games: readonly HomeGame[];
}

/** *Show at the desk* — the reader's own code for the game, on its day. */
export interface CheckIn {
  /** Six characters to type when the camera will not read. */
  readonly shortCode: string;
  /** What the QR code encodes. */
  readonly qrPayload: string;
}

/**
 * **What *Leave the game* would cost now** (the mechanics §13; #544) — the line under the button and
 * the sheet in front of it. Absent where there is no button: once the hour has come, on a game that
 * is over, and for a reader not on the game.
 *
 * Before the cut-off nothing is taken (Q113). After it the read quotes what comes back if somebody
 * takes the seat, to the grosz, or nothing while the fee kept is not known (#641).
 */
export interface Leaving {
  readonly kind: LeavingKind;
  /**
   * **Before the cut-off, whether leaving lets a hold on the card go** (Q113) — while the reader's
   * share is held; not while it is only checked, which holds nothing yet. Folded on the read's
   * clock (`leavingAt`); the read's own `leaving` carries none.
   */
  readonly letsAHoldGo?: boolean;
  /**
   * **After the cut-off, the read's exact quote** (#641, #644) — absent while the fee kept on the
   * payment is not yet known, where the words give no figure and no clause, never an estimate.
   */
  readonly lateRefund?: LateRefund;
}

/**
 * *If someone takes your seat, you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment)*
 * — **what a leaver after the cut-off gets back if somebody takes the seat** (Q113): the share less
 * exactly what was kept on the reader's own payment, both the server's to the grosz. The two
 * together are the payment.
 */
export interface LateRefund {
  readonly backGrosze: number;
  readonly keptGrosze: number;
}

/** **The payment a late refund is less of** — *40 zł*: what comes back and what was kept, together. */
export function paymentOf(refund: LateRefund): number {
  return refund.backGrosze + refund.keptGrosze;
}

/**
 * **The open seat, offered to a reader not on the game** (#545) — a *Seat open* card or a *Seats to
 * fill* row opened: they stand in the seat that opened first, unpaid (*You?*), and *I'm in* takes it.
 */
export interface RescueOffer {
  /** When the seat leaves the board — the club's cut-off while it is ahead, then the start. */
  readonly deadline: string;
  /** *fills by Fri 16:00* — the game is off unless its seats are taken by then. */
  readonly fillsByTheCutOff: boolean;
}

/** What leaving costs while an On request club decides — nobody has paid anything (#543). */
export const LEAVING_WHILE_WAITING: Leaving = { kind: 'WHILE_WAITING_FOR_THE_CLUB' };

/** **A booked game in detail** (the screens A4.1) — the card's facts, and what only the details draw. */
export interface BookedGame extends Omit<HomeGame, 'club'> {
  /** The instant the status and the money were folded against. */
  readonly readAt: string;
  /** An hour after the start: TIME's *until*. */
  readonly endsAt: string;
  /** WHERE: the club, and how far it is from the reader — omitted with no Location area. */
  readonly where: DeckCard['club'] & { readonly distanceKm?: number };
  /** Draw the balance forecast — the Game's own pairing read — while the full game awaits its entry. */
  readonly showsForecast: boolean;
  /** On the game's day, the reader's code to show at the desk; absent on every other day. */
  readonly checkIn?: CheckIn;
  /** *Leave the game*'s cost now — absent where there is no button. */
  readonly leaving?: Leaving;
  /** The reader is not on the game, and its open seat is offered to them: a rescue seen from outside. */
  readonly rescue?: RescueOffer;
}

// ---------------------------------------------------------------------------
// The money line
// ---------------------------------------------------------------------------

/**
 * **The line under a Home card** (the mechanics §14.1's table) — or nothing, which is every result
 * state's: *unchanged from today*, and today's cards carry no money.
 *
 * - `booked` — *30 zł · free to leave until Sat 17:00* while the cut-off is ahead, the share held
 *   or only checked; *Paid · 30 zł* once it is taken (Q113).
 * - `waiting` — *Bonarka answers by 20:45 · Nobody pays until it confirms* while the club's
 *   deadline is ahead (Q98), then *Nobody pays until Bonarka confirms*.
 * - `seatOpen` — *1 seat open*, and *fills by Sat 17:00 or the game is off* before the cut-off;
 *   *offered to others · the game goes ahead* after it.
 * - `fillingAgain` — a full game gone back to filling (Q106): *1 seat open*, *Kazimierz Padel is
 *   asked again when it's full* or *books when it's full*, and *nobody paid*. The club is carried
 *   for the first.
 * - `paymentAwaited` — one player's payment awaited (Q111): *Waiting for one payment · until 14:40
 *   · Nobody pays until it's in*, the time while it is ahead. Never whose.
 * - `yourPayment` — the same game, or one gone back to filling meanwhile, read by the payer while
 *   their time runs: *Confirm your payment by 14:40*, or before the cut-off *Fix your card by 14:40*
 *   (`window`, Q113). So is a booked game whose holding was refused (#639): it stays booked, and
 *   only its player's card says so.
 * - `calledOff` — why, and *refunded 30 zł* when the shares came back; when none did, *nothing was
 *   taken* or *nobody paid*, by the reason. The club is carried for the reasons that are the club's.
 * - `seatEmpty` — *Uncounted* because its hour came with a seat still open: no Level moved.
 * - `noShow` — *Uncounted* because somebody who came marked a player who did not (#560): to that
 *   player, while they may still say they were there (`yours`, the read's *needs you*), that they
 *   were marked; to everybody else, that somebody didn't come.
 */
export type MoneyLine =
  | {
      readonly kind: 'booked';
      readonly shareGrosze: number;
      /** Taken, at `now`. */
      readonly paid: boolean;
      /** The club's cut-off while the share is not yet taken and it is still ahead of `now`. */
      readonly freeToLeaveUntil?: string;
    }
  | { readonly kind: 'waiting'; readonly club?: string; readonly answerBy?: AnswerBy }
  | { readonly kind: 'seatOpen'; readonly seats: number; readonly fillsBy?: string }
  | {
      readonly kind: 'fillingAgain';
      readonly seats: number;
      readonly club?: string;
      readonly clubConfirms: boolean;
    }
  | { readonly kind: 'paymentAwaited'; readonly until?: Deadline }
  | ({ readonly kind: 'yourPayment' } & YourTime)
  | {
      readonly kind: 'calledOff';
      readonly reason?: CalledOffReason;
      /** The club's own reason, with `CANCELLED_BY_THE_CLUB` (#547). */
      readonly clubCancelReason?: ClubCancelReason;
      readonly club?: string;
      readonly refundedGrosze?: number;
    }
  | { readonly kind: 'seatEmpty' }
  | { readonly kind: 'noShow'; readonly yours: boolean };

/**
 * **The cut-off, while it is still ahead of `now`** — the instant *free to leave until …* leaves the
 * card's line, and *fills by …* a seat open's.
 */
export function cutOffAhead(money: BookedMoney, now: number): string | undefined {
  const until = money.freeToLeaveUntil;
  return until !== undefined && Date.parse(until) > now ? until : undefined;
}

/**
 * **Where the reader's share stands at `now`** (Q113; the mechanics §12.2) — the details' money row
 * says it: *held on your card · taken Wed 19:00*, *held from Sat 19:00 · taken Wed 19:00*, or paid.
 */
export type ShareAt =
  | { readonly kind: 'held'; readonly takenAt: string }
  | { readonly kind: 'checked'; readonly heldFrom: string; readonly takenAt: string }
  | { readonly kind: 'taken' };

/**
 * **The read's share, folded on the read's clock** — the wire's state switches by itself at the two
 * instants it names, and so does this: a checked share is held from `heldFrom`, and every share is
 * taken at `takenAt`, the cut-off, where the server's own `paid` turns too. Nothing for a share the
 * read gives no state, which is no money on the game.
 */
export function shareAt(money: BookedMoney, now: number): ShareAt | undefined {
  const { shareState, takenAt, heldFrom } = money;
  if (money.paid || shareState === 'TAKEN') return { kind: 'taken' };
  if (shareState === undefined || takenAt === undefined) return undefined;
  if (!(Date.parse(takenAt) > now)) return { kind: 'taken' };
  if (shareState === 'CHECKED' && heldFrom !== undefined && Date.parse(heldFrom) > now) {
    return { kind: 'checked', heldFrom, takenAt };
  }
  return { kind: 'held', takenAt };
}

/**
 * **A deadline Home names** — the club's to say yes (*Bonarka answers by 20:45*, Q98), a time to pay
 * (*until 14:40*, *Confirm your payment by 14:40*, Q111) — and whether it falls on `now`'s day on the
 * club's calendar: the hour alone then, the weekday with it on any other day (the screens A8).
 */
export interface Deadline {
  readonly at: string;
  readonly today: boolean;
}

/** *Bonarka answers by 20:45* — the club's deadline to say yes (Q98). */
export type AnswerBy = Deadline;

/**
 * **The window a refused card's words are in** (#638; Q113) — the one the read names while the time
 * runs: `FIX_THE_CARD` before the club's cut-off, where nothing is taken and nobody is asked to pay,
 * `PAY` after it. `UNNAMED` once the time has gone — the read names none then, and a seat taken back
 * is held before the cut-off and paid after it — where no time was given, and from an older server:
 * the words then say *confirm*, never *pay* nor *fix*.
 */
export type PaymentWindow = TimeTo | 'UNNAMED';

/**
 * **The payer's own time, and its window** — *Fix your card by 14:40* or *Confirm your payment by
 * 14:40*: what Home's line, the details' row, a *TO CONFIRM* row and the sheet name.
 */
export interface YourTime {
  readonly by: Deadline;
  readonly window: PaymentWindow;
}

/** The window at `now`: the read's, while `by` is ahead of it. */
export function paymentWindowAt(
  by: string | undefined,
  timeTo: TimeTo | undefined,
  now: number,
): PaymentWindow {
  return timeTo === undefined || deadlineAhead(by, now) === undefined ? 'UNNAMED' : timeTo;
}

/**
 * **Whose seat a refused card's time keeps** — the player's own, on a game that filled or was booked
 * (*to keep your seat*), or a rescue's, kept for them alone to take and not yet theirs (*to take the
 * seat*, #640): the notice's and the email's two endings.
 */
export type SeatAtStake = 'yours' | 'aRescue';

/**
 * **The seat the details' money row says is at stake**, beside the payer's own time — where the
 * status tag does not say it: a rescue's, seen from outside (#640), and the player's own on a game
 * booked already, whose holding was refused and whose tag still says *Booked* (#639; the screens
 * A4.1). Nothing on a game not booked yet: its tag says it waits.
 */
export function stakeOnTheDetails(
  game: Pick<BookedGame, 'rescue' | 'status' | 'fillingAgain'>,
): SeatAtStake | undefined {
  if (game.rescue !== undefined) return 'aRescue';
  return courtIsGiven(game) ? 'yours' : undefined;
}

/** **A deadline as Home writes it, from `now`** — whether it is still ahead or not. */
export function deadlineOf(at: string, now: number): Deadline {
  return { at, today: gameDayOf(at, now)?.kind === 'today' };
}

/**
 * **A deadline, while it is still ahead of `now`** — the instant a clause naming it leaves a card's
 * line and either details' money row, as *free to leave until* leaves at the cut-off. Nothing for
 * no deadline, or a value that is not an instant.
 */
export function deadlineAhead(at: string | undefined, now: number): Deadline | undefined {
  return at === undefined || !(Date.parse(at) > now) ? undefined : deadlineOf(at, now);
}

/**
 * **The club's deadline, while it is still ahead of `now`** — the instant *answers by …* leaves a
 * card's line and either details' money row, as *free to leave until* leaves at the cut-off. Past
 * it the club can no longer say yes, and the server's timeout calls the game off within about
 * thirty seconds; until it has, the line reads only *Nobody pays until Bonarka confirms*.
 */
export function answerByAhead(
  game: { readonly answerBy?: string },
  now: number,
): AnswerBy | undefined {
  return deadlineAhead(game.answerBy, now);
}

/**
 * **Whether the game's line carries a clause that runs out by itself** — *free to leave until* and
 * *fills by* at the cut-off, *held from* at a checked share's holding time, *answers by* at the
 * club's deadline, *until* and *Confirm your payment by* at a time to pay. While one is there the
 * read's clock ticks (`useReadClock`), so the clause leaves the screen at that instant rather than
 * at the next read.
 */
export function lineCanRunOut(
  game: Pick<HomeGame, 'money' | 'answerBy' | 'paymentDueBy' | 'yourPaymentDueBy'>,
): boolean {
  return (
    game.money.freeToLeaveUntil !== undefined ||
    game.money.heldFrom !== undefined ||
    game.answerBy !== undefined ||
    game.paymentDueBy !== undefined ||
    game.yourPaymentDueBy !== undefined
  );
}

/**
 * The line a card takes at `now`. **Nothing here is counted**: how many seats are open, why a game
 * is off and what came back are the read's (#544), and only the clauses that run out — at the
 * cut-off, at the club's deadline and at a time to pay — are folded on the clock.
 *
 * **The payer reads their own time first** (Q111): on a game waiting for their payment, or gone back
 * to filling meanwhile, *Confirm your payment by 14:40* while it runs — the status tag still says
 * which of the two it is — and on a booked game whose holding was refused, *Fix your card by 14:40*
 * (#639, Q113), the tag still *Booked*. The read names the time to its payer alone, so whichever the
 * status, it is theirs. From the deadline on, the line is everybody's.
 */
export function moneyLineOf(
  game: Pick<
    HomeGame,
    | 'status'
    | 'money'
    | 'club'
    | 'openSeats'
    | 'calledOffReason'
    | 'clubCancelReason'
    | 'uncountedReason'
    | 'needsYou'
    | 'answerBy'
    | 'fillingAgain'
    | 'paymentDueBy'
    | 'yourPaymentDueBy'
    | 'timeTo'
  >,
  now: number,
): MoneyLine | undefined {
  const { money } = game;
  const club = game.club.name === undefined ? {} : { club: game.club.name };
  const yours = deadlineAhead(game.yourPaymentDueBy, now);
  if (yours !== undefined) {
    return {
      kind: 'yourPayment',
      by: yours,
      window: paymentWindowAt(game.yourPaymentDueBy, game.timeTo, now),
    };
  }
  switch (game.status) {
    case 'BOOKED': {
      if (shareAt(money, now)?.kind === 'taken') {
        return { kind: 'booked', shareGrosze: money.shareGrosze, paid: true };
      }
      const until = cutOffAhead(money, now);
      return {
        kind: 'booked',
        shareGrosze: money.shareGrosze,
        paid: false,
        ...(until === undefined ? {} : { freeToLeaveUntil: until }),
      };
    }
    case 'WAITING_FOR_THE_CLUB': {
      const by = answerByAhead(game, now);
      return { kind: 'waiting', ...club, ...(by === undefined ? {} : { answerBy: by }) };
    }
    case 'WAITING_FOR_A_PAYMENT': {
      const until = deadlineAhead(game.paymentDueBy, now);
      return { kind: 'paymentAwaited', ...(until === undefined ? {} : { until }) };
    }
    case 'SEAT_OPEN': {
      // Gone back to filling (Q106): nobody paid, so there is no cut-off to fill by.
      if (game.fillingAgain !== undefined) {
        return {
          kind: 'fillingAgain',
          seats: game.openSeats,
          ...club,
          clubConfirms: game.fillingAgain.clubConfirms,
        };
      }
      const until = cutOffAhead(money, now);
      return {
        kind: 'seatOpen',
        seats: game.openSeats,
        ...(until === undefined ? {} : { fillsBy: until }),
      };
    }
    case 'CALLED_OFF':
      return {
        kind: 'calledOff',
        ...(game.calledOffReason === undefined ? {} : { reason: game.calledOffReason }),
        ...(game.clubCancelReason === undefined ? {} : { clubCancelReason: game.clubCancelReason }),
        ...club,
        ...(money.refundedGrosze === undefined ? {} : { refundedGrosze: money.refundedGrosze }),
      };
    case 'UNCOUNTED':
      switch (game.uncountedReason) {
        case 'SEAT_EMPTY':
          return { kind: 'seatEmpty' };
        case 'NO_SHOW':
          return { kind: 'noShow', yours: youMayDispute(game) };
        case undefined:
          return undefined;
      }
    case 'NEEDS_RESULT':
    case 'CONFIRM_THE_RESULT':
    case 'COUNTED':
    case 'NEVER_PLAYED':
      return undefined;
  }
}

// ---------------------------------------------------------------------------
// Which cards Home draws
// ---------------------------------------------------------------------------

/** How long an ended game keeps its card — **a day, the Classic rail's number** (`plans`). */
export const ENDED_HOME_SHELF_LIFE_MS = 24 * 60 * 60 * 1000;

/**
 * **A status as Home draws it** — the wire's, with one more: a full game **gone back to filling**
 * (#624, Q106) reads *Seat open* as a booked game a player left does, and is another thing under
 * it — nobody paid, no Game, no room and no court.
 */
type Stage = HomeStatus | 'FILLING_AGAIN';

function stageOf(game: Pick<HomeGame, 'status' | 'fillingAgain'>): Stage {
  return game.status === 'SEAT_OPEN' && game.fillingAgain !== undefined
    ? 'FILLING_AGAIN'
    : game.status;
}

/**
 * **What each stage says about a booked game** — one table, so a tenth status is one row and every
 * rule below answers for it at once:
 *
 * - `ended` — one of the four ends: a game that will not be played, or whose result is settled.
 * - `fresh` — filled and not yet past its hour, which is when a game can be *new*.
 * - `room` — the game can have a room. **Its own life decides past that** (the mechanics §14.3): a
 *   booked game's room opens with the booking and closes as today — 48 hours after *we played*,
 *   when the result window closes, or when the game is called off — so the door is drawn while the
 *   join finds the room, and a counted game's room outlives the result by a day or two. A game
 *   waiting for the club has none yet, and a called-off one none any more.
 * - `court` — the court is given: an On request club gives it with its yes (A4.2: *no court
 *   number* while waiting).
 *
 * **A game waiting for one payment** (Q111) filled, so it is *new* until opened — the four are
 * matched — but nobody paid and nothing is booked: no room and no court until the payment is in, at
 * either kind of club (the wire gives none while it waits).
 *
 * **A game gone back to filling is none of the four**: still live, not *new* — the tag marks a game
 * that filled, and this one is not full any more — and, like a game waiting for its club, no room
 * and no court until it is booked.
 */
const STATUS: Readonly<
  Record<
    Stage,
    {
      readonly ended: boolean;
      readonly fresh: boolean;
      readonly room: boolean;
      readonly court: boolean;
    }
  >
> = {
  WAITING_FOR_THE_CLUB: { ended: false, fresh: true, room: false, court: false },
  WAITING_FOR_A_PAYMENT: { ended: false, fresh: true, room: false, court: false },
  BOOKED: { ended: false, fresh: true, room: true, court: true },
  SEAT_OPEN: { ended: false, fresh: true, room: true, court: true },
  NEEDS_RESULT: { ended: false, fresh: false, room: true, court: true },
  CONFIRM_THE_RESULT: { ended: false, fresh: false, room: true, court: true },
  COUNTED: { ended: true, fresh: false, room: true, court: true },
  UNCOUNTED: { ended: true, fresh: false, room: true, court: true },
  NEVER_PLAYED: { ended: true, fresh: false, room: true, court: true },
  CALLED_OFF: { ended: true, fresh: false, room: false, court: true },
  FILLING_AGAIN: { ended: false, fresh: false, room: false, court: false },
};

/**
 * **Whether a game is on Home at `now`** — every live game, and an ended one until a day after its
 * hour. **The server sends only what Home draws** (#613): live games, games that ended less than a
 * day after their hour, and any game that needs the reader. So this rule is not the shelf: it
 * catches a card that crosses the line while Home is on screen, at that instant rather than at the
 * next read. **One card it still drops that the server sends**: an uncounted game whose reader may
 * dispute a report of their not coming outlives its day by up to another (#560), and is on the
 * badge all that time — what the phone draws for it is story S-33's.
 *
 * **Measured from the hour's end, the one instant every ending has**: the wire dates no ending of a
 * booking, so a game called off days ahead stays until a day after the hour it was for — the player
 * who looks at Home that evening finds why there is no game — and a result settled later than a day
 * after the hour is not drawn, which is the Classic rail's own cost for a score counted by silence.
 */
export function onHome(
  game: Pick<HomeGame, 'status' | 'fillingAgain' | 'startsAt'>,
  now: number,
): boolean {
  if (!STATUS[stageOf(game)].ended) return true;
  const hourEnds = Date.parse(game.startsAt) + GAME_LENGTH_MS;
  return Number.isNaN(hourEnds) || now - hourEnds < ENDED_HOME_SHELF_LIFE_MS;
}

/**
 * **Marked *new* until opened** (the mechanics §11.4; the screens A8) — a game that filled since you
 * last looked, while its details have never been opened on this phone and its hour is still ahead.
 * A game past its hour is asking for a result or is over, and *new* is not what it is any more.
 *
 * `opened` is `undefined` while the phone is being read, and **nothing is new until it has said**:
 * a *new* tag flashing on every card for the frame before the list arrives is the noise the tag is
 * meant to cut through.
 */
export function isNew(
  game: Pick<HomeGame, 'bookingId' | 'status' | 'fillingAgain'>,
  opened: ReadonlySet<string> | undefined,
): boolean {
  return opened !== undefined && STATUS[stageOf(game)].fresh && !opened.has(game.bookingId);
}

/**
 * **The opened games, as the phone kept them** — a JSON list of booking ids, and nothing for a value
 * that is not one: a store this build cannot read is a store that kept nothing (ADR-0188 §4).
 */
export function openedFrom(saved: string | undefined): readonly string[] {
  if (saved === undefined) return [];
  try {
    const parsed: unknown = JSON.parse(saved);
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === 'string') : [];
  } catch {
    return [];
  }
}

/**
 * **What the phone keeps once a game is opened** — that game, and every earlier one Home still
 * holds. The list is pruned to Home's own read, so it is never longer than the games a player has;
 * with no read of Home to prune by, nothing is dropped.
 */
export function openedToKeep(
  kept: readonly string[],
  opened: string,
  onHomeNow: readonly string[] | undefined,
): readonly string[] {
  const still = onHomeNow === undefined ? kept : kept.filter((id) => onHomeNow.includes(id));
  return still.includes(opened) ? still : [...still, opened];
}

// ---------------------------------------------------------------------------
// The details
// ---------------------------------------------------------------------------

/**
 * **Whether the game can have a room** — the Chat door's status half (the mechanics §14.2, §14.3);
 * the other half is the join finding the room, whose own life closes it as today (`STATUS`).
 */
export function chatIsOpen(game: Pick<HomeGame, 'status' | 'fillingAgain'>): boolean {
  return STATUS[stageOf(game)].room;
}

/**
 * **What *Leave the game* costs at `now`** (Q113, the mechanics §13) — the read's, folded on the
 * read's clock as the money row is: before the cut-off whether it lets a hold on the card go (while
 * the reader's share is held, and not while it is only checked, which holds nothing until its holding
 * time), and **after the cut-off from the instant the share is taken**, as the server will say once
 * read again. Nothing where there is no button.
 */
export function leavingAt(
  game: Pick<BookedGame, 'leaving' | 'money'>,
  now: number,
): Leaving | undefined {
  const { leaving } = game;
  if (leaving?.kind !== 'BEFORE_THE_CUT_OFF') return leaving;
  const share = shareAt(game.money, now)?.kind;
  return share === 'taken'
    ? { kind: 'AFTER_THE_CUT_OFF' }
    : { ...leaving, letsAHoldGo: share === 'held' };
}

/**
 * ***You complete it* on a rescue seen from outside** — the reader's yes takes the last open seat,
 * the card's own rule (A2.3); *You?* while more are open.
 */
export function completesTheRescue(game: Pick<BookedGame, 'rescue' | 'openSeats'>): boolean {
  return game.rescue !== undefined && game.openSeats === 1;
}

/**
 * **A full game gone back to filling, while it fills** (Q106) — whose way out is a game still
 * filling's, *Withdraw*. Not once it is called off: the read keeps the mark on that game, and
 * there is nothing left to withdraw from.
 */
export function isFillingAgain(game: Pick<HomeGame, 'status' | 'fillingAgain'>): boolean {
  return stageOf(game) === 'FILLING_AGAIN';
}

/** **Whether the court is given** — WHERE names it once the club has said yes (A4.2). */
export function courtIsGiven(game: Pick<HomeGame, 'status' | 'fillingAgain'>): boolean {
  return STATUS[stageOf(game)].court;
}

/**
 * The result act the details lead to — today's game screen, which tells and agrees a result, and
 * where a player marked as not coming says they were there (#560).
 */
export type ResultAct = 'we-played' | 'confirm' | 'dispute';

/**
 * **What the details offer once the hour has come** — *We played* while nobody has said, *Confirm
 * the result* once a score is on the table, and to a player marked as not coming, while their day
 * runs, the door to saying they were there — or nothing. The result states are unchanged from
 * today (§14.1), so the act is today's screen's; the details are only the door to it.
 */
export function resultActOf(
  game: Pick<HomeGame, 'status' | 'uncountedReason' | 'needsYou'>,
): ResultAct | undefined {
  if (game.status === 'NEEDS_RESULT') return 'we-played';
  if (game.status === 'CONFIRM_THE_RESULT') return 'confirm';
  return youMayDispute(game) ? 'dispute' : undefined;
}

/**
 * **The reader was marked as not coming, and their day to answer runs** (#560) — the read's *needs
 * you* on a game uncounted because somebody didn't come: on an uncounted game nobody disagreed
 * about, a report waiting on the reader is the only thing that needs them. Home's line says it and
 * the details' door opens on it.
 */
function youMayDispute(game: Pick<HomeGame, 'status' | 'uncountedReason' | 'needsYou'>): boolean {
  return game.status === 'UNCOUNTED' && game.uncountedReason === 'NO_SHOW' && game.needsYou;
}

/**
 * **Who the club's desk checked in** — by id, as `games`' result screen is handed them: a player
 * checked in can never be marked as not coming (#560; the mechanics §15.1).
 */
export function checkedInOn(game: Pick<HomeGame, 'sides'>): readonly string[] {
  return [...game.sides.yours, ...game.sides.theirs].flatMap((person) =>
    person.checkedIn === true ? [person.playerId] : [],
  );
}

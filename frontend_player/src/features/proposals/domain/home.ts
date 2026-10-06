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
 * read's `read_at` moved on by however long the phone has held it — so the line that says *free to
 * leave until Sat 17:00* switches at that instant by itself, as the wire asks, and never by this
 * phone's idea of the time.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCard } from './deck';
import type {
  CalledOffReason,
  ClubCancelReason,
  GameKind,
  HomeStatus,
  LeavingKind,
  UncountedReason,
} from './vocabulary';
import { GAME_LENGTH_MS } from './when';

/** *Paid · 30 zł · free to leave until Sat 17:00* — the money a booked game carries. */
export interface BookedMoney {
  /** Every seat's share, in grosze. */
  readonly shareGrosze: number;
  /** Every seat's share was taken. */
  readonly paid: boolean;
  /** The club's cut-off while it was still ahead at the read — leaving before it is refunded. */
  readonly freeToLeaveUntil?: string;
  /** What everybody still in was given back — a game called off at its cut-off (#544). */
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
 */
export interface Leaving {
  readonly kind: LeavingKind;
  /** What comes back — the share less the card fee; nought when nobody paid. */
  readonly refundGrosze: number;
  /** The card fee that isn't returned — the provider's standard price, an estimate. */
  readonly cardFeeGrosze: number;
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
export const LEAVING_WHILE_WAITING: Leaving = {
  kind: 'WHILE_WAITING_FOR_THE_CLUB',
  refundGrosze: 0,
  cardFeeGrosze: 0,
};

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
 * - `booked` — *Paid · 30 zł*, with *free to leave until Sat 17:00* while the cut-off is ahead.
 * - `waiting` — *Nobody pays until Bonarka confirms*.
 * - `seatOpen` — *1 seat open*, and *fills by Sat 17:00 or the game is off* before the cut-off;
 *   *offered to others · the game goes ahead* after it.
 * - `calledOff` — why, and *refunded 30 zł* when the shares came back, *nobody paid* when none was
 *   taken. The club is carried for the two reasons that are the club's.
 * - `seatEmpty` — *Uncounted* because its hour came with a seat still open: no Level moved.
 * - `noShow` — *Uncounted* because somebody who came marked a player who did not (#560): to that
 *   player, while they may still say they were there (`yours`, the read's *needs you*), that they
 *   were marked; to everybody else, that somebody didn't come.
 */
export type MoneyLine =
  | {
      readonly kind: 'booked';
      readonly shareGrosze: number;
      readonly paid: boolean;
      readonly freeToLeaveUntil?: string;
    }
  | { readonly kind: 'waiting'; readonly club?: string }
  | { readonly kind: 'seatOpen'; readonly seats: number; readonly fillsBy?: string }
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
 * **The cut-off, while it is still ahead of `now`** — the instant *free to leave until …* leaves
 * the card's line and the details' money row, both off this one fold.
 */
export function cutOffAhead(money: BookedMoney, now: number): string | undefined {
  const until = money.freeToLeaveUntil;
  return until !== undefined && Date.parse(until) > now ? until : undefined;
}

/**
 * The line a card takes at `now`. **Nothing here is counted**: how many seats are open, why a game
 * is off and what came back are the read's (#544), and only the clause that runs out at the
 * cut-off is folded on the clock.
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
  >,
  now: number,
): MoneyLine | undefined {
  const { money } = game;
  const club = game.club.name === undefined ? {} : { club: game.club.name };
  switch (game.status) {
    case 'BOOKED': {
      const until = cutOffAhead(money, now);
      return {
        kind: 'booked',
        shareGrosze: money.shareGrosze,
        paid: money.paid,
        ...(until === undefined ? {} : { freeToLeaveUntil: until }),
      };
    }
    case 'WAITING_FOR_THE_CLUB':
      return { kind: 'waiting', ...club };
    case 'SEAT_OPEN': {
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
 * **What each status says about a booked game** — one table, so a tenth status is one row and every
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
 */
const STATUS: Readonly<
  Record<
    HomeStatus,
    {
      readonly ended: boolean;
      readonly fresh: boolean;
      readonly room: boolean;
      readonly court: boolean;
    }
  >
> = {
  WAITING_FOR_THE_CLUB: { ended: false, fresh: true, room: false, court: false },
  BOOKED: { ended: false, fresh: true, room: true, court: true },
  SEAT_OPEN: { ended: false, fresh: true, room: true, court: true },
  NEEDS_RESULT: { ended: false, fresh: false, room: true, court: true },
  CONFIRM_THE_RESULT: { ended: false, fresh: false, room: true, court: true },
  COUNTED: { ended: true, fresh: false, room: true, court: true },
  UNCOUNTED: { ended: true, fresh: false, room: true, court: true },
  NEVER_PLAYED: { ended: true, fresh: false, room: true, court: true },
  CALLED_OFF: { ended: true, fresh: false, room: false, court: true },
};

/**
 * **Whether a game is on Home at `now`** — every live game, and an ended one until a day after its
 * hour. Home returns every booking ever (#542, call 2), so the shelf is the client's, as `GET /games`'
 * is the Classic rail's.
 *
 * **Measured from the hour's end, the one instant every ending has**: the wire dates no ending of a
 * booking, so a game called off days ahead stays until a day after the hour it was for — the player
 * who looks at Home that evening finds why there is no game — and a result settled later than a day
 * after the hour is not drawn, which is the Classic rail's own cost for a score counted by silence.
 */
export function onHome(game: Pick<HomeGame, 'status' | 'startsAt'>, now: number): boolean {
  if (!STATUS[game.status].ended) return true;
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
  game: Pick<HomeGame, 'bookingId' | 'status'>,
  opened: ReadonlySet<string> | undefined,
): boolean {
  return opened !== undefined && STATUS[game.status].fresh && !opened.has(game.bookingId);
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
export function chatIsOpen(status: HomeStatus): boolean {
  return STATUS[status].room;
}

/**
 * ***You complete it* on a rescue seen from outside** — the reader's yes takes the last open seat,
 * the card's own rule (A2.3); *You?* while more are open.
 */
export function completesTheRescue(game: Pick<BookedGame, 'rescue' | 'openSeats'>): boolean {
  return game.rescue !== undefined && game.openSeats === 1;
}

/** **Whether the court is given** — WHERE names it once the club has said yes (A4.2). */
export function courtIsGiven(status: HomeStatus): boolean {
  return STATUS[status].court;
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

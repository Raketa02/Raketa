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
import type { GameKind, HomeStatus } from './vocabulary';
import { GAME_LENGTH_MS } from './when';

/** *Paid · 30 zł · free to leave until Sat 17:00* — the money a booked game carries. */
export interface BookedMoney {
  /** Every seat's share, in grosze. */
  readonly shareGrosze: number;
  /** Every seat's share was taken. */
  readonly paid: boolean;
  /** The club's cut-off while it was still ahead at the read — leaving before it is refunded. */
  readonly freeToLeaveUntil?: string;
}

/**
 * **One card on Home** — a game the reader booked, from the moment it filled. The sides are the
 * deck's people, the reader's side first and the reader first on it, each with their *paid*.
 */
export interface HomeGame {
  /** The booking — the same id the game had while it filled. */
  readonly bookingId: string;
  /** The ordinary Game it opened: the result, the forecast and the room are reached by it. */
  readonly gameId: string;
  /** The pool it filled in — a group's id. */
  readonly groupId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
  readonly status: HomeStatus;
  /** A result to enter, a score waiting on the reader's agreement, or a seat open in their game. */
  readonly needsYou: boolean;
  /** The court hour's start; games are an hour. */
  readonly startsAt: string;
  readonly club: DeckCard['club'];
  /** What the club calls the court — *Court 2*. */
  readonly courtName: string;
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
 * - `calledOff` — *Refunded 30 zł* when the shares were taken, *Nobody paid* when they were not.
 *   **The reason is owed**: the wire carries no field for it yet (#544).
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
  | { readonly kind: 'calledOff'; readonly refundedGrosze?: number };

/** The cut-off, while it is still ahead of `now` — the instant the line switches at. */
function cutOffAhead(money: BookedMoney, now: number): string | undefined {
  const until = money.freeToLeaveUntil;
  return until !== undefined && Date.parse(until) > now ? until : undefined;
}

/**
 * The line a card takes at `now`. **How many stand on the court is handed in** (`seats`), as the
 * deck's rows take it: it is drawn knowledge, and a second table of seats here would be a second
 * answer to it.
 *
 * A seat open is counted off the sides — the court's seats less the people on it — and is **one at
 * the least**, because the status says a seat is open whatever the sides still hold: the wire has
 * no count of its own yet (#544).
 */
export function moneyLineOf(
  game: Pick<HomeGame, 'status' | 'money' | 'club' | 'sides'>,
  seats: number,
  now: number,
): MoneyLine | undefined {
  const { money } = game;
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
      return { kind: 'waiting', ...(game.club.name === undefined ? {} : { club: game.club.name }) };
    case 'SEAT_OPEN': {
      const on = game.sides.yours.length + game.sides.theirs.length;
      const until = cutOffAhead(money, now);
      return {
        kind: 'seatOpen',
        seats: Math.max(1, seats - on),
        ...(until === undefined ? {} : { fillsBy: until }),
      };
    }
    case 'CALLED_OFF':
      return { kind: 'calledOff', ...(money.paid ? { refundedGrosze: money.shareGrosze } : {}) };
    case 'NEEDS_RESULT':
    case 'CONFIRM_THE_RESULT':
    case 'COUNTED':
    case 'UNCOUNTED':
    case 'NEVER_PLAYED':
      return undefined;
  }
}

// ---------------------------------------------------------------------------
// Which cards Home draws
// ---------------------------------------------------------------------------

/** How long an ended game keeps its card — **a day, the Classic rail's number** (`plans`). */
export const ENDED_HOME_SHELF_LIFE_MS = 24 * 60 * 60 * 1000;

/** The four ends — a game that will not be played, or whose result is settled. */
const ENDED: Readonly<Record<HomeStatus, boolean>> = {
  WAITING_FOR_THE_CLUB: false,
  BOOKED: false,
  SEAT_OPEN: false,
  NEEDS_RESULT: false,
  CONFIRM_THE_RESULT: false,
  COUNTED: true,
  UNCOUNTED: true,
  NEVER_PLAYED: true,
  CALLED_OFF: true,
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
  if (!ENDED[game.status]) return true;
  const hourEnds = Date.parse(game.startsAt) + GAME_LENGTH_MS;
  return Number.isNaN(hourEnds) || now - hourEnds < ENDED_HOME_SHELF_LIFE_MS;
}

/** The statuses a fresh game can be in — filled, and not yet past its hour. */
const FRESH: Readonly<Record<HomeStatus, boolean>> = {
  WAITING_FOR_THE_CLUB: true,
  BOOKED: true,
  SEAT_OPEN: true,
  NEEDS_RESULT: false,
  CONFIRM_THE_RESULT: false,
  COUNTED: false,
  UNCOUNTED: false,
  NEVER_PLAYED: false,
  CALLED_OFF: false,
};

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
  return opened !== undefined && FRESH[game.status] && !opened.has(game.bookingId);
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
 * **The Chat door is open** while you are in the game and it is not over (the mechanics §14.2,
 * §14.3) — from the booking, when the room opens, to the result, when it closes as today. A game
 * waiting for the club has no room yet; an ended one has none any more.
 */
const CHAT_OPEN: Readonly<Record<HomeStatus, boolean>> = {
  WAITING_FOR_THE_CLUB: false,
  BOOKED: true,
  SEAT_OPEN: true,
  NEEDS_RESULT: true,
  CONFIRM_THE_RESULT: true,
  COUNTED: false,
  UNCOUNTED: false,
  NEVER_PLAYED: false,
  CALLED_OFF: false,
};

export function chatIsOpen(status: HomeStatus): boolean {
  return CHAT_OPEN[status];
}

/** The result act the details lead to — today's game screen, which tells and agrees a result. */
export type ResultAct = 'we-played' | 'confirm';

/**
 * **What the details offer once the hour has come** — *We played* while nobody has said, *Confirm
 * the result* once a score is on the table — or nothing. The result states are unchanged from
 * today (§14.1), so the act is today's screen's; the details are only the door to it.
 */
export function resultActOf(status: HomeStatus): ResultAct | undefined {
  if (status === 'NEEDS_RESULT') return 'we-played';
  if (status === 'CONFIRM_THE_RESULT') return 'confirm';
  return undefined;
}

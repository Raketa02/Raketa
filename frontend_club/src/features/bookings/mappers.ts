/**
 * **The club's bookings, wire to view and back.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the view models it makes.
 */

import type { components } from '@/generated/schema';
import type { Sport } from '@/features/club-details/mappers';
import { CLUB_ZONE, clubDay } from '@/features/courts/mappers';

type WireDay = components['schemas']['ClubBookingsResponse'];
type WireBooking = components['schemas']['ClubBookingSchema'];
type WirePlayer = components['schemas']['ClubBookingPlayerSchema'];
type WireFreeCourts = components['schemas']['FreeCourtsResponse'];
type WireCourtToMoveTo = components['schemas']['CourtToMoveToSchema'];
type WireMoveBody = components['schemas']['MoveRequest'];
type WireCancelBody = components['schemas']['CancelRequest'];
type WireCancelOutcome = components['schemas']['CancelOutcomeSchema'];

/** What a booking is to the club right now (the mechanics §16.7). */
export type BookingStatus = components['schemas']['ClubStatus'];

/** Competitive, or for fun: a friendly. */
export type Kind = components['schemas']['SearchMode'];

/** Why a game will not be played. */
export type CalledOffReason = components['schemas']['CalledOffReason'];

/** Why the club cancelled a game: the players are told it with what comes of their money (§16.9). */
export type CancelReason = components['schemas']['ClubCancelReason'];

/**
 * **Where a player's share stands, as the club sees it** (the mechanics §16.7, Q113): held on
 * their card until the cut-off, or taken (at the cut-off, or at once after it).
 */
export type Share = 'HELD' | 'TAKEN';

/**
 * **What cancelling a game does with the players' money** (the mechanics §16.9): before the
 * cut-off every hold is let go and nobody pays a fee; after it everyone is refunded in full, and
 * the card fees are not returned.
 */
export type CancelGivesBack = 'HOLDS_LET_GO' | 'REFUNDED_IN_FULL';

const KNOWN_CANCEL_GIVES_BACK: Readonly<Record<CancelGivesBack, true>> = {
  HOLDS_LET_GO: true,
  REFUNDED_IN_FULL: true,
};

export function isCancelGivesBack(value: unknown): value is CancelGivesBack {
  return typeof value === 'string' && value in KNOWN_CANCEL_GIVES_BACK;
}

/** Which of the day's bookings the page shows: all, or one status. */
export type BookingsFilter = components['schemas']['ClubFilter'];

/**
 * The filters, in the order the page offers them. A `Record` over the wire's enum, so a fifth
 * fails to compile here until the page has a place for it.
 */
const KNOWN_FILTERS: Readonly<Record<BookingsFilter, true>> = {
  ALL: true,
  SEAT_OPEN: true,
  CALLED_OFF: true,
};

export const FILTERS = Object.keys(KNOWN_FILTERS) as readonly BookingsFilter[];

/** The reasons a club cancels with, in the order the dialog offers them. */
const KNOWN_CANCEL_REASONS: Readonly<Record<CancelReason, true>> = {
  WEATHER: true,
  REPAIR: true,
  DOUBLE_BOOKING: true,
  OTHER: true,
};

export const CANCEL_REASONS = Object.keys(KNOWN_CANCEL_REASONS) as readonly CancelReason[];

export function isCancelReason(value: unknown): value is CancelReason {
  return typeof value === 'string' && value in KNOWN_CANCEL_REASONS;
}

/** **An hour at the club**: its local day and the wall clock it starts and ends at. */
export interface ClubHour {
  /** The local day, `2026-10-12`. */
  readonly day: string;
  /** `19:00`. */
  readonly from: string;
  /** `20:00`. */
  readonly until: string;
}

const CLOCK = new Intl.DateTimeFormat('en-GB', {
  timeZone: CLUB_ZONE,
  hourCycle: 'h23',
  hour: '2-digit',
  minute: '2-digit',
});

/** **The club's clock at an instant** the wire wrote: `18:52`. */
export function clubClock(instant: string): string {
  return CLOCK.format(Date.parse(instant));
}

/** The club's hour from the wire's two instants. */
export function clubHour(startsAt: string, endsAt: string): ClubHour {
  return {
    day: clubDay(Date.parse(startsAt)),
    from: clubClock(startsAt),
    until: clubClock(endsAt),
  };
}

/**
 * **A court a game is on, or may go to**: its name and its kind of court, indoor or outdoor, as
 * the players read it, *Court 3 · indoor* (Q122).
 */
export interface GameCourt {
  readonly name: string;
  readonly indoor: boolean;
}

/**
 * A player on a game, as the club sees them: their nickname, and where their share stands
 * (ADR-0199 §5).
 */
export interface BookingPlayer {
  readonly id: string;
  /** Their whole nickname, or `null` for an account that can no longer be named. */
  readonly nickname: string | null;
  /**
   * `null` while it is neither held nor taken: on a card checked and held later, or once its hold
   * was let go.
   */
  readonly share: Share | null;
}

/** The group a game was booked in: one of the club's official groups, or a player group. */
export interface BookedFrom {
  readonly name: string;
  readonly official: boolean;
}

/** **One Raketa booking at the club**, as a row of the Bookings page draws it. */
export interface Booking {
  readonly id: string;
  readonly hour: ClubHour;
  readonly court: GameCourt;
  readonly sport: Sport;
  readonly kind: Kind;
  readonly status: BookingStatus;
  /** Why it is called off, and the club's reason when the club cancelled it. */
  readonly calledOff: {
    readonly reason: CalledOffReason;
    readonly cancel: CancelReason | null;
  } | null;
  /** The first side first. */
  readonly players: readonly BookingPlayer[];
  readonly openSeats: number;
  readonly money: {
    readonly priceGrosze: number;
    /** Taken shares only: a share held is not collected yet. */
    readonly collectedGrosze: number;
    /** `null`, not yet known, while a refund less the fee kept waits for Stripe to say the fee. */
    readonly refundedGrosze: number | null;
  };
  /** What a cancel would do with the players' money, as the dialog spells it out. */
  readonly cancelGivesBack: CancelGivesBack;
  /** `null` for a group that is gone. */
  readonly from: BookedFrom | null;
  /** **Move** and **Cancel** are the club's: booked or with a seat open, and not started. */
  readonly mayMoveOrCancel: boolean;
}

/** **One day of the club's bookings**, under one filter, with every filter's count for the day. */
export interface BookingsDay {
  /** The local day read, `2026-10-12`. */
  readonly day: string;
  /** The local day at the club now: the page says *Today*, *Tomorrow* or *Yesterday* by it. */
  readonly today: string;
  readonly filter: BookingsFilter;
  readonly counts: Readonly<Record<BookingsFilter, number>>;
  /** Soonest first. */
  readonly bookings: readonly Booking[];
}

/**
 * **What a cancel would do**: refund in full when a share was taken, else let every hold go. The
 * read names no cut-off, and a game keeps the one it was booked with (§16.6), so the shares say
 * which side of it the game is, as the backend's cancel gives back what it took and lets go what
 * it held. A share taken early by the fallback (§12.2), beside others still held, reads as
 * refunded too: the club bears that share's fee, so *nobody pays a fee* would not be true.
 */
function cancelGivesBack(players: readonly WirePlayer[]): CancelGivesBack {
  return players.some((player) => player.paid) ? 'REFUNDED_IN_FULL' : 'HOLDS_LET_GO';
}

function shareOf(player: WirePlayer): Share | null {
  if (player.paid) return 'TAKEN';
  return player.held ? 'HELD' : null;
}

function toBooking(wire: WireBooking): Booking {
  return {
    id: wire.booking_id,
    hour: clubHour(wire.starts_at, wire.ends_at),
    court: { name: wire.court_name, indoor: wire.indoor },
    sport: wire.sport,
    kind: wire.kind,
    status: wire.status,
    calledOff:
      wire.called_off_reason === null
        ? null
        : { reason: wire.called_off_reason, cancel: wire.cancel_reason },
    players: wire.players.map((player) => ({
      id: player.player_id,
      nickname: player.nickname,
      share: shareOf(player),
    })),
    openSeats: wire.open_seats,
    money: {
      priceGrosze: wire.money.price_grosze,
      collectedGrosze: wire.money.collected_grosze,
      refundedGrosze: wire.money.refunded_grosze,
    },
    cancelGivesBack: cancelGivesBack(wire.players),
    from:
      wire.booked_from === null
        ? null
        : { name: wire.booked_from.name, official: wire.booked_from.official },
    mayMoveOrCancel: wire.may_move_or_cancel,
  };
}

export function toBookingsDay(wire: WireDay, today: string): BookingsDay {
  return {
    day: wire.day,
    today,
    filter: wire.filter,
    counts: {
      ALL: wire.counts.all,
      SEAT_OPEN: wire.counts.seat_open,
      CALLED_OFF: wire.counts.called_off,
    },
    bookings: wire.bookings.map(toBooking),
  };
}

/**
 * A court a game can be moved to: another of its sport, free at its hour, of its kind or indoor
 * for an outdoor game, as the backend offers them.
 */
export interface FreeCourt extends GameCourt {
  readonly id: string;
}

export function toGameCourt(wire: WireCourtToMoveTo): GameCourt {
  return { name: wire.name, indoor: wire.indoor };
}

function toFreeCourt(wire: WireCourtToMoveTo): FreeCourt {
  return { id: wire.court_id, ...toGameCourt(wire) };
}

export function toFreeCourts(wire: WireFreeCourts): readonly FreeCourt[] {
  return wire.courts.map(toFreeCourt);
}

export function toMoveBody(courtId: string): WireMoveBody {
  return { court_id: courtId };
}

/**
 * **What a cancel does, or would do** (the mechanics §16.9, Q122): another of the club's courts
 * takes the game, which moves there with every hold and payment as it was, or the game is called
 * off. The dialog reads it before the desk confirms; the cancel decides afresh, and answers it.
 */
export type CancelOutcome =
  { readonly outcome: 'MOVED'; readonly court: FreeCourt } | { readonly outcome: 'CALLED_OFF' };

export function toCancelOutcome(wire: WireCancelOutcome): CancelOutcome {
  return wire.outcome === 'MOVED' && wire.court !== null
    ? { outcome: 'MOVED', court: toFreeCourt(wire.court) }
    : { outcome: 'CALLED_OFF' };
}

/**
 * A cancel, with the reason the players are told. `anyway` is *Cancel the game anyway*, for a
 * club closing the whole hour: called off, even when another court would take the game.
 */
export function toCancelBody(reason: CancelReason, anyway: boolean): WireCancelBody {
  return { reason, anyway };
}

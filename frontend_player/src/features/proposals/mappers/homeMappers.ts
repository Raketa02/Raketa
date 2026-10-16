/**
 * **Home and a booked game, off the wire** — `GET /home` and `GET /bookings/{id}` (#542) read into
 * the domain's shapes ([#556](https://github.com/Raketa02/Raketa/issues/556)).
 *
 * A seat is the deck's person with its *paid* beside it: the tiles are the deck's tiles, and a
 * booked game is the card it was, turned into a court. A `null` on the wire is a field left off,
 * as every mapper here does it. A card in a sport this build cannot name is dropped — the app
 * would have no word, no colour and no court to draw it with.
 */

import { toSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { DeckPerson } from '../domain/deck';
import type { BookedGame, BookedMoney, Home, HomeGame, Leaving, RescueOffer } from '../domain/home';
import type { LeavingKind, ShareState, TimeTo } from '../domain/vocabulary';

import { toClub, toKind } from './deckMappers';

type Schemas = components['schemas'];

/** A seat on a booked court — the deck's person, with *paid*. A Fill in row's players too. */
export function toSeat(wire: Schemas['BookedTileSchema']): DeckPerson {
  return {
    playerId: wire.player_id,
    isYou: wire.is_you,
    // Nobody on a booked court is *In* — that word is a game still filling's.
    isIn: false,
    paid: wire.paid,
    ...(wire.name === null ? {} : { name: wire.name }),
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    ...(wire.level === null ? {} : { level: wire.level }),
  };
}

function toSides(wire: Schemas['BookedSidesSchema']): HomeGame['sides'] {
  return { yours: wire.yours.map(toSeat), theirs: wire.theirs.map(toSeat) };
}

/**
 * A booked game's money. Where the share stands and its two instants (#637, #639; Q113) are absent
 * for a `null`, and for the fields missing altogether: a server older than them sends none, and the
 * line then says only what `paid` and the cut-off say.
 */
function toMoney(wire: Schemas['BookedMoneySchema']): BookedMoney {
  const state: ShareState | null | undefined = wire.share_state;
  const heldFrom: string | null | undefined = wire.held_from;
  const takenAt: string | null | undefined = wire.taken_at;
  return {
    shareGrosze: wire.share_grosze,
    paid: wire.paid,
    ...(state === null || state === undefined ? {} : { shareState: state }),
    ...(heldFrom === null || heldFrom === undefined ? {} : { heldFrom }),
    ...(takenAt === null || takenAt === undefined ? {} : { takenAt }),
    ...(wire.free_to_leave_until === null ? {} : { freeToLeaveUntil: wire.free_to_leave_until }),
    ...(wire.refunded_grosze === null ? {} : { refundedGrosze: wire.refunded_grosze }),
  };
}

/**
 * **When the payment a game waits for is due** (#625, #626) — on Home, a booked game's details and a
 * game still filling's. Nothing for a `null`, and nothing from a server older than it.
 */
export function toPaymentDueBy(wire: { readonly payment_due_by?: string | null }): {
  readonly paymentDueBy?: string;
} {
  const due = wire.payment_due_by;
  return due === null || due === undefined ? {} : { paymentDueBy: due };
}

/** **The reader's own time to pay** (#625, #626) — as `toPaymentDueBy`, for the payer alone. */
function toYourPaymentDueBy(wire: {
  readonly your_payment_due_by?: string | null;
}): Pick<HomeGame, 'yourPaymentDueBy'> {
  const due = wire.your_payment_due_by;
  return due === null || due === undefined ? {} : { yourPaymentDueBy: due };
}

/** **What the time is for** (#638) — as `toPaymentDueBy`: nothing for a `null` or an older server. */
function toTimeTo(wire: { readonly time_to?: TimeTo | null }): Pick<HomeGame, 'timeTo'> {
  const timeTo = wire.time_to;
  return timeTo === null || timeTo === undefined ? {} : { timeTo };
}

/**
 * **A full game gone back to filling** (#624) — nothing for a booked game, and nothing from a server
 * older than it, which sends no such field.
 */
function toFillingAgain(
  wire: Pick<Schemas['HomeGameSchema'], 'filling_again'>,
): Pick<HomeGame, 'fillingAgain'> {
  const fillingAgain: boolean | undefined = wire.filling_again;
  return fillingAgain === true ? { fillingAgain } : {};
}

/** What Home and the details share of a booked game — every nullable read as an absent field. */
function toBooking(
  wire: Schemas['HomeGameSchema'] | Schemas['BookingDetailsResponse'],
): Omit<HomeGame, 'sport' | 'club'> {
  return {
    bookingId: wire.booking_id,
    ...(wire.game_id === null ? {} : { gameId: wire.game_id }),
    groupId: wire.pool_id,
    kind: toKind(wire.kind),
    status: wire.status,
    ...(wire.called_off_reason === null ? {} : { calledOffReason: wire.called_off_reason }),
    ...(wire.club_cancel_reason === null ? {} : { clubCancelReason: wire.club_cancel_reason }),
    ...(wire.uncounted_reason === null ? {} : { uncountedReason: wire.uncounted_reason }),
    openSeats: wire.open_seats,
    needsYou: wire.needs_you,
    startsAt: wire.starts_at,
    ...(wire.court_name === null ? {} : { courtName: wire.court_name }),
    ...(wire.indoor === null ? {} : { indoor: wire.indoor }),
    sides: toSides(wire.sides),
    money: toMoney(wire.money),
    ...toFillingAgain(wire),
    ...toPaymentDueBy(wire),
    ...toYourPaymentDueBy(wire),
    ...toTimeTo(wire),
  };
}

/**
 * What leaving costs. After the cut-off the read quotes the refund if the seat is taken and the fee
 * kept, to the grosz (#641), or neither while the fee is not yet known. The noughts the read sends
 * while one payment is awaited are no quote: nobody has paid.
 */
function toLeaving(wire: Schemas['LeavingSchema']): Leaving {
  const { kind, refund_grosze: back, card_fee_grosze: kept } = wire;
  if (kind !== 'AFTER_THE_CUT_OFF' || back === null || kept === null) return { kind };
  return { kind, lateRefund: { backGrosze: back, keptGrosze: kept } };
}

function toRescue(wire: Schemas['RescueOfferSchema']): RescueOffer {
  return { deadline: wire.deadline, fillsByTheCutOff: wire.fills_by_the_cut_off };
}

export function toHomeGame(wire: Schemas['HomeGameSchema']): HomeGame | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;
  return { ...toBooking(wire), sport, club: toClub(wire.club) };
}

export function toHome(wire: Schemas['HomeResponse']): Home {
  return {
    readAt: wire.read_at,
    needingYou: wire.needing_you,
    games: wire.games.map(toHomeGame).filter((game): game is HomeGame => game !== undefined),
  };
}

export function toBookedGame(wire: Schemas['BookingDetailsResponse']): BookedGame | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  const rescue = wire.rescue ?? null;
  return {
    ...toBooking(wire),
    sport,
    readAt: wire.read_at,
    endsAt: wire.ends_at,
    where: {
      ...toClub(wire.where),
      ...(wire.where.distance_km === null ? {} : { distanceKm: wire.where.distance_km }),
    },
    showsForecast: wire.shows_forecast,
    ...(wire.leaving === null ? {} : { leaving: toLeaving(wire.leaving) }),
    ...(rescue === null ? {} : { rescue: toRescue(rescue) }),
  };
}

/** *Leave the game*, done — which of the three it was (#544). */
export function toLeft(wire: Schemas['DepartureResponse']): LeavingKind {
  return wire.left;
}

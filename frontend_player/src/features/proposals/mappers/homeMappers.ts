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
import type { LeavingKind } from '../domain/vocabulary';

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
    checkedIn: wire.checked_in,
    ...(wire.name === null ? {} : { name: wire.name }),
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    ...(wire.level === null ? {} : { level: wire.level }),
  };
}

function toSides(wire: Schemas['BookedSidesSchema']): HomeGame['sides'] {
  return { yours: wire.yours.map(toSeat), theirs: wire.theirs.map(toSeat) };
}

function toMoney(wire: Schemas['BookedMoneySchema']): BookedMoney {
  // What leaving gives back (Q99) — absent for a `null`, and for the field missing altogether: a
  // server older than it sends none, and the line then has no clause.
  const back: number | null | undefined = wire.back_if_you_leave_grosze;
  return {
    shareGrosze: wire.share_grosze,
    paid: wire.paid,
    ...(wire.free_to_leave_until === null ? {} : { freeToLeaveUntil: wire.free_to_leave_until }),
    ...(back === null || back === undefined ? {} : { backIfYouLeaveGrosze: back }),
    ...(wire.refunded_grosze === null ? {} : { refundedGrosze: wire.refunded_grosze }),
  };
}

/**
 * **When the club answers** (#614) — absent for a `null`, and for the field missing altogether:
 * a server older than it sends none, and the line then reads as it did before.
 */
export function toAnswerBy(wire: string | null | undefined): { readonly answerBy?: string } {
  return wire === null || wire === undefined ? {} : { answerBy: wire };
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
    sides: toSides(wire.sides),
    money: toMoney(wire.money),
    ...toAnswerBy(wire.answer_by),
  };
}

function toLeaving(wire: Schemas['LeavingSchema']): Leaving {
  return {
    kind: wire.kind,
    refundGrosze: wire.refund_grosze,
    cardFeeGrosze: wire.card_fee_grosze,
  };
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
    ...(wire.check_in === null
      ? {}
      : { checkIn: { shortCode: wire.check_in.short_code, qrPayload: wire.check_in.qr_payload } }),
    ...(wire.leaving === null ? {} : { leaving: toLeaving(wire.leaving) }),
    ...(rescue === null ? {} : { rescue: toRescue(rescue) }),
  };
}

/** *Leave the game*, done — which of the three it was (#544). */
export function toLeft(wire: Schemas['DepartureResponse']): LeavingKind {
  return wire.left;
}

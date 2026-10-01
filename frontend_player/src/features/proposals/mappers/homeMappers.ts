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
import type { BookedGame, BookedMoney, Home, HomeGame } from '../domain/home';

import { toClub, toKind } from './deckMappers';

type Schemas = components['schemas'];

function toSeat(wire: Schemas['BookedTileSchema']): DeckPerson {
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

function toMoney(wire: Schemas['BookedMoneySchema']): BookedMoney {
  return {
    shareGrosze: wire.share_grosze,
    paid: wire.paid,
    ...(wire.free_to_leave_until === null ? {} : { freeToLeaveUntil: wire.free_to_leave_until }),
  };
}

export function toHomeGame(wire: Schemas['HomeGameSchema']): HomeGame | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  return {
    bookingId: wire.booking_id,
    gameId: wire.game_id,
    groupId: wire.pool_id,
    sport,
    kind: toKind(wire.kind),
    status: wire.status,
    needsYou: wire.needs_you,
    startsAt: wire.starts_at,
    club: toClub(wire.club),
    courtName: wire.court_name,
    sides: toSides(wire.sides),
    money: toMoney(wire.money),
  };
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

  return {
    bookingId: wire.booking_id,
    gameId: wire.game_id,
    groupId: wire.pool_id,
    sport,
    kind: toKind(wire.kind),
    readAt: wire.read_at,
    status: wire.status,
    needsYou: wire.needs_you,
    startsAt: wire.starts_at,
    endsAt: wire.ends_at,
    where: {
      ...toClub(wire.where),
      ...(wire.where.distance_km === null ? {} : { distanceKm: wire.where.distance_km }),
    },
    courtName: wire.court_name,
    sides: toSides(wire.sides),
    money: toMoney(wire.money),
    showsForecast: wire.shows_forecast,
    ...(wire.check_in === null
      ? {}
      : { checkIn: { shortCode: wire.check_in.short_code, qrPayload: wire.check_in.qr_payload } }),
  };
}

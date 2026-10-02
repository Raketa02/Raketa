/**
 * **A group's Fill in, off the wire** — `GET /pools/{id}/fill-in` (#545) read into the domain's
 * shape ([#557](https://github.com/Raketa02/Raketa/issues/557)). A row's players are a booked
 * court's seats (`toSeat`), and a row in a sport this build cannot name is dropped, as a card is.
 */

import { toSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { FillIn, SeatToFill } from '../domain/fillIn';

import { toClub, toKind } from './deckMappers';
import { toSeat } from './homeMappers';

type Schemas = components['schemas'];

/** One rescue offered to the reader — a *Seats to fill* row, and a cell's sheet's (#558). */
export function toSeatToFill(wire: Schemas['SeatToFillSchema']): SeatToFill | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;
  return {
    bookingId: wire.booking_id,
    sport,
    kind: toKind(wire.kind),
    startsAt: wire.starts_at,
    club: toClub(wire.club),
    courtName: wire.court_name,
    shareGrosze: wire.share_grosze,
    openSeats: wire.open_seats,
    deadline: wire.deadline,
    fillsByTheCutOff: wire.fills_by_the_cut_off,
    players: wire.players.map(toSeat),
  };
}

export function toFillIn(wire: Schemas['FillInResponse']): FillIn {
  return {
    readAt: wire.read_at,
    badge: wire.badge,
    seatsToFill: wire.seats_to_fill
      .map(toSeatToFill)
      .filter((row): row is SeatToFill => row !== undefined),
  };
}

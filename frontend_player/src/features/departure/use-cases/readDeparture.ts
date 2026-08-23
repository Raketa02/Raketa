/**
 * Ask what leaving this match is worth.
 *
 * A thin pass-through, and `ADR-0009`'s escape hatch covers exactly that: the
 * client has no business rule about what leaving is worth, because that is the
 * server's whole job here and a client-side opinion about it would be a second,
 * weaker one — which is precisely what the quote-and-refuse rule exists to make
 * impossible. The folder is kept for predictability rather than filled with an
 * invented invariant.
 */

import { readDeparture as fetchDeparture } from '../api/departureApi';
import type { Departure } from '../domain/Departure';
import { toDeparture } from '../mappers/departureMappers';

export interface ReadDepartureOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

export function readDeparture({ matchId, signal }: ReadDepartureOptions): Promise<Departure> {
  return fetchDeparture({ matchId, signal }).then(toDeparture);
}

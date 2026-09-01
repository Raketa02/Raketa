/**
 * How many yeses of yours are still standing, per sport — the **Match me count**.
 *
 * One read, and the only one in this tab that is allowed to move while a player is looking at
 * it. Everything else in Play is a mutation-minted record pinned at `staleTime: Infinity`,
 * because foregrounding must not reorder a pool under somebody's finger; this is a **count**,
 * not an ordering, and a stale one is the segment lying about what the player has out.
 */

import { readInterest, type ReadInterestOptions } from '../api/deckApi';
import { toOutstandingInterest, type OutstandingInterest } from '../mappers/interestMappers';

export function readOutstandingInterest(
  options: ReadInterestOptions = {},
): Promise<OutstandingInterest> {
  return readInterest(options).then(toOutstandingInterest);
}

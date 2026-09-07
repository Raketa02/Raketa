/**
 * How many yeses of yours are still standing, per sport.
 *
 * One read, and the only one in this tab that is allowed to move while a player is looking at
 * it. Everything else in Play is a record pinned at `staleTime: Infinity`, because foregrounding
 * must not reorder a pool under somebody's finger; this is a **count**, not an ordering, and a
 * stale one is the deck's ending sentence lying about what the player has out.
 *
 * It was the segment's `Match me · 3` as well until that was struck for reading as a count of
 * waiting cards. One reader fewer; the same read, and the same reason for it.
 */

import { readInterest, type ReadInterestOptions } from '../api/deckApi';
import { toOutstandingInterest, type OutstandingInterest } from '../mappers/interestMappers';

export function readOutstandingInterest(
  options: ReadInterestOptions = {},
): Promise<OutstandingInterest> {
  return readInterest(options).then(toOutstandingInterest);
}

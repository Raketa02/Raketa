/**
 * Your own yeses: how many are still standing per sport, and who you said them to.
 *
 * One read, and the only one in this tab that is allowed to move while a player is looking at
 * it. Everything else in Play is a record pinned at `staleTime: Infinity`, because foregrounding
 * must not reorder a pool under somebody's finger; this is a **count and a lookup**, not an
 * ordering, and a stale one is the deck's counter lying about what the player has out or a
 * builder card missing the *You said yes* it has earned.
 *
 * It was the deck's alone — the segment's `Match me · 3` before that, struck for reading as a
 * count of waiting cards. [ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8 gave the same read two more readers, the pool and the challenge screen, for the one list
 * that was already on the wire: the reader's own outgoing yeses.
 */

import { readInterest, type ReadInterestOptions } from '../api/deckApi';
import { toInterest, type MyInterest } from '../mappers/interestMappers';

export function readMyInterest(options: ReadInterestOptions = {}): Promise<MyInterest> {
  return readInterest(options).then(toInterest);
}

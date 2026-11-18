/**
 * **Same vibe's two reads** ([#803](https://github.com/Raketa02/Raketa/issues/803)) — pass-throughs,
 * the template's uniform-strict escape hatch: who is on the row, with which vibe % and in which order
 * are the server's (the Home rows mechanics §8, §9), and nothing here judges them again.
 */

import { getSameVibe, getSameVibePage, type Cancellable } from '../api/discoveryApi';
import type { PeopleRow } from '../domain/peopleRow';
import type { SameVibePlayer } from '../domain/sameVibe';
import type { SeeAllAsk, SeeAllPage } from '../domain/seeAll';
import { toPageAsked, toSameVibePage, toSameVibeRow } from '../mappers/discoveryMappers';

/** Home's row — up to 10, in the server's order, and how many it could show (#822). */
export function readSameVibe(options: Cancellable = {}): Promise<PeopleRow<SameVibePlayer>> {
  return getSameVibe(options).then(toSameVibeRow);
}

/** One page of See all — with a sport, only those holding a level in it. */
export function readSameVibePage(
  page: SeeAllAsk,
  options: Cancellable = {},
): Promise<SeeAllPage<SameVibePlayer>> {
  return getSameVibePage(toPageAsked(page), options).then(toSameVibePage);
}

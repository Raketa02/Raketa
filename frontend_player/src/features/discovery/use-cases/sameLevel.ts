/**
 * **Same competitive level's two reads** ([#802](https://github.com/Rakieta02/Rakieta/issues/802)) —
 * pass-throughs, the template's uniform-strict escape hatch: who is on the row, in which sport, with
 * which % and in which order are the server's (the Home rows mechanics §6, §9), and nothing here
 * judges them again.
 */

import { getSameLevel, getSameLevelPage, type Cancellable } from '../api/discoveryApi';
import type { PeopleRow } from '../domain/peopleRow';
import type { SameLevelPlayer } from '../domain/sameLevel';
import type { SeeAllAsk, SeeAllPage } from '../domain/seeAll';
import { toPageAsked, toSameLevelPage, toSameLevelRow } from '../mappers/discoveryMappers';

/**
 * Home's row — up to 10, in the server's order, and how many it could show (#822); none while the
 * reader holds no level.
 */
export function readSameLevel(options: Cancellable = {}): Promise<PeopleRow<SameLevelPlayer>> {
  return getSameLevel(options).then(toSameLevelRow);
}

/** One page of See all — with a sport, everybody holding a level in it, compared there. */
export function readSameLevelPage(
  page: SeeAllAsk,
  options: Cancellable = {},
): Promise<SeeAllPage<SameLevelPlayer>> {
  return getSameLevelPage(toPageAsked(page), options).then(toSameLevelPage);
}

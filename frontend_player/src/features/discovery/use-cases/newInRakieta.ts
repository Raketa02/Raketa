/**
 * **New in Rakieta's two reads** ([#801](https://github.com/Rakieta02/Rakieta/issues/801)) —
 * pass-throughs, the template's uniform-strict escape hatch: who is on the row, in which order and
 * how many are the server's (the Home rows mechanics §7), and nothing here judges them again.
 */

import { getNewInRakieta, getNewInRakietaPage, type Cancellable } from '../api/discoveryApi';
import type { Joiner, JoinerPage } from '../domain/joiner';
import type { PeopleRow } from '../domain/peopleRow';
import type { SeeAllAsk } from '../domain/seeAll';
import { toJoinerPage, toNewInRakietaRow, toPageAsked } from '../mappers/discoveryMappers';

/** Home's row — up to 10, in the server's order, and how many it could show (#822). */
export function readNewInRakieta(options: Cancellable = {}): Promise<PeopleRow<Joiner>> {
  return getNewInRakieta(options).then(toNewInRakietaRow);
}

/** One page of See all — with a sport, only those holding a level in it. */
export function readNewInRakietaPage(
  page: SeeAllAsk,
  options: Cancellable = {},
): Promise<JoinerPage> {
  return getNewInRakietaPage(toPageAsked(page), options).then(toJoinerPage);
}

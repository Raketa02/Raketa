/**
 * **New in Raketa's two reads** ([#801](https://github.com/Raketa02/Raketa/issues/801)) —
 * pass-throughs, the template's uniform-strict escape hatch: who is on the row, in which order and
 * how many are the server's (the Home rows mechanics §7), and nothing here judges them again.
 */

import { getNewInRaketa, getNewInRaketaPage, type Cancellable } from '../api/discoveryApi';
import type { Joiner, JoinerPage } from '../domain/joiner';
import type { SeeAllAsk } from '../domain/seeAll';
import { toJoiner, toJoinerPage, toPageAsked } from '../mappers/discoveryMappers';

/** Home's row — up to 10, in the server's order. */
export function readNewInRaketa(options: Cancellable = {}): Promise<readonly Joiner[]> {
  return getNewInRaketa(options).then((answer) => answer.players.map(toJoiner));
}

/** One page of See all — with a sport, only those holding a level in it. */
export function readNewInRaketaPage(
  page: SeeAllAsk,
  options: Cancellable = {},
): Promise<JoinerPage> {
  return getNewInRaketaPage(toPageAsked(page), options).then(toJoinerPage);
}

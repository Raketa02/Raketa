/**
 * **New in Raketa's two reads** ([#801](https://github.com/Raketa02/Raketa/issues/801)) —
 * pass-throughs, the template's uniform-strict escape hatch: who is on the row, in which order and
 * how many are the server's (the Home rows mechanics §7), and nothing here judges them again.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getNewInRaketa, getNewInRaketaPage, type Cancellable } from '../api/discoveryApi';
import type { Joiner, JoinerPage } from '../domain/joiner';
import { toJoiner, toJoinerPage } from '../mappers/discoveryMappers';

/** Home's row — up to 10, in the server's order. */
export function readNewInRaketa(options: Cancellable = {}): Promise<readonly Joiner[]> {
  return getNewInRaketa(options).then((answer) => answer.players.map(toJoiner));
}

/** One page of See all — with a sport, only those holding a level in it. */
export function readNewInRaketaPage(
  page: { readonly sport: Sport | undefined; readonly after: string | undefined },
  options: Cancellable = {},
): Promise<JoinerPage> {
  return getNewInRaketaPage(
    {
      ...(page.sport === undefined ? {} : { sport: toWireSport(page.sport) }),
      ...(page.after === undefined ? {} : { after: page.after }),
    },
    options,
  ).then(toJoinerPage);
}

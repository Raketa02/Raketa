/**
 * **Same competitive level's two reads** ([#802](https://github.com/Raketa02/Raketa/issues/802)) —
 * pass-throughs, the template's uniform-strict escape hatch: who is on the row, in which sport, with
 * which % and in which order are the server's (the Home rows mechanics §6, §9), and nothing here
 * judges them again.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getSameLevel, getSameLevelPage, type Cancellable } from '../api/discoveryApi';
import type { SameLevelPlayer } from '../domain/sameLevel';
import type { SeeAllPage } from '../domain/seeAll';
import { toSameLevelPage, toSameLevelPlayers } from '../mappers/discoveryMappers';

/** Home's row — up to 10, in the server's order; none while the reader holds no level. */
export function readSameLevel(options: Cancellable = {}): Promise<readonly SameLevelPlayer[]> {
  return getSameLevel(options).then((answer) => toSameLevelPlayers(answer.players));
}

/** One page of See all — with a sport, everybody holding a level in it, compared there. */
export function readSameLevelPage(
  page: { readonly sport: Sport | undefined; readonly after: string | undefined },
  options: Cancellable = {},
): Promise<SeeAllPage<SameLevelPlayer>> {
  return getSameLevelPage(
    {
      ...(page.sport === undefined ? {} : { sport: toWireSport(page.sport) }),
      ...(page.after === undefined ? {} : { after: page.after }),
    },
    options,
  ).then(toSameLevelPage);
}

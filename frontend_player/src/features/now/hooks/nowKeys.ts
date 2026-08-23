/**
 * Every query key this feature uses, in one factory.
 *
 * **The sport is part of the key**, because switching sport is a new request and
 * not a filter over a payload holding every sport (`ADR-0070`): one key per sport
 * is what makes a switch back instant and what stops two compositions of two
 * different screens sharing one cache entry.
 *
 * `all` is exported so an action elsewhere can reach the screen — that is
 * `ADR-0054`'s third ask, and until the update shape exists (`Raketa02/Raketa#79`,
 * `#80`, `#81`) invalidating this key is the whole of it.
 */

import type { SportFilter } from '../mappers/codes';

export const nowKeys = {
  all: ['now'] as const,
  screen: (sport: SportFilter) => [...nowKeys.all, 'screen', sport] as const,
};

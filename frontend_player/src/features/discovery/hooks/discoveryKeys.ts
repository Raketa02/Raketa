/**
 * **Discovery's query keys** ([#801](https://github.com/Rakieta02/Rakieta/issues/801),
 * [#802](https://github.com/Rakieta02/Rakieta/issues/802), [#803](https://github.com/Rakieta02/Rakieta/issues/803)) — each people row and its See all, one
 * entry per sport. **A friend write reaches them all** — through the
 * `LISTS_PEOPLE` tag their reads declare, not these keys — so one tap moves that person on every row
 * and See all at once (the Home rows mechanics §13). The cursor is the infinite query's page parameter, so a See all entry holds every
 * page read under it.
 */

import type { SeeAllSport } from '../domain/seeAll';

export const discoveryKeys = {
  all: ['discovery'] as const,
  /** `GET /new-in-rakieta` — Home's row. */
  newInRakieta: () => [...discoveryKeys.all, 'new-in-rakieta', 'row'] as const,
  /** `GET /new-in-rakieta/all?sport` — See all, for *All* or one sport, every page read. */
  newInRakietaAll: (sport: SeeAllSport) =>
    [...discoveryKeys.all, 'new-in-rakieta', 'see-all', sport] as const,
  /** `GET /same-level` — Home's row. */
  sameLevel: () => [...discoveryKeys.all, 'same-level', 'row'] as const,
  /** `GET /same-level/all?sport` — See all, for *All* or one sport, every page read. */
  sameLevelAll: (sport: SeeAllSport) =>
    [...discoveryKeys.all, 'same-level', 'see-all', sport] as const,
  /** `GET /same-vibe` — Home's row. */
  sameVibe: () => [...discoveryKeys.all, 'same-vibe', 'row'] as const,
  /** `GET /same-vibe/all?sport` — See all, for *All* or one sport, every page read. */
  sameVibeAll: (sport: SeeAllSport) =>
    [...discoveryKeys.all, 'same-vibe', 'see-all', sport] as const,
};

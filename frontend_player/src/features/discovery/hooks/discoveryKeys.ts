/**
 * **Discovery's query keys** ([#801](https://github.com/Raketa02/Raketa/issues/801)) — New in
 * Raketa's row and See all, one entry per sport. **A friend write re-reads them all** — through the
 * `LISTS_PEOPLE` tag their reads declare, not these keys — so one tap moves that person on every row
 * and See all at once (the Home rows mechanics §13). The cursor is the infinite query's page parameter, so a See all entry holds every
 * page read under it.
 */

import type { SeeAllSport } from '../domain/joiner';

export const discoveryKeys = {
  all: ['discovery'] as const,
  /** `GET /new-in-raketa` — Home's row. */
  newInRaketa: () => [...discoveryKeys.all, 'new-in-raketa', 'row'] as const,
  /** `GET /new-in-raketa/all?sport` — See all, for *All* or one sport, every page read. */
  newInRaketaAll: (sport: SeeAllSport) =>
    [...discoveryKeys.all, 'new-in-raketa', 'see-all', sport] as const,
};

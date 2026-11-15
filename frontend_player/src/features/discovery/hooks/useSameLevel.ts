/**
 * **Same competitive level, read** ([#802](https://github.com/Raketa02/Raketa/issues/802); the Home
 * rows mechanics §3, §6, §13).
 *
 * | | |
 * | --- | --- |
 * | `useSameLevel` | `GET /same-level` — Home's row, on its own: a slow or failed read holds up nothing else on Home |
 * | `useSameLevelPage` | `GET /same-level/all?sport&after` — See all, 20 to a page, read on as the list nears its end |
 *
 * **Coming back to Home re-reads the row once its last read is older than thirty seconds** — the
 * app's `staleTime`, as New in Raketa does; foregrounding does the same through the focus manager.
 * The row is worked out again on every read (§9), so a return shows a new fresh match.
 *
 * **One tap moves a person everywhere** (§13): both reads declare `LISTS_PEOPLE`, so every friend
 * write reaches the row — holding still under the thumb (`usePeopleRow`) — and every See all, and
 * every block re-reads both. Home's pull is `rereadDiscovery`.
 */

import type { SameLevelPlayer } from '../domain/sameLevel';
import { pageSport, type SeeAllSport } from '../domain/seeAll';
import { readSameLevel, readSameLevelPage } from '../use-cases/sameLevel';

import { discoveryKeys } from './discoveryKeys';
import { usePeopleRow } from './usePeopleRow';
import { useSeeAllPages, type SeeAllList } from './useSeeAllPages';

/** Home's row — re-read on return, holding still under a friend write (`usePeopleRow`). */
export function useSameLevel() {
  return usePeopleRow(discoveryKeys.sameLevel(), (signal) => readSameLevel({ signal }));
}

/** **See all** — best % first; a sport re-compares everybody in it, and keeps only them. */
export function useSameLevelPage(choice: SeeAllSport): SeeAllList<SameLevelPlayer> {
  return useSeeAllPages(discoveryKeys.sameLevelAll(choice), (after, signal) =>
    readSameLevelPage({ sport: pageSport(choice), after }, { signal }),
  );
}

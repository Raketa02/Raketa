/**
 * **Same vibe, read** ([#803](https://github.com/Raketa02/Raketa/issues/803); the Home rows mechanics
 * §3, §8, §13).
 *
 * | | |
 * | --- | --- |
 * | `useSameVibe` | `GET /same-vibe` — Home's row, on its own: a slow or failed read holds up nothing else on Home |
 * | `useSameVibePage` | `GET /same-vibe/all?sport&after` — See all, 20 to a page, read on as the grid nears its end |
 *
 * **Coming back to Home re-reads the row once its last read is older than thirty seconds**, as the
 * other people rows do; the row is worked out again on every read (§9), so a return shows a new fresh
 * match. **One tap moves a person everywhere** (§13): both reads declare `LISTS_PEOPLE`, so every
 * friend write reaches the row — holding still under the thumb (`usePeopleRow`) — and every See all,
 * and every block re-reads both. Home's pull is `rereadDiscovery`.
 */

import type { SameVibePlayer } from '../domain/sameVibe';
import { pageSport, type SeeAllSport } from '../domain/seeAll';
import { readSameVibe, readSameVibePage } from '../use-cases/sameVibe';

import { discoveryKeys } from './discoveryKeys';
import { usePeopleRow } from './usePeopleRow';
import { useSeeAllPages, type SeeAllList } from './useSeeAllPages';

/** Home's row — re-read on return, holding still under a friend write (`usePeopleRow`). */
export function useSameVibe() {
  return usePeopleRow(discoveryKeys.sameVibe(), (signal) => readSameVibe({ signal }));
}

/** **See all** — most in common first; a sport keeps only who holds a level in it. */
export function useSameVibePage(choice: SeeAllSport): SeeAllList<SameVibePlayer> {
  return useSeeAllPages(discoveryKeys.sameVibeAll(choice), (after, signal) =>
    readSameVibePage({ sport: pageSport(choice), after }, { signal }),
  );
}

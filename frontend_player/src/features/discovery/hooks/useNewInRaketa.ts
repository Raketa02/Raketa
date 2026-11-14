/**
 * **New in Raketa, read** ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows
 * mechanics §3, §7, §13).
 *
 * | | |
 * | --- | --- |
 * | `useNewInRaketa` | `GET /new-in-raketa` — Home's row, on its own: a slow or failed read holds up nothing else on Home |
 * | `useNewInRaketaPage` | `GET /new-in-raketa/all?sport&after` — See all, 20 to a page, read on as the grid nears its end (`useSeeAllPages`) |
 * | `rereadDiscovery` | every Discovery read — Home's pull |
 *
 * **Coming back to Home re-reads the row once its last read is older than thirty seconds** (Q22) —
 * the app's `staleTime`, as Hottest groups does; foregrounding does the same through the focus
 * manager. The row is the 10 newest, so a return after somebody joined shows them.
 *
 * **One tap moves a person everywhere** (§13): both reads declare `LISTS_PEOPLE`, so every friend
 * write and every block — wherever it is made — re-reads the row and every See all, and the round
 * button's write settles once they have. See all opened over Home keeps Home's row mounted, so both
 * move. `rereadDiscovery` is Home's pull.
 */

import type { QueryClient } from '@tanstack/react-query';

import type { Joiner } from '../domain/joiner';
import { pageSport, type SeeAllSport } from '../domain/seeAll';
import { readNewInRaketa, readNewInRaketaPage } from '../use-cases/newInRaketa';

import { discoveryKeys } from './discoveryKeys';
import { usePeopleRow } from './usePeopleRow';
import { useSeeAllPages, type SeeAllList } from './useSeeAllPages';

/** Home's row — re-read on return and by every friend write (`usePeopleRow`). */
export function useNewInRaketa() {
  return usePeopleRow<Joiner>(discoveryKeys.newInRaketa(), (signal) => readNewInRaketa({ signal }));
}

/** **See all** — 20 Joiners to a page, newest first; a sport keeps who holds a level in it. */
export function useNewInRaketaPage(choice: SeeAllSport): SeeAllList<Joiner> {
  return useSeeAllPages(discoveryKeys.newInRaketaAll(choice), (after, signal) =>
    readNewInRaketaPage({ sport: pageSport(choice), after }, { signal }),
  );
}

/** **Every Discovery read, again** — the row and every See all, for every sport read: Home's pull. */
export function rereadDiscovery(client: QueryClient): Promise<unknown> {
  return client.invalidateQueries({ queryKey: discoveryKeys.all });
}

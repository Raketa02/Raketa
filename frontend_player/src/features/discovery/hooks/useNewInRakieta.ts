/**
 * **New in Rakieta, read** ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows
 * mechanics §3, §7, §13).
 *
 * | | |
 * | --- | --- |
 * | `useNewInRakieta` | `GET /new-in-rakieta` — Home's row, on its own: a slow or failed read holds up nothing else on Home |
 * | `useNewInRakietaPage` | `GET /new-in-rakieta/all?sport&after` — See all, 20 to a page, read on as the grid nears its end (`useSeeAllPages`) |
 * | `rereadDiscovery` | every Discovery read — Home's pull |
 *
 * **Coming back to Home re-reads the row once its last read is older than thirty seconds** (Q22) —
 * the app's `staleTime`, as Hottest groups does; foregrounding does the same through the focus
 * manager. The row is the 10 newest, so a return after somebody joined shows them.
 *
 * **One tap moves a person everywhere** (§13): both reads declare `LISTS_PEOPLE`, so every friend
 * write — wherever it is made — reaches the row, holding still under the thumb (`usePeopleRow`), and
 * every See all, which reads again; the round button's write settles once they have. Every block
 * re-reads both. `rereadDiscovery` is Home's pull.
 */

import type { QueryClient } from '@tanstack/react-query';

import type { Joiner } from '../domain/joiner';
import { pageSport, type SeeAllSport } from '../domain/seeAll';
import { readNewInRakieta, readNewInRakietaPage } from '../use-cases/newInRakieta';

import { discoveryKeys } from './discoveryKeys';
import { peopleRowRead, usePeopleRow } from './usePeopleRow';
import { useSeeAllPages, type SeeAllList } from './useSeeAllPages';

/** Home's row's read — the hook's, and Home's warm-up's (#874). */
export const newInRakietaRow = peopleRowRead<Joiner>(discoveryKeys.newInRakieta(), (signal) =>
  readNewInRakieta({ signal }),
);

/** Home's row — re-read on return, holding still under a friend write (`usePeopleRow`). */
export function useNewInRakieta() {
  return usePeopleRow(newInRakietaRow);
}

/** **See all** — 20 Joiners to a page, newest first; a sport keeps who holds a level in it. */
export function useNewInRakietaPage(choice: SeeAllSport): SeeAllList<Joiner> {
  return useSeeAllPages(discoveryKeys.newInRakietaAll(choice), (after, signal) =>
    readNewInRakietaPage({ sport: pageSport(choice), after }, { signal }),
  );
}

/** **Every Discovery read, again** — the row and every See all, for every sport read: Home's pull. */
export function rereadDiscovery(client: QueryClient): Promise<unknown> {
  return client.invalidateQueries({ queryKey: discoveryKeys.all });
}

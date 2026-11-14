/**
 * **New in Raketa, read** ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows
 * mechanics §3, §7, §13).
 *
 * | | |
 * | --- | --- |
 * | `useNewInRaketa` | `GET /new-in-raketa` — Home's row, on its own: a slow or failed read holds up nothing else on Home |
 * | `useNewInRaketaPage` | `GET /new-in-raketa/all?sport&after` — See all, 20 to a page, read on as the grid nears its end |
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

import {
  useInfiniteQuery,
  useQuery,
  useQueryClient,
  type InfiniteData,
  type QueryClient,
} from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';
import { LISTS_PEOPLE } from '@/shared/lib/query-client';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  joinPages,
  pageSport,
  type Joiner,
  type JoinerPage,
  type SeeAllSport,
} from '../domain/joiner';
import { readNewInRaketa, readNewInRaketaPage } from '../use-cases/newInRaketa';

import { discoveryKeys } from './discoveryKeys';

export function useNewInRaketa() {
  const client = useQueryClient();

  useOnReturn(() => {
    void client.refetchQueries({ queryKey: discoveryKeys.newInRaketa(), stale: true });
  });

  return useQuery<readonly Joiner[], AppError>({
    queryKey: discoveryKeys.newInRaketa(),
    queryFn: ({ signal }) => readNewInRaketa({ signal }),
    meta: LISTS_PEOPLE,
  });
}

type Pages = InfiniteData<JoinerPage, string | undefined>;

/** **See all, as the screen reads it** — the grid so far, the pill's sports, and its states. */
export interface JoinerGrid {
  /** Every Joiner read so far, newest first — `undefined` until the first page lands. */
  readonly joiners: readonly Joiner[] | undefined;
  /** The sports the first page says at least one Joiner holds a level in. */
  readonly sports: readonly Sport[] | undefined;
  /** The first page's failure, while nothing is drawn. */
  readonly error: AppError | null;
  /** Waiting for a connection to read the first page. */
  readonly paused: boolean;
  /** A later page refused, with the way to ask for it again. */
  readonly moreFailure: { readonly error: AppError; readonly retry: () => void } | undefined;
  /** The grid neared its end: read the next page, if there is one and it is not already coming. */
  readonly loadMore: () => void;
  /** The pull's — every page read again. */
  readonly reread: () => Promise<unknown>;
  readonly retry: () => void;
}

export function useNewInRaketaPage(choice: SeeAllSport): JoinerGrid {
  const read = useInfiniteQuery<
    JoinerPage,
    AppError,
    Pages,
    readonly unknown[],
    string | undefined
  >({
    queryKey: discoveryKeys.newInRaketaAll(choice),
    queryFn: ({ pageParam, signal }) =>
      readNewInRaketaPage({ sport: pageSport(choice), after: pageParam }, { signal }),
    initialPageParam: undefined,
    getNextPageParam: (page) => page.next,
    meta: LISTS_PEOPLE,
  });

  const loadMore = () => {
    if (!read.hasNextPage || read.isFetchingNextPage || read.isRefetching) return;
    // `cancelRefetch: false`: an end reached while its page is on its way joins it.
    void read.fetchNextPage({ cancelRefetch: false });
  };

  return {
    joiners: read.data === undefined ? undefined : joinPages(read.data.pages),
    sports: read.data?.pages[0]?.sports,
    error: read.data === undefined ? read.error : null,
    paused: read.fetchStatus === 'paused',
    moreFailure:
      read.isFetchNextPageError && read.error !== null
        ? { error: read.error, retry: loadMore }
        : undefined,
    loadMore,
    reread: () => read.refetch(),
    retry: () => void read.refetch(),
  };
}

/** **Every Discovery read, again** — the row and every See all, for every sport read: Home's pull. */
export function rereadDiscovery(client: QueryClient): Promise<unknown> {
  return client.invalidateQueries({ queryKey: discoveryKeys.all });
}

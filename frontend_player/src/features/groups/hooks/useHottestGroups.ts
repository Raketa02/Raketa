/**
 * **Home's Hottest groups, read** ([#800](https://github.com/Rakieta02/Rakieta/issues/800); the Home
 * rows mechanics §3, §13).
 *
 * | | |
 * | --- | --- |
 * | `useHottestGroups` | `GET /hottest-groups` — the row, on its own: a slow or failed read holds up nothing else on Home |
 * | `useHottestGroupsPage` | `GET /hottest-groups/all?after` — *Groups heating up*, 20 to a page, read on as the list nears its end (#823) |
 * | `rereadHomeGroups` | the pull's — the row and the Groups list read again now, so the spinner stops on both |
 *
 * **Coming back to Home re-reads the row once its last read is older than thirty seconds** (the
 * mechanics §3, Q22) — the app's `staleTime`, so a return a moment after a read asks nothing, and the
 * group page pushed over Home is the usual way back. Foregrounding the app does the same through the
 * focus manager, on the same stale rule.
 */

import {
  queryOptions,
  useInfiniteQuery,
  useQuery,
  useQueryClient,
  type InfiniteData,
  type QueryClient,
} from '@tanstack/react-query';
import { useEffect, useMemo, useRef } from 'react';

import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';
import { LISTS_PEOPLE, useReadFinished } from '@/shared/lib/query-client';

import type { HottestGroup, HottestPage, HottestRow } from '../domain/group';
import { joinHottestPages } from '../domain/hottest';
import { readHottestGroups, readHottestGroupsPage } from '../use-cases/groupReads';

import { groupKeys } from './groupKeys';
import { myGroupsRead } from './useGroups';

/** The row's read, as one definition — what the hook observes and Home's warm-up sets out (#874). */
const hottestRead = queryOptions<HottestRow, AppError>({
  queryKey: groupKeys.hottest(),
  queryFn: ({ signal }) => readHottestGroups({ signal }),
  // Its faces are friends first, and the sheet counts them: a friend write re-reads it (#801).
  meta: LISTS_PEOPLE,
});

export function useHottestGroups() {
  const client = useQueryClient();

  useOnReturn(() => {
    void client.refetchQueries({ queryKey: groupKeys.hottest(), stale: true });
  });

  return useQuery(hottestRead);
}

/**
 * **Whether Groups heating up's read has finished** (#871) — landed, refused, held for a connection,
 * or failed once and retrying: one of the reads FOR YOU waits on before Home reveals it. Read off the
 * cache, so it draws again only as it turns.
 */
export function useHottestGroupsFinished(): boolean {
  return useReadFinished(groupKeys.hottest());
}

/** ***Groups heating up*, as the page reads it** — the list so far, and its states. */
export interface HottestGroupsList {
  /** Every group read so far, in the row's order, each once — `undefined` until the first page lands. */
  readonly groups: readonly HottestGroup[] | undefined;
  /** The first page's failure, while nothing is drawn. */
  readonly error: AppError | null;
  /** Waiting for a connection to read the first page. */
  readonly paused: boolean;
  /** A later page refused, with the way to ask for it again. */
  readonly moreFailure: { readonly error: AppError; readonly retry: () => void } | undefined;
  /** The list neared its end: read the next page, if there is one and it is not already coming. */
  readonly loadMore: () => void;
  /** The pull's — every page read again. */
  readonly reread: () => Promise<unknown>;
  readonly retry: () => void;
}

type HottestPages = InfiniteData<HottestPage, string | undefined>;

/**
 * ***Groups heating up*, page by page** ([#823](https://github.com/Rakieta02/Rakieta/issues/823);
 * ADR-0205 §7) — `GET /hottest-groups/all`, 20 to a page, the next read as the list nears its end, as
 * the people See all screens read theirs. **It lists people too** — the faces are the reader's friends
 * first, and the sheet counts them — so it declares `LISTS_PEOPLE`, and a friend write reads every page
 * again, as it does the row. A join, an ask and a withdraw move its cards as they move the row's
 * (`useGroupWrites`).
 */
export function useHottestGroupsPage(): HottestGroupsList {
  const read = useInfiniteQuery<
    HottestPage,
    AppError,
    HottestPages,
    ReturnType<typeof groupKeys.hottestAll>,
    string | undefined
  >({
    queryKey: groupKeys.hottestAll(),
    queryFn: ({ pageParam, signal }) => readHottestGroupsPage(pageParam, { signal }),
    initialPageParam: undefined,
    getNextPageParam: (page) => page.next,
    meta: LISTS_PEOPLE,
  });

  const groups = useMemo(
    () => (read.data === undefined ? undefined : joinHottestPages(read.data.pages)),
    [read.data],
  );
  const pages = read.data?.pages.length ?? 0;

  // **The end the list reached, until a page behind it draws something new** — what the list held
  // then. The list only says it reached its end when it has grown since, so a page that never landed
  // or added nobody is asked for again here, or never: a relation write cancels the page on its way
  // and re-reads only the pages drawn (`useGroupWrites`), a re-read in flight holds the ask, and a page
  // can bring back only groups that cooled behind its cursor (the mechanics §5.10).
  const owed = useRef<{ readonly pages: number; readonly groups: number }>();

  const loadMore = () => {
    if (!read.hasNextPage) return;
    owed.current ??= { pages, groups: groups?.length ?? 0 };
    if (read.isFetchingNextPage || read.isRefetching) return;
    // `cancelRefetch: false`: an end reached while its page is on its way joins it.
    void read.fetchNextPage({ cancelRefetch: false });
  };

  useEffect(() => {
    const end = owed.current;
    if (end === undefined || read.isFetching || read.fetchStatus === 'paused') return;
    const drewMore = pages > end.pages && (groups?.length ?? 0) > end.groups;
    if (drewMore || read.isFetchNextPageError || !read.hasNextPage) {
      // Grown, refused — its failure says so, with *Try again* — or at the end of the list.
      owed.current = undefined;
      return;
    }
    void read.fetchNextPage({ cancelRefetch: false });
  });

  return {
    groups,
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

/**
 * **Home's pull** (the mechanics §3) — the row, and the Groups list the groupless line is drawn from,
 * so a group joined on another phone takes the line away when the spinner stops.
 */
export function rereadHomeGroups(client: QueryClient): Promise<unknown> {
  return Promise.all([
    client.invalidateQueries({ queryKey: groupKeys.hottest() }),
    client.invalidateQueries({ queryKey: groupKeys.mine() }),
  ]);
}

/**
 * **Home's two group reads, set out before Home is drawn** (#874) — the launch's warm-up, during the
 * splash: the row, and the Groups list the groupless line and the level card are drawn from, the two
 * the pull reads again. Under the hooks' own definitions, so Home finds them fresh when it mounts.
 */
export function prefetchHomeGroups(client: QueryClient): Promise<unknown> {
  return Promise.all([client.prefetchQuery(hottestRead), client.prefetchQuery(myGroupsRead)]);
}

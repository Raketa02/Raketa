/**
 * **A people row's See all, read page by page** ([#801](https://github.com/Raketa02/Raketa/issues/801),
 * [#802](https://github.com/Raketa02/Raketa/issues/802); the Home rows mechanics §6.7, §7.4, §13) —
 * 20 to a page, the next read as the list nears its end, one entry per sport.
 *
 * **One tap moves a person everywhere** (§13): the read declares `LISTS_PEOPLE`, so every friend
 * write and every block — wherever it is made — reads every page again.
 */

import { useInfiniteQuery, type InfiniteData, type QueryKey } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { LISTS_PEOPLE } from '@/shared/lib/query-client';
import type { Sport } from '@/shared/vocabulary/sport';

import { joinPages, type SeeAllPage } from '../domain/seeAll';

/** **See all, as the screen reads it** — the list so far, the pill's sports, and its states. */
export interface SeeAllList<Person> {
  /** Everybody read so far, in the server's order — `undefined` until the first page lands. */
  readonly people: readonly Person[] | undefined;
  /** The sports the first page offers the pill. */
  readonly sports: readonly Sport[] | undefined;
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

type Pages<Person> = InfiniteData<SeeAllPage<Person>, string | undefined>;

export function useSeeAllPages<Person extends { readonly playerId: string }>(
  queryKey: QueryKey,
  readPage: (after: string | undefined, signal: AbortSignal) => Promise<SeeAllPage<Person>>,
): SeeAllList<Person> {
  const read = useInfiniteQuery<
    SeeAllPage<Person>,
    AppError,
    Pages<Person>,
    QueryKey,
    string | undefined
  >({
    queryKey,
    queryFn: ({ pageParam, signal }) => readPage(pageParam, signal),
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
    people: read.data === undefined ? undefined : joinPages(read.data.pages),
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

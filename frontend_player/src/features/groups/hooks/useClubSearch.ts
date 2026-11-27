/**
 * **The two searches** — New group's home club and Join a group — as one hook over two routes.
 * The home-club search has a third caller: *Pick a club near where you play*, the player
 * profile's way to an area without the phone's location (#733, ADR-0200 §10).
 *
 * **A new question on every keystroke** (story 32): the text is the key, so each letter asks
 * again and the previous letter's request is abandoned through its `signal`. **The answer on
 * screen stays until the next one lands** (`keepPreviousData`), so the list narrows under the
 * finger rather than blanking between letters — except after a blank text, which is ✕ having
 * cleared it. There is no debounce: the ticket asks for every
 * keystroke, and the cancelled reads cost nothing (`groupsApi`'s note).
 *
 * **Twenty clubs at a time, more as the list scrolls** (story 17): an infinite query over the
 * server's `next_page`, and `loadMore` asks for the next page only when there is one and none is
 * already on its way.
 *
 * **A blank text asks nothing** — the server would answer nothing, and the screens draw their
 * empty state without a round trip.
 *
 * **An answer lives only while it is on screen** (`gcTime: 0`, `staleTime: 0`). A search answer
 * carries the reader's relation to every group in it, and that relation changes on another phone:
 * an Owner lets them in, or declines. Kept by text, the answer to `og` read before the approval was
 * drawn again the next time `og` was typed — so as the reader typed, the row flipped between
 * *requested · waiting* and *you're in*, letter by letter (#529 D6). So a text that is typed again
 * is asked again, and what bridges the letters is only the answer on screen (`keepPreviousData`),
 * never one kept from before.
 */

import { keepPreviousData, useInfiniteQuery, type InfiniteData } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';

import type { AppError } from '@/shared/errors';

import type { ClubSearch } from '../domain/group';
import { searchHomeClubs, searchToJoin } from '../use-cases/groupReads';

import { groupKeys } from './groupKeys';

export interface ClubSearchState {
  /** The text as asked — trimmed. */
  readonly text: string;
  /** Every page so far, as one answer. `undefined` for a blank text and before the first answer. */
  readonly answer: ClubSearch | undefined;
  readonly error: AppError | null;
  readonly loadMore: () => void;
  readonly retry: () => void;
}

type Search = (
  text: string,
  page: number,
  options: { signal?: AbortSignal },
) => Promise<ClubSearch>;

function useClubSearch(
  key: (text: string) => readonly unknown[],
  search: Search,
  typed: string,
): ClubSearchState {
  const text = typed.trim();
  const asking = text !== '';

  const query = useInfiniteQuery<
    ClubSearch,
    AppError,
    InfiniteData<ClubSearch, number>,
    readonly unknown[],
    number
  >({
    queryKey: key(text),
    queryFn: ({ pageParam, signal }) => search(text, pageParam, { signal }),
    initialPageParam: 1,
    getNextPageParam: (last) => last.nextPage ?? undefined,
    enabled: asking,
    placeholderData: keepPreviousData,
    staleTime: 0,
    gcTime: 0,
  });

  // The last answer stays on screen while the next text is asked — **but never across a blank
  // text**: ✕ cleared it (story 31), and the next letter must not bring it back. Query offers the
  // last answer that had data whatever came between, so the blank is remembered here, and a
  // placeholder is not drawn after one until a real answer has landed.
  const cleared = useRef(false);
  useEffect(() => {
    if (!asking) cleared.current = true;
    else if (query.data !== undefined && !query.isPlaceholderData) cleared.current = false;
  });
  const stale = query.isPlaceholderData && cleared.current;

  const pages = asking && !stale ? query.data?.pages : undefined;
  const [first] = pages ?? [];
  const answer =
    pages === undefined || first === undefined
      ? undefined
      : {
          ...first,
          clubs: pages.flatMap((page) => page.clubs),
          nextPage: pages[pages.length - 1]?.nextPage ?? null,
        };

  return {
    text,
    answer,
    error: asking ? query.error : null,
    loadMore: () => {
      if (query.hasNextPage && !query.isFetchingNextPage) void query.fetchNextPage();
    },
    retry: () => void query.refetch(),
  };
}

/** Every club in Rakieta whose name or district holds the text — New group's home club field. */
export function useHomeClubSearch(typed: string): ClubSearchState {
  return useClubSearch(groupKeys.homeClubs, searchHomeClubs, typed);
}

/** Clubs, districts, group names and links — Join a group's one field. */
export function useJoinSearch(typed: string): ClubSearchState {
  return useClubSearch(groupKeys.toJoin, searchToJoin, typed);
}

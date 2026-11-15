/**
 * **General, as the page reads it** ([#775](https://github.com/Raketa02/Raketa/issues/775),
 * [#776](https://github.com/Raketa02/Raketa/issues/776); the screens §4, §5.3) — the main read, and the
 * list in pages of 50.
 *
 * **Two windows over one list, each an infinite query.**
 *
 * - **From the top**: the main read is its first page — the card, the podium and the first 50 rows,
 *   one kept order's — and each page after it is read below the last one's cursor as the list nears
 *   its end.
 * - **Around the reader**: the *You · 212th* button's page, the reader in the middle, and from there
 *   the page above or below as the list nears either end. It is read only once the button is
 *   pressed, and **drawn only once it has landed** — until then the list stays where it was, so a jump
 *   never blanks the page. Each press reads it afresh, from the reader's place as it stands.
 *
 * The card and the podium are always the main read's: around the reader the page still knows the
 * reader's place, and draws them above the rows once the window reaches the top of the list. What it
 * hands the page is `RankingRead`, the shape the Friends table hands it too (#777).
 *
 * **The app's defaults, chosen** (architecture Part 7): a place moves when a result settles anywhere
 * in Raketa and the server keeps a sport's order for at most a minute (the rankings mechanics §15),
 * so the moderate class's 30 seconds is fresh enough while the page is up, foregrounding reads it
 * again, and **opening it always does** (the screens §2–§3: switching sport or view re-reads the page). **A read again is every page drawn**, one after another, each below the fresh one before
 * it — the query's own refetch, so the window stays whole; a reader deep in the list pays a page a
 * round trip for it, which is what keeps the rows on screen agreeing with each other.
 *
 * **Nothing follows a switch.** The page once re-read itself a second at a time behind *Show me in
 * General* (#778); that switch and the hidden card it drove are gone (ADR-0204 §2,
 * [#799](https://github.com/Raketa02/Raketa/issues/799)) — the ranking lists everybody, so there is
 * nothing for the reader's own card to catch up with.
 *
 * **A page is asked for only when there is one, and never twice**: an end reached while that page is
 * on its way joins it. **An end reached while the list is read again is owed**, and asked for once
 * that read has landed — the platform's list says an end once, and would not say it again to a
 * reader holding still at it.
 */

import { useInfiniteQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { joinPages, jumpPlace, type PageAt } from '../domain/ranking';
import { readGeneralPage, type GeneralRead } from '../use-cases/readGeneralPage';

import { rankingKeys } from './rankingKeys';
import type { ListWindow, RankingRead } from './rankingRead';

type Pages = InfiniteData<GeneralRead, PageAt>;

const below = (page: GeneralRead): PageAt | undefined =>
  page.next === undefined ? undefined : { at: 'after', cursor: page.next };
const above = (page: GeneralRead): PageAt | undefined =>
  page.previous === undefined ? undefined : { at: 'before', cursor: page.previous };

/** General for one sport. */
export function useGeneral(sport: Sport): RankingRead {
  const queryClient = useQueryClient();
  const [jumped, setJumped] = useState(false);
  const read = ({ pageParam, signal }: { pageParam: PageAt; signal: AbortSignal }) =>
    readGeneralPage(sport, pageParam, { signal });

  const top = useInfiniteQuery<GeneralRead, AppError, Pages, readonly unknown[], PageAt>({
    queryKey: rankingKeys.generalFromTheTop(sport),
    queryFn: read,
    initialPageParam: { at: 'top' },
    getNextPageParam: below,
    // Opening General — the page, another sport, or the switch back from Friends — always reads it.
    refetchOnMount: 'always',
  });

  const aroundMe = useInfiniteQuery<GeneralRead, AppError, Pages, readonly unknown[], PageAt>({
    queryKey: rankingKeys.generalAroundMe(sport),
    queryFn: read,
    initialPageParam: { at: 'aroundMe' },
    getNextPageParam: below,
    getPreviousPageParam: above,
    enabled: jumped,
  });

  const drawn: ListWindow = jumped && aroundMe.data !== undefined ? 'aroundMe' : 'fromTheTop';
  const shown = drawn === 'aroundMe' ? aroundMe : top;
  const pages = shown.data?.pages ?? [];
  // The page the window read first — the reader's own after a jump, until a pull reads them all.
  const first = Math.max(0, shown.data?.pageParams.findIndex((at) => at.at === 'aroundMe') ?? 0);

  const owedEnd = useRef<'earlier' | 'later'>();
  const ask = (end: 'earlier' | 'later') => {
    const more = end === 'later' ? shown.hasNextPage : shown.hasPreviousPage;
    if (!more) return;
    if (shown.isRefetching) {
      owedEnd.current = end;
      return;
    }
    // `cancelRefetch: false`: an end reached while its page is on its way joins it, rather than
    // cancelling it and asking again — two ends reached in one tick both see the render before.
    if (end === 'later') void shown.fetchNextPage({ cancelRefetch: false });
    else void shown.fetchPreviousPage({ cancelRefetch: false });
  };
  useEffect(() => {
    const end = owedEnd.current;
    if (end === undefined || shown.isFetching) return;
    owedEnd.current = undefined;
    ask(end);
  });

  const jumpToMe = () => {
    // Afresh every time: the reader's place moves whenever a result settles anywhere in Raketa.
    void queryClient.resetQueries({ queryKey: rankingKeys.generalAroundMe(sport), exact: true });
    setJumped(true);
  };
  const failure = (refused: boolean, retry: () => void, error = shown.error) =>
    refused && error !== null ? { error, retry } : undefined;

  const ranking = top.data?.pages[0]?.ranking;
  const place = jumpPlace(ranking?.card);

  return {
    ranking,
    error: top.data === undefined ? top.error : null,
    paused: top.fetchStatus === 'paused',
    window: drawn,
    rows: joinPages(pages, first),
    atTheTop: pages[0]?.previous === undefined,
    loadEarlier: () => ask('earlier'),
    loadLater: () => ask('later'),
    earlierFailure: failure(shown.isFetchPreviousPageError, () => ask('earlier')),
    laterFailure: failure(shown.isFetchNextPageError, () => ask('later')),
    jump:
      place === undefined
        ? undefined
        : {
            place,
            toMe: jumpToMe,
            failure: failure(jumped && aroundMe.data === undefined, jumpToMe, aroundMe.error),
          },
    reread: () =>
      Promise.all([top.refetch(), ...(drawn === 'aroundMe' ? [aroundMe.refetch()] : [])]),
    retry: () => void top.refetch(),
  };
}

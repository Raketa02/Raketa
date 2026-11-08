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
 * reader's place, and draws them above the rows once the window reaches the top of the list.
 *
 * **The app's defaults, chosen** (architecture Part 7): a place moves when a result settles anywhere
 * in Raketa and the server keeps a sport's order for at most a minute (the rankings mechanics §15),
 * so the moderate class's 30 seconds is fresh enough, and opening the page or foregrounding reads it
 * again. **A read again is every page drawn**, one after another, each below the fresh one before
 * it — the query's own refetch, so the window stays whole; a reader deep in the list pays a page a
 * round trip for it, which is what keeps the rows on screen agreeing with each other.
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

import { joinPages, jumpPlace, type PageAt, type RankedRow, type Ranking } from '../domain/ranking';
import { readGeneralPage, type GeneralRead } from '../use-cases/readGeneralPage';

import { rankingKeys } from './rankingKeys';

/** A page of the list that could not be read — said where it was asked for, with its Try again. */
export interface PageFailure {
  readonly error: AppError;
  readonly retry: () => void;
}

/** **The jump** — the reader's place, while they are listed and shown in General. */
export interface Jump {
  readonly place: number;
  /** Read the page around the reader — for a row the list has not read yet. */
  readonly toMe: () => void;
  readonly failure: PageFailure | undefined;
}

/** Which window of the list is drawn — a new one is a new list, centred on the reader. */
export type GeneralWindow = 'fromTheTop' | 'aroundMe';

export interface GeneralState {
  /** The main read — the card, the podium, how many are listed. `undefined` until it lands. */
  readonly ranking: Ranking | undefined;
  /** The main read's own failure, while there is nothing to draw. */
  readonly error: AppError | null;
  /** The main read is waiting for a connection. */
  readonly paused: boolean;
  readonly window: GeneralWindow;
  /** The rows drawn, best first. */
  readonly rows: readonly RankedRow[];
  /** The rows start at place 1 — the card and the podium stand above them. */
  readonly atTheTop: boolean;
  readonly loadEarlier: () => void;
  readonly loadLater: () => void;
  /** The page above, and the page below, refused. */
  readonly earlierFailure: PageFailure | undefined;
  readonly laterFailure: PageFailure | undefined;
  /** Absent while the reader isn't listed, or is hidden: no button. */
  readonly jump: Jump | undefined;
  /** A pull: everything drawn, read again. Settles once every read has landed, refused or not. */
  readonly reread: () => Promise<unknown>;
  readonly retry: () => void;
}

type Pages = InfiniteData<GeneralRead, PageAt>;

const below = (page: GeneralRead): PageAt | undefined =>
  page.next === undefined ? undefined : { at: 'after', cursor: page.next };
const above = (page: GeneralRead): PageAt | undefined =>
  page.previous === undefined ? undefined : { at: 'before', cursor: page.previous };

export function useGeneral(sport: Sport): GeneralState {
  const queryClient = useQueryClient();
  const [jumped, setJumped] = useState(false);
  const read = ({ pageParam, signal }: { pageParam: PageAt; signal: AbortSignal }) =>
    readGeneralPage(sport, pageParam, { signal });

  const top = useInfiniteQuery<GeneralRead, AppError, Pages, readonly unknown[], PageAt>({
    queryKey: rankingKeys.generalFromTheTop(sport),
    queryFn: read,
    initialPageParam: { at: 'top' },
    getNextPageParam: below,
  });

  const aroundMe = useInfiniteQuery<GeneralRead, AppError, Pages, readonly unknown[], PageAt>({
    queryKey: rankingKeys.generalAroundMe(sport),
    queryFn: read,
    initialPageParam: { at: 'aroundMe' },
    getNextPageParam: below,
    getPreviousPageParam: above,
    enabled: jumped,
  });

  const drawn: GeneralWindow = jumped && aroundMe.data !== undefined ? 'aroundMe' : 'fromTheTop';
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

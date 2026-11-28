/**
 * **Home's Top 10, read** ([#805](https://github.com/Rakieta02/Rakieta/issues/805); the Home rows
 * mechanics §3, §10; the screens §7) — on its own, so a slow or failed read holds up nothing else on
 * Home.
 *
 * - **It opens on the trophy's sport**, else the deck's last, else padel (`useOpeningSport`, the
 *   Rankings page's own reads), **sent as the preferred sport**: the server falls through to the next
 *   sport where somebody is ranked, and says which it chose. Nothing is read until that sport is known.
 * - **A pick on the pill is asked for exactly** — *Nobody ranked in squash yet* for a sport with
 *   nobody in it — and is held while Home is up, kept nowhere (§10.3).
 * - **A pick re-reads this row and nothing else**: its own query, and **the cards on screen stay until
 *   the new ones land** (`keepPreviousData`), so the row never empties under the pill and no other row
 *   blinks. The pill says the picked sport at once.
 * - **A pick whose read fails puts the pill back** on the sport before it, whose cards never left — a
 *   call: the screens leave a failed row out, and a row that vanished on a pick would take the pill
 *   with it.
 * - **Coming back to Home re-reads it once its last read is older than thirty seconds**, as every row
 *   does; foregrounding does the same through the focus manager. `rereadTopTen` is Home's pull.
 *
 * It lists people, but no friend write moves anybody in it — it shows the ranking, which neither a
 * friendship nor a block changes (ADR-0204 §2) — so it declares no `LISTS_PEOPLE`.
 */

import {
  hashKey,
  keepPreviousData,
  skipToken,
  useQuery,
  useQueryClient,
  type QueryClient,
  type QueryState,
} from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';

import { prefetchDeckSport } from '@/features/groups/types';
import { onboardingKeys } from '@/features/onboarding/types';
import { prefetchHome, proposalKeys } from '@/features/proposals/types';
import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';
import { readHasFinished, useQueryCacheAnswer } from '@/shared/lib/query-client';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  topTenAsk,
  topTenFace,
  topTenReadFinished,
  type TopTen,
  type TopTenAsk,
  type TopTenFace,
} from '../domain/topTen';
import { readTopTen } from '../use-cases/readTopTen';

import { rankingKeys } from './rankingKeys';
import { openingSportIn, useOpeningSport } from './useRankingsSport';

/** **A sport picked on the pill**, and the pick it was made over — where a failed read goes back to. */
interface PickedSport {
  readonly sport: Sport;
  readonly before: PickedSport | undefined;
}

export interface TopTenRead {
  /** What the row draws. */
  readonly face: TopTenFace;
  /** The pill's sports — all four, rated first — `undefined` while the ratings are read. */
  readonly sports: readonly Sport[] | undefined;
  /** The pill's sport: the one picked, else the one the read shows. */
  readonly sport: Sport | undefined;
  readonly pick: (sport: Sport) => void;
}

export function useTopTen(): TopTenRead {
  const client = useQueryClient();
  const { sports, opening } = useOpeningSport();
  const [picked, setPicked] = useState<PickedSport>();
  const ask = topTenAsk(picked?.sport, opening);

  // No sport yet is `skipToken` under a key of its own, as `useDeckCounts` keeps it.
  const read = useQuery<TopTen | null, AppError>({
    ...(ask === undefined
      ? { queryKey: rankingKeys.topTenUnasked(), queryFn: skipToken }
      : topTenRead(ask)),
    placeholderData: keepPreviousData,
  });

  useOnReturn(() => {
    void client.refetchQueries({ queryKey: rankingKeys.topTen(), type: 'active', stale: true });
  });

  /**
   * **The read last drawn** — what stays on screen while a pick's own read has nothing to show yet:
   * `keepPreviousData` keeps it while a read is out, but not past a failure, nor once the pick before
   * was cancelled under a second pick and is read again. So **the line never empties under the pill**
   * on a pick, whatever its reads do — which matters since #820: FOR YOU closes a line that stops being
   * shown, and an open Top 10 would close under the reader.
   */
  const lastDrawn = useRef<TopTen | null>();
  useEffect(() => {
    if (read.data !== undefined) lastDrawn.current = read.data;
  });

  // Derived state, as `usePersonSheet` keeps it: a pick that could not be read is undone at once.
  const undone = picked !== undefined && read.isError && read.data === undefined;
  if (undone) setPicked(picked.before);
  const shown = read.data ?? (picked !== undefined ? lastDrawn.current : undefined);

  return {
    face: topTenFace(shown),
    sports,
    sport: (undone ? picked.before?.sport : picked?.sport) ?? shown?.sport,
    pick: (sport) => setPicked({ sport, before: picked }),
  };
}

/** **One Top 10 read** — its key and its fetch: the row's, and Home's warm-up's (#874). */
function topTenRead(ask: TopTenAsk) {
  return {
    queryKey: rankingKeys.topTenAsked(ask),
    queryFn: ({ signal }: { readonly signal: AbortSignal }) => readTopTen(ask, { signal }),
  };
}

/**
 * **Top 10, set out before Home is drawn** (#874; ADR-0209 §2, amended 2026-11-24) — its chain
 * included. The row opens on the trophy's sport, off Home's read, else on the deck's, off the ratings
 * and the sport last picked (`openingSportIn`, the hook's own rule): so Home's read and the deck's two
 * are set out first, the deck's waited on only when the trophy names no sport, and then the row is
 * asked for the sport they name, under the key the hook will look for. Home finds it fresh when it
 * mounts and asks nothing twice; with no sport named, nothing is asked.
 */
export async function prefetchTopTen(client: QueryClient): Promise<void> {
  const deck = prefetchDeckSport(client);
  await prefetchHome(client);
  let ask = topTenAsk(undefined, openingSportIn(client));
  if (ask === undefined) {
    await deck;
    ask = topTenAsk(undefined, openingSportIn(client));
  }
  if (ask !== undefined) await client.prefetchQuery<TopTen | null, AppError>(topTenRead(ask));
}

/**
 * **Whether Top 10's read has finished** (#871) — `topTenReadFinished` over the cache: an asked Top 10
 * read, else the two reads its opening sport waits behind (`useOpeningSport`), Home's and the
 * ratings. What FOR YOU waits on before Home reveals it. Read off the cache, so it draws again only as
 * it turns.
 */
export function useTopTenFinished(): boolean {
  return useQueryCacheAnswer(topTenFinished);
}

function topTenFinished(client: QueryClient): boolean {
  const unasked = hashKey(rankingKeys.topTenUnasked());
  const asked = client
    .getQueryCache()
    .findAll({ queryKey: rankingKeys.topTen() })
    .filter((read) => read.queryHash !== unasked);
  return topTenReadFinished({
    asked: asked.length > 0,
    askedFinished: asked.some((read) => readHasFinished(read.state)),
    behindAFailure: [proposalKeys.home(), onboardingKeys.ratings()].some((key) =>
      failedUnanswered(client.getQueryState(key)),
    ),
  });
}

/** A read that has failed with nothing to show for it — retrying, or refused. */
function failedUnanswered(read: QueryState | undefined): boolean {
  return read !== undefined && read.data === undefined && read.fetchFailureCount > 0;
}

/** **Every Top 10 read, again** — Home's pull. */
export function rereadTopTen(client: QueryClient): Promise<unknown> {
  return client.invalidateQueries({ queryKey: rankingKeys.topTen() });
}

/**
 * **Which view Rankings is on, and the reader choosing another** ([#777](https://github.com/Raketa02/Raketa/issues/777);
 * the rankings screens §3, the mechanics §8) — *General* or *Friends*, remembered per account on the
 * phone, as the deck's last sport is
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md);
 * ADR-0203 §5). **The page and Home's trophy read this one value**, so the number on the trophy is
 * always the place on the page it opens, and a switch on the page is on the trophy beneath it at once.
 *
 * `view` is `undefined` until the phone has been read, and neither draws a view until then (§4: *no
 * screen draws one choice and then jumps to another*) — the page draws no switch, and the trophy no
 * number. The read is `usePlaySegment`'s posture, for its reasons: local, never waiting on the network
 * (`networkMode: 'always'`), once per account per session and kept for good, and every choice written
 * to the cache first and the phone second. **The write is not a mutation** — one key nothing waits
 * for and nothing retries.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { useReaderId } from '@/features/auth/types';
import { phonePreferenceKeys } from '@/shared/lib/preferences';

import { FIRST_VIEW } from '../domain/ranking';
import type { RankingView } from '../domain/vocabulary';
import { keepRankingView, readRankingView } from '../use-cases/rankingView';

export interface RankingViewState {
  /** The view to draw — `undefined` while the phone is being read. */
  readonly view: RankingView | undefined;
  readonly choose: (view: RankingView) => void;
}

export function useRankingView(): RankingViewState {
  const client = useQueryClient();
  // Whose choice this is — read from the cache once, and never observed (`useReaderId`).
  const account = useReaderId();

  const read = useQuery({
    queryKey: phonePreferenceKeys.one(account ?? '', 'rankingView'),
    queryFn: () => readRankingView(account ?? ''),
    enabled: account !== undefined,
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // A phone that cannot tell whose choice to read is a store that cannot be read, and that gives
  // General (ADR-0188 §4) — chosen in memory while the page is up, kept nowhere.
  const [unkept, setUnkept] = useState<RankingView>(FIRST_VIEW);

  const choose = useCallback(
    (view: RankingView) => {
      if (account === undefined) {
        setUnkept(view);
        return;
      }
      client.setQueryData(phonePreferenceKeys.one(account, 'rankingView'), view);
      void keepRankingView(account, view);
    },
    [account, client],
  );

  return { view: account === undefined ? unkept : read.data, choose };
}

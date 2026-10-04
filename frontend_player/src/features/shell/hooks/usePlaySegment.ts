/**
 * **Which segment Play is on, and the player choosing another** — remembered per account on the
 * phone ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)).
 *
 * `segment` is `undefined` until the store has been read, and the screen draws **nothing** until
 * then (§4: *no screen draws one choice and then jumps to another*). The read is local and never
 * waits on the network — `networkMode: 'always'`, because offline is exactly when a paused read
 * would leave Play blank — and it happens once per account per session: the answer is kept in the
 * cache for good, and every choice after that is written to the cache first and the phone second.
 *
 * **The write is not a mutation.** It is one key on the phone that nothing waits for and nothing
 * retries; a failed write loses only the next launch's copy, which the store already swallows.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { currentUserQuery } from '@/features/auth/types';
import { phonePreferenceKeys } from '@/shared/lib/preferences';

import { DEFAULT_PLAY_SEGMENT, type PlaySegment } from '../domain/playSegment';
import { keepPlaySegment, readPlaySegment } from '../use-cases/playSegment';

export interface PlaySegmentState {
  /** The segment to draw — `undefined` while the phone is being read. */
  readonly segment: PlaySegment | undefined;
  readonly choose: (segment: PlaySegment) => void;
}

export function usePlaySegment(): PlaySegmentState {
  const client = useQueryClient();
  // Whose choice this is — read from the cache once, as `useFeatureOnMount` reads it, and never
  // observed: an observer here would refetch `/users/me` on every entry to Play once it was stale.
  // The entry gate has always read the player before a tab can mount, and the account cannot
  // change under a mounted tab — a sign-out tears the tree down.
  const [account] = useState(() => client.getQueryData(currentUserQuery().queryKey)?.id);

  const read = useQuery({
    queryKey: phonePreferenceKeys.one(account ?? '', 'playSegment'),
    queryFn: () => readPlaySegment(account ?? ''),
    enabled: account !== undefined,
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // A phone that cannot tell whose choice to read is a store that cannot be read, and that gives
  // the defaults (ADR-0188 §4) — chosen in memory for as long as the screen is up, kept nowhere.
  const [unkept, setUnkept] = useState<PlaySegment>(DEFAULT_PLAY_SEGMENT);

  const choose = useCallback(
    (segment: PlaySegment) => {
      if (account === undefined) {
        setUnkept(segment);
        return;
      }
      client.setQueryData(phonePreferenceKeys.one(account, 'playSegment'), segment);
      void keepPlaySegment(account, segment);
    },
    [account, client],
  );

  return { segment: account === undefined ? unkept : read.data, choose };
}

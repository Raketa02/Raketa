/**
 * **The rows seen on a group page's tab** — what its badge is counted against, and the tab marking
 * what it has on screen ([ADR-0208](../../../../../docs/adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md),
 * [#849](https://github.com/Raketa02/Raketa/issues/849)). Fill in and You’re in today; Games from #850.
 *
 * **Kept per account on the phone** (`shared/lib/preferences`, one list per group, sport and tab) and
 * forgotten at sign-out; held in the query cache for the session, never in a store, as the opened
 * games are (`useOpenedGames`).
 *
 * **Never waited on** (§5) — the product owner's *a badge is a nudge, not a ledger*:
 * - **read once**, local and never paused for the network (`networkMode: 'always'`), the first time
 *   the tab bar asks — never before a first frame, and nothing holds for it;
 * - **until it has been read, no badge is drawn**, and the badge sits outside the layout, so when it
 *   arrives nothing moves;
 * - **written without waiting** — the cache first, the phone second, and a write that fails loses
 *   only the next launch's copy. **The write is not a mutation**: one key nothing waits for and
 *   nothing retries, as the last sport's is.
 */

import { useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import { useReaderId } from '@/features/auth/types';
import { phonePreferenceKeys, type SeenRowsPreference } from '@/shared/lib/preferences';
import type { Sport } from '@/shared/vocabulary/sport';

import { afterALook, sameSeen, unseenCount, type SeenTab } from '../domain/seen';
import { keepSeenRows, readSeenRows, seenRowsPreference } from '../use-cases/seenRows';

import { useLatest } from './useLatest';

function seenQuery(account: string, preference: SeenRowsPreference) {
  return {
    queryKey: phonePreferenceKeys.one(account, preference),
    queryFn: () => readSeenRows(account, preference),
    networkMode: 'always' as const,
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
  };
}

/**
 * **A tab's badge** — the ids it counts now (`counted`, `undefined` until its read has answered),
 * minus the ids seen (`unseenCount`). 0 — nothing drawn — until both are in.
 */
export function useUnseenCount(
  groupId: string,
  sport: Sport,
  tab: SeenTab,
  counted: readonly string[] | undefined,
): number {
  // Whose phone memory this is — read from the cache once, and never observed (`useReaderId`).
  const account = useReaderId();
  const read = useQuery({
    ...seenQuery(account ?? '', seenRowsPreference(groupId, sport, tab)),
    enabled: account !== undefined,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
  // A phone that cannot tell whose memory to read has nothing kept: nothing seen (ADR-0208 §4).
  const seen = account === undefined ? [] : read.data;
  return counted === undefined || seen === undefined ? 0 : unseenCount(counted, seen);
}

/**
 * **What a tab has in front of the player** — the ids it draws, and the ids its read still holds,
 * which the seen set is cut back to (`afterALook`). On You’re in they are the same; on Fill in the
 * read's rows include one past its deadline that the board's clock has dropped and the tab bar's —
 * a clock of its own — may count for a moment longer, so it stays seen until the read lets it go.
 */
export interface TabLook {
  readonly onScreen: readonly string[];
  readonly counted: readonly string[];
}

/**
 * **A tab marking what it has on screen as seen** — every time what it draws changes while it is
 * `inView`, so a row arriving under the player's eyes (a pull, a re-read) is seen at once, and one
 * arriving while a screen or a sheet covers the page is not, until the page is uncovered. `look`
 * is `undefined` until the tab's read has answered.
 */
export function useSeeRows(
  groupId: string,
  sport: Sport,
  tab: SeenTab,
  look: TabLook | undefined,
  inView: boolean,
): void {
  const client = useQueryClient();
  const account = useReaderId();
  const preference = seenRowsPreference(groupId, sport, tab);
  const latest = useLatest(look);
  // What is drawn and held, as one value — a re-render with the same rows marks nothing.
  const drawn =
    look === undefined ? undefined : `${look.onScreen.join(' ')}|${look.counted.join(' ')}`;

  useEffect(() => {
    const now = latest.current;
    if (!inView || now === undefined || account === undefined) return;
    // Nothing waits on a look, and one cut short — the session ending under it — is simply lost.
    lookAt(client, account, preference, now).catch(() => undefined);
  }, [account, client, drawn, inView, preference, latest]);
}

async function lookAt(
  client: QueryClient,
  account: string,
  preference: SeenRowsPreference,
  { onScreen, counted }: TabLook,
): Promise<void> {
  const query = seenQuery(account, preference);
  // What was kept, from the cache — or from the phone, when the tab is looked at before its badge
  // has read it: writing over a list never read would forget a row seen before that the read still
  // holds and the board no longer draws.
  await client.fetchQuery(query);
  // A session that ended during the read took the cache with it (`endSession`); writing now would
  // put back on the phone what the sign-out has just forgotten.
  if (client.getQueryState(query.queryKey) === undefined) return;
  const kept = client.getQueryData<readonly string[]>(query.queryKey) ?? [];
  const next = afterALook(kept, onScreen, counted);
  if (sameSeen(kept, next)) return;
  client.setQueryData(query.queryKey, next);
  await keepSeenRows(account, preference, next);
}

/**
 * **The profile an account wore last, and keeping a new one** — per account, on the phone
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2, [#518](https://github.com/Raketa02/Raketa/issues/518)).
 *
 * The Play segment's shape (`shell`'s `usePlaySegment`): the phone is read once per account per
 * session into the Query cache, under `phonePreferenceKeys`, and never waits on the network —
 * `networkMode: 'always'`, because offline is exactly when a paused read would hold the launch.
 * Every choice after that is written to the cache first and the phone second, fire and forget.
 *
 * **Its reader is the entry gate**, which opens an account with two profiles in the one it wore last
 * and so must not answer before the read has (§4: *no screen draws one choice and then jumps to
 * another*). Its writers are the switcher, *Start playing* and a removal: each changes which hat
 * the app has on, and the next launch has to agree.
 */

import { queryOptions, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { phonePreferenceKeys } from '@/shared/lib/preferences';

import type { AuthenticatedUser } from '../domain/AuthenticatedUser';
import type { ProfileChoice } from '../domain/lastProfile';
import { keepLastProfile, readLastProfile } from '../use-cases/lastProfile';

import { authKeys } from './authKeys';

/**
 * The read, as one definition. `null` is *read, and nothing chosen* — Query reserves `undefined` for
 * nothing cached, and a read that answered `undefined` would be recorded as a failure.
 */
function lastProfileQuery(account: string) {
  return queryOptions({
    queryKey: phonePreferenceKeys.one(account, 'lastProfile'),
    queryFn: async (): Promise<ProfileChoice | null> => (await readLastProfile(account)) ?? null,
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}

export interface LastProfile {
  /** What the phone holds for this account — `undefined` for nothing chosen, or not read yet. */
  readonly choice: ProfileChoice | undefined;
  /** Whether the phone has been read. Nothing may be decided from `choice` before it has. */
  readonly settled: boolean;
}

/**
 * @param account whose choice — `undefined` while the account is not known, which reads nothing.
 * @param enabled whether this caller may read yet — the gate's own *is there a session*.
 */
export function useLastProfile(account: string | undefined, enabled: boolean): LastProfile {
  const read = useQuery({
    ...lastProfileQuery(account ?? ''),
    enabled: enabled && account !== undefined,
  });

  return { choice: read.data ?? undefined, settled: read.isSuccess };
}

/**
 * **Keep the profile the app now wears**, for the signed-in account: into the cache at once — so a
 * gate reading it in the next instant already agrees — and onto the phone behind it. An account the
 * cache does not know keeps nothing, which is a store that cannot be written (ADR-0188 §4).
 */
export function useKeepProfile(): (choice: ProfileChoice) => void {
  const client = useQueryClient();

  return useCallback(
    (choice: ProfileChoice) => {
      const account = client.getQueryData<AuthenticatedUser>(authKeys.currentUser())?.id;
      if (account === undefined) return;
      client.setQueryData(lastProfileQuery(account).queryKey, choice);
      void keepLastProfile(account, choice);
    },
    [client],
  );
}

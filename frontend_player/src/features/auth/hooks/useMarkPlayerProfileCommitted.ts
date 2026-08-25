/**
 * Record, in the cache, that this player now has a Player profile.
 *
 * **The fact belongs to the authenticated player, so the write belongs to this feature.**
 * `has_player_profile` is served on `GET /users/me` and the entry gate's fourth branch is
 * read from it — so the shape of that cached entity is auth's to know, and a feature that
 * reshaped it from outside would be one release away from writing a field this one had
 * renamed.
 *
 * **Written and then invalidated, in that order**, which is the cache effect this app asks
 * every mutation to declare:
 *
 * - The **write** is immediate and is not a guess. Whoever calls this has just had the
 *   server create the thing the flag reports. Waiting for a round trip to learn it would
 *   let the gate answer from a stale `false` and route the player back into onboarding's
 *   second part the moment they finished it.
 * - The **invalidation** is what keeps the server the authority. The query is unobserved
 *   while onboarding runs, so nothing refetches now; it is marked stale and the next screen
 *   that reads the player asks.
 *
 * It takes no argument and returns nothing: there is one fact here and it only ever moves
 * in one direction. Nothing un-commits a Player profile.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type { AuthenticatedUser } from '../domain/AuthenticatedUser';

import { authKeys } from './authKeys';

export function useMarkPlayerProfileCommitted(): () => void {
  const queryClient = useQueryClient();

  return useCallback(() => {
    queryClient.setQueryData<AuthenticatedUser>(authKeys.currentUser(), (player) =>
      // Nothing cached to update — the entry gate will fetch it, and the server is about to
      // say the same thing. Returning `undefined` leaves the cache untouched rather than
      // inventing a player out of one boolean.
      player === undefined ? undefined : { ...player, hasPlayerProfile: true },
    );
    void queryClient.invalidateQueries({ queryKey: authKeys.currentUser() });
  }, [queryClient]);
}

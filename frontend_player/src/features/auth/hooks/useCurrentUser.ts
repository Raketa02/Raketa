/**
 * The signed-in player's profile — backend data, so TanStack Query owns it and nothing
 * mirrors it. The session machine holds a status and deliberately not this.
 */

import { queryOptions, useQuery } from '@tanstack/react-query';

import { useSessionStatus } from '@/shared/lib/auth';
import type { AppError } from '@/shared/errors';

import { me } from '../api/authApi';
import type { AuthenticatedUser } from '../domain/AuthenticatedUser';
import { toAuthenticatedUser } from '../mappers/authMappers';

import { authKeys } from './authKeys';

/**
 * The one read of the signed-in player — its key and its fetch, as one thing.
 *
 * Spelled once so the hook below and the naming's re-read (`useNamePlayer`) cannot disagree
 * about what `/users/me` is or how it is mapped: a second `queryFn` under the same key would
 * be two answers to one question, and the second is the one that drifts.
 */
export function currentUserQuery() {
  return queryOptions<AuthenticatedUser, AppError>({
    queryKey: authKeys.currentUser(),
    queryFn: ({ signal }) => me({ signal }).then(toAuthenticatedUser),
  });
}

/**
 * `enabled` on the session status, not on a token: an unauthenticated launch must not
 * fire an authenticated request that can only 401, and a 401 fired at launch is exactly
 * what would make the rotation chase a session that never existed.
 *
 * Bootstrap seeds this key when it validated a stored session, so a warm launch renders
 * the profile without a second request.
 */
export function useCurrentUser() {
  const status = useSessionStatus();

  return useQuery({
    ...currentUserQuery(),
    enabled: status === 'authenticated',
  });
}

/**
 * **How often the account is re-read while it runs a club's groups and the app is in front**
 * ([ADR-0192](../../../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)
 * §3): the query's own staleness, so a handover, an invitation or a removal the server already
 * knows reaches a screen nobody is touching within the same half minute it would reach a screen
 * somebody returns to.
 */
export const ACCOUNT_FOLLOWED_MS = 30_000;

/**
 * **The same read, followed** — a second observer of `/users/me` that re-reads it every
 * `ACCOUNT_FOLLOWED_MS` **while the account administers a club** and the app is in the foreground
 * (Query pauses an interval in the background, through the focus manager the app wires to
 * `AppState`). Nothing is fetched twice: it is the one query, with one more reason to refresh.
 *
 * Only an administrator is followed, because what it brings is theirs to hear — a club handing
 * them a group, or taking their profile away. A player who administers nothing hears an invitation
 * when the app comes back to the front, as before, and costs the server nothing while it sits open.
 */
export function useFollowedAccount() {
  const status = useSessionStatus();

  return useQuery({
    ...currentUserQuery(),
    enabled: status === 'authenticated',
    refetchInterval: (query) =>
      (query.state.data?.profiles.administers.length ?? 0) > 0 ? ACCOUNT_FOLLOWED_MS : false,
  });
}

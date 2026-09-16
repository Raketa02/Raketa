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

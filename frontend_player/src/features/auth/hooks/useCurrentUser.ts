/**
 * The signed-in player's profile — backend data, so TanStack Query owns it and nothing
 * mirrors it. The session machine holds a status and deliberately not this.
 */

import { queryOptions, useQuery, type QueryClient } from '@tanstack/react-query';

import { useSessionStatus } from '@/shared/lib/auth';
import type { TimeoutClass } from '@/shared/lib/http';
import type { AppError } from '@/shared/errors';

import { me } from '../api/authApi';
import type { AuthenticatedUser } from '../domain/AuthenticatedUser';
import { toAuthenticatedUser } from '../mappers/authMappers';

import { authKeys } from './authKeys';

/**
 * The one read of the signed-in player — its key and its fetch, as one thing.
 *
 * Spelled once so the hook below, the naming's re-read (`useNamePlayer`) and the launch's
 * validation cannot disagree about what `/users/me` is or how it is mapped: a second
 * `queryFn` under the same key would be two answers to one question, and the second is the
 * one that drifts. **How long it may take is the one thing a caller chooses**, and only the
 * launch chooses.
 */
export function currentUserQuery(timeout: TimeoutClass = 'request') {
  return queryOptions<AuthenticatedUser, AppError>({
    queryKey: authKeys.currentUser(),
    queryFn: ({ signal }) => me({ signal, timeout }).then(toAuthenticatedUser),
  });
}

/**
 * **The launch's validation of a stored session — the entry gate's first read**, asked once,
 * with the splash up, through the cache the gate reads.
 *
 * Through the cache so that **either answer is left where the gate looks.** An answer seeds
 * the player, so a warm launch's first screen asks nothing; a failure is left as the read's
 * error, so the gate opens on it — the first frame after the splash says the server could not
 * be reached — rather than asking again behind an empty screen, which on a connection that
 * reaches nothing was three more fifteen-second timeouts with nothing drawn.
 *
 * - **`launch` timeout.** Nothing gets past the splash, and giving up costs only the wait:
 *   `restoreSession` keeps an unanswered session.
 * - **No retry.** The gate retries, on a screen that says what is happening.
 * - **`networkMode: 'always'`.** The cache pauses a read while the phone says it is offline,
 *   and a paused launch read is a splash held until the connection comes back. Offline, it
 *   fails at once; the gate then says it is waiting, because the read the gate makes pauses.
 */
export function fetchCurrentUserAtLaunch(client: QueryClient): Promise<AuthenticatedUser> {
  return client.fetchQuery({
    ...currentUserQuery('launch'),
    retry: false,
    networkMode: 'always',
  });
}

/**
 * **The first read of a session a form opened** — sign-in, sign-up, an invitation's password, a
 * reset — asked _before_ the status opens, as `beginSession`'s `readFirst`
 * (`docs/specs/busy-indicator/decisions.md` §3.1).
 *
 * Opening the status unmounts the form, and the entry gate cannot choose where to go without this
 * read. Asked afterwards, the gate drew blank paper while it was out; asked first, the form's busy
 * button turns through the wait and the gate finds the answer here. The launch's sibling, and
 * through the same cache for the same reason: **either answer is left where the gate looks.**
 *
 * - **`request` timeout.** The button is turning, so an ordinary wait is an honest one.
 * - **No retry.** The gate retries, on a screen that says what is happening.
 * - **`networkMode: 'always'`.** A paused read would hold the button busy until the connection came
 *   back. Offline it fails at once, the session opens, and the gate says it is waiting.
 * - **`staleTime: 0`.** A new session's answer, never whatever a cache still holds.
 */
export function fetchCurrentUserAtSessionStart(client: QueryClient): Promise<AuthenticatedUser> {
  return client.fetchQuery({
    ...currentUserQuery(),
    staleTime: 0,
    retry: false,
    networkMode: 'always',
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

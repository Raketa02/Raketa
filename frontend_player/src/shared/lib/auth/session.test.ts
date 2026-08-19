/**
 * Ending a session, from where it is actually reached.
 *
 * `endSession` is almost never called from quiet code. Its real caller is a 401 that
 * arrived in a `queryFn`, went to the refresh coordinator, and came back rejected — so
 * the teardown runs **inside a query that is still in flight**, and its own second step
 * cancels that query.
 *
 * That is the case these tests exist for. A teardown that only finishes when nothing is
 * running is a teardown that does not finish at the one moment it matters, and the state
 * it leaves behind — no credentials, but a status that still says `authenticated` — is
 * worse than either end of the transition. Every request after it goes out with no
 * `Authorization` header, is refused, and cannot be recovered by rotating anything.
 */

import { queryClient } from '@/shared/lib/query-client';

import { getSessionStatus, resetSessionStatus, setSessionStatus } from './authSession';
import { endSession } from './session';
import { hasTokens, save } from './tokenManager';

beforeEach(async () => {
  resetSessionStatus();
  queryClient.clear();
  await save({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  setSessionStatus('authenticated');
});

afterEach(() => {
  queryClient.clear();
});

describe('ending a session', () => {
  it('leaves no credentials and an unauthenticated status', async () => {
    await endSession('requested');

    expect(hasTokens()).toBe(false);
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  it('is safe to call twice, because several failing requests can each conclude it', async () => {
    await endSession('session-invalidated');
    await endSession('session-invalidated');

    expect(getSessionStatus()).toBe('unauthenticated');
  });

  it('finishes when it is called from inside a query that is still running', async () => {
    // The real shape of the teardown: a request 401s, the refresh is rejected, and the
    // session ends — all while the query that made the request is still in flight.
    // Cancelling that query is one of the steps, so a teardown that waits for the
    // cancellation to settle is waiting for its own caller to return.
    const running = queryClient.fetchQuery({
      queryKey: ['a-request-that-401d'],
      queryFn: async () => {
        await endSession('session-invalidated');
        throw new Error('401');
      },
    });

    await expect(running).rejects.toThrow();

    // The half-transition is the bug: credentials gone, status still `authenticated`.
    // Every later request would then go out with no header — a 401 with nothing to
    // rotate, so the rotation cannot even classify it, and the player is shown a retry
    // for a session that no longer exists.
    expect(hasTokens()).toBe(false);
    expect(getSessionStatus()).toBe('unauthenticated');
  });
});

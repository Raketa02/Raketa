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
import { beginSession, endSession } from './session';
import { clear, getCredential, hasTokens, save } from './tokenManager';

beforeEach(async () => {
  resetSessionStatus();
  queryClient.clear();
  await save({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  setSessionStatus('authenticated');
});

afterEach(() => {
  queryClient.clear();
});

/**
 * **The first read between the credentials and the status** (`docs/specs/busy-indicator/decisions.md`
 * §3.1). Opening the status unmounts the screen whose busy button is the only thing saying the app
 * is working, and the entry gate then drew blank paper until the account came back. So the read
 * the gate asks first runs before the status opens: with the credentials already saved, so it goes
 * out authenticated, and with the screen — and its spinner — still up.
 */
describe('beginning a session', () => {
  const TOKENS = { accessToken: 'access-2', refreshToken: 'refresh-2' };

  beforeEach(async () => {
    await clear();
    resetSessionStatus();
    setSessionStatus('unauthenticated');
  });

  it('saves the credentials, reads first, and only then opens the status', async () => {
    const seen: { readonly status: string; readonly credential: string | undefined }[] = [];

    await beginSession(TOKENS, async () => {
      seen.push({ status: getSessionStatus(), credential: getCredential()?.accessToken });
    });

    expect(seen).toEqual([{ status: 'unauthenticated', credential: 'access-2' }]);
    expect(getSessionStatus()).toBe('authenticated');
  });

  it('opens straight away when there is nothing to read first', async () => {
    await beginSession(TOKENS);

    expect(getSessionStatus()).toBe('authenticated');
  });

  /** The gate reads the failure out of the cache and says so — the launch's own path. */
  it('still opens when the read fails, because the credentials were good', async () => {
    await beginSession(TOKENS, () => Promise.reject(new Error('the server is down')));

    expect(hasTokens()).toBe(true);
    expect(getSessionStatus()).toBe('authenticated');
  });

  /** A read that ended the session — a refresh refused — leaves nothing to open. */
  it('refuses to open a session the read itself ended', async () => {
    const ending = beginSession(TOKENS, async () => {
      await endSession('session-invalidated');
      throw new Error('401');
    });

    await expect(ending).rejects.toThrow('401');
    expect(hasTokens()).toBe(false);
    expect(getSessionStatus()).toBe('unauthenticated');
  });
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

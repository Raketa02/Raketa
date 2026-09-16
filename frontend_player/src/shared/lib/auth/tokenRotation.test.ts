/**
 * The 401 -> refresh -> retry rotation, driven through the network boundary.
 *
 * Only `fetch` is faked. The HTTP client, the coordinator's single-flight logic, the
 * keychain module, the session machine, error mapping and the auth feature's wire call
 * all run for real — so the request counts asserted below are the requests a phone would
 * actually make.
 *
 * These tests are the deliverable as much as the code is. Ordinary login tests catch
 * none of this: every scenario here needs either concurrency or a specific failure the
 * happy path never produces, and each one is a bug that signs a player out of a working
 * session. docs/architecture.md Part 19 names them explicitly for that reason.
 *
 * `refreshTokens` is imported from the auth feature's public surface because that is
 * exactly how the root layout wires it. Stubbing the exchange instead would make "exactly
 * one refresh request" a statement about a fake rather than about the socket.
 */

import { refreshTokens } from '@/features/auth/types';
import { httpRequest, resetHttp } from '@/shared/lib/http';
import { queryClient } from '@/shared/lib/query-client';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import {
  beginSession,
  clearStoredTokens,
  endSession,
  getSessionStatus,
  hasTokens,
  readStoredTokens,
  resetRefresh,
  resetSessionStatus,
  subscribeToSession,
  wireHttpCredentials,
} from '.';

const ACCESS_1 = 'access-token-1';
const ACCESS_2 = 'access-token-2';

const ROTATED: Wire['TokenResponse'] = {
  access_token: ACCESS_2,
  refresh_token: 'refresh-token-2',
  token_type: 'bearer',
  expires_in: 900,
};

const REFRESH = '/api/v1/auth/refresh';
const ME = '/api/v1/users/me';

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  resetRefresh();
  resetHttp();
  // The real wiring, as the bootstrap sequence performs it.
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
});

afterEach(async () => {
  transport.restore();
  resetRefresh();
  resetHttp();
  await clearStoredTokens();
  queryClient.clear();
});

/** A live session holding the credential the fake server is about to stop accepting. */
async function signedIn(): Promise<void> {
  await beginSession({ accessToken: ACCESS_1, refreshToken: 'refresh-token-1' });
}

/** A route that rejects the old credential and accepts the rotated one, like a server. */
function guarded(path: string): void {
  transport.on('GET', path, (request) =>
    request.headers.Authorization === `Bearer ${ACCESS_2}`
      ? json({ ok: true })
      : errorResponse(401, 'access_token_expired'),
  );
}

/** Answers a refresh once, with a rotated pair. */
function rotates(): void {
  transport.on('POST', REFRESH, () => json(ROTATED));
}

function read(path: string) {
  return httpRequest({ method: 'GET', path, authenticated: true });
}

// ---------------------------------------------------------------------------
// The happy path: the player never finds out
// ---------------------------------------------------------------------------

describe('a token that expires mid-flow', () => {
  it('is refreshed and the request retried, transparently', async () => {
    await signedIn();
    guarded(ME);
    rotates();

    await expect(read(ME)).resolves.toEqual({ ok: true });

    const attempts = transport.requestsTo('GET', ME);
    expect(attempts).toHaveLength(2);
    // The retry carries the new credential, not the one the server just rejected.
    expect(attempts[0]?.headers.Authorization).toBe(`Bearer ${ACCESS_1}`);
    expect(attempts[1]?.headers.Authorization).toBe(`Bearer ${ACCESS_2}`);
    expect(getSessionStatus()).toBe('authenticated');
  });

  it('persists both halves of the rotated pair, so a relaunch keeps the session', async () => {
    await signedIn();
    guarded(ME);
    rotates();

    await read(ME);

    // Written as one value: a new access token beside the retired refresh token is a
    // session that cannot recover.
    await expect(readStoredTokens()).resolves.toEqual({
      accessToken: ACCESS_2,
      refreshToken: 'refresh-token-2',
    });
  });

  it('sends the refresh without an Authorization header, so it cannot refresh itself', async () => {
    await signedIn();
    guarded(ME);
    rotates();

    await read(ME);

    expect(transport.requestsTo('POST', REFRESH)[0]?.headers.Authorization).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// Concurrency — the failure that logs people out at random
// ---------------------------------------------------------------------------

describe('many requests failing at once', () => {
  it('produces exactly one refresh, and every waiter reuses it', async () => {
    await signedIn();
    const paths = ['/api/v1/ratings', '/api/v1/sports', ME, '/api/v1/assessments/a'];
    paths.forEach(guarded);
    rotates();

    const results = await Promise.all(paths.map(read));

    // The whole point: four 401s, one rotation. Four rotations would retire each other's
    // refresh token and end the session in the middle of a working screen.
    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(1);
    expect(results).toEqual(paths.map(() => ({ ok: true })));
    for (const path of paths) {
      expect(transport.requestsTo('GET', path)).toHaveLength(2);
    }
  });

  it('does not rotate again for a 401 that answers an already-replaced token', async () => {
    // The stragglers are what single-flight alone misses. On a slow connection the 401s
    // arrive strung out over seconds, so a late one finds no flight in progress and would
    // start a second rotation — the same failure, reached the long way round.
    await signedIn();
    rotates();
    guarded(ME);

    let releaseSlow = (): void => {};
    const slowHeld = new Promise<void>((resolve) => {
      releaseSlow = resolve;
    });

    let slowAttempts = 0;
    transport.on('GET', '/api/v1/sports', async (request) => {
      slowAttempts += 1;
      if (slowAttempts === 1) await slowHeld;
      return request.headers.Authorization === `Bearer ${ACCESS_2}`
        ? json({ ok: true })
        : errorResponse(401, 'access_token_expired');
    });

    // Sent with the old credential, and still in flight while the rotation happens.
    const slow = read('/api/v1/sports');
    await read(ME);

    releaseSlow();
    await expect(slow).resolves.toEqual({ ok: true });

    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(1);
    // It still recovered — it simply retried against the credential already in hand.
    expect(transport.requestsTo('GET', '/api/v1/sports')).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// A refresh the server rejects: the session really is over
// ---------------------------------------------------------------------------

describe('a rejected refresh', () => {
  it('signs the player out exactly once, clearing credentials and the cache', async () => {
    await signedIn();
    queryClient.setQueryData(['previous', 'player'], { name: 'ada' });

    const paths = [ME, '/api/v1/ratings', '/api/v1/sports'];
    paths.forEach(guarded);
    transport.on('POST', REFRESH, () => errorResponse(401, 'refresh_token_expired'));

    let transitions = 0;
    subscribeToSession(() => {
      transitions += 1;
    });

    const failures = await Promise.all(
      paths.map((path) => read(path).catch((error: unknown) => error)),
    );

    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(1);
    // Once — not once per failing request. Three redirects would fire three times.
    expect(transitions).toBe(1);
    expect(getSessionStatus()).toBe('unauthenticated');

    expect(hasTokens()).toBe(false);
    await expect(readStoredTokens()).resolves.toBeUndefined();
    // The privacy step: the previous player's data must not be sitting there for whoever
    // signs in next on this device.
    expect(queryClient.getQueryData(['previous', 'player'])).toBeUndefined();

    for (const failure of failures) {
      expect(failure).toMatchObject({ name: 'AppError', kind: 'unauthorized' });
    }
  });
});

// ---------------------------------------------------------------------------
// A refresh that never arrived: the session is none of our business
// ---------------------------------------------------------------------------

describe('a refresh that could not reach the server', () => {
  it('keeps the session — losing signal in a lift is not a logout', async () => {
    await signedIn();
    guarded(ME);
    transport.on('POST', REFRESH, networkFailure());

    const failure = await read(ME).catch((error: unknown) => error);

    // Reported as what actually went wrong. Surfacing the 401 would carry
    // `requires-reauthentication`, and launch validation would read a dropped connection
    // as a session that ended — destroying valid credentials and costing a password.
    expect(failure).toMatchObject({
      name: 'AppError',
      kind: 'network-unavailable',
      recovery: 'retryable-automatically',
    });
    expect(getSessionStatus()).toBe('authenticated');
    expect(hasTokens()).toBe(true);
    await expect(readStoredTokens()).resolves.toMatchObject({ accessToken: ACCESS_1 });
  });

  it('keeps the session when the auth server itself fails', async () => {
    // A 503 says nothing about this player's credentials either.
    await signedIn();
    guarded(ME);
    transport.on('POST', REFRESH, () => errorResponse(503, 'service_unavailable'));

    await expect(read(ME)).rejects.toMatchObject({ kind: 'network-unavailable' });
    expect(getSessionStatus()).toBe('authenticated');
    expect(hasTokens()).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// The retried request fails too
// ---------------------------------------------------------------------------

describe('a retry that is rejected as well', () => {
  it('terminates the session once instead of looping', async () => {
    await signedIn();
    // Rejects every credential, including the one minted a moment ago.
    transport.on('GET', ME, () => errorResponse(401, 'access_token_expired'));
    rotates();

    let transitions = 0;
    subscribeToSession(() => {
      transitions += 1;
    });

    await expect(read(ME)).rejects.toMatchObject({
      name: 'AppError',
      recovery: 'requires-reauthentication',
    });

    // Two attempts and one rotation, full stop. Without the hard stop this is the
    // 401 -> refresh -> retry -> 401 loop that drains a battery and hammers the API.
    expect(transport.requestsTo('GET', ME)).toHaveLength(2);
    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(1);
    expect(transitions).toBe(1);
    expect(getSessionStatus()).toBe('unauthenticated');
    expect(hasTokens()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// The boundaries of the rotation
// ---------------------------------------------------------------------------

describe('what is never rotated or replayed', () => {
  it('leaves a sign-in attempt alone — a wrong password is not an expired session', async () => {
    transport.on('POST', '/api/v1/auth/login', () => errorResponse(401, 'invalid_credentials'));

    await expect(
      httpRequest({
        method: 'POST',
        path: '/api/v1/auth/login',
        body: { email: 'ada@example.com', password: 'wrong' },
        authenticated: false,
      }),
    ).rejects.toMatchObject({ recovery: 'requires-user-correction' });

    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(0);
  });

  it('leaves a 403 alone — it is said to a session that is perfectly valid', async () => {
    await signedIn();
    transport.on('GET', ME, () => errorResponse(403, 'not_permitted'));

    await expect(read(ME)).rejects.toMatchObject({ kind: 'forbidden' });

    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(0);
    expect(getSessionStatus()).toBe('authenticated');
  });

  it('does not replay a write that failed for any reason other than a 401', async () => {
    // The replay is safe only because the backend raises a 401 from the dependency that
    // resolves the current player, before the handler runs — so the request had no
    // effect. A 500 carries no such promise: the booking may well have been made.
    await signedIn();
    let attempts = 0;
    transport.on('POST', '/api/v1/assessments', () => {
      attempts += 1;
      return errorResponse(500, 'internal_error');
    });

    await expect(
      httpRequest({
        method: 'POST',
        path: '/api/v1/assessments',
        body: { sport: 'padel' },
        authenticated: true,
      }),
    ).rejects.toMatchObject({ kind: 'server' });

    expect(attempts).toBe(1);
    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(0);
  });

  it('does not try to rotate when the request carried no credential at all', async () => {
    // No session, so the 401 is simply correct and there is nothing to refresh.
    transport.on('GET', ME, () => errorResponse(401, 'access_token_missing'));

    await expect(read(ME)).rejects.toMatchObject({ kind: 'unauthorized' });

    expect(transport.requestsTo('GET', ME)).toHaveLength(1);
    expect(transport.requestsTo('POST', REFRESH)).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Signing out while a rotation is in the air
// ---------------------------------------------------------------------------

describe('a sign-out that races the rotation', () => {
  it('does not resurrect the session when the refresh lands afterwards', async () => {
    await signedIn();
    guarded(ME);

    let releaseRefresh = (): void => {};
    const refreshHeld = new Promise<void>((resolve) => {
      releaseRefresh = resolve;
    });
    // Signals that the exchange has genuinely reached the socket. Counting microtask
    // ticks instead would sign out *before* the rotation started, and the test would
    // pass without ever reaching the race it is named for.
    let refreshStarted = (): void => {};
    const refreshInFlight = new Promise<void>((resolve) => {
      refreshStarted = resolve;
    });
    transport.on('POST', REFRESH, async () => {
      refreshStarted();
      await refreshHeld;
      return json(ROTATED);
    });

    const pending = read(ME).catch((error: unknown) => error);
    await refreshInFlight;

    await endSession('requested');
    releaseRefresh();
    await pending;

    // Writing the rotated pair here would leave a live credential on a device showing a
    // sign-in screen — a session the player has already left.
    expect(hasTokens()).toBe(false);
    await expect(readStoredTokens()).resolves.toBeUndefined();
    expect(getSessionStatus()).toBe('unauthenticated');
  });
});

// ---------------------------------------------------------------------------
// Credentials never reach a log
// ---------------------------------------------------------------------------

describe('logging', () => {
  it('never writes a token, an Authorization header or a payload to the console', async () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((level) =>
      jest.spyOn(console, level).mockImplementation(() => {}),
    );

    try {
      await signedIn();
      guarded(ME);
      rotates();
      await read(ME);

      // And again down the failing path, which is where a debugging line gets left
      // behind. Back to the retired credential, and this time the rotation is refused.
      await beginSession({ accessToken: ACCESS_1, refreshToken: 'refresh-token-1' });
      transport.on('POST', REFRESH, () => errorResponse(401, 'refresh_token_expired'));
      await read(ME).catch(() => undefined);

      // Both rotations really happened — a clean console proves nothing otherwise.
      expect(transport.requestsTo('POST', REFRESH)).toHaveLength(2);
      expect(getSessionStatus()).toBe('unauthenticated');

      const written = spies
        .flatMap((spy) => spy.mock.calls)
        .map((call) => call.map((arg) => String(arg)).join(' '))
        .join('\n');

      for (const secret of [ACCESS_1, ACCESS_2, 'refresh-token-1', 'refresh-token-2', 'Bearer']) {
        expect(written).not.toContain(secret);
      }
    } finally {
      spies.forEach((spy) => spy.mockRestore());
    }
  });
});

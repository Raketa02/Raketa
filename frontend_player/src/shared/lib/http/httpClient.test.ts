/**
 * The chokepoint's own behaviour: the things that are true of every request in the app
 * because they are true here.
 */

import { AppError } from '@/shared/errors';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  neverResponds,
  noContent,
  type Transport,
} from '@/test-support/transport';

import { configureHttp, httpGetFromFeaturesHost, httpRequest, resetHttp } from './httpClient';
import { TIMEOUT_MS } from './timeouts';

let transport: Transport;

/**
 * A credential adapter holding one token and refusing to rotate.
 *
 * The rotation itself is driven end to end in `shared/lib/auth/tokenRotation.test.ts`,
 * against the real coordinator; these tests are about the chokepoint's other behaviours,
 * so here a refresh is `unavailable` — the outcome that changes nothing.
 */
function credentialsFor(accessToken: string | undefined) {
  return {
    current: () => (accessToken === undefined ? undefined : { accessToken, generation: 1 }),
    refresh: () => Promise.resolve('unavailable' as const),
    abandon: () => Promise.resolve(),
  };
}

beforeEach(() => {
  transport = installTransport();
  resetHttp();
});

afterEach(() => {
  transport.restore();
  resetHttp();
  jest.useRealTimers();
});

describe('the auth header', () => {
  it('is attached to an authenticated request', async () => {
    configureHttp(credentialsFor('token-1'));
    transport.on('GET', '/api/v1/users/me', () => json({ ok: true }));

    await httpRequest({ method: 'GET', path: '/api/v1/users/me', authenticated: true });

    expect(transport.requests[0]?.headers.Authorization).toBe('Bearer token-1');
  });

  it('is absent from an unauthenticated request even when a token exists', async () => {
    // Login, refresh and registration must not carry a stale token: the endpoints that
    // take none are a different set from the endpoints that happen to have none.
    configureHttp(credentialsFor('token-1'));
    transport.on('POST', '/api/v1/auth/login', () => json({ ok: true }));

    await httpRequest({
      method: 'POST',
      path: '/api/v1/auth/login',
      body: {},
      authenticated: false,
    });

    expect(transport.requests[0]?.headers.Authorization).toBeUndefined();
  });

  it('is absent when there is no session', async () => {
    configureHttp(credentialsFor(undefined));
    transport.on('GET', '/api/v1/sports', () => json({ sports: [] }));

    await httpRequest({ method: 'GET', path: '/api/v1/sports', authenticated: true });

    expect(transport.requests[0]?.headers.Authorization).toBeUndefined();
  });
});

describe('the timeout policy', () => {
  it('abandons a request the server never answers', async () => {
    jest.useFakeTimers();
    transport.on('GET', '/api/v1/sports', neverResponds());

    const pending = httpRequest({
      method: 'GET',
      path: '/api/v1/sports',
      authenticated: false,
    });
    // Assert before advancing, or an unhandled rejection escapes the microtask queue.
    const assertion = expect(pending).rejects.toMatchObject({ kind: 'timeout' });

    jest.advanceTimersByTime(TIMEOUT_MS.request + 1);

    await assertion;
  });

  it('uses the class the caller named, not one number for everything', async () => {
    jest.useFakeTimers();
    transport.on('GET', '/api/v1/sports', neverResponds());

    const pending = httpRequest({
      method: 'GET',
      path: '/api/v1/sports',
      authenticated: false,
      timeout: 'background',
    });
    const assertion = expect(pending).rejects.toMatchObject({ kind: 'timeout' });

    // Past the interactive timeout, and the background request is still running.
    jest.advanceTimersByTime(TIMEOUT_MS.request + 1);
    await Promise.resolve();

    jest.advanceTimersByTime(TIMEOUT_MS.background);
    await assertion;
  });
});

describe('cancellation', () => {
  it('propagates an abort as an abort, not as a failure', async () => {
    // TanStack Query cancels a query on unmount. If that arrived as an `AppError` the
    // screen would render an error for work nobody was waiting for any more.
    const controller = new AbortController();
    transport.on('GET', '/api/v1/sports', neverResponds());

    const pending = httpRequest({
      method: 'GET',
      path: '/api/v1/sports',
      authenticated: false,
      signal: controller.signal,
    });
    const assertion = expect(pending).rejects.toMatchObject({ name: 'AbortError' });

    controller.abort();

    await assertion;
  });
});

describe('normalizing failures', () => {
  it('turns an error envelope into an AppError carrying its code', async () => {
    transport.on('GET', '/api/v1/assessments/x', () =>
      errorResponse(409, 'question_not_outstanding'),
    );

    await expect(
      httpRequest({
        method: 'GET',
        path: '/api/v1/assessments/x',
        authenticated: false,
      }),
    ).rejects.toMatchObject({
      name: 'AppError',
      code: 'question_not_outstanding',
      status: 409,
      traceId: 'trace-test',
    });
  });

  it('turns an unreachable server into an AppError, not a raw TypeError', async () => {
    transport.on('GET', '/api/v1/sports', networkFailure());

    const failure = await httpRequest({
      method: 'GET',
      path: '/api/v1/sports',
      authenticated: false,
    }).catch((error: unknown) => error);

    // Raw fetch rejections must never reach a screen.
    expect(failure).toBeInstanceOf(AppError);
    expect((failure as AppError).kind).toBe('network-unavailable');
  });
});

describe('decoding', () => {
  it('returns undefined for a 204 rather than failing to parse an empty body', async () => {
    transport.on('POST', '/api/v1/assessments/x/abandonment', () => noContent());

    await expect(
      httpRequest({
        method: 'POST',
        path: '/api/v1/assessments/x/abandonment',
        authenticated: false,
      }),
    ).resolves.toBeUndefined();
  });
});

describe('the request itself', () => {
  it('carries a correlation id in the alphabet the backend accepts', async () => {
    transport.on('GET', '/api/v1/sports', () => json({ sports: [] }));

    await httpRequest({ method: 'GET', path: '/api/v1/sports', authenticated: false });

    const id = transport.requests[0]?.headers['X-Request-ID'];
    // Anything outside this pattern the backend discards and replaces, which would leave
    // a client-side failure tied to nothing.
    expect(id).toMatch(/^[A-Za-z0-9._-]{1,64}$/);
  });

  it('gives every request its own id', async () => {
    transport.on('GET', '/api/v1/sports', () => json({ sports: [] }));

    await httpRequest({ method: 'GET', path: '/api/v1/sports', authenticated: false });
    await httpRequest({ method: 'GET', path: '/api/v1/sports', authenticated: false });

    expect(transport.requests[0]?.headers['X-Request-ID']).not.toBe(
      transport.requests[1]?.headers['X-Request-ID'],
    );
  });

  it('resolves the path against the configured API base URL', async () => {
    transport.on('GET', '/api/v1/sports', () => json({ sports: [] }));

    await httpRequest({ method: 'GET', path: '/api/v1/sports', authenticated: false });

    expect(transport.requests[0]?.path).toBe('/api/v1/sports');
  });
});

describe('the idempotency key', () => {
  it('is sent as the header the write path reads', async () => {
    transport.on('POST', '/api/v1/players/me/profile', () => json({ ok: true }, 201));

    await httpRequest({
      method: 'POST',
      path: '/api/v1/players/me/profile',
      body: {},
      authenticated: false,
      idempotencyKey: 'commit-1',
    });

    expect(transport.requests[0]?.headers['Idempotency-Key']).toBe('commit-1');
  });

  it('is absent from a request that names none', async () => {
    // Every other endpoint. A header set on everything would be a claim about writes the
    // backend never made, and one more thing to get wrong on the one route that needs it.
    transport.on('GET', '/api/v1/sports', () => json({ sports: [] }));

    await httpRequest({ method: 'GET', path: '/api/v1/sports', authenticated: false });

    expect(transport.requests[0]?.headers['Idempotency-Key']).toBeUndefined();
  });

  it('survives the replay a rotated token makes', async () => {
    // The rotation exists to be invisible above this module. A replay that dropped the key
    // would be a second write to the server — one profile becoming two because a token
    // happened to expire mid-commit.
    let rotated = false;
    configureHttp({
      current: () => ({ accessToken: rotated ? 'token-2' : 'token-1', generation: 1 }),
      refresh: () => {
        rotated = true;
        return Promise.resolve('retry' as const);
      },
      abandon: () => Promise.resolve(),
    });
    transport.on('POST', '/api/v1/players/me/profile', () =>
      rotated ? json({ ok: true }, 201) : errorResponse(401, 'unauthorized'),
    );

    await httpRequest({
      method: 'POST',
      path: '/api/v1/players/me/profile',
      body: {},
      authenticated: true,
      idempotencyKey: 'commit-1',
    });

    expect(transport.requests).toHaveLength(2);
    expect(transport.requests.map((request) => request.headers['Idempotency-Key'])).toEqual([
      'commit-1',
      'commit-1',
    ]);
  });
});

/**
 * **The second host.** The feature-flag datafile is the one document this app reads from
 * somewhere other than the API
 * ([ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §4, §6), and it is read through this module for every reason the API is — the timeout, the
 * correlation id, the error model — and one the API does not have: the host is somebody's Mac on
 * the LAN today and a public bucket tomorrow, so **it never sees the access token.**
 */
describe('the features host', () => {
  const DATAFILE = '/development/featurevisor-player.json';

  it('resolves the path against the configured features base URL, not the API', async () => {
    transport.on('GET', DATAFILE, () => json({ schemaVersion: '2' }));

    await httpGetFromFeaturesHost({ path: DATAFILE });

    expect(transport.requests[0]?.url).toBe(`https://features.test.raketa.invalid${DATAFILE}`);
  });

  it('returns the decoded document', async () => {
    transport.on('GET', DATAFILE, () => json({ schemaVersion: '2', revision: '7' }));

    await expect(httpGetFromFeaturesHost({ path: DATAFILE })).resolves.toEqual({
      schemaVersion: '2',
      revision: '7',
    });
  });

  it('never carries the access token, even with a session', async () => {
    configureHttp(credentialsFor('token-1'));
    transport.on('GET', DATAFILE, () => json({ schemaVersion: '2' }));

    await httpGetFromFeaturesHost({ path: DATAFILE });

    expect(transport.requests[0]?.headers.Authorization).toBeUndefined();
  });

  it('normalizes a failure like any other request', async () => {
    // What the serve script answers for an environment it has not built: a 404, with a body
    // that is not the API's envelope. It still leaves as an `AppError`, classified by status.
    transport.on('GET', DATAFILE, () => new Response('Not Found', { status: 404 }));

    await expect(httpGetFromFeaturesHost({ path: DATAFILE })).rejects.toMatchObject({
      kind: 'not-found',
    });
  });

  it('is a background read: nobody is looking at a spinner for it', async () => {
    jest.useFakeTimers();
    transport.on('GET', DATAFILE, neverResponds());

    const pending = httpGetFromFeaturesHost({ path: DATAFILE });
    const assertion = expect(pending).rejects.toMatchObject({ kind: 'timeout' });
    let settled = false;
    pending.then(
      () => (settled = true),
      () => (settled = true),
    );

    // Past the interactive timeout, and the read is still running. Asserted rather than assumed:
    // the rejection below is a timeout under either class, so only this line tells them apart.
    jest.advanceTimersByTime(TIMEOUT_MS.request + 1);
    for (let hop = 0; hop < 10; hop += 1) await Promise.resolve();
    expect(settled).toBe(false);

    jest.advanceTimersByTime(TIMEOUT_MS.background);
    await assertion;
  });
});

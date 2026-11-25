/**
 * Relaunch: what the app concludes from what it finds in the keychain.
 *
 * Two of these — the rejected token and the unreachable server — are the reason the step
 * exists at all. They look identical from the app's side (a stored token, a failed
 * validation) and demand opposite behaviour.
 */

import { onlineManager, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react-native';
import { Text } from 'react-native';

import {
  beginSession,
  clearStoredTokens,
  getSessionStatus,
  hasTokens,
  readStoredTokens,
  resetSessionStatus,
  useSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { LaunchGate, bootstrapApp } from '@/shared/lib/bootstrap';
import { TIMEOUT_MS } from '@/shared/lib/http';
import type { Reachability } from '@/shared/lib/platform';
import { queryClient } from '@/shared/lib/query-client';
import type { AppError } from '@/shared/errors';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  neverResponds,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { authKeys } from '../hooks/authKeys';
import { fetchCurrentUserAtLaunch } from '../hooks/useCurrentUser';

import { refreshTokens } from './refreshTokens';
import { restoreSession } from './restoreSession';

/** The launch's read, as the root layout hands it in: through the cache the gate reads. */
const readAtLaunch = () => fetchCurrentUserAtLaunch(queryClient);

/** What the phone says about reaching the internet, as the network-state module answers it. */
const phoneSays = (answer: Reachability) => jest.fn(() => Promise.resolve(answer));

/** The ordinary launch: a connection the phone believes in. */
const reachable = phoneSays('reachable');

const USER: Wire['MeResponse'] = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  nickname: 'ada',
  authority: 'player',
  is_admin: false,
  is_active: true,
  has_player_profile: false,
  adult_attested: true,
  profiles: { acts_as_player: true, administers: [], pending_invitations: [], handovers: [] },
};

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  jest.useRealTimers();
});

/** A previous run of the app that ended with a signed-in player. */
async function credentialsOnDevice() {
  await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  resetSessionStatus(); // the process restarted; only the keychain survived
}

describe('relaunching', () => {
  it('restores the session when the server still recognises the token', async () => {
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    const restored = await restoreSession(readAtLaunch, reachable);

    expect(restored.status).toBe('authenticated');
    expect(getSessionStatus()).toBe('authenticated');
    expect(restored.user).toEqual({
      id: USER.id,
      email: USER.email,
      nickname: USER.nickname,
      hasPlayerProfile: USER.has_player_profile,
      profiles: { actsAsPlayer: true, administers: [], pendingInvitations: [], handovers: [] },
    });
  });

  it('sends the stored token on the validation request', async () => {
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    await restoreSession(readAtLaunch, reachable);

    const [validation] = transport.requestsTo('GET', '/api/v1/users/me');
    expect(validation?.headers.Authorization).toBe('Bearer access-1');
  });

  it('is signed out when the device holds no credentials', async () => {
    const restored = await restoreSession(readAtLaunch, reachable);

    expect(restored.status).toBe('unauthenticated');
    expect(getSessionStatus()).toBe('unauthenticated');
    // Nothing was asked of the server: an unauthenticated launch that fires an
    // authenticated request can only 401.
    expect(transport.requests).toHaveLength(0);
  });

  it('discards credentials the server no longer recognises', async () => {
    // The iOS reinstall case: Keychain data outlives the app, so a fresh install can
    // start life holding credentials the backend retired months ago. Both halves are
    // dead here — an access token alone is no longer proof, because a stale one is now
    // answered by a rotation.
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => errorResponse(401, 'access_token_invalid'));
    transport.on('POST', '/api/v1/auth/refresh', () =>
      errorResponse(401, 'refresh_token_not_recognised'),
    );

    const restored = await restoreSession(readAtLaunch, reachable);

    expect(restored.status).toBe('unauthenticated');
    expect(hasTokens()).toBe(false);
  });

  it('refreshes an expired access token rather than ending the session', async () => {
    // An access token expires in minutes and a refresh token lasts weeks, so this is the
    // *ordinary* relaunch — the app has been closed overnight. Signing the player out
    // here would mean re-entering a password every morning.
    await credentialsOnDevice();
    const rotatedPair: Wire['TokenResponse'] = {
      access_token: 'access-2',
      refresh_token: 'refresh-2',
      token_type: 'bearer',
      expires_in: 900,
    };

    let rotated = false;
    transport.on('GET', '/api/v1/users/me', (request) =>
      request.headers.Authorization === 'Bearer access-2'
        ? json(USER)
        : errorResponse(401, 'access_token_expired'),
    );
    transport.on('POST', '/api/v1/auth/refresh', () => {
      rotated = true;
      return json(rotatedPair);
    });

    const restored = await restoreSession(readAtLaunch, reachable);

    expect(rotated).toBe(true);
    expect(restored.status).toBe('authenticated');
    expect(restored.user?.nickname).toBe('ada');
    expect(hasTokens()).toBe(true);
  });

  it('keeps the session when the server could not be reached', async () => {
    // Unreachable is not rejected. Destroying a valid session — and costing someone
    // their password — because a tunnel swallowed one request is the worst outcome here,
    // and it is the easy mistake.
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', networkFailure());

    const restored = await restoreSession(readAtLaunch, reachable);

    expect(restored.status).toBe('authenticated');
    expect(hasTokens()).toBe(true);
  });

  it('keeps the session when the server itself failed', async () => {
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => errorResponse(503, 'internal_error'));

    const restored = await restoreSession(readAtLaunch, reachable);

    expect(restored.status).toBe('authenticated');
    expect(hasTokens()).toBe(true);
  });

  it('stops waiting at the launch budget, not the request timeout, and keeps the session', async () => {
    // The splash is up and nothing on the phone gets past it. A connection that reaches
    // nothing held it for the full request timeout — fifteen seconds of a frozen launch, to
    // learn the one thing unreachable already means: keep the session, ask again later.
    jest.useFakeTimers();
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', neverResponds());

    let settled = false;
    const restoring = restoreSession(readAtLaunch, reachable).finally(() => {
      settled = true;
    });

    await jest.advanceTimersByTimeAsync(TIMEOUT_MS.launch - 1);
    expect(settled).toBe(false);
    await jest.advanceTimersByTimeAsync(1);

    const restored = await restoring;
    expect(restored.status).toBe('authenticated');
    expect(hasTokens()).toBe(true);
    expect(TIMEOUT_MS.launch).toBeLessThan(TIMEOUT_MS.request);
  });

  it('asks whatever the cache believes, once the phone has not said it is offline', async () => {
    // The cache pauses a read while offline. A launch read that paused would hold the splash
    // until the connection came back — for ever, in a lift. Only the phone's own answer, read
    // before the check, decides that the check is not worth sending (below).
    await credentialsOnDevice();
    onlineManager.setOnline(false);
    transport.on('GET', '/api/v1/users/me', networkFailure());

    const restored = await restoreSession(readAtLaunch, reachable);

    expect(restored.status).toBe('authenticated');
    expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(1);
  });

  it('leaves an unanswered validation where the entry gate reads it', async () => {
    // The launch already learned the server could not be reached; the gate opens on that,
    // rather than asking again behind an empty screen.
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', networkFailure());

    await restoreSession(readAtLaunch, reachable);

    const state = queryClient.getQueryState<unknown, AppError>(authKeys.currentUser());
    expect(state?.status).toBe('error');
    expect(state?.error?.recovery).toBe('retryable-automatically');
  });
});

/**
 * **A launch that already knows it has no internet doesn't wait on the check** (ADR-0209 §4). A
 * captive portal or a *connected, no internet* network is one the phone has already judged, and a
 * check sent there could only wait out its five seconds to learn what the phone said first.
 */
describe('relaunching on a phone that already knows it is offline', () => {
  it('keeps the session without asking, and writes nothing', async () => {
    await credentialsOnDevice();
    const read = jest.fn(readAtLaunch);
    const unreachable = phoneSays('unreachable');

    const restored = await restoreSession(read, unreachable);

    expect(restored).toEqual({ status: 'authenticated' });
    expect(getSessionStatus()).toBe('authenticated');
    expect(read).not.toHaveBeenCalled();
    expect(transport.requests).toHaveLength(0);
    expect(unreachable).toHaveBeenCalledTimes(1);
    // **No synthesised failure.** Nothing in the cache is what leaves the entry gate's own read
    // to pause on the offline manager and say *Waiting for a connection* — a failure left here
    // would open the gate on *We couldn't pick up where you left off* instead.
    expect(queryClient.getQueryState(authKeys.currentUser())).toBeUndefined();
    await expect(readStoredTokens()).resolves.toEqual({
      accessToken: 'access-1',
      refreshToken: 'refresh-1',
    });
  });

  it('asks as it always has when the phone has not decided yet', async () => {
    // `null` while the platform is still deciding — counted as reachable, as the online manager
    // counts it: a skip on a maybe would strand perfectly good connections at launch.
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => json(USER));
    const read = jest.fn(readAtLaunch);

    const restored = await restoreSession(read, phoneSays('undecided'));

    expect(read).toHaveBeenCalledTimes(1);
    expect(restored.status).toBe('authenticated');
    expect(restored.user?.nickname).toBe('ada');
  });

  it('asks as it always has when the phone could not be asked', async () => {
    // A read that fails says nothing about the network, so it is not a reason to skip anything.
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => json(USER));
    const read = jest.fn(readAtLaunch);
    const unanswerable = jest.fn(() => Promise.reject<Reachability>(new Error('no native answer')));

    const restored = await restoreSession(read, unanswerable);

    expect(read).toHaveBeenCalledTimes(1);
    expect(restored.status).toBe('authenticated');
    expect(restored.user?.nickname).toBe('ada');
  });

  it('never asks the phone on a launch with no credentials, which has nothing to check', async () => {
    const unreachable = phoneSays('unreachable');

    const restored = await restoreSession(readAtLaunch, unreachable);

    expect(restored.status).toBe('unauthenticated');
    expect(unreachable).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// The launch sequence, rendered — no flash in either direction
// ---------------------------------------------------------------------------

/**
 * The tree mounts **under the launch's drawn splash** (ADR-0209), hidden from a screen reader until
 * the splash has gone — and nothing lays out here, so it never goes. What is mounted is the question.
 */
const UNDER_THE_SPLASH = { includeHiddenElements: true } as const;

/** Stands in for the route tree: it names whichever branch the guard would render. */
function TreeUnderTest() {
  const status = useSessionStatus();
  return <Text>{status === 'authenticated' ? 'Signed in' : 'Sign in'}</Text>;
}

function renderLaunch() {
  const seen: string[] = [];

  const run = () =>
    bootstrapApp({
      validateConfig: () => {},
      wirePlatformManagers: () => {},
      wireCredentials: () => wireHttpCredentials(refreshTokens),
      restoreSession: async () => {
        await restoreSession(readAtLaunch, reachable);
      },
      warmHome: () => {},
      readInstallReferrer: () => {},
      loadFonts: async () => {},
    });

  render(
    <QueryClientProvider client={queryClient}>
      <LaunchGate run={run}>
        <Recorder seen={seen} />
      </LaunchGate>
    </QueryClientProvider>,
  );

  return seen;
}

function Recorder({ seen }: { readonly seen: string[] }) {
  const status = useSessionStatus();
  seen.push(status);
  return <TreeUnderTest />;
}

describe('the launch sequence', () => {
  it('shows the authenticated tree with no login-screen flash', async () => {
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    const seen = renderLaunch();

    expect(await screen.findByText('Signed in', UNDER_THE_SPLASH)).toBeTruthy();
    // The tree renders only after the sequence resolves, so it was never mounted while
    // the status was still `bootstrapping` — which is what a login-screen flash is.
    expect(seen).not.toContain('bootstrapping');
    expect(seen).not.toContain('unauthenticated');
  });

  it('shows the sign-in tree with no authenticated-tree flash', async () => {
    const seen = renderLaunch();

    expect(await screen.findByText('Sign in', UNDER_THE_SPLASH)).toBeTruthy();
    expect(seen).not.toContain('bootstrapping');
    expect(seen).not.toContain('authenticated');
  });

  it('seeds the profile it already fetched, so the first screen does not refetch', async () => {
    await credentialsOnDevice();
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    renderLaunch();

    await waitFor(() =>
      expect(queryClient.getQueryData(authKeys.currentUser())).toEqual({
        id: USER.id,
        email: USER.email,
        nickname: USER.nickname,
        hasPlayerProfile: USER.has_player_profile,
        profiles: { actsAsPlayer: true, administers: [], pendingInvitations: [], handovers: [] },
      }),
    );
    expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(1);
  });
});

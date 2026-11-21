/**
 * **The account is read before the session opens**, driven through the real route tree and the
 * network boundary (`docs/specs/busy-indicator/decisions.md` §3.1).
 *
 * Sign-in and sign-up used to open the session the moment the credentials came back. That unmounted
 * the form at once — and with it the busy button, the only thing on screen saying the app was
 * working — while the entry gate could not choose where to go until `/users/me` answered, and drew
 * blank paper until it did: up to a request timeout of nothing. Now the read runs first, under the
 * button's spinner, and the gate finds the account in the cache and goes straight there.
 *
 * Only `fetch` is faked. Every assertion is about what a player can see or what left the device.
 */

import { fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';
import { ActivityIndicator } from 'react-native';

import {
  clearStoredTokens,
  getSessionStatus,
  resetSessionStatus,
  setSessionStatus,
  subscribeToSession,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  ONBOARDING_ROUTES,
  stubGate as stubGateWith,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { authKeys } from '../hooks/authKeys';
import { ADULT_LABEL } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';

import { SIGN_IN_COPY, SIGN_UP_COPY } from './authPresentation';

const ME_PATH = '/api/v1/users/me';

let transport: Transport;
let stopWatchingTheOpening = () => {};

/**
 * Whether the account was already in the cache at the instant the session opened — the claim that
 * the gate has nothing to ask, and so nothing to draw blank while it asks.
 *
 * Read at the opening rather than by counting requests afterwards: the harness runs every pending
 * timer on a navigation, which moves the clock past the read's freshness, so the gate's mount
 * re-reads here although on a phone it finds the answer fresh.
 */
function watchTheOpening(): boolean[] {
  const cached: boolean[] = [];
  stopWatchingTheOpening = subscribeToSession(() => {
    if (getSessionStatus() !== 'authenticated') return;
    cached.push(queryClient.getQueryData(authKeys.currentUser()) !== undefined);
  });
  return cached;
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  setSessionStatus('unauthenticated');
});

afterEach(() => {
  stopWatchingTheOpening();
  transport.restore();
  queryClient.clear();
});

function stubCredentials() {
  transport.on('POST', '/api/v1/users', () =>
    json<Wire['UserResponse']>({ ...GATE_USER, nickname: null }, 201),
  );
  transport.on('POST', '/api/v1/auth/login', () =>
    json<Wire['TokenResponse']>({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
      expires_in: 900,
    }),
  );
}

/** What was true at the moment `/users/me` arrived — which is the whole claim. */
interface AtTheRead {
  readonly status: string;
  readonly busyButton: string | null;
  readonly spinning: boolean;
}

/**
 * An account with no nickname, answered at once — synchronously, as this harness needs: it runs
 * every pending timer on a navigation, so a held answer times out or is collected under the gate —
 * and noting, as the read arrives, the session's status and what the form was drawing.
 */
function watchTheAccountRead(busyWord: string) {
  stubGateWith(transport, { nickname: null });
  const atTheRead: AtTheRead[] = [];
  transport.on('GET', ME_PATH, () => {
    atTheRead.push({
      status: getSessionStatus(),
      busyButton: screen.queryByRole('button', { name: busyWord }) === null ? null : busyWord,
      spinning: screen.UNSAFE_queryAllByType(ActivityIndicator).length > 0,
    });
    return json<Wire['MeResponse']>({ ...GATE_USER, nickname: null });
  });
  return atTheRead;
}

async function signIn() {
  renderRouter(ONBOARDING_ROUTES, { initialUrl: '/sign-in' });
  await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  fireEvent.changeText(screen.getByLabelText('Email'), 'ada@example.com');
  fireEvent.changeText(screen.getByLabelText('Password'), 'correct horse');
  fireEvent.press(screen.getByLabelText(SIGN_IN_COPY.submit));
}

describe('signing in', () => {
  it('keeps Sign in turning on its screen while the account is read, then goes straight there', async () => {
    stubCredentials();
    const atTheRead = watchTheAccountRead(SIGN_IN_COPY.submitting);
    const cachedAtTheOpening = watchTheOpening();

    await signIn();

    await waitFor(() => expect(screen).toHavePathname('/name'));
    // Asked with the session still shut, and the form — its button busy and turning — on screen.
    expect(atTheRead[0]).toEqual({
      status: 'unauthenticated',
      busyButton: SIGN_IN_COPY.submitting,
      spinning: true,
    });
    // And answered by the time it opened, so the gate had the account to route from at once.
    expect(cachedAtTheOpening).toEqual([true]);
  });

  it('signs in anyway when the account cannot be read, and says so on the entry screen', async () => {
    stubCredentials();
    stubGateWith(transport, { nickname: null });
    // Terminal rather than a dropped connection, so the gate's own retries do not run here.
    transport.on('GET', ME_PATH, () => errorResponse(403, 'forbidden'));

    await signIn();

    expect(await screen.findByText("We couldn't pick up where you left off")).toBeTruthy();
    expect(getSessionStatus()).toBe('authenticated');
  });
});

describe('signing up', () => {
  it('keeps Create account turning through the account read, then goes straight to the naming', async () => {
    stubCredentials();
    const atTheRead = watchTheAccountRead(SIGN_UP_COPY.submitting);
    const cachedAtTheOpening = watchTheOpening();

    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/sign-up' });
    await waitFor(() => expect(screen).toHavePathname('/sign-up'));
    fireEvent.changeText(screen.getByLabelText('Email'), 'ania@example.com');
    fireEvent.changeText(screen.getByLabelText('Password'), 'hunter2hunter2');
    fireEvent.changeText(screen.getByLabelText('Repeat password'), 'hunter2hunter2');
    fireEvent.press(screen.getByLabelText(ADULT_LABEL));
    fireEvent.press(screen.getByLabelText(SIGN_UP_COPY.submit));

    await waitFor(() => expect(screen).toHavePathname('/name'));
    expect(atTheRead[0]).toEqual({
      status: 'unauthenticated',
      busyButton: SIGN_UP_COPY.submitting,
      spinning: true,
    });
    expect(cachedAtTheOpening).toEqual([true]);
  });
});

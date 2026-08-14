/**
 * The auth flow, driven through the network boundary.
 *
 * Only `fetch` is faked. The http client, its timeout policy, error mapping, the
 * keychain module, the session machine, the mappers, the use-cases, the hooks and the
 * screens all run for real — so a pass here means the walking skeleton works end to end
 * minus the socket.
 *
 * Every assertion is about what a player can see or what left the device. None reads a
 * store's internals or a hook's return shape.
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import type { ReactElement } from 'react';

import {
  beginSession,
  clearStoredTokens,
  getSessionStatus,
  hasTokens,
  readStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { authKeys } from '../hooks/authKeys';
import { refreshTokens } from '../use-cases/refreshTokens';
import { signIn } from '../use-cases/signIn';

import { AccountScreen } from './AccountScreen';
import { SignInScreen } from './SignInScreen';
import { SignUpScreen } from './SignUpScreen';

const TOKENS: Wire['TokenResponse'] = {
  access_token: 'access-token-1',
  refresh_token: 'refresh-token-1',
  token_type: 'bearer',
  expires_in: 900,
};

const USER: Wire['UserResponse'] = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  nickname: 'ada',
  authority: 'player',
  is_admin: false,
  is_active: true,
  created_at: '2026-08-13T10:00:00Z',
};

let transport: Transport;

function renderScreen(element: ReactElement) {
  return render(<QueryClientProvider client={queryClient}>{element}</QueryClientProvider>);
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  // The real wiring: the session subsystem hands the http client its credential adapter
  // exactly as bootstrap does.
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// Signing in
// ---------------------------------------------------------------------------

describe('signing in', () => {
  it('opens a session and stores the credentials', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/auth/login', () => json(TOKENS));

    renderScreen(<SignInScreen />);

    fireEvent.changeText(screen.getByLabelText('Email'), 'ada@example.com');
    fireEvent.changeText(screen.getByLabelText('Password'), 'correct horse');
    fireEvent.press(screen.getByLabelText('Sign in'));

    await waitFor(() => expect(getSessionStatus()).toBe('authenticated'));

    // Credentials reached the keychain, which is what makes the session survive a kill.
    await expect(readStoredTokens()).resolves.toEqual({
      accessToken: 'access-token-1',
      refreshToken: 'refresh-token-1',
    });
  });

  it('tells the player what to fix, and stays signed out, on a wrong password', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/auth/login', () => errorResponse(401, 'invalid_credentials'));

    renderScreen(<SignInScreen />);

    fireEvent.changeText(screen.getByLabelText('Email'), 'ada@example.com');
    fireEvent.changeText(screen.getByLabelText('Password'), 'wrong');
    fireEvent.press(screen.getByLabelText('Sign in'));

    expect(await screen.findByText("That email and password don't match. Try again.")).toBeTruthy();
    // A 401 answering a sign-in attempt must not be read as "the session ended" —
    // there is no session, and the machine must not move.
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  it('says the connection failed, not that the password was wrong', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/auth/login', networkFailure());

    renderScreen(<SignInScreen />);

    fireEvent.changeText(screen.getByLabelText('Email'), 'ada@example.com');
    fireEvent.changeText(screen.getByLabelText('Password'), 'correct horse');
    fireEvent.press(screen.getByLabelText('Sign in'));

    expect(
      await screen.findByText("We couldn't reach Rakieta. Check your connection and try again."),
    ).toBeTruthy();
  });

  it('does not reach the network when the form is not filled in', async () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignInScreen />);
    fireEvent.press(screen.getByLabelText('Sign in'));

    expect(await screen.findByText('Enter your email address.')).toBeTruthy();
    expect(transport.requests).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Signing up
// ---------------------------------------------------------------------------

describe('signing up', () => {
  function fillSignUp(password = 'hunter2hunter2', confirm = 'hunter2hunter2') {
    fireEvent.changeText(screen.getByLabelText('Email'), 'ada@example.com');
    fireEvent.changeText(screen.getByLabelText('Nickname'), 'ada');
    fireEvent.changeText(screen.getByLabelText('Password'), password);
    fireEvent.changeText(screen.getByLabelText('Repeat password'), confirm);
  }

  it('creates the account, signs in, and lands in a live session', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () => json(USER, 201));
    transport.on('POST', '/api/v1/auth/login', () => json(TOKENS));

    renderScreen(<SignUpScreen />);
    fillSignUp();
    fireEvent.press(screen.getByLabelText('Create account'));

    await waitFor(() => expect(getSessionStatus()).toBe('authenticated'));

    // Registration returns a user, not a token pair, so the workflow is genuinely two
    // requests — and both have to happen for a new player to be signed in.
    expect(transport.requestsTo('POST', '/api/v1/users')).toHaveLength(1);
    expect(transport.requestsTo('POST', '/api/v1/auth/login')).toHaveLength(1);
  });

  it('sends the password twice, because the backend checks both halves', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () => json(USER, 201));
    transport.on('POST', '/api/v1/auth/login', () => json(TOKENS));

    renderScreen(<SignUpScreen />);
    fillSignUp();
    fireEvent.press(screen.getByLabelText('Create account'));

    await waitFor(() => expect(getSessionStatus()).toBe('authenticated'));

    const [registration] = transport.requestsTo('POST', '/api/v1/users');
    expect(registration?.body).toEqual({
      email: 'ada@example.com',
      nickname: 'ada',
      password1: 'hunter2hunter2',
      password2: 'hunter2hunter2',
    });
  });

  it('catches a password mismatch before a round trip', async () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignUpScreen />);
    fillSignUp('hunter2hunter2', 'hunter2hunter3');
    fireEvent.press(screen.getByLabelText('Create account'));

    expect(await screen.findByText("Those passwords don't match.")).toBeTruthy();
    expect(transport.requests).toHaveLength(0);
  });

  it('puts a taken nickname under the nickname field', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () =>
      json(
        {
          code: 'nickname_already_taken',
          message: 'nickname already taken',
          trace_id: 'trace-test',
          details: { field: 'nickname' },
        } satisfies Wire['ErrorResponse'],
        409,
      ),
    );

    renderScreen(<SignUpScreen />);
    fillSignUp();
    fireEvent.press(screen.getByLabelText('Create account'));

    expect(await screen.findByText('That nickname is taken. Pick another.')).toBeTruthy();
    // It never got as far as signing in, and the player is still signed out.
    expect(transport.requestsTo('POST', '/api/v1/auth/login')).toHaveLength(0);
    expect(getSessionStatus()).toBe('unauthenticated');
  });
});

// ---------------------------------------------------------------------------
// Signing out
// ---------------------------------------------------------------------------

describe('signing out', () => {
  async function signedIn() {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/auth/login', () => json(TOKENS));
    await signIn({ email: 'ada@example.com', password: 'correct horse' });
  }

  it('revokes, clears the credentials and empties the cache', async () => {
    await signedIn();
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    // Something a previous player would rather not leave behind.
    queryClient.setQueryData(authKeys.currentUser(), {
      id: USER.id,
      email: USER.email,
      nickname: USER.nickname,
    });

    renderScreen(<AccountScreen />);
    fireEvent.press(screen.getByLabelText('Sign out'));

    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));

    expect(hasTokens()).toBe(false);
    await expect(readStoredTokens()).resolves.toBeUndefined();
    // The privacy step: user A's cached profile must not be sitting there when user B
    // signs in on the same device. Route replacement clears nothing, which is why
    // sign-out is a system operation.
    expect(queryClient.getQueryData(authKeys.currentUser())).toBeUndefined();

    const [revoke] = transport.requestsTo('POST', '/api/v1/auth/logout');
    expect(revoke?.body).toEqual({ refresh_token: 'refresh-token-1' });
  });

  it('still signs the player out when the revoke cannot reach the server', async () => {
    await signedIn();
    transport.on('POST', '/api/v1/auth/logout', networkFailure());
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    renderScreen(<AccountScreen />);
    fireEvent.press(screen.getByLabelText('Sign out'));

    // A player who taps sign out on a train has decided to leave. Refusing would strand
    // them in the account AND leave live credentials on the device.
    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));
    expect(hasTokens()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// The authenticated screen
// ---------------------------------------------------------------------------

describe('the account screen', () => {
  it('shows the player, read through Query rather than held by the session', async () => {
    setSessionStatus('authenticated');
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    renderScreen(<AccountScreen />);

    expect(await screen.findByText('ada')).toBeTruthy();
    expect(screen.getByText('ada@example.com')).toBeTruthy();
  });

  it('does not sign the player out when a request is forbidden', async () => {
    // Real credentials, because the assertion is that they SURVIVE.
    await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
    transport.on('GET', '/api/v1/users/me', () => errorResponse(403, 'forbidden'));

    renderScreen(<AccountScreen />);

    await waitFor(() =>
      expect(screen.getByText('Something went wrong at our end. Try again later.')),
    );
    // A 403 means "you may not do this", said to a perfectly valid session. Signing the
    // player out in response is both wrong and infuriating.
    expect(getSessionStatus()).toBe('authenticated');
    expect(hasTokens()).toBe(true);
  });
});

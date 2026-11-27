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
import { KeyboardAvoidingView, Text } from 'react-native';

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
import { PushProvider } from '@/shared/lib/platform';
import { queryClient } from '@/shared/lib/query-client';
import { fakePush, PUSH_TOKEN } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { authKeys } from '../hooks/authKeys';
import { ADULT_ATTESTATION_MISSING, ADULT_LABEL } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';
import { signIn } from '../use-cases/signIn';

import { useCurrentUser } from '../hooks/useCurrentUser';

import { AccountPanel } from './AccountPanel';
import { authErrorMessage } from './authErrorMessage';
import { SignInScreen } from './SignInScreen';
import { SignUpScreen } from './SignUpScreen';

const TOKENS: Wire['TokenResponse'] = {
  access_token: 'access-token-1',
  refresh_token: 'refresh-token-1',
  token_type: 'bearer',
  expires_in: 900,
};

const USER: Wire['MeResponse'] = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  nickname: 'ada',
  authority: 'player',
  is_admin: false,
  is_active: true,
  has_player_profile: false,
  created_at: '2026-08-13T10:00:00Z',
  adult_attested: true,
  profiles: { acts_as_player: true, administers: [], pending_invitations: [], handovers: [] },
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

/**
 * #529: on iOS the keyboard's height changes while it is up — its bar is swapped per field and on
 * *Show* — and a form centred in what a `KeyboardAvoidingView` left jumped with every swap. The
 * scroll takes the keyboard as a native inset instead, so the form is laid out once.
 */
describe('the keyboard, on the sign-in and sign-up screens', () => {
  it.each([
    ['sign-in', <SignInScreen key="in" />],
    ['sign-up', <SignUpScreen key="up" />],
  ])('is an inset on %s’s scroll, never a re-layout of the form', (_name, element) => {
    renderScreen(element);

    const frame = screen.getByTestId('auth-frame');
    expect(frame.props.automaticallyAdjustKeyboardInsets).toBe(true);
    expect(screen.UNSAFE_queryAllByType(KeyboardAvoidingView)).toHaveLength(0);
  });
});

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

  /**
   * The same control the sign-up form's two boxes carry, for the same kind of reason.
   *
   * A typo here does not cost a whole form — it costs a refusal the player cannot tell apart
   * from a wrong password, and a keychain that filled the box with the wrong entry looks
   * identical either way. It starts masked, as every password box does.
   */
  it('lets the password be read back', async () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignInScreen />);

    expect(screen.getByLabelText('Password').props.secureTextEntry).toBe(true);

    fireEvent.press(screen.getByLabelText('Show password'));
    expect(screen.getByLabelText('Password').props.secureTextEntry).toBe(false);

    fireEvent.press(screen.getByLabelText('Hide password'));
    expect(screen.getByLabelText('Password').props.secureTextEntry).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Signing up
// ---------------------------------------------------------------------------

describe('signing up', () => {
  function fillSignUp(password = 'hunter2hunter2', confirm = 'hunter2hunter2') {
    fireEvent.changeText(screen.getByLabelText('Email'), 'ada@example.com');
    fireEvent.changeText(screen.getByLabelText('Password'), password);
    fireEvent.changeText(screen.getByLabelText('Repeat password'), confirm);
    // Ticked here rather than in the screen, because nothing may arrive ticked: an
    // attestation nobody made is the one thing this form must not be able to send.
    fireEvent.press(screen.getByLabelText(ADULT_LABEL));
  }

  /** The account is created **unnamed** — registration answers with no name and no handle. */
  const { adult_attested: _attested, profiles: _profiles, ...REGISTERED } = USER;
  const UNNAMED: Wire['UserResponse'] = { ...REGISTERED, nickname: null };

  it('creates the account, signs in, and lands in a live session', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () => json(UNNAMED, 201));
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

  /**
   * **Credentials only, and no nickname box** — sign-up is choosing credentials, and saying
   * who you are is onboarding's first screen
   * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). The
   * server refuses a payload that still carries one as malformed, so what leaves the
   * form is pinned field by field.
   */
  it('shows no nickname field, and sends the password twice with nothing about who you are', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () => json(UNNAMED, 201));
    transport.on('POST', '/api/v1/auth/login', () => json(TOKENS));

    renderScreen(<SignUpScreen />);
    expect(screen.queryByLabelText('Nickname')).toBeNull();
    fillSignUp();
    fireEvent.press(screen.getByLabelText('Create account'));

    await waitFor(() => expect(getSessionStatus()).toBe('authenticated'));

    const [registration] = transport.requestsTo('POST', '/api/v1/users');
    // The password twice, because the backend checks both halves.
    expect(registration?.body).toEqual({
      email: 'ada@example.com',
      password1: 'hunter2hunter2',
      password2: 'hunter2hunter2',
      adult_attested: true,
    });
  });

  /**
   * **Nothing arrives ticked, and the form cannot send a claim the player did not make.**
   * The box is the whole of the age rule on this side of the wire (ADR-0124): a pre-ticked
   * one would send an attestation nobody gave, which is the single failure mode an
   * attestation exists to rule out.
   */
  it('never arrives ticked', () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignUpScreen />);

    expect(screen.getByLabelText(ADULT_LABEL).props.accessibilityState?.checked).toBe(false);
  });

  /**
   * The refusal is a refusal and not a closed button. A disabled *Create account* would
   * leave a player looking at a control that does nothing and no sentence saying why
   * ([ADR-0089](../../../../../docs/adr/0089-player-profile-context-event-sourced.md)), so
   * the button presses, the form refuses, and it says what is missing.
   */
  it('refuses an unanswered age question before a round trip, and says so', async () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignUpScreen />);
    fillSignUp();
    // Untick: the answer is now explicitly *no*, which is not an answer this form sends.
    fireEvent.press(screen.getByLabelText(ADULT_LABEL));
    fireEvent.press(screen.getByLabelText('Create account'));

    expect(await screen.findByText(ADULT_ATTESTATION_MISSING)).toBeTruthy();
    expect(transport.requests).toHaveLength(0);
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  /**
   * The server re-refuses what the box enforced, and this is the branch that renders it.
   * An older build, or a replayed request, can carry a body this form would not have sent
   * — and *try again* would be the one sentence that is not true, because the identical
   * body fails identically.
   */
  it("renders the server's refusal under the box that takes the answer", async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () =>
      json(
        {
          code: 'adult_attestation_required',
          message: 'registration requires an adult attestation',
          trace_id: 'trace-test',
          details: { field: 'adult_attested' },
        } satisfies Wire['ErrorResponse'],
        400,
      ),
    );

    renderScreen(<SignUpScreen />);
    fillSignUp();
    fireEvent.press(screen.getByLabelText('Create account'));

    expect(await screen.findByText(ADULT_ATTESTATION_MISSING)).toBeTruthy();
    expect(transport.requestsTo('POST', '/api/v1/auth/login')).toHaveLength(0);
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  it('catches a password mismatch before a round trip', async () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignUpScreen />);
    fillSignUp('hunter2hunter2', 'hunter2hunter3');
    fireEvent.press(screen.getByLabelText('Create account'));

    expect(await screen.findByText("Those passwords don't match.")).toBeTruthy();
    expect(transport.requests).toHaveLength(0);
  });

  /**
   * **No account is created from a half-filled form**, which is the shape of the bug this
   * was written against: a player reported reaching onboarding without having finished the
   * repeat-password box. Nothing on this path allows it — the schema refuses an empty
   * repeat, no request leaves, and the session machine does not move — so the assertion is
   * here to keep it that way, next to the mismatch case that guards the other half.
   *
   * What can *look* like it is the phone: iOS strong-password autofill fills both
   * `newPassword` boxes at once, so a player who typed into neither still has a complete,
   * matching pair. The reveal control on both boxes is what makes that visible rather than
   * mysterious.
   */
  it('creates nothing when the repeat is empty, and opens no session', async () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignUpScreen />);
    fillSignUp('hunter2hunter2', '');
    fireEvent.press(screen.getByLabelText('Create account'));

    expect(await screen.findByText('Repeat your password.')).toBeTruthy();
    expect(transport.requests).toHaveLength(0);
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  /**
   * A password box that cannot be read back is the one place a typo costs a whole form: the
   * player retypes both halves and is told a third time that they do not match, with no way
   * to see which character is wrong.
   */
  it('lets each password box be read back on its own', async () => {
    setSessionStatus('unauthenticated');

    renderScreen(<SignUpScreen />);

    const password = screen.getByLabelText('Password');
    expect(password.props.secureTextEntry).toBe(true);

    fireEvent.press(screen.getByLabelText('Show password'));
    expect(screen.getByLabelText('Password').props.secureTextEntry).toBe(false);
    // Revealing one says nothing about the other: it is a deliberate act on one box.
    expect(screen.getByLabelText('Repeat password').props.secureTextEntry).toBe(true);

    fireEvent.press(screen.getByLabelText('Hide password'));
    expect(screen.getByLabelText('Password').props.secureTextEntry).toBe(true);
  });

  it('puts a taken email under the email field', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () =>
      json(
        {
          code: 'email_already_registered',
          message: 'email already registered',
          trace_id: 'trace-test',
          details: { field: 'email' },
        } satisfies Wire['ErrorResponse'],
        409,
      ),
    );

    renderScreen(<SignUpScreen />);
    fillSignUp();
    fireEvent.press(screen.getByLabelText('Create account'));

    expect(
      await screen.findByText('That email already has an account. Sign in instead.'),
    ).toBeTruthy();
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
    // Nothing to read first: these tests are about the way out, not the gate's first read.
    await signIn({ email: 'ada@example.com', password: 'correct horse' }, async () => undefined);
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

    renderScreen(<AccountPanel />);
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

  /**
   * **The phone stops being pushed this player's notices before the session ends** (#559): the
   * removal needs the session the sign-out is about to end, so it is sent while the access token is
   * still there — the token in the body, never a path — and the next player to sign in on this phone
   * is not pushed the last one's.
   */
  it('lets this phone go while the session can still say so', async () => {
    await signedIn();
    transport.on('POST', '/api/v1/players/me/devices/removal', () => noContent());
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );

    render(
      <QueryClientProvider client={queryClient}>
        <PushProvider port={fakePush({ state: 'granted' })}>
          <AccountPanel />
        </PushProvider>
      </QueryClientProvider>,
    );
    fireEvent.press(screen.getByLabelText('Sign out'));

    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));
    const [removal] = transport.requestsTo('POST', '/api/v1/players/me/devices/removal');
    expect(removal?.body).toEqual({ token: PUSH_TOKEN });
    expect(removal?.headers.Authorization).toBe('Bearer access-token-1');
    expect(transport.requestsTo('POST', '/api/v1/auth/logout')).toHaveLength(1);
  });

  // A phone registered while it allowed notifications, switched off in Settings since: switched on
  // again with nobody signed in, it would show the last player's notices.
  it('lets the phone go whatever its permission says now', async () => {
    await signedIn();
    transport.on('POST', '/api/v1/players/me/devices/removal', () => noContent());
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );

    render(
      <QueryClientProvider client={queryClient}>
        <PushProvider port={fakePush({ state: 'blocked' })}>
          <AccountPanel />
        </PushProvider>
      </QueryClientProvider>,
    );
    fireEvent.press(screen.getByLabelText('Sign out'));

    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));
    expect(transport.requestsTo('POST', '/api/v1/players/me/devices/removal')).toHaveLength(1);
  });

  it('lets nothing go from a phone with no token to give', async () => {
    await signedIn();
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );

    render(
      <QueryClientProvider client={queryClient}>
        <PushProvider port={fakePush({ state: 'granted', token: null })}>
          <AccountPanel />
        </PushProvider>
      </QueryClientProvider>,
    );
    fireEvent.press(screen.getByLabelText('Sign out'));

    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));
    expect(transport.requestsTo('POST', '/api/v1/players/me/devices/removal')).toHaveLength(0);
  });

  it('still signs the player out when the phone cannot be let go', async () => {
    await signedIn();
    transport.on('POST', '/api/v1/players/me/devices/removal', networkFailure());
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );

    render(
      <QueryClientProvider client={queryClient}>
        <PushProvider port={fakePush({ state: 'granted' })}>
          <AccountPanel />
        </PushProvider>
      </QueryClientProvider>,
    );
    fireEvent.press(screen.getByLabelText('Sign out'));

    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));
    expect(hasTokens()).toBe(false);
    expect(transport.requestsTo('POST', '/api/v1/auth/logout')).toHaveLength(1);
  });

  it('still signs the player out when the revoke cannot reach the server', async () => {
    await signedIn();
    transport.on('POST', '/api/v1/auth/logout', networkFailure());
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    renderScreen(<AccountPanel />);
    fireEvent.press(screen.getByLabelText('Sign out'));

    // A player who taps sign out on a train has decided to leave. Refusing would strand
    // them in the account AND leave live credentials on the device.
    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));
    expect(hasTokens()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// The account panel
// ---------------------------------------------------------------------------

/** A screen that reads the player and says what the read said — the smallest such screen. */
function WhoAmI() {
  const user = useCurrentUser();
  if (user.error !== null) return <Text>{authErrorMessage(user.error)}</Text>;
  return <Text>{user.data?.nickname ?? ''}</Text>;
}

describe('the account panel', () => {
  /**
   * **The panel is the button now** (ADR-0179 §1). The identity it drew — the nickname and the
   * email — is the You tab's header card's and its *Nickname* row's, asserted where they are
   * drawn (`theShell.test.tsx`); what the panel keeps is the one act that is the account's.
   */
  it('draws the way out, and no identity of its own', async () => {
    setSessionStatus('authenticated');
    transport.on('GET', '/api/v1/users/me', () => json(USER));

    renderScreen(<AccountPanel />);

    expect(screen.getByLabelText('Sign out')).toBeTruthy();
    expect(screen.queryByText('ada')).toBeNull();
    expect(screen.queryByText('ada@example.com')).toBeNull();
    // Nothing read: the panel has no fact of its own to fetch.
    expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(0);
  });

  it('does not sign the player out when a request is forbidden', async () => {
    // Real credentials, because the assertion is that they SURVIVE.
    await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
    transport.on('GET', '/api/v1/users/me', () => errorResponse(403, 'forbidden'));

    // Any screen that reads the player: the rule is the session's, not a panel's.
    renderScreen(<WhoAmI />);

    await waitFor(() =>
      expect(screen.getByText('Something went wrong at our end. Try again later.')),
    );
    // A 403 means "you may not do this", said to a perfectly valid session. Signing the
    // player out in response is both wrong and infuriating.
    expect(getSessionStatus()).toBe('authenticated');
    expect(hasTokens()).toBe(true);
  });
});

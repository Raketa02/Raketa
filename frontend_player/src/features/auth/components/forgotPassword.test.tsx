/**
 * *Forgot password?* — driven through the real route tree and the network boundary
 * ([#515](https://github.com/Raketa02/Raketa/issues/515),
 * [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §5).
 *
 * Only `fetch` is faked. The router, the `(auth)` guard, the entry gate, the http client, the
 * keychain module, the session machine, the use-cases, the mutations, the schemas and the screens
 * all run for real — so a pass here means a player who has forgotten their password can ask, type
 * the code and set a new one, and is signed in at the end, minus the socket.
 *
 * Every assertion is about what a player can see or what left the device.
 */

import { fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import {
  clearStoredTokens,
  getSessionStatus,
  hasTokens,
  readStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  NOW_TAB_LINE,
  ONBOARDING_ROUTES,
  launchSignedIn,
  stubGate,
  type GateStub,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { PASSWORD_RULE } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';

import { EMAIL_LABEL, REPEAT_PASSWORD_LABEL } from './authPresentation';
import { RESET_COPY } from './resetPresentation';

const FORGOT_PATH = '/api/v1/auth/forgot-password';
const CLAIM_PATH = '/api/v1/auth/forgot-password/claim';
const NEW_PASSWORD_PATH = '/api/v1/auth/forgot-password/new-password';

/** The email's link token — URL-safe, as the server mints it. */
const TOKEN = 'Zx9_link-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';

/** What a right code buys — URL-safe, as the server mints it. */
const TICKET = 'ticket_Qx2P-k7m4AbCdEfGhIjKlMnOpQrStUvWxYz012';

/** This session's own pair, which the new password answers with. */
const NEW_PAIR: Wire['TokenResponse'] = {
  access_token: 'access-after-reset',
  refresh_token: 'refresh-after-reset',
  token_type: 'bearer',
  expires_in: 900,
};

/** Tomek plays padel and is past onboarding, so a session that begins lands on the Now tab. */
const IN_THE_APP: GateStub = {
  hasPlayerProfile: true,
  ratings: [
    {
      sport: 'PADEL',
      mu: 2.71,
      sigma: 0.62,
      confidence: 28,
      range: { low: 2.09, high: 3.33 },
      band: { name: 'Established', lower: 2.7, upper: 3.8 },
      status: 'initial_estimate',
      engine_version: 'racketskill-v3',
      updated_at: '2026-08-14T09:00:00Z',
    },
  ],
};

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A cold launch with nobody signed in, on the one sign-in screen everyone uses. */
async function launchSignedOut(initialUrl = '/sign-in') {
  setSessionStatus('unauthenticated');
  stubGate(transport, IN_THE_APP);
  renderRouter(ONBOARDING_ROUTES, { initialUrl });
  await waitFor(() => expect(screen).toHavePathname(initialUrl));
}

/** The server's one answer to *Forgot password?*, for everybody: `202`, and no body. */
function stubAsk() {
  transport.on('POST', FORGOT_PATH, () => new Response(null, { status: 202 }));
}

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

function stubClaim(ticket = TICKET) {
  transport.on('POST', CLAIM_PATH, () =>
    json<Wire['ClaimTicketResponse']>({ ticket, expires_in: 900 }),
  );
}

/** A refusal the server names a field for — `details.field`, as the wire carries it. */
function refusedOn(field: string, status: number, code: string): Response {
  return json<Wire['ErrorResponse']>(
    { code, message: 'test refusal', trace_id: 'trace-test', details: { field } },
    status,
  );
}

function stubNewPassword() {
  transport.on('POST', NEW_PASSWORD_PATH, () => json(NEW_PAIR));
}

/** From sign-in to the confirmation, as Tomek walks it. */
async function askFor(email: string) {
  stubAsk();
  await launchSignedOut();
  fireEvent.press(screen.getByLabelText(RESET_COPY.signInLink));
  await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
  fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), email);
  fireEvent.press(screen.getByLabelText(RESET_COPY.ask.send));
  await waitFor(() => expect(screen).toHavePathname('/forgot-password/sent'));
}

describe('asking', () => {
  it('sits under the Sign in button and opens the email form', async () => {
    await launchSignedOut();

    fireEvent.press(screen.getByLabelText(RESET_COPY.signInLink));

    await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
    expect(screen.getByText(RESET_COPY.ask.title)).toBeTruthy();
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  it('carries the email already typed under Sign in', async () => {
    await launchSignedOut();

    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'tomek@example.com');
    fireEvent.press(screen.getByLabelText(RESET_COPY.signInLink));

    await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
    expect(screen.getByLabelText(EMAIL_LABEL).props.value).toBe('tomek@example.com');
  });

  /**
   * **The same message whether or not the account exists.** The server's answer is identical for
   * both, and so is this screen: it says *if* that email has an account, and nothing on it depends
   * on whether one does.
   */
  it('sends the email and tells him to check his inbox, in words that do not say whether he has an account', async () => {
    await askFor(' Tomek@Example.com ');

    const [asked] = transport.requestsTo('POST', FORGOT_PATH);
    expect(asked?.body).toEqual({ email: 'tomek@example.com' });
    expect(screen.getByText(RESET_COPY.sent.title)).toBeTruthy();
    expect(
      screen.getByText(
        "If tomek@example.com has a Raketa account, we've sent it a link and an 8-character code. " +
          'Both work for one hour, once.',
      ),
    ).toBeTruthy();
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  it('refuses an address that is not one before a round trip', async () => {
    await launchSignedOut('/forgot-password');

    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'tomek');
    fireEvent.press(screen.getByLabelText(RESET_COPY.ask.send));

    expect(await screen.findByText("That doesn't look like an email address.")).toBeTruthy();
    expect(transport.requestsTo('POST', FORGOT_PATH)).toHaveLength(0);
  });

  it('says the connection failed, and stays on the form', async () => {
    transport.on('POST', FORGOT_PATH, networkFailure());
    await launchSignedOut('/forgot-password');

    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'tomek@example.com');
    fireEvent.press(screen.getByLabelText(RESET_COPY.ask.send));

    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen).toHavePathname('/forgot-password');
  });

  it('opens the code screen from the confirmation with the email already in its box', async () => {
    await askFor('tomek@example.com');

    fireEvent.press(screen.getByLabelText(RESET_COPY.sent.enterCode));

    await waitFor(() => expect(screen).toHavePathname('/forgot-password/code'));
    expect(screen.getByLabelText(EMAIL_LABEL).props.value).toBe('tomek@example.com');
    expect(screen.getByLabelText(RESET_COPY.code.label)).toBeTruthy();
  });

  it('goes back to sign in from the confirmation', async () => {
    await askFor('tomek@example.com');

    fireEvent.press(screen.getByLabelText(RESET_COPY.backToSignIn));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  });
});

/** On from the confirmation: the code screen, typed and sent. */
async function claim(code = 'K7M4QX2P') {
  fireEvent.press(screen.getByLabelText(RESET_COPY.sent.enterCode));
  await waitFor(() => expect(screen).toHavePathname('/forgot-password/code'));
  fireEvent.changeText(screen.getByLabelText(RESET_COPY.code.label), code);
  fireEvent.press(screen.getByLabelText(RESET_COPY.code.continue));
}

function typeNewPassword(password = 'forehand42', repeat = password) {
  fireEvent.changeText(screen.getByLabelText(RESET_COPY.newPassword.label), password);
  fireEvent.changeText(screen.getByLabelText(REPEAT_PASSWORD_LABEL), repeat);
  fireEvent.press(screen.getByLabelText(RESET_COPY.newPassword.set));
}

describe('the code, and a new password', () => {
  /**
   * **The ticket's own walk**: Tomek taps *Forgot password?*, types his email, types the code from
   * the email, sets a new password — and he's signed in. The code is read the way the server reads
   * it, so the dash he typed to keep his place is not sent.
   */
  it('takes him from Forgot password? to signed in, in the app', async () => {
    stubClaim();
    stubNewPassword();
    await askFor('tomek@example.com');

    await claim('k7m4-qx2p');

    await waitFor(() => expect(screen).toHavePathname('/forgot-password/new-password'));
    const [claimed] = transport.requestsTo('POST', CLAIM_PATH);
    expect(claimed?.body).toEqual({ email: 'tomek@example.com', code: 'K7M4QX2P' });
    expect(screen.getByText(RESET_COPY.newPassword.title)).toBeTruthy();

    typeNewPassword();

    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    expect(getSessionStatus()).toBe('authenticated');
    const [set] = transport.requestsTo('POST', NEW_PASSWORD_PATH);
    expect(set?.body).toEqual({ ticket: TICKET, password: 'forehand42' });
    // The pair the server answered is the one in the keychain — what survives a kill.
    await expect(readStoredTokens()).resolves.toEqual({
      accessToken: 'access-after-reset',
      refreshToken: 'refresh-after-reset',
    });
    expect(toasts()).toEqual([[RESET_COPY.done, 'ok']]);
  });
});

describe('a code that does not work', () => {
  /**
   * **Wrong** — and the one that has to change is the code, so it lands under that box. The
   * server says the same for an address nothing was sent to, and so does the sentence.
   */
  it('puts a wrong code under the code box, and stays', async () => {
    transport.on('POST', CLAIM_PATH, () => refusedOn('code', 400, 'code_incorrect'));
    await askFor('tomek@example.com');

    await claim('K7M4QX2Z');

    expect(
      await screen.findByText(
        "That isn't the code we sent to that email. Check it and type it again.",
      ),
    ).toBeTruthy();
    expect(screen).toHavePathname('/forgot-password/code');
    expect(transport.requestsTo('POST', NEW_PASSWORD_PATH)).toHaveLength(0);
  });

  /** **Expired says to ask again**, and *Ask again* is right there, with the email carried. */
  it('says an expired code has to be asked for again, and asking again is one press', async () => {
    transport.on('POST', CLAIM_PATH, () => errorResponse(409, 'credential_expired'));
    await askFor('tomek@example.com');

    await claim();

    expect(await screen.findByText('That code has expired. Ask again for a new one.')).toBeTruthy();

    fireEvent.press(screen.getByLabelText(RESET_COPY.code.askAgain));

    await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
    expect(screen.getByLabelText(EMAIL_LABEL).props.value).toBe('tomek@example.com');
    fireEvent.press(screen.getByLabelText(RESET_COPY.ask.send));
    await waitFor(() => expect(transport.requestsTo('POST', FORGOT_PATH)).toHaveLength(2));
  });

  it.each([
    [
      'credential_used',
      'That code has already been used. Sign in with your new password, or ask again for a new one.',
    ],
    [
      'credential_locked',
      'Too many wrong codes were typed, so that one is locked. Ask again for a new one.',
    ],
  ])('says %s in its own words', async (code, sentence) => {
    transport.on('POST', CLAIM_PATH, () => errorResponse(409, code));
    await askFor('tomek@example.com');

    await claim();

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(screen).toHavePathname('/forgot-password/code');
  });

  /** Five wrong codes lock the email, so one that cannot be right does not spend an attempt. */
  it('refuses a code of the wrong length before a round trip', async () => {
    await askFor('tomek@example.com');

    await claim('K7M4');

    expect(await screen.findByText('The code is 8 characters.')).toBeTruthy();
    expect(transport.requestsTo('POST', CLAIM_PATH)).toHaveLength(0);
  });
});

describe('setting the new password', () => {
  /** From sign-in to *Set a new password* by a right code. */
  async function toNewPassword() {
    stubClaim();
    await askFor('tomek@example.com');
    await claim();
    await waitFor(() => expect(screen).toHavePathname('/forgot-password/new-password'));
  }

  it('writes the rule under the box before anything is typed', async () => {
    await toNewPassword();

    expect(screen.getByText(PASSWORD_RULE)).toBeTruthy();
    expect(screen.getByText(RESET_COPY.newPassword.lead)).toBeTruthy();
  });

  it.each([
    ['forehands', 'forehands', 'Use at least one digit.'],
    ['short1', 'short1', 'Use at least 8 characters.'],
    ['forehand42', 'forehand43', "Those passwords don't match."],
  ])('refuses %p / %p before a round trip', async (password, repeat, sentence) => {
    await toNewPassword();

    typeNewPassword(password, repeat);

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(transport.requestsTo('POST', NEW_PASSWORD_PATH)).toHaveLength(0);
  });

  /** The server's copy of the rule, under the box — and the rule is not drawn a second time. */
  it("puts the server's password_too_weak under the box", async () => {
    transport.on('POST', NEW_PASSWORD_PATH, () => refusedOn('password', 400, 'password_too_weak'));
    await toNewPassword();

    typeNewPassword();

    // The refusal line under the box says the rule, and the note that said it before is gone.
    expect(await screen.findByRole('alert', { name: PASSWORD_RULE })).toBeTruthy();
    expect(screen.getAllByText(PASSWORD_RULE)).toHaveLength(1);
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  /**
   * **A ticket lasts fifteen minutes, and a claim is not a use.** *Enter the code again* goes back
   * to boxes that still hold the email and the code, and the same code buys a fresh ticket.
   */
  it('sends him back to the code when the ticket ran out, and the same code buys another', async () => {
    transport.on('POST', NEW_PASSWORD_PATH, () => errorResponse(409, 'ticket_expired'));
    await toNewPassword();

    typeNewPassword();

    expect(await screen.findByText('That took too long. Enter the code again.')).toBeTruthy();
    fireEvent.press(screen.getByLabelText(RESET_COPY.newPassword.enterCodeAgain));

    await waitFor(() => expect(screen).toHavePathname('/forgot-password/code'));
    expect(screen.getByLabelText(RESET_COPY.code.label).props.value).toBe('K7M4QX2P');
    stubClaim('ticket_the-second-one');
    stubNewPassword();
    fireEvent.press(screen.getByLabelText(RESET_COPY.code.continue));
    await waitFor(() => expect(screen).toHavePathname('/forgot-password/new-password'));
    typeNewPassword();

    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    expect(transport.requestsTo('POST', NEW_PASSWORD_PATH).at(-1)?.body).toEqual({
      ticket: 'ticket_the-second-one',
      password: 'forehand42',
    });
  });

  it.each([
    ['credential_expired', 'That code has expired. Ask again for a new one.'],
    [
      'credential_used',
      'That code has already been used. Sign in with your new password, or ask again for a new one.',
    ],
    [
      'credential_locked',
      'Too many wrong codes were typed, so that one is locked. Ask again for a new one.',
    ],
    ['credential_not_found', 'That code has stopped working. Ask again for a new one.'],
  ])('says %s about the code, and stays signed out', async (code, sentence) => {
    transport.on('POST', NEW_PASSWORD_PATH, () => errorResponse(409, code));
    await toNewPassword();

    typeNewPassword();

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(getSessionStatus()).toBe('unauthenticated');
    expect(hasTokens()).toBe(false);
  });
});

describe('setting it, when the code is spent or the line is down', () => {
  /**
   * **The way out follows the refusal.** Once the email is spent, back to the code would only meet
   * the same refusal one screen earlier — so the link under the button becomes *Ask again*, with
   * the address carried.
   */
  it('offers Ask again, with the email, once the code is spent', async () => {
    stubClaim();
    transport.on('POST', NEW_PASSWORD_PATH, () => errorResponse(409, 'credential_expired'));
    await askFor('tomek@example.com');
    await claim();
    await waitFor(() => expect(screen).toHavePathname('/forgot-password/new-password'));
    expect(screen.getByLabelText(RESET_COPY.newPassword.enterCodeAgain)).toBeTruthy();

    typeNewPassword();
    await screen.findByText('That code has expired. Ask again for a new one.');
    expect(screen.queryByLabelText(RESET_COPY.newPassword.enterCodeAgain)).toBeNull();
    fireEvent.press(screen.getByLabelText(RESET_COPY.newPassword.askAgain));

    await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
    expect(screen.getByLabelText(EMAIL_LABEL).props.value).toBe('tomek@example.com');
  });

  it('says the connection failed on the code, and stays', async () => {
    transport.on('POST', CLAIM_PATH, networkFailure());
    await askFor('tomek@example.com');

    await claim();

    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen).toHavePathname('/forgot-password/code');
  });

  it('says the connection failed on the new password, and stays signed out', async () => {
    stubClaim();
    transport.on('POST', NEW_PASSWORD_PATH, networkFailure());
    await askFor('tomek@example.com');
    await claim();
    await waitFor(() => expect(screen).toHavePathname('/forgot-password/new-password'));

    typeNewPassword();

    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(getSessionStatus()).toBe('unauthenticated');
    // Nothing was spent that the person can see, so the way back to the code stays.
    expect(screen.getByLabelText(RESET_COPY.newPassword.enterCodeAgain)).toBeTruthy();
  });
});

describe("the email's link", () => {
  /**
   * **The reset-link screen exists and is reachable by route** — `reset/<token>`, the path the
   * email's button names. The links ticket (#520) is what opens it from an incoming link.
   */
  it('opens Set a new password, sends the token, and signs him in', async () => {
    stubNewPassword();
    await launchSignedOut(`/reset/${TOKEN}`);

    expect(screen.getByText(RESET_COPY.newPassword.title)).toBeTruthy();
    typeNewPassword();

    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    const [set] = transport.requestsTo('POST', NEW_PASSWORD_PATH);
    expect(set?.body).toEqual({ token: TOKEN, password: 'forehand42' });
    await expect(readStoredTokens()).resolves.toEqual({
      accessToken: 'access-after-reset',
      refreshToken: 'refresh-after-reset',
    });
    expect(toasts()).toEqual([[RESET_COPY.done, 'ok']]);
  });

  it.each([
    ['credential_expired', 409, 'That link has expired. Ask again for a new one.'],
    [
      'credential_used',
      409,
      'That link has already been used. Sign in with your new password, or ask again for a new one.',
    ],
    [
      'credential_locked',
      409,
      'Too many wrong codes were typed for that email, so its link is locked too. Ask again for a new one.',
    ],
    ['credential_not_found', 404, "That link isn't one we sent. Ask again for a new one."],
  ])('says %s about the link', async (code, status, sentence) => {
    transport.on('POST', NEW_PASSWORD_PATH, () => errorResponse(status, code));
    await launchSignedOut(`/reset/${TOKEN}`);

    typeNewPassword();

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  it('asks again from a link that did not work', async () => {
    transport.on('POST', NEW_PASSWORD_PATH, () => errorResponse(409, 'credential_expired'));
    await launchSignedOut(`/reset/${TOKEN}`);
    typeNewPassword();
    await screen.findByText('That link has expired. Ask again for a new one.');

    fireEvent.press(screen.getByLabelText(RESET_COPY.newPassword.askAgain));

    await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
  });
});

describe('what the routes refuse', () => {
  /** A route param is input from outside the app, and a token that cannot be one opens nothing. */
  it('sends a link with a token that cannot be one to the form that asks for a working one', async () => {
    setSessionStatus('unauthenticated');
    stubGate(transport, IN_THE_APP);
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/reset/not.a~token' });

    await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
    expect(transport.requestsTo('POST', NEW_PASSWORD_PATH)).toHaveLength(0);
  });

  it('sends Set a new password with no ticket to the code screen', async () => {
    setSessionStatus('unauthenticated');
    stubGate(transport, IN_THE_APP);
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/forgot-password/new-password' });

    await waitFor(() => expect(screen).toHavePathname('/forgot-password/code'));
  });

  it('sends a confirmation about no address to the form', async () => {
    setSessionStatus('unauthenticated');
    stubGate(transport, IN_THE_APP);
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/forgot-password/sent' });

    await waitFor(() => expect(screen).toHavePathname('/forgot-password'));
  });
});

describe('the other phone', () => {
  /**
   * **His old phone isn't signed in any more.** A new password refuses every token issued before
   * it: the old phone's next request is `access_token_revoked`, its refresh is revoked, and the
   * session ends there — on the sign-in screen, with nothing left in the keychain.
   */
  it('is signed out on its next request', async () => {
    stubGate(transport, IN_THE_APP);
    transport.on('GET', '/api/v1/users/me', () => errorResponse(401, 'access_token_revoked'));
    transport.on('POST', '/api/v1/auth/refresh', () => errorResponse(401, 'refresh_token_revoked'));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(hasTokens()).toBe(false);
  });
});

/**
 * ***Have an invitation code?*** and ***Set your password*** — an invited person's way in, driven
 * through the real route tree and the network boundary
 * ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories 113–116 and 121,
 * [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §2–§5).
 *
 * Only `fetch` is faked. The router, the `(auth)` guard, the entry gate, the http client, the
 * keychain module, the session machine, the use-cases, the mutations, the schemas and the screens
 * all run for real — so a pass here means Marta, whom Ogrody 33 invited and who cannot use the
 * email's button, can type her email and code, choose a password and be in her administrator area,
 * minus the socket.
 */

import { fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import {
  clearStoredTokens,
  getSessionStatus,
  readStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { ADMINISTRATOR_ONLY, CLUB_ID, club } from '@/test-support/officialGroupsServer';
import { ONBOARDING_ROUTES, stubGate } from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { PASSWORD_RULE } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';

import { EMAIL_LABEL, REPEAT_PASSWORD_LABEL } from './authPresentation';
import { INVITATION_COPY } from './invitationPresentation';

const CLAIM_PATH = '/api/v1/invitations/claim';
const PASSWORD_PATH = '/api/v1/invitations/password';
const BY_TOKEN_PATH = '/api/v1/invitations/by-token';

/** What a right code buys — URL-safe, as the server mints it. */
const TICKET = 'ticket_Inv-7m4AbCdEfGhIjKlMnOpQrStUvWxYz012';

/** The email's link token — URL-safe, as the server mints it. */
const TOKEN = 'Zx9_invite-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';

/** The session the new password answers with. */
const HER_PAIR: Wire['TokenResponse'] = {
  access_token: 'access-marta',
  refresh_token: 'refresh-marta',
  token_type: 'bearer',
  expires_in: 900,
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

/**
 * A cold launch with nobody signed in. Once a session begins, the account is Marta's as the
 * invitation opened it: the name Ogrody 33 typed, no nickname, and nothing but its administrator
 * profile — so the gate sends her to the area, where the club's routes answer.
 */
async function launchSignedOut(initialUrl = '/sign-in') {
  setSessionStatus('unauthenticated');
  stubGate(transport, { name: 'Marta Nowak', nickname: null, profiles: ADMINISTRATOR_ONLY });
  club().install(transport);
  renderRouter(ONBOARDING_ROUTES, { initialUrl });
  await waitFor(() => expect(screen).toHavePathname(initialUrl));
}

function stubClaim(ticket = TICKET) {
  transport.on('POST', CLAIM_PATH, () =>
    json<Wire['ClaimTicketResponse']>({ ticket, expires_in: 900 }),
  );
}

function stubPassword() {
  transport.on('POST', PASSWORD_PATH, () => json(HER_PAIR));
}

/** A refusal the server names a field for — `details.field`, as the wire carries it. */
function refusedOn(field: string, status: number, code: string): Response {
  return json<Wire['ErrorResponse']>(
    { code, message: 'test refusal', trace_id: 'trace-test', details: { field } },
    status,
  );
}

/** From sign-in, the code form, typed and sent. */
async function typeTheCode(email = 'marta@ogrody33.pl', code = 'K7M4QX2P') {
  await launchSignedOut();
  fireEvent.press(screen.getByLabelText(INVITATION_COPY.signInLink));
  await waitFor(() => expect(screen).toHavePathname('/invitation'));
  fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), email);
  fireEvent.changeText(screen.getByLabelText(INVITATION_COPY.code.label), code);
  fireEvent.press(screen.getByLabelText(INVITATION_COPY.code.continue));
}

function typeAPassword(password = 'backhand42', repeat = password) {
  fireEvent.changeText(screen.getByLabelText(INVITATION_COPY.password.label), password);
  fireEvent.changeText(screen.getByLabelText(REPEAT_PASSWORD_LABEL), repeat);
  fireEvent.press(screen.getByLabelText(INVITATION_COPY.password.set));
}

async function expectTheArea() {
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
  expect(getSessionStatus()).toBe('authenticated');
}

describe('Have an invitation code?', () => {
  /**
   * **Marta's own walk**: she cannot use the email's button, so under Sign in she taps *Have an
   * invitation code?*, types her email and the code, lands on *Set your password* with her email
   * locked, chooses one — and she is in her administrator area.
   */
  it('takes her from Sign in to her administrator area', async () => {
    stubClaim();
    stubPassword();

    await typeTheCode(' Marta@Ogrody33.pl ', 'k7m4-qx2p');

    await waitFor(() => expect(screen).toHavePathname('/invitation/password'));
    const [claimed] = transport.requestsTo('POST', CLAIM_PATH);
    expect(claimed?.body).toEqual({ email: 'marta@ogrody33.pl', code: 'K7M4QX2P' });
    expect(screen.getByText(INVITATION_COPY.password.title)).toBeTruthy();
    // Her email, and she cannot change it: the invitation is to that address.
    const email = screen.getByLabelText(EMAIL_LABEL);
    expect(email.props.value).toBe('marta@ogrody33.pl');
    expect(email.props.editable).toBe(false);
    expect(screen.getByText(PASSWORD_RULE)).toBeTruthy();

    typeAPassword();

    await expectTheArea();
    const [set] = transport.requestsTo('POST', PASSWORD_PATH);
    expect(set?.body).toEqual({ ticket: TICKET, password: 'backhand42' });
    await expect(readStoredTokens()).resolves.toEqual({
      accessToken: 'access-marta',
      refreshToken: 'refresh-marta',
    });
  });
});

describe('the code form', () => {
  it('sits under the Sign in button, beside Forgot password?, and carries the email typed there', async () => {
    await launchSignedOut();

    // On the one sign-in screen, after its button and *Forgot password?*.
    const links = screen.getAllByRole('link').map((link) => link.props.accessibilityLabel);
    expect(links.indexOf('Forgot password?')).toBeLessThan(
      links.indexOf(INVITATION_COPY.signInLink),
    );

    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'marta@ogrody33.pl');
    fireEvent.press(screen.getByLabelText(INVITATION_COPY.signInLink));

    await waitFor(() => expect(screen).toHavePathname('/invitation'));
    expect(screen.getByLabelText(EMAIL_LABEL).props.value).toBe('marta@ogrody33.pl');
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  /** Five wrong codes lock the invitation, so one that cannot be right does not spend an attempt. */
  it('refuses a code of the wrong length before a round trip', async () => {
    await typeTheCode('marta@ogrody33.pl', 'K7M4');

    expect(await screen.findByText('The code is 8 characters.')).toBeTruthy();
    expect(transport.requestsTo('POST', CLAIM_PATH)).toHaveLength(0);
  });

  it('goes back to sign in', async () => {
    await launchSignedOut();
    fireEvent.press(screen.getByLabelText(INVITATION_COPY.signInLink));
    await waitFor(() => expect(screen).toHavePathname('/invitation'));

    fireEvent.press(screen.getByLabelText(INVITATION_COPY.backToSignIn));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  });
});

describe('a code that does not work', () => {
  /** The one that has to change is the code, so it lands under that box. */
  it('puts a wrong code under the code box, and stays', async () => {
    transport.on('POST', CLAIM_PATH, () => refusedOn('code', 400, 'code_incorrect'));

    await typeTheCode();

    expect(
      await screen.findByText(
        "That isn't the code we sent to that email. Check it and type it again.",
      ),
    ).toBeTruthy();
    expect(screen).toHavePathname('/invitation');
    expect(transport.requestsTo('POST', PASSWORD_PATH)).toHaveLength(0);
  });

  /**
   * **Each its own sentence** — and an expired invitation is the club's to send again, so the
   * sentence says who to ask (story 115).
   */
  it.each([
    ['credential_expired', 'That invitation has expired. Ask the club to send a new one.'],
    [
      'credential_used',
      'That invitation has already been used. Sign in with the password you set.',
    ],
    [
      'credential_locked',
      'Too many wrong codes were typed, so that invitation is locked. Ask the club to send a new one.',
    ],
  ])('says %s in its own words', async (code, sentence) => {
    transport.on('POST', CLAIM_PATH, () => errorResponse(409, code));

    await typeTheCode();

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(screen).toHavePathname('/invitation');
  });

  /**
   * **Tomek plays already, and typed the code instead** (story 121): an existing account accepts
   * from the app, signed in — so he is sent to sign in, and the way there is under the button.
   */
  it('tells an email that already has an account to sign in and accept', async () => {
    transport.on('POST', CLAIM_PATH, () => errorResponse(409, 'sign_in_to_accept'));

    await typeTheCode('tomek@example.com');

    expect(
      await screen.findByText('This email already has an account — sign in to accept.'),
    ).toBeTruthy();
    fireEvent.press(screen.getByLabelText(INVITATION_COPY.backToSignIn));
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(getSessionStatus()).toBe('unauthenticated');
  });
});

describe('Set your password, by a code', () => {
  async function toSetYourPassword() {
    stubClaim();
    await typeTheCode();
    await waitFor(() => expect(screen).toHavePathname('/invitation/password'));
  }

  it.each([
    ['backhands', 'backhands', 'Use at least one digit.'],
    ['short1', 'short1', 'Use at least 8 characters.'],
    ['backhand42', 'backhand43', "Those passwords don't match."],
  ])('refuses %p / %p before a round trip', async (password, repeat, sentence) => {
    await toSetYourPassword();

    typeAPassword(password, repeat);

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(transport.requestsTo('POST', PASSWORD_PATH)).toHaveLength(0);
  });

  it("puts the server's password_too_weak under the box", async () => {
    transport.on('POST', PASSWORD_PATH, () => refusedOn('password', 400, 'password_too_weak'));
    await toSetYourPassword();

    typeAPassword();

    expect(await screen.findByRole('alert', { name: PASSWORD_RULE })).toBeTruthy();
    expect(getSessionStatus()).toBe('unauthenticated');
  });

  /** A claim is not a use: back to boxes that still hold the code, and the same code buys another. */
  it('sends her back to the code when the ticket ran out, and the same code buys another', async () => {
    transport.on('POST', PASSWORD_PATH, () => errorResponse(409, 'ticket_expired'));
    await toSetYourPassword();

    typeAPassword();

    expect(await screen.findByText('That took too long. Enter the code again.')).toBeTruthy();
    fireEvent.press(screen.getByLabelText(INVITATION_COPY.password.enterCodeAgain));

    await waitFor(() => expect(screen).toHavePathname('/invitation'));
    expect(screen.getByLabelText(INVITATION_COPY.code.label).props.value).toBe('K7M4QX2P');
    stubClaim('ticket_the-second-one');
    stubPassword();
    fireEvent.press(screen.getByLabelText(INVITATION_COPY.code.continue));
    await waitFor(() => expect(screen).toHavePathname('/invitation/password'));
    typeAPassword();

    await expectTheArea();
    expect(transport.requestsTo('POST', PASSWORD_PATH).at(-1)?.body).toEqual({
      ticket: 'ticket_the-second-one',
      password: 'backhand42',
    });
  });

  /** Spent while she chose one — the code is no help now, so the way out is sign in. */
  it('sends her to sign in once the invitation itself is spent', async () => {
    transport.on('POST', PASSWORD_PATH, () => errorResponse(409, 'credential_expired'));
    await toSetYourPassword();

    typeAPassword();

    expect(
      await screen.findByText('That invitation has expired. Ask the club to send a new one.'),
    ).toBeTruthy();
    expect(screen.queryByLabelText(INVITATION_COPY.password.enterCodeAgain)).toBeNull();
    fireEvent.press(screen.getByLabelText(INVITATION_COPY.backToSignIn));
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  });

  it('sends a ticket that cannot be one to the code form', async () => {
    await launchSignedOut('/sign-in');
    screen.unmount();
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/invitation/password?ticket=not%20one' });

    await waitFor(() => expect(screen).toHavePathname('/invitation'));
  });
});

describe('Set your password, by the email’s link', () => {
  function stubLink(state: Wire['InvitationLinkState']) {
    transport.on('POST', BY_TOKEN_PATH, () =>
      json<Wire['InvitationByTokenResponse']>({
        email: 'marta@ogrody33.pl',
        name: 'Marta Nowak',
        club_name: 'Ogrody 33',
        state,
      }),
    );
  }

  /**
   * **The token is validated first** (story 113): the link is read, and only one that still works
   * draws the form — with the email the server read, locked.
   */
  it('reads the link, locks her email, and signs her into her area', async () => {
    stubLink('valid');
    stubPassword();

    await launchSignedOut(`/invite/${TOKEN}`);

    expect(await screen.findByText(INVITATION_COPY.password.title)).toBeTruthy();
    const email = await screen.findByLabelText(EMAIL_LABEL);
    expect(email.props.value).toBe('marta@ogrody33.pl');
    expect(email.props.editable).toBe(false);
    expect(transport.requestsTo('POST', BY_TOKEN_PATH)[0]?.body).toEqual({ token: TOKEN });

    typeAPassword();

    await expectTheArea();
    expect(transport.requestsTo('POST', PASSWORD_PATH)[0]?.body).toEqual({
      token: TOKEN,
      password: 'backhand42',
    });
  });

  it.each([
    ['expired', 'That link has expired. Ask the club to send a new one.'],
    ['used', 'That link has already been used. Sign in with the password you set.'],
    [
      'locked',
      'Too many wrong codes were typed for that invitation, so its link is locked too. Ask the club to send a new one.',
    ],
  ] as const)(
    'says a link that is %s in its own words, and draws no form',
    async (state, sentence) => {
      stubLink(state);

      await launchSignedOut(`/invite/${TOKEN}`);

      expect(await screen.findByText(sentence)).toBeTruthy();
      expect(screen.queryByLabelText(INVITATION_COPY.password.label)).toBeNull();
      fireEvent.press(screen.getByLabelText(INVITATION_COPY.backToSignIn));
      await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    },
  );

  it('says a link that was never sent is not one of ours', async () => {
    transport.on('POST', BY_TOKEN_PATH, () => errorResponse(404, 'credential_not_found'));

    await launchSignedOut(`/invite/${TOKEN}`);

    expect(
      await screen.findByText("That link isn't one we sent. Ask the club to send a new one."),
    ).toBeTruthy();
    expect(screen.queryByLabelText(INVITATION_COPY.password.label)).toBeNull();
    expect(screen.queryByLabelText(INVITATION_COPY.tryAgain)).toBeNull();
  });

  it('says a link that could not be read, and reads it again', async () => {
    transport.on('POST', BY_TOKEN_PATH, () => errorResponse(503, 'service_unavailable'));

    await launchSignedOut(`/invite/${TOKEN}`);

    expect(await screen.findByLabelText(INVITATION_COPY.tryAgain)).toBeTruthy();
    stubLink('valid');
    fireEvent.press(screen.getByLabelText(INVITATION_COPY.tryAgain));

    expect(await screen.findByLabelText(INVITATION_COPY.password.label)).toBeTruthy();
  });

  it('sends a token that cannot be one to the code form', async () => {
    await launchSignedOut('/sign-in');
    screen.unmount();
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/invite/not%20a%20token' });

    await waitFor(() => expect(screen).toHavePathname('/invitation'));
  });
});

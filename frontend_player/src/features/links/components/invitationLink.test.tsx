/**
 * **An invitation's link, opened on a phone** — in every sign-in state the ticket names
 * ([#520](https://github.com/Raketa02/Raketa/issues/520), PRD #500 stories 112–118):
 *
 * - Marta, a new person, taps the button and lands on **Set your password**, the token read and her
 *   email locked;
 * - Tomek already plays: signed in, he gets the **Accept** sheet; signed out, he signs in first and
 *   then gets it;
 * - Kuba's phone is signed in when Tomek's link is opened on it: a sheet names the address the
 *   invitation is for, and offers **Sign out**.
 *
 * The real route tree with the app's link reader in front of it; only `fetch` is faked.
 */

import { fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import {
  beginSession,
  clearStoredTokens,
  getSessionStatus,
  resetSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ADMINISTRATOR_ONLY,
  CLUB,
  CLUB_ID,
  O3_CLUB_GROUP,
  club,
  rating,
} from '@/test-support/officialGroupsServer';
import {
  NOW_TAB_LINE,
  ONBOARDING_ROUTES,
  launchByLink,
  launchSignedIn,
  openLink,
  stubGate,
  stubInterest,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
  type GateStub,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useHeldLinkStore } from '../store/heldLink.store';

import { redirectSystemPath } from './redirectSystemPath';

const TOKEN = 'Zx9_invite-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';
const BY_TOKEN_PATH = '/api/v1/invitations/by-token';
const PASSWORD_PATH = '/api/v1/invitations/password';

const TOMEK_EMAIL = 'tomek.k@example.com';
const KUBA_EMAIL = 'kuba@example.com';
const MARTA_EMAIL = 'marta@ogrody33.pl';

const SHEET_TITLE = `${CLUB.name} wants to make you an administrator`;
const FOR_TOMEK = `This invitation is for ${TOMEK_EMAIL}`;

const INVITATION: Wire['PendingInvitationSchema'] = {
  administrator_id: 'd0000000-0000-4000-8000-000000000001',
  club_id: CLUB_ID,
  club_name: CLUB.name,
  expires_at: '2026-09-29T12:00:00Z',
};

const TOKENS: Wire['TokenResponse'] = {
  access_token: 'access-1',
  refresh_token: 'refresh-1',
  token_type: 'bearer',
  expires_in: 900,
};

/** Tomek plays padel, is past onboarding, and Ogrody 33 has invited him. */
const TOMEK: GateStub = {
  email: TOMEK_EMAIL,
  name: 'Tomek Kowal',
  ratings: [rating('PADEL')],
  hasPlayerProfile: true,
  profiles: {
    acts_as_player: true,
    administers: [],
    pending_invitations: [INVITATION],
    handovers: [],
  },
};

/** Kuba plays padel too, and nobody has invited him. */
const KUBA: GateStub = {
  email: KUBA_EMAIL,
  name: 'Kuba Wróbel',
  ratings: [rating('PADEL')],
  hasPlayerProfile: true,
};

let transport: Transport;

function serve(account: GateStub) {
  stubGate(transport, account);
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
  club([O3_CLUB_GROUP]).install(transport);
}

/** What the link says about itself — `by-token`, read before anything is drawn. */
function stubTheLink(
  state: Wire['InvitationLinkState'] = 'valid',
  email = TOMEK_EMAIL,
  name = 'Tomek Kowal',
) {
  transport.on('POST', BY_TOKEN_PATH, () =>
    json<Wire['InvitationByTokenResponse']>({ email, name, club_name: CLUB.name, state }),
  );
}

function stubSignIn() {
  transport.on('POST', '/api/v1/auth/login', () => json(TOKENS));
}

function stubSignOut() {
  transport.on('POST', '/api/v1/auth/logout', () =>
    json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
  );
}

async function signInAs(email: string) {
  fireEvent.changeText(screen.getByLabelText('Email'), email);
  fireEvent.changeText(screen.getByLabelText('Password'), 'correct horse');
  fireEvent.press(screen.getByLabelText('Sign in'));
}

function typeAPassword() {
  fireEvent.changeText(screen.getByLabelText('Password'), 'backhand42');
  fireEvent.changeText(screen.getByLabelText('Repeat password'), 'backhand42');
  fireEvent.press(screen.getByLabelText('Set password'));
}

async function expectTheAcceptSheet() {
  expect(await screen.findByRole('header', { name: SHEET_TITLE })).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Accept' })).toBeTruthy();
}

const toasts = () => useToastQueue.getState().queue.map((toast) => toast.message);

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  useHeldLinkStore.getState().reset();
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  useHeldLinkStore.getState().reset();
  await clearStoredTokens();
});

describe('a new person', () => {
  /**
   * **Marta's walk**: the button in the club's email opens *Set your password* with the token read
   * and her email locked, and setting one puts her in her administrator area — with nothing more
   * said about the link, which she has just used.
   */
  it('gets Set your password with the token read and the email locked, then her area', async () => {
    serve({
      email: MARTA_EMAIL,
      name: 'Marta Nowak',
      nickname: null,
      profiles: ADMINISTRATOR_ONLY,
    });
    stubTheLink('valid', MARTA_EMAIL, 'Marta Nowak');
    transport.on('POST', PASSWORD_PATH, () => {
      stubTheLink('used', MARTA_EMAIL, 'Marta Nowak');
      return json(TOKENS);
    });

    await launchByLink(`/invite/${TOKEN}`, { signedIn: false });

    await waitFor(() => expect(screen).toHavePathname(`/invite/${TOKEN}`));
    const email = await screen.findByLabelText('Email');
    expect(email.props.value).toBe(MARTA_EMAIL);
    expect(email.props.editable).toBe(false);
    expect(transport.requestsTo('POST', BY_TOKEN_PATH)[0]?.body).toEqual({ token: TOKEN });

    typeAPassword();

    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
    expect(transport.requestsTo('POST', PASSWORD_PATH)[0]?.body).toEqual({
      token: TOKEN,
      password: 'backhand42',
    });
    // Read once more, signed in, and found used by this very account: nothing to say.
    await waitFor(() => expect(transport.requestsTo('POST', BY_TOKEN_PATH)).toHaveLength(2));
    expect(screen.queryByText(/This invitation is for/)).toBeNull();
    expect(toasts()).toEqual([]);
  });
});

describe('an account the invitation was sent to', () => {
  it('gets the Accept sheet when it is signed in', async () => {
    serve(TOMEK);
    stubTheLink();

    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });

    await expectTheAcceptSheet();
  });

  /** Set aside with *Not now* this launch — and the link is him asking for it again. */
  it('gets it again from the link, though it was set aside this launch', async () => {
    serve(TOMEK);
    stubTheLink();
    await launchSignedIn();
    await expectTheAcceptSheet();
    fireEvent.press(screen.getByRole('button', { name: 'Not now' }));
    await waitFor(() => expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull());

    openLink(`raketa://invite/${TOKEN}`);

    await expectTheAcceptSheet();
    // Nobody was moved to get there.
    expect(screen).toHavePathname('/');
  });

  /**
   * **Tomek's own button.** The club's email to an account that already exists carries no token —
   * it is `raketa://`, *open Raketa and accept there* (ADR-0184 §2) — so tapped after *Not now*, it
   * is the app's bare address that asks for the sheet again.
   */
  it('gets it again from the button of the email an existing account is sent', async () => {
    serve(TOMEK);
    await launchSignedIn();
    await expectTheAcceptSheet();
    fireEvent.press(screen.getByRole('button', { name: 'Not now' }));
    await waitFor(() => expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull());

    openLink('raketa://');

    await expectTheAcceptSheet();
    expect(screen).toHavePathname('/');
  });

  /**
   * *Not now* holds until the next launch (story 119): a link about one club takes back that club's
   * and no other's.
   */
  it('takes back only its own club’s invitation from what was set aside', async () => {
    const BONARKA: Wire['PendingInvitationSchema'] = {
      administrator_id: 'd0000000-0000-4000-8000-000000000002',
      club_id: 'c0000000-0000-4000-8000-000000000044',
      club_name: 'Bonarka Arena',
      expires_at: '2026-09-29T13:00:00Z',
    };
    const bonarkaTitle = 'Bonarka Arena wants to make you an administrator';
    serve({
      ...TOMEK,
      profiles: { ...TOMEK.profiles!, pending_invitations: [INVITATION, BONARKA] },
    });
    stubTheLink();
    await launchSignedIn();
    await expectTheAcceptSheet();
    fireEvent.press(screen.getByRole('button', { name: 'Not now' }));
    expect(await screen.findByRole('header', { name: bonarkaTitle })).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: 'Not now' }));
    await waitFor(() => expect(screen.queryByRole('header', { name: bonarkaTitle })).toBeNull());

    openLink(`raketa://invite/${TOKEN}`);

    await expectTheAcceptSheet();
    fireEvent.press(screen.getByRole('button', { name: 'Not now' }));
    await waitFor(() => expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull());
    expect(screen.queryByRole('header', { name: bonarkaTitle })).toBeNull();
  });

  /**
   * **Signed out: he signs in first, then gets the sheet.** The link opens *Set your password*,
   * which is a new person's way in; setting one for an address that is already an account is
   * refused with *sign in to accept*, and signing in is answered with the sheet.
   */
  it('signs in first when it is signed out, then gets the sheet', async () => {
    serve(TOMEK);
    stubTheLink();
    stubSignIn();
    transport.on('POST', PASSWORD_PATH, () => errorResponse(409, 'sign_in_to_accept'));

    await launchByLink(`/invite/${TOKEN}`, { signedIn: false });
    expect(await screen.findByLabelText('Set password')).toBeTruthy();
    typeAPassword();
    expect(
      await screen.findByText('This email already has an account — sign in to accept.'),
    ).toBeTruthy();
    fireEvent.press(screen.getByLabelText('Back to sign in'));
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));

    await signInAs(TOMEK_EMAIL);

    await expectTheAcceptSheet();
  });

  /**
   * **A cold start while the keychain is still being read** — the one path the reader cannot tell
   * apart: it sends the link to its screen, whose guard finds the phone signed in and hands it to
   * the gate, where the held link is answered.
   */
  it('gets it through the screen’s guard at a cold start', async () => {
    serve(TOMEK);
    stubTheLink();

    const landing = redirectSystemPath({ path: `raketa://invite/${TOKEN}`, initial: true });
    expect(landing).toBe(`/invite/${TOKEN}`);
    await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
    renderRouter(ONBOARDING_ROUTES, { initialUrl: landing });

    await expectTheAcceptSheet();
    expect(screen).toHavePathname('/');
  });

  it('says a link that has expired, and offers nothing', async () => {
    serve({ ...TOMEK, profiles: { ...TOMEK.profiles!, pending_invitations: [] } });
    stubTheLink('expired');

    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });

    await waitFor(() =>
      expect(toasts()).toEqual(['That link has expired. Ask the club to send a new one.']),
    );
    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull();
  });

  it('says a link that was never sent is not one of ours', async () => {
    serve(TOMEK);
    transport.on('POST', BY_TOKEN_PATH, () => errorResponse(404, 'credential_not_found'));

    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });

    await waitFor(() =>
      expect(toasts()).toEqual(["That link isn't one we sent. Ask the club to send a new one."]),
    );
  });
});

describe('a phone signed in as somebody else', () => {
  it('names the address the invitation is for, and offers Sign out', async () => {
    serve(KUBA);
    stubTheLink();

    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });

    expect(await screen.findByRole('header', { name: FOR_TOMEK })).toBeTruthy();
    expect(screen.getByText(new RegExp(`You’re signed in as ${KUBA_EMAIL}`))).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeTruthy();
    // Kuba's own app is under it, and nothing was accepted.
    expect(screen.getByText(NOW_TAB_LINE)).toBeTruthy();
    expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull();
  });

  /**
   * **Sign out leads to the link's own way in** — *Set your password*, for Tomek's address — and
   * the link stays held, so an account Tomek already has, signed in there, is offered it.
   */
  it('signs out onto Set your password for that address', async () => {
    serve(KUBA);
    stubTheLink();
    stubSignOut();
    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });
    expect(await screen.findByRole('header', { name: FOR_TOMEK })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Sign out' }));

    await waitFor(() => expect(screen).toHavePathname(`/invite/${TOKEN}`));
    expect(getSessionStatus()).toBe('unauthenticated');
    const email = await screen.findByLabelText('Email');
    expect(email.props.value).toBe(TOMEK_EMAIL);
    expect(email.props.editable).toBe(false);
  });

  it('then offers it to Tomek once he signs in on that phone', async () => {
    serve(KUBA);
    stubTheLink();
    stubSignOut();
    stubSignIn();
    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });
    fireEvent.press(await screen.findByRole('button', { name: 'Sign out' }));
    await waitFor(() => expect(screen).toHavePathname(`/invite/${TOKEN}`));

    serve(TOMEK);
    fireEvent.press(await screen.findByLabelText('Back to sign in'));
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    await signInAs(TOMEK_EMAIL);

    await expectTheAcceptSheet();
  });

  /**
   * **A link belongs to the session it arrived in.** Signed out by the sheet, the phone shows the
   * link's own screen by the token in its path — and Kuba signing back in is not asked about Tomek's
   * invitation again.
   */
  it('asks nothing of Kuba once he signs back in himself', async () => {
    serve(KUBA);
    stubTheLink();
    stubSignOut();
    stubSignIn();
    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });
    fireEvent.press(await screen.findByRole('button', { name: 'Sign out' }));
    await waitFor(() => expect(screen).toHavePathname(`/invite/${TOKEN}`));

    fireEvent.press(await screen.findByLabelText('Back to sign in'));
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    await signInAs(KUBA_EMAIL);

    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    expect(screen.queryByRole('header', { name: FOR_TOMEK })).toBeNull();
    expect(transport.requestsTo('POST', BY_TOKEN_PATH)).toHaveLength(2);
  });

  it('stays signed in, and lets the link go', async () => {
    serve(KUBA);
    stubTheLink();
    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });
    expect(await screen.findByRole('header', { name: FOR_TOMEK })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Stay signed in' }));

    await waitFor(() => expect(screen.queryByRole('header', { name: FOR_TOMEK })).toBeNull());
    expect(getSessionStatus()).toBe('authenticated');
    expect(screen.getByText(NOW_TAB_LINE)).toBeTruthy();
  });

  /** A link that no longer works is said, not signed out for. */
  it('says a used link is used rather than asking anybody to sign out', async () => {
    serve(KUBA);
    stubTheLink('used');

    await launchByLink(`/invite/${TOKEN}`, { signedIn: true });

    await waitFor(() =>
      expect(toasts()).toEqual([
        'That link has already been used. Sign in with the password you set.',
      ]),
    );
    expect(screen.queryByRole('header', { name: FOR_TOMEK })).toBeNull();
  });
});

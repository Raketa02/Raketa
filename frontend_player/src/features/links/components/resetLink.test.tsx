/**
 * **A password reset's link, opened on a phone** — it opens **Set a new password** with its token
 * ([#520](https://github.com/Raketa02/Raketa/issues/520), PRD #500 stories 84–87; the screen is
 * #515's).
 *
 * Signed out, the link lands straight on the screen. Signed in, a sheet asks first: a reset link
 * names no account, so the app cannot tell whether it is this one's, and setting a password through
 * it signs the phone into whichever account it was sent to. **Sign out** then leads to the screen.
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
import { rating } from '@/test-support/officialGroupsServer';
import {
  GATE_USER,
  NOW_TAB_LINE,
  ONBOARDING_ROUTES,
  launchByLink,
  launchSignedIn,
  openLink,
  stubGate,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { useHeldLinkStore } from '../store/heldLink.store';

import { redirectSystemPath } from './redirectSystemPath';

const TOKEN = 'Rs7_reset-token-9Pq3Wn5Lk1Tz8Vb2Hc4Jf6Md0Ng';
const NEW_PASSWORD_PATH = '/api/v1/auth/forgot-password/new-password';

const SHEET_TITLE = 'Set a new password?';

let transport: Transport;

function serve() {
  stubGate(transport, { ratings: [rating('PADEL')], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  transport.on('POST', NEW_PASSWORD_PATH, () =>
    json<Wire['TokenResponse']>({
      access_token: 'access-after-reset',
      refresh_token: 'refresh-after-reset',
      token_type: 'bearer',
      expires_in: 900,
    }),
  );
  transport.on('POST', '/api/v1/auth/logout', () =>
    json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
  );
}

function typeANewPassword() {
  fireEvent.changeText(screen.getByLabelText('New password'), 'forehand42');
  fireEvent.changeText(screen.getByLabelText('Repeat password'), 'forehand42');
  fireEvent.press(screen.getByLabelText('Set password'));
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  useHeldLinkStore.getState().reset();
  serve();
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  useHeldLinkStore.getState().reset();
  await clearStoredTokens();
});

describe('a reset link, with nobody signed in', () => {
  /**
   * The screen sets the password and begins the session, and the link is answered there: the phone
   * that is now signed in is not asked about it again.
   */
  it('opens Set a new password with the token, and signs in', async () => {
    await launchByLink(`/reset/${TOKEN}`, { signedIn: false });

    await waitFor(() => expect(screen).toHavePathname(`/reset/${TOKEN}`));
    expect(screen.getByText('Set a new password')).toBeTruthy();

    typeANewPassword();

    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    expect(transport.requestsTo('POST', NEW_PASSWORD_PATH)[0]?.body).toEqual({
      token: TOKEN,
      password: 'forehand42',
    });
    expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull();
  });

  it('is ignored when its token cannot be one', async () => {
    await launchByLink('/reset/not%20a%20token', { signedIn: false });

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  });
});

describe('a reset link, on a phone that is signed in', () => {
  it('asks to sign out first, naming who is signed in, over wherever the person is', async () => {
    await launchSignedIn();
    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();

    openLink(`raketa://reset/${TOKEN}`);

    expect(await screen.findByRole('header', { name: SHEET_TITLE })).toBeTruthy();
    expect(screen.getByText(new RegExp(`You’re signed in as ${GATE_USER.email}`))).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(transport.requestsTo('POST', NEW_PASSWORD_PATH)).toHaveLength(0);
  });

  /**
   * **A cold start while the keychain is still being read** — the reader sends the link to its
   * screen, whose guard finds the phone signed in and hands it to the gate, where the held link asks.
   */
  it('asks through the screen’s guard at a cold start', async () => {
    const landing = redirectSystemPath({ path: `raketa://reset/${TOKEN}`, initial: true });
    expect(landing).toBe(`/reset/${TOKEN}`);
    await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
    renderRouter(ONBOARDING_ROUTES, { initialUrl: landing });

    expect(await screen.findByRole('header', { name: SHEET_TITLE })).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('signs out onto Set a new password with the token', async () => {
    await launchByLink(`/reset/${TOKEN}`, { signedIn: true });
    fireEvent.press(await screen.findByRole('button', { name: 'Sign out' }));

    await waitFor(() => expect(screen).toHavePathname(`/reset/${TOKEN}`));
    expect(getSessionStatus()).toBe('unauthenticated');
    expect(screen.getByText('Set a new password')).toBeTruthy();

    typeANewPassword();

    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    expect(transport.requestsTo('POST', NEW_PASSWORD_PATH)[0]?.body).toEqual({
      token: TOKEN,
      password: 'forehand42',
    });
    // The link was answered on its screen: the session it began is not asked about it.
    expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull();
  });

  it('stays signed in, and lets the link go', async () => {
    await launchByLink(`/reset/${TOKEN}`, { signedIn: true });

    fireEvent.press(await screen.findByRole('button', { name: 'Stay signed in' }));

    await waitFor(() => expect(screen.queryByRole('header', { name: SHEET_TITLE })).toBeNull());
    expect(getSessionStatus()).toBe('authenticated');
    expect(screen.getByText(NOW_TAB_LINE)).toBeTruthy();
  });
});

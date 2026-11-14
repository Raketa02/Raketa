/**
 * **A friend link, opened on a phone** ([#756](https://github.com/Raketa02/Raketa/issues/756), PRD
 * #743; the friends mechanics §4.2–§4.3). Tomek sends his link, `rakieta.app/f/<code>`:
 *
 * - **Ania, signed in**, opens it and lands on Home with *tomek.k wants to be your friend · Invited
 *   you to Raketa* on top.
 * - **Zofia, new**, opens it, signs up, goes through onboarding, and lands on the same Home.
 * - **Her own link, or a friend's**, moves nobody; **a dead link** is a toast, and so is one whose
 *   owner she blocked.
 * - **On Android, a fresh install** from the public site's Google Play button reads the link it
 *   carried once, on the first launch, as if it had been tapped.
 *
 * Driven through the real route tree **with the app's link reader in front of it**
 * (`src/app/+native-intent`), as `groupLink.test.tsx` is; only `fetch` and Google Play are faked.
 * The server puts Tomek's request on Home the moment his link is opened, as #748's does.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { FRIENDS_COPY, wantsToBeYourFriend } from '@/features/friends/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { walkANewAccountToFinish } from '@/test-support/newAccountWalk';
import { CLUB, CLUB_ID, club, rating } from '@/test-support/officialGroupsServer';
import {
  GATE_USER,
  HOME_PATH,
  HOME_TAB_LINE,
  NOTICES_PATH,
  launchByLink,
  launchSignedIn,
  openLink,
  resetLocation,
  stubGate,
  stubHome,
  stubProfileOptions,
  stubProfileSurface,
  type GateStub,
} from '@/test-support/onboardingRouter';
import { fakeInstallReferrer } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useHeldLinkStore } from '../store/heldLink.store';

import { readTheInstallReferrerOnce } from './installReferrerLink';

const CODE = 'tk4m9q2z';
/** Tomek's link as the app spells it while no web domain is set — the app's own scheme. */
const LINK = `raketa://f/${CODE}`;
const OPENING = `/api/v1/friends/links/${CODE}/opening`;
const TOMEK = { id: 'e0000000-0000-4000-8000-000000000101', name: 'tomek.k' };

/** Ania: rated at padel and past onboarding — in the app the moment she opens it. */
const ANIA: GateStub = { ratings: [rating('PADEL')], hasPlayerProfile: true };

let transport: Transport;

/** Tomek's request, as Home carries one made by his link. */
const tomeksRequest: Wire['HomeFriendRequestSchema'] = {
  player_id: TOMEK.id,
  nickname: TOMEK.name,
  photo_id: null,
  photo_url: null,
  asked_at: '2026-10-01T07:59:00Z',
  by_link: true,
  from_ranking: false,
  from_new_players: false,
  from_same_level: false,
  group: null,
  sport: null,
  level: null,
  player_score: 96,
  reliability_band: 'VERY_HIGH',
  percent_even: null,
};

/**
 * **Tomek's link, on the server** — opening it answers `relation`, and an `ASKED_YOU` puts his
 * request on Home, as the opening does. A refusal answers its code instead.
 */
function serveTheLink(answer: Wire['FriendRelation'] | { readonly refused: [number, string] }) {
  transport.on('POST', OPENING, () => {
    if (typeof answer === 'object') return errorResponse(answer.refused[0], answer.refused[1]);
    if (answer === 'ASKED_YOU') stubHome(transport, { friend_requests: [tomeksRequest] });
    return json<Wire['OpenedFriendLinkResponse']>({ relation: answer });
  });
}

function serve(account: GateStub) {
  stubGate(transport, account);
  stubProfileOptions(transport);
  stubProfileSurface(transport);
}

const openings = () => transport.requestsTo('POST', OPENING).length;
const toasts = () => useToastQueue.getState().queue.map((toast) => toast.message);

/** Home, with Tomek's request on top: *tomek.k wants to be your friend · Invited you to Raketa*. */
async function expectTomeksRequestOnHome() {
  await waitFor(() => expect(screen).toHavePathname('/'));
  const card = within(await screen.findByTestId(`friend-request-${TOMEK.id}`));
  expect(card.getByText(wantsToBeYourFriend(TOMEK.name))).toBeTruthy();
  expect(card.getByText(FRIENDS_COPY.home.byLink)).toBeTruthy();
}

/** Ania, signed in and on her You tab — anywhere but Home. */
async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  await waitFor(() => expect(screen).toHavePathname('/you'));
}

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
  resetLocation();
  queryClient.clear();
  resetSessionStatus();
  useToastQueue.setState({ queue: [] });
  useHeldLinkStore.getState().reset();
  await clearStoredTokens();
});

describe('a friend link, on a phone that is signed in', () => {
  it('opens it and lands on Home, the request on top', async () => {
    serve(ANIA);
    serveTheLink('ASKED_YOU');
    await onYou();
    const bellReads = transport.requestsTo('GET', NOTICES_PATH).length;

    openLink(`raketa://f/${CODE.toUpperCase()}?utm_source=whatsapp`);

    await expectTomeksRequestOnHome();
    // Opened once, by the code the link was read with, and the bell read again for its notice.
    expect(openings()).toBe(1);
    expect(transport.requestsTo('GET', NOTICES_PATH).length).toBeGreaterThan(bellReads);
    expect(useHeldLinkStore.getState().link).toBeNull();
  });

  it('opens it from a cold start by the link', async () => {
    serve(ANIA);
    serveTheLink('ASKED_YOU');

    await launchByLink(`/f/${CODE}`, { signedIn: true });

    await expectTomeksRequestOnHome();
    expect(openings()).toBe(1);
  });

  /** Her own link, or one of a friend's — or her own request crossing his: nothing to answer. */
  it.each(['NONE', 'FRIEND'] as const)('moves nobody when it answers %s', async (relation) => {
    serve(ANIA);
    serveTheLink(relation);
    await onYou();

    openLink(LINK);

    await waitFor(() => expect(openings()).toBe(1));
    await waitFor(() => expect(useHeldLinkStore.getState().link).toBeNull());
    expect(screen).toHavePathname('/you');
    expect(toasts()).toEqual([]);
  });

  it('says a dead link is nothing, and moves nobody', async () => {
    serve(ANIA);
    serveTheLink({ refused: [404, 'friend_link_not_found'] });
    await onYou();

    openLink(LINK);

    await waitFor(() => expect(toasts()).toEqual([FRIENDS_COPY.linkRefused.friend_link_not_found]));
    expect(screen).toHavePathname('/you');
    expect(useHeldLinkStore.getState().link).toBeNull();
  });

  it('says how to see the request of somebody she blocked', async () => {
    serve(ANIA);
    serveTheLink({ refused: [409, 'unblock_them_first'] });
    await onYou();

    openLink(LINK);

    await waitFor(() => expect(toasts()).toEqual([FRIENDS_COPY.linkRefused.unblock_them_first]));
    expect(screen).toHavePathname('/you');
  });

  it.each(['raketa://f/tk4m', 'raketa://f/tk4m-9q2', 'https://evil.example/f/tk4m9q2z'])(
    'reads nothing out of a link that cannot be one: %p',
    async (url) => {
      serve(ANIA);
      serveTheLink('ASKED_YOU');
      await onYou();

      openLink(url);

      expect(screen).toHavePathname('/you');
      expect(openings()).toBe(0);
    },
  );
});

describe('a friend link, before the account is in the app', () => {
  /**
   * **Zofia's walk, whole** — she opened Tomek's link before she had an account: she signs up, names
   * herself, answers the profile steps, and lands on Home with his request on top. Nothing is opened
   * on the way: the link is opened as the account, once the account is in the app.
   */
  it('is kept through sign-up, the naming and the profile steps, then lands on Home', async () => {
    serve({ email: 'zofia@example.com', nickname: null });
    serveTheLink('ASKED_YOU');

    await launchByLink(`/f/${CODE}`, { signedIn: false });
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));

    await walkANewAccountToFinish(transport, { email: 'zofia@example.com', nickname: 'zofia.b' });
    expect(openings()).toBe(0);

    fireEvent.press(screen.getByLabelText('Finish'));

    await expectTomeksRequestOnHome();
    expect(openings()).toBe(1);
  });
});

describe('a friend link, in the administrator area', () => {
  /** An administrator who plays is switched to Player, and the player's app opens it. */
  it('switches an account that also plays to Player, and lands on Home', async () => {
    serve({
      ...ANIA,
      profiles: {
        acts_as_player: true,
        administers: [{ club_id: CLUB_ID, club_name: CLUB.name }],
        pending_invitations: [],
        handovers: [],
      },
    });
    serveTheLink('ASKED_YOU');
    club().install(transport);
    await savePhonePreference(GATE_USER.id, 'lastProfile', `administrator:${CLUB_ID}`);
    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));

    openLink(LINK);

    await expectTomeksRequestOnHome();
    expect(openings()).toBe(1);
  });
});

/**
 * **The install referrer** (the mechanics §4.3) — what the launch's own step does on an Android
 * phone's first launch, before the tree renders: the link the store button carried is held as if it
 * had been tapped.
 */
describe('a friend link carried through an Android install', () => {
  it('is opened on the first launch and lands on Home, and is never read again', async () => {
    serve(ANIA);
    serveTheLink('ASKED_YOU');
    const play = fakeInstallReferrer(`https://raketa.app/f/${CODE}`);

    await readTheInstallReferrerOnce(play);
    await launchSignedIn();

    await expectTomeksRequestOnHome();
    expect(openings()).toBe(1);

    // The next launch reads nothing, and opens nothing.
    await readTheInstallReferrerOnce(play);
    expect(play.reads).toBe(1);
    expect(useHeldLinkStore.getState().link).toBeNull();
    expect(openings()).toBe(1);
  });

  it('opens nothing for an install that carried no link', async () => {
    serve(ANIA);
    serveTheLink('ASKED_YOU');

    await readTheInstallReferrerOnce(
      fakeInstallReferrer('utm_source=google-play&utm_medium=organic'),
    );
    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(openings()).toBe(0);
    expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(0);
  });
});

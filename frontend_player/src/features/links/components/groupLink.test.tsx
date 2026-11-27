/**
 * **A group link, opened on a phone** — Kuba taps one in WhatsApp and the app opens on Join a group
 * with that group already there; Kasia opened the same link before she had an account, and lands on
 * it once she has signed up and been rated ([#520](https://github.com/Raketa02/Raketa/issues/520),
 * PRD #500 stories 46 and 48).
 *
 * Driven through the real route tree **with the app's link reader in front of it**
 * (`src/app/+native-intent`), so every link here passes the gate a real one passes. Only `fetch` is
 * faked. A cold start is a launch *by* the link; a link opened while the app runs goes through
 * `openLink`, which does what expo-router's listener does with the reader's answer.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ADMINISTRATOR_ONLY,
  CLUB,
  CLUB_ID,
  club,
  rating,
} from '@/test-support/officialGroupsServer';
import {
  GATE_USER,
  HOME_TAB_LINE,
  launchByLink,
  launchSignedIn,
  openLink,
  resetLocation,
  stubGate,
  stubProfileOptions,
  stubProfileSurface,
  type GateStub,
} from '@/test-support/onboardingRouter';
import { walkANewAccountToFinish } from '@/test-support/newAccountWalk';
import { fakeInstallReferrer } from '@/test-support/platform';
import {
  installTransport,
  json,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useHeldLinkStore } from '../store/heldLink.store';

import { readTheInstallReferrerOnce } from './installReferrerLink';

const COPY = GROUPS_COPY.joinGroup;

const CODE = 'k7pq2mxa';
/** The group link as the app spells it while no web domain is set — the app's own scheme. */
const LINK = `rakieta://join/${CODE}`;
const JOIN_SEARCH = '/api/v1/join-search';

const O3_CLUB: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000001',
  kind: 'PLAYER',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 11,
  join_policy: 'ANYONE',
  owner_nickname: 'Coach Andrzej',
  administrator_nickname: null,
  is_administrator: false,
  relation: 'NONE',
};

const OGRODY: Wire['ClubCardSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000003',
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  distance_km: 2.4,
  sports: ['TENNIS', 'PADEL'],
  groups: [O3_CLUB],
};

/** Kuba: rated at padel and past onboarding — in the app the moment he opens it. */
const KUBA: GateStub = { ratings: [rating('PADEL')], hasPlayerProfile: true };

let transport: Transport;

const searched = () =>
  transport
    .requestsTo('GET', JOIN_SEARCH)
    .map((request) => new URLSearchParams(request.path.split('?')[1] ?? '').get('q'));

/** Join search as the server answers it: the link finds exactly its group, anything else nothing. */
function stubJoinSearch() {
  transport.on('GET', JOIN_SEARCH, (request: RecordedRequest) => {
    const q = new URLSearchParams(request.path.split('?')[1] ?? '').get('q') ?? '';
    return json<Wire['JoinSearchResponse']>(
      q.includes(`/join/${CODE}`)
        ? { clubs: [OGRODY], next_page: null, read_as: 'LINK' }
        : { clubs: [], next_page: null, read_as: 'TEXT' },
    );
  });
}

function serve(account: GateStub) {
  stubGate(transport, account);
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubJoinSearch();
}

/** Join a group, with the link in its field and the group found under it. */
async function expectTheGroupOnJoin() {
  await waitFor(() => expect(screen).toHavePathname('/play/join'));
  expect(screen.getByLabelText(COPY.field).props.value).toBe(LINK);
  expect(await screen.findByText(O3_CLUB.name)).toBeTruthy();
  expect(searched()).toContain(LINK);
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
  useHeldLinkStore.getState().reset();
  await clearStoredTokens();
});

describe('a group link, on a phone that is signed in', () => {
  it('opens Join a group with the link filled in and its group found', async () => {
    serve(KUBA);

    await launchByLink(`/join/${CODE.toUpperCase()}`, { signedIn: true });

    await expectTheGroupOnJoin();
    // One tap from joining: the field holds the link, so the keyboard is not asked for.
    expect(screen.getByLabelText(COPY.field).props.autoFocus).toBe(false);
  });

  it('lays Play › Groups beneath it, so back is the Groups list', async () => {
    serve(KUBA);
    await launchByLink(`/join/${CODE}`, { signedIn: true });
    await expectTheGroupOnJoin();

    fireEvent.press(screen.getByLabelText(COPY.back));

    await waitFor(() => expect(screen).toHavePathname('/play'));
  });

  it('opens it from a link tapped while the app is open, keeping nothing but the code', async () => {
    serve(KUBA);
    await launchSignedIn();
    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();

    openLink(`${LINK}?utm_source=whatsapp&api=https://evil.example`);

    await expectTheGroupOnJoin();
    // Nothing the link carried reached the wire but the code: every request went to the
    // configured hosts, and the search was for the link the app spelled itself.
    expect(searched()).toEqual([LINK]);
    for (const request of transport.requests) {
      expect(request.url).toMatch(/^https:\/\/(api|features)\.test\.raketa\.invalid\//);
    }
  });
});

describe('a link the app cannot read', () => {
  it('is ignored at a launch: the app opens where it would have', async () => {
    serve(KUBA);

    await launchByLink('/join/k7pq', { signedIn: true });

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(searched()).toEqual([]);
  });

  it.each(['rakieta://join/k7pq-2mx', 'rakieta://play/join', 'https://evil.example/join/k7pq2mxa'])(
    'is ignored while the app is open, and nothing moves: %p',
    async (url) => {
      serve(KUBA);
      await launchSignedIn();
      expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();

      openLink(url);

      expect(screen).toHavePathname('/');
      expect(screen.getByText(HOME_TAB_LINE)).toBeTruthy();
      expect(searched()).toEqual([]);
    },
  );
});

describe('a group link, before the account is in the app', () => {
  it('is kept through sign-in, and opened once signed in', async () => {
    serve(KUBA);
    transport.on('POST', '/api/v1/auth/login', () =>
      json<Wire['TokenResponse']>({
        access_token: 'access-1',
        refresh_token: 'refresh-1',
        token_type: 'bearer',
        expires_in: 900,
      }),
    );

    await launchByLink(`/join/${CODE}`, { signedIn: false });
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(searched()).toEqual([]);

    fireEvent.changeText(screen.getByLabelText('Email'), GATE_USER.email);
    fireEvent.changeText(screen.getByLabelText('Password'), 'correct horse');
    fireEvent.press(screen.getByLabelText('Sign in'));

    await expectTheGroupOnJoin();
  });

  /**
   * **Kasia's walk, whole** — the ticket's second sentence. She opened the link before she had an
   * account: she signs up, names herself, answers the profile steps, and lands on the group — with
   * no questionnaire on the way, since a level is asked where play begins (ADR-0200 §1, #730). Each
   * screen of it is its own suite's; what this proves is that the link outlives every one of them
   * and waits for the last.
   */
  it('is kept through sign-up, the naming and the profile steps', async () => {
    // A new account: unnamed, unrated, with no Player profile.
    serve({ email: 'kasia@example.com', nickname: null });

    // The link, before there is an account.
    await launchByLink(`/join/${CODE}`, { signedIn: false });
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));

    await walkANewAccountToFinish(transport, { email: 'kasia@example.com', nickname: 'kasia' });

    // Nothing was searched for on the way: the link waited.
    expect(searched()).toEqual([]);

    // *Finish* is the way into the app, and the link is answered there.
    fireEvent.press(screen.getByLabelText('Finish'));

    await expectTheGroupOnJoin();
  });
});

describe('a group link, in the administrator area', () => {
  const OGRODY_ADMIN: Wire['AdministeredClubSchema'] = { club_id: CLUB_ID, club_name: CLUB.name };

  /** Tomek plays padel and runs Ogrody 33's groups, and wore his administrator profile last. */
  it('switches an account that also plays to Player, and opens it there', async () => {
    serve({
      ...KUBA,
      profiles: {
        acts_as_player: true,
        administers: [OGRODY_ADMIN],
        pending_invitations: [],
        handovers: [],
      },
    });
    club().install(transport);
    await savePhonePreference(GATE_USER.id, 'lastProfile', `administrator:${CLUB_ID}`);
    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));

    openLink(LINK);

    await expectTheGroupOnJoin();
  });

  /**
   * Marta only runs the club's groups: Join a group is not hers until she starts playing, so the
   * link waits — *Start playing*'s steps end in the player's app, where it is opened like Kasia's.
   */
  it('takes an account that does not play nowhere', async () => {
    serve({ nickname: null, profiles: ADMINISTRATOR_ONLY });
    club().install(transport);
    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));

    openLink(LINK);

    expect(screen).toHavePathname(`/administrator/${CLUB_ID}`);
    expect(searched()).toEqual([]);
  });
});

/**
 * **A group link carried through an Android install** (#756, the friends mechanics §4.3: *this holds
 * for group links too*) — the public site's group page carries its link on the Google Play button,
 * and the first launch opens it as if it had been tapped.
 */
describe('a group link carried through an Android install', () => {
  it('opens Join a group on the first launch, its group found', async () => {
    serve(KUBA);

    await readTheInstallReferrerOnce(fakeInstallReferrer(`https://raketa.app/join/${CODE}`));
    await launchSignedIn();

    await expectTheGroupOnJoin();
  });
});

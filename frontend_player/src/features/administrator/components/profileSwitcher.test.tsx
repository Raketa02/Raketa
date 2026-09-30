/**
 * **The profile switcher, walked** — the chip on each profile's You tab, the sheet it opens, the
 * switch, and the phone remembering which profile an account wore last
 * ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories 134, 135 and 138; club
 * mocks 6–7; ADR-0185 §3, ADR-0188 §2).
 *
 * The real route tree, with only the socket faked. The club's administrator routes are answered by
 * the small fake of the server (`club`). *A relaunch* is the process ending and a new one starting:
 * the Query cache and the session go, and what is saved on the device — the keychain, and the
 * phone's preferences — stays.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ADMINISTRATOR_ONLY,
  CLUB,
  CLUB_ID,
  club,
  O3_CLUB_GROUP,
  rating,
} from '@/test-support/officialGroupsServer';
import {
  GATE_USER,
  HOME_TAB_LINE,
  PLAYER_ONLY,
  launchSignedIn,
  stubGate,
  stubInterest,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
  type GateStub,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { ADMINISTRATOR_COPY } from './administratorCopy';

const COPY = ADMINISTRATOR_COPY.switcher;

/** A second club, for the person who runs two. */
const BONARKA_ID = 'c0000000-0000-4000-8000-000000000044';
const OGRODY: Wire['AdministeredClubSchema'] = { club_id: CLUB_ID, club_name: CLUB.name };
const BONARKA: Wire['AdministeredClubSchema'] = {
  club_id: BONARKA_ID,
  club_name: 'Bonarka Arena',
};

/** Tomek plays padel, is past onboarding, and runs Ogrody 33's padel WhatsApp group. */
const TOMEK: GateStub = {
  name: 'Tomek Kowal',
  ratings: [rating('PADEL')],
  hasPlayerProfile: true,
  profiles: { acts_as_player: true, administers: [OGRODY], pending_invitations: [] },
};

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Serve this account, the player's You tab and the club's routes — both clubs', empty. */
function serve(account: GateStub) {
  stubGate(transport, account);
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
  club([O3_CLUB_GROUP]).install(transport);
  transport.on('GET', `/api/v1/administrator/clubs/${BONARKA_ID}/groups`, () =>
    json<Wire['AdministeredGroupsResponse']>({
      club: { id: BONARKA_ID, name: 'Bonarka Arena', sports: ['PADEL'] },
      groups: [],
    }),
  );
}

async function relaunch(initialUrl = '/') {
  screen.unmount();
  queryClient.clear();
  resetSessionStatus();
  await launchSignedIn(initialUrl);
}

const chip = () => screen.queryByRole('button', { name: new RegExp(`^${COPY.chip}`) });

async function openPlayerYou() {
  fireEvent.press(await screen.findByLabelText('You'));
  await waitFor(() => expect(screen).toHavePathname('/you'));
}

async function openAdministratorYou(clubId = CLUB_ID) {
  fireEvent.press(await screen.findByRole('tab', { name: 'You' }));
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${clubId}/you`));
}

async function openTheSheet() {
  fireEvent.press((await waitFor(() => chip())) as NonNullable<ReturnType<typeof chip>>);
  expect(await screen.findByRole('header', { name: COPY.title })).toBeTruthy();
}

const row = (name: string, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

async function expectPlayerApp() {
  expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
  expect(screen).toHavePathname('/');
}

async function expectTheArea(clubId = CLUB_ID) {
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${clubId}`));
  expect(await screen.findByRole('header', { name: ADMINISTRATOR_COPY.groups.title })).toBeTruthy();
}

describe('the chip', () => {
  it('is not drawn for an account that only plays', async () => {
    serve({ ...TOMEK, profiles: PLAYER_ONLY });
    await launchSignedIn();

    await openPlayerYou();

    expect(await screen.findByRole('header', { name: 'You' })).toBeTruthy();
    expect(chip()).toBeNull();
  });

  it('is not drawn for an account that runs one club and does not play', async () => {
    serve({ name: 'Marta Nowak', nickname: null, profiles: ADMINISTRATOR_ONLY });
    await launchSignedIn();
    await expectTheArea();

    await openAdministratorYou();

    expect(await screen.findByRole('header', { name: 'Marta Nowak' })).toBeTruthy();
    expect(chip()).toBeNull();
  });

  it('sits on the player You tab of an account with two, and lists both with Player ticked', async () => {
    serve(TOMEK);
    await launchSignedIn();
    await openPlayerYou();

    await openTheSheet();

    expect(await row('Tomek Kowal, Player', true)).toBeTruthy();
    expect(await row('Ogrody 33, Administrator', false)).toBeTruthy();
  });

  it('sits on the administrator You tab too, with the club ticked', async () => {
    serve(TOMEK);
    await launchSignedIn(`/administrator/${CLUB_ID}`);
    await expectTheArea();
    await openAdministratorYou();

    await openTheSheet();

    expect(await row('Ogrody 33, Administrator', true)).toBeTruthy();
    expect(await row('Tomek Kowal, Player', false)).toBeTruthy();
  });
});

describe('switching', () => {
  it('goes to the administrator profile at once, with no password', async () => {
    serve(TOMEK);
    await launchSignedIn();
    await openPlayerYou();
    await openTheSheet();
    const before = transport.requestsTo('POST', '/api/v1/auth/login').length;

    fireEvent.press(await row('Ogrody 33, Administrator'));

    await expectTheArea();
    expect(transport.requestsTo('POST', '/api/v1/auth/login')).toHaveLength(before);
  });

  it('goes back to Player from the administrator You tab', async () => {
    serve(TOMEK);
    await launchSignedIn(`/administrator/${CLUB_ID}`);
    await openAdministratorYou();
    await openTheSheet();

    fireEvent.press(await row('Tomek Kowal, Player'));

    await expectPlayerApp();
  });

  it('closes on the profile already worn, and goes nowhere', async () => {
    serve(TOMEK);
    await launchSignedIn();
    await openPlayerYou();
    await openTheSheet();

    fireEvent.press(await row('Tomek Kowal, Player'));

    await waitFor(() => expect(screen.queryByRole('header', { name: COPY.title })).toBeNull());
    expect(screen).toHavePathname('/you');
  });

  it('moves between two clubs for an account that runs both', async () => {
    serve({
      name: 'Marta Nowak',
      nickname: null,
      profiles: { acts_as_player: false, administers: [OGRODY, BONARKA], pending_invitations: [] },
    });
    await launchSignedIn();
    await expectTheArea();
    await openAdministratorYou();
    await openTheSheet();

    // One administrator profile per club, and no Player: she does not play.
    expect(await row('Ogrody 33, Administrator', true)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /, Player$/ })).toBeNull();
    fireEvent.press(await row('Bonarka Arena, Administrator', false));

    await expectTheArea(BONARKA_ID);
  });
});

describe('the profile the phone remembers', () => {
  it('opens an account with two in Player until another is chosen', async () => {
    serve(TOMEK);

    await launchSignedIn();

    await expectPlayerApp();
  });

  it('reopens in the administrator profile after the app is closed', async () => {
    serve(TOMEK);
    await launchSignedIn();
    await openPlayerYou();
    await openTheSheet();
    fireEvent.press(await row('Ogrody 33, Administrator'));
    await expectTheArea();

    await relaunch();

    await expectTheArea();
  });

  it('reopens in Player once Player is chosen again', async () => {
    serve(TOMEK);
    await savePhonePreference(GATE_USER.id, 'lastProfile', `administrator:${CLUB_ID}`);
    await launchSignedIn();
    await expectTheArea();
    await openAdministratorYou();
    await openTheSheet();
    fireEvent.press(await row('Tomek Kowal, Player'));
    await expectPlayerApp();

    await relaunch();

    await expectPlayerApp();
  });

  it('reopens an account running two clubs in the club it wore last', async () => {
    serve({
      name: 'Marta Nowak',
      nickname: null,
      profiles: { acts_as_player: false, administers: [OGRODY, BONARKA], pending_invitations: [] },
    });
    await savePhonePreference(GATE_USER.id, 'lastProfile', `administrator:${BONARKA_ID}`);

    await launchSignedIn();

    await expectTheArea(BONARKA_ID);
  });

  it('opens in Player when the club it wore last no longer has it', async () => {
    serve({ ...TOMEK, profiles: PLAYER_ONLY });
    await savePhonePreference(GATE_USER.id, 'lastProfile', `administrator:${CLUB_ID}`);

    await launchSignedIn();

    await expectPlayerApp();
  });

  it('is forgotten at sign-out', async () => {
    serve(TOMEK);
    await savePhonePreference(GATE_USER.id, 'lastProfile', `administrator:${CLUB_ID}`);
    await launchSignedIn();
    await expectTheArea();
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );
    await openAdministratorYou();

    fireEvent.press(await screen.findByRole('button', { name: 'Sign out' }));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    await expect(readPhonePreference(GATE_USER.id, 'lastProfile')).resolves.toBeUndefined();
  });
});

describe('removed, for an account with two', () => {
  /**
   * The club removes Tomek while his administrator profile is the one he wore: he is told, moved to
   * Player, and — because the switch is kept — the next launch opens in Player too.
   */
  it('is told, switched to Player, and reopens in Player', async () => {
    serve(TOMEK);
    const server = club([O3_CLUB_GROUP]);
    server.install(transport);
    await savePhonePreference(GATE_USER.id, 'lastProfile', `administrator:${CLUB_ID}`);
    await launchSignedIn();
    await expectTheArea();
    server.remove();

    await act(async () => {
      await queryClient.refetchQueries();
    });

    await expectPlayerApp();
    expect(useToastQueue.getState().queue.map((toast) => toast.message)).toEqual([
      'Ogrody 33 removed you as an administrator.',
    ]);
    await expect(readPhonePreference(GATE_USER.id, 'lastProfile')).resolves.toBe('player');

    stubGate(transport, { ...TOMEK, profiles: PLAYER_ONLY });
    await relaunch();

    await expectPlayerApp();
  });
});

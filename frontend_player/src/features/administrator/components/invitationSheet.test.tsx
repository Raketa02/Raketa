/**
 * **The invitation sheet, walked** — an existing player the club invited, offered the administrator
 * profile on launch ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories
 * 117–119; club mocks 5–6; ADR-0184 §2, ADR-0185 §3).
 *
 * The real route tree, with only the socket faked. *A relaunch* is the process ending and a new one
 * starting: the Query cache, the session and what was set aside for this launch go; the keychain
 * and the phone's preferences stay.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { CLUB, CLUB_ID, club, O3_CLUB_GROUP, rating } from '@/test-support/officialGroupsServer';
import {
  HOME_TAB_LINE,
  launchSignedIn,
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

import { useInvitationsSetAside } from '../store/invitationsSetAside.store';

import { ADMINISTRATOR_COPY } from './administratorCopy';

const COPY = ADMINISTRATOR_COPY.invitation;

const ADMINISTRATOR_ID = 'd0000000-0000-4000-8000-000000000001';
const ACCEPT_PATH = `/api/v1/invitations/${ADMINISTRATOR_ID}/acceptance`;
const OGRODY: Wire['AdministeredClubSchema'] = { club_id: CLUB_ID, club_name: CLUB.name };

const INVITATION: Wire['PendingInvitationSchema'] = {
  administrator_id: ADMINISTRATOR_ID,
  club_id: CLUB_ID,
  club_name: CLUB.name,
  expires_at: '2026-09-29T12:00:00Z',
};

/** Tomek plays padel and is past onboarding; Ogrody 33 has invited him. */
function tomek(pending: readonly Wire['PendingInvitationSchema'][] = [INVITATION]): GateStub {
  return {
    name: 'Tomek Kowal',
    ratings: [rating('PADEL')],
    hasPlayerProfile: true,
    profiles: {
      acts_as_player: true,
      administers: [],
      pending_invitations: [...pending],
      handovers: [],
    },
  };
}

const TITLE = 'Ogrody 33 wants to make you an administrator';

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
  useInvitationsSetAside.getState().reset();
  serve(tomek());
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  useInvitationsSetAside.getState().reset();
  await clearStoredTokens();
});

function serve(account: GateStub) {
  stubGate(transport, account);
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
  club([O3_CLUB_GROUP]).install(transport);
}

/** The server's answer to Accept: the account's profiles, the club's now among them. */
function stubAccept() {
  transport.on('POST', ACCEPT_PATH, () =>
    json<Wire['AccountProfilesSchema']>({
      acts_as_player: true,
      administers: [OGRODY],
      pending_invitations: [],
      handovers: [],
    }),
  );
}

async function relaunch() {
  screen.unmount();
  queryClient.clear();
  resetSessionStatus();
  useInvitationsSetAside.getState().reset();
  await launchSignedIn();
}

const theSheet = () => screen.queryByRole('header', { name: TITLE });

async function expectTheSheet() {
  expect(await screen.findByRole('header', { name: TITLE })).toBeTruthy();
}

async function expectNoSheet() {
  expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
  expect(theSheet()).toBeNull();
}

describe('the invitation sheet', () => {
  it('shows on launch when the club has invited the account', async () => {
    await launchSignedIn();

    await expectTheSheet();
    expect(
      screen.getByText(
        'It becomes a second profile on this account, next to your player profile. You switch between them from You.',
      ),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.accept })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.notNow })).toBeTruthy();
  });

  it('is not shown to an account nobody has invited', async () => {
    serve(tomek([]));

    await launchSignedIn();

    await expectNoSheet();
  });

  /** Accept adds the profile, and the sheet becomes the profile list (club 6), Player ticked. */
  it('adds the administrator profile on Accept, and confirms with the profile list', async () => {
    stubAccept();
    await launchSignedIn();
    await expectTheSheet();

    fireEvent.press(screen.getByRole('button', { name: COPY.accept }));

    expect(
      await screen.findByRole('header', { name: ADMINISTRATOR_COPY.switcher.title }),
    ).toBeTruthy();
    expect(transport.requestsTo('POST', ACCEPT_PATH)).toHaveLength(1);
    expect(
      screen.getByRole('button', { name: 'Tomek Kowal, Player', selected: true }),
    ).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Ogrody 33, Administrator', selected: false }),
    ).toBeTruthy();
  });

  it('switches into the new profile from the list', async () => {
    stubAccept();
    await launchSignedIn();
    await expectTheSheet();
    fireEvent.press(screen.getByRole('button', { name: COPY.accept }));

    fireEvent.press(await screen.findByRole('button', { name: 'Ogrody 33, Administrator' }));

    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
  });

  it('leaves the account where it is when the list is closed', async () => {
    stubAccept();
    await launchSignedIn();
    await expectTheSheet();
    fireEvent.press(screen.getByRole('button', { name: COPY.accept }));
    await screen.findByRole('header', { name: ADMINISTRATOR_COPY.switcher.title });

    fireEvent.press(screen.getByRole('button', { name: ADMINISTRATOR_COPY.switcher.close }));

    await waitFor(() =>
      expect(screen.queryByRole('header', { name: ADMINISTRATOR_COPY.switcher.title })).toBeNull(),
    );
    expect(screen).toHavePathname('/');
    // Accepted, so it is not offered again.
    expect(theSheet()).toBeNull();
  });
});

describe('Not now', () => {
  it('hides the sheet for the rest of this launch', async () => {
    await launchSignedIn();
    await expectTheSheet();

    fireEvent.press(screen.getByRole('button', { name: COPY.notNow }));

    await waitFor(() => expect(theSheet()).toBeNull());
    // Nothing was accepted, and moving about the app does not bring it back.
    fireEvent.press(screen.getByLabelText('You'));
    await waitFor(() => expect(screen).toHavePathname('/you'));
    fireEvent.press(screen.getByLabelText('Home'));
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(theSheet()).toBeNull();
    expect(transport.requestsTo('POST', ACCEPT_PATH)).toHaveLength(0);
  });

  it('is what the close control does too', async () => {
    await launchSignedIn();
    await expectTheSheet();

    fireEvent.press(screen.getByRole('button', { name: COPY.close }));

    await waitFor(() => expect(theSheet()).toBeNull());
    expect(transport.requestsTo('POST', ACCEPT_PATH)).toHaveLength(0);
  });

  it('brings the sheet back at the next launch', async () => {
    await launchSignedIn();
    await expectTheSheet();
    fireEvent.press(screen.getByRole('button', { name: COPY.notNow }));
    await waitFor(() => expect(theSheet()).toBeNull());

    await relaunch();

    await expectTheSheet();
  });

  /** The server stops listing it past its 72 hours, and a launch after that offers nothing. */
  it('stops bringing it back once the invitation has expired', async () => {
    await launchSignedIn();
    await expectTheSheet();
    fireEvent.press(screen.getByRole('button', { name: COPY.notNow }));
    await waitFor(() => expect(theSheet()).toBeNull());

    serve(tomek([]));
    await relaunch();

    await expectNoSheet();
  });
});

describe('an invitation that ran out while the sheet was up', () => {
  it('says so, in words that say who to ask, and offers nothing to accept', async () => {
    transport.on('POST', ACCEPT_PATH, () => errorResponse(409, 'invitation_expired'));
    await launchSignedIn();
    await expectTheSheet();

    fireEvent.press(screen.getByRole('button', { name: COPY.accept }));

    expect(
      await screen.findByText('This invitation has expired. Ask Ogrody 33 to send a new one.'),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: COPY.accept })).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: COPY.done }));
    await waitFor(() => expect(theSheet()).toBeNull());
  });

  it('keeps Accept when the server could not be reached, to press again', async () => {
    transport.on('POST', ACCEPT_PATH, () => errorResponse(503, 'service_unavailable'));
    await launchSignedIn();
    await expectTheSheet();

    fireEvent.press(screen.getByRole('button', { name: COPY.accept }));

    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.accept })).toBeTruthy();
  });
});

describe('an administrator another club invites', () => {
  /** Marta runs Bonarka's groups and does not play; Ogrody 33 invites her as well. */
  it('offers it over the administrator area, next to the profile she has', async () => {
    const BONARKA_ID = 'c0000000-0000-4000-8000-000000000044';
    serve({
      name: 'Marta Nowak',
      nickname: null,
      profiles: {
        acts_as_player: false,
        administers: [{ club_id: BONARKA_ID, club_name: 'Bonarka Arena' }],
        pending_invitations: [INVITATION],
        handovers: [],
      },
    });
    transport.on('GET', `/api/v1/administrator/clubs/${BONARKA_ID}/groups`, () =>
      json<Wire['AdministeredGroupsResponse']>({
        club: { id: BONARKA_ID, name: 'Bonarka Arena', sports: ['PADEL'] },
        groups: [],
      }),
    );

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/administrator/${BONARKA_ID}`));
    await expectTheSheet();
    expect(
      screen.getByText(
        'It becomes a second profile on this account, next to Bonarka Arena. You switch between them from You.',
      ),
    ).toBeTruthy();
  });
});

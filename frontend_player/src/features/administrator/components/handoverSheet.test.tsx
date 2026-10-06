/**
 * **The handover sheet, walked** — a club handing an official group to an administrator, who is
 * told so once, wherever they are in the app, and without sending it away and back
 * ([ADR-0192](../../../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md),
 * #529 N5–N7).
 *
 * The real route tree, with only the socket faked. `/users/me` is served from what the server knows
 * *now* (`handed`), and the sheet's *seen* takes the groups it names out of it, as the backend does.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ADMINISTRATOR_ONLY,
  CLUB,
  CLUB_ID,
  CLUB_PATH,
  club,
  NOW,
  O3_CLUB_GROUP,
  O3_CLUB_ID,
  OPEN_PLAY_GROUP,
  OPEN_PLAY_ID,
  rating,
} from '@/test-support/officialGroupsServer';
import {
  GATE_USER,
  HOME_TAB_LINE,
  launchSignedIn,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
  type GateStub,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useHandoversClosed } from '../store/handoversClosed.store';
import { useInvitationsSetAside } from '../store/invitationsSetAside.store';

import { ADMINISTRATOR_COPY } from './administratorCopy';

const COPY = ADMINISTRATOR_COPY.handover;
const SEEN_PATH = `${CLUB_PATH}/handovers/seen`;
const OGRODY: Wire['AdministeredClubSchema'] = { club_id: CLUB_ID, club_name: CLUB.name };

function handover(group: { id: string; name: string }, waiting = 0): Wire['HandoverSchema'] {
  return {
    club_id: CLUB_ID,
    club_name: CLUB.name,
    group_id: group.id,
    group_name: group.name,
    waiting_count: waiting,
  };
}

const O3_HANDED = handover({ id: O3_CLUB_ID, name: 'Ogrody 33 Club' }, 2);
const OPEN_PLAY_HANDED = handover({ id: OPEN_PLAY_ID, name: 'Ogrody open play' });
const O3_TITLE = 'Ogrody 33 made you the administrator of Ogrody 33 Club';

/** Marta runs Ogrody 33's groups and does not play. */
const MARTA: GateStub = { name: 'Marta Nowak', nickname: null, profiles: ADMINISTRATOR_ONLY };

/** Tomek plays padel and runs Ogrody 33's groups too. */
const TOMEK: GateStub = {
  name: 'Tomek Kowal',
  ratings: [rating('PADEL')],
  hasPlayerProfile: true,
  profiles: { acts_as_player: true, administers: [OGRODY], pending_invitations: [], handovers: [] },
};

let transport: Transport;
/** What the server says the account was handed and has not been told about — *now*. */
let handed: Wire['HandoverSchema'][];
let pending: Wire['PendingInvitationSchema'][];

beforeEach(() => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
  useHandoversClosed.getState().reset();
  useInvitationsSetAside.getState().reset();
  handed = [];
  pending = [];
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  useHandoversClosed.getState().reset();
  useInvitationsSetAside.getState().reset();
  await clearStoredTokens();
});

/** The account, and a `/users/me` that answers what the server knows at the moment it is asked. */
function serve(account: GateStub) {
  stubGate(transport, account);
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
  club([O3_CLUB_GROUP, OPEN_PLAY_GROUP]).install(transport);
  const profiles = account.profiles ?? ADMINISTRATOR_ONLY;
  transport.on('GET', '/api/v1/users/me', () =>
    json<Wire['MeResponse']>({
      ...GATE_USER,
      name: account.name ?? null,
      nickname: account.nickname === undefined ? 'tomek' : account.nickname,
      has_player_profile: account.hasPlayerProfile ?? false,
      adult_attested: profiles.acts_as_player,
      profiles: { ...profiles, pending_invitations: [...pending], handovers: [...handed] },
    }),
  );
  transport.on('POST', SEEN_PATH, (request) => {
    const told = (request.body as Wire['HandoversSeenRequest']).group_ids;
    handed = handed.filter((handover_) => !told.includes(handover_.group_id));
    return noContent();
  });
}

async function launchAsMarta() {
  serve(MARTA);
  await launchSignedIn();
  jest.setSystemTime(new Date(NOW));
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
}

const theSheet = (title = O3_TITLE) => screen.queryByRole('header', { name: title });
const seenBodies = () => transport.requestsTo('POST', SEEN_PATH).map((request) => request.body);

describe('the handover sheet', () => {
  it('tells an administrator the club made them the administrator of a group, and its queue', async () => {
    handed = [O3_HANDED];

    await launchAsMarta();

    expect(await screen.findByRole('header', { name: O3_TITLE })).toBeTruthy();
    expect(
      screen.getByText(
        'You answer who asks to join it and look after its settings now. Its players, its link and who can join stay as they were.',
      ),
    ).toBeTruthy();
    expect(screen.getByText('2 people are waiting for your answer.')).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.openGroup })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.gotIt })).toBeTruthy();
  });

  it('is not shown to an administrator nobody handed anything', async () => {
    await launchAsMarta();

    expect(
      await screen.findByRole('header', { name: ADMINISTRATOR_COPY.groups.title }),
    ).toBeTruthy();
    expect(theSheet()).toBeNull();
  });

  it('Got it says it was seen, stays where it is, and the sheet does not come back', async () => {
    handed = [O3_HANDED];
    await launchAsMarta();
    expect(await screen.findByRole('header', { name: O3_TITLE })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.gotIt }));

    await waitFor(() => expect(theSheet()).toBeNull());
    await waitFor(() => expect(seenBodies()).toEqual([{ group_ids: [O3_CLUB_ID] }]));
    expect(screen).toHavePathname(`/administrator/${CLUB_ID}`);

    // A relaunch reads the server, which has been told.
    screen.unmount();
    queryClient.clear();
    resetSessionStatus();
    useHandoversClosed.getState().reset();
    await launchSignedIn();
    expect(
      await screen.findByRole('header', { name: ADMINISTRATOR_COPY.groups.title }),
    ).toBeTruthy();
    expect(theSheet()).toBeNull();
  });

  it('Open the group says it was seen and lands on its page, with the queue it came with', async () => {
    handed = [O3_HANDED];
    await launchAsMarta();
    expect(await screen.findByRole('header', { name: O3_TITLE })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.openGroup }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/administrator/${CLUB_ID}/group/${O3_CLUB_ID}`),
    );
    expect(await screen.findByRole('header', { name: 'Ogrody 33 Club' })).toBeTruthy();
    expect(await screen.findByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
    expect(theSheet()).toBeNull();
    await waitFor(() => expect(seenBodies()).toEqual([{ group_ids: [O3_CLUB_ID] }]));
  });

  it('tells several groups one club handed at once on one sheet, and opens the Groups tab', async () => {
    handed = [OPEN_PLAY_HANDED, O3_HANDED];
    const title = 'Ogrody 33 made you the administrator of 2 groups';
    await launchAsMarta();

    expect(await screen.findByRole('header', { name: title })).toBeTruthy();
    expect(
      screen.getByText(
        'Ogrody open play and Ogrody 33 Club. You answer who asks to join them and look after their settings now.',
      ),
    ).toBeTruthy();
    expect(screen.getByText('2 people are waiting for your answer.')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.openGroups }));

    await waitFor(() => expect(theSheet(title)).toBeNull());
    expect(screen).toHavePathname(`/administrator/${CLUB_ID}`);
    await waitFor(() => expect(seenBodies()).toEqual([{ group_ids: [OPEN_PLAY_ID, O3_CLUB_ID] }]));
  });

  it('appears while the app stays open, without being sent away and back', async () => {
    await launchAsMarta();
    expect(
      await screen.findByRole('header', { name: ADMINISTRATOR_COPY.groups.title }),
    ).toBeTruthy();
    expect(theSheet()).toBeNull();

    // The desk hands Marta a group while she looks at her Groups tab.
    handed = [O3_HANDED];
    await act(async () => {
      jest.advanceTimersByTime(30_000);
    });

    expect(await screen.findByRole('header', { name: O3_TITLE })).toBeTruthy();
  });
});

describe('the handover sheet, for an administrator who plays', () => {
  it('is told over the player app, and Open the group switches to the club and opens it', async () => {
    handed = [O3_HANDED];
    serve(TOMEK);

    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(await screen.findByRole('header', { name: O3_TITLE })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.openGroup }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/administrator/${CLUB_ID}/group/${O3_CLUB_ID}`),
    );
    expect(await screen.findByRole('header', { name: 'Ogrody 33 Club' })).toBeTruthy();
  });

  it('waits while an invitation is on offer, and is told once it is answered', async () => {
    handed = [O3_HANDED];
    pending = [
      {
        administrator_id: 'd0000000-0000-4000-8000-000000000009',
        club_id: 'c0000000-0000-4000-8000-000000000099',
        club_name: 'Bonarka Arena',
        expires_at: '2026-09-29T12:00:00Z',
      },
    ];
    serve(TOMEK);

    await launchSignedIn();

    const invitation = 'Bonarka Arena wants to make you an administrator';
    expect(await screen.findByRole('header', { name: invitation })).toBeTruthy();
    expect(theSheet()).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: ADMINISTRATOR_COPY.invitation.notNow }));

    expect(await screen.findByRole('header', { name: O3_TITLE })).toBeTruthy();
  });
});

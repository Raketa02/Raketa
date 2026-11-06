/**
 * **The administrator area, walked** — the gate, the Groups tab, New official group and an official
 * group's page ([#516](https://github.com/Raketa02/Raketa/issues/516), PRD #500 stories 122–130
 * and 136; club mocks 8–11, 17–20).
 *
 * The real route tree, with the socket, the share sheet and the clipboard faked at the platform
 * edge. **The club's administrator routes are answered by a small fake of the server**
 * (`club`), so a create, an approval or a removal changes what the next read says, as it would.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { clearStoredTokens, getSessionStatus, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  launchSignedIn,
  resetClipboard,
  resetShare,
  stubClipboard,
  stubGate,
  stubShare,
} from '@/test-support/onboardingRouter';
import {
  fakeClipboard,
  fakeShare,
  type FakeClipboard,
  type FakeShare,
} from '@/test-support/platform';
import {
  ADMINISTRATOR_ONLY,
  CLUB_ID,
  club,
  CREATED_ID,
  EVERYBODY,
  GROUPS_PATH,
  KUBA,
  MICHAL,
  NOW,
  O3_CLUB_GROUP,
  O3_CLUB_ID,
  OPEN_PLAY_GROUP,
  rating,
  refusal,
  TOMEK,
  type GroupSetup,
} from '@/test-support/officialGroupsServer';
import { NEW_MEMBER_RELIABILITY } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  neverResponds,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from '@/features/groups/types';

import { ADMINISTRATOR_COPY } from './administratorCopy';

const COPY = ADMINISTRATOR_COPY;

// ---------------------------------------------------------------------------
// The walk
// ---------------------------------------------------------------------------

let transport: Transport;
let share: FakeShare;
let clipboard: FakeClipboard;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { nickname: null, profiles: ADMINISTRATOR_ONLY });
  share = fakeShare();
  stubShare(share);
  clipboard = fakeClipboard();
  stubClipboard(clipboard);
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  resetShare();
  resetClipboard();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

/** Launch as Marta, with the club's server answering, and land on the Groups tab. */
async function launchAsAdministrator(setups: readonly GroupSetup[] = []) {
  const server = club(setups);
  server.install(transport);
  await launchSignedIn();
  jest.setSystemTime(new Date(NOW));
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
  expect(await screen.findByRole('header', { name: COPY.groups.title })).toBeTruthy();
  return server;
}

// ---------------------------------------------------------------------------

describe('the entry gate', () => {
  it('sends an account that only administers straight to its area, never to onboarding', async () => {
    await launchAsAdministrator();

    expect(screen.getByRole('button', { name: COPY.groups.newGroupLabel })).toBeTruthy();
  });

  // What a player owes the gate — a rating, a run — is no question this account has to answer, so
  // a read of it that fails holds nothing up.
  it('does not wait on the player’s reads', async () => {
    transport.on('GET', '/api/v1/ratings', () => errorResponse(403, 'forbidden'));
    transport.on('GET', '/api/v1/assessments/in-progress', neverResponds());

    await launchAsAdministrator();

    expect(screen.getByRole('button', { name: COPY.groups.newGroupLabel })).toBeTruthy();
  });

  it('draws the area’s own two tabs, Groups lit', async () => {
    await launchAsAdministrator();

    const bar = screen.getAllByRole('tab');
    expect(bar.map((tab) => tab.props.accessibilityLabel)).toEqual(['Groups', 'You']);
    expect(screen.getByRole('tab', { name: 'Groups', selected: true })).toBeTruthy();
    // Not the player's five.
    expect(screen.queryByRole('tab', { name: 'Play' })).toBeNull();
  });

  it('leaves an account that also plays in the player’s app', async () => {
    stubGate(transport, {
      ratings: [],
      hasPlayerProfile: false,
      profiles: { ...ADMINISTRATOR_ONLY, acts_as_player: true },
    });
    club().install(transport);
    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/tags'));
    expect(transport.requestsTo('GET', GROUPS_PATH)).toHaveLength(0);
  });
});

describe('the Groups tab', () => {
  // The bar under the screen already says whose area it is (#529); the You tab's went too.
  it('is titled Groups, with nothing over the title', async () => {
    await launchAsAdministrator();

    expect(screen.getByRole('header', { name: 'Groups' })).toBeTruthy();
    expect(screen.queryByText('Ogrody 33 · Administrator')).toBeNull();
  });

  it('says there are no official groups yet, beside the one button', async () => {
    await launchAsAdministrator();

    expect(await screen.findByText(COPY.groups.emptyTitle)).toBeTruthy();
    expect(screen.getByText(COPY.groups.emptyLine)).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.groups.newGroupLabel })).toBeTruthy();
  });
});

describe('the Groups tab, with groups', () => {
  it('draws a card per group, newest created first, with who is waiting', async () => {
    await launchAsAdministrator([O3_CLUB_GROUP, OPEN_PLAY_GROUP]);

    const cards = await screen.findAllByRole('button', { name: /^Ogrody (33 Club|open play),/ });
    expect(cards.map((card) => card.props.accessibilityLabel)).toEqual([
      'Ogrody 33 Club, 3 members, 1 waiting, plays Padel, Tennis, Squash, Ogrody 33',
      'Ogrody open play, 2 members, plays Padel, Tennis, Ogrody 33',
    ]);
    expect(within(cards[0]!).getByText('1 waiting')).toBeTruthy();
    expect(within(cards[1]!).queryByText(/waiting/)).toBeNull();
    expect(screen.queryByText(COPY.groups.emptyTitle)).toBeNull();
  });

  it('opens a group’s page from its card', async () => {
    await launchAsAdministrator([O3_CLUB_GROUP]);

    fireEvent.press(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/administrator/${CLUB_ID}/group/${O3_CLUB_ID}`),
    );
    expect(await screen.findByRole('header', { name: 'Ogrody 33 Club' })).toBeTruthy();
    // #529: no eyebrow over the name — every group here is the club's, and official.
    expect(screen.queryByText('Ogrody 33 · Official')).toBeNull();
  });

  // #529: somebody asking on another phone reached the tab only on a refocus, thirty seconds on.
  it('reads the groups again on a pull, and the spinner stops once it has', async () => {
    const server = await launchAsAdministrator([O3_CLUB_GROUP]);
    const list = () => screen.getByTestId('administered-groups');
    expect(
      within(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ })).getByText(
        '1 waiting',
      ),
    ).toBeTruthy();

    server.ask(O3_CLUB_ID, KUBA);
    await act(async () => {
      fireEvent(within(list()).UNSAFE_getByType(RefreshControl), 'refresh');
    });

    expect(
      within(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ })).getByText(
        '2 waiting',
      ),
    ).toBeTruthy();
    await waitFor(() =>
      expect(within(list()).UNSAFE_getByType(RefreshControl).props.refreshing).toBe(false),
    );
  });

  it('says why when the list cannot be read, and reads it again', async () => {
    const server = club([O3_CLUB_GROUP]);
    server.install(transport);
    // Retryable by the person rather than unattended, so it surfaces at once.
    transport.on('GET', GROUPS_PATH, () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();

    // `groups`' failed-read block, and its words.
    const retry = await screen.findByRole('button', { name: GROUPS_COPY.retry });
    server.install(transport);
    fireEvent.press(retry);

    expect(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ })).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------

async function openNewGroup() {
  fireEvent.press(await screen.findByRole('button', { name: COPY.groups.newGroupLabel }));
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}/new-group`));
  expect(await screen.findByRole('header', { name: COPY.newGroup.title })).toBeTruthy();
}

const createButton = () => screen.getByRole('button', { name: COPY.newGroup.create });
const createDisabled = () => createButton().props.accessibilityState?.disabled === true;

async function fillNewGroup({
  name = 'Ogrody 33 Club',
  size = '48',
  sports = ['Padel'],
  approve = true,
}: {
  readonly name?: string;
  readonly size?: string;
  readonly sports?: readonly string[];
  readonly approve?: boolean;
} = {}) {
  fireEvent.changeText(screen.getByLabelText('Name'), name);
  if (approve) fireEvent.press(screen.getByRole('button', { name: 'People I approve' }));
  fireEvent.changeText(screen.getByLabelText(COPY.newGroup.size), size);
  for (const sport of sports) fireEvent.press(await screen.findByRole('button', { name: sport }));
}

describe('New official group', () => {
  it('asks for a name, shows the club fixed, and offers only the club’s sports', async () => {
    await launchAsAdministrator();
    await openNewGroup();

    expect(screen.getByPlaceholderText(COPY.newGroup.namePlaceholder)).toBeTruthy();
    // The size is the group's, not a WhatsApp group's: the crowd gathers in any app (#529).
    expect(screen.getByLabelText('Group size')).toBeTruthy();
    expect(screen.queryByText(/WhatsApp group size/i)).toBeNull();
    expect(screen.getByPlaceholderText(COPY.newGroup.sizePlaceholder)).toBeTruthy();
    // The home club is the club, fixed — a tag, not a field or a choice.
    expect(screen.getByText('Ogrody 33')).toBeTruthy();
    expect(screen.queryByPlaceholderText(/search clubs/i)).toBeNull();
    // Who can join, without the player form's note: an official group declares its sports.
    expect(screen.getByRole('button', { name: 'Anyone' })).toBeTruthy();
    expect(screen.queryByText(/No sport to pick/)).toBeNull();
    expect(await screen.findByRole('button', { name: 'Padel' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Tennis' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Squash' })).toBeTruthy();
    // Ogrody 33 offers no badminton, so no group of its may declare it.
    expect(screen.queryByRole('button', { name: 'Badminton' })).toBeNull();
    // #529: the chips stand alone, with no line under them.
    expect(screen.queryByText(/offers\. Players see this group/)).toBeNull();
  });

  it('creates the group and opens its page, with the toast', async () => {
    await launchAsAdministrator();
    await openNewGroup();

    await fillNewGroup();
    expect(createDisabled()).toBe(false);
    fireEvent.press(createButton());

    await waitFor(() =>
      expect(screen).toHavePathname(`/administrator/${CLUB_ID}/group/${CREATED_ID}`),
    );
    expect(await screen.findByRole('header', { name: 'Ogrody 33 Club' })).toBeTruthy();
    expect(toasts()).toEqual([[COPY.newGroup.created, 'ok']]);
    const [sent] = transport.requestsTo('POST', GROUPS_PATH);
    expect(sent?.body).toEqual({
      name: 'Ogrody 33 Club',
      join_policy: 'PEOPLE_I_APPROVE',
      whatsapp_size: 48,
      sports: ['PADEL'],
    });

    // Back from a new group is the list — never the form — and the list has its card.
    fireEvent.press(screen.getByRole('button', { name: COPY.group.back }));
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
    expect(await screen.findByRole('button', { name: /^Ogrody 33 Club, 0 members,/ })).toBeTruthy();
  });

  it('sends the sports in the registry’s order, whatever order they were ticked in', async () => {
    await launchAsAdministrator();
    await openNewGroup();

    await fillNewGroup({ sports: ['Squash', 'Padel'] });
    fireEvent.press(createButton());

    await waitFor(() => expect(transport.requestsTo('POST', GROUPS_PATH)).toHaveLength(1));
    const [sent] = transport.requestsTo('POST', GROUPS_PATH);
    expect((sent?.body as Wire['CreateOfficialGroupRequest']).sports).toEqual(['PADEL', 'SQUASH']);
  });

  it('stays closed without a name, a group size or a sport', async () => {
    await launchAsAdministrator();
    await openNewGroup();

    expect(createDisabled()).toBe(true);
    await fillNewGroup({ name: '   ' });
    expect(createDisabled()).toBe(true);

    fireEvent.changeText(screen.getByLabelText('Name'), 'Ogrody 33 Club');
    expect(createDisabled()).toBe(false);

    // Required: an empty size is no group.
    fireEvent.changeText(screen.getByLabelText(COPY.newGroup.size), '');
    expect(createDisabled()).toBe(true);
    fireEvent.changeText(screen.getByLabelText(COPY.newGroup.size), '48');

    // Required: unticking the one sport is no group.
    fireEvent.press(screen.getByRole('button', { name: 'Padel' }));
    expect(createDisabled()).toBe(true);
  });

  it('holds the group size to 2–1024, and says so on the field', async () => {
    await launchAsAdministrator();
    await openNewGroup();
    await fillNewGroup();
    const size = screen.getByLabelText(COPY.newGroup.size);

    for (const typed of ['1', '1025', '4.5']) {
      fireEvent.changeText(size, typed);
      expect(createDisabled()).toBe(true);
      expect(screen.getByText('A whole number from 2 to 1024')).toBeTruthy();
    }
    for (const typed of ['2', '1024']) {
      fireEvent.changeText(size, typed);
      expect(createDisabled()).toBe(false);
      expect(screen.queryByText('A whole number from 2 to 1024')).toBeNull();
    }
  });

  it('says a refusal on the field the server names, and forgets it once the field changes', async () => {
    await launchAsAdministrator();
    transport.on('POST', GROUPS_PATH, () => refusal('sport_not_offered_by_club', 'sports'));
    await openNewGroup();
    await fillNewGroup();

    fireEvent.press(createButton());

    expect(
      await screen.findByText('The club doesn’t offer one of those sports any more. Pick again.'),
    ).toBeTruthy();
    expect(screen).toHavePathname(`/administrator/${CLUB_ID}/new-group`);

    fireEvent.press(screen.getByRole('button', { name: 'Tennis' }));
    expect(screen.queryByText(/doesn’t offer one of those sports/)).toBeNull();
  });

  it('discards the form on the back arrow', async () => {
    await launchAsAdministrator();
    await openNewGroup();
    await fillNewGroup();

    fireEvent.press(screen.getByRole('button', { name: COPY.newGroup.back }));
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
    await openNewGroup();

    expect(screen.getByLabelText('Name').props.value).toBe('');
    expect(transport.requestsTo('POST', GROUPS_PATH)).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------

async function openGroup(setup: GroupSetup, setups: readonly GroupSetup[] = [setup]) {
  const server = await launchAsAdministrator(setups);
  fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${setup.name},`) }));
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}/group/${setup.id}`));
  expect(await screen.findByRole('header', { name: setup.name })).toBeTruthy();
  return server;
}

describe('an official group’s page', () => {
  // #529: a request left since the page was read waited for a return to it, thirty seconds on.
  it('reads the group again on a pull, and the spinner stops once it has', async () => {
    const server = await openGroup(O3_CLUB_GROUP);
    const page = () => screen.getByTestId('official-group-page');
    expect(await screen.findByRole('header', { name: 'Want to join · 1' })).toBeTruthy();

    server.ask(O3_CLUB_ID, KUBA);
    await act(async () => {
      fireEvent(within(page()).UNSAFE_getByType(RefreshControl), 'refresh');
    });

    expect(await screen.findByRole('header', { name: 'Want to join · 2' })).toBeTruthy();
    expect(screen.getByLabelText(/^Kuba Wróbel,/)).toBeTruthy();
    await waitFor(() =>
      expect(within(page()).UNSAFE_getByType(RefreshControl).props.refreshing).toBe(false),
    );
  });

  it('draws the link card with Share link and Copy link, and never a posted tag', async () => {
    await openGroup(O3_CLUB_GROUP);

    expect(screen.getByLabelText('Group link, raketa.app/join/K7PQ2MXA')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Share link' })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.group.copy })).toBeTruthy();
    // The link goes out through any app now, so the card names none (#529).
    expect(screen.queryByText(/WhatsApp/)).toBeNull();
    expect(screen.queryByText(/posted/i)).toBeNull();
    expect(screen.queryByText(/Post again/i)).toBeNull();
  });

  it('shares the message through the phone’s share sheet', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: COPY.group.share }));

    await waitFor(() =>
      expect(share.shared).toEqual([
        'Join Ogrody 33 Club on Raketa: https://raketa.app/join/K7PQ2MXA',
      ]),
    );
  });

  it('copies the bare link, and says so', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: COPY.group.copy }));

    await waitFor(() => expect(clipboard.text).toBe('https://raketa.app/join/K7PQ2MXA'));
    await waitFor(() => expect(toasts()).toEqual([['Link copied', 'ok']]));
  });

  it('counts the members, stacks their faces, and rings how much of the group has arrived', async () => {
    await openGroup(OPEN_PLAY_GROUP);

    const card = screen.getByRole('button', { name: '2 members, 7% of the group size' });
    const faces = within(card)
      .queryAllByTestId(/^members-face-/, { includeHiddenElements: true })
      .map((node) => (node.props.testID as string).replace('members-face-', ''));
    expect(faces).toEqual([MICHAL.id, TOMEK.id]);
    // Members, as Info's card says it to a member (#529) — they were club 18's *players*.
    expect(within(card).getByText('2 members')).toBeTruthy();
    expect(screen.queryByText(/\bplayers?\b/)).toBeNull();
    expect(within(card).getByText('7%', { includeHiddenElements: true })).toBeTruthy();
    // The rule and the share in words went with the line; the list of join dates with the tap.
    expect(screen.queryByText(/of the WhatsApp group/)).toBeNull();
    expect(screen.queryByText(/anyone with the link joins/)).toBeNull();
    expect(screen.queryByText(/31 Aug|this week/)).toBeNull();
    expect(screen.queryByText(/remove/i)).toBeNull();
  });

  it('draws an empty ring under nobody yet', async () => {
    await openGroup({ ...O3_CLUB_GROUP, players: [], requests: [] });

    expect(screen.getByRole('button', { name: '0 members, 0% of the group size' })).toBeTruthy();
    expect(screen.queryAllByTestId(/^members-face-/, { includeHiddenElements: true })).toEqual([]);
    expect(screen.queryByTestId('arrived-arc', { includeHiddenElements: true })).toBeNull();
    expect(screen.queryByText(/^Want to join/)).toBeNull();
  });

  it('counts past five faces, and past the whole group size', async () => {
    const crowd = EVERYBODY.map((who, at) => ({
      who,
      joinedAt: `2026-08-${String(20 - at).padStart(2, '0')}T10:00:00Z`,
    }));
    await openGroup({ ...OPEN_PLAY_GROUP, size: 6, players: crowd });

    expect(screen.getByRole('button', { name: '7 members, 117% of the group size' })).toBeTruthy();
    expect(screen.getByText('+2')).toBeTruthy();
    expect(screen.getByText('117%', { includeHiddenElements: true })).toBeTruthy();
  });

  it('has no way to delete or leave the group', async () => {
    await openGroup(O3_CLUB_GROUP);

    expect(screen.queryByRole('button', { name: /delete|leave/i })).toBeNull();
  });
});

describe('Members, from the members card', () => {
  const membersPath = (groupId: string) => `/api/v1/groups/${groupId}/members`;

  /** The members read, for one sport — the server's rows for the Administrator who runs it. */
  function serveMembers(
    groupId: string,
    rows: Readonly<Record<string, Wire['GroupMemberSchema'][]>>,
  ) {
    transport.on('GET', membersPath(groupId), (request) => {
      const sport = new URLSearchParams(request.path.split('?')[1]).get('sport') as Wire['Sport'];
      return json<Wire['GroupMembersResponse']>({ sport, members: rows[sport] ?? [] });
    });
  }

  const member = (who: typeof MICHAL, level: number): Wire['GroupMemberSchema'] => ({
    player_id: who.id,
    nickname: who.name,
    level,
    ...NEW_MEMBER_RELIABILITY,
    is_owner: false,
    is_administrator: false,
    joined_at: '2026-09-24T09:00:00Z',
    relation: 'NONE',
  });

  async function openMembers(setup: GroupSetup) {
    await openGroup(setup);
    fireEvent.press(screen.getByRole('button', { name: /^\d+ members?, / }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/administrator/${CLUB_ID}/group/${setup.id}/members`),
    );
  }

  it('opens the member’s Members from the card, on the group’s first sport', async () => {
    serveMembers(OPEN_PLAY_GROUP.id, {
      PADEL: [member(MICHAL, 2.44), member(TOMEK, 2.71)],
      TENNIS: [member(TOMEK, 3.1)],
    });
    await openMembers(OPEN_PLAY_GROUP);

    expect(await screen.findByRole('header', { name: 'Members · 2' })).toBeTruthy();
    const rows = (await screen.findAllByTestId(/^member-/)).map(
      (node) => node.props.accessibilityLabel as string,
    );
    expect(rows).toEqual([
      expect.stringMatching(/^Michał Rogalski/),
      expect.stringMatching(/^Tomek Kowal/),
    ]);
    const asked = transport.requestsTo('GET', membersPath(OPEN_PLAY_GROUP.id));
    expect(asked.map((request) => request.path.split('?')[1])).toEqual(['sport=PADEL']);
  });

  // #753: the Administrator's view of an official group's Members draws no friend pills or tags,
  // whatever the rows carry (the friends screens §1).
  it('draws no friend pill or tag on any row', async () => {
    serveMembers(OPEN_PLAY_GROUP.id, {
      PADEL: [{ ...member(MICHAL, 2.44), relation: 'ASKED_YOU' }, member(TOMEK, 2.71)],
    });
    await openMembers(OPEN_PLAY_GROUP);

    expect(await screen.findByRole('header', { name: 'Members · 2' })).toBeTruthy();
    expect(screen.queryAllByTestId(/^friend-row-/)).toHaveLength(0);
    expect(screen.queryByText(/^(\+ Add|Accept|request sent|friend)$/)).toBeNull();
  });

  // Marta plays nothing: the pill is the group's sports, never a *Rate Padel* card for hers.
  it('lists the group’s declared sports, whatever the Administrator plays', async () => {
    serveMembers(OPEN_PLAY_GROUP.id, {
      PADEL: [member(MICHAL, 2.44), member(TOMEK, 2.71)],
      TENNIS: [member(TOMEK, 3.1)],
    });
    await openMembers(OPEN_PLAY_GROUP);
    expect(await screen.findByRole('header', { name: 'Members · 2' })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Sport: Padel' }));
    const bar = await screen.findByTestId('sport-bar');
    fireEvent.press(within(bar).getByRole('button', { name: 'Tennis' }));

    expect(await screen.findByRole('header', { name: 'Members · 1' })).toBeTruthy();
    expect(screen.queryByText(/Add (Padel|Tennis)/)).toBeNull();
  });

  // The server reads Members for whoever runs the group; a refusal means it is no longer hers.
  it('says the group is no longer hers when the list is refused', async () => {
    transport.on('GET', membersPath(OPEN_PLAY_GROUP.id), () =>
      errorResponse(404, 'group_not_found'),
    );
    await openMembers(OPEN_PLAY_GROUP);

    expect(await screen.findByText('This isn’t a group you run any more.')).toBeTruthy();
    expect(screen.queryByText(/went wrong at our end/)).toBeNull();
  });

  it('goes back to the group’s page', async () => {
    serveMembers(OPEN_PLAY_GROUP.id, { PADEL: [member(MICHAL, 2.44)] });
    await openMembers(OPEN_PLAY_GROUP);
    expect(await screen.findByRole('header', { name: 'Members · 1' })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: GROUPS_COPY.members.back }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/administrator/${CLUB_ID}/group/${OPEN_PLAY_GROUP.id}`),
    );
    expect(screen.getByRole('tab', { name: 'Groups', selected: true })).toBeTruthy();
  });
});

describe('Want to join', () => {
  it('lists who is asking, with every sport they are rated in', async () => {
    await openGroup(O3_CLUB_GROUP);

    expect(screen.getByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
    expect(screen.getByLabelText('Michał Rogalski, Padel 2,44 · Tennis 2,60')).toBeTruthy();
  });

  it('admits the person approved, whose face comes first on the members card', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: 'Approve Michał Rogalski' }));

    await waitFor(() => expect(screen.queryByText(/^Want to join/)).toBeNull());
    const card = await screen.findByRole('button', { name: '4 members, 8% of the group size' });
    const [newest] = within(card).queryAllByTestId(/^members-face-/, {
      includeHiddenElements: true,
    });
    expect(newest?.props.testID).toBe(`members-face-${MICHAL.id}`);
    expect(
      transport.requestsTo('POST', `${GROUPS_PATH}/${O3_CLUB_ID}/requests/${MICHAL.id}/approve`),
    ).toHaveLength(1);
  });

  it('declines at once and admits nobody', async () => {
    const server = await openGroup(O3_CLUB_GROUP);
    server.ask(O3_CLUB_ID, KUBA);
    await act(async () => {
      await queryClient.refetchQueries();
    });
    expect(await screen.findByRole('header', { name: 'Want to join · 2' })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Decline Kuba Wróbel' }));

    expect(await screen.findByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
    expect(screen.queryByLabelText(/^Kuba Wróbel,/)).toBeNull();
    expect(
      transport.requestsTo('POST', `${GROUPS_PATH}/${O3_CLUB_ID}/requests/${KUBA.id}/decline`),
    ).toHaveLength(1);
    expect(screen.getByRole('button', { name: /^3 members,/ })).toBeTruthy();
  });

  it('takes the row before the answer lands', async () => {
    await openGroup(O3_CLUB_GROUP);
    transport.on(
      'POST',
      `${GROUPS_PATH}/${O3_CLUB_ID}/requests/${MICHAL.id}/decline`,
      neverResponds(),
    );

    fireEvent.press(screen.getByRole('button', { name: 'Decline Michał Rogalski' }));

    await waitFor(() => expect(screen.queryByLabelText(/^Michał Rogalski,/)).toBeNull());
  });

  it('puts the row back, and says why, when the answer is refused', async () => {
    await openGroup(O3_CLUB_GROUP);
    transport.on('POST', `${GROUPS_PATH}/${O3_CLUB_ID}/requests/${MICHAL.id}/approve`, () =>
      errorResponse(404, 'join_request_not_found'),
    );

    fireEvent.press(screen.getByRole('button', { name: 'Approve Michał Rogalski' }));

    await waitFor(() =>
      expect(toasts()).toEqual([['That request isn’t waiting any more.', 'bad']]),
    );
  });

  it('refreshes the Groups tab’s waiting count', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: 'Approve Michał Rogalski' }));
    await waitFor(() => expect(screen.queryByText(/^Want to join/)).toBeNull());
    fireEvent.press(screen.getByRole('button', { name: COPY.group.back }));

    expect(
      await screen.findByRole('button', { name: /^Ogrody 33 Club, 4 members, plays/ }),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------

describe('removed while here', () => {
  it('tells an account that only administers, and signs it out', async () => {
    const server = await launchAsAdministrator([O3_CLUB_GROUP]);
    server.remove();

    fireEvent.press(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ }));

    await waitFor(() => expect(getSessionStatus()).toBe('unauthenticated'));
    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(toasts()).toEqual([
      ['Ogrody 33 removed you as an administrator. You’re signed out.', 'base'],
    ]);
  });

  it('says it once, however many requests are refused', async () => {
    const server = await launchAsAdministrator([O3_CLUB_GROUP]);
    server.remove();

    fireEvent.press(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ }));
    await act(async () => {
      await queryClient.refetchQueries();
    });

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(toasts()).toHaveLength(1);
  });

  it('is noticed on a write as well as a read', async () => {
    const server = await openGroup(O3_CLUB_GROUP);
    server.remove();

    fireEvent.press(screen.getByRole('button', { name: 'Approve Michał Rogalski' }));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    // The removal is the one sentence; the refused answer adds none of its own.
    expect(toasts()).toEqual([
      ['Ogrody 33 removed you as an administrator. You’re signed out.', 'base'],
    ]);
  });
});

describe('removed, and the profile read says so first', () => {
  // The You tab asks no administrator route, so the removal is heard from `/users/me`, which no
  // longer lists the club — the area must not fall through to the gate and onboarding.
  it('tells an account that only administers, and signs it out', async () => {
    await launchAsAdministrator();
    fireEvent.press(screen.getByRole('tab', { name: 'You' }));
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}/you`));

    stubGate(transport, {
      nickname: null,
      profiles: { ...ADMINISTRATOR_ONLY, administers: [] },
    });
    await act(async () => {
      await queryClient.refetchQueries();
    });

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(toasts()).toEqual([
      ['Ogrody 33 removed you as an administrator. You’re signed out.', 'base'],
    ]);
    // Never handed to the gate, which would have sent it into the player's profile steps.
    expect(screen.queryByText('What kind of player are you?')).toBeNull();
  });
});

describe('removed, an account that also plays', () => {
  it('is told, and moved to its player side rather than signed out', async () => {
    stubGate(transport, {
      nickname: 'tomek.k',
      ratings: [rating('PADEL')],
      hasPlayerProfile: true,
      profiles: { ...ADMINISTRATOR_ONLY, acts_as_player: true },
    });
    const server = club([O3_CLUB_GROUP]);
    server.install(transport);
    await launchSignedIn(`/administrator/${CLUB_ID}`);
    expect(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ })).toBeTruthy();
    server.remove();

    fireEvent.press(screen.getByRole('button', { name: /^Ogrody 33 Club,/ }));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(getSessionStatus()).toBe('authenticated');
    expect(toasts()).toEqual([['Ogrody 33 removed you as an administrator.', 'base']]);
  });
});

describe('the two tabs', () => {
  it('opens You, with the way out, and comes back to Groups', async () => {
    await launchAsAdministrator([O3_CLUB_GROUP]);

    fireEvent.press(screen.getByRole('tab', { name: 'You' }));

    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}/you`));
    // Club 8's header, moved here (#517): the account's nickname, and *You* for one that has not
    // started playing and holds none — the name its club typed is the Administrator's (ADR-0199 §4).
    expect(await screen.findByRole('header', { name: 'You' })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'You', selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeTruthy();

    fireEvent.press(screen.getByRole('tab', { name: 'Groups' }));
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
  });

  it('draws each tab with the inset under its header from the first frame', async () => {
    // A tab press replaces the screen with no transition, so a native `SafeAreaView`'s first frame
    // — drawn without the inset and moved down on the next — was the whole press on Android: the
    // header blinked between the tabs (#529). Every screen here takes the inset from the provider.
    await launchAsAdministrator([O3_CLUB_GROUP]);
    expect(screen.UNSAFE_queryAllByType(SafeAreaView)).toHaveLength(0);

    fireEvent.press(screen.getByRole('tab', { name: 'You' }));

    expect(await screen.findByRole('header', { name: 'You' })).toBeTruthy();
    expect(screen.UNSAFE_queryAllByType(SafeAreaView)).toHaveLength(0);
  });

  it('lays the Groups list down from a group’s page, never the page', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('tab', { name: 'Groups' }));

    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
  });

  it('signs out from You', async () => {
    await launchAsAdministrator();
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );

    fireEvent.press(screen.getByRole('tab', { name: 'You' }));
    fireEvent.press(await screen.findByRole('button', { name: 'Sign out' }));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    // Leaving on purpose is not a removal.
    expect(toasts()).toEqual([]);
  });

  it('sends an account to the gate from a club it does not administer', async () => {
    club().install(transport);
    await launchSignedIn(`/administrator/c0000000-0000-4000-8000-000000000099`);

    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
  });
});

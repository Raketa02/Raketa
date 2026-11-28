/**
 * **You › Friends and the Add friends sheet, walked through the real route tree**
 * ([#754](https://github.com/Rakieta02/Rakieta/issues/754), PRD #743; the friends screens §4.1, §5;
 * friends 3, 4).
 *
 * - **The You tab's *Friends* row** says how many friends and who asked, and opens the page.
 * - **The page's three tabs**, *Friends · Asked you · You asked*: only *Asked you* counts; its rows
 *   have **Accept**, *You asked*'s **Cancel**, and the rest of every row opens the record; each tab
 *   has a one-line empty state.
 * - **+ Add friends** opens the sheet: *From your groups*, each group's tile, name and *8 members ·
 *   2 to add*, and a tap lands on that group's Members — where a request asked turns up on *You
 *   asked* back on the page.
 * - **The sheet's link card** (#756, friends 4): *Not on Rakieta yet?*, your link, **Copy** onto the
 *   clipboard, and a small **New link** that asks first and then kills the old one.
 *
 * **The friends routes are answered by a small fake of the server** (`friendsServer`): an act moves
 * what the next read says, as it would, so a row that leaves after a press is the page re-read.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { RECORD_TITLE } from '@/features/player_record/types';
import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { doorRowLabel } from '@/shared/ui';
import {
  FRIEND_LINK_PATH,
  FRIEND_REQUESTS_PATH,
  FRIENDS_PATH,
  SPORTS_SERVED,
  launchSignedIn,
  resetClipboard,
  stubClipboard,
  stubGate,
  stubMyGroups,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, type FakeClipboard } from '@/test-support/platform';
import { servedReliability } from '@/test-support/playerRecord';
import { stubGroupDeck } from '@/test-support/groupDeck';
import {
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import {
  FRIENDS_COPY,
  acceptLabel,
  addLabel,
  askedYouTab,
  cancelRequestLabel,
  friendLinkLabel,
  friendsRowLine,
  groupRowLabel,
} from './friendsCopy';

const PAGE = FRIENDS_COPY.page;
const SHEET = FRIENDS_COPY.sheet;
const LINK = FRIENDS_COPY.link;
const HIDDEN_TOO = { includeHiddenElements: true } as const;

interface Person {
  readonly id: string;
  readonly name: string;
}

const person = (n: number, name: string): Person => ({
  id: `e0000000-0000-4000-8000-0000000000${String(n).padStart(2, '0')}`,
  name,
});

/** Friends, by nickname as the server sends them. */
const ANIA = person(1, 'ania.k');
const EWA = person(2, 'ewa.m');
/** She asked Tomek — once set aside, once not. */
const INES = person(3, 'ines.d');
const ZOFIA = person(4, 'zofia.b');
/** Tomek asked him. */
const MICHAL = person(5, 'michal.r');
/** In Kazimierz crew, and nothing between them yet. */
const KUBA = person(6, 'kuba.w');
const PEOPLE = [ANIA, EWA, INES, ZOFIA, MICHAL, KUBA];

const OGRODY: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000011',
  kind: 'OFFICIAL',
  name: 'Ogrody open play',
  monogram: { letters: 'Oo', colour: 2 },
  sports: ['PADEL'],
  member_count: 8,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Ogrody 33' },
};

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000012',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 5 },
  sports: ['PADEL'],
  member_count: 10,
  home_club: { id: 'c0000000-0000-4000-8000-000000000002', name: 'Centrum Ruchu' },
};

const CREW_PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://rakieta.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [{ sport: 'PADEL', rated_count: 10, first_rated: [] }],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

const GROUPS_PATH = '/api/v1/friends/groups';
const acceptPath = (who: Person) => `${FRIEND_REQUESTS_PATH}/${who.id}/acceptance`;
const cancelPath = (who: Person) => `${FRIEND_REQUESTS_PATH}/${who.id}`;
const recordPath = (who: Person) => `/api/v1/players/${who.id}/record`;
const MEMBERS_PATH = `/api/v1/groups/${CREW.id}/members`;

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.62,
    confidence: 28,
    range: { low: mu - 0.6, high: mu + 0.6 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

/** Each friend's sports, as `GET /friends` gives them. */
const SPORTS: Readonly<Record<string, readonly Wire['FriendSportSchema'][]>> = {
  [ANIA.id]: [{ sport: 'PADEL', level: 2.68, band: 'Established' }],
  [EWA.id]: [
    { sport: 'PADEL', level: 2.6, band: 'Developing' },
    { sport: 'TENNIS', level: 3.1, band: 'Established' },
  ],
  [INES.id]: [{ sport: 'PADEL', level: 3.4, band: 'Established' }],
};

interface ServerState {
  readonly friends: Person[];
  readonly askedYou: Person[];
  readonly youAsked: Person[];
}

/**
 * **The friends routes, faked** — your friends by nickname, the requests newest first, and the
 * sheet's groups counting who is left to add. An accept makes them a friend; a cancel takes yours
 * back; asking from Members puts them on *You asked*.
 */
function friendsServer(
  initially: Partial<ServerState> = {},
  { setAside = [INES.id] }: { readonly setAside?: readonly string[] } = {},
): ServerState {
  const state: ServerState = {
    friends: [...(initially.friends ?? [ANIA, EWA])],
    askedYou: [...(initially.askedYou ?? [INES, ZOFIA])],
    youAsked: [...(initially.youAsked ?? [MICHAL])],
  };
  const byName = (a: Person, b: Person) => a.name.localeCompare(b.name);
  const request = (who: Person): Wire['FriendRequestSchema'] => ({
    player_id: who.id,
    nickname: who.name,
    photo_id: null,
    photo_url: null,
    asked_at: '2026-10-01T07:00:00Z',
    set_aside: setAside.includes(who.id),
  });
  const relation = (who: Person): Wire['FriendRelation'] =>
    state.friends.includes(who)
      ? 'FRIEND'
      : state.askedYou.includes(who)
        ? 'ASKED_YOU'
        : state.youAsked.includes(who)
          ? 'SENT'
          : 'NONE';

  transport.on('GET', FRIENDS_PATH, () =>
    json<Wire['FriendsResponse']>({
      sport: null,
      friends: [...state.friends].sort(byName).map((who) => ({
        player_id: who.id,
        nickname: who.name,
        photo_id: null,
        photo_url: null,
        friends_since: '2026-10-01T10:00:00Z',
        level_asked_in: [],
        sports: [...(SPORTS[who.id] ?? [])],
      })),
    }),
  );
  transport.on('GET', FRIEND_REQUESTS_PATH, (asked) => {
    const direction: Wire['Direction'] = asked.path.includes('YOU_ASKED')
      ? 'YOU_ASKED'
      : 'ASKED_YOU';
    const list = direction === 'ASKED_YOU' ? state.askedYou : state.youAsked;
    return json<Wire['FriendRequestsResponse']>({ direction, requests: list.map(request) });
  });
  transport.on('POST', FRIEND_REQUESTS_PATH, (asked) => {
    const { player_id: id } = asked.body as Wire['AskToBeFriendsRequest'];
    const who = PEOPLE.find((one) => one.id === id)!;
    state.youAsked.unshift(who);
    return json<Wire['RelationResponse']>({ relation: 'SENT' });
  });
  transport.on('GET', GROUPS_PATH, () =>
    json<Wire['GroupsToAddFromResponse']>({
      groups: [
        { group_id: OGRODY.id, name: OGRODY.name, member_count: 8, to_add: 2 },
        {
          group_id: CREW.id,
          name: CREW.name,
          member_count: 10,
          // Kuba is the one left to add in the crew, until he is asked.
          to_add: relation(KUBA) === 'NONE' ? 1 : 0,
        },
      ],
    }),
  );

  for (const who of PEOPLE) {
    transport.on('POST', acceptPath(who), () => {
      state.askedYou.splice(state.askedYou.indexOf(who), 1);
      state.friends.push(who);
      return json<Wire['RelationResponse']>({ relation: 'FRIEND' });
    });
    transport.on('DELETE', cancelPath(who), () => {
      const at = state.youAsked.indexOf(who);
      if (at >= 0) state.youAsked.splice(at, 1);
      return noContent();
    });
    transport.on('GET', recordPath(who), () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: relation(who),
        can_add_friend: true,
        nickname: who.name,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: 2.7, band: 'Established' }],
        reliability: servedReliability({ player_score: 95, is_new: false }),
      }),
    );
  }

  // Kazimierz crew's Members, where the sheet lands.
  transport.on('GET', MEMBERS_PATH, () =>
    json<Wire['GroupMembersResponse']>({
      sport: 'PADEL',
      members: [KUBA, MICHAL].map((who) => ({
        player_id: who.id,
        nickname: who.name,
        level: 2.8,
        player_score: 96,
        reliability_band: 'VERY_HIGH' as const,
        is_owner: false,
        is_administrator: false,
        joined_at: '2026-09-10T10:00:00Z',
        relation: relation(who),
      })),
    }),
  );

  return state;
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [rating('PADEL', 2.71)], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubOwnRecord(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  stubMyGroups(transport, [OGRODY, CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(CREW_PAGE));
  stubGroupDeck(transport, CREW.id);
});

afterEach(async () => {
  // One test takes the connection away, and `onlineManager` is a singleton.
  onlineManager.setOnline(true);
  resetClipboard();
  useToastQueue.setState({ queue: [] });
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** The You tab, its *Friends* row drawn with this line. */
async function openYou(line: string) {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  return screen.findByLabelText(doorRowLabel(FRIENDS_COPY.row.title, line));
}

/** You › Friends, from its row. */
async function openFriends(line = friendsRowLine(2, 2)) {
  fireEvent.press(await openYou(line));
  await waitFor(() => expect(screen).toHavePathname('/you/friends'));
  expect(await screen.findByRole('header', { name: PAGE.title })).toBeTruthy();
}

/** A tab of the page's segmented control, by what it says. */
const tab = (label: string) => screen.getByRole('button', { name: label });

const rowOf = (prefix: string, who: Person) => screen.queryByTestId(`${prefix}-${who.id}`);

// ---------------------------------------------------------------------------
// The You tab's row
// ---------------------------------------------------------------------------

describe('the Friends row on You', () => {
  it('says how many friends and who asked, and opens the page', async () => {
    friendsServer();
    await openFriends(friendsRowLine(2, 2));

    expect(screen.getByRole('button', { name: PAGE.addLabel })).toBeTruthy();
  });

  it('comes back out to You from the page’s back control', async () => {
    friendsServer();
    await openFriends();

    fireEvent.press(screen.getByRole('button', { name: 'Back' }));

    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(
      await screen.findByLabelText(doorRowLabel(FRIENDS_COPY.row.title, friendsRowLine(2, 2))),
    ).toBeTruthy();
  });

  it('says plainly there are none yet', async () => {
    friendsServer({ friends: [], askedYou: [], youAsked: [] });
    expect(await openYou(friendsRowLine(0, 0))).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The page's three tabs (the screens §4.1)
// ---------------------------------------------------------------------------

describe('You › Friends', () => {
  it('opens on Friends, by nickname, each with every sport they play and its Level', async () => {
    friendsServer();
    await openFriends();

    expect(tab(PAGE.tabs.friends).props.accessibilityState).toEqual({ selected: true });
    const rows = await screen.findAllByTestId(/^friend-e/);
    expect(rows.map((row) => row.props.testID)).toEqual([`friend-${ANIA.id}`, `friend-${EWA.id}`]);
    expect(within(rows[0]!).getByText('Padel 2,68')).toBeTruthy();
    expect(within(rows[1]!).getByText('Padel 2,60 · Tennis 3,10')).toBeTruthy();
    // A friend's row has nothing to press but itself.
    expect(within(rows[0]!).queryByText(PAGE.accept)).toBeNull();
    expect(within(rows[0]!).queryByText(PAGE.cancel)).toBeNull();
  });

  it('counts Asked you alone, set-aside requests included', async () => {
    friendsServer();
    await openFriends();

    expect(tab(askedYouTab(2))).toBeTruthy();
    expect(tab(PAGE.tabs.friends)).toBeTruthy();
    expect(tab(PAGE.tabs.YOU_ASKED)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Friends · |^You asked · / })).toBeNull();
  });

  it('Asked you: Accept on each, and an accepted one moves to Friends', async () => {
    friendsServer();
    await openFriends();

    fireEvent.press(tab(askedYouTab(2)));
    expect(await screen.findByTestId(`asked-you-${INES.id}`)).toBeTruthy();
    expect(rowOf('asked-you', ZOFIA)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: acceptLabel(ZOFIA.name) }));

    await waitFor(() => expect(transport.requestsTo('POST', acceptPath(ZOFIA))).toHaveLength(1));
    await waitFor(() => expect(rowOf('asked-you', ZOFIA)).toBeNull());
    expect(tab(askedYouTab(1))).toBeTruthy();

    fireEvent.press(tab(PAGE.tabs.friends));
    expect(await screen.findByTestId(`friend-${ZOFIA.id}`)).toBeTruthy();
  });

  it('You asked: Cancel on each, and a cancelled one leaves', async () => {
    friendsServer();
    await openFriends();

    fireEvent.press(tab(PAGE.tabs.YOU_ASKED));
    const row = await screen.findByTestId(`you-asked-${MICHAL.id}`);
    expect(within(row).getByText(PAGE.cancel)).toBeTruthy();

    fireEvent.press(within(row).getByRole('button', { name: cancelRequestLabel(MICHAL.name) }));

    await waitFor(() => expect(transport.requestsTo('DELETE', cancelPath(MICHAL))).toHaveLength(1));
    expect(await screen.findByText(PAGE.empty.YOU_ASKED)).toBeTruthy();
  });

  it.each([
    ['friends', 'friend', ANIA],
    ['ASKED_YOU', 'asked-you', INES],
    ['YOU_ASKED', 'you-asked', MICHAL],
  ] as const)(
    '%s: the rest of a row opens the record, and asks nothing',
    async (key, prefix, who) => {
      friendsServer();
      await openFriends();
      fireEvent.press(tab(key === 'ASKED_YOU' ? askedYouTab(2) : PAGE.tabs[key]));

      fireEvent.press(await screen.findByTestId(`${prefix}-open-${who.id}`));

      expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
      await waitFor(() => expect(transport.requestsTo('GET', recordPath(who))).toHaveLength(1));
      expect(transport.requestsTo('POST', acceptPath(who))).toHaveLength(0);
      expect(transport.requestsTo('DELETE', cancelPath(who))).toHaveLength(0);
    },
  );

  it('says one line on each tab with nobody on it', async () => {
    friendsServer({ friends: [], askedYou: [], youAsked: [] });
    await openFriends(friendsRowLine(0, 0));

    expect(await screen.findByText(PAGE.empty.friends)).toBeTruthy();
    // Nobody waits: the tab is its name alone.
    fireEvent.press(tab(PAGE.tabs.ASKED_YOU));
    expect(await screen.findByText(PAGE.empty.ASKED_YOU)).toBeTruthy();
    fireEvent.press(tab(PAGE.tabs.YOU_ASKED));
    expect(await screen.findByText(PAGE.empty.YOU_ASKED)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The Add friends sheet (the screens §5; friends 4)
// ---------------------------------------------------------------------------

describe('+ Add friends', () => {
  async function openSheet() {
    fireEvent.press(screen.getByRole('button', { name: PAGE.addLabel }));
    expect(await screen.findByRole('header', { name: SHEET.title })).toBeTruthy();
  }

  it('lists your groups, each with its tile, name, and how many are left to add', async () => {
    friendsServer();
    await openFriends();
    await openSheet();

    expect(screen.getByText(SHEET.fromYourGroups)).toBeTruthy();
    const ogrody = await screen.findByRole('button', { name: groupRowLabel(OGRODY.name, 8, 2) });
    expect(within(ogrody).getByText('8 members · 2 to add')).toBeTruthy();
    // The tile is the Groups list's, read the moment the sheet asks for it.
    expect(await within(ogrody).findByText('Oo', HIDDEN_TOO)).toBeTruthy();
    const crew = screen.getByRole('button', { name: groupRowLabel(CREW.name, 10, 1) });
    expect(within(crew).getByText('10 members · 1 to add')).toBeTruthy();
    expect(await within(crew).findByText('Kc', HIDDEN_TOO)).toBeTruthy();
  });

  it('lands on the group’s Members, and a request asked there is on You asked back here', async () => {
    friendsServer();
    await openFriends();
    await openSheet();

    fireEvent.press(await screen.findByRole('button', { name: groupRowLabel(CREW.name, 10, 1) }));

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}/members`));
    expect(screen.queryByRole('header', { name: SHEET.title })).toBeNull();
    fireEvent.press(await screen.findByRole('button', { name: addLabel(KUBA.name) }));
    await waitFor(() => expect(transport.requestsTo('POST', FRIEND_REQUESTS_PATH)).toHaveLength(1));
    expect(
      await within(screen.getByTestId(`friend-row-${KUBA.id}`)).findByText(
        FRIENDS_COPY.members.sent,
      ),
    ).toBeTruthy();

    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/you/friends'));
    fireEvent.press(tab(PAGE.tabs.YOU_ASKED));
    expect(await screen.findByTestId(`you-asked-${KUBA.id}`)).toBeTruthy();
  });

  /** The groups and the link card under them (#756) each wait, and each says so. */
  it('says the groups and the link wait for the network while offline, never reading forever', async () => {
    friendsServer();
    await openFriends();
    act(() => onlineManager.setOnline(false));

    await openSheet();

    expect(await screen.findAllByText(offlineMessage('resumes'))).toHaveLength(2);
    expect(screen.queryByText(SHEET.reading)).toBeNull();
    expect(screen.queryByText(FRIENDS_COPY.link.reading)).toBeNull();
    expect(transport.requestsTo('GET', GROUPS_PATH)).toHaveLength(0);
    expect(transport.requestsTo('GET', FRIEND_LINK_PATH)).toHaveLength(0);
  });

  it('says so when you are in no group', async () => {
    friendsServer();
    transport.on('GET', GROUPS_PATH, () => json<Wire['GroupsToAddFromResponse']>({ groups: [] }));
    await openFriends();
    await openSheet();

    expect(await screen.findByText(SHEET.none)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The link card (#756)
// ---------------------------------------------------------------------------

describe('the Add friends sheet’s link card', () => {
  const REPLACEMENT_PATH = `${FRIEND_LINK_PATH}/replacement`;
  const linkAt = (code: string) => `https://rakieta.app/f/${code}`;
  let clipboard: FakeClipboard;

  /** Your link, as `GET /friends/link` answers it — until a New link mints the next code. */
  function linkServer(codes: readonly string[] = ['tk4m9q2z', 'w8n3r5qa']) {
    let current = 0;
    const answer = () =>
      json<Wire['FriendLinkResponse']>({ code: codes[current]!, link: linkAt(codes[current]!) });
    transport.on('GET', FRIEND_LINK_PATH, answer);
    transport.on('POST', REPLACEMENT_PATH, () => {
      current += 1;
      return answer();
    });
  }

  async function openTheCard() {
    friendsServer();
    linkServer();
    clipboard = fakeClipboard();
    stubClipboard(clipboard);
    await openFriends();
    fireEvent.press(screen.getByRole('button', { name: PAGE.addLabel }));
    expect(await screen.findByRole('header', { name: SHEET.title })).toBeTruthy();
    expect(await screen.findByLabelText(friendLinkLabel(linkAt('tk4m9q2z')))).toBeTruthy();
  }

  const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

  it('shows your link under your groups, without its scheme', async () => {
    await openTheCard();

    expect(screen.getByText(LINK.title)).toBeTruthy();
    expect(screen.getByText('rakieta.app/f/tk4m9q2z')).toBeTruthy();
    // Read when the sheet opens, not with the page.
    expect(transport.requestsTo('GET', FRIEND_LINK_PATH)).toHaveLength(1);
  });

  it('copies the whole link, and says so', async () => {
    await openTheCard();

    fireEvent.press(screen.getByRole('button', { name: LINK.copyLabel }));

    await waitFor(() => expect(clipboard.text).toBe(linkAt('tk4m9q2z')));
    await waitFor(() => expect(toasts()).toEqual([[LINK.copied, 'ok']]));
  });

  it('says so when the phone would not take it', async () => {
    await openTheCard();
    clipboard.writable = false;

    fireEvent.press(screen.getByRole('button', { name: LINK.copyLabel }));

    await waitFor(() => expect(toasts()).toEqual([[LINK.notCopied, 'bad']]));
    expect(clipboard.text).toBe('');
  });

  it('asks before a New link, and Keep this link changes nothing', async () => {
    await openTheCard();

    fireEvent.press(screen.getByRole('button', { name: LINK.newLinkLabel }));
    expect(await screen.findByRole('header', { name: LINK.confirm.title })).toBeTruthy();
    expect(screen.getByText(LINK.confirm.body)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: LINK.confirm.keep }));

    await waitFor(() =>
      expect(screen.queryByRole('header', { name: LINK.confirm.title })).toBeNull(),
    );
    expect(transport.requestsTo('POST', REPLACEMENT_PATH)).toHaveLength(0);
    expect(screen.getByText('rakieta.app/f/tk4m9q2z')).toBeTruthy();
    expect(screen.queryByText(LINK.made)).toBeNull();
  });

  it('makes a New link, shows it, and says the old one no longer works', async () => {
    await openTheCard();

    fireEvent.press(screen.getByRole('button', { name: LINK.newLinkLabel }));
    fireEvent.press(await screen.findByRole('button', { name: LINK.confirm.act }));

    expect(await screen.findByText('rakieta.app/f/w8n3r5qa')).toBeTruthy();
    expect(screen.getByText(LINK.made)).toBeTruthy();
    expect(screen.queryByRole('header', { name: LINK.confirm.title })).toBeNull();
    expect(transport.requestsTo('POST', REPLACEMENT_PATH)).toHaveLength(1);

    // Copy now takes the new one.
    fireEvent.press(screen.getByRole('button', { name: LINK.copyLabel }));
    await waitFor(() => expect(clipboard.text).toBe(linkAt('w8n3r5qa')));
  });
});

/**
 * **The administrator area, walked** — the gate, the Groups tab, New official group and an official
 * group's page ([#516](https://github.com/Raketa02/Raketa/issues/516), PRD #500 stories 122–130
 * and 136; club mocks 8–11, 17–20).
 *
 * The real route tree, with the socket, the share sheet, WhatsApp and the clipboard faked at the
 * platform edge. **The club's administrator routes are answered by a small fake of the server**
 * (`club`), so a create, an approval or a removal changes what the next read says, as it would.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

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
  errorResponse,
  installTransport,
  json,
  neverResponds,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from '@/features/groups/types';

import { ADMINISTRATOR_COPY } from './administratorCopy';

const COPY = ADMINISTRATOR_COPY;

// ---------------------------------------------------------------------------
// The club, its people and its groups
// ---------------------------------------------------------------------------

const CLUB_ID = 'c0000000-0000-4000-8000-000000000033';
const CLUB = { id: CLUB_ID, name: 'Ogrody 33', sports: ['PADEL', 'TENNIS', 'SQUASH'] } as const;
const CLUB_PATH = `/api/v1/administrator/clubs/${CLUB_ID}`;
const GROUPS_PATH = `${CLUB_PATH}/groups`;

/** Marta runs Ogrody 33's WhatsApp groups and has never played on Raketa. */
const ADMINISTRATOR_ONLY: Wire['AccountProfilesSchema'] = {
  acts_as_player: false,
  administers: [{ club_id: CLUB_ID, club_name: CLUB.name }],
  pending_invitations: [],
};

interface Person {
  readonly id: string;
  readonly name: string;
  readonly levels: Readonly<Partial<Record<Wire['Sport'], number>>>;
}

function person(n: number, name: string, levels: Person['levels'] = {}): Person {
  return { id: `e0000000-0000-4000-8000-${String(n).padStart(12, '0')}`, name, levels };
}

const MICHAL = person(1, 'Michał Rogalski', { PADEL: 2.44, TENNIS: 2.6 });
const TOMEK = person(2, 'Tomek Kowal', { PADEL: 2.71, TENNIS: 3.1, SQUASH: 2.3 });
const ANIA = person(3, 'Ania Kowalczyk', { PADEL: 2.68 });
const STAS = person(4, 'Staś Wójcik', { PADEL: 2.5 });
const FILIP = person(5, 'Filip Nowak', { TENNIS: 3.0 });
const BARTEK = person(6, 'Bartek Lis', { PADEL: 2.9 });
const KUBA = person(7, 'Kuba Wróbel', { PADEL: 2.8 });

const EVERYBODY = [MICHAL, TOMEK, ANIA, STAS, FILIP, BARTEK, KUBA];

/** "Now", for *this week* — the router's fake clock is set to it before every walk. */
const NOW = '2026-09-26T12:00:00Z';

interface Stay {
  readonly who: Person;
  readonly joinedAt: string;
}

interface GroupSetup {
  readonly id: string;
  readonly name: string;
  readonly letters: string;
  readonly colour?: number;
  readonly sports?: readonly Wire['Sport'][];
  readonly policy?: Wire['JoinPolicy'];
  readonly size?: number;
  /** Newest joined first, as the server serves them. */
  readonly players?: readonly Stay[];
  /** In the order they asked. */
  readonly requests?: readonly Person[];
}

const O3_CLUB_ID = 'a0000000-0000-4000-8000-000000000001';
const OPEN_PLAY_ID = 'a0000000-0000-4000-8000-000000000002';
/** The id the fake server gives the one group a walk creates. */
const CREATED_ID = 'a0000000-0000-4000-8000-000000000100';
const LINK_OF: Readonly<Record<string, string>> = {
  [O3_CLUB_ID]: 'https://raketa.app/join/K7PQ2MXA',
  [OPEN_PLAY_ID]: 'https://raketa.app/join/R4TW9ZHB',
  [CREATED_ID]: 'https://raketa.app/join/G4H3JK2M',
};

/** *Ogrody 33 Club* as club 17 and 18 draw it: players, and Michał waiting. */
const O3_CLUB_GROUP: GroupSetup = {
  id: O3_CLUB_ID,
  name: 'Ogrody 33 Club',
  letters: 'O3',
  colour: 1,
  sports: ['PADEL', 'TENNIS', 'SQUASH'],
  policy: 'PEOPLE_I_APPROVE',
  size: 48,
  players: [
    { who: ANIA, joinedAt: '2026-09-07T18:00:00Z' },
    { who: STAS, joinedAt: '2026-09-07T10:00:00Z' },
    { who: FILIP, joinedAt: '2026-08-31T10:00:00Z' },
  ],
  requests: [MICHAL],
};

/** *Ogrody open play* (club 19): nobody waiting. */
const OPEN_PLAY_GROUP: GroupSetup = {
  id: OPEN_PLAY_ID,
  name: 'Ogrody open play',
  letters: 'Oo',
  colour: 2,
  sports: ['PADEL', 'TENNIS'],
  policy: 'ANYONE',
  size: 30,
  players: [
    { who: MICHAL, joinedAt: '2026-09-24T09:00:00Z' },
    { who: TOMEK, joinedAt: '2026-08-31T10:00:00Z' },
  ],
};

function rating(sport: Wire['Sport']): Wire['RatingResponse'] {
  return {
    sport,
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.1, high: 3.3 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

function refusal(code: string, field: string): Response {
  return json<Wire['ErrorResponse']>(
    { code, message: 'test failure', trace_id: 'trace-test', details: { field } },
    400,
  );
}

/**
 * **The club's server, faked** — the rules the routes document and nothing more: the groups the
 * administrator runs, newest created first; a create checked field by field in the form's order;
 * an approval making the person a player at once; a decline removing the request; and, once the
 * club has removed them, `not_an_administrator` on every route.
 */
function club(setups: readonly GroupSetup[] = []) {
  const state = {
    removed: false,
    groups: setups.map((setup) => ({
      id: setup.id,
      name: setup.name,
      letters: setup.letters,
      colour: setup.colour ?? 0,
      sports: [...(setup.sports ?? ['PADEL'])],
      policy: setup.policy ?? 'ANYONE',
      size: setup.size ?? 48,
      players: [...(setup.players ?? [])],
      requests: [...(setup.requests ?? [])],
    })),
  };
  type Held = (typeof state.groups)[number];

  const card = (group: Held): Wire['AdministeredGroupCardSchema'] => ({
    id: group.id,
    kind: 'OFFICIAL',
    name: group.name,
    monogram: { letters: group.letters, colour: group.colour },
    sports: group.sports,
    member_count: group.players.length,
    waiting_count: group.requests.length,
    home_club: { id: CLUB_ID, name: CLUB.name },
  });

  const page = (group: Held): Wire['AdministeredGroupResponse'] => ({
    id: group.id,
    kind: 'OFFICIAL',
    name: group.name,
    monogram: { letters: group.letters, colour: group.colour },
    sports: group.sports,
    member_count: group.players.length,
    home_club: { ...CLUB, sports: [...CLUB.sports] },
    link: LINK_OF[group.id] ?? 'https://raketa.app/join/UNKNOWN0',
    join_policy: group.policy,
    whatsapp_size: group.size,
    players: group.players.map(({ who, joinedAt }) => ({
      player_id: who.id,
      name: who.name,
      joined_at: joinedAt,
    })),
    requests: group.requests.map((who) => ({
      player_id: who.id,
      name: who.name,
      levels: (['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'] as const).flatMap((sport) => {
        const level = who.levels[sport];
        return level === undefined ? [] : [{ sport, level }];
      }),
    })),
  });

  const removed = () => errorResponse(403, 'not_an_administrator');
  const find = (id: string) => state.groups.find((group) => group.id === id);

  function create(body: Wire['CreateOfficialGroupRequest']): Response {
    const name = body.name.trim().replace(/\s+/g, ' ');
    if (name.length < 1 || name.length > 40) return refusal('group_name_invalid', 'name');
    if (
      !Number.isInteger(body.whatsapp_size) ||
      body.whatsapp_size < 2 ||
      body.whatsapp_size > 1024
    ) {
      return refusal('whatsapp_size_invalid', 'whatsapp_size');
    }
    if (body.sports.length === 0) return refusal('group_sports_required', 'sports');
    const group: Held = {
      id: CREATED_ID,
      name,
      letters: 'O3',
      colour: 4,
      sports: [...new Set(body.sports)],
      policy: body.join_policy,
      size: body.whatsapp_size,
      players: [],
      requests: [],
    };
    state.groups.unshift(group);
    return json(page(group), 201);
  }

  return {
    state,
    /** The club removes the administrator, from its website. */
    remove() {
      state.removed = true;
    },
    /** Somebody taps the link in WhatsApp and asks to join. */
    ask(groupId: string, who: Person) {
      find(groupId)?.requests.push(who);
    },
    install(transport: Transport) {
      transport.on('GET', GROUPS_PATH, () =>
        state.removed
          ? removed()
          : json<Wire['AdministeredGroupsResponse']>({
              club: { ...CLUB, sports: [...CLUB.sports] },
              groups: state.groups.map(card),
            }),
      );
      transport.on('POST', GROUPS_PATH, (request) =>
        state.removed ? removed() : create(request.body as Wire['CreateOfficialGroupRequest']),
      );
      for (const id of [O3_CLUB_ID, OPEN_PLAY_ID, CREATED_ID]) {
        transport.on('GET', `${GROUPS_PATH}/${id}`, () => {
          if (state.removed) return removed();
          const group = find(id);
          return group === undefined ? errorResponse(404, 'group_not_found') : json(page(group));
        });
        for (const who of EVERYBODY) {
          const requestPath = `${GROUPS_PATH}/${id}/requests/${who.id}`;
          transport.on('POST', `${requestPath}/approve`, () => {
            if (state.removed) return removed();
            const group = find(id);
            if (group === undefined) return errorResponse(404, 'group_not_found');
            group.requests = group.requests.filter((asking) => asking.id !== who.id);
            group.players.unshift({ who, joinedAt: NOW });
            return noContent();
          });
          transport.on('POST', `${requestPath}/decline`, () => {
            if (state.removed) return removed();
            const group = find(id);
            if (group === undefined) return errorResponse(404, 'group_not_found');
            group.requests = group.requests.filter((asking) => asking.id !== who.id);
            return noContent();
          });
        }
      }
    },
  };
}

// ---------------------------------------------------------------------------
// The walk
// ---------------------------------------------------------------------------

let transport: Transport;
let share: FakeShare;
let clipboard: FakeClipboard;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { name: 'Marta Nowak', profiles: ADMINISTRATOR_ONLY });
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

    expect(screen.getByText('Ogrody 33 · Administrator')).toBeTruthy();
  });

  // What a player owes the gate — a rating, a run — is no question this account has to answer, so
  // a read of it that fails holds nothing up.
  it('does not wait on the player’s reads', async () => {
    transport.on('GET', '/api/v1/ratings', () => errorResponse(403, 'forbidden'));
    transport.on('GET', '/api/v1/assessments/in-progress', neverResponds());

    await launchAsAdministrator();

    expect(screen.getByText('Ogrody 33 · Administrator')).toBeTruthy();
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

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('GET', GROUPS_PATH)).toHaveLength(0);
  });
});

describe('the Groups tab', () => {
  it('says there are no official groups yet, under the one button', async () => {
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
    expect(await screen.findByText('Ogrody 33 · Official')).toBeTruthy();
    expect(await screen.findByRole('header', { name: 'Ogrody 33 Club' })).toBeTruthy();
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
  fireEvent.changeText(screen.getByLabelText(COPY.newGroup.whatsAppSize), size);
  for (const sport of sports) fireEvent.press(await screen.findByRole('button', { name: sport }));
}

describe('New official group', () => {
  it('asks for a name, shows the club fixed, and offers only the club’s sports', async () => {
    await launchAsAdministrator();
    await openNewGroup();

    expect(screen.getByPlaceholderText(COPY.newGroup.namePlaceholder)).toBeTruthy();
    expect(screen.getByPlaceholderText(COPY.newGroup.whatsAppSizePlaceholder)).toBeTruthy();
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

  it('stays closed without a name, a WhatsApp group size or a sport', async () => {
    await launchAsAdministrator();
    await openNewGroup();

    expect(createDisabled()).toBe(true);
    await fillNewGroup({ name: '   ' });
    expect(createDisabled()).toBe(true);

    fireEvent.changeText(screen.getByLabelText('Name'), 'Ogrody 33 Club');
    expect(createDisabled()).toBe(false);

    // Required: an empty size is no group.
    fireEvent.changeText(screen.getByLabelText(COPY.newGroup.whatsAppSize), '');
    expect(createDisabled()).toBe(true);
    fireEvent.changeText(screen.getByLabelText(COPY.newGroup.whatsAppSize), '48');

    // Required: unticking the one sport is no group.
    fireEvent.press(screen.getByRole('button', { name: 'Padel' }));
    expect(createDisabled()).toBe(true);
  });

  it('holds the WhatsApp group size to 2–1024, and says so on the field', async () => {
    await launchAsAdministrator();
    await openNewGroup();
    await fillNewGroup();
    const size = screen.getByLabelText(COPY.newGroup.whatsAppSize);

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
  it('draws club 11’s link card, and never a posted tag', async () => {
    await openGroup(O3_CLUB_GROUP);

    expect(screen.getByText(COPY.group.linkLine)).toBeTruthy();
    expect(screen.getByLabelText('Group link, raketa.app/join/K7PQ2MXA')).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.group.post })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.group.copy })).toBeTruthy();
    expect(screen.queryByText(/posted/i)).toBeNull();
    expect(screen.queryByText(/Post again/i)).toBeNull();
  });

  it('opens WhatsApp with the message typed', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: COPY.group.post }));

    await waitFor(() =>
      expect(share.whatsApped).toEqual([
        'Join Ogrody 33 Club on Raketa: https://raketa.app/join/K7PQ2MXA',
      ]),
    );
    expect(share.shared).toEqual([]);
  });

  it('opens the share sheet instead on a phone without WhatsApp', async () => {
    share.whatsAppInstalled = false;
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: COPY.group.post }));

    await waitFor(() =>
      expect(share.shared).toEqual([
        'Join Ogrody 33 Club on Raketa: https://raketa.app/join/K7PQ2MXA',
      ]),
    );
    expect(share.whatsApped).toEqual([]);
  });

  it('copies the bare link, and says so', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: COPY.group.copy }));

    await waitFor(() => expect(clipboard.text).toBe('https://raketa.app/join/K7PQ2MXA'));
    await waitFor(() => expect(toasts()).toEqual([['Link copied', 'ok']]));
  });

  it('counts the players, stacks their faces, and lists them newest first with the day', async () => {
    await openGroup(OPEN_PLAY_GROUP);

    expect(
      screen.getByLabelText('2 players, anyone with the link joins · 7% of the WhatsApp group'),
    ).toBeTruthy();
    const faces = screen
      .queryAllByTestId(/^players-face-/, { includeHiddenElements: true })
      .map((node) => (node.props.testID as string).replace('players-face-', ''));
    expect(faces).toEqual([MICHAL.id, TOMEK.id]);

    const rows = screen
      .queryAllByTestId(/^player-/)
      .map((node) => node.props.accessibilityLabel as string);
    expect(rows).toEqual(['Michał Rogalski, joined this week', 'Tomek Kowal, joined 31 Aug']);
    // A row opens nothing, and nobody can be removed.
    expect(screen.queryByRole('button', { name: /Michał Rogalski/ })).toBeNull();
    expect(screen.queryByText(/remove/i)).toBeNull();
  });

  it('draws the join rule and the WhatsApp share under nobody yet', async () => {
    await openGroup({ ...O3_CLUB_GROUP, players: [], requests: [] });

    expect(
      screen.getByLabelText('0 players, you approve joins · 0% of the WhatsApp group'),
    ).toBeTruthy();
    expect(screen.queryAllByTestId(/^player-/)).toHaveLength(0);
    expect(screen.queryByText(/^Want to join/)).toBeNull();
  });

  it('counts past five faces, and past the whole WhatsApp group', async () => {
    const crowd = EVERYBODY.map((who, at) => ({
      who,
      joinedAt: `2026-08-${String(20 - at).padStart(2, '0')}T10:00:00Z`,
    }));
    await openGroup({ ...OPEN_PLAY_GROUP, size: 6, players: crowd });

    expect(
      screen.getByLabelText('7 players, anyone with the link joins · 117% of the WhatsApp group'),
    ).toBeTruthy();
    expect(screen.getByText('+2')).toBeTruthy();
  });

  it('has no way to delete or leave the group', async () => {
    await openGroup(O3_CLUB_GROUP);

    expect(screen.queryByRole('button', { name: /delete|leave/i })).toBeNull();
  });
});

describe('Want to join', () => {
  it('lists who is asking, with every sport they are rated in', async () => {
    await openGroup(O3_CLUB_GROUP);

    expect(screen.getByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
    expect(screen.getByLabelText('Michał Rogalski, Padel 2,44 · Tennis 2,60')).toBeTruthy();
  });

  it('admits the person approved, who tops the players list, this week', async () => {
    await openGroup(O3_CLUB_GROUP);

    fireEvent.press(screen.getByRole('button', { name: 'Approve Michał Rogalski' }));

    await waitFor(() => expect(screen.queryByText(/^Want to join/)).toBeNull());
    expect(
      await screen.findByLabelText('4 players, you approve joins · 8% of the WhatsApp group'),
    ).toBeTruthy();
    const rows = screen
      .queryAllByTestId(/^player-/)
      .map((node) => node.props.accessibilityLabel as string);
    expect(rows[0]).toBe('Michał Rogalski, joined this week');
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
    expect(screen.getByLabelText(/^3 players,/)).toBeTruthy();
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
      name: 'Marta Nowak',
      profiles: { ...ADMINISTRATOR_ONLY, administers: [] },
    });
    const ratingsBefore = transport.requestsTo('GET', '/api/v1/ratings').length;
    await act(async () => {
      await queryClient.refetchQueries();
    });

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(toasts()).toEqual([
      ['Ogrody 33 removed you as an administrator. You’re signed out.', 'base'],
    ]);
    // Never handed to the gate, which would have asked the player's reads on the way to welcome.
    expect(transport.requestsTo('GET', '/api/v1/ratings')).toHaveLength(ratingsBefore);
  });
});

describe('removed, an account that also plays', () => {
  it('is told, and moved to its player side rather than signed out', async () => {
    stubGate(transport, {
      name: 'Tomek Kowal',
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
    expect(await screen.findByRole('header', { name: COPY.you.title })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'You', selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeTruthy();

    fireEvent.press(screen.getByRole('tab', { name: 'Groups' }));
    await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
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

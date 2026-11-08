/**
 * **A group's Info and Members, walked** — Info opened from the page's header (Q125), the link
 * card, *Want to join* and the Owner's count on the tile, the members row, Edit group, leaving and
 * deleting, the re-reads, and Members with its press and hold
 * ([#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500 stories 71–84; play mocks
 * 57–61, club 20).
 *
 * The real route tree, with the socket, the share sheet and the clipboard faked at the platform
 * edge. **The group's routes are answered by a small fake of the server** (`crew`), so an approval,
 * an edit or a departure changes what the next read says, as it would — the page, Members and the
 * Groups list are re-read after each and have to agree with it.
 */

import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { RefreshControl, StyleSheet } from 'react-native';

import { sportColour } from '@/features/onboarding/types';
import {
  FULL_RECORD,
  OWN_RECORD_TITLE,
  RECORD_TITLE,
  RELIABILITY_BAND_WORD,
  countLines,
} from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import {
  GATE_USER,
  launchSignedIn,
  MY_GROUPS_PATH,
  resetClipboard,
  resetShare,
  stubClipboard,
  stubFriends,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
  stubShare,
} from '@/test-support/onboardingRouter';
import {
  fakeClipboard,
  fakeShare,
  type FakeClipboard,
  type FakeShare,
} from '@/test-support/platform';
import { stubGroupDeck } from '@/test-support/groupDeck';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  neverResponds,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from './groupsPresentation';

const COPY = GROUPS_COPY;

// ---------------------------------------------------------------------------
// The people, and the group
// ---------------------------------------------------------------------------

interface Person {
  readonly id: string;
  readonly name: string;
  readonly levels: Readonly<Partial<Record<Wire['Sport'], number>>>;
  /** Player reliability in points — everyone has one, 100 to start (ADR-0195 §1). */
  readonly score: number;
  readonly band: Wire['ReliabilityBand'];
}

function person(
  n: number,
  name: string,
  levels: Person['levels'],
  score = 100,
  band: Wire['ReliabilityBand'] = 'VERY_HIGH',
): Person {
  const id = `e0000000-0000-4000-8000-${String(n).padStart(12, '0')}`;
  return { id, name, levels, score, band };
}

/** The reader — `GET /users/me`'s id, which is how the rows know which one is *You*. */
const ME: Person = {
  id: GATE_USER.id,
  name: 'Tomek Kowal',
  levels: { PADEL: 2.71, TENNIS: 3.1 },
  score: 92,
  band: 'VERY_HIGH',
};
const KAROL = person(1, 'Karol Tomczak', { PADEL: 2.75, TENNIS: 3.0 }, 75, 'HIGH');
const EWA = person(2, 'Ewa Mazur', { PADEL: 2.6 }, 91);
const ZOFIA = person(3, 'Zofia Bąk', { PADEL: 2.69 }, 95);
const ANIA = person(4, 'ania.k', { PADEL: 2.68 }, 99);
const KUBA = person(5, 'Kuba Wróbel', { PADEL: 2.8 }, 96);
/** Rated in padel and nothing has happened to her yet: 100, like everybody at the start. */
const OLA = person(6, 'Ola Nowak', { PADEL: 2.64 });
/** Plays tennis and not padel: in the group, and not on its padel Members. */
const MAREK = person(7, 'Marek Zając', { TENNIS: 3.2 }, 91);
const MICHAL = person(8, 'Michał Rogalski', { PADEL: 2.44, TENNIS: 2.6 });
const TOMASZ = person(9, 'Tomasz Król', { PADEL: 2.71, TENNIS: 3.1, SQUASH: 2.3, BADMINTON: 2.05 });

const EVERYBODY = [ME, KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK, MICHAL, TOMASZ];

const GROUP_ID = 'a0000000-0000-4000-8000-000000000005';
const GROUP_PATH = `/api/v1/groups/${GROUP_ID}`;
const LINK = 'https://raketa.app/join/K7PQ2MXA';
const HOME_CLUB = { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' };

const WIRE_SPORTS: readonly Wire['Sport'][] = ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'];
const SEATS: Readonly<Record<Wire['Sport'], number>> = {
  PADEL: 4,
  TENNIS: 2,
  SQUASH: 2,
  BADMINTON: 4,
};

function face(who: Person): Wire['GroupPersonSchema'] {
  return { player_id: who.id, nickname: who.name };
}

interface CrewSetup {
  readonly name?: string;
  /** In the order they joined, the Owner first. */
  readonly members: readonly Person[];
  readonly owner?: Person;
  readonly policy?: Wire['JoinPolicy'];
  /** In the order they asked. */
  readonly requests?: readonly Person[];
}

/**
 * **The group's server, faked** — the rules the routes document and nothing more: Members in
 * the order the reader, the Owner, then newest joined first; the members row's five faces in that
 * order without the reader; a switch to Anyone admitting everybody waiting; an Owner leaving
 * passing the group to whoever has been in longest; Delete only for an Owner alone.
 */
function crew({
  name = 'Kazimierz crew',
  members,
  owner = members[0] ?? ME,
  policy = 'ANYONE',
  requests = [],
}: CrewSetup) {
  const state = {
    name,
    policy,
    ownerId: owner.id,
    stays: [...members],
    waiting: [...requests],
    deleted: false,
  };

  const joinedAt = (who: Person) =>
    `2026-09-${String(10 + EVERYBODY.indexOf(who)).padStart(2, '0')}T10:00:00Z`;
  const has = (who: Person) => state.stays.some((stay) => stay.id === who.id);
  const rated = (sport: Wire['Sport']) =>
    state.stays.filter((who) => who.levels[sport] !== undefined);
  const theOwner = () => state.stays.find((who) => who.id === state.ownerId);
  /** Everybody but the reader: the Owner, then newest joined first. */
  const others = () => {
    const rest = state.stays
      .filter((who) => who.id !== ME.id && who.id !== state.ownerId)
      .reverse();
    const lead = theOwner();
    return lead === undefined || lead.id === ME.id ? rest : [lead, ...rest];
  };

  const group = (): Wire['GroupResponse'] => ({
    id: GROUP_ID,
    kind: 'PLAYER',
    name: state.name,
    monogram: { letters: 'Kc', colour: 1 },
    sports: WIRE_SPORTS.filter((sport) => rated(sport).length >= 2),
    member_count: state.stays.length,
    home_club: HOME_CLUB,
    link: LINK,
    join_policy: state.policy,
    is_owner: state.ownerId === ME.id,
    administrator_nickname: null,
    is_administrator: false,
    rated_by_sport: WIRE_SPORTS.map((sport) => ({
      sport,
      rated_count: rated(sport).length,
      first_rated: rated(sport).slice(0, SEATS[sport]).map(face),
    })),
    member_faces: others().slice(0, 5).map(face),
  });

  const membersFor = (sport: Wire['Sport']): Wire['GroupMemberSchema'][] =>
    [ME, ...others()]
      .filter((who) => has(who) && who.levels[sport] !== undefined)
      .map((who) => ({
        player_id: who.id,
        nickname: who.name,
        level: who.levels[sport] ?? 0,
        player_score: who.score,
        reliability_band: who.band,
        is_owner: who.id === state.ownerId,
        is_administrator: false,
        joined_at: joinedAt(who),
        relation: 'NONE',
      }));

  const requestOf = (who: Person): Wire['JoinRequestSchema'] => ({
    player_id: who.id,
    nickname: who.name,
    levels: WIRE_SPORTS.flatMap((sport) => {
      const level = who.levels[sport];
      return level === undefined ? [] : [{ sport, level }];
    }),
  });

  const myGroups = (): Wire['MyGroupSchema'][] => {
    if (state.deleted || !has(ME)) return [];
    const { id, kind, name: title, monogram, sports, member_count, home_club } = group();
    return [{ id, kind, name: title, monogram, sports, member_count, home_club }];
  };

  /** Somebody leaves — the handover to whoever has been in longest is the server's. */
  const leave = (who: Person): Response => {
    if (who.id === state.ownerId && state.stays.length === 1) {
      return errorResponse(409, 'lone_owner_cannot_leave');
    }
    state.stays = state.stays.filter((stay) => stay.id !== who.id);
    if (who.id === state.ownerId) state.ownerId = state.stays[0]?.id ?? '';
    return noContent();
  };

  return {
    state,
    /** Somebody leaves on their own phone. */
    leave,
    install(transport: Transport) {
      transport.on('GET', MY_GROUPS_PATH, () => json({ groups: myGroups() }));
      transport.on('GET', GROUP_PATH, () =>
        state.deleted || !has(ME) ? errorResponse(404, 'group_not_found') : json(group()),
      );
      stubGroupDeck(transport, GROUP_ID);
      transport.on('GET', `${GROUP_PATH}/members`, (request) => {
        const sport = (new URLSearchParams(request.path.split('?')[1]).get('sport') ??
          'PADEL') as Wire['Sport'];
        return json<Wire['GroupMembersResponse']>({ sport, members: membersFor(sport) });
      });
      transport.on('GET', `${GROUP_PATH}/requests`, () =>
        state.ownerId === ME.id
          ? json<Wire['JoinRequestsResponse']>({ requests: state.waiting.map(requestOf) })
          : errorResponse(403, 'not_the_group_owner'),
      );
      for (const who of EVERYBODY) {
        transport.on('POST', `${GROUP_PATH}/requests/${who.id}/approve`, () => {
          state.waiting = state.waiting.filter((asking) => asking.id !== who.id);
          state.stays.push(who);
          return noContent();
        });
        transport.on('POST', `${GROUP_PATH}/requests/${who.id}/decline`, () => {
          state.waiting = state.waiting.filter((asking) => asking.id !== who.id);
          return noContent();
        });
      }
      transport.on('PUT', `${GROUP_PATH}/details`, (request) => {
        const body = request.body as Wire['EditGroupRequest'];
        const admitted = body.join_policy === 'ANYONE' ? state.waiting : [];
        state.stays.push(...admitted);
        state.waiting = body.join_policy === 'ANYONE' ? [] : state.waiting;
        state.name = body.name;
        state.policy = body.join_policy;
        return json<Wire['EditedGroupResponse']>({ group: group(), admitted: admitted.map(face) });
      });
      transport.on('DELETE', `${GROUP_PATH}/membership`, () => leave(ME));
      transport.on('DELETE', GROUP_PATH, () => {
        if (state.stays.length > 1) return errorResponse(409, 'group_has_other_members');
        state.deleted = true;
        return noContent();
      });
    },
  };
}

/** Kazimierz crew as play 58 draws it: eight members, Karol its Owner. */
const KAZIMIERZ = [KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK, ME];

// ---------------------------------------------------------------------------
// The walk
// ---------------------------------------------------------------------------

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

let transport: Transport;
let share: FakeShare;
let clipboard: FakeClipboard;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, {
    ratings: [rating('PADEL', 2.71), rating('TENNIS', 3.1)],
    hasPlayerProfile: true,
  });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  // The Friends tab reads the picker's list for its court's faces (#757).
  stubFriends(transport);
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

/** A tab by its name — the start of it: Games and Fill in add their counts. */
const tab = (name: string, selected?: boolean) =>
  screen.findByRole('button', {
    name: new RegExp(`^${name}`),
    ...(selected === undefined ? {} : { selected }),
  });

const PAGE_PATH = `/play/group/${GROUP_ID}`;
const INFO_PATH = `${PAGE_PATH}/info`;

/** The page's header, by what it opens — the list's card under the page is named by the group too. */
const pageHeader = () => screen.findByHintText(COPY.group.openInfo);

/** Serve the group and land on its page. */
async function openPage(setup: CrewSetup) {
  const server = crew(setup);
  server.install(transport);
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(
    await screen.findByRole('button', { name: new RegExp(`^${server.state.name},`) }),
  );
  await waitFor(() => expect(screen).toHavePathname(PAGE_PATH));
  return server;
}

/** Open Info from the page's header (Q125) — its own screen, headed by the group. */
async function openInfoFromThePage(name = 'Kazimierz crew') {
  fireEvent.press(await pageHeader());
  await waitFor(() => expect(screen).toHavePathname(INFO_PATH));
  expect(await screen.findByRole('header', { name: new RegExp(`^${name}`) })).toBeTruthy();
}

/** Serve the group, land on its page and open Info. */
async function openInfo(setup: CrewSetup) {
  const server = await openPage(setup);
  await openInfoFromThePage(server.state.name);
  return server;
}

async function backToThePage() {
  fireEvent.press(await screen.findByRole('button', { name: COPY.info.back }));
  await waitFor(() => expect(screen).toHavePathname(PAGE_PATH));
}

const membersRow = (label: RegExp) => screen.findByRole('button', { name: label });
const rowFaces = () =>
  screen
    .queryAllByTestId(/^members-row-face-/, { includeHiddenElements: true })
    .map((node) => (node.props.testID as string).replace('members-row-face-', ''));

async function openMembers() {
  fireEvent.press(await membersRow(/ members?, /));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP_ID}/members`));
  expect(await screen.findByRole('header', { name: /^Members/ })).toBeTruthy();
}

/** The tags under a request's name, left to right. */
function requestTagTexts(who: Person): string[] {
  return within(screen.getByTestId(`join-request-${who.id}`))
    .queryAllByTestId(/^request-tag/)
    .map((node) => node.props.children as string);
}

/** Members' rows, top to bottom, by whose they are. */
const memberIds = () =>
  screen
    .queryAllByTestId(/^member-/)
    .map((node) => (node.props.testID as string).replace('member-', ''));

// ---------------------------------------------------------------------------

describe('the link card', () => {
  it('draws the link in mono without its scheme, with Share and Copy beside it', async () => {
    await openInfo({ members: KAZIMIERZ });

    expect(await screen.findByLabelText('Group link, raketa.app/join/K7PQ2MXA')).toBeTruthy();
    expect(screen.getByText('raketa.app/join/K7PQ2MXA')).toBeTruthy();
    // Drawn short, spoken whole.
    expect(screen.getByText(COPY.link.shareShort)).toBeTruthy();
    expect(screen.getByText(COPY.link.copyShort)).toBeTruthy();
  });

  it('opens the share sheet with the link, and copies it', async () => {
    await openInfo({ members: KAZIMIERZ });

    fireEvent.press(await screen.findByRole('button', { name: COPY.link.share }));
    await waitFor(() => expect(share.shared).toEqual([`Join Kazimierz crew on Raketa: ${LINK}`]));

    fireEvent.press(screen.getByRole('button', { name: COPY.link.copy }));
    await waitFor(() => expect(clipboard.text).toBe(LINK));
    await waitFor(() => expect(toasts()).toEqual([[COPY.link.copied, 'ok']]));
  });
});

describe('the members row', () => {
  it('stacks five faces, the Owner first, and counts the rest', async () => {
    await openInfo({ members: KAZIMIERZ });

    expect(await membersRow(/^8 members, plays Padel, Tennis, anyone can join$/)).toBeTruthy();
    // Everybody but the reader — the Owner, then newest joined first — five of them.
    expect(rowFaces()).toEqual([KAROL.id, MAREK.id, OLA.id, KUBA.id, ANIA.id]);
    expect(screen.getByText('+2')).toBeTruthy();
    expect(screen.getByText(COPY.info.anyoneCanJoin)).toBeTruthy();
  });

  it('draws your own face when you are alone, and nothing more', async () => {
    await openInfo({ name: 'My raketa group', members: [ME] });

    expect(await membersRow(/^1 member, anyone can join$/)).toBeTruthy();
    expect(rowFaces()).toEqual([ME.id]);
    expect(screen.queryByText(/^\+\d/)).toBeNull();
  });

  it('says who approves joins, from where the reader stands', async () => {
    await openInfo({ members: KAZIMIERZ, policy: 'PEOPLE_I_APPROVE' });

    expect(await screen.findByText(COPY.info.ownerApproves)).toBeTruthy();
  });

  it('opens Members', async () => {
    await openInfo({ members: KAZIMIERZ });

    await openMembers();
  });
});

describe('Want to join', () => {
  const OWNED = [ME, KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK];

  it('lists who is asking, with every sport they are rated in, for the Owner', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });

    expect(await screen.findByRole('header', { name: 'Want to join · 2' })).toBeTruthy();
    expect(screen.getByLabelText('Michał Rogalski, Padel 2,44 · Tennis 2,60')).toBeTruthy();
    expect(
      screen.getByLabelText('Tomasz Król, Padel 2,71 · Tennis 3,10 · Squash 2,30 · Badminton 2,05'),
    ).toBeTruthy();
    // Between the link card and the members row.
    const order = screen
      .getAllByText(/^(raketa\.app\/join\/K7PQ2MXA|Want to join · 2|8 members)$/)
      .map((node) => node.props.children as string);
    expect(order).toEqual(['raketa.app/join/K7PQ2MXA', 'Want to join · 2', '8 members']);
  });

  // #529: four sports ran the row onto three lines. Two short tags, the rest as one +N tag, and
  // every sport still spoken in full.
  it('draws two sports as short tags and counts the rest, speaking every one', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });
    await screen.findByRole('header', { name: 'Want to join · 2' });

    expect(requestTagTexts(MICHAL)).toEqual(['Pad 2,44', 'Ten 2,60']);
    expect(requestTagTexts(TOMASZ)).toEqual(['Pad 2,71', 'Ten 3,10', '+2']);
    expect(screen.queryByText(/Squash|Badminton/)).toBeNull();
    expect(
      screen.getByLabelText('Tomasz Król, Padel 2,71 · Tennis 3,10 · Squash 2,30 · Badminton 2,05'),
    ).toBeTruthy();
  });

  // 2026-10-01: the sports are the dot and the text, and the +N the text alone — no tag box.
  it('draws each sport as its dot and its text, and the count as text, with no tag around either', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [TOMASZ] });
    await screen.findByRole('header', { name: 'Want to join · 1' });

    const row = within(screen.getByTestId(`join-request-${TOMASZ.id}`));
    const fills = row
      .getAllByTestId(/^request-(sport|tag)/, { includeHiddenElements: true })
      .map((node) => StyleSheet.flatten(node.props.style)?.backgroundColor);
    // Two dots in the sports' own colours, and nothing else on the line carries a fill.
    expect(fills.filter((fill) => fill !== undefined)).toEqual([
      sportColour('padel'),
      sportColour('tennis'),
    ]);
  });

  it('is never asked for by anybody but the Owner', async () => {
    await openInfo({ members: KAZIMIERZ, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL] });

    await membersRow(/^8 members/);
    expect(screen.queryByText(/^Want to join/)).toBeNull();
    expect(transport.requestsTo('GET', `${GROUP_PATH}/requests`)).toHaveLength(0);
  });

  it('draws nothing while nobody is waiting', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE' });

    await membersRow(/^8 members/);
    // Once for the tile's count as the page opened, and again as Info opened.
    await waitFor(() =>
      expect(transport.requestsTo('GET', `${GROUP_PATH}/requests`)).toHaveLength(2),
    );
    expect(screen.queryByText(/^Want to join/)).toBeNull();
  });

  it('admits the person approved at once, and every count says so', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });

    fireEvent.press(await screen.findByRole('button', { name: 'Approve Michał Rogalski' }));

    expect(await screen.findByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
    expect(screen.queryByLabelText(/^Michał Rogalski,/)).toBeNull();
    expect(await membersRow(/^9 members,/)).toBeTruthy();
    expect(await screen.findByText('9 members · Centrum Ruchu')).toBeTruthy();
    expect(
      transport.requestsTo('POST', `${GROUP_PATH}/requests/${MICHAL.id}/approve`),
    ).toHaveLength(1);
  });

  it('declines at once and admits nobody, and goes when the queue is empty', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [TOMASZ] });

    fireEvent.press(await screen.findByRole('button', { name: 'Decline Tomasz Król' }));

    await waitFor(() => expect(screen.queryByText(/^Want to join/)).toBeNull());
    expect(
      transport.requestsTo('POST', `${GROUP_PATH}/requests/${TOMASZ.id}/decline`),
    ).toHaveLength(1);
    expect(await membersRow(/^8 members,/)).toBeTruthy();
  });

  // The answer ends the request whatever the server does, so nothing waits on the reply.
  it('takes the row before the answer lands', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });
    transport.on('POST', `${GROUP_PATH}/requests/${TOMASZ.id}/decline`, neverResponds());

    fireEvent.press(await screen.findByRole('button', { name: 'Decline Tomasz Król' }));

    await waitFor(() => expect(screen.queryByLabelText(/^Tomasz Król,/)).toBeNull());
    expect(screen.getByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
  });

  // Two answers in flight: a refusal of one puts back that row, never the other's.
  it('puts back only the refused row while another answer is on its way', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });
    transport.on('POST', `${GROUP_PATH}/requests/${TOMASZ.id}/decline`, neverResponds());
    let refuse: (response: Response) => void = () => undefined;
    transport.on(
      'POST',
      `${GROUP_PATH}/requests/${MICHAL.id}/approve`,
      () => new Promise<Response>((resolve) => (refuse = resolve)),
    );

    fireEvent.press(await screen.findByRole('button', { name: 'Approve Michał Rogalski' }));
    await waitFor(() => expect(screen.queryByLabelText(/^Michał Rogalski,/)).toBeNull());
    fireEvent.press(await screen.findByRole('button', { name: 'Decline Tomasz Król' }));
    await waitFor(() => expect(screen.queryByLabelText(/^Tomasz Król,/)).toBeNull());
    await act(async () => refuse(errorResponse(403, 'not_the_group_owner')));

    expect(await screen.findByLabelText(/^Michał Rogalski,/)).toBeTruthy();
    expect(screen.queryByLabelText(/^Tomasz Król,/)).toBeNull();
  });

  it('puts the row back and says why when the answer is refused', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL] });
    transport.on('POST', `${GROUP_PATH}/requests/${MICHAL.id}/approve`, () =>
      errorResponse(403, 'not_the_group_owner'),
    );

    fireEvent.press(await screen.findByRole('button', { name: 'Approve Michał Rogalski' }));

    await waitFor(() =>
      expect(toasts()).toEqual([['Only the group’s owner answers requests.', 'bad']]),
    );
    expect(await screen.findByLabelText(/^Michał Rogalski,/)).toBeTruthy();
  });
});

// #529 D6: the Owner could not tell from the page that anybody was waiting. Q125 moved the count
// from the Info tab to the group's tile.
describe('the Owner’s count on the tile', () => {
  const OWNED = [ME, KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK];
  const tileCount = (count: string) =>
    within(screen.getByTestId('group-header-tile')).queryByText(count, {
      includeHiddenElements: true,
    });

  it('says how many are waiting to join on the page’s header, from any tab', async () => {
    await openPage({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });

    const waiting = 'Kazimierz crew, 8 members · Centrum Ruchu, 2 requests waiting';
    expect(await screen.findByRole('button', { name: waiting })).toBeTruthy();
    expect(tileCount('2')).toBeTruthy();

    fireEvent.press(await tab('Friends'));
    await tab('Friends', true);
    expect(screen.getByRole('button', { name: waiting })).toBeTruthy();
    expect(tileCount('2')).toBeTruthy();
  });

  it('counts down as the Owner answers on Info, and the page says so on the way back', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });

    fireEvent.press(await screen.findByRole('button', { name: 'Approve Michał Rogalski' }));
    expect(
      await screen.findByRole('header', {
        name: 'Kazimierz crew, 9 members · Centrum Ruchu, 1 request waiting',
      }),
    ).toBeTruthy();
    await backToThePage();
    expect(
      await screen.findByRole('button', {
        name: 'Kazimierz crew, 9 members · Centrum Ruchu, 1 request waiting',
      }),
    ).toBeTruthy();
    expect(tileCount('1')).toBeTruthy();

    await openInfoFromThePage();
    fireEvent.press(await screen.findByRole('button', { name: 'Decline Tomasz Król' }));
    await waitFor(() => expect(screen.queryByText(/^Want to join/)).toBeNull());
    await backToThePage();

    // The drawn words are the whole name again, and nothing is on the tile.
    await waitFor(async () =>
      expect((await pageHeader()).props.accessibilityLabel).toBeUndefined(),
    );
    expect(tileCount('1')).toBeNull();
  });

  it('is nobody’s but the Owner’s', async () => {
    await openPage({ members: KAZIMIERZ, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL] });

    expect((await pageHeader()).props.accessibilityLabel).toBeUndefined();
    expect(tileCount('1')).toBeNull();
    expect(transport.requestsTo('GET', `${GROUP_PATH}/requests`)).toHaveLength(0);
  });
});

describe('the Info screen', () => {
  const OWNED = [ME, KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK];

  // Q125: the page's header without the sport pill, and not a door to anything.
  it('is headed by the page’s header without the pill, and the header presses nothing', async () => {
    await openInfo({ members: KAZIMIERZ });

    const header = screen.getByRole('header', { name: /^Kazimierz crew/ });
    expect(within(header).getByText('8 members · Centrum Ruchu')).toBeTruthy();
    expect(screen.getByTestId('group-header-tile')).toBeTruthy();
    expect(screen.queryByLabelText(/^Sport: /)).toBeNull();
    expect(screen.queryByHintText(COPY.group.openInfo)).toBeNull();
  });

  it('draws the link card, Want to join, the members row and Edit group, in that order', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL] });
    await screen.findByRole('header', { name: 'Want to join · 1' });

    const names = within(screen.getByTestId('group-info-body'))
      .getAllByRole('button')
      .map((node) => (node.props.accessibilityLabel as string | undefined) ?? '');
    const at = (name: RegExp) => names.findIndex((each) => name.test(each));
    expect(at(/^Share the link$/)).toBeGreaterThanOrEqual(0);
    expect(at(/^Share the link$/)).toBeLessThan(at(/^Approve Michał Rogalski$/));
    expect(at(/^Approve Michał Rogalski$/)).toBeLessThan(at(/^8 members, /));
    expect(at(/^8 members, /)).toBeLessThan(at(/^Edit group/));
  });
});

describe('pulling Info', () => {
  const OWNED = [ME, KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK];
  const infoBody = () => within(screen.getByTestId('group-info-body'));
  const pull = () => fireEvent(infoBody().UNSAFE_getByType(RefreshControl), 'refresh');

  // #529: a request that arrived while the page was open reached it only by leaving and coming back.
  it('re-reads the group and who is waiting', async () => {
    const server = await openInfo({
      members: OWNED,
      policy: 'PEOPLE_I_APPROVE',
      requests: [MICHAL],
    });
    expect(await screen.findByRole('header', { name: 'Want to join · 1' })).toBeTruthy();

    // Tomasz asks on his phone, and Karol leaves on his.
    server.state.waiting.push(TOMASZ);
    server.leave(KAROL);
    await act(async () => {
      pull();
    });

    expect(await screen.findByRole('header', { name: 'Want to join · 2' })).toBeTruthy();
    expect(
      await screen.findByRole('header', {
        name: 'Kazimierz crew, 7 members · Centrum Ruchu, 2 requests waiting',
      }),
    ).toBeTruthy();
    expect(await membersRow(/^7 members,/)).toBeTruthy();
    await waitFor(() =>
      expect(infoBody().UNSAFE_getByType(RefreshControl).props.refreshing).toBe(false),
    );
  });
});

// Games and Fill in pull on the page (`groupGames`, `groupFillIn`); Friends, drawn by the page's
// scroller too, does not.
describe('pulling the page', () => {
  it('is not Friends’', async () => {
    await openPage({ members: KAZIMIERZ });
    fireEvent.press(await tab('Friends'));
    await tab('Friends', true);

    expect(
      within(screen.getByTestId('group-page-body')).UNSAFE_queryByType(RefreshControl),
    ).toBeNull();
  });
});

// #529 F2: what another phone changed reached Info only by a pull. Opening it, and coming back to
// it, are looks too (Q125).
describe('Info re-reads', () => {
  const OWNED = [ME, KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK];

  it('the group and who is waiting when it opens', async () => {
    const server = await openPage({
      members: OWNED,
      policy: 'PEOPLE_I_APPROVE',
      requests: [MICHAL],
    });
    await screen.findByRole('button', { name: /, 1 request waiting$/ });

    // Tomasz asks on his phone, and Karol leaves on his, while this one is on Games.
    server.state.waiting.push(TOMASZ);
    server.leave(KAROL);
    await openInfoFromThePage();

    expect(await screen.findByRole('header', { name: 'Want to join · 2' })).toBeTruthy();
    expect(await membersRow(/^7 members,/)).toBeTruthy();
  });

  it('them on the way back from Members', async () => {
    const server = await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE' });
    await openMembers();

    server.state.waiting.push(TOMASZ);
    fireEvent.press(screen.getByRole('button', { name: COPY.members.back }));
    await waitFor(() => expect(screen).toHavePathname(INFO_PATH));

    expect(await screen.findByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
  });

  it('them on the way back from Edit group', async () => {
    const server = await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE' });
    fireEvent.press(await screen.findByRole('button', { name: /^Edit group,/ }));
    await waitFor(() => expect(screen).toHavePathname(`${PAGE_PATH}/edit`));

    server.state.waiting.push(TOMASZ);
    fireEvent.press(await screen.findByRole('button', { name: COPY.editGroup.back }));
    await waitFor(() => expect(screen).toHavePathname(INFO_PATH));

    expect(await screen.findByRole('header', { name: 'Want to join · 1' })).toBeTruthy();
  });

  // Only Info re-read on a return, and Info is its own screen now: the page reads nothing on the
  // way back from it.
  it('alone — the page reads nothing on the way back from it', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE' });
    await screen.findByRole('header', { name: /^Kazimierz crew/ });
    const reads = () =>
      transport.requestsTo('GET', GROUP_PATH).length +
      transport.requestsTo('GET', `${GROUP_PATH}/requests`).length;
    await waitFor(() => expect(transport.requestsTo('GET', GROUP_PATH)).toHaveLength(2));
    const before = reads();

    await backToThePage();
    await act(async () => {
      await Promise.resolve();
    });

    expect(reads()).toBe(before);
  });
});

describe('Edit group', () => {
  const OWNED = [ME, KAROL, EWA, ZOFIA, ANIA, KUBA, OLA, MAREK];

  async function openEdit() {
    fireEvent.press(await screen.findByRole('button', { name: /^Edit group,/ }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP_ID}/edit`));
    expect(await screen.findByRole('header', { name: COPY.editGroup.title })).toBeTruthy();
  }

  it('is the Owner’s, above the way out', async () => {
    await openInfo({ members: OWNED });

    expect(
      await screen.findByRole('button', { name: 'Edit group, Name and who can join' }),
    ).toBeTruthy();
  });

  it('is nobody else’s', async () => {
    await openInfo({ members: KAZIMIERZ });

    await membersRow(/^8 members/);
    expect(screen.queryByRole('button', { name: /^Edit group/ })).toBeNull();
  });

  it('renames the group, and Info and the page say so on the way back', async () => {
    await openInfo({ members: OWNED });
    await openEdit();

    // It opens on what the group says, with nothing to save — and, #529, no note under Who can
    // join: the Owner is past choosing what a group is.
    expect(screen.getByDisplayValue('Kazimierz crew')).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.editGroup.saved, disabled: true })).toBeTruthy();
    expect(screen.queryByText(COPY.newGroup.noSportNote)).toBeNull();

    fireEvent.changeText(screen.getByDisplayValue('Kazimierz crew'), 'Kazimierz padel');
    fireEvent.press(screen.getByRole('button', { name: COPY.editGroup.save }));

    expect(
      await screen.findByRole('button', { name: COPY.editGroup.saved, disabled: true }),
    ).toBeTruthy();
    expect(transport.requestsTo('PUT', `${GROUP_PATH}/details`).map((r) => r.body)).toEqual([
      { name: 'Kazimierz padel', join_policy: 'ANYONE' },
    ]);

    fireEvent.press(screen.getByRole('button', { name: COPY.editGroup.back }));
    await waitFor(() => expect(screen).toHavePathname(INFO_PATH));
    expect(await screen.findByRole('header', { name: /^Kazimierz padel/ })).toBeTruthy();
    await backToThePage();
    expect(within(await pageHeader()).getByText('Kazimierz padel')).toBeTruthy();
  });

  it('switched to Anyone, lets everybody waiting in and shows who', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL, TOMASZ] });
    await screen.findByRole('header', { name: 'Want to join · 2' });
    await openEdit();

    fireEvent.press(screen.getByRole('button', { name: COPY.newGroup.anyone }));
    fireEvent.press(screen.getByRole('button', { name: COPY.editGroup.save }));

    // #529: asked first, with what it does to the people waiting — and nothing sent until then.
    const sheet = within(await screen.findByTestId('bottom-sheet'));
    expect(sheet.getByRole('header', { name: COPY.editGroup.anyoneTitle })).toBeTruthy();
    expect(sheet.getByText(COPY.editGroup.anyoneBody)).toBeTruthy();
    expect(transport.requestsTo('PUT', `${GROUP_PATH}/details`)).toHaveLength(0);
    fireEvent.press(sheet.getByRole('button', { name: COPY.editGroup.save }));

    expect(await screen.findByRole('header', { name: 'Let in · 2' })).toBeTruthy();
    expect(screen.getByText(COPY.editGroup.admittedLine)).toBeTruthy();
    expect(
      screen.queryAllByTestId(/^admitted-/).map((node) => node.props.accessibilityLabel as string),
    ).toEqual(['Michał Rogalski', 'Tomasz Król']);

    fireEvent.press(screen.getByRole('button', { name: COPY.editGroup.back }));
    await waitFor(() => expect(screen).toHavePathname(INFO_PATH));
    expect(await membersRow(/^10 members, plays Padel, Tennis, anyone can join$/)).toBeTruthy();
    await waitFor(() => expect(screen.queryByText(/^Want to join/)).toBeNull());
  });

  it('saves nothing when the Owner steps back from Anyone', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE', requests: [MICHAL] });
    await screen.findByRole('header', { name: 'Want to join · 1' });
    await openEdit();

    fireEvent.press(screen.getByRole('button', { name: COPY.newGroup.anyone }));
    fireEvent.press(screen.getByRole('button', { name: COPY.editGroup.save }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.editGroup.anyoneClose }));

    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());
    expect(transport.requestsTo('PUT', `${GROUP_PATH}/details`)).toHaveLength(0);
    // The form still holds the choice, unsaved, for the Owner to change or save.
    expect(screen.getByRole('button', { name: COPY.editGroup.save })).toBeTruthy();
  });

  it('asks nothing of a save that keeps People I approve', async () => {
    await openInfo({ members: OWNED, policy: 'PEOPLE_I_APPROVE' });
    await openEdit();

    fireEvent.changeText(screen.getByDisplayValue('Kazimierz crew'), 'Kazimierz padel');
    fireEvent.press(screen.getByRole('button', { name: COPY.editGroup.save }));

    expect(
      await screen.findByRole('button', { name: COPY.editGroup.saved, disabled: true }),
    ).toBeTruthy();
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
  });

  it('says why a name was refused', async () => {
    await openInfo({ members: OWNED });
    transport.on('PUT', `${GROUP_PATH}/details`, () => errorResponse(400, 'group_name_invalid'));
    await openEdit();

    fireEvent.changeText(screen.getByDisplayValue('Kazimierz crew'), 'Kazimierz padel');
    fireEvent.press(screen.getByRole('button', { name: COPY.editGroup.save }));

    expect(await screen.findByText('Give the group a name of up to 40 characters.')).toBeTruthy();
  });
});

describe('leaving and deleting', () => {
  const listCard = () =>
    screen.queryByRole('button', { name: /^Kazimierz crew,|^My raketa group,/ });

  async function confirm(act: string) {
    const sheet = within(await screen.findByTestId('bottom-sheet'));
    fireEvent.press(sheet.getByRole('button', { name: act }));
  }

  // #529 F1: the way out stands at Info's foot, however long Info is, and never scrolls away.
  it.each([
    ['Leave', { members: KAZIMIERZ }, COPY.info.leave],
    ['Delete', { name: 'My raketa group', members: [ME] }, COPY.info.delete],
  ] as const)('pins %s under Info, outside what scrolls', async (_, setup, door) => {
    await openInfo(setup);

    expect(await screen.findByRole('button', { name: door })).toBeTruthy();
    const scrolled = within(screen.getByTestId('group-info-body'));
    expect(scrolled.getByRole('button', { name: / members?, / })).toBeTruthy();
    expect(scrolled.queryByRole('button', { name: door })).toBeNull();
  });

  it('is Info’s alone — no tab of the page draws it', async () => {
    await openPage({ members: KAZIMIERZ });

    for (const name of ['Games', 'Fill in', 'Friends']) {
      fireEvent.press(await tab(name));
      await tab(name, true);
      expect(screen.queryByRole('button', { name: COPY.info.leave })).toBeNull();
    }
  });

  // #529 F5: a leave the network was holding went on waiting after the sheet was closed, and left
  // the group a minute later — silently, from whatever page the player was on by then.
  describe('while the phone is offline', () => {
    afterEach(() => onlineManager.setOnline(true));

    const leaves = () => transport.requestsTo('DELETE', `${GROUP_PATH}/membership`);

    async function comeBackOnline() {
      await act(async () => {
        onlineManager.setOnline(true);
        await Promise.resolve();
      });
    }

    it('takes a waiting leave back when the sheet is closed', async () => {
      await openInfo({ members: KAZIMIERZ });
      act(() => onlineManager.setOnline(false));

      fireEvent.press(await screen.findByRole('button', { name: COPY.info.leave }));
      await confirm(COPY.info.leave);
      expect(leaves()).toHaveLength(0);
      fireEvent.press(await screen.findByRole('button', { name: COPY.info.leaveClose }));
      await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());
      await comeBackOnline();

      expect(leaves()).toHaveLength(0);
      expect(screen).toHavePathname(INFO_PATH);
    });

    it('still leaves once the phone is back, when the sheet was left open', async () => {
      await openInfo({ members: KAZIMIERZ });
      act(() => onlineManager.setOnline(false));

      fireEvent.press(await screen.findByRole('button', { name: COPY.info.leave }));
      await confirm(COPY.info.leave);
      expect(leaves()).toHaveLength(0);
      await comeBackOnline();

      await waitFor(() => expect(leaves()).toHaveLength(1));
      await waitFor(() => expect(screen).toHavePathname('/play'));
    });
  });

  it('deletes a group its Owner is alone in, after asking, and lands on the list', async () => {
    const server = await openInfo({ name: 'My raketa group', members: [ME] });

    fireEvent.press(await screen.findByRole('button', { name: COPY.info.delete }));
    expect(await screen.findByRole('header', { name: COPY.info.deleteTitle })).toBeTruthy();
    expect(screen.getByText(COPY.info.deleteBody)).toBeTruthy();
    await confirm(COPY.info.delete);

    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(server.state.deleted).toBe(true);
    await waitFor(() => expect(listCard()).toBeNull());
    await waitFor(() => expect(toasts()).toEqual([[COPY.info.deleted, 'ok']]));
  });

  it('keeps the group when the sheet is closed', async () => {
    const server = await openInfo({ name: 'My raketa group', members: [ME] });

    fireEvent.press(await screen.findByRole('button', { name: COPY.info.delete }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.info.deleteClose }));

    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());
    expect(server.state.deleted).toBe(false);
    expect(screen).toHavePathname(INFO_PATH);
  });

  it('lets a member leave, after saying how to come back, and lands on the list', async () => {
    await openInfo({ members: KAZIMIERZ });

    fireEvent.press(await screen.findByRole('button', { name: COPY.info.leave }));
    expect(await screen.findByRole('header', { name: COPY.info.leaveTitle })).toBeTruthy();
    expect(screen.getByText(COPY.info.rejoinAnyone)).toBeTruthy();
    expect(screen.queryByText(COPY.info.leaveHandover)).toBeNull();
    const reads = transport.requestsTo('GET', GROUP_PATH).length;
    await confirm(COPY.info.leave);

    await waitFor(() => expect(screen).toHavePathname('/play'));
    await waitFor(() => expect(listCard()).toBeNull());
    await waitFor(() => expect(toasts()).toEqual([[COPY.info.left, 'ok']]));
    // The page on its way out is not asked about a group the reader is no longer in.
    expect(transport.requestsTo('GET', GROUP_PATH)).toHaveLength(reads);
  });

  it('lets an Owner with others leave, saying the group passes on', async () => {
    const server = await openInfo({
      members: [ME, EWA, ZOFIA],
      policy: 'PEOPLE_I_APPROVE',
    });

    fireEvent.press(await screen.findByRole('button', { name: COPY.info.leave }));
    expect(await screen.findByText(COPY.info.leaveHandover)).toBeTruthy();
    expect(screen.getByText(COPY.info.rejoinAsk)).toBeTruthy();
    await confirm(COPY.info.leave);

    await waitFor(() => expect(screen).toHavePathname('/play'));
    // Ewa has been in longest.
    expect(server.state.ownerId).toBe(EWA.id);
  });

  it('offers Delete instead when everybody else left since the page was read', async () => {
    const server = await openInfo({ name: 'My raketa group', members: [ME, ZOFIA] });
    server.leave(ZOFIA);

    fireEvent.press(await screen.findByRole('button', { name: COPY.info.leave }));
    await confirm(COPY.info.leave);

    expect(
      await screen.findByText('You’re the only one left in the group — delete it instead.'),
    ).toBeTruthy();
    // The group is re-read, and the sheet's act is the door that works now.
    await confirm(COPY.info.delete);
    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(server.state.deleted).toBe(true);
  });
});

describe('Members', () => {
  // #529 F1: the group's name and count over *Members* said nothing the page under it did not.
  it('heads the page with Members and the sport pill, and nothing above them', async () => {
    await openInfo({ members: KAZIMIERZ });
    await openMembers();

    expect(await screen.findByRole('button', { name: 'Sport: Padel' })).toBeTruthy();
    expect(screen.queryByText(/Kazimierz crew/i)).toBeNull();
  });

  it('lists who plays the sport: you, the Owner with admin, then newest joined first', async () => {
    await openInfo({ members: KAZIMIERZ });
    await openMembers();

    // The count is the title's now, and the *Play Padel · 7* heading under the header is gone.
    expect(await screen.findByRole('header', { name: 'Members · 7' })).toBeTruthy();
    expect(screen.queryByText(/^Play Padel/)).toBeNull();
    // Marek plays tennis only, so he is not on padel's list.
    expect(memberIds()).toEqual([ME.id, KAROL.id, OLA.id, KUBA.id, ANIA.id, ZOFIA.id, EWA.id]);
    // The points and the band's word, spoken as the tag draws them (#660).
    expect(screen.getByLabelText('You, reliability 92, Very high, Padel 2,71')).toBeTruthy();
    expect(
      screen.getByLabelText('Karol Tomczak, reliability 75, High, admin, Padel 2,75'),
    ).toBeTruthy();
    // Nothing has happened to Ola yet: 100, like everybody at the start, never a missing tag.
    expect(screen.getByLabelText('Ola Nowak, reliability 100, Very high, Padel 2,64')).toBeTruthy();
    // A member by her nickname, whole and never with an @ (ADR-0199 §1).
    expect(screen.getByLabelText('ania.k, reliability 99, Very high, Padel 2,68')).toBeTruthy();
    expect(within(screen.getByTestId(`member-${ANIA.id}`)).getByText('ania.k')).toBeTruthy();
    expect(screen.queryByText(/@/)).toBeNull();
    // The tag beside the name, on the tint of the band the server served.
    const row = (id: string) => within(screen.getByTestId(`member-${id}`));
    expect(row(ME.id).getByTestId('score-tag-VERY_HIGH')).toBeTruthy();
    expect(row(ME.id).getByText('92')).toBeTruthy();
    expect(row(KAROL.id).getByTestId('score-tag-HIGH')).toBeTruthy();
    expect(row(KAROL.id).getByText('75')).toBeTruthy();
    expect(row(OLA.id).getByTestId('score-tag-VERY_HIGH')).toBeTruthy();
    // Every line opens on the sport's own dot.
    const dots = screen.getAllByTestId('member-sport-dot', { includeHiddenElements: true });
    expect(dots).toHaveLength(7);
    expect(StyleSheet.flatten(dots[0]?.props.style).backgroundColor).toBe(sportColour('padel'));
    expect(screen.getAllByText(COPY.members.admin)).toHaveLength(1);
    expect(screen.queryByText(/friend/i)).toBeNull();
    // A tap opens the record now, so there is no hold to explain.
    expect(screen.queryByText(/press and hold/i)).toBeNull();
  });

  // A group left on another phone: the list is refused with the page's own code, and says so
  // rather than blaming the server.
  it('says the group is not theirs when the list is refused', async () => {
    await openInfo({ members: KAZIMIERZ });
    transport.on('GET', `${GROUP_PATH}/members`, () => errorResponse(404, 'group_not_found'));
    await openMembers();

    expect(await screen.findByText(COPY.group.refused.group_not_found)).toBeTruthy();
    expect(screen.queryByText(/went wrong at our end/)).toBeNull();
  });

  it('shares the filter with the group page', async () => {
    await openInfo({ members: KAZIMIERZ });
    await openMembers();

    fireEvent.press(await screen.findByRole('button', { name: 'Sport: Padel' }));
    await screen.findByTestId('sport-bar');
    act(() => jest.advanceTimersByTime(theme.motion.unfold));
    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Tennis' }),
    );

    // The title counts the new sport's list.
    expect(await screen.findByRole('header', { name: 'Members · 3' })).toBeTruthy();
    expect(memberIds()).toEqual([ME.id, KAROL.id, MAREK.id]);

    fireEvent.press(screen.getByRole('button', { name: COPY.members.back }));
    await waitFor(() => expect(screen).toHavePathname(INFO_PATH));
    await backToThePage();
    expect(await screen.findByRole('button', { name: 'Sport: Tennis' })).toBeTruthy();
  });

  it('opens the full record of anybody tapped', async () => {
    transport.on('GET', `/api/v1/players/${ZOFIA.id}/record`, () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'NONE',
        can_add_friend: true,
        nickname: ZOFIA.name,
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: 2.69, band: 'Established' }],
        skill: {
          sport: 'PADEL',
          level: 2.69,
          band: 'Established',
          confidence: 40,
          counted_games: 3,
          likely_range: { low: 2.4, high: 2.9 },
          last_five: ['WIN'],
        },
        reliability: servedReliability({
          player_score: 95,
          band: 'VERY_HIGH',
          is_new: false,
          turned_up: 9,
          turned_up_of: 9,
          kept: 8,
          kept_of: 8,
          left_in_dispute: 1,
        }),
        variety: { distinct_opponents: 3, times_on_court: 3 },
      }),
    );
    await openInfo({ members: KAZIMIERZ });
    await openMembers();

    fireEvent.press(await screen.findByRole('button', { name: /^Zofia Bąk,/ }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', `/api/v1/players/${ZOFIA.id}/record`)).toHaveLength(1),
    );
    // A group-mate reads the sheet Zofia reads about herself: the points and the band's word,
    // and the four counts under *Full record* (#660).
    // (The block's figure, not the Members row's tag under the sheet, which prints 95 too.)
    expect(await screen.findByText(RELIABILITY_BAND_WORD.VERY_HIGH)).toBeTruthy();
    expect(screen.getAllByText('95')).toHaveLength(2);
    fireEvent.press(screen.getByRole('button', { name: FULL_RECORD }));
    const lines = countLines({
      turnedUp: 9,
      turnedUpOf: 9,
      late: 0,
      kept: 8,
      keptOf: 8,
      leftInDispute: 1,
    });
    expect(await screen.findByText(lines[0]?.value ?? '')).toBeTruthy();
    for (const line of lines) {
      expect(screen.getByText(line.label)).toBeTruthy();
      expect(screen.getByText(line.value)).toBeTruthy();
    }
  });

  it('opens your own record from your own row, a button like every other', async () => {
    stubOwnRecord(transport);
    await openInfo({ members: KAZIMIERZ });
    await openMembers();

    const you = await screen.findByRole('button', { name: /^You,/ });
    // A plain tap, which every screen reader activates — no hold, so no custom action for one.
    expect(you.props.accessibilityActions).toBeUndefined();
    expect(you.props.accessibilityHint).toBe('Opens your record');
    fireEvent.press(you);

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
  });

  it('shows who the group passed to when its Owner left', async () => {
    const server = await openInfo({ members: KAZIMIERZ });
    // Karol leaves on his own phone; Ewa has been in longest.
    server.leave(KAROL);

    await openMembers();

    expect(
      await screen.findByLabelText('Ewa Mazur, reliability 91, Very high, admin, Padel 2,60'),
    ).toBeTruthy();
    expect(memberIds()).toEqual([ME.id, EWA.id, OLA.id, KUBA.id, ANIA.id, ZOFIA.id]);
    expect(screen.queryByLabelText(/^Karol Tomczak,/)).toBeNull();
  });
});

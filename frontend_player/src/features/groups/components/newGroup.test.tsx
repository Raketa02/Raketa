/**
 * **New group, walked** — every state play mocks 4–13 draw, through the real routes with only the
 * socket faked ([#512](https://github.com/Raketa02/Raketa/issues/512), PRD #500 stories 11–28).
 *
 * The home club is **required** (PRD #500 overrides play 4 by name), and its search rows draw no
 * distance (#512). The walks run on the code defaults, which since #512 put Groups on the Play tab.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  launchSignedIn,
  stubGate,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import {
  CREATE_REFUSALS,
  GROUPS_COPY,
  chosenClubConsequence,
  noClubCalled,
} from './groupsPresentation';
import { NEW_GROUP_PAGE_TEST_ID } from './NewGroupScreen';

const COPY = GROUPS_COPY.newGroup;

const PADEL_RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

const CENTRUM: Wire['ClubCardSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000001',
  name: 'Centrum Ruchu',
  district: 'Dębniki',
  distance_km: 2.0,
  sports: ['SQUASH', 'PADEL'],
  groups: [],
};

const BONARKA: Wire['ClubCardSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000002',
  name: 'Bonarka Arena',
  district: 'Bonarka',
  distance_km: 3.1,
  sports: ['PADEL', 'BADMINTON'],
  groups: [],
};

const O3_CLUB: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000001',
  kind: 'PLAYER',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  sports: ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'],
  member_count: 11,
  join_policy: 'PEOPLE_I_APPROVE',
  owner_name: 'Coach Andrzej',
  administrator_name: null,
  is_administrator: false,
  relation: 'NONE',
};

const OPEN_PLAY: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000002',
  kind: 'PLAYER',
  name: 'Ogrody open play',
  monogram: { letters: 'Oo', colour: 0 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 8,
  join_policy: 'ANYONE',
  owner_name: 'Zofia Wiśniewska',
  administrator_name: null,
  is_administrator: false,
  relation: 'MEMBER',
};

const OGRODY: Wire['ClubCardSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000003',
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  distance_km: 2.4,
  sports: ['TENNIS', 'PADEL'],
  groups: [O3_CLUB, OPEN_PLAY],
};

const CREATED: Wire['GroupResponse'] = {
  id: 'b0000000-0000-4000-8000-000000000001',
  kind: 'PLAYER',
  name: 'My raketa group',
  monogram: { letters: 'Mr', colour: 3 },
  sports: [],
  member_count: 1,
  home_club: { id: BONARKA.id, name: BONARKA.name },
  link: 'https://raketa.app/join/ABCDEFGH',
  join_policy: 'ANYONE',
  is_owner: true,
  rated_by_sport: [],
  member_faces: [],
  administrator_name: null,
  is_administrator: false,
};

const HOME_CLUBS = '/api/v1/home-clubs';

let transport: Transport;

/** `q` and `page` off a recorded request — the transport routes on the path without them. */
function queryOf(request: RecordedRequest) {
  const params = new URLSearchParams(request.path.split('?')[1] ?? '');
  return { q: params.get('q') ?? '', page: Number(params.get('page') ?? '1') };
}

/** Home-club search that answers each text from a table, one page each unless told otherwise. */
function stubHomeClubs(answers: Readonly<Record<string, readonly Wire['HomeClubPageResponse'][]>>) {
  transport.on('GET', HOME_CLUBS, (request) => {
    const { q, page } = queryOf(request);
    const pages = answers[q] ?? [{ clubs: [], next_page: null }];
    return json<Wire['HomeClubPageResponse']>(pages[page - 1] ?? { clubs: [], next_page: null });
  });
}

function onePage(clubs: readonly Wire['ClubCardSchema'][]): Wire['HomeClubPageResponse'][] {
  return [{ clubs: [...clubs], next_page: null }];
}

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubHomeClubs({
    b: onePage([CENTRUM, BONARKA]),
    o: onePage([OGRODY]),
    bonarka: onePage([BONARKA]),
  });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  useToastQueue.getState().clear();
  resetSessionStatus();
  await clearStoredTokens();
});

async function openNewGroup() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.list.newGroupLabel }));
  await waitFor(() => expect(screen).toHavePathname('/play/new-group'));
  await screen.findByRole('header', { name: COPY.title });
}

const createButton = () => screen.getByRole('button', { name: COPY.create });
const isDisabled = (node: ReturnType<typeof createButton>) =>
  node.props.accessibilityState?.disabled === true;

function searchFor(text: string) {
  fireEvent.changeText(screen.getByLabelText(COPY.homeClub), text);
}

describe('opening New group', () => {
  it('opens a full-screen form with the empty home club and Create disabled', async () => {
    await openNewGroup();

    expect(screen.getByLabelText(COPY.name).props.value ?? '').toBe('');
    expect(screen.getByText(COPY.homeClubHint)).toBeTruthy();
    expect(screen.getByText(COPY.homeClubConsequence)).toBeTruthy();
    expect(isDisabled(createButton())).toBe(true);
  });

  it('takes a name of up to 40 characters', async () => {
    await openNewGroup();

    expect(screen.getByLabelText(COPY.name).props.maxLength).toBe(40);
  });

  // Story 12: leaving is never a commitment, and the next open is empty again.
  it('discards the form on the back arrow', async () => {
    await openNewGroup();
    fireEvent.changeText(screen.getByLabelText(COPY.name), 'Half a name');

    fireEvent.press(screen.getByRole('button', { name: COPY.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.list.newGroupLabel }));
    await waitFor(() => expect(screen).toHavePathname('/play/new-group'));

    expect(screen.getByLabelText(COPY.name).props.value ?? '').toBe('');
  });
});

describe('searching for the home club', () => {
  it('lists clubs as the player types, with no distance in the rows', async () => {
    await openNewGroup();

    searchFor('b');

    expect(await screen.findByText('Centrum Ruchu')).toBeTruthy();
    expect(screen.getByText('Dębniki · Squash, Padel')).toBeTruthy();
    expect(screen.getByText('Bonarka · Padel, Badminton')).toBeTruthy();
    expect(screen.queryByText(/km/)).toBeNull();
    expect(screen.getAllByText(COPY.setAsHome)).toHaveLength(2);
    expect(queryOf(transport.requestsTo('GET', HOME_CLUBS).at(-1)!)).toEqual({ q: 'b', page: 1 });
  });

  it('says there is no club by that name', async () => {
    await openNewGroup();

    searchFor('perr');

    expect(await screen.findByText(noClubCalled('perr'))).toBeTruthy();
    expect(screen.getByText(COPY.noClubNote)).toBeTruthy();
  });

  it('loads twenty more clubs when the list is scrolled to its end', async () => {
    stubHomeClubs({
      a: [
        { clubs: [CENTRUM], next_page: 2 },
        { clubs: [BONARKA], next_page: null },
      ],
    });
    await openNewGroup();
    searchFor('a');
    await screen.findByText('Centrum Ruchu');
    expect(screen.queryByText('Bonarka Arena')).toBeNull();

    fireEvent.scroll(screen.getByTestId(NEW_GROUP_PAGE_TEST_ID), {
      nativeEvent: {
        contentOffset: { y: 400 },
        contentSize: { height: 800, width: 375 },
        layoutMeasurement: { height: 600, width: 375 },
      },
    });

    expect(await screen.findByText('Bonarka Arena')).toBeTruthy();
    expect(queryOf(transport.requestsTo('GET', HOME_CLUBS).at(-1)!)).toEqual({ q: 'a', page: 2 });
  });
});

describe('a club that already has groups', () => {
  it('is tagged, with a strip for each of its groups', async () => {
    await openNewGroup();

    searchFor('o');

    expect(await screen.findByText(COPY.groupAlreadyHere)).toBeTruthy();
    expect(screen.getByText('Ogrody 33 Club')).toBeTruthy();
    expect(screen.getByText('11 members · Coach Andrzej approves joins')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Ask to join Ogrody 33 Club' })).toBeTruthy();
    expect(screen.getByText(GROUPS_COPY.action.in)).toBeTruthy();
  });

  it('turns Ask to join into requested · waiting', async () => {
    transport.on('POST', `/api/v1/groups/${O3_CLUB.id}/membership`, () =>
      json<Wire['GroupAtClubSchema']>({ ...O3_CLUB, relation: 'REQUESTED' }),
    );
    await openNewGroup();
    searchFor('o');

    fireEvent.press(await screen.findByRole('button', { name: 'Ask to join Ogrody 33 Club' }));

    expect(await screen.findByText(GROUPS_COPY.action.requested)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Ask to join Ogrody 33 Club' })).toBeNull();
    expect(transport.requestsTo('POST', `/api/v1/groups/${O3_CLUB.id}/membership`)).toHaveLength(1);
  });

  it('puts the reader straight into an Anyone group from inside the form', async () => {
    const open = { ...OPEN_PLAY, relation: 'NONE' as const };
    stubHomeClubs({ o: onePage([{ ...OGRODY, groups: [O3_CLUB, open] }]) });
    transport.on('POST', `/api/v1/groups/${OPEN_PLAY.id}/membership`, () =>
      json<Wire['GroupAtClubSchema']>({ ...open, relation: 'MEMBER', member_count: 9 }),
    );
    await openNewGroup();
    searchFor('o');

    fireEvent.press(await screen.findByRole('button', { name: 'Join Ogrody open play' }));

    expect(await screen.findByText(GROUPS_COPY.action.in)).toBeTruthy();
    expect(screen.getByText('9 members · anyone can join')).toBeTruthy();
    expect(screen).toHavePathname('/play/new-group');
  });

  // Story 22: a second group at the same club is allowed.
  it('can still be set as home', async () => {
    await openNewGroup();
    searchFor('o');

    fireEvent.press(await screen.findByRole('button', { name: /^Set Ogrody 33 as home club/ }));

    expect(await screen.findByText(chosenClubConsequence('Ogrody 33'))).toBeTruthy();
  });
});

describe('the chosen home club', () => {
  it('replaces the field with the club, its distance and Change', async () => {
    await openNewGroup();
    searchFor('bonarka');

    fireEvent.press(await screen.findByRole('button', { name: /^Set Bonarka Arena as home club/ }));

    expect(await screen.findByText('Bonarka · 3,1 km · Padel, Badminton')).toBeTruthy();
    expect(screen.getByText(chosenClubConsequence('Bonarka Arena'))).toBeTruthy();
    expect(screen.queryByLabelText(COPY.homeClub)).toBeNull();
    expect(screen.queryByText(COPY.homeClubConsequence)).toBeNull();
  });

  it('goes back to the search on Change', async () => {
    await openNewGroup();
    searchFor('bonarka');
    fireEvent.press(await screen.findByRole('button', { name: /^Set Bonarka Arena as home club/ }));

    fireEvent.press(await screen.findByRole('button', { name: COPY.changeLabel }));

    expect(await screen.findByLabelText(COPY.homeClub)).toBeTruthy();
    expect(screen.queryByText(chosenClubConsequence('Bonarka Arena'))).toBeNull();
  });

  // Story 28: nothing pretends to know where a player with no Location area is.
  it('draws no distance for a player whose location is unknown', async () => {
    stubHomeClubs({ bonarka: onePage([{ ...BONARKA, distance_km: null }]) });
    await openNewGroup();
    searchFor('bonarka');

    fireEvent.press(await screen.findByRole('button', { name: /^Set Bonarka Arena as home club/ }));

    expect(await screen.findByText('Bonarka · Padel, Badminton')).toBeTruthy();
    expect(screen.queryByText(/km/)).toBeNull();
  });
});

describe('who can join', () => {
  it('offers Anyone, chosen, and People I approve, with the note that there is no sport', async () => {
    await openNewGroup();

    expect(screen.getByRole('button', { name: COPY.anyone, selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.peopleIApprove, selected: false })).toBeTruthy();
    expect(screen.getByText(COPY.noSportNote)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.peopleIApprove }));

    expect(screen.getByRole('button', { name: COPY.peopleIApprove, selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.anyone, selected: false })).toBeTruthy();
  });
});

describe('creating the group', () => {
  async function fillIn(name: string) {
    fireEvent.changeText(screen.getByLabelText(COPY.name), name);
    searchFor('bonarka');
    fireEvent.press(await screen.findByRole('button', { name: /^Set Bonarka Arena as home club/ }));
    await screen.findByText(chosenClubConsequence('Bonarka Arena'));
  }

  it('stays disabled with a name and no home club, and with a home club and no name', async () => {
    await openNewGroup();

    fireEvent.changeText(screen.getByLabelText(COPY.name), 'My raketa group');
    expect(isDisabled(createButton())).toBe(true);

    await fillIn('   ');
    expect(isDisabled(createButton())).toBe(true);

    fireEvent.changeText(screen.getByLabelText(COPY.name), 'My raketa group');
    expect(isDisabled(createButton())).toBe(false);
  });

  it('opens the new group’s page with Group created', async () => {
    transport.on('POST', '/api/v1/groups', () => json(CREATED, 201));
    transport.on('GET', `/api/v1/groups/${CREATED.id}`, () => json(CREATED));
    await openNewGroup();
    await fillIn('My raketa group');
    fireEvent.press(screen.getByRole('button', { name: COPY.peopleIApprove }));

    stubMyGroups(transport, [
      {
        id: CREATED.id,
        kind: 'PLAYER',
        name: CREATED.name,
        monogram: CREATED.monogram,
        sports: [],
        member_count: 1,
        home_club: CREATED.home_club,
      },
    ]);
    fireEvent.press(createButton());

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREATED.id}`));
    expect(await screen.findByText('My raketa group')).toBeTruthy();
    expect(screen.getByText('1 member · Bonarka Arena')).toBeTruthy();
    expect(useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone])).toEqual([
      [COPY.created, 'ok'],
    ]);
    expect(transport.requestsTo('POST', '/api/v1/groups').map((request) => request.body)).toEqual([
      { name: 'My raketa group', home_club_id: BONARKA.id, join_policy: 'PEOPLE_I_APPROVE' },
    ]);

    // Back is the Groups list, with the new group on it — never the form it came from.
    fireEvent.press(screen.getByRole('button', { name: GROUPS_COPY.group.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    const card = await screen.findByRole('button', { name: /^My raketa group/ });
    expect(within(card).getByText('Bonarka Arena')).toBeTruthy();
  });

  it('names a refusal it can say something about', async () => {
    transport.on('POST', '/api/v1/groups', () => errorResponse(400, 'home_club_unknown'));
    await openNewGroup();
    await fillIn('My raketa group');

    fireEvent.press(createButton());

    expect(await screen.findByText(CREATE_REFUSALS.home_club_unknown)).toBeTruthy();
    expect(screen).toHavePathname('/play/new-group');
  });
});

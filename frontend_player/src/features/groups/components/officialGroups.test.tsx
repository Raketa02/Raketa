/**
 * **Official groups, from the player's side** — the club's groups as a player meets them in both
 * searches, on the Groups list, on the page and on Members
 * ([#519](https://github.com/Raketa02/Raketa/issues/519), PRD #500 stories 40, 56, 57;
 * ADR-0183 §3, §6, §7).
 *
 * Kasia is rated only in tennis. She finds *Ogrody 33 Club*, which plays padel, and joins it
 * anyway; its page says what to add to see its games. Tomek runs another of the club's groups and
 * plays too: from his player profile the group he runs is **Join**, never *Ask to join*. Marta runs
 * the club's group and joined it as a player, so Members tags her **admin**.
 *
 * The real route tree, with the socket and the platform faked at the edge.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import {
  GATE_USER,
  launchSignedIn,
  PLAYER_ONLY,
  resetClipboard,
  resetShare,
  stubClipboard,
  stubGate,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
  stubRunsInProgress,
  stubShare,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, fakeShare } from '@/test-support/platform';
import { stubGroupDeck } from '@/test-support/groupDeck';
import { NEW_MEMBER_RELIABILITY } from '@/test-support/playerRecord';
import {
  installTransport,
  json,
  networkFailure,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { clubCardTestId } from './ClubResultCard';
import { GROUPS_COPY } from './groupsPresentation';

const COPY = GROUPS_COPY;

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

const PADEL = rating('PADEL', 2.71);
const TENNIS = rating('TENNIS', 3.1);
const SQUASH = rating('SQUASH', 2.3);

const OGRODY_ID = 'c0000000-0000-4000-8000-000000000003';
const LINK = 'https://raketa.app/join/K7PQ2MXA';

/** The club's group, run by Marta: it plays padel, and Marta approves joins. */
/** The official marks drawn — hidden from a screen reader, so found among hidden elements. */
function officialMarks(inside?: Parameters<typeof within>[0]) {
  return (inside === undefined ? screen : within(inside)).queryAllByTestId('official-mark', {
    includeHiddenElements: true,
  });
}

const O3_CLUB: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000031',
  kind: 'OFFICIAL',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  sports: ['PADEL'],
  member_count: 11,
  join_policy: 'PEOPLE_I_APPROVE',
  owner_nickname: null,
  administrator_nickname: 'Marta Wójcik',
  is_administrator: false,
  relation: 'NONE',
};

/** The club's other group, whose administrator the club removed: it needs one. */
const OPEN_PLAY: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000032',
  kind: 'OFFICIAL',
  name: 'Ogrody open play',
  monogram: { letters: 'Oo', colour: 0 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 8,
  join_policy: 'PEOPLE_I_APPROVE',
  owner_nickname: null,
  administrator_nickname: null,
  is_administrator: false,
  relation: 'NONE',
};

/** Karol's own group at the same club — a player group keeps its Owner's line. */
const WIECZOREM: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000033',
  kind: 'PLAYER',
  name: 'Ogrody wieczorem',
  monogram: { letters: 'Ow', colour: 4 },
  sports: ['TENNIS'],
  member_count: 5,
  join_policy: 'PEOPLE_I_APPROVE',
  owner_nickname: 'Karol Nowak',
  administrator_nickname: null,
  is_administrator: false,
  relation: 'NONE',
};

/** Tomek's group: he runs it, and it asks for approval — of everybody but him. */
const TOMEK_RUNS: Wire['GroupAtClubSchema'] = {
  ...OPEN_PLAY,
  administrator_nickname: 'Tomek Kowal',
  is_administrator: true,
};

const OGRODY: Wire['ClubCardSchema'] = {
  id: OGRODY_ID,
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  distance_km: 2.4,
  sports: ['PADEL', 'TENNIS'],
  groups: [O3_CLUB, OPEN_PLAY, WIECZOREM],
};

const JOIN_SEARCH = '/api/v1/join-search';
const HOME_CLUBS = '/api/v1/home-clubs';
const ASSESSMENTS = '/api/v1/assessments';

let transport: Transport;

function queryOf(request: RecordedRequest) {
  return new URLSearchParams(request.path.split('?')[1] ?? '').get('q') ?? '';
}

/** Both searches, answering `ogrody` with these groups at Ogrody 33 and nothing else. */
function stubSearches(groups: readonly Wire['GroupAtClubSchema'][] = OGRODY.groups) {
  const club = { ...OGRODY, groups: [...groups] };
  transport.on('GET', JOIN_SEARCH, (request) =>
    json<Wire['JoinSearchResponse']>({
      clubs: queryOf(request) === 'ogrody' ? [club] : [],
      next_page: null,
      read_as: 'TEXT',
    }),
  );
  transport.on('GET', HOME_CLUBS, (request) =>
    json<Wire['HomeClubPageResponse']>({
      clubs: queryOf(request) === 'ogrody' ? [club] : [],
      next_page: null,
    }),
  );
}

/** Kasia, rated only in tennis — or whoever these ratings say. */
function stubAPlayer(
  ratings: readonly Wire['RatingResponse'][] = [TENNIS],
  profiles: Wire['AccountProfilesSchema'] = PLAYER_ONLY,
) {
  stubGate(transport, { ratings, hasPlayerProfile: true, profiles });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
}

/** Tomek: plays, and runs the club's groups too. */
const TOMEK_PROFILES: Wire['AccountProfilesSchema'] = {
  acts_as_player: true,
  administers: [{ club_id: OGRODY_ID, club_name: OGRODY.name }],
  pending_invitations: [],
  handovers: [],
};

beforeEach(() => {
  transport = installTransport();
  stubAPlayer();
  stubSearches();
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
});

afterEach(async () => {
  transport.restore();
  resetShare();
  resetClipboard();
  queryClient.clear();
  useToastQueue.getState().clear();
  resetSessionStatus();
  await clearStoredTokens();
});

async function onPlay() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

async function joinSearch(text = 'ogrody') {
  await onPlay();
  fireEvent.press(await screen.findByRole('button', { name: COPY.list.joinLabel }));
  await waitFor(() => expect(screen).toHavePathname('/play/join'));
  fireEvent.changeText(await screen.findByLabelText(COPY.joinGroup.field), text);
  await screen.findByLabelText(new RegExp(`^${OGRODY.name},`));
  return screen.getByTestId(clubCardTestId(OGRODY.id));
}

async function homeClubSearch(text = 'ogrody') {
  await onPlay();
  fireEvent.press(await screen.findByRole('button', { name: COPY.list.newGroupLabel }));
  await waitFor(() => expect(screen).toHavePathname('/play/new-group'));
  fireEvent.changeText(await screen.findByLabelText(COPY.newGroup.homeClub), text);
  await screen.findByRole('button', { name: new RegExp(`^Set ${OGRODY.name} as home club`) });
}

// ---------------------------------------------------------------------------
// In a search
// ---------------------------------------------------------------------------

describe('an official group in Join a group', () => {
  it('carries the official mark and draws its declared sports as its dots', async () => {
    const card = await joinSearch();

    // Two official groups and Karol's: the mark is an official group's alone, and the words
    // *official* are spoken rather than drawn (#529).
    expect(officialMarks(card)).toHaveLength(2);
    expect(within(card).queryByText(COPY.official)).toBeNull();
    // The dots have no words of their own; the row speaks the sports by name.
    expect(
      screen.getByLabelText('Ogrody 33 Club, official, 11 members · Needs approval, plays Padel'),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Ogrody open play, official, 8 members · Needs approval, plays Padel, Tennis',
      ),
    ).toBeTruthy();
    expect(
      screen.getByLabelText('Ogrody wieczorem, 5 members · Needs approval, plays Tennis'),
    ).toBeTruthy();
  });

  // #529: whoever answers — its administrator, the club while it needs one, a player group's
  // Owner — the row says only that somebody does.
  it('says every group that asks needs approval, whoever answers', async () => {
    const card = await joinSearch();

    expect(within(card).getByText('11 members · Needs approval')).toBeTruthy();
    expect(within(card).getByText('8 members · Needs approval')).toBeTruthy();
    expect(within(card).getByText('5 members · Needs approval')).toBeTruthy();
    expect(within(card).queryByText(/approves joins/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Ask to join Ogrody 33 Club' })).toBeTruthy();
  });

  it('says anyone can join an official group that lets anyone in', async () => {
    stubSearches([{ ...O3_CLUB, join_policy: 'ANYONE' }]);

    const card = await joinSearch();

    expect(within(card).getByText('11 members · anyone can join')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Join Ogrody 33 Club' })).toBeTruthy();
  });
});

describe('an official group in New group’s home-club search', () => {
  // The 2026-09-27 mocks: the count alone under the name, and the mark on an official group only.
  it('carries the official mark, and each row under the club says its count', async () => {
    await homeClubSearch();

    expect(officialMarks()).toHaveLength(2);
    expect(screen.queryByText(COPY.official)).toBeNull();
    expect(screen.getByText('11 members')).toBeTruthy();
    expect(screen.getByText('8 members')).toBeTruthy();
    expect(screen.getByText('5 members')).toBeTruthy();
  });

  // The dots have no words of their own; the row speaks its sports, the declared ones.
  it('speaks official and its declared sports', async () => {
    await homeClubSearch();

    expect(screen.getByLabelText('Ogrody 33 Club, official, 11 members, plays Padel')).toBeTruthy();
    expect(screen.getByLabelText('Ogrody wieczorem, 5 members, plays Tennis')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The account that runs it
// ---------------------------------------------------------------------------

describe('an account that runs an official group', () => {
  beforeEach(() => {
    stubAPlayer([PADEL], TOMEK_PROFILES);
    stubSearches([TOMEK_RUNS, WIECZOREM]);
  });

  it('sees Join on it in Join a group, never Ask to join, and is in at once', async () => {
    transport.on('POST', `/api/v1/groups/${TOMEK_RUNS.id}/membership`, () =>
      json<Wire['GroupAtClubSchema']>({ ...TOMEK_RUNS, relation: 'MEMBER', member_count: 9 }),
    );
    await joinSearch();

    expect(screen.queryByRole('button', { name: 'Ask to join Ogrody open play' })).toBeNull();
    // Only his own: Karol's group still asks.
    expect(screen.getByRole('button', { name: 'Ask to join Ogrody wieczorem' })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Join Ogrody open play' }));

    expect(await screen.findByText(COPY.action.in)).toBeTruthy();
    expect(screen.getByText('9 members · Needs approval')).toBeTruthy();
    expect(transport.requestsTo('POST', `/api/v1/groups/${TOMEK_RUNS.id}/membership`)).toHaveLength(
      1,
    );
  });

  it('sees Join on it in New group’s club rows, and is in at once', async () => {
    transport.on('POST', `/api/v1/groups/${TOMEK_RUNS.id}/membership`, () =>
      json<Wire['GroupAtClubSchema']>({ ...TOMEK_RUNS, relation: 'MEMBER', member_count: 9 }),
    );
    await homeClubSearch();

    expect(screen.queryByRole('button', { name: 'Ask to join Ogrody open play' })).toBeNull();
    fireEvent.press(await screen.findByRole('button', { name: 'Join Ogrody open play' }));

    expect(await screen.findByText(COPY.action.in)).toBeTruthy();
    expect(screen.getByText('9 members')).toBeTruthy();
  });

  // #509: a request left before he was made its administrator is admitted by his own Join.
  it('sees Join rather than requested · waiting when he asked before he ran it', async () => {
    stubSearches([{ ...TOMEK_RUNS, relation: 'REQUESTED' }]);

    await joinSearch();

    expect(screen.getByRole('button', { name: 'Join Ogrody open play' })).toBeTruthy();
    expect(screen.queryByText(COPY.action.requested)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The Groups list
// ---------------------------------------------------------------------------

const O3_MINE: Wire['MyGroupSchema'] = {
  id: O3_CLUB.id,
  kind: 'OFFICIAL',
  name: O3_CLUB.name,
  monogram: O3_CLUB.monogram,
  sports: ['PADEL'],
  member_count: 12,
  home_club: { id: OGRODY_ID, name: OGRODY.name },
};

describe('an official group on the Groups list', () => {
  it('draws its declared sports as its dots, and the official mark beside its name', async () => {
    stubMyGroups(transport, [O3_MINE]);

    await onPlay();

    const card = await screen.findByRole('button', {
      name: 'Ogrody 33 Club, official, 12 members, plays Padel, Ogrody 33',
    });
    expect(officialMarks(card)).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// Its page
// ---------------------------------------------------------------------------

const MARTA: Wire['GroupPersonSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000000041',
  nickname: 'Marta Wójcik',
};
const KASIA: Wire['GroupPersonSchema'] = { player_id: GATE_USER.id, nickname: 'Kasia Lis' };

function pageOf(
  group: Wire['MyGroupSchema'],
  overrides: Partial<Wire['GroupResponse']> = {},
): Wire['GroupResponse'] {
  return {
    ...group,
    link: LINK,
    join_policy: 'PEOPLE_I_APPROVE',
    is_owner: false,
    declared_sports: group.sports,
    rated_by_sport: [
      { sport: 'PADEL', rated_count: 11, first_rated: [MARTA] },
      { sport: 'TENNIS', rated_count: 1, first_rated: [KASIA] },
      { sport: 'SQUASH', rated_count: 1, first_rated: [KASIA] },
      { sport: 'BADMINTON', rated_count: 0, first_rated: [] },
    ],
    member_faces: [MARTA],
    administrator_nickname: O3_CLUB.administrator_nickname,
    is_administrator: false,
    ...overrides,
  };
}

async function openPage(
  group: Wire['MyGroupSchema'] = O3_MINE,
  page: Wire['GroupResponse'] = pageOf(group),
) {
  stubMyGroups(transport, [group]);
  transport.on('GET', `/api/v1/groups/${group.id}`, () => json(page));
  stubGroupDeck(transport, group.id);
  await onPlay();
  fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${group.name}, `) }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${group.id}`));
  await screen.findByRole('button', { name: new RegExp(`^${group.name}`) });
}

const tab = (name: string, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

async function openTab(name: string) {
  fireEvent.press(await tab(name));
  expect(await tab(name, true)).toBeTruthy();
}

/** Info, from the page's header (Q125) — found by what it opens, as the list's card is named too. */
async function openInfo(group: Wire['MyGroupSchema'] = O3_MINE) {
  fireEvent.press(await screen.findByHintText(COPY.group.openInfo));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${group.id}/info`));
}

function barOptions(): string[] {
  const bar = screen.getByTestId('sport-bar');
  return within(bar)
    .getAllByRole('button')
    .map((option) => option.props.accessibilityLabel as string);
}

const PADEL_AND_SQUASH: Wire['MyGroupSchema'] = { ...O3_MINE, sports: ['PADEL', 'SQUASH'] };

describe('an official group’s header', () => {
  // #529: the mark beside the name, as in both searches — drawn, not spoken; the header says it.
  it('carries the official mark beside the name, and says official', async () => {
    stubAPlayer([PADEL, TENNIS]);
    await openPage();

    expect(
      screen.getByRole('button', { name: 'Ogrody 33 Club, official, 12 members · Ogrody 33' }),
    ).toBeTruthy();
    // The header's mark, and the list card's under the page — a page pushed over the list leaves
    // the list's card mounted beneath it, and that card carries the mark too.
    expect(officialMarks()).toHaveLength(2);
  });

  it('is an official group’s alone', async () => {
    stubAPlayer([PADEL, TENNIS]);
    const mine: Wire['MyGroupSchema'] = { ...O3_MINE, kind: 'PLAYER', name: 'Ogrody wieczorem' };
    await openPage(mine, pageOf(mine, { administrator_nickname: null }));

    expect(
      screen.getByRole('button', { name: /^Ogrody wieczorem/ }).props.accessibilityLabel,
    ).toBeUndefined();
    expect(officialMarks()).toHaveLength(0);
  });
});

describe('the filter on an official group’s page', () => {
  it('lists only the sports the player is rated in that the group plays', async () => {
    stubAPlayer([PADEL, TENNIS, SQUASH]);
    await openPage(PADEL_AND_SQUASH);

    fireEvent.press(await screen.findByRole('button', { name: 'Sport: Padel' }));
    await screen.findByTestId('sport-bar');
    act(() => jest.advanceTimersByTime(theme.motion.unfold));

    expect(barOptions()).toEqual(['Squash', 'Padel']);
  });

  it('opens on a sport the group plays when the one last picked is not one of them', async () => {
    stubAPlayer([PADEL, TENNIS, SQUASH]);
    await savePhonePreference(GATE_USER.id, 'lastSport', 'tennis');

    await openPage(PADEL_AND_SQUASH);

    expect(await screen.findByRole('button', { name: 'Sport: Padel' })).toBeTruthy();
  });

  it('is a plain label when the player is rated in one of its sports', async () => {
    stubAPlayer([PADEL, TENNIS]);
    await openPage();

    expect(await screen.findByLabelText('Sport: Padel')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Sport: Padel' })).toBeNull();
    // The Games card is drawn for padel as for any group.
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
  });
});

const ADD_HEADLINE = 'This group plays padel';
const ADD_LINE = 'Add padel to your Skill passport to see its games.';

describe('an official group’s page for a player rated in none of its sports', () => {
  it('shows one card in place of Games — what it plays, and a way to add it', async () => {
    await openPage();

    expect(await screen.findByText(ADD_HEADLINE)).toBeTruthy();
    expect(screen.getByText(ADD_LINE)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Add Padel' })).toBeTruthy();
    // Nothing is drawn for a sport, and there is no sport to pick.
    expect(screen.queryByLabelText(/^Sport: /)).toBeNull();
    expect(screen.queryByText('Just you so far')).toBeNull();
    expect(screen.queryByRole('button', { name: COPY.link.share })).toBeNull();
  });

  it('shows the same card in place of Fill in and Friends, with no game to post', async () => {
    await openPage();
    await screen.findByText(ADD_HEADLINE);

    await openTab(COPY.group.tabs.fillIn);
    expect(screen.getByText(ADD_HEADLINE)).toBeTruthy();
    expect(screen.queryByText(COPY.fillIn.postAGameDrawn)).toBeNull();

    await openTab(COPY.group.tabs.friends);
    expect(screen.getByText(ADD_HEADLINE)).toBeTruthy();
    expect(screen.queryByText(COPY.friends.competitive)).toBeNull();
  });

  // Q125: the header still opens Info, and the way out is there — it is not a sport's.
  it('keeps Info, through the header — the group, its dots and the way out', async () => {
    await openPage();
    await screen.findByText(ADD_HEADLINE);

    await openInfo();

    expect(
      await screen.findByRole('button', {
        name: '12 members, plays Padel, the administrator approves joins',
      }),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.info.leave })).toBeTruthy();
    expect(screen.queryByText(ADD_HEADLINE)).toBeNull();
  });

  it('names every sport the group plays, and offers each', async () => {
    await openPage(PADEL_AND_SQUASH);

    expect(await screen.findByText('This group plays padel and squash')).toBeTruthy();
    expect(
      screen.getByText('Add padel or squash to your Skill passport to see its games.'),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Add Padel' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Add Squash' })).toBeTruthy();
  });

  it('shows the card on Members too, where the list is drawn for a sport', async () => {
    await openPage();
    await openInfo();

    fireEvent.press(await screen.findByRole('button', { name: /^12 members, / }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${O3_MINE.id}/members`));

    expect(await screen.findByText(ADD_HEADLINE)).toBeTruthy();
    // No sport, so no list and nothing to count: the title is the word alone.
    expect(screen.getByRole('header', { name: COPY.members.title })).toBeTruthy();
    expect(transport.requestsTo('GET', `/api/v1/groups/${O3_MINE.id}/members`)).toHaveLength(0);
  });

  describe('Add', () => {
    const RUN = '4d5e6f70-8192-4a3b-8c4d-5e6f70819203';
    const OPENING: Wire['AssessmentStepResponse'] = {
      assessment_id: RUN,
      status: 'in_progress',
      questions_asked: 0,
      transcript: [],
      question: {
        id: 'q-played',
        category: 'Recent activity',
        tier: null,
        situation: 'Before anything else',
        text: 'Have you played padel before?',
        qualifier: 'Any level counts',
        options: [
          { id: 'never', text: 'Never played' },
          { id: 'regular', text: 'I play most weeks' },
        ],
      },
    };

    it('begins the Add a sport questionnaire for that sport', async () => {
      transport.on('POST', ASSESSMENTS, () => {
        stubRunsInProgress(transport, [{ assessment_id: RUN, sport: 'PADEL' }]);
        return json(OPENING, 201);
      });
      transport.on('GET', `${ASSESSMENTS}/${RUN}`, () => json(OPENING));
      await openPage();

      fireEvent.press(await screen.findByRole('button', { name: 'Add Padel' }));

      await waitFor(() => expect(screen).toHavePathname(`/question/${RUN}`));
      expect(await screen.findByText('Have you played padel before?')).toBeTruthy();
      expect(transport.requestsTo('POST', ASSESSMENTS).map((request) => request.body)).toEqual([
        { sport: 'PADEL' },
      ]);
    });

    it('says so on the card when the start fails, and offers it again', async () => {
      transport.on('POST', ASSESSMENTS, networkFailure());
      await openPage();

      fireEvent.press(await screen.findByRole('button', { name: 'Add Padel' }));

      expect(await screen.findByRole('alert')).toBeTruthy();
      expect(screen).toHavePathname(`/play/group/${O3_MINE.id}`);
      expect(screen.getByRole('button', { name: 'Add Padel' })).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// Members
// ---------------------------------------------------------------------------

/** Kasia's padel row, and Michał's — a list with no Administrator on it. */
const KASIA_ROW: Wire['GroupMemberSchema'] = {
  player_id: GATE_USER.id,
  nickname: 'Kasia Lis',
  level: 2.71,
  ...NEW_MEMBER_RELIABILITY,
  is_owner: false,
  is_administrator: false,
  joined_at: '2026-09-20T10:00:00Z',
};
const MICHAL_ROW: Wire['GroupMemberSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000000042',
  nickname: 'Michał Rogalski',
  level: 2.44,
  ...NEW_MEMBER_RELIABILITY,
  is_owner: false,
  is_administrator: false,
  joined_at: '2026-09-10T10:00:00Z',
};

function stubMembers(members: readonly Wire['GroupMemberSchema'][]) {
  transport.on('GET', `/api/v1/groups/${O3_MINE.id}/members`, () =>
    json<Wire['GroupMembersResponse']>({ sport: 'PADEL', members: [...members] }),
  );
}

async function openMembers(page: Wire['GroupResponse'] = pageOf(O3_MINE)) {
  await openPage(O3_MINE, page);
  await openInfo();
  fireEvent.press(await screen.findByRole('button', { name: /^12 members, / }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${O3_MINE.id}/members`));
}

describe('Members of an official group', () => {
  // #529: an Administrator who does not play in the group was on no list, so a member could not
  // see who runs it.
  it('names the administrator who is not on the list over it, and counts only the members', async () => {
    stubAPlayer([PADEL, TENNIS]);
    stubMembers([KASIA_ROW, MICHAL_ROW]);
    await openMembers();

    const runner = await screen.findByTestId('members-runner');
    expect(runner.props.accessibilityLabel).toBe(
      'Marta Wójcik, admin, runs this group for Ogrody 33',
    );
    expect(within(runner).getByText('Marta Wójcik')).toBeTruthy();
    expect(within(runner).getByText(COPY.members.admin)).toBeTruthy();
    expect(within(runner).getByText('runs this group for Ogrody 33')).toBeTruthy();
    // Not a member, so not counted; not a button, since there may be no record to open.
    expect(screen.getByRole('header', { name: 'Members · 2' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Marta Wójcik/ })).toBeNull();
    // Over the list.
    const order = screen
      .getAllByTestId(/^members-runner$|^member-/)
      .map((node) => node.props.testID as string);
    expect(order).toEqual([
      'members-runner',
      `member-${GATE_USER.id}`,
      `member-${MICHAL_ROW.player_id}`,
    ]);
  });

  it('names the club while the group needs an administrator', async () => {
    stubAPlayer([PADEL, TENNIS]);
    stubMembers([KASIA_ROW]);
    await openMembers(pageOf(O3_MINE, { administrator_nickname: null }));

    const runner = await screen.findByTestId('members-runner');
    expect(runner.props.accessibilityLabel).toBe('Ogrody 33, no administrator right now');
    expect(within(runner).queryByText(COPY.members.admin)).toBeNull();
  });

  it('tags the administrator who joined as a player admin', async () => {
    stubAPlayer([PADEL, TENNIS]);
    transport.on('GET', `/api/v1/groups/${O3_MINE.id}/members`, () =>
      json<Wire['GroupMembersResponse']>({
        sport: 'PADEL',
        members: [
          {
            player_id: GATE_USER.id,
            nickname: 'Kasia Lis',
            level: 2.71,
            ...NEW_MEMBER_RELIABILITY,
            is_owner: false,
            is_administrator: false,
            joined_at: '2026-09-20T10:00:00Z',
          },
          {
            player_id: MARTA.player_id,
            nickname: 'Marta Wójcik',
            level: 2.6,
            player_score: 91,
            reliability_band: 'VERY_HIGH',
            is_owner: false,
            is_administrator: true,
            joined_at: '2026-09-01T10:00:00Z',
          },
          {
            player_id: 'e0000000-0000-4000-8000-000000000042',
            nickname: 'Michał Rogalski',
            level: 2.44,
            ...NEW_MEMBER_RELIABILITY,
            is_owner: false,
            is_administrator: false,
            joined_at: '2026-09-10T10:00:00Z',
          },
        ],
      }),
    );
    await openPage();
    await openInfo();
    fireEvent.press(await screen.findByRole('button', { name: /^12 members, / }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${O3_MINE.id}/members`));

    expect(
      await screen.findByLabelText('Marta Wójcik, reliability 91, Very high, admin, Padel 2,60'),
    ).toBeTruthy();
    expect(screen.getAllByText(COPY.members.admin)).toHaveLength(1);
    expect(
      screen.getByLabelText('Michał Rogalski, reliability 100, Very high, Padel 2,44'),
    ).toBeTruthy();
    // Her own row says who runs it: she is not drawn twice.
    expect(screen.queryByTestId('members-runner')).toBeNull();
  });

  // Tomek, on a group he runs and joined: his own row is You, tagged admin.
  it('tags the reader’s own row admin when they run the group', async () => {
    stubAPlayer([PADEL], TOMEK_PROFILES);
    transport.on('GET', `/api/v1/groups/${O3_MINE.id}/members`, () =>
      json<Wire['GroupMembersResponse']>({
        sport: 'PADEL',
        members: [
          {
            player_id: GATE_USER.id,
            nickname: 'Tomek Kowal',
            level: 2.71,
            ...NEW_MEMBER_RELIABILITY,
            is_owner: false,
            is_administrator: true,
            joined_at: '2026-09-20T10:00:00Z',
          },
        ],
      }),
    );
    await openMembers(
      pageOf(O3_MINE, { administrator_nickname: 'Tomek Kowal', is_administrator: true }),
    );

    expect(
      await screen.findByLabelText('You, reliability 100, Very high, admin, Padel 2,71'),
    ).toBeTruthy();
    expect(screen.queryByTestId('members-runner')).toBeNull();
  });
});

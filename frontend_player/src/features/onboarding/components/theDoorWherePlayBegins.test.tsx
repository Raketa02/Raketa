/**
 * **A level is asked where play begins** ([#730](https://github.com/Raketa02/Raketa/issues/730),
 * [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §2–§6), driven
 * through the real route tree with only `fetch` faked.
 *
 * Ania signed up in eight screens and answered no skill question. She joins Kuba's player group
 * *Wednesday padel*, rated in nothing, and every way of playing there — Games, Fill in, You’re in,
 * Friends, *Post a game* and Members — shows one door: *Get your level — pick the sports you play,
 * a few questions each*. It opens *Which sports do you play?* with nothing ticked; she picks padel and
 * tennis, rates both (*Rate Tennis* between them) and lands back on the tab she pressed it on, with
 * both sports on the chip. On Games, *Your usual game at Padel* comes next.
 *
 * Left halfway, the questions never take over the app: it opens on Home, and the door says *Carry
 * on with your padel questions — you're on question 5*, and opens that run where it stands.
 *
 * *Padel at Kazimierz*, a club's official group, keeps its own card (`aPassFromAGroup.test`).
 *
 * Every assertion is about what a player can see or what left the device.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { groupDeck, stubGroupDeck } from '@/test-support/groupDeck';
import {
  HOME_TAB_LINE,
  SPORTS_SERVED,
  launchSignedIn,
  profileSurface,
  stubGate,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
  stubRunsInProgress,
  ratingGuideAlreadyShown,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { onboardingKeys } from '../hooks/onboardingKeys';
import { useOnboardingPass } from '../store/onboardingPass.store';

/** A walk — the group, the door, two runs and the landing — is longer than jest's five seconds. */
const WALK_TIMEOUT = 30_000;

const ASSESSMENTS_PATH = '/api/v1/assessments';
const RATINGS_PATH = '/api/v1/ratings';
const stepPath = (id: string) => `${ASSESSMENTS_PATH}/${id}`;
const groupPath = (id: string) => `/api/v1/groups/${id}`;

const TABS = GROUPS_COPY.group.tabs;
const DOOR = 'Get your level';
const DOOR_LINE = 'Pick the sports you play, a few questions each.';

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.7,
    confidence: 24,
    range: { low: mu - 0.7, high: mu + 0.7 },
    band: { name: 'Developing', lower: 1.6, upper: 2.6 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-11-04T09:00:00Z',
  };
}

// ---------------------------------------------------------------------------
// The groups
// ---------------------------------------------------------------------------

const WEDNESDAY: Wire['MyGroupSchema'] = {
  id: 'c3000000-0000-4000-8000-000000000730',
  kind: 'PLAYER',
  name: 'Wednesday padel',
  monogram: { letters: 'Wp', colour: 3 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c2000000-0000-4000-8000-000000000730', name: 'Kazimierz Padel Club' },
};

const KAZIMIERZ: Wire['MyGroupSchema'] = {
  id: 'c1000000-0000-4000-8000-000000000730',
  kind: 'OFFICIAL',
  name: 'Padel at Kazimierz',
  monogram: { letters: 'PK', colour: 1 },
  sports: ['PADEL'],
  member_count: 9,
  home_club: { id: 'c2000000-0000-4000-8000-000000000730', name: 'Kazimierz Padel Club' },
};

const KUBA: Wire['GroupPersonSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000000730',
  nickname: 'kuba',
};

function pageOf(group: Wire['MyGroupSchema']): Wire['GroupResponse'] {
  const official = group.kind === 'OFFICIAL';
  return {
    ...group,
    link: 'https://raketa.app/join/K7PQ2MXA',
    join_policy: 'PEOPLE_I_APPROVE',
    is_owner: false,
    ...(official ? { declared_sports: group.sports } : {}),
    rated_by_sport: [
      { sport: 'PADEL', rated_count: 5, first_rated: [KUBA] },
      { sport: 'TENNIS', rated_count: 1, first_rated: [KUBA] },
      { sport: 'SQUASH', rated_count: 0, first_rated: [] },
      { sport: 'BADMINTON', rated_count: 0, first_rated: [] },
    ],
    member_faces: [KUBA],
    administrator_nickname: official ? KUBA.nickname : null,
    is_administrator: false,
  };
}

// ---------------------------------------------------------------------------
// The runs, as a server that performs their transitions
// ---------------------------------------------------------------------------

interface Run {
  readonly id: string;
  readonly sport: Wire['Sport'];
  readonly name: string;
  readonly mu: number;
  /** The level the result screen leads with — how the walk knows it arrived. */
  readonly level: string;
}

const PADEL_RUN: Run = {
  id: '4d5e6f70-8192-4a3b-8c4d-5e6f70819730',
  sport: 'PADEL',
  name: 'Padel',
  mu: 1.9,
  level: '1,90',
};
const TENNIS_RUN: Run = {
  id: '5e6f7081-92a3-4b4c-8d5e-6f7081920730',
  sport: 'TENNIS',
  name: 'Tennis',
  mu: 3.4,
  level: '3,40',
};
const RUNS = [PADEL_RUN, TENNIS_RUN];

function questionOf(run: Run): Wire['QuestionResponse'] {
  return {
    id: `q-played-${run.name}`,
    category: 'Recent activity',
    tier: null,
    situation: 'Before anything else',
    text: `Have you played ${run.name.toLowerCase()} before?`,
    qualifier: 'Any level counts',
    options: [
      { id: 'never', text: 'Never played' },
      { id: 'regular', text: 'I play most weeks' },
    ],
  };
}

/** The run at its outstanding question, `answered` already behind it. */
function askingOf(run: Run, answered = 0): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: run.id,
    status: 'in_progress',
    questions_asked: answered,
    transcript: Array.from({ length: answered }, (_, at) => ({
      question: { ...questionOf(run), id: `q-earlier-${at}` },
      option_id: 'regular',
    })),
    question: questionOf(run),
  };
}

/** One more answer in, and the engine has stopped: the review is next. */
function stoppedOf(run: Run, answered = 1): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: run.id,
    status: 'in_progress',
    questions_asked: answered,
    transcript: Array.from({ length: answered }, () => ({
      question: questionOf(run),
      option_id: 'regular',
    })),
    question: null,
    result: null,
  };
}

function ratedOf(run: Run, answered = 1): Wire['AssessmentStepResponse'] {
  return {
    ...stoppedOf(run, answered),
    status: 'completed',
    result: {
      mu: run.mu,
      sigma: 0.7,
      confidence: 24,
      confidence_ceiling: 30,
      range: { low: run.mu - 0.7, high: run.mu + 0.7 },
      band: { name: 'Developing', lower: 1.6, upper: 2.6 },
      status: 'initial_estimate',
      questions_asked: answered,
      engine_version: 'racketskill-v3',
      calibration_priority: 'standard',
    },
  };
}

let transport: Transport;
/** What `GET /ratings` says now — a completion adds to it. */
let ratings: Wire['RatingResponse'][];

/**
 * Ania, set up and rated in nothing, in these groups — with no usual game declared for any sport,
 * and a server that runs the questionnaire: a start opens the sport's run, a completion rates it.
 * `leftHalfway` is a run she left with four answers in.
 */
function stubAnia(
  groups: readonly Wire['MyGroupSchema'][],
  { leftHalfway }: { readonly leftHalfway?: Run } = {},
) {
  ratings = [];
  stubGate(transport, { ratings, hasPlayerProfile: true });
  stubProfileSurface(transport, profileSurface({ play_intents: {} }));
  stubProfileOptions(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  transport.on('GET', RATINGS_PATH, () => json<Wire['RatingsResponse']>({ ratings: [...ratings] }));
  stubMyGroups(transport, groups);
  for (const group of groups) {
    transport.on('GET', groupPath(group.id), () => json(pageOf(group)));
    // No usual game declared yet: the deck asks for one before it deals (ADR-0094).
    stubGroupDeck(transport, group.id, groupDeck({ segments: [], cards: [] }));
  }
  stubRunsInProgress(
    transport,
    leftHalfway === undefined ? [] : [{ assessment_id: leftHalfway.id, sport: leftHalfway.sport }],
  );

  transport.on('POST', ASSESSMENTS_PATH, (request) => {
    const { sport } = request.body as { readonly sport: Wire['Sport'] };
    const run = RUNS.find((one) => one.sport === sport)!;
    stubRunsInProgress(transport, [{ assessment_id: run.id, sport }]);
    return json(askingOf(run), 201);
  });
  for (const run of RUNS) {
    const answered = run === leftHalfway ? 4 : 0;
    transport.on('GET', stepPath(run.id), () => json(askingOf(run, answered)));
    transport.on('POST', `${stepPath(run.id)}/answers`, () => json(stoppedOf(run, answered + 1)));
    transport.on('POST', `${stepPath(run.id)}/completion`, () => {
      stubRunsInProgress(transport, []);
      ratings = [...ratings, rating(run.sport, run.mu)];
      return json(ratedOf(run, answered + 1));
    });
    transport.on('POST', `${stepPath(run.id)}/abandonment`, () => {
      stubRunsInProgress(transport, []);
      return noContent();
    });
  }
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useOnboardingPass.getState().reset();
  await ratingGuideAlreadyShown();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
});

// ---------------------------------------------------------------------------
// Walking
// ---------------------------------------------------------------------------

/** Play › Groups › the group's page. */
async function openTheGroup(group: Wire['MyGroupSchema']) {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${group.name}, `) }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${group.id}`));
}

const tab = (name: string, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

async function openTab(name: string) {
  fireEvent.press(await tab(name));
  expect(await tab(name, true)).toBeTruthy();
}

/** The door, as it reads with nothing left halfway — and the page has nothing else to offer. */
async function expectTheDoor() {
  expect(await screen.findByText(DOOR)).toBeTruthy();
  expect(screen.getByText(DOOR_LINE)).toBeTruthy();
  // No sport pill: she holds no rating to list.
  expect(screen.queryByLabelText(/^Sport: /)).toBeNull();
}

/** One sport's questionnaire, walked from its outstanding question to *Your rating*. */
async function rate(run: Run) {
  await waitFor(() => expect(screen).toHavePathname(`/question/${run.id}`));
  expect(await screen.findByText(questionOf(run).text)).toBeTruthy();
  fireEvent.press(screen.getByLabelText('I play most weeks'));
  fireEvent.press(screen.getByLabelText('Confirm answer'));
  await waitFor(() => expect(screen).toHavePathname(`/review/${run.id}`));
  fireEvent.press(await screen.findByLabelText(`Get my ${run.name} level`));
  await waitFor(() => expect(screen).toHavePathname(`/result/${run.id}`), { timeout: 4000 });
  expect(await screen.findByText(run.level)).toBeTruthy();
}

/** Back on the group's page, on this tab. */
async function expectTheGroup(group: Wire['MyGroupSchema'], on: string) {
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${group.id}`), { timeout: 4000 });
  expect(await tab(on, true)).toBeTruthy();
}

/** The chip's sports, unfolded — every one it offers, as a listener meets them. */
async function chipSports(on: string): Promise<string[]> {
  fireEvent.press(await screen.findByRole('button', { name: `Sport: ${on}` }));
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
  return within(screen.getByTestId('sport-bar'))
    .getAllByRole('button')
    .map((option) => option.props.accessibilityLabel as string);
}

// ---------------------------------------------------------------------------
// The door, everywhere a player group plays
// ---------------------------------------------------------------------------

describe('a player rated in nothing, in a player group', () => {
  it(
    'meets the door on Games, Fill in, You’re in and Friends, with no chip over any of them',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);

      // Games, which the page opens on.
      await expectTheDoor();
      await openTab(TABS.fillIn);
      await expectTheDoor();
      await openTab(TABS.youreIn);
      await expectTheDoor();
      await openTab(TABS.friends);
      await expectTheDoor();
      // No court behind the door, so no menu on its tab (#861): no chevron, and a press opens none.
      expect(
        screen.queryByTestId('segment-chevron-friends', { includeHiddenElements: true }),
      ).toBeNull();
      fireEvent.press(await tab(TABS.friends, true));
      expect(screen.queryByTestId('tab-menu', { includeHiddenElements: true })).toBeNull();
      // Nothing was started by looking.
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toEqual([]);
    },
    WALK_TIMEOUT,
  );

  it(
    'meets it on Post a game, which still floats over You’re in’s door — and only there',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);
      await openTab(TABS.fillIn);
      await expectTheDoor();
      expect(screen.queryByTestId('post-a-game-fab')).toBeNull();
      await openTab(TABS.youreIn);
      await expectTheDoor();

      // The screens A3: the FAB floats over You’re in's door, and *Post a game* shows the same door.
      expect(screen.getByTestId('post-a-game-fab')).toBeTruthy();
      fireEvent.press(await screen.findByRole('button', { name: /Post a game/ }));

      await waitFor(() => expect(screen).toHavePathname(`/play/group/${WEDNESDAY.id}/post`));
      await expectTheDoor();
      // Not the official group's card, which names sports the group declares.
      expect(screen.queryByText(/^Get rated in /)).toBeNull();
    },
    WALK_TIMEOUT,
  );

  // #848: a pass begun on Post a game returns to You’re in — where its button lives and a post
  // lands — whichever tab Post a game was opened over; here, Games.
  it(
    'rates from Post a game’s door and lands back on You’re in, even opened over Games',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);
      expect(await tab(TABS.games, true)).toBeTruthy();

      act(() => router.push(`/play/group/${WEDNESDAY.id}/post`));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${WEDNESDAY.id}/post`));
      await expectTheDoor();
      fireEvent.press(screen.getByRole('button', { name: 'Pick your sports' }));
      await waitFor(() => expect(screen).toHavePathname('/sports'));
      fireEvent.press(await screen.findByLabelText('Padel'));
      fireEvent.press(screen.getByLabelText('Rate 1 sport'));
      await rate(PADEL_RUN);
      fireEvent.press(screen.getByLabelText(`Back to ${WEDNESDAY.name}`));

      await expectTheGroup(WEDNESDAY, TABS.youreIn);
    },
    WALK_TIMEOUT,
  );

  it(
    'meets it on Members, in place of a list she is on nobody’s copy of',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);

      fireEvent.press(await screen.findByHintText(GROUPS_COPY.group.openInfo));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${WEDNESDAY.id}/info`));
      fireEvent.press(await screen.findByRole('button', { name: /^6 members, / }));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${WEDNESDAY.id}/members`));

      await expectTheDoor();
    },
    WALK_TIMEOUT,
  );

  it(
    'opens the picker over every sport, with nothing ticked',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);

      fireEvent.press(await screen.findByRole('button', { name: 'Pick your sports' }));

      await waitFor(() => expect(screen).toHavePathname('/sports'));
      expect(await screen.findByText('Which sports do you play?')).toBeTruthy();
      for (const sport of ['Padel', 'Tennis', 'Squash', 'Badminton']) {
        expect(await screen.findByRole('button', { name: sport, selected: false })).toBeTruthy();
      }
      expect(screen.queryByText('Selected')).toBeNull();
    },
    WALK_TIMEOUT,
  );

  it(
    'picks padel and tennis, rates both, and lands back on the tab with both on the chip',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);
      await openTab(TABS.friends);

      fireEvent.press(await screen.findByRole('button', { name: 'Pick your sports' }));
      await waitFor(() => expect(screen).toHavePathname('/sports'));
      fireEvent.press(await screen.findByLabelText('Padel'));
      fireEvent.press(screen.getByLabelText('Tennis'));
      fireEvent.press(screen.getByLabelText('Rate 2 sports'));

      await rate(PADEL_RUN);
      expect(screen.getByLabelText('Done for now')).toBeTruthy();
      fireEvent.press(screen.getByLabelText('Rate Tennis'));

      await rate(TENNIS_RUN);
      fireEvent.press(screen.getByLabelText(`Back to ${WEDNESDAY.name}`));

      await expectTheGroup(WEDNESDAY, TABS.friends);
      // The door is gone, and the chip lists exactly the two sports she is rated in, standing on
      // the one rated last — ending with + Another sport, squash and badminton left (#731).
      await waitFor(() => expect(screen.queryByText(DOOR)).toBeNull());
      expect(await chipSports('Tennis')).toEqual([
        GROUPS_COPY.filter.anotherSport,
        'Padel',
        'Tennis',
      ]);
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH).map((request) => request.body)).toEqual(
        [{ sport: 'PADEL' }, { sport: 'TENNIS' }],
      );
    },
    WALK_TIMEOUT,
  );

  it(
    'is asked her usual game next, on Games, for the sport she just rated',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);

      fireEvent.press(await screen.findByRole('button', { name: 'Pick your sports' }));
      await waitFor(() => expect(screen).toHavePathname('/sports'));
      fireEvent.press(await screen.findByLabelText('Padel'));
      fireEvent.press(screen.getByLabelText('Rate 1 sport'));
      await rate(PADEL_RUN);
      fireEvent.press(screen.getByLabelText(`Back to ${WEDNESDAY.name}`));

      await expectTheGroup(WEDNESDAY, TABS.games);
      expect(await screen.findByText('Your usual game at Padel')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );

  it(
    'turns back from the picker to the tab the door stood on, having started nothing',
    async () => {
      stubAnia([WEDNESDAY]);
      await openTheGroup(WEDNESDAY);
      await openTab(TABS.fillIn);

      fireEvent.press(await screen.findByRole('button', { name: 'Pick your sports' }));
      await waitFor(() => expect(screen).toHavePathname('/sports'));
      fireEvent.press(await screen.findByLabelText('Back'));

      await expectTheGroup(WEDNESDAY, TABS.fillIn);
      await expectTheDoor();
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toEqual([]);
    },
    WALK_TIMEOUT,
  );
});

describe('the door, offline with nothing to answer from', () => {
  it('says it is waiting, and draws itself the moment the connection is back', async () => {
    stubAnia([WEDNESDAY]);
    await openTheGroup(WEDNESDAY);
    await expectTheDoor();

    // The connection drops, and what was read about a run left halfway is gone with it — so the
    // door the next tab draws cannot say whether it is *Get your level* or *Carry on*.
    act(() => {
      onlineManager.setOnline(false);
      queryClient.removeQueries({ queryKey: onboardingKeys.runInProgress() });
    });
    await openTab(TABS.fillIn);

    expect(
      await screen.findByText("You're offline. This will load as soon as you're back."),
    ).toBeTruthy();
    expect(screen.queryByText(DOOR)).toBeNull();

    act(() => onlineManager.setOnline(true));

    expect(await screen.findByText(DOOR)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// A run left halfway
// ---------------------------------------------------------------------------

describe('a run left halfway', () => {
  it('opens the app normally, on Home, and asks nothing about the run', async () => {
    stubAnia([WEDNESDAY], { leftHalfway: PADEL_RUN });

    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(screen.queryByText(questionOf(PADEL_RUN).text)).toBeNull();
  });

  it(
    'is what the door offers — Carry on, on the question she is on — and opens that run',
    async () => {
      stubAnia([WEDNESDAY], { leftHalfway: PADEL_RUN });
      await openTheGroup(WEDNESDAY);

      // Four answered, so she is on question 5. Never *Get your level*: it never offers to start
      // again.
      expect(await screen.findByText('Carry on with your padel questions')).toBeTruthy();
      expect(screen.getByText("You're on question 5.")).toBeTruthy();
      expect(screen.queryByText(DOOR)).toBeNull();

      fireEvent.press(screen.getByRole('button', { name: 'Carry on' }));

      // Straight into the run, at its outstanding question — no picker, and no new start.
      await rate(PADEL_RUN);
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toEqual([]);
      fireEvent.press(screen.getByLabelText(`Back to ${WEDNESDAY.name}`));

      await expectTheGroup(WEDNESDAY, TABS.games);
      expect(await screen.findByLabelText('Sport: Padel')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );

  it(
    'is offered again after she leaves it to continue later',
    async () => {
      stubAnia([WEDNESDAY], { leftHalfway: PADEL_RUN });
      await openTheGroup(WEDNESDAY);
      await openTab(TABS.friends);

      fireEvent.press(await screen.findByRole('button', { name: 'Carry on' }));
      await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_RUN.id}`));
      fireEvent.press(await screen.findByLabelText('Leave this rating'));
      fireEvent.press(await screen.findByLabelText(/^Continue later\./));

      await expectTheGroup(WEDNESDAY, TABS.friends);
      expect(await screen.findByText('Carry on with your padel questions')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );
});

// ---------------------------------------------------------------------------
// An official group keeps its own card
// ---------------------------------------------------------------------------

describe('a player rated in none of an official group’s sports', () => {
  it('meets its own card, never the door', async () => {
    stubAnia([KAZIMIERZ]);
    await openTheGroup(KAZIMIERZ);

    expect(await screen.findByRole('button', { name: 'Rate Padel' })).toBeTruthy();
    expect(screen.queryByText(DOOR)).toBeNull();
  });
});

/**
 * **Two more ways to the same questions** — *+ Another sport* at the end of a group's sport chip,
 * and *Get your level* on Home ([#731](https://github.com/Raketa02/Raketa/issues/731),
 * [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §4, §5, §7),
 * driven through the real route tree with only `fetch` faked.
 *
 * Ania is rated in padel. In Kuba's player group *Wednesday padel* the chip ends with *+ Another
 * sport*, which opens *Which sports do you play?* over every sport she is unrated in — tennis,
 * squash, badminton — and the pass returns to the group, the chip on the sport just rated. In
 * *Padel & tennis at Kazimierz*, a club's official group, it offers only the group's own sport she
 * is missing: tennis. Rated in everything there is to offer, there is no *+ Another sport*.
 *
 * Rated in nothing, a member of a group who never opens it meets Home's card: *Get your level —
 * your groups can't deal you games until you have one.* It opens the picker, the last *Your rating*
 * says *Back to Home*, and once she holds a rating the card is gone. With a run left halfway it
 * offers to carry on.
 *
 * The notice that opens Home is the notifications suite's (`notifications.test`).
 *
 * Every assertion is about what a player can see or what left the device.
 */

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

import { useOnboardingPass } from '../store/onboardingPass.store';

/** A walk — the group, the chip, the picker, a run and the landing — is longer than five seconds. */
const WALK_TIMEOUT = 30_000;

const ASSESSMENTS_PATH = '/api/v1/assessments';
const RATINGS_PATH = '/api/v1/ratings';
const stepPath = (id: string) => `${ASSESSMENTS_PATH}/${id}`;
const groupPath = (id: string) => `/api/v1/groups/${id}`;

const TABS = GROUPS_COPY.group.tabs;
const ANOTHER_SPORT = GROUPS_COPY.filter.anotherSport;
const ANOTHER_SPORT_DRAWN = GROUPS_COPY.filter.anotherSportDrawn;
const HOME_CARD = 'Get your level';
const HOME_CARD_LINE = "Your groups can't deal you games until you have one.";

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

const PADEL = rating('PADEL', 2.2);

// ---------------------------------------------------------------------------
// The groups
// ---------------------------------------------------------------------------

const WEDNESDAY: Wire['MyGroupSchema'] = {
  id: 'c3000000-0000-4000-8000-000000000731',
  kind: 'PLAYER',
  name: 'Wednesday padel',
  monogram: { letters: 'Wp', colour: 3 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c2000000-0000-4000-8000-000000000731', name: 'Kazimierz Padel Club' },
};

/** A club's official group that plays two sports — padel and tennis, and nothing else. */
const KAZIMIERZ: Wire['MyGroupSchema'] = {
  id: 'c1000000-0000-4000-8000-000000000731',
  kind: 'OFFICIAL',
  name: 'Padel & tennis at Kazimierz',
  monogram: { letters: 'PK', colour: 1 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 9,
  home_club: { id: 'c2000000-0000-4000-8000-000000000731', name: 'Kazimierz Padel Club' },
};

const KUBA: Wire['GroupPersonSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000000731',
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
  id: '4d5e6f70-8192-4a3b-8c4d-5e6f70819731',
  sport: 'PADEL',
  name: 'Padel',
  mu: 1.9,
  level: '1,90',
};
const TENNIS_RUN: Run = {
  id: '5e6f7081-92a3-4b4c-8d5e-6f7081920731',
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
 * Ania, set up, in these groups and rated in `rated` — with no usual game declared for any sport,
 * and a server that runs the questionnaire: a start opens the sport's run, a completion rates it.
 * `leftHalfway` is a run she left with four answers in.
 */
function stubAnia(
  groups: readonly Wire['MyGroupSchema'][],
  {
    rated = [],
    leftHalfway,
  }: { readonly rated?: readonly Wire['RatingResponse'][]; readonly leftHalfway?: Run } = {},
) {
  ratings = [...rated];
  stubGate(transport, { ratings, hasPlayerProfile: true });
  stubProfileSurface(transport, profileSurface({ play_intents: {} }));
  stubProfileOptions(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  transport.on('GET', RATINGS_PATH, () => json<Wire['RatingsResponse']>({ ratings: [...ratings] }));
  stubMyGroups(transport, groups);
  for (const group of groups) {
    transport.on('GET', groupPath(group.id), () => json(pageOf(group)));
    transport.on('GET', `${groupPath(group.id)}/members`, () =>
      json<Wire['GroupMembersResponse']>({ sport: 'PADEL', members: [] }),
    );
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

/** The chip, unfolded — every button its bar offers, as a listener meets them, left to right. */
async function unfoldTheChip(on: string): Promise<string[]> {
  fireEvent.press(await screen.findByRole('button', { name: `Sport: ${on}` }));
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
  return within(screen.getByTestId('sport-bar'))
    .getAllByRole('button')
    .map((option) => option.props.accessibilityLabel as string);
}

/** The picker, and the sports it lists — the ones it offers, in the server's order. */
async function pickerSports(): Promise<string[]> {
  await waitFor(() => expect(screen).toHavePathname('/sports'));
  expect(await screen.findByText('Which sports do you play?')).toBeTruthy();
  await screen.findAllByHintText('Adds this sport');
  return screen
    .getAllByHintText('Adds this sport')
    .map((card) => card.props.accessibilityLabel as string);
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

const started = () => transport.requestsTo('POST', ASSESSMENTS_PATH).map((request) => request.body);

// ---------------------------------------------------------------------------
// + Another sport
// ---------------------------------------------------------------------------

describe('+ Another sport, in a player group', () => {
  it(
    'ends the chip of a player rated in one sport — a choice of one is a choice again',
    async () => {
      stubAnia([WEDNESDAY], { rated: [PADEL] });
      await openTheGroup(WEDNESDAY);

      expect(await unfoldTheChip('Padel')).toEqual([ANOTHER_SPORT, 'Padel']);
      expect(screen.getByText(ANOTHER_SPORT_DRAWN)).toBeTruthy();
    },
    WALK_TIMEOUT,
  );

  it(
    'opens the picker over every sport she is unrated in, and the pass returns to the tab',
    async () => {
      stubAnia([WEDNESDAY], { rated: [PADEL] });
      await openTheGroup(WEDNESDAY);
      await openTab(TABS.fillIn);

      await unfoldTheChip('Padel');
      fireEvent.press(screen.getByRole('button', { name: ANOTHER_SPORT }));

      // Never padel, which she is rated in; nothing ticked.
      expect(await pickerSports()).toEqual(['Tennis', 'Squash', 'Badminton']);
      expect(screen.queryByText('Selected')).toBeNull();

      fireEvent.press(screen.getByLabelText('Tennis'));
      fireEvent.press(screen.getByLabelText('Rate 1 sport'));
      await rate(TENNIS_RUN);
      fireEvent.press(screen.getByLabelText(`Back to ${WEDNESDAY.name}`));

      // Back on Fill in, the chip on the sport just rated, listing both — and still ending with
      // + Another sport, since squash and badminton are left.
      await expectTheGroup(WEDNESDAY, TABS.fillIn);
      expect(await unfoldTheChip('Tennis')).toEqual([ANOTHER_SPORT, 'Padel', 'Tennis']);
      expect(started()).toEqual([{ sport: 'TENNIS' }]);
    },
    WALK_TIMEOUT,
  );

  it(
    'turns back from the picker to the group, having started nothing',
    async () => {
      stubAnia([WEDNESDAY], { rated: [PADEL] });
      await openTheGroup(WEDNESDAY);
      await openTab(TABS.friends);

      await unfoldTheChip('Padel');
      fireEvent.press(screen.getByRole('button', { name: ANOTHER_SPORT }));
      await pickerSports();
      fireEvent.press(await screen.findByLabelText('Back'));

      await expectTheGroup(WEDNESDAY, TABS.friends);
      expect(await screen.findByLabelText('Sport: Padel')).toBeTruthy();
      expect(started()).toEqual([]);
    },
    WALK_TIMEOUT,
  );

  // A call made here: Members' chip is the page's chip, so it ends the same way — and, as the
  // official group's card does there (#729), the pass returns to the page beneath, on its tab.
  it(
    'ends Members’ chip too, whose pass returns to the page beneath it',
    async () => {
      stubAnia([WEDNESDAY], { rated: [PADEL] });
      await openTheGroup(WEDNESDAY);
      await openTab(TABS.friends);
      fireEvent.press(await screen.findByHintText(GROUPS_COPY.group.openInfo));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${WEDNESDAY.id}/info`));
      fireEvent.press(await screen.findByRole('button', { name: /^6 members, / }));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${WEDNESDAY.id}/members`));

      expect(await unfoldTheChip('Padel')).toEqual([ANOTHER_SPORT, 'Padel']);
      fireEvent.press(screen.getByRole('button', { name: ANOTHER_SPORT }));

      expect(await pickerSports()).toEqual(['Tennis', 'Squash', 'Badminton']);
      fireEvent.press(await screen.findByLabelText('Back'));

      await expectTheGroup(WEDNESDAY, TABS.friends);
      expect(started()).toEqual([]);
    },
    WALK_TIMEOUT,
  );

  it(
    'is gone once she is rated in every sport there is',
    async () => {
      stubAnia([WEDNESDAY], {
        rated: [PADEL, rating('TENNIS', 3.1), rating('SQUASH', 2.4), rating('BADMINTON', 1.8)],
      });
      await openTheGroup(WEDNESDAY);

      expect(await unfoldTheChip('Padel')).toEqual(['Tennis', 'Squash', 'Badminton', 'Padel']);
      expect(screen.queryByText(ANOTHER_SPORT_DRAWN)).toBeNull();
    },
    WALK_TIMEOUT,
  );
});

describe('+ Another sport, in an official group', () => {
  it(
    'opens the picker over only the group’s sports she is missing, and returns to the group',
    async () => {
      stubAnia([KAZIMIERZ], { rated: [PADEL] });
      await openTheGroup(KAZIMIERZ);

      await unfoldTheChip('Padel');
      fireEvent.press(screen.getByRole('button', { name: ANOTHER_SPORT }));

      // Tennis alone: squash and badminton are sports this group does not play.
      expect(await pickerSports()).toEqual(['Tennis']);

      fireEvent.press(screen.getByLabelText('Tennis'));
      fireEvent.press(screen.getByLabelText('Rate 1 sport'));
      await rate(TENNIS_RUN);
      fireEvent.press(screen.getByLabelText(`Back to ${KAZIMIERZ.name}`));

      await expectTheGroup(KAZIMIERZ, TABS.games);
      // Rated in both its sports, there is nothing left to offer.
      expect(await unfoldTheChip('Tennis')).toEqual(['Padel', 'Tennis']);
    },
    WALK_TIMEOUT,
  );

  it(
    'is not there for a player rated in everything the group plays',
    async () => {
      stubAnia([KAZIMIERZ], { rated: [PADEL, rating('TENNIS', 3.1)] });
      await openTheGroup(KAZIMIERZ);

      expect(await unfoldTheChip('Padel')).toEqual(['Tennis', 'Padel']);
      expect(screen.queryByText(ANOTHER_SPORT_DRAWN)).toBeNull();
    },
    WALK_TIMEOUT,
  );
});

// ---------------------------------------------------------------------------
// The Home card
// ---------------------------------------------------------------------------

describe('Home, for a member of a group rated in nothing', () => {
  it('says why nothing is happening — the card, over the rail', async () => {
    stubAnia([WEDNESDAY]);
    await launchSignedIn();

    expect(await screen.findByText(HOME_CARD)).toBeTruthy();
    expect(screen.getByText(HOME_CARD_LINE)).toBeTruthy();
    expect(screen.getByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it(
    'opens the picker over every sport, and the last Your rating comes back to Home without it',
    async () => {
      stubAnia([WEDNESDAY]);
      await launchSignedIn();

      fireEvent.press(await screen.findByRole('button', { name: 'Pick your sports' }));
      expect(await pickerSports()).toEqual(['Padel', 'Tennis', 'Squash', 'Badminton']);
      fireEvent.press(screen.getByLabelText('Padel'));
      fireEvent.press(screen.getByLabelText('Rate 1 sport'));
      await rate(PADEL_RUN);
      fireEvent.press(screen.getByLabelText('Back to Home'));

      await waitFor(() => expect(screen).toHavePathname('/'));
      expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
      // She holds a rating now: the card is gone.
      await waitFor(() => expect(screen.queryByText(HOME_CARD)).toBeNull());
      expect(screen.queryByText(HOME_CARD_LINE)).toBeNull();
    },
    WALK_TIMEOUT,
  );

  it(
    'offers to carry on with a run left halfway, and never to start again',
    async () => {
      stubAnia([WEDNESDAY], { leftHalfway: PADEL_RUN });
      await launchSignedIn();

      expect(await screen.findByText('Carry on with your padel questions')).toBeTruthy();
      expect(screen.getByText("You're on question 5.")).toBeTruthy();
      expect(screen.queryByText(HOME_CARD)).toBeNull();

      fireEvent.press(screen.getByRole('button', { name: 'Carry on' }));

      await rate(PADEL_RUN);
      expect(started()).toEqual([]);
      fireEvent.press(screen.getByLabelText('Back to Home'));
      await waitFor(() => expect(screen).toHavePathname('/'));
    },
    WALK_TIMEOUT,
  );
});

describe('Home, for anybody else', () => {
  it('draws no card for a player in no group — there is nothing a level unlocks yet', async () => {
    stubAnia([]);
    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    // Every read the card would be drawn from has answered.
    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/groups')).not.toEqual([]));
    expect(screen.queryByText(HOME_CARD)).toBeNull();
  });

  it('draws no card for a player who holds any rating — and never asks which groups she is in', async () => {
    stubAnia([WEDNESDAY], { rated: [PADEL] });
    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    await waitFor(() => expect(transport.requestsTo('GET', RATINGS_PATH)).not.toEqual([]));
    // The ratings have answered and been drawn from: a rated Home is one read.
    await act(async () => jest.advanceTimersByTime(1));
    expect(screen.queryByText(HOME_CARD)).toBeNull();
    expect(transport.requestsTo('GET', '/api/v1/groups')).toEqual([]);
  });
});

/**
 * **A rating pass begun on a group returns to that group**
 * ([#729](https://github.com/Raketa02/Raketa/issues/729),
 * [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §3, §5), driven
 * through the real route tree with only `fetch` faked.
 *
 * Ania is rated only in squash. *Padel at Kazimierz* is a club's official group and plays padel,
 * so every tab offers its card — *This group plays padel · [Rate Padel]* — and so do Members and
 * *Post a game*. She rates padel from the card and lands back on *Padel at Kazimierz*, on the tab
 * she pressed it on, with the chip on padel — not on the Skill passport. *Wednesday padel* is
 * Kuba's player group: a pass over two sports begun there (the picker opened from a group's tab,
 * the door #730 puts on it) offers *Rate Tennis* and *Done for now* after padel, and *Back to
 * Wednesday padel* after the last.
 *
 * A pass begun on the Skill passport still ends there: `addASport.test` proves it, unchanged.
 *
 * Every assertion is about what a player can see or what left the device.
 */

import { useNavigation } from 'expo-router';
import { fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { GROUPS_COPY } from '@/features/groups/types';
import {
  beginSession,
  clearStoredTokens,
  resetSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { stubGroupDeck } from '@/test-support/groupDeck';
import {
  ONBOARDING_ROUTES,
  SPORTS_SERVED,
  launchSignedIn,
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

/**
 * A walk — the group, the card, the run, the review, the calculating screen's hold, the result
 * and the landing — is longer than jest's five seconds under the harness's fake timers.
 */
const WALK_TIMEOUT = 30_000;

const ASSESSMENTS_PATH = '/api/v1/assessments';
const RATINGS_PATH = '/api/v1/ratings';
const stepPath = (id: string) => `${ASSESSMENTS_PATH}/${id}`;
const groupPath = (id: string) => `/api/v1/groups/${id}`;

const TABS = GROUPS_COPY.group.tabs;

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

/** Ania's one rating: she is in the app, and rated in none of *Padel at Kazimierz*'s sports. */
const SQUASH = rating('SQUASH', 2.2);

// ---------------------------------------------------------------------------
// The groups
// ---------------------------------------------------------------------------

const KAZIMIERZ: Wire['MyGroupSchema'] = {
  id: 'c1000000-0000-4000-8000-000000000729',
  kind: 'OFFICIAL',
  name: 'Padel at Kazimierz',
  monogram: { letters: 'PK', colour: 1 },
  sports: ['PADEL'],
  member_count: 9,
  home_club: { id: 'c2000000-0000-4000-8000-000000000729', name: 'Kazimierz Padel Club' },
};

const WEDNESDAY: Wire['MyGroupSchema'] = {
  id: 'c3000000-0000-4000-8000-000000000729',
  kind: 'PLAYER',
  name: 'Wednesday padel',
  monogram: { letters: 'Wp', colour: 3 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c2000000-0000-4000-8000-000000000729', name: 'Kazimierz Padel Club' },
};

const MARTA: Wire['GroupPersonSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000000729',
  nickname: 'marta.w',
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
      { sport: 'PADEL', rated_count: 8, first_rated: [MARTA] },
      { sport: 'TENNIS', rated_count: 1, first_rated: [MARTA] },
      { sport: 'SQUASH', rated_count: 1, first_rated: [MARTA] },
      { sport: 'BADMINTON', rated_count: 0, first_rated: [] },
    ],
    member_faces: [MARTA],
    administrator_nickname: official ? MARTA.nickname : null,
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
  id: '4d5e6f70-8192-4a3b-8c4d-5e6f70819729',
  sport: 'PADEL',
  name: 'Padel',
  mu: 1.9,
  level: '1,90',
};
const TENNIS_RUN: Run = {
  id: '5e6f7081-92a3-4b4c-8d5e-6f7081920729',
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

function openingOf(run: Run): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: run.id,
    status: 'in_progress',
    questions_asked: 0,
    transcript: [],
    question: questionOf(run),
  };
}

/** One answer in, and the engine has stopped: the review is next. */
function stoppedOf(run: Run): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: run.id,
    status: 'in_progress',
    questions_asked: 1,
    transcript: [{ question: questionOf(run), option_id: 'regular' }],
    question: null,
    result: null,
  };
}

function ratedOf(run: Run): Wire['AssessmentStepResponse'] {
  return {
    ...stoppedOf(run),
    status: 'completed',
    result: {
      mu: run.mu,
      sigma: 0.7,
      confidence: 24,
      confidence_ceiling: 30,
      range: { low: run.mu - 0.7, high: run.mu + 0.7 },
      band: { name: 'Developing', lower: 1.6, upper: 2.6 },
      status: 'initial_estimate',
      questions_asked: 1,
      engine_version: 'racketskill-v3',
      calibration_priority: 'standard',
    },
  };
}

let transport: Transport;
/** What `GET /ratings` says now — a completion adds to it. */
let ratings: Wire['RatingResponse'][];

/**
 * Ania, set up long ago and rated in squash, with these groups — and a server that runs the
 * questionnaire: a start opens the sport's run, a completion rates it, an abandonment ends it.
 */
function stubAnia(groups: readonly Wire['MyGroupSchema'][]) {
  ratings = [SQUASH];
  stubGate(transport, { ratings, hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  transport.on('GET', RATINGS_PATH, () => json<Wire['RatingsResponse']>({ ratings: [...ratings] }));
  stubMyGroups(transport, groups);
  for (const group of groups) {
    transport.on('GET', groupPath(group.id), () => json(pageOf(group)));
    stubGroupDeck(transport, group.id);
  }

  transport.on('POST', ASSESSMENTS_PATH, (request) => {
    const { sport } = request.body as { readonly sport: Wire['Sport'] };
    const run = RUNS.find((one) => one.sport === sport)!;
    stubRunsInProgress(transport, [{ assessment_id: run.id, sport }]);
    return json(openingOf(run), 201);
  });
  for (const run of RUNS) {
    transport.on('GET', stepPath(run.id), () => json(openingOf(run)));
    transport.on('POST', `${stepPath(run.id)}/answers`, () => json(stoppedOf(run)));
    transport.on('POST', `${stepPath(run.id)}/completion`, () => {
      stubRunsInProgress(transport, []);
      ratings = [...ratings, rating(run.sport, run.mu)];
      return json(ratedOf(run));
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

/** One sport's questionnaire, walked from its opening question to *Your rating*. */
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

const backTo = (group: Wire['MyGroupSchema']) => `Back to ${group.name}`;

// ---------------------------------------------------------------------------
// The official group's card
// ---------------------------------------------------------------------------

describe('a pass begun on an official group’s card', () => {
  // You’re in is a tab of its own since #847, and a pass begun there returns there.
  it.each([TABS.fillIn, TABS.youreIn])(
    'ends back on the group, on the tab it began on (%s), with the chip on padel',
    async (began) => {
      stubAnia([KAZIMIERZ]);
      await openTheGroup(KAZIMIERZ);
      await openTab(began);

      fireEvent.press(await screen.findByRole('button', { name: 'Rate Padel' }));
      await rate(PADEL_RUN);

      // One control, and it names where she is going — not the passport's *See your ratings*.
      expect(screen.queryByLabelText('Done for now')).toBeNull();
      expect(screen.queryByLabelText('See your ratings')).toBeNull();
      fireEvent.press(screen.getByLabelText(backTo(KAZIMIERZ)));

      await expectTheGroup(KAZIMIERZ, began);
      // The chip stands on the sport just rated, and the card is gone: she plays here now.
      expect(await screen.findByLabelText('Sport: Padel')).toBeTruthy();
      expect(screen.queryByRole('button', { name: 'Rate Padel' })).toBeNull();
    },
    WALK_TIMEOUT,
  );

  it(
    'lands the group with Play beneath it, so back is the Groups list',
    async () => {
      stubAnia([KAZIMIERZ]);
      await openTheGroup(KAZIMIERZ);

      fireEvent.press(await screen.findByRole('button', { name: 'Rate Padel' }));
      await rate(PADEL_RUN);
      fireEvent.press(screen.getByLabelText(backTo(KAZIMIERZ)));
      await expectTheGroup(KAZIMIERZ, TABS.games);

      fireEvent.press(await screen.findByLabelText(GROUPS_COPY.group.back));

      await waitFor(() => expect(screen).toHavePathname('/play'));
    },
    WALK_TIMEOUT,
  );

  it(
    'draws the group as the first screen back in the app — Home is never on top on the way',
    async () => {
      // The app's tree is torn down while the questions are up, and comes back at `/` — Home. A
      // landing that waited for Home to be drawn before laying the group over it showed Home for a
      // frame and then slid the group in: a blink. Home is still beneath, so it is watched for being
      // drawn as the screen on top, not for being drawn at all.
      let homeOnTop = 0;
      const Home = ONBOARDING_ROUTES['(app)/(tabs)/index'];
      function WatchedHome() {
        if (useNavigation().isFocused()) homeOnTop += 1;
        return <Home />;
      }
      stubAnia([KAZIMIERZ]);
      await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
      renderRouter(
        { ...ONBOARDING_ROUTES, '(app)/(tabs)/index': WatchedHome },
        { initialUrl: '/' },
      );
      fireEvent.press(await screen.findByLabelText('Play'));
      await waitFor(() => expect(screen).toHavePathname('/play'));
      fireEvent.press(
        await screen.findByRole('button', { name: new RegExp(`^${KAZIMIERZ.name}, `) }),
      );
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${KAZIMIERZ.id}`));
      fireEvent.press(await screen.findByRole('button', { name: 'Rate Padel' }));
      await rate(PADEL_RUN);
      homeOnTop = 0;

      fireEvent.press(screen.getByLabelText(backTo(KAZIMIERZ)));

      await expectTheGroup(KAZIMIERZ, TABS.games);
      expect(homeOnTop).toBe(0);
      // And the stack beneath is still Play's: back is the Groups list, then Home.
      fireEvent.press(await screen.findByLabelText(GROUPS_COPY.group.back));
      await waitFor(() => expect(screen).toHavePathname('/play'));
    },
    WALK_TIMEOUT,
  );

  it(
    'ends back on the group when she leaves the questions to continue later',
    async () => {
      stubAnia([KAZIMIERZ]);
      await openTheGroup(KAZIMIERZ);
      await openTab(TABS.friends);

      fireEvent.press(await screen.findByRole('button', { name: 'Rate Padel' }));
      await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_RUN.id}`));
      fireEvent.press(await screen.findByLabelText('Leave this rating'));
      fireEvent.press(await screen.findByLabelText(/^Continue later\./));

      await expectTheGroup(KAZIMIERZ, TABS.friends);
      // Nothing was rated, so the card is offered again.
      expect(await screen.findByRole('button', { name: 'Rate Padel' })).toBeTruthy();
    },
    WALK_TIMEOUT,
  );

  it(
    'ends back on the group from Members’ card, on the tab beneath it',
    async () => {
      stubAnia([KAZIMIERZ]);
      await openTheGroup(KAZIMIERZ);
      await openTab(TABS.friends);
      fireEvent.press(await screen.findByHintText(GROUPS_COPY.group.openInfo));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${KAZIMIERZ.id}/info`));
      fireEvent.press(await screen.findByRole('button', { name: /^9 members, / }));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${KAZIMIERZ.id}/members`));

      fireEvent.press(await screen.findByRole('button', { name: 'Rate Padel' }));
      await rate(PADEL_RUN);
      fireEvent.press(screen.getByLabelText(backTo(KAZIMIERZ)));

      await expectTheGroup(KAZIMIERZ, TABS.friends);
      expect(await screen.findByLabelText('Sport: Padel')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );
});

describe('a pass begun on Post a game’s card', () => {
  it(
    'ends back on the group, on You’re in, where every way back from Post a game lands (#847)',
    async () => {
      stubAnia([KAZIMIERZ]);
      await launchSignedIn(`/play/group/${KAZIMIERZ.id}/post`);
      expect(await screen.findByText('Get rated in padel to post here')).toBeTruthy();

      fireEvent.press(screen.getByRole('button', { name: 'Rate Padel' }));
      await rate(PADEL_RUN);
      fireEvent.press(screen.getByLabelText(backTo(KAZIMIERZ)));

      await expectTheGroup(KAZIMIERZ, TABS.youreIn);
      expect(await screen.findByLabelText('Sport: Padel')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );
});

// ---------------------------------------------------------------------------
// A pass over two sports, begun on a group's tab
// ---------------------------------------------------------------------------

/** The picker, opened from *Wednesday padel*'s Friends tab — the door #730 draws there. */
async function pickFromWednesday(...sports: readonly string[]) {
  stubAnia([WEDNESDAY]);
  await launchSignedIn(`/sports?groupId=${WEDNESDAY.id}&tab=friends`);
  expect(await screen.findByText('Which sports do you play?')).toBeTruthy();
  for (const sport of sports) fireEvent.press(await screen.findByLabelText(sport));
  fireEvent.press(screen.getByLabelText(`Rate ${sports.length} sports`));
}

describe('a pass over two sports begun on a group', () => {
  it(
    'offers Rate Tennis after padel, then Back to Wednesday padel, on the tab, chip on tennis',
    async () => {
      await pickFromWednesday('Padel', 'Tennis');
      await rate(PADEL_RUN);

      // Mid-pass: the next sport, or stopping here — never the way back yet.
      expect(screen.getByLabelText('Rate Tennis')).toBeTruthy();
      expect(screen.getByLabelText('Done for now')).toBeTruthy();
      expect(screen.queryByLabelText(backTo(WEDNESDAY))).toBeNull();
      fireEvent.press(screen.getByLabelText('Rate Tennis'));

      await rate(TENNIS_RUN);
      expect(screen.queryByLabelText('Done for now')).toBeNull();
      fireEvent.press(screen.getByLabelText(backTo(WEDNESDAY)));

      await expectTheGroup(WEDNESDAY, TABS.friends);
      // A player group plays whatever she is rated in, and it stands on the sport just rated.
      expect(await screen.findByLabelText('Sport: Tennis')).toBeTruthy();
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH).map((request) => request.body)).toEqual(
        [{ sport: 'PADEL' }, { sport: 'TENNIS' }],
      );
    },
    WALK_TIMEOUT,
  );

  it(
    'returns to the group on Done for now, with the chip on padel',
    async () => {
      await pickFromWednesday('Padel', 'Tennis');
      await rate(PADEL_RUN);

      fireEvent.press(screen.getByLabelText('Done for now'));

      await expectTheGroup(WEDNESDAY, TABS.friends);
      expect(await screen.findByLabelText('Sport: Padel')).toBeTruthy();
      // Tennis was skipped, not started.
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH).map((request) => request.body)).toEqual(
        [{ sport: 'PADEL' }],
      );
    },
    WALK_TIMEOUT,
  );
});

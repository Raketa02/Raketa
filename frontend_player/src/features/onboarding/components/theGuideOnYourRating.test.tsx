/**
 * **The guide on _Your rating_** ([#732](https://github.com/Raketa02/Raketa/issues/732),
 * [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8), walked
 * through the real route tree with only `fetch` faked.
 *
 * Ania is rated in nothing and picks padel and tennis from Home's picker. On her first *Your
 * rating* the screen dims and a bubble explains her level (*1 of 3*), then the likely range, then
 * the confidence (*3 of 3*, *Got it*) — the ⓘ marks' own words, one at a time. A tap on the dim is
 * *Next*, *Skip* ends it, nothing beneath it answers while it is up, and **the phone never shows
 * it again** — not on tennis, and not to whoever signs in on it next. The Skill passport's cards
 * never run it.
 *
 * The device's storage is jest's in-memory AsyncStorage, emptied after every test, so every test
 * here begins on a phone that has never shown the guide. What the guide does on Android's back
 * button is `Guide.test`'s, because the harness runs as iOS.
 *
 * Every assertion is about what a player can see or what left the device.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { SKILL_PASSPORT_TITLE } from '@/features/player_record/types';
import {
  clearStoredTokens,
  endSession,
  resetSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  SPORTS_SERVED,
  launchSignedIn,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
  stubRunsInProgress,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useOnboardingPass } from '../store/onboardingPass.store';

/** The picker, two runs, their reviews and the calculating screen's hold, under fake timers. */
const WALK_TIMEOUT = 30_000;

/** The dim is hidden from a listener — the bubble's controls carry the names — so a walk looks for it. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

const ASSESSMENTS_PATH = '/api/v1/assessments';
const RATINGS_PATH = '/api/v1/ratings';
const stepPath = (id: string) => `${ASSESSMENTS_PATH}/${id}`;

/** The ⓘ marks' words, which are the guide's (ADR-0200 §8). */
const LEVEL_WORDS = /^Where you sit on the 1,00–5,00 scale for this sport\./;
const RANGE_WORDS = /^Where Raketa thinks your level most likely sits/;
const CONFIDENCE_WORDS = /^Shows how confident Raketa is about your level/;
/** Bubble 3 keeps the ceiling, so a 24 % does not read as Raketa doubting her (Q7). */
const CEILING_SENTENCE = /The questionnaire can provide up to 30% confidence\./;

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
// The runs, as a server that performs their transitions
// ---------------------------------------------------------------------------

interface Run {
  readonly id: string;
  readonly sport: Wire['Sport'];
  readonly name: string;
  readonly mu: number;
  /** The level *Your rating* leads with — how the walk knows it arrived. */
  readonly level: string;
}

const PADEL_RUN: Run = {
  id: '4d5e6f70-8192-4a3b-8c4d-5e6f70819732',
  sport: 'PADEL',
  name: 'Padel',
  mu: 1.9,
  level: '1,90',
};
const TENNIS_RUN: Run = {
  id: '5e6f7081-92a3-4b4c-8d5e-6f7081920732',
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

/** Ania, set up and rated in nothing — and a server that runs the questionnaire. */
function stubAnia(id?: string) {
  ratings = [];
  stubGate(transport, { ratings, hasPlayerProfile: true, ...(id === undefined ? {} : { id }) });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  transport.on('GET', RATINGS_PATH, () => json<Wire['RatingsResponse']>({ ratings: [...ratings] }));

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
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// Walking
// ---------------------------------------------------------------------------

/** Home's picker, these sports ticked, and the pass begun. */
async function pick(...sports: readonly string[]) {
  await launchSignedIn('/sports');
  expect(await screen.findByText('Which sports do you play?')).toBeTruthy();
  for (const sport of sports) fireEvent.press(await screen.findByLabelText(sport));
  fireEvent.press(
    screen.getByLabelText(sports.length === 1 ? 'Rate 1 sport' : `Rate ${sports.length} sports`),
  );
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
}

/** The bubble, on this step of three. */
async function expectBubble(step: number, title: string, words: RegExp) {
  expect(await screen.findByText(`${step} of 3`)).toBeTruthy();
  expect(screen.getByRole('header', { name: title })).toBeTruthy();
  expect(screen.getByText(words)).toBeTruthy();
}

/** The guide is down, and *Your rating* is the screen again. */
async function expectNoGuide(run: Run) {
  expect(await screen.findByText(run.level)).toBeTruthy();
  expect(screen.queryByText(/ of 3$/)).toBeNull();
  expect(screen.queryByRole('button', { name: 'Skip the guide' })).toBeNull();
}

// ---------------------------------------------------------------------------
// The first Your rating
// ---------------------------------------------------------------------------

describe('the first Your rating a phone shows', () => {
  it(
    'explains the level, the likely range and the confidence, one at a time, in that order',
    async () => {
      stubAnia();
      await pick('Padel', 'Tennis');
      await rate(PADEL_RUN);

      // The screen beneath is dimmed out of reach, so a listener finds the bubble alone.
      await expectBubble(1, 'Your Level', LEVEL_WORDS);
      expect(screen.queryByText(PADEL_RUN.level)).toBeNull();
      expect(screen.getByRole('button', { name: 'Skip the guide' })).toBeTruthy();
      fireEvent.press(screen.getByRole('button', { name: 'Next' }));

      await expectBubble(2, 'Your likely range', RANGE_WORDS);
      // A habitual tap off the bubble moves the guide on rather than throwing it away.
      fireEvent.press(screen.getByTestId('guide-dim', HIDDEN_TOO));

      await expectBubble(3, 'Confidence', CONFIDENCE_WORDS);
      expect(screen.getByText(CEILING_SENTENCE)).toBeTruthy();
      expect(screen.queryByRole('button', { name: 'Next' })).toBeNull();
      fireEvent.press(screen.getByRole('button', { name: 'Got it' }));

      await expectNoGuide(PADEL_RUN);
      expect(screen.getByLabelText('Rate Tennis')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );

  it(
    'ends on Skip, from any step',
    async () => {
      stubAnia();
      await pick('Padel');
      await rate(PADEL_RUN);
      await expectBubble(1, 'Your Level', LEVEL_WORDS);
      fireEvent.press(screen.getByRole('button', { name: 'Next' }));
      await expectBubble(2, 'Your likely range', RANGE_WORDS);

      fireEvent.press(screen.getByRole('button', { name: 'Skip the guide' }));

      await expectNoGuide(PADEL_RUN);
      // The ⓘ marks stay, for re-reading any one number.
      fireEvent.press(screen.getByLabelText('What your likely range means'));
      expect(await screen.findByText(RANGE_WORDS)).toBeTruthy();
      expect(screen.getByLabelText('Close Your likely range')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );

  it(
    'lets nothing beneath it answer while it is up',
    async () => {
      stubAnia();
      await pick('Padel', 'Tennis');
      await rate(PADEL_RUN);
      await expectBubble(1, 'Your Level', LEVEL_WORDS);

      // Pressed anyway, past the dim: the next sport, stopping, and an ⓘ mark.
      fireEvent.press(screen.getByLabelText('Rate Tennis', HIDDEN_TOO));
      fireEvent.press(screen.getByLabelText('Done for now', HIDDEN_TOO));
      fireEvent.press(screen.getByLabelText('What Confidence means', HIDDEN_TOO));

      // Still on her rating, still on the guide's first step, and nothing left the device.
      expect(screen).toHavePathname(`/result/${PADEL_RUN.id}`);
      expect(screen.getByText('1 of 3')).toBeTruthy();
      expect(screen.queryByLabelText('Close Confidence')).toBeNull();
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(1);
    },
    WALK_TIMEOUT,
  );
});

// ---------------------------------------------------------------------------
// Once per phone
// ---------------------------------------------------------------------------

describe('once per phone', () => {
  it(
    'shows no guide on a second rating',
    async () => {
      stubAnia();
      await pick('Padel', 'Tennis');
      await rate(PADEL_RUN);
      await expectBubble(1, 'Your Level', LEVEL_WORDS);
      fireEvent.press(screen.getByRole('button', { name: 'Skip the guide' }));
      await expectNoGuide(PADEL_RUN);

      fireEvent.press(screen.getByLabelText('Rate Tennis'));
      await rate(TENNIS_RUN);

      await expectNoGuide(TENNIS_RUN);
      expect(screen.getByLabelText('Back to Home')).toBeTruthy();
    },
    WALK_TIMEOUT,
  );

  it(
    'shows no guide to whoever signs in on the phone next',
    async () => {
      stubAnia();
      await pick('Padel');
      await rate(PADEL_RUN);
      await expectBubble(1, 'Your Level', LEVEL_WORDS);
      fireEvent.press(screen.getByRole('button', { name: 'Skip the guide' }));
      await expectNoGuide(PADEL_RUN);

      // Signed out, the app closed, and somebody else on the same phone: the account's choices
      // went with the session, and the phone's fact did not (ADR-0200 §8).
      screen.unmount();
      await endSession('requested');
      // The sign-out drops the cache after the old session's work is cancelled, and does not wait
      // for it — so wait here, or the drop lands on the next session's first reads.
      await waitFor(() => expect(queryClient.getQueryCache().getAll()).toHaveLength(0));
      useOnboardingPass.getState().reset();
      resetSessionStatus();
      stubAnia('22222222-3333-4444-8555-666666666732');
      await pick('Tennis');
      await rate(TENNIS_RUN);

      await expectNoGuide(TENNIS_RUN);
    },
    WALK_TIMEOUT,
  );
});

// ---------------------------------------------------------------------------
// The passport
// ---------------------------------------------------------------------------

describe('the Skill passport', () => {
  it(
    'never runs the guide on its cards, even on a phone that has never shown it',
    async () => {
      stubAnia();
      ratings = [rating('PADEL', 1.9)];
      stubGate(transport, { ratings, hasPlayerProfile: true });
      stubOwnRecord(transport);

      await launchSignedIn();
      fireEvent.press(await screen.findByLabelText('You'));
      fireEvent.press(await screen.findByLabelText(SKILL_PASSPORT_TITLE, { exact: false }));
      await screen.findByRole('header', { name: SKILL_PASSPORT_TITLE });

      await expectNoGuide(PADEL_RUN);
    },
    WALK_TIMEOUT,
  );
});

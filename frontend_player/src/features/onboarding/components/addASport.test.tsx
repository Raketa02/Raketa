/**
 * **The second door into the onboarding pass** — a pass begun at the Skill passport's *Add a
 * sport* ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3), driven through the real route tree with only `fetch` faked.
 *
 * What is proved is the pass's *origin* doing its one job: the chip begins a pass of exactly one
 * sport at the question route, the questionnaire between is onboarding's own, and every way out
 * of it — *See your ratings*, *continue later*, *abandon* — lands back on the passport. The
 * admission rule keeps its refusals on the way. Passes begun on a group are
 * `aPassFromAGroup.test`'s and `theDoorWherePlayBegins.test`'s.
 *
 * Every assertion is about what a player can see or what left the device.
 */

import { cleanup, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { ADD_A_SPORT, SKILL_PASSPORT_TITLE, rateSportChip } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  HOME_TAB_LINE,
  SPORTS_SERVED,
  launchSignedIn,
  stubGate as stubGateWith,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
  stubRunsInProgress,
  ratingGuideAlreadyShown,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  networkFailure,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FROM_THE_PASSPORT } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { ratingStatusLabel } from './bandPresentation';
import { passEyebrow } from './passEyebrow';

const BADMINTON_RUN = '4d5e6f70-8192-4a3b-8c4d-5e6f70819203';

/**
 * The whole walk — a launch, the tab, the passport, the run, the review, the calculating
 * screen's hold, the result and the landing — is longer than jest's five seconds under the
 * harness's fake timers, which `waitFor` advances one tick at a time.
 */
const WALK_TIMEOUT = 20_000;
const STRANGE_LINK_ID = 'e5f6a7b8-9c0d-4e1f-8a2b-3c4d5e6f7a8b';

const ASSESSMENTS_PATH = '/api/v1/assessments';
const RATINGS_PATH = '/api/v1/ratings';
const stepPath = (id: string) => `${ASSESSMENTS_PATH}/${id}`;

function rating(sport: Wire['Sport'], over: Partial<Wire['RatingResponse']> = {}) {
  return {
    sport,
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
    ...over,
  } satisfies Wire['RatingResponse'];
}

/** Tomek: rated at padel, tennis and squash. Badminton is the one chip on his passport. */
const THREE_RATED: readonly Wire['RatingResponse'][] = [
  rating('PADEL', { status: 'calibrating', confidence: 61 }),
  rating('TENNIS', { mu: 3.1 }),
  rating('SQUASH', { mu: 2.2, band: { name: 'Developing', lower: 1.6, upper: 2.6 } }),
];

const PLAYED_QUESTION: Wire['QuestionResponse'] = {
  id: 'q-played',
  category: 'Recent activity',
  tier: null,
  situation: 'Before anything else',
  text: 'Have you played badminton before?',
  qualifier: 'Any level counts',
  options: [
    { id: 'never', text: 'Never played' },
    { id: 'regular', text: 'I play most weeks' },
  ],
};

const OPENING: Wire['AssessmentStepResponse'] = {
  assessment_id: BADMINTON_RUN,
  status: 'in_progress',
  questions_asked: 0,
  transcript: [],
  question: PLAYED_QUESTION,
};

/** One answer in, and the engine has stopped: the review is next. */
const STOPPED: Wire['AssessmentStepResponse'] = {
  assessment_id: BADMINTON_RUN,
  status: 'in_progress',
  questions_asked: 1,
  transcript: [{ question: PLAYED_QUESTION, option_id: 'regular' }],
  question: null,
  result: null,
};

const BADMINTON_RESULT: Wire['ResultResponse'] = {
  mu: 1.9,
  sigma: 0.7,
  confidence: 24,
  confidence_ceiling: 30,
  range: { low: 1.2, high: 2.6 },
  band: { name: 'Developing', lower: 1.6, upper: 2.6 },
  status: 'initial_estimate',
  questions_asked: 1,
  engine_version: 'racketskill-v3',
  calibration_priority: 'standard',
};

const RATED: Wire['AssessmentStepResponse'] = {
  assessment_id: BADMINTON_RUN,
  status: 'completed',
  questions_asked: 1,
  transcript: STOPPED.transcript,
  question: null,
  result: BADMINTON_RESULT,
};

/** What `GET /ratings` says once the run is over: the fourth card. */
const BADMINTON_RATING = rating('BADMINTON', {
  mu: 1.9,
  confidence: 24,
  range: { low: 1.2, high: 2.6 },
  band: { name: 'Developing', lower: 1.6, upper: 2.6 },
});

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

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

/** A relaunch: the process is gone, so the cache and every in-memory store go with it. */
async function relaunch() {
  cleanup();
  queryClient.clear();
  useOnboardingPass.getState().reset();
  resetSessionStatus();
  await launchSignedIn();
}

/** A player long since set up, on their passport, with one sport left to rate. */
async function onThePassport() {
  stubGate({ ratings: THREE_RATED, hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(await screen.findByLabelText(SKILL_PASSPORT_TITLE, { exact: false }));
  await screen.findByRole('header', { name: SKILL_PASSPORT_TITLE });
  await screen.findByLabelText(rateSportChip('badminton'));
}

/**
 * A server that performs the transitions: the start creates the run and reports it
 * unfinished; completion ends it and adds the rating; abandonment ends it and adds nothing.
 */
function serveTheRun() {
  transport.on('POST', ASSESSMENTS_PATH, () => {
    stubRunsInProgress(transport, [{ assessment_id: BADMINTON_RUN, sport: 'BADMINTON' }]);
    return json(OPENING, 201);
  });
  transport.on('GET', stepPath(BADMINTON_RUN), () => json(OPENING));
  transport.on('POST', `${stepPath(BADMINTON_RUN)}/answers`, () => json(STOPPED));
  transport.on('POST', `${stepPath(BADMINTON_RUN)}/completion`, () => {
    stubRunsInProgress(transport, []);
    transport.on('GET', RATINGS_PATH, () =>
      json<Wire['RatingsResponse']>({ ratings: [...THREE_RATED, BADMINTON_RATING] }),
    );
    return json(RATED);
  });
  transport.on('POST', `${stepPath(BADMINTON_RUN)}/abandonment`, () => {
    stubRunsInProgress(transport, []);
    return noContent();
  });
}

async function rateBadminton() {
  serveTheRun();
  fireEvent.press(screen.getByLabelText(rateSportChip('badminton')));
  await waitFor(() => expect(screen).toHavePathname(`/question/${BADMINTON_RUN}`));
  expect(await screen.findByText(PLAYED_QUESTION.text)).toBeTruthy();
}

const openTheConfirm = () => fireEvent.press(screen.getByLabelText('Leave this rating'));

/** The questionnaire's own screens, walked: the one answer, the review, the held calculating
 * screen, and the result — every one of them onboarding's, unchanged. */
async function walkToTheResult() {
  fireEvent.press(screen.getByLabelText('I play most weeks'));
  fireEvent.press(screen.getByLabelText('Confirm answer'));
  await waitFor(() => expect(screen).toHavePathname(`/review/${BADMINTON_RUN}`));
  fireEvent.press(await screen.findByLabelText('Get my Badminton level'));
  await waitFor(() => expect(screen).toHavePathname(`/result/${BADMINTON_RUN}`), {
    timeout: 4000,
  });
  expect(await screen.findByText('1,90')).toBeTruthy();
}

async function expectThePassport() {
  await waitFor(() => expect(screen).toHavePathname('/you/passport'), { timeout: 4000 });
  expect(await screen.findByRole('header', { name: SKILL_PASSPORT_TITLE })).toBeTruthy();
}

// ---------------------------------------------------------------------------
// The chip begins a pass
// ---------------------------------------------------------------------------

describe('Add a sport', () => {
  it('begins a pass of that one sport at the question route, as onboarding asks it', async () => {
    await onThePassport();

    await rateBadminton();

    // One start, naming the sport — the same request the picker sends.
    const [started] = transport.requestsTo('POST', ASSESSMENTS_PATH);
    expect(started?.body).toEqual({ sport: 'BADMINTON' });
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(1);
    // The questionnaire's own chrome: a pass of one sport, honestly counted.
    expect(screen.getByText(passEyebrow('badminton', { index: 1, total: 1 }))).toBeTruthy();
    // Not the picker: the chip named the sport, so there is nothing to choose.
    expect(screen.queryByText('Which sports do you play?')).toBeNull();
  });

  it('says the start is under way, and sends one however fast the chip is tapped', async () => {
    await onThePassport();
    let open = () => {};
    const held = new Promise<void>((resolve) => {
      open = resolve;
    });
    transport.on('POST', ASSESSMENTS_PATH, async () => {
      await held;
      return json(OPENING, 201);
    });
    transport.on('GET', stepPath(BADMINTON_RUN), () => json(OPENING));

    fireEvent.press(screen.getByLabelText(rateSportChip('badminton')));
    expect(await screen.findByLabelText('Starting…')).toBeTruthy();
    fireEvent.press(screen.getByLabelText('Starting…'));

    open();
    await waitFor(() => expect(screen).toHavePathname(`/question/${BADMINTON_RUN}`));
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(1);
  });

  it('says so on the passport when the start fails, and offers the chip again', async () => {
    await onThePassport();
    transport.on('POST', ASSESSMENTS_PATH, networkFailure());

    fireEvent.press(screen.getByLabelText(rateSportChip('badminton')));

    expect(
      await screen.findByText("We couldn't reach Rakieta. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen.getByRole('alert')).toBeTruthy();
    // Still on the passport, chip pressable: a failed start began nothing.
    expect(screen).toHavePathname('/you/passport');
    expect(screen.getByLabelText(rateSportChip('badminton'))).toBeTruthy();

    serveTheRun();
    fireEvent.press(screen.getByLabelText(rateSportChip('badminton')));
    await waitFor(() => expect(screen).toHavePathname(`/question/${BADMINTON_RUN}`));
  });
});

// ---------------------------------------------------------------------------
// The walk: question → review → result → the passport
// ---------------------------------------------------------------------------

describe('a pass begun at the passport', () => {
  it(
    'walks the questionnaire and ends on the passport with the new card drawn',
    async () => {
      await onThePassport();
      const ratingsReadsBefore = transport.requestsTo('GET', RATINGS_PATH).length;
      await rateBadminton();
      await walkToTheResult();

      // One control, and it names what is next — the passport, which *is* your ratings.
      expect(screen.queryByText('Done for now')).toBeNull();
      fireEvent.press(screen.getByLabelText('See your ratings'));

      await expectThePassport();
      // The ratings were re-read from the server, and the fourth card is drawn from them: the
      // sport tag across its top, and its status said twice per card — the chip across the top
      // and the *Rating status* row under the bar — so three estimates read six times.
      expect(transport.requestsTo('GET', RATINGS_PATH).length).toBeGreaterThan(ratingsReadsBefore);
      expect(await screen.findByText('Badminton')).toBeTruthy();
      expect(screen.getAllByText(ratingStatusLabel('initial_estimate'))).toHaveLength(6);
      expect(screen.getAllByText(ratingStatusLabel('calibrating'))).toHaveLength(2);
      // And no chip for it any more — nothing is left to add; the card is drawn for nobody.
      expect(screen.queryByLabelText(rateSportChip('badminton'))).toBeNull();
      expect(screen.queryByText(ADD_A_SPORT)).toBeNull();
    },
    WALK_TIMEOUT,
  );

  it(
    'never shows the profile steps, or a summary of the pass',
    async () => {
      await onThePassport();
      await rateBadminton();
      await walkToTheResult();

      fireEvent.press(screen.getByLabelText('See your ratings'));

      await expectThePassport();
      expect(screen.queryByText('Your starting ratings')).toBeNull();
      expect(screen.queryByText(/Step 1 of 6/)).toBeNull();
      // A pass begun here returns to no group, so no group is read to name the way back (#729).
      expect(transport.requests.filter((r) => r.path.startsWith('/api/v1/groups/'))).toEqual([]);
    },
    WALK_TIMEOUT,
  );

  it(
    'lands on the passport with the You tab beneath it, so back goes where it came from',
    async () => {
      await onThePassport();
      await rateBadminton();
      await walkToTheResult();
      fireEvent.press(screen.getByLabelText('See your ratings'));
      await expectThePassport();

      fireEvent.press(screen.getByLabelText('Back'));

      await waitFor(() => expect(screen).toHavePathname('/you'));
    },
    WALK_TIMEOUT,
  );
});

// ---------------------------------------------------------------------------
// Leaving mid-run
// ---------------------------------------------------------------------------

describe('leaving a pass begun at the passport', () => {
  it('returns to the passport on continue later, sending nothing', async () => {
    await onThePassport();
    await rateBadminton();

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Continue later\./));

    await expectThePassport();
    // Nothing was written — not an abandonment, not anything else after the start.
    expect(transport.requests.filter((r) => r.method !== 'GET')).toHaveLength(1);
    // And nothing took her back into the run: still on the passport a beat later, with
    // the chip offered again for a run the server still holds.
    expect(await screen.findByLabelText(rateSportChip('badminton'))).toBeTruthy();
    expect(screen).toHavePathname('/you/passport');
  });

  it('opens the next launch in the app, not in the run it left (ADR-0200 §5)', async () => {
    await onThePassport();
    await rateBadminton();
    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Continue later\./));
    await expectThePassport();

    await relaunch();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(screen.queryByText(PLAYED_QUESTION.text)).toBeNull();
  });

  it('returns to the passport on abandon, with the run ended and no card added', async () => {
    await onThePassport();
    await rateBadminton();

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Badminton\./));

    await expectThePassport();
    expect(transport.requestsTo('POST', `${stepPath(BADMINTON_RUN)}/abandonment`)).toHaveLength(1);
    // Three cards, as before — two estimates, said twice each — and the chip is back.
    expect(await screen.findByLabelText(rateSportChip('badminton'))).toBeTruthy();
    expect(screen.getAllByText(ratingStatusLabel('initial_estimate'))).toHaveLength(4);
    expect(screen.queryByText('Badminton')).toBeNull();
    expect(screen.queryByText('Your starting ratings')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The admission rule keeps its refusals
// ---------------------------------------------------------------------------

describe('a link during a pass begun at the passport', () => {
  it('sends a link naming another sport back to the passport, not into the middle of the pass', async () => {
    stubGate({ ratings: THREE_RATED, hasPlayerProfile: true });
    // A pass of one sport is running from the passport, and the link names another.
    useOnboardingPass.getState().begin(['badminton'], FROM_THE_PASSPORT);

    await launchSignedIn(`/question/${STRANGE_LINK_ID}?sport=squash`);

    // Out to the app's root, which ends the running pass — and a pass ends where it began.
    await expectThePassport();
    expect(transport.requestsTo('GET', stepPath(STRANGE_LINK_ID))).toEqual([]);
  });
});

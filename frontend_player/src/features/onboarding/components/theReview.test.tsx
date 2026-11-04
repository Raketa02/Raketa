/**
 * The review, the calculating screen and the submit that creates the rating — driven
 * through the real route tree and the network boundary.
 *
 * Only `fetch` is faked. The router, the http client, error mapping, the mappers, the
 * use-cases, the hooks, the cache and the screens all run for real, so a pass here means
 * the last stretch of onboarding works end to end minus the socket.
 *
 * **The transcript fixtures carry real copy**, unlike `transcriptOf`'s deliberate filler:
 * this is the first suite where what an answered question *says* is the thing on screen,
 * and a review of three questions all reading "Answered" would assert nothing about
 * whether the right answer is beside the right question.
 *
 * Every assertion is about what a player can see or what left the device.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  runInProgress,
  stubGate as stubGateWith,
  ratingGuideAlreadyShown,
} from '@/test-support/onboardingRouter';
import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useOnboardingPass } from '../store/onboardingPass.store';

const ASSESSMENT_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const STEP_PATH = `/api/v1/assessments/${ASSESSMENT_ID}`;
/** The run's own route — what *Carry on* opens; the gate resumes nothing (ADR-0200 §5, #730). */
const RUN_ROUTE = `/question/${ASSESSMENT_ID}?sport=padel`;
const ANSWERS_PATH = `${STEP_PATH}/answers`;
const COMPLETION_PATH = `${STEP_PATH}/completion`;
const ABANDONMENT_PATH = `${STEP_PATH}/abandonment`;

const PLAYED_QUESTION: Wire['QuestionResponse'] = {
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
};

const OVERHEAD_QUESTION: Wire['QuestionResponse'] = {
  id: 'q-overhead',
  category: 'Match execution',
  tier: 'discriminating',
  situation: 'A deep lob pushes you off the net',
  text: 'How often do you play a controlled overhead and recover your position?',
  qualifier: 'A normal match against players at your level',
  options: [
    { id: 'rarely', text: 'Rarely' },
    { id: 'usually', text: 'Usually' },
  ],
};

const LAYOFF_QUESTION: Wire['QuestionResponse'] = {
  id: 'q-layoff',
  category: 'Time away',
  tier: null,
  situation: 'Life gets in the way',
  text: 'Have you had a break from padel in the last year?',
  qualifier: 'A break of a month or more',
  options: [
    { id: 'none', text: 'No real break' },
    { id: 'six-months', text: 'About six months' },
  ],
};

const THREE_ANSWERS: Wire['AssessmentStepResponse']['transcript'] = [
  { question: PLAYED_QUESTION, option_id: 'regular' },
  { question: OVERHEAD_QUESTION, option_id: 'usually' },
  { question: LAYOFF_QUESTION, option_id: 'none' },
];

/**
 * The stop: in progress, three answers, and **neither a question nor a result**.
 *
 * Nothing has been rated and every answer is still the player's to change. This is the
 * whole shape the review exists to render, and the shape that used to reach a result screen
 * with no result on it.
 */
const STOPPED: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 3,
  transcript: THREE_ANSWERS,
  question: null,
  result: null,
};

/** The last question of the run, whose answer produces the stop. */
const LAST_QUESTION: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 2,
  transcript: THREE_ANSWERS.slice(0, 2),
  question: LAYOFF_QUESTION,
};

/** Standing back on question 2, which is what opening its entry on the review reaches. */
const RESULT: Wire['ResultResponse'] = {
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  confidence_ceiling: 30,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.65, upper: 3.85 },
  status: 'initial_estimate',
  questions_asked: 3,
  engine_version: 'racketskill-v3',
  calibration_priority: 'high',
};

/** What completion returns: the rating, inline, on a run that is now over. */
const RATED: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'completed',
  questions_asked: 3,
  transcript: THREE_ANSWERS,
  question: null,
  result: RESULT,
};

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

/**
 * A run force-quit at the stop, opened again — as the door's *Carry on* opens it.
 *
 * This is also the shortest way to the review, and deliberately the one used everywhere
 * below: the review has to be reachable from a cold launch with nothing on the device, or
 * "force-quitting at the review returns to the review" is a property only the happy path
 * has. The run's route is the question, and the question screen — finding a run with
 * nothing left to ask — sends the player on to the review.
 */
async function resumeIntoTheReview() {
  stubGate({ hasPlayerProfile: true, runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
  transport.on('GET', STEP_PATH, () => json(STOPPED));

  await launchSignedIn(RUN_ROUTE);

  await waitFor(() => expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`));
}

const submit = () => fireEvent.press(screen.getByLabelText('Get my Padel level'));

// ---------------------------------------------------------------------------
// Reaching the review
// ---------------------------------------------------------------------------

describe('reaching the end of the questionnaire', () => {
  it('shows the review rather than a result, when the engine stops', async () => {
    // The defect this closes: a stopped run has no result, and the screen that announces
    // one had nothing to announce.
    stubGate({ hasPlayerProfile: true, runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
    transport.on('GET', STEP_PATH, () => json(LAST_QUESTION));

    await launchSignedIn(RUN_ROUTE);
    expect(await screen.findByText('Time away')).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(STOPPED));
    fireEvent.press(screen.getByLabelText('No real break'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    await waitFor(() => expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`));
    expect(screen.queryByText(/Established/)).toBeNull();
  });

  it('lists every question and the answer given to it, in the order they were asked', async () => {
    await resumeIntoTheReview();

    expect(await screen.findByText('Have you played padel before?')).toBeTruthy();
    expect(screen.getByText('I play most weeks')).toBeTruthy();
    expect(
      screen.getByText('How often do you play a controlled overhead and recover your position?'),
    ).toBeTruthy();
    expect(screen.getByText('Usually')).toBeTruthy();
    expect(screen.getByText('Have you had a break from padel in the last year?')).toBeTruthy();
    expect(screen.getByText('No real break')).toBeTruthy();

    // In order, and numbered the way the questionnaire numbers them — an entry that opened
    // the question beside the one it describes would discard the wrong answers.
    expect(screen.getByText('Question 1')).toBeTruthy();
    expect(screen.getByText('Question 2')).toBeTruthy();
    expect(screen.getByText('Question 3')).toBeTruthy();
  });

  it('names the sport it belongs to', async () => {
    await resumeIntoTheReview();

    // A run inside a multi-sport pass has to be unambiguous, and the eyebrow is where this
    // flow already says which sport of how many.
    expect(await screen.findByText('Padel · Rating 1 of 1')).toBeTruthy();
  });

  it('shows no level, likely range or confidence anywhere', async () => {
    await resumeIntoTheReview();

    expect(await screen.findByText('Question 1')).toBeTruthy();
    // The no-running-estimate rule, applied where it matters most: every answer here is
    // still editable, so a number on this screen is an invitation to tune it.
    expect(screen.queryByText(/2[.,]71/)).toBeNull();
    expect(screen.queryByText(/%/)).toBeNull();
    expect(screen.queryByText(/Established/)).toBeNull();
    expect(screen.queryByText(/confiden/i)).toBeNull();
    expect(screen.queryByText(/so far/i)).toBeNull();
  });

  it('resumes to the review after a force quit, with nothing cached on the device', async () => {
    // Nothing local: a cold launch, an empty cache, and the whole run replayed from the
    // server. The review is where a player who force-quit at the review comes back to.
    await resumeIntoTheReview();

    expect(await screen.findByText('Have you played padel before?')).toBeTruthy();
    expect(transport.requestsTo('POST', COMPLETION_PATH)).toEqual([]);
  });

  it('reaches the review after one answer, on the beginner path', async () => {
    stubGate({ hasPlayerProfile: true, runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
    transport.on('GET', STEP_PATH, () =>
      json<Wire['AssessmentStepResponse']>({
        assessment_id: ASSESSMENT_ID,
        status: 'in_progress',
        questions_asked: 0,
        transcript: [],
        question: PLAYED_QUESTION,
      }),
    );

    await launchSignedIn(RUN_ROUTE);
    expect(await screen.findByText('Recent activity')).toBeTruthy();

    // "Never played" leaves the engine nothing more to ask. One question screen, one
    // review, one result is one rule — and a beginner's single answer is the
    // highest-leverage answer in the bank, so it gets the same last look as anyone's nine.
    transport.on('POST', ANSWERS_PATH, () =>
      json<Wire['AssessmentStepResponse']>({
        assessment_id: ASSESSMENT_ID,
        status: 'in_progress',
        questions_asked: 1,
        transcript: [{ question: PLAYED_QUESTION, option_id: 'never' }],
        question: null,
        result: null,
      }),
    );
    fireEvent.press(screen.getByLabelText('Never played'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    await waitFor(() => expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`));
    expect(await screen.findByText('Never played')).toBeTruthy();
  });

  it('keeps the confirm control identically labelled on the answer that ends the run', async () => {
    // The wart ADR-0017 accepted and ADR-0020 retires. The last question is no longer the
    // commitment, so the client never has to predict which question is the last one.
    stubGate({ hasPlayerProfile: true, runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
    transport.on('GET', STEP_PATH, () => json(LAST_QUESTION));

    await launchSignedIn(RUN_ROUTE);
    expect(await screen.findByText('Time away')).toBeTruthy();

    expect(screen.getByLabelText('Confirm answer')).toBeTruthy();
    expect(screen.queryByLabelText(/finish/i)).toBeNull();
    expect(screen.queryByLabelText(/last/i)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Changing an answer from the review
// ---------------------------------------------------------------------------

describe('changing an answer from the review', () => {
  it('returns to the questionnaire, standing on the question that was tapped', async () => {
    await resumeIntoTheReview();

    fireEvent.press(
      await screen.findByLabelText(
        'Question 2. How often do you play a controlled overhead and recover your position? Your answer: Usually',
      ),
    );

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
    // The question, with the answer they gave shown as they gave it — a review that landed
    // them anywhere else would be asking them to rebuild the run from a summary screen.
    expect(await screen.findByText('Question 2')).toBeTruthy();
    expect(screen.getByText('Match execution')).toBeTruthy();
    expect(screen.getByText('Your answer')).toBeTruthy();
  });

  it('draws that question from what it already had, and sends nothing to reach it', async () => {
    await resumeIntoTheReview();

    fireEvent.press(
      await screen.findByLabelText(
        'Question 1. Have you played padel before? Your answer: I play most weeks',
      ),
    );

    // No loading state and nothing awaited on the socket: the whole run arrived with the
    // step, so the question and the answer given to it are already in hand.
    expect(await screen.findByText('Question 1')).toBeTruthy();
    expect(screen.queryByLabelText('Loading your question')).toBeNull();
    expect(screen.getByText('Have you played padel before?')).toBeTruthy();
    expect(screen.getByText('Your answer')).toBeTruthy();

    // And nothing is recorded by looking. Only answering and changing are writes, and
    // opening an entry is neither. (The step itself is re-read in the background when a
    // screen mounts — TanStack's `refetchOnMount`, app-wide and not this flow's — which is
    // why the guarantee asserted here is *no write* and *no wait*, and the zero-request
    // guarantee for moving between answered questions lives in `questionLoop.test.tsx`,
    // where the moving happens.)
    expect(transport.requests.filter((request) => request.method !== 'GET')).toEqual([]);
  });

  it('shows the updated answers when the review is reached again', async () => {
    await resumeIntoTheReview();

    fireEvent.press(
      await screen.findByLabelText(
        'Question 3. Have you had a break from padel in the last year? Your answer: No real break',
      ),
    );
    expect(await screen.findByText('Question 3')).toBeTruthy();

    // Changing the last answer discards none, and the run stops again on the answer that
    // replaced it.
    transport.on('POST', ANSWERS_PATH, () =>
      json<Wire['AssessmentStepResponse']>({
        ...STOPPED,
        transcript: [
          ...THREE_ANSWERS.slice(0, 2),
          { question: LAYOFF_QUESTION, option_id: 'six-months' },
        ],
      }),
    );
    fireEvent.press(screen.getByLabelText('About six months'));
    fireEvent.press(await screen.findByLabelText('Change my answer'));

    await waitFor(() => expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`));
    // The review always describes the run as it stands, never as it was reached the first
    // time.
    expect(await screen.findByText('About six months')).toBeTruthy();
    expect(screen.queryByText('No real break')).toBeNull();
  });

  it('walks back to the review from the last answer rather than promising another question', async () => {
    await resumeIntoTheReview();

    fireEvent.press(
      await screen.findByLabelText(
        'Question 3. Have you had a break from padel in the last year? Your answer: No real break',
      ),
    );
    expect(await screen.findByText('Question 3')).toBeTruthy();

    // Forward from the last answer of a stopped run: there is no next question, and the
    // control says where it actually leads.
    fireEvent.press(screen.getByLabelText('Back to your answers'));

    await waitFor(() => expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`));
  });
});

// ---------------------------------------------------------------------------
// The submit that creates the rating
// ---------------------------------------------------------------------------

describe('submitting the reviewed answers', () => {
  it('holds the calculating screen, then shows the result', async () => {
    await resumeIntoTheReview();
    transport.on('POST', COMPLETION_PATH, () => json(RATED));

    expect(await screen.findByText('Question 1')).toBeTruthy();
    submit();

    expect(await screen.findByText('Working out your Padel level…')).toBeTruthy();

    // The rating already exists on this device — the request went and came back — and the
    // screen is held anyway. Without the hold this arrives and leaves inside a frame,
    // which reads as a glitch rather than as the moment the rating was made.
    await waitFor(() => expect(transport.requestsTo('POST', COMPLETION_PATH)).toHaveLength(1));
    await act(async () => {});
    expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`);
    expect(screen.getByText('Working out your Padel level…')).toBeTruthy();

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`), {
      timeout: 4000,
    });
    // The result screen and everything after it are unchanged.
    expect(await screen.findByText('2,71')).toBeTruthy();
    expect(screen.getByText('2,09 – 3,33')).toBeTruthy();
  });

  it('creates one rating and one navigation, however fast the control is tapped', async () => {
    await resumeIntoTheReview();

    let land = () => {};
    const held = new Promise<void>((resolve) => {
      land = resolve;
    });
    transport.on('POST', COMPLETION_PATH, async () => {
      await held;
      return json(RATED);
    });

    expect(await screen.findByText('Question 1')).toBeTruthy();
    // The same node, pressed again while the first press is still in the air — which is
    // what a player does on a slow connection, and this is the one control in onboarding
    // whose press cannot be taken back.
    const control = screen.getByLabelText('Get my Padel level');
    fireEvent.press(control);
    fireEvent.press(control);
    fireEvent.press(control);

    land();
    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`), {
      timeout: 4000,
    });
    // One rating, and one navigation — the second of which is the latch's, not the
    // server's: a second completion would have recorded nothing and returned the same
    // result, so only the client can keep this promise.
    expect(transport.requestsTo('POST', COMPLETION_PATH)).toHaveLength(1);
  });

  it('reads the rating out of the response rather than asking for it again', async () => {
    await resumeIntoTheReview();
    transport.on('POST', COMPLETION_PATH, () => json(RATED));

    expect(await screen.findByText('Question 1')).toBeTruthy();
    const readsBefore = transport.requestsTo('GET', STEP_PATH).length;
    submit();

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`), {
      timeout: 4000,
    });
    // Completion answers with the finished step, result inline, in one transaction. A
    // refetch here would be a second read of something already in hand.
    expect(transport.requestsTo('GET', STEP_PATH)).toHaveLength(readsBefore);
  });

  it('says so and offers the same control again, when the rating cannot be created', async () => {
    await resumeIntoTheReview();
    transport.on('POST', COMPLETION_PATH, networkFailure());

    expect(await screen.findByText('Question 1')).toBeTruthy();
    submit();

    // The wait ends where it started: the screen it was waiting for cannot arrive, so the
    // message takes its place beside the control that retries it.
    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`);
    expect(screen.getByText('Have you played padel before?')).toBeTruthy();

    transport.on('POST', COMPLETION_PATH, () => json(RATED));
    submit();

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`), {
      timeout: 4000,
    });
    expect(transport.requestsTo('POST', COMPLETION_PATH)).toHaveLength(2);
  });

  it('renders whatever the run turns out to be, when it had already moved on', async () => {
    await resumeIntoTheReview();

    // `assessment_not_stopped`: this device asked for a rating on a run the server says is
    // still asking — answered on a second handset. Nothing failed and nothing is owed an
    // explanation, so the recovery is a re-read and the question it turns up.
    transport.on('POST', COMPLETION_PATH, () =>
      errorResponse(409, 'assessment_not_stopped', 'the run is still asking'),
    );
    transport.on('GET', STEP_PATH, () => json(LAST_QUESTION));

    expect(await screen.findByText('Question 1')).toBeTruthy();
    submit();

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`), {
      timeout: 4000,
    });
    expect(await screen.findByText('Time away')).toBeTruthy();
    expect(screen.queryByText(/couldn't/i)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Leaving from the review
// ---------------------------------------------------------------------------

describe('leaving the flow from the review', () => {
  it('offers the same two doors it offers from a question', async () => {
    await resumeIntoTheReview();

    fireEvent.press(await screen.findByLabelText('Leave this rating'));

    expect(await screen.findByRole('header', { name: 'Leave this rating?' })).toBeTruthy();
    expect(screen.getByLabelText(/^Continue later\./)).toBeTruthy();
    expect(screen.getByLabelText(/^Stop rating Padel\./)).toBeTruthy();
    // Nothing is sent by opening it. Reaching the end of the questionnaire must not be the
    // one place in the flow with no way out.
    expect(transport.requestsTo('POST', ABANDONMENT_PATH)).toEqual([]);
    expect(transport.requestsTo('POST', COMPLETION_PATH)).toEqual([]);
  });

  it('abandons the run and moves the pass on, without creating a rating', async () => {
    await resumeIntoTheReview();
    transport.on('POST', ABANDONMENT_PATH, () => noContent());

    fireEvent.press(await screen.findByLabelText('Leave this rating'));
    fireEvent.press(await screen.findByLabelText(/^Stop rating Padel\./));

    // One sport and nothing rated, so the pass has no account to give and the player goes
    // to the app — the advance rule's answer, unchanged, and reached from the review
    // exactly as it is from a question.
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('POST', ABANDONMENT_PATH)).toHaveLength(1);
    // Nothing was rated: leaving from the review must not be a quiet way to finish.
    expect(transport.requestsTo('POST', COMPLETION_PATH)).toEqual([]);
  });

  it('keeps the run for later without sending anything', async () => {
    await resumeIntoTheReview();

    fireEvent.press(await screen.findByLabelText('Leave this rating'));
    fireEvent.press(await screen.findByLabelText(/^Continue later\./));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('POST', ABANDONMENT_PATH)).toEqual([]);
    expect(transport.requestsTo('POST', COMPLETION_PATH)).toEqual([]);
  });
});

/**
 * **The device's back button, on a screen that draws none.**
 *
 * The review's one way out is the close control's confirm — *continue later* or *stop rating
 * this sport*, both of which say what they cost. Every screen in onboarding `replace`s, so
 * until 2026-09-10 Android's back popped through the group's single history entry to the
 * screen the part began on: out of the run, past the confirm, and without either of the two
 * answers it exists to collect.
 * [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md): *"Back and
 * forward move freely inside each part and never cross between them."*
 *
 * So the press is claimed and nothing happens, which is what a screen with no back control
 * has already said. It does not open the confirm: answering the cheapest gesture on the
 * screen with a modal would make an interruption the easiest thing to trigger.
 */
describe("the device's own back button", () => {
  beforeEach(watchHardwareBack);
  afterEach(stopWatchingHardwareBack);

  it('is claimed and refused, leaving the run and its way out exactly where they were', async () => {
    await resumeIntoTheReview();

    expect(pressHardwareBack()).toBe(true);

    expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`);
    expect(screen.queryByRole('header', { name: 'Leave this rating?' })).toBeNull();
    expect(transport.requestsTo('POST', ABANDONMENT_PATH)).toEqual([]);
  });
});

/**
 * The adaptive question loop, driven through the real route tree and the network boundary.
 *
 * Only `fetch` is faked. The router, the http client, error mapping, the mappers, the
 * use-cases, the hooks, the cache and the screens all run for real — so a pass here means
 * the loop works end to end minus the socket.
 *
 * Every assertion is about what a player can see or what left the device. None reads the
 * cache directly, a store's internals or a hook's return shape.
 */

import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  SPORTS_SERVED,
  launchSignedIn,
  runInProgress,
  stubGate as stubGateWith,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useOnboardingPass } from '../store/onboardingPass.store';

const ASSESSMENT_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const ANSWERS_PATH = `/api/v1/assessments/${ASSESSMENT_ID}/answers`;
const STEP_PATH = `/api/v1/assessments/${ASSESSMENT_ID}`;

/** The opening question, which the engine asks of everyone. No tier: it routes, it rates. */
const OPENING: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  // Nothing answered yet. The outstanding question is never in this count.
  questions_asked: 0,
  question: {
    id: 'q-played',
    category: 'Recent activity',
    tier: null,
    situation: 'Before anything else',
    text: 'Have you played padel before?',
    qualifier: 'Any level counts',
    options: [
      { id: 'never', text: 'Never played' },
      { id: 'regular', text: 'I play regularly' },
    ],
  },
};

/** A demonstration, asked at the tier the estimate implied. */
const EXECUTION: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 1,
  question: {
    id: 'q-overhead',
    category: 'Match execution',
    tier: 'discriminating',
    situation: 'A deep lob pushes you off the net',
    text: 'How often do you play a controlled overhead and recover your position?',
    qualifier: 'A normal match against players at your level',
    options: [
      { id: 'rarely', text: 'Rarely' },
      { id: 'sometimes', text: 'About half the time' },
      { id: 'usually', text: 'Usually' },
    ],
  },
};

/** Another ordinary question from the bank, deeper into a run. */
const LAYOFF: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 5,
  question: {
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
  },
};

const RESULT: Wire['ResultResponse'] = {
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.65, upper: 3.85 },
  status: 'initial_estimate',
  questions_asked: 2,
  engine_version: 'racketskill-v3',
  calibration_priority: 'high',
};

/** Nothing outstanding, and a rating exists. The one exit from the loop. */
const FINISHED: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'completed',
  // The same number the result carries — the count means one thing at both moments in a
  // run's life, so it does not jump as the run finishes.
  questions_asked: 2,
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
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
});

/**
 * Land on the opening question the way a returning player does — the gate finds an
 * unfinished padel run and resumes it. Resume is the shorter road to the loop and it
 * exercises the same one screen; the walk in from the picker has its own test below.
 */
async function resumeAtTheOpeningQuestion() {
  stubGate({ runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
  transport.on('GET', STEP_PATH, () => json(OPENING));

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
  expect(await screen.findByText('Have you played padel before?')).toBeTruthy();
}

// ---------------------------------------------------------------------------
// One question, in the order it is meant to be read
// ---------------------------------------------------------------------------

describe('the question screen', () => {
  it('leads with the category and never makes the question the title', async () => {
    await resumeAtTheOpeningQuestion();

    // The category is the heading — a title is read last on a screen the eye scans
    // top-down, so the question must not be it.
    expect(screen.getByRole('header', { name: 'Recent activity' })).toBeTruthy();
    expect(screen.queryByRole('header', { name: 'Have you played padel before?' })).toBeNull();

    // Situation, question and qualifier all present, in one card.
    expect(screen.getByText('Before anything else')).toBeTruthy();
    expect(screen.getByText('Any level counts')).toBeTruthy();
  });

  it('shows the difficulty where the engine supplies one, and nothing where it does not', async () => {
    await resumeAtTheOpeningQuestion();

    // The opening question has no tier: it is asked of everyone, so there is nothing to
    // report and an invented "basic" would be the client authoring engine vocabulary.
    expect(screen.queryByLabelText(/^Difficulty:/)).toBeNull();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByLabelText('Difficulty: discriminating')).toBeTruthy();
  });

  it('has no back control, and answering never opens a route to go back to', async () => {
    await resumeAtTheOpeningQuestion();

    // An answer's numeric meaning depends on the tier it was asked at, and that tier came
    // from the estimate as it stood — so revisiting one would silently change what every
    // later answer meant (ADR-0017).
    expect(screen.queryByLabelText('Back')).toBeNull();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Match execution')).toBeTruthy();
    // The next question replaces this one's data in place rather than pushing a route, so
    // the device back gesture has no answered question to return to.
    expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`);
    expect(screen.queryByLabelText('Back')).toBeNull();
  });

  it('never shows a running level', async () => {
    await resumeAtTheOpeningQuestion();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));
    expect(await screen.findByText('Match execution')).toBeTruthy();

    // The design system draws a "3,17 so far" chip in the meta row. It is deliberately
    // absent: a player watching a number move would answer to move it.
    expect(screen.queryByText(/so far/i)).toBeNull();
    expect(screen.queryByText(/2[.,]71/)).toBeNull();
  });

  it('counts the questions asked without inventing a length for the flow', async () => {
    await resumeAtTheOpeningQuestion();

    expect(screen.getByText('Question 1')).toBeTruthy();
    // The bar measures sports, which is the one denominator the player chose. The counter
    // carries movement inside a sport and is never a fraction.
    expect(screen.getByLabelText('Rating 1 of 1')).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Question 2')).toBeTruthy();
    expect(screen.getByLabelText('Rating 1 of 1')).toBeTruthy();
  });

  it('shows a resumed run the position it is really at, not question 1', async () => {
    // Four answers behind them from yesterday, and the fifth question outstanding. The
    // count is the server's replay of the transcript — the only thing that ever survived
    // the player closing the app, so it is the only thing that can answer this.
    const resumed: Wire['AssessmentStepResponse'] = { ...EXECUTION, questions_asked: 4 };
    stubGate({ runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
    transport.on('GET', STEP_PATH, () => json(resumed));

    await launchSignedIn();

    expect(await screen.findByText('Question 5')).toBeTruthy();
    expect(screen.queryByText('Question 1')).toBeNull();

    // And it carries on from there. A screen counting the questions it had itself shown
    // would say "Question 2" here — which is the bug this reads the step to avoid.
    transport.on('POST', ANSWERS_PATH, () => json(LAYOFF));
    fireEvent.press(screen.getByLabelText('Usually'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Question 6')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Selecting, and the confirm that earns the irreversibility
// ---------------------------------------------------------------------------

describe('choosing an answer', () => {
  it('selects on tap and submits only on confirm', async () => {
    await resumeAtTheOpeningQuestion();

    fireEvent.press(screen.getByLabelText('I play regularly'));

    // A mis-tap costs nothing: selecting is not committing.
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toEqual([]);
    expect(screen.getByText('Selected')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'I play regularly', selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Never played', selected: false })).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    await waitFor(() => expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1));
    const [submitted] = transport.requestsTo('POST', ANSWERS_PATH);
    expect(submitted?.body).toEqual({ question_id: 'q-played', option_id: 'regular' });
  });

  it('offers the confirm from the first question, disabled until something is chosen', async () => {
    await resumeAtTheOpeningQuestion();

    // Present from the first question, so the control never appears from nowhere.
    expect(screen.getByRole('button', { name: 'Confirm answer', disabled: true })).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Never played'));

    expect(screen.getByRole('button', { name: 'Confirm answer', disabled: false })).toBeTruthy();
  });

  it('keeps the same confirm label on every question, including the last', async () => {
    await resumeAtTheOpeningQuestion();
    expect(screen.getByLabelText('Confirm answer')).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));
    expect(await screen.findByText('Match execution')).toBeTruthy();

    // The engine decides it has enough *after* the answer arrives, so the client cannot
    // know this is the last question — and a label that changed would say it did.
    expect(screen.getByLabelText('Confirm answer')).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(FINISHED));
    fireEvent.press(screen.getByLabelText('Usually'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`));
  });

  it('clears the selection when the next question arrives', async () => {
    await resumeAtTheOpeningQuestion();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Match execution')).toBeTruthy();
    expect(screen.queryByText('Selected')).toBeNull();
    expect(screen.getByRole('button', { name: 'Confirm answer', disabled: true })).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// One round trip, and nothing predicted
// ---------------------------------------------------------------------------

describe('what leaves the device', () => {
  it('answers in a single round trip and renders the response', async () => {
    await resumeAtTheOpeningQuestion();
    const readsBefore = transport.requestsTo('GET', STEP_PATH).length;

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Match execution')).toBeTruthy();
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1);
    // The next question *is* the response, so it is written into the cache. Invalidating
    // and refetching would be a second round trip for an answer already in hand.
    expect(transport.requestsTo('GET', STEP_PATH)).toHaveLength(readsBefore);
  });

  it('applies no optimistic update — the question does not move until the server answers', async () => {
    await resumeAtTheOpeningQuestion();

    let answer = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('POST', ANSWERS_PATH, async () => {
      await held;
      return json(EXECUTION);
    });

    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    await waitFor(() => expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1));

    // Selecting the next question *is* the rating calculation, so there is nothing the
    // client could optimistically show. It waits, and says it is waiting.
    expect(screen.getByText('Have you played padel before?')).toBeTruthy();
    expect(screen.queryByText('Match execution')).toBeNull();
    expect(screen.getByLabelText('Submitting…')).toBeTruthy();

    await act(async () => {
      answer();
    });
    expect(await screen.findByText('Match execution')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Failure, and the two conflicts that are not failures
// ---------------------------------------------------------------------------

describe('when an answer does not go through', () => {
  it('offers a retry in place and does not lose the selection', async () => {
    await resumeAtTheOpeningQuestion();

    transport.on('POST', ANSWERS_PATH, networkFailure());
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(
      await screen.findByText("We couldn't reach Rakieta. Check your connection and try again."),
    ).toBeTruthy();

    // Still on the same question, with the answer they gave still chosen — a player on a
    // bad connection must not be made to remember what they had picked.
    expect(screen.getByText('Have you played padel before?')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'I play regularly', selected: true })).toBeTruthy();

    // The retry is the confirm control itself, still enabled and still holding the choice.
    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Match execution')).toBeTruthy();
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(2);
  });

  it('recovers silently from a duplicate submission', async () => {
    await resumeAtTheOpeningQuestion();

    // A double-tapped confirm, or the same run answered on a second device: the first
    // answer landed and the engine has moved on, so this one names a question that is no
    // longer outstanding.
    transport.on('POST', ANSWERS_PATH, () => errorResponse(409, 'question_not_outstanding'));
    transport.on('GET', STEP_PATH, () => json(EXECUTION));

    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    // Left on the correct question, with nothing to dismiss. An answer *was* recorded, so
    // reporting a failure would be reporting something that did not happen.
    expect(await screen.findByText('Match execution')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByText('Question 2')).toBeTruthy();

    // Recovered by re-reading, never by re-sending: the same answer would fail identically.
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1);
  });

  it('recovers silently when the run finished somewhere else', async () => {
    await resumeAtTheOpeningQuestion();

    transport.on('POST', ANSWERS_PATH, () => errorResponse(409, 'assessment_already_finished'));
    transport.on('GET', STEP_PATH, () => json(FINISHED));

    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    // The other 409 demands the opposite recovery — jump to the result rather than
    // re-render a question that no longer exists. Both are reached by re-reading the step.
    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`));
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('still reports a conflict it has no recovery for', async () => {
    await resumeAtTheOpeningQuestion();

    // Same status, same endpoint, different code. Recovering from this one would hide a
    // genuine failure behind a silent refetch.
    transport.on('POST', ANSWERS_PATH, () => errorResponse(409, 'invalid_answer_option'));

    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText("That can't be done right now.")).toBeTruthy();
    expect(screen.getByText('Have you played padel before?')).toBeTruthy();
    // Announced when it appears, and the positive half of the two silent-recovery tests
    // above: without this, their `queryByRole("alert")` assertions would prove nothing.
    expect(screen.getByRole('alert')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Both ends of the loop
// ---------------------------------------------------------------------------

describe('finishing', () => {
  it('finishes a beginner after a single question', async () => {
    await resumeAtTheOpeningQuestion();

    // "Never played" completes the assessment immediately — which is the whole reason the
    // gate is a question from the engine's bank rather than a screen of its own.
    transport.on('POST', ANSWERS_PATH, () => json(FINISHED));
    fireEvent.press(screen.getByLabelText('Never played'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`));
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1);
  });

  it('walks the picker, both questions and out to the result', async () => {
    stubGate();
    transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
    transport.on('POST', '/api/v1/assessments', () => json(OPENING, 201));

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    fireEvent.press(screen.getByLabelText('Get started'));

    expect(await screen.findByLabelText('Padel')).toBeTruthy();
    fireEvent.press(screen.getByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Rate 1 sport'));

    expect(await screen.findByText('Have you played padel before?')).toBeTruthy();
    expect(screen.getByText('Question 1')).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Match execution')).toBeTruthy();
    expect(screen.getByText('Question 2')).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(FINISHED));
    fireEvent.press(screen.getByLabelText('About half the time'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`));
    // The whole walk cost one read of the step — the start — and one request per answer.
    expect(transport.requestsTo('GET', STEP_PATH)).toEqual([]);
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(2);
  });

  it('leaves a resumed-but-finished run on the result rather than on a dead question', async () => {
    stubGate({ runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
    // The gate saw a run in progress; by the time the screen read it, it was over.
    transport.on('GET', STEP_PATH, () => json(FINISHED));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`));
  });
});

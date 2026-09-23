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
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  transcriptOf,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useOnboardingPass } from '../store/onboardingPass.store';

const ASSESSMENT_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const ANSWERS_PATH = `/api/v1/assessments/${ASSESSMENT_ID}/answers`;
const STEP_PATH = `/api/v1/assessments/${ASSESSMENT_ID}`;

/** The opening question, which the engine asks of everyone. No tier: it routes, it rates. */
const OPENING_QUESTION: Wire['QuestionResponse'] = {
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
};

/** A demonstration, asked at the tier the estimate implied. */
const EXECUTION_QUESTION: Wire['QuestionResponse'] = {
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
};

/** Another ordinary question from the bank, deeper into a run. */
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

const OPENING: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  // Nothing answered yet. The outstanding question is never in this count.
  questions_asked: 0,
  transcript: [],
  question: OPENING_QUESTION,
};

/**
 * The step the opening answer produces — and it carries that answer.
 *
 * **The transcript is the question as it was asked plus the option chosen**, which is what
 * lets the screen draw an answered question it may never have shown: a run resumed on a
 * second handset has nothing else to draw it from. So a fixture that answers `q-played`
 * and then serves a transcript without it would be describing a response the backend
 * cannot produce.
 */
const EXECUTION: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 1,
  transcript: [{ question: OPENING_QUESTION, option_id: 'regular' }],
  question: EXECUTION_QUESTION,
};

const LAYOFF: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 5,
  transcript: [...transcriptOf(4), { question: EXECUTION_QUESTION, option_id: 'usually' }],
  question: LAYOFF_QUESTION,
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
  transcript: transcriptOf(2),
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

  /*
   * DELETED HERE, deliberately: `has no back control, and answering never opens a route to
   * go back to`.
   *
   * It asserted the opposite of what this app now does. ADR-0020 supersedes ADR-0017's
   * irreversibility rule: a player may walk back over the questions they have answered,
   * and the header's back control is how. What the deleted test protected — that answering
   * pushes no route, so the device back gesture cannot walk out of the run — is protected
   * below by `stays on one route`, which is the half of it that survived.
   */

  it('offers no way back from the first question, because there is nothing behind it', async () => {
    await resumeAtTheOpeningQuestion();

    expect(screen.queryByLabelText('Previous question')).toBeNull();
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
    // Which sport of how many lives in the eyebrow and only there. The indicator under
    // the header measures this run's questions now, so nothing on the screen counts
    // sports twice — and nothing claims a total for a run whose length the engine
    // decides one answer at a time.
    expect(screen.getByText('Padel · Rating 1 of 1')).toBeTruthy();
    expect(screen.queryByRole('progressbar')).toBeNull();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Question 2')).toBeTruthy();
    expect(screen.getByText('Padel · Rating 1 of 1')).toBeTruthy();
  });

  it('shows a resumed run the position it is really at, not question 1', async () => {
    // Four answers behind them from yesterday, and the fifth question outstanding. The
    // count is the server's replay of the transcript — the only thing that ever survived
    // the player closing the app, so it is the only thing that can answer this.
    const resumed: Wire['AssessmentStepResponse'] = {
      ...EXECUTION,
      questions_asked: 4,
      // Served with the count, and by the same replay: what survived the player
      // closing the app is the stream, so both come from it or neither does.
      transcript: transcriptOf(4),
    };
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
// Walking back over the questions already answered (ADR-0020)
// ---------------------------------------------------------------------------

/**
 * Four answers behind them and a fifth question outstanding — the run a player would
 * actually want to look back through. The four answered questions are the served
 * transcript's, which is the only place they have ever existed as far as this device is
 * concerned: nothing was cached when they were answered, because they were answered
 * yesterday, or on another handset.
 */
async function resumeFiveQuestionsIn() {
  const resumed: Wire['AssessmentStepResponse'] = {
    ...EXECUTION,
    questions_asked: 4,
    transcript: transcriptOf(4),
  };
  stubGate({ runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
  transport.on('GET', STEP_PATH, () => json(resumed));

  await launchSignedIn();

  expect(await screen.findByText('Question 5')).toBeTruthy();
}

const goBack = () => fireEvent.press(screen.getByLabelText('Previous question'));
const goForward = () => fireEvent.press(screen.getByLabelText('Next question'));

describe('moving over answered questions', () => {
  it('shows an answered question with the answer that was given', async () => {
    await resumeFiveQuestionsIn();

    goBack();

    expect(await screen.findByText('Question 4')).toBeTruthy();
    expect(screen.getByText('The question answered at position 4')).toBeTruthy();
    // The choice they made, as a word rather than only a border — and the alternative
    // beside it, because re-reading what you agreed to means re-reading what you did not.
    expect(screen.getByText('Your answer')).toBeTruthy();
    expect(screen.getByLabelText('What the player chose. Your answer.')).toBeTruthy();
    expect(screen.getByLabelText('What they did not')).toBeTruthy();
  });

  it('costs nothing to look, in either direction', async () => {
    await resumeFiveQuestionsIn();
    const readsBefore = transport.requestsTo('GET', STEP_PATH).length;

    goBack();
    expect(await screen.findByText('Question 4')).toBeTruthy();
    goBack();
    goBack();
    expect(await screen.findByText('Question 2')).toBeTruthy();
    goForward();
    goForward();
    goForward();

    // Back where they started, on the question they are actually being asked.
    expect(
      await screen.findByText(
        'How often do you play a controlled overhead and recover your position?',
      ),
    ).toBeTruthy();

    // **Zero.** The whole run arrived with the step, so looking is free — which is what
    // has to be true before "you can change your mind" can mean anything.
    expect(transport.requestsTo('GET', STEP_PATH)).toHaveLength(readsBefore);
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toEqual([]);
  });

  it('reaches the first question, and offers nothing behind it', async () => {
    await resumeFiveQuestionsIn();

    goBack();
    goBack();
    goBack();
    goBack();

    expect(await screen.findByText('Question 1')).toBeTruthy();
    expect(screen.getByText('The question answered at position 1')).toBeTruthy();
    // No answer is beyond reach, and there is nothing beyond the first one.
    expect(screen.queryByLabelText('Previous question')).toBeNull();
  });

  it('keeps the question being asked distinguishable from the ones already answered', async () => {
    await resumeFiveQuestionsIn();

    // The live question is the one that can be answered, and the only one with a confirm.
    expect(screen.getByLabelText('Confirm answer')).toBeTruthy();
    expect(screen.queryByText('Your answer')).toBeNull();

    goBack();

    expect(await screen.findByText('Question 4')).toBeTruthy();
    expect(screen.queryByLabelText('Confirm answer')).toBeNull();
    expect(screen.getByLabelText('Next question')).toBeTruthy();
  });

  it('records nothing, and leaves the answer waiting where it was', async () => {
    await resumeFiveQuestionsIn();

    fireEvent.press(screen.getByLabelText('Usually'));
    goBack();
    expect(await screen.findByText('Question 4')).toBeTruthy();
    goForward();
    expect(await screen.findByText('Question 5')).toBeTruthy();

    // Looking changed nothing: not the answers behind them, and not the one they were
    // part-way through giving.
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toEqual([]);
    expect(screen.getByRole('button', { name: 'Usually', selected: true })).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(LAYOFF));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    expect(await screen.findByText('Question 6')).toBeTruthy();
    const [submitted] = transport.requestsTo('POST', ANSWERS_PATH);
    expect(submitted?.body).toEqual({ question_id: 'q-overhead', option_id: 'usually' });
  });

  /*
   * DELETED HERE, deliberately: `cannot be changed from here — this slice moves, it does
   * not revise`.
   *
   * It asserted that an answered question's alternatives are not operable, which was true
   * of the slice that could only move over them. They are operable now, and pressing one
   * opens the change sheet — see `changing an answer` below, which asserts the opposite of
   * every line of it. The part worth keeping is that a press still changes nothing on its
   * own; that is `asks before it changes anything, and names what the change costs`.
   */

  it('stays on one route, so the device back gesture never walks out of the run', async () => {
    await resumeFiveQuestionsIn();

    goBack();
    expect(await screen.findByText('Question 4')).toBeTruthy();

    // Moving inside the questionnaire is state, not navigation — the half of the deleted
    // no-back-control test that survived ADR-0020. Pushing a route per question would put
    // the run's history behind the system back gesture, where leaving it and moving
    // through it become the same gesture.
    expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`);
  });
});

// ---------------------------------------------------------------------------
// The navigator: it grows, and it claims no total
// ---------------------------------------------------------------------------

describe('the question navigator', () => {
  it('says where the player is and how much is behind them, and never a total', async () => {
    await resumeAtTheOpeningQuestion();

    // A row of rectangles is not readable at any font size, so this is the whole of it in
    // words. There is no "of 9" anywhere in it: the engine decides it has heard enough
    // only after an answer arrives, so no total exists to state.
    expect(screen.getByLabelText('Question 1. No answers given yet.')).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(EXECUTION));
    fireEvent.press(screen.getByLabelText('I play regularly'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    // It advances with the answer — on the screen a player spends the longest on, which
    // is the one the sports bar never moved on.
    expect(await screen.findByLabelText('Question 2. 1 answer given so far.')).toBeTruthy();
  });

  it('announces standing on an answer as a different position from being asked one', async () => {
    await resumeFiveQuestionsIn();

    expect(screen.getByLabelText('Question 5. 4 answers given so far.')).toBeTruthy();

    goBack();

    // The sighted difference is a segment's fill; this is that difference in words.
    expect(
      await screen.findByLabelText('Question 4, already answered. 4 answers given so far.'),
    ).toBeTruthy();
  });

  it('is not a control — the segments announce nothing and move nobody', async () => {
    await resumeFiveQuestionsIn();

    // Ten segments across the content width is a 26pt target against the 44pt minimum,
    // and selecting the wrong one would be the most destructive tap in the flow. So it
    // indicates: one element, one label, and never five buttons for a screen reader to
    // enumerate.
    expect(screen.queryAllByRole('progressbar')).toEqual([]);
    expect(screen.queryByRole('button', { name: /Question 2/ })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Changing an answer, and losing the answers that depended on it (ADR-0020)
// ---------------------------------------------------------------------------

/**
 * What a change at position 2 of a four-answer run comes back as: two answers, the second
 * of them now the other option, and the question the engine chooses from that transcript.
 *
 * The two answers that were behind it are simply not in it — which is the whole of
 * "truncates", as a client sees it.
 */
const REVISED_AT_TWO: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 2,
  transcript: transcriptOf(2).map((entry, index) =>
    index === 1 ? { ...entry, option_id: 'other' } : entry,
  ),
  question: LAYOFF_QUESTION,
};

/**
 * A change to the opening answer that ends the questionnaire — "never played" is the one
 * answer that stops a run on its own.
 *
 * In progress, one answer, and **neither a question nor a result**: the run has stopped
 * and nothing has been rated (#59). Nothing here is special to a revision — a last
 * ordinary answer produces the same shape.
 */
const STOPPED_AFTER_ONE: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 1,
  transcript: transcriptOf(1).map((entry) => ({ ...entry, option_id: 'other' })),
  question: null,
  result: null,
};

const askToChange = () => fireEvent.press(screen.getByLabelText('What they did not'));
const confirmChange = () => fireEvent.press(screen.getByLabelText('Change my answer'));

/** Back to the second of four answers — the one with two answers standing on it. */
async function walkBackToQuestionTwo() {
  await resumeFiveQuestionsIn();
  goBack();
  goBack();
  goBack();
  expect(await screen.findByText('Question 2')).toBeTruthy();
}

describe('changing an answer', () => {
  it('asks before it changes anything, and names what the change costs', async () => {
    await walkBackToQuestionTwo();

    askToChange();

    // The consequence is put in front of the player rather than performed on them, and
    // the number is the decision: two answers here, none at all at the end of a run.
    expect(await screen.findByRole('header', { name: 'Change this answer?' })).toBeTruthy();
    expect(screen.getByText(/Changing it discards 2 later answers/)).toBeTruthy();
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toEqual([]);

    fireEvent.press(screen.getByLabelText('Keep my answer'));

    await waitFor(() =>
      expect(screen.queryByRole('header', { name: 'Change this answer?' })).toBeNull(),
    );
    // Nothing was sent and nothing moved: the answer they had is still the answer they
    // have, on the question they were looking at.
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toEqual([]);
    expect(screen.getByText('Question 2')).toBeTruthy();
    expect(screen.getByLabelText('What the player chose. Your answer.')).toBeTruthy();
  });

  it('changes an answer deep in a run, and continues from what the engine now asks', async () => {
    await walkBackToQuestionTwo();
    transport.on('POST', ANSWERS_PATH, () => json(REVISED_AT_TWO));

    askToChange();
    expect(await screen.findByRole('header', { name: 'Change this answer?' })).toBeTruthy();
    confirmChange();

    // Not the most recent answer — any answered question, which is what stops this being
    // a one-step undo wearing another name.
    expect(
      await screen.findByText('Have you had a break from padel in the last year?'),
    ).toBeTruthy();
    const [sent] = transport.requestsTo('POST', ANSWERS_PATH);
    expect(sent?.body).toEqual({ question_id: 'answered-2', option_id: 'other' });

    // Standing on the question the engine chose from the transcript this change produced,
    // rather than on the answer they just changed. A screen that kept its position would
    // leave them re-reading what they had already decided.
    expect(screen.getByText('Question 3')).toBeTruthy();
    expect(screen.getByLabelText('Confirm answer')).toBeTruthy();
  });

  it('shrinks the navigator to match the answers that are left', async () => {
    await walkBackToQuestionTwo();
    expect(
      screen.getByLabelText('Question 2, already answered. 4 answers given so far.'),
    ).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(REVISED_AT_TWO));
    askToChange();
    confirmChange();

    // The run describes less progress than it did a moment ago, and the indicator says so.
    // Anything counting what it had itself shown would still be claiming four.
    expect(await screen.findByLabelText('Question 3. 2 answers given so far.')).toBeTruthy();
  });

  it('walks back to the change and finds the new answer recorded there', async () => {
    await walkBackToQuestionTwo();
    transport.on('POST', ANSWERS_PATH, () => json(REVISED_AT_TWO));
    askToChange();
    confirmChange();
    expect(await screen.findByText('Question 3')).toBeTruthy();

    goBack();

    // The run is coherent afterwards: what they said is what is recorded, and the option
    // they turned down is the one they had before.
    expect(await screen.findByText('Question 2')).toBeTruthy();
    expect(screen.getByLabelText('What they did not. Your answer.')).toBeTruthy();
    expect(screen.getByLabelText('What the player chose')).toBeTruthy();
  });

  it('does nothing at all when the answer already recorded is chosen again', async () => {
    await walkBackToQuestionTwo();

    fireEvent.press(screen.getByLabelText('What the player chose. Your answer.'));

    // Changing your mind and changing it back is not punished — and a confirmation naming
    // a cost nobody pays would be the punishment.
    expect(screen.queryByRole('header', { name: 'Change this answer?' })).toBeNull();
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toEqual([]);
    expect(screen.getByText('Question 2')).toBeTruthy();
  });

  it('shows no level, range or confidence while any of this happens', async () => {
    await walkBackToQuestionTwo();
    transport.on('POST', ANSWERS_PATH, () => json(REVISED_AT_TWO));

    askToChange();
    expect(await screen.findByRole('header', { name: 'Change this answer?' })).toBeTruthy();
    // Not on the sheet, which is the one screen in the flow that could argue for it:
    // a player told what a change would do to their number would change until it moved.
    expect(screen.queryByText(/so far/i)).toBeNull();
    expect(screen.queryByText(/2[.,]71/)).toBeNull();

    confirmChange();

    expect(await screen.findByText('Question 3')).toBeTruthy();
    expect(screen.queryByText(/2[.,]71/)).toBeNull();
    expect(screen.queryByText(/%/)).toBeNull();
  });

  it('routes onward when a change ends the questionnaire', async () => {
    await resumeFiveQuestionsIn();
    goBack();
    goBack();
    goBack();
    goBack();
    expect(await screen.findByText('Question 1')).toBeTruthy();

    // The beginner's answer, given late: "never played" leaves the engine nothing more to
    // ask, so the response carries no question — and the client must not sit waiting for
    // one. Onward is the **review**, by the same path a last ordinary answer takes: the
    // run has stopped and nothing has been rated, so there is no result to route to and
    // every answer is still the player's to change (#62).
    transport.on('POST', ANSWERS_PATH, () => json(STOPPED_AFTER_ONE));
    askToChange();
    confirmChange();

    await waitFor(() => expect(screen).toHavePathname(`/review/${ASSESSMENT_ID}`));
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1);
  });
});

describe('when a change does not go through', () => {
  it('offers a retry in place and keeps the option that was chosen', async () => {
    await walkBackToQuestionTwo();
    transport.on('POST', ANSWERS_PATH, networkFailure());

    askToChange();
    confirmChange();

    // The message is beside the control that retries it, and the sheet stays open with the
    // change still described — a dropped request must not cost the player the answers a
    // successful change would have kept.
    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Change this answer?' })).toBeTruthy();
    expect(screen.getByText(/Changing it discards 2 later answers/)).toBeTruthy();

    transport.on('POST', ANSWERS_PATH, () => json(REVISED_AT_TWO));
    confirmChange();

    expect(await screen.findByText('Question 3')).toBeTruthy();
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(2);
    const [, retried] = transport.requestsTo('POST', ANSWERS_PATH);
    expect(retried?.body).toEqual({ question_id: 'answered-2', option_id: 'other' });
  });

  it('makes one change out of a double-tapped confirm', async () => {
    await walkBackToQuestionTwo();

    let land = () => {};
    const held = new Promise<void>((resolve) => {
      land = resolve;
    });
    transport.on('POST', ANSWERS_PATH, async () => {
      await held;
      return json(REVISED_AT_TWO);
    });

    askToChange();
    // The same node, pressed again while the first press is still in the air — which is
    // exactly what a player does on a slow connection, and this is the control that
    // discards their later answers.
    const control = screen.getByLabelText('Change my answer');
    fireEvent.press(control);
    fireEvent.press(control);
    fireEvent.press(control);

    await waitFor(() => expect(screen.getByLabelText('Changing…')).toBeTruthy());
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1);

    // And it cannot be dismissed out from under the request it started: the change is
    // already running, and a sheet that closed here would say otherwise.
    fireEvent.press(screen.getByLabelText('Close and keep your answer'));
    expect(screen.getByRole('header', { name: 'Change this answer?' })).toBeTruthy();

    await act(async () => {
      land();
    });

    // And even had a duplicate reached the server, it would have recorded nothing: the
    // option is already the one the transcript holds. The guarantee here is the client's
    // half — one press's worth of consequence per change.
    expect(await screen.findByText('Question 3')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByRole('header', { name: 'Change this answer?' })).toBeNull();
  });

  it('recovers silently when the rating already exists', async () => {
    await walkBackToQuestionTwo();

    // Revising is refused once a rating has been proved, with its own code — and the
    // recovery is the opposite of a retry: there is no question to go back to, only a
    // rating to show. Reached by re-reading the step, like the other two.
    transport.on('POST', ANSWERS_PATH, () => errorResponse(409, 'answer_not_revisable'));
    transport.on('GET', STEP_PATH, () => json(FINISHED));

    askToChange();
    confirmChange();

    await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`));
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Selecting, and the confirm that submits one answer
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

  it('sends one answer however many times the confirm is pressed', async () => {
    await resumeAtTheOpeningQuestion();

    let land = () => {};
    const held = new Promise<void>((resolve) => {
      land = resolve;
    });
    transport.on('POST', ANSWERS_PATH, async () => {
      await held;
      return json(EXECUTION);
    });

    fireEvent.press(screen.getByLabelText('I play regularly'));
    // The same node, pressed again while the first press is still in the air. The busy
    // control cannot answer for this: it belongs to a render that does not exist yet when
    // the second tap lands.
    const confirm = screen.getByLabelText('Confirm answer');
    fireEvent.press(confirm);
    fireEvent.press(confirm);
    fireEvent.press(confirm);

    await waitFor(() => expect(screen.getByLabelText('Submitting…')).toBeTruthy());
    expect(transport.requestsTo('POST', ANSWERS_PATH)).toHaveLength(1);

    await act(async () => {
      land();
    });
    expect(await screen.findByText('Match execution')).toBeTruthy();
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
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
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

/**
 * **The device's back button is *Previous question*, and never the way out of a run.**
 *
 * The header says so already — *"Back through the run, never out of it — the way out is the
 * close control on the other side of the header, and the two must not be confused for each
 * other"* — and until 2026-09-10 the device's own gesture was the confusion. Every screen in
 * onboarding `replace`s, so the group holds one history entry and Android's back popped
 * straight through it to the screen the part began on, past both controls.
 * [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md): *"Back and
 * forward move freely inside each part and never cross between them."*
 *
 * `pressHardwareBack` replays the press through what the app subscribed and answers whether
 * anything claimed it; the pop that follows an unclaimed press is the activity's, and no test
 * can perform it. So *claimed* is what these assert.
 */
describe("the device's own back button", () => {
  beforeEach(watchHardwareBack);
  afterEach(stopWatchingHardwareBack);

  it('moves back through the run, exactly as the control in the header does', async () => {
    await resumeFiveQuestionsIn();

    expect(pressHardwareBack()).toBe(true);

    expect(await screen.findByText('Question 4')).toBeTruthy();
  });

  it('is claimed and refused on the first question, which draws no back at all', async () => {
    await resumeAtTheOpeningQuestion();

    expect(pressHardwareBack()).toBe(true);

    // Still on the run. The floor `questionNavigation` clamps at position 1 is what the
    // missing control says, and the press says the same thing rather than something louder.
    expect(await screen.findByText('Question 1')).toBeTruthy();
    expect(screen.queryByLabelText('Previous question')).toBeNull();
  });
});

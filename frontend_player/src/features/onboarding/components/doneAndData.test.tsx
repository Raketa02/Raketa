/**
 * The end of onboarding: a second sport, the summary, and what the app kept.
 *
 * Driven through the real route tree with only `fetch` faked, like every other flow suite
 * here — so the player walks in the way a player does, by answering the last question,
 * pressing what is in front of them and arriving where that leads.
 *
 * Every assertion is about what a player can see or do, or about what left the device. The
 * one exception is declared where it is made: tabular figures are a style, and a style is
 * the only way to assert a requirement whose whole purpose is that two numbers line up.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { router } from 'expo-router';
import { StyleSheet, type StyleProp, type TextStyle } from 'react-native';

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
  installTransport,
  json,
  networkFailure,
  noContent,
  transcriptOf,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { onboardingKeys } from '../hooks/onboardingKeys';
import { useOnboardingPass } from '../store/onboardingPass.store';

const PADEL_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const TENNIS_ID = 'b7c8d9e0-1f2a-4b3c-8d4e-5f6a7b8c9d0e';
/**
 * A second tennis run, unfinished — started on another device, or from a link.
 *
 * Tennis on purpose, and not a sport nobody chose: the defect is that a resumed run was
 * numbered against the queue of a walk that was already over, and tennis is *in* that
 * queue. A third sport would have fallen through to the old "a sport outside the pass is a
 * run of one" fallback and read correctly by accident.
 */
const TENNIS_AGAIN_ID = 'c9d0e1f2-3a4b-4c5d-8e6f-7a8b9c0d1e2f';

const stepPath = (assessmentId: string) => `/api/v1/assessments/${assessmentId}`;
const answersPath = (assessmentId: string) => `${stepPath(assessmentId)}/answers`;

/** One outstanding question. Which sport it belongs to is the route's, not the wire's. */
function outstanding(assessmentId: string): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: assessmentId,
    status: 'in_progress',
    questions_asked: 0,
    transcript: transcriptOf(0),
    question: {
      id: 'q-overhead',
      category: 'Match execution',
      tier: 'standard',
      situation: 'A deep lob pushes you off the net',
      text: 'How often do you play a controlled overhead?',
      qualifier: 'A normal match against players at your level',
      options: [
        { id: 'rarely', text: 'Rarely' },
        { id: 'usually', text: 'Usually' },
      ],
    },
  };
}

/**
 * A rating the ceiling bound: the evidence would have supported more, and 30% is all a
 * questionnaire can prove.
 */
const PADEL_RESULT: Wire['ResultResponse'] = {
  mu: 2.71,
  sigma: 0.62,
  confidence: 30,
  // The ceiling is the engine's and travels with the rating; the two sentences below are
  // the app comparing these two numbers, never a number the app holds.
  confidence_ceiling: 30,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.65, upper: 3.85 },
  status: 'initial_estimate',
  questions_asked: 6,
  engine_version: 'racketskill-v3',
  calibration_priority: 'standard',
  confidence_reason: {
    key: 'limited-match-evidence',
    sentence: 'We have not seen you play yet, so this is a starting estimate.',
  },
  factors: [{ key: 'match-execution', label: 'Match execution', direction: 'up', level: 3.1 }],
  uncertainty_factors: [],
};

/** A rating the evidence bound: answers that disagreed kept it below the ceiling. */
const TENNIS_RESULT: Wire['ResultResponse'] = {
  mu: 1.9,
  sigma: 0.8,
  confidence: 18,
  confidence_ceiling: 30,
  range: { low: 1.1, high: 2.7 },
  band: { name: 'Developing', lower: 1.55, upper: 2.65 },
  status: 'initial_estimate',
  questions_asked: 4,
  engine_version: 'racketskill-v3',
  calibration_priority: 'elevated',
  confidence_reason: {
    key: 'answers-disagreed',
    sentence: 'Some of your answers point to different skill ranges.',
  },
  factors: [],
  uncertainty_factors: [
    {
      key: 'answers-disagreed',
      label: 'Answers pointing to different ranges',
      detail: 'Your answers point to more than one range, so we kept the range wider.',
      sigma_added: 0.21,
    },
  ],
};

function finished(assessmentId: string, result: Wire['ResultResponse']) {
  return {
    assessment_id: assessmentId,
    status: 'completed',
    questions_asked: result.questions_asked,
    transcript: transcriptOf(result.questions_asked),
    question: null,
    result,
  } satisfies Wire['AssessmentStepResponse'];
}

/** What `GET /ratings` says about a sport once its run has produced one. */
function ratingOf(sport: Wire['Sport'], result: Wire['ResultResponse']): Wire['RatingResponse'] {
  return {
    sport,
    mu: result.mu,
    sigma: result.sigma,
    confidence: result.confidence,
    range: result.range,
    band: result.band,
    status: result.status,
    engine_version: result.engine_version,
    updated_at: '2026-08-14T09:00:00Z',
  };
}

const USER: Wire['UserResponse'] = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  nickname: 'ada',
  authority: 'player',
  is_admin: false,
  is_active: true,
  created_at: '2026-08-13T10:00:00Z',
};

/**
 * What a player sees once the gate lets her through: **Now**, not the account
 * placeholder. The strip's own heading, which is present whether or not she is in
 * anything — `ADR-0070` sends every region always, so *present and empty* is the
 * one code path and the heading is always drawn.
 */
const ON_NOW = 'Your matches';

let transport: Transport;
/** What the server holds now. The gate reads it again on the way into the app. */
let held: Wire['RatingResponse'][];

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useOnboardingPass.getState().reset();
  held = [];
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

/**
 * Welcome → the picker → the first chosen sport's opening question.
 *
 * `POST /assessments` answers per sport, the way the real route does: one endpoint, and
 * which run comes back depends on what was asked for.
 */
async function startRating(...sports: readonly string[]) {
  stubGate();
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  transport.on('POST', '/api/v1/assessments', (request) => {
    const { sport } = request.body as { sport: Wire['Sport'] };
    return json(outstanding(sport === 'PADEL' ? PADEL_ID : TENNIS_ID), 201);
  });

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/welcome'));

  fireEvent.press(screen.getByLabelText('Get started'));
  await waitFor(() => expect(screen).toHavePathname('/sports'));

  expect(await screen.findByLabelText('Padel')).toBeTruthy();
  for (const sport of sports) fireEvent.press(screen.getByLabelText(sport));
  fireEvent.press(
    screen.getByLabelText(sports.length === 1 ? 'Rate 1 sport' : `Rate ${sports.length} sports`),
  );
}

/**
 * Answer the outstanding question, which ends the run and lands on its result.
 *
 * The re-stubbed reads are what the server would say afterwards: the run is over with its
 * rating on it, and the player now holds one more rating than they did.
 */
async function answerTheLastQuestion(
  assessmentId: string,
  sport: Wire['Sport'],
  result: Wire['ResultResponse'],
) {
  transport.on('POST', answersPath(assessmentId), () => {
    transport.on('GET', stepPath(assessmentId), () => json(finished(assessmentId, result)));
    held = [...held, ratingOf(sport, result)];
    stubGate({ ratings: held });
    return json(finished(assessmentId, result));
  });

  expect(await screen.findByLabelText('Usually')).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Usually'));
  fireEvent.press(screen.getByLabelText('Confirm answer'));

  await waitFor(() => expect(screen).toHavePathname(`/result/${assessmentId}`));
}

/** The commonest walk: two sports chosen, both rated, standing on the done screen. */
async function rateBothSports() {
  await startRating('Padel', 'Tennis');
  await answerTheLastQuestion(PADEL_ID, 'PADEL', PADEL_RESULT);

  fireEvent.press(await screen.findByLabelText('Rate Tennis'));
  await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_ID}`));
  await answerTheLastQuestion(TENNIS_ID, 'TENNIS', TENNIS_RESULT);

  fireEvent.press(await screen.findByLabelText('See your ratings'));
  await waitFor(() => expect(screen).toHavePathname('/done'));
}

// ---------------------------------------------------------------------------
// Rate another, or done for now
// ---------------------------------------------------------------------------

describe('after a result', () => {
  it('offers the next sport that was chosen, and rates it', async () => {
    await startRating('Padel', 'Tennis');
    await answerTheLastQuestion(PADEL_ID, 'PADEL', PADEL_RESULT);

    // Named, not "next sport": the player chose these and is owed the one they are being
    // offered. The eyebrow moves with it — it is the sole carrier of which sport of how
    // many, now that onboarding's indicator measures the run instead (ADR-0020).
    fireEvent.press(await screen.findByLabelText('Rate Tennis'));

    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_ID}`));
    expect(await screen.findByText('Tennis · Rating 2 of 2')).toBeTruthy();

    const [, second] = transport.requestsTo('POST', '/api/v1/assessments');
    expect(second?.body).toEqual({ sport: 'TENNIS' });
  });

  it('lets a player stop part-way and keep what they have', async () => {
    await startRating('Padel', 'Tennis');
    await answerTheLastQuestion(PADEL_ID, 'PADEL', PADEL_RESULT);

    fireEvent.press(await screen.findByLabelText('Done for now'));

    await waitFor(() => expect(screen).toHavePathname('/done'));
    // What they produced is on the summary; what they skipped is simply not, and no run
    // was started for it. Stopping is an outcome, not an abandonment.
    expect(await screen.findByLabelText('Padel level: 2,71')).toBeTruthy();
    expect(screen.queryByText('Tennis')).toBeNull();
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toHaveLength(1);
  });

  it('tells the player when the next sport fails to start, and retries it in place', async () => {
    // The defect this closes: the result screen held its own copy of "start the next sport
    // and go there" and had no error branch at all, so a failed tap did **nothing
    // visible**. Both screens now call the same hook, and this is the question screen's
    // behaviour arriving here — a message, and the control that failed as the retry.
    await startRating('Padel', 'Tennis');
    await answerTheLastQuestion(PADEL_ID, 'PADEL', PADEL_RESULT);

    transport.on('POST', '/api/v1/assessments', networkFailure());
    fireEvent.press(await screen.findByLabelText('Rate Tennis'));

    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen.getByRole('alert')).toBeTruthy();
    // Still here. A failed start changed nothing, so the padel result is exactly as it
    // was — including the control that failed, which is the retry.
    expect(screen).toHavePathname(`/result/${PADEL_ID}`);
    expect(screen.getByText('Your rating')).toBeTruthy();
    expect(screen.getByLabelText('Rate Tennis')).toBeTruthy();

    // And the latch was released, so pressing again genuinely tries again rather than
    // being swallowed by a departure that never completed.
    transport.on('POST', '/api/v1/assessments', () => json(outstanding(TENNIS_ID), 201));
    fireEvent.press(screen.getByLabelText('Rate Tennis'));

    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_ID}`));
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toHaveLength(3);
  });

  it('offers no next sport when there is none, and never invents one', async () => {
    await startRating('Padel');
    await answerTheLastQuestion(PADEL_ID, 'PADEL', PADEL_RESULT);

    expect(await screen.findByLabelText('See your ratings')).toBeTruthy();
    expect(screen.queryByLabelText(/^Rate /)).toBeNull();
    expect(screen.queryByLabelText('Done for now')).toBeNull();

    fireEvent.press(screen.getByLabelText('See your ratings'));
    await waitFor(() => expect(screen).toHavePathname('/done'));
    expect(await screen.findByLabelText('Padel level: 2,71')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The done screen
// ---------------------------------------------------------------------------

describe('the done screen', () => {
  it('lists every rating this run produced, with its figures and its status', async () => {
    await rateBothSports();

    // One card per sport, each named — the sport's colour is the rail beside its name and
    // never the only thing carrying which rating this is.
    expect(await screen.findByLabelText('Padel level: 2,71')).toBeTruthy();
    expect(await screen.findByLabelText('Tennis level: 1,90')).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.getByText('Tennis')).toBeTruthy();

    expect(screen.getByLabelText('Padel likely range: 2,09 – 3,33')).toBeTruthy();
    expect(screen.getByLabelText('Padel confidence: 30%')).toBeTruthy();
    expect(screen.getByLabelText('Tennis likely range: 1,10 – 2,70')).toBeTruthy();
    expect(screen.getByLabelText('Tennis confidence: 18%')).toBeTruthy();

    // Everyone leaves onboarding as an Initial Estimate — the questionnaire counts no
    // matches — and each card says so rather than the screen saying it once.
    expect(screen.getByLabelText('Padel rating status: Initial estimate')).toBeTruthy();
    expect(screen.getByLabelText('Tennis rating status: Initial estimate')).toBeTruthy();
  });

  it('distinguishes a Confidence the ceiling bound from one the evidence bound', async () => {
    await rateBothSports();

    // Two different statements about a player, and only one is true of each rating. Padel
    // reached the ceiling: nothing the player answered held it back. Tennis did not, so
    // the ceiling bound nothing and its own evidence is what stopped it.
    expect(await screen.findByText(/Nothing you answered held it back/)).toBeTruthy();
    expect(screen.getByText(/because your answers left more to settle/)).toBeTruthy();

    // Both sentences name the ceiling that was actually served with each rating.
    expect(screen.getByText(/reached the 30% a questionnaire can prove/)).toBeTruthy();
    expect(screen.getByText(/sits below the 30% a questionnaire can prove/)).toBeTruthy();
  });

  it('reads each rating against the ceiling it was served, not a number of its own', async () => {
    // The same 30% is the ceiling for one engine and short of it for another. A client
    // holding a copy would tell this player nothing held their padel rating back, when the
    // engine that produced it says its own evidence did.
    await startRating('Padel');
    await answerTheLastQuestion(PADEL_ID, 'PADEL', {
      ...PADEL_RESULT,
      confidence: 30,
      confidence_ceiling: 45,
    });

    fireEvent.press(await screen.findByLabelText('See your ratings'));
    await waitFor(() => expect(screen).toHavePathname('/done'));

    expect(await screen.findByText(/sits below the 45% a questionnaire can prove/)).toBeTruthy();
    expect(screen.queryByText(/Nothing you answered held it back/)).toBeNull();
  });

  it('says nothing about a ceiling for a rating whose engine has been retired', async () => {
    // No served ceiling is not a missing number to fill in — it is a rating replayed from
    // its stream, which keeps its figures and loses its explanation. The card shows the
    // figures and simply does not make the ceiling-versus-evidence claim, exactly as the
    // result screen shows no confidence sentence when the engine sent none.
    await startRating('Padel');
    await answerTheLastQuestion(PADEL_ID, 'PADEL', {
      ...PADEL_RESULT,
      confidence_ceiling: null,
      confidence_reason: null,
    });

    fireEvent.press(await screen.findByLabelText('See your ratings'));
    await waitFor(() => expect(screen).toHavePathname('/done'));

    expect(await screen.findByLabelText('Padel confidence: 30%')).toBeTruthy();
    expect(screen.queryByText(/a questionnaire can prove/)).toBeNull();
  });

  it('says the ratings are hypotheses, and that matches are what narrow them', async () => {
    await rateBothSports();

    // The sentence that frames the cards. A player who leaves believing their Level is a
    // verdict has been mis-served by this screen.
    expect(await screen.findByText('These are hypotheses, not verdicts')).toBeTruthy();
    expect(screen.getByText(/Real matches are what narrow the range/)).toBeTruthy();
  });

  it('names the engine that produced them, which is what the data screen claims is kept', async () => {
    await rateBothSports();

    // Both were rated by the same engine, and saying so twice would read as two facts.
    expect(await screen.findByText('Produced by rating engine racketskill-v3')).toBeTruthy();
  });

  it('lists what this run produced, not what the player is rated at', async () => {
    // A player already rated at padel, standing in an unfinished tennis run — which is
    // also the single-sport path, since the queue was never persisted and a run reached
    // on its own has nothing after it.
    //
    // **Reached by a link rather than by the entry gate**, because `ADR-0084` stopped the
    // gate resuming a run for a player who already holds a rating: it parks, and Now's
    // door is the way back in. A link is the other way a player stands here with no pass
    // running, and it is the branch `admissionTo` calls *begin*.
    held = [ratingOf('PADEL', PADEL_RESULT)];
    stubGate({ ratings: held, runs: [runInProgress('TENNIS', TENNIS_ID)] });
    transport.on('GET', stepPath(TENNIS_ID), () => json(outstanding(TENNIS_ID)));

    await launchSignedIn(`/question/${TENNIS_ID}?sport=tennis`);
    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_ID}`));
    await answerTheLastQuestion(TENNIS_ID, 'TENNIS', TENNIS_RESULT);

    fireEvent.press(await screen.findByLabelText('See your ratings'));
    await waitFor(() => expect(screen).toHavePathname('/done'));

    // Padel is on this player's account and is deliberately not on this screen: they
    // answered no padel question today, and a card claiming otherwise would be the
    // ratings collection answering a question this screen did not ask.
    expect(await screen.findByLabelText('Tennis level: 1,90')).toBeTruthy();
    expect(screen.queryByText('Padel')).toBeNull();
    expect(screen.queryByLabelText(/^Padel /)).toBeNull();
  });

  it('writes every figure in tabular numerals, so the cards line up', async () => {
    await rateBothSports();

    // The one style assertion in this file, and it is here because the requirement *is*
    // the style: two levels one under another that do not share a digit width read as a
    // ragged column, whatever the numbers are.
    const tabular = (element: { props: { style?: StyleProp<TextStyle> } }) =>
      StyleSheet.flatten(element.props.style).fontVariant;

    expect(tabular(await screen.findByText('2,71'))).toEqual(['tabular-nums']);
    expect(tabular(screen.getByText('1,90'))).toEqual(['tabular-nums']);
    expect(tabular(screen.getByText('2,09 – 3,33'))).toEqual(['tabular-nums']);
    expect(tabular(screen.getByText('18%'))).toEqual(['tabular-nums']);
  });
});

// ---------------------------------------------------------------------------
// The data screen, and the way out
// ---------------------------------------------------------------------------

describe('the data screen', () => {
  async function reachTheDataScreen() {
    await rateBothSports();
    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/data'));
  }

  it('says what was kept, what is never done with it, and that no Level can be hand-edited', async () => {
    await reachTheDataScreen();

    expect(await screen.findByText(/Your answers, the rating they produced/)).toBeTruthy();
    expect(screen.getByText('What we keep')).toBeTruthy();
    expect(screen.getByText(/which version of the rating engine produced it/)).toBeTruthy();
    expect(screen.getByText(/not shared with other players, and they are never sold/)).toBeTruthy();

    // The invariant the whole rating context is built on, said plainly because the player
    // is entitled to know it.
    expect(screen.getByText('No one can hand-edit a Level')).toBeTruthy();
    expect(screen.getByText(/not Raketa staff/)).toBeTruthy();
    expect(screen.getByText(/proved, never declared/)).toBeTruthy();

    expect(screen.getByText('You can rate a sport again later')).toBeTruthy();
  });

  it('calls no endpoint at all', async () => {
    // Entered directly, which is the only way to assert this without counting around
    // whatever the screen before it had in flight. The whole screen is copy: there is no
    // hook here, and an empty request list is the assertion that says so.
    await launchSignedIn('/data');

    expect(await screen.findByText('What Raketa keeps')).toBeTruthy();
    expect(transport.requests).toEqual([]);
  });

  it('captures no consent and records no preference, anywhere in the flow', async () => {
    await reachTheDataScreen();
    fireEvent.press(screen.getByLabelText('Start playing'));

    // Every write this flow makes, from welcome to the app: two runs started and two
    // answers submitted. Nothing here is a consent — what a consent covers is a legal
    // question this flow cannot answer — and the match-proposals opt-in is its own
    // explicit, skippable step whenever it arrives, never folded into this one.
    const writes = transport.requests.filter((request) => request.method !== 'GET');
    expect(writes.map((request) => `${request.method} ${request.path}`)).toEqual([
      'POST /api/v1/assessments',
      `POST ${answersPath(PADEL_ID)}`,
      'POST /api/v1/assessments',
      `POST ${answersPath(TENNIS_ID)}`,
    ]);
  });

  it('enters the app when it is done, and the next launch goes straight there', async () => {
    transport.on('GET', '/api/v1/users/me', () => json(USER));
    await reachTheDataScreen();

    fireEvent.press(screen.getByLabelText('Start playing'));

    // The gate decides where finishing lands, exactly as it does from every other exit:
    // a player who now holds ratings belongs in the app.
    expect(await screen.findByText(ON_NOW)).toBeTruthy();
    expect(screen).toHavePathname('/');

    // And on the next launch, with nothing cached — which is the whole point of onboarding
    // happening once. The server holds two ratings now, so the gate never offers it again.
    screen.unmount();
    queryClient.clear();
    await launchSignedIn();

    expect(await screen.findByText(ON_NOW)).toBeTruthy();
    expect(screen).toHavePathname('/');
    // Not back through the questionnaire, and not back through the welcome.
    expect(screen.queryByText("Let's find your level")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Two passes, one process

/**
 * The case every other suite in this app hides.
 *
 * Each of them resets the stores in `beforeEach`, so a walk through onboarding always
 * begins from nothing — and the defect is precisely that a *second* walk in the same
 * process did not. **Nothing is reset between the two passes below**, deliberately, and
 * that is what makes this the regression test rather than a longer version of the others.
 *
 * The second pass is reached the way a player reaches one: not through the picker, but by
 * standing in a run that already exists. That is why the picker's "nothing else reaches
 * onboarding twice in one launch" assumption was never true.
 *
 * It used to be the entry gate's resume path. `ADR-0084` took that away from a player who
 * already holds a rating — the run **parks**, and Now's door is the way back into it — so
 * the second pass here is reached by a link into the run instead. What is being tested is
 * unchanged and is not about how she got there: a pass begun on top of a finished walk
 * must be numbered against **its own** queue.
 */
describe('a second pass in the same process', () => {
  /** Two sports rated, the closing screens read, standing in the app. */
  async function completeAPassAndEnterTheApp() {
    transport.on('GET', '/api/v1/users/me', () => json(USER));
    await rateBothSports();

    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/data'));

    fireEvent.press(screen.getByLabelText('Start playing'));
    expect(await screen.findByText(ON_NOW)).toBeTruthy();
    expect(screen).toHavePathname('/');
  }

  /**
   * Into a run that already exists — no relaunch, no picker, and **no store reset**. A
   * third sport the player started somewhere else, or on another device, is the ordinary
   * way this happens.
   */
  async function resumeTennisWithoutRelaunching() {
    stubGate({ ratings: held, runs: [runInProgress('TENNIS', TENNIS_AGAIN_ID)] });
    transport.on('GET', stepPath(TENNIS_AGAIN_ID), () => json(outstanding(TENNIS_AGAIN_ID)));

    await queryClient.invalidateQueries({ queryKey: onboardingKeys.runInProgress() });
    act(() => {
      router.replace(`/question/${TENNIS_AGAIN_ID}?sport=tennis`);
    });
    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_AGAIN_ID}`));
  }

  it('reports a resumed run as one of one, not as the last pass plus one', async () => {
    await completeAPassAndEnterTheApp();
    await resumeTennisWithoutRelaunching();

    // The defect, exactly as filed: padel and tennis were rated in a walk that is over,
    // and this single run used to be numbered against that walk's queue — "Rating 2 of 2"
    // for one run. A run resumed on its own is a pass of one sport, and the eyebrow says
    // so, because the pass does.
    expect(await screen.findByText(/Tennis · Rating 1 of 1/)).toBeTruthy();
    expect(screen.queryByText(/Rating 2 of 2/)).toBeNull();
  });

  it("sends a player who abandons a resumed run to the app, not to an earlier walk's summary", async () => {
    await completeAPassAndEnterTheApp();
    await resumeTennisWithoutRelaunching();

    transport.on('POST', `${stepPath(TENNIS_AGAIN_ID)}/abandonment`, () => noContent());
    stubGate({ ratings: held, runs: [] });

    fireEvent.press(screen.getByLabelText('Leave this rating'));
    fireEvent.press(await screen.findByLabelText(/^Stop rating Tennis\./));

    // This pass rated nothing, so there is no account to give. The done screen would have
    // listed padel and tennis — ratings from a walk the player already finished and was
    // already shown — which is the summary they must not be sent back to.
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(screen.queryByText('Your ratings')).toBeNull();
  });
});

/**
 * Leaving the questionnaire, and coming back to it.
 *
 * Driven through the real route tree with only `fetch` faked: the router, the http
 * client, error mapping, the mappers, the use-cases, the cache and the screens all run.
 *
 * Two operations with opposite consequences share one confirm, so most of what is
 * asserted here is the *difference* between them — what leaves the device, what the gate
 * answers afterwards, and what a relaunch does.
 */

import { onlineManager } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { cleanup, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  SPORTS_SERVED,
  launchSignedIn,
  runInProgress,
  stubGate as stubGateWith,
  stubRunsInProgress,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  networkFailure,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { onboardingKeys } from '../hooks/onboardingKeys';
import { useDeferredRuns } from '../store/deferredRuns.store';
import { useOnboardingPass } from '../store/onboardingPass.store';

const PADEL_RUN = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const TENNIS_RUN = '2a1b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d';

const abandonmentPath = (id: string) => `/api/v1/assessments/${id}/abandonment`;
const stepPath = (id: string) => `/api/v1/assessments/${id}`;

function opening(assessmentId: string, text: string): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: assessmentId,
    status: 'in_progress',
    questions_asked: 0,
    question: {
      id: `q-played-${assessmentId}`,
      category: 'Recent activity',
      tier: null,
      situation: 'Before anything else',
      text,
      qualifier: 'Any level counts',
      options: [
        { id: 'never', text: 'Never played' },
        { id: 'regular', text: 'I play regularly' },
      ],
    },
  };
}

const PADEL_OPENING = opening(PADEL_RUN, 'Have you played padel before?');
const TENNIS_OPENING = opening(TENNIS_RUN, 'Have you played tennis before?');

/** The second padel question — what a resumed run must land on, not the first. */
const PADEL_SECOND: Wire['AssessmentStepResponse'] = {
  assessment_id: PADEL_RUN,
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
      { id: 'usually', text: 'Usually' },
    ],
  },
};

const PADEL_ABANDONED: Wire['AssessmentStepResponse'] = {
  assessment_id: PADEL_RUN,
  status: 'abandoned',
  questions_asked: 1,
  question: null,
};

const PADEL_RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.65, upper: 3.85 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

/** The padel run finished, as the done screen reads it back to draw its card. */
const PADEL_FINISHED: Wire['AssessmentStepResponse'] = {
  assessment_id: PADEL_RUN,
  status: 'completed',
  questions_asked: 4,
  question: null,
  result: {
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.65, upper: 3.85 },
    status: 'initial_estimate',
    questions_asked: 4,
    engine_version: 'racketskill-v3',
    calibration_priority: 'standard',
    confidence_reason: {
      key: 'self-report-ceiling',
      sentence: 'A questionnaire can only take a rating so far.',
    },
    factors: [{ key: 'match-execution', label: 'Match execution', direction: 'up', level: 3.1 }],
    uncertainty_factors: [],
  },
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
  useDeferredRuns.getState().reset();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
});

/**
 * A relaunch: the process is gone, so the cache and every in-memory store go with it.
 * Nothing about the transcript ever lived on the device, which is the whole reason resume
 * survives one.
 */
async function relaunch(initialUrl = '/') {
  cleanup();
  queryClient.clear();
  useOnboardingPass.getState().reset();
  useDeferredRuns.getState().reset();
  resetSessionStatus();
  await launchSignedIn(initialUrl);
}

/** Land mid-run, the way the gate does: an unfinished padel assessment, resumed. */
async function resumePadel(step = PADEL_OPENING) {
  stubGate({ runs: [runInProgress('PADEL', PADEL_RUN)] });
  transport.on('GET', stepPath(PADEL_RUN), () => json(step));

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_RUN}`));
  expect(await screen.findByText(step.question?.text ?? '')).toBeTruthy();
}

/** Choose two sports and start the first, so there is a queue with a sport after padel. */
async function walkInWithTwoSports() {
  stubGate();
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  transport.on('POST', '/api/v1/assessments', () => json(PADEL_OPENING, 201));

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/welcome'));
  fireEvent.press(screen.getByLabelText('Get started'));

  expect(await screen.findByLabelText('Padel')).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Padel'));
  fireEvent.press(screen.getByLabelText('Tennis'));
  fireEvent.press(screen.getByLabelText('Rate 2 sports'));

  expect(await screen.findByText('Have you played padel before?')).toBeTruthy();
}

function openTheConfirm() {
  fireEvent.press(screen.getByLabelText('Leave this rating'));
}

/**
 * A server that actually performs the transition: once the run is abandoned, it is no
 * longer among the player's unfinished runs.
 *
 * Worth the four lines. A fake that kept answering "unfinished" after a successful
 * abandonment would let the client pass while relying on a cached answer the server had
 * already contradicted — which is the exact failure the gate has to survive.
 *
 * `remaining` is what is still unfinished afterwards, which for every case here is nothing.
 */
function stubAbandonment(
  assessmentId: string,
  remaining: readonly Wire['InProgressAssessmentResponse'][] = [],
) {
  transport.on('POST', abandonmentPath(assessmentId), () => {
    stubRunsInProgress(transport, remaining);
    return noContent();
  });
}

// ---------------------------------------------------------------------------
// The confirm itself
// ---------------------------------------------------------------------------

describe('the way out', () => {
  it('is reachable from the question and offers all three choices', async () => {
    await resumePadel();

    // The close control is in the header's right slot. It is not a back control: leaving
    // the questionnaire is not revisiting an answer (ADR-0017).
    expect(screen.queryByLabelText('Back')).toBeNull();
    openTheConfirm();

    expect(await screen.findByRole('header', { name: 'Leave this rating?' })).toBeTruthy();
    expect(screen.getByLabelText(/^Continue later\./)).toBeTruthy();
    expect(screen.getByLabelText(/^Stop rating Padel\./)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Keep answering' })).toBeTruthy();
  });

  it('says on the abandon option that the answers are discarded', async () => {
    await resumePadel();
    openTheConfirm();

    // The one destructive action in onboarding, in a flow that has spent ten questions
    // teaching the player that every tap is permanent.
    expect(
      await screen.findByText(/The answers you've given for Padel are discarded/),
    ).toBeTruthy();
    // And the other option says the opposite, so the two cannot be confused.
    expect(screen.getByText(/Every answer you've given for Padel is kept/)).toBeTruthy();
  });

  it('keeps the question when the player carries on, and sends nothing', async () => {
    await resumePadel();
    openTheConfirm();
    expect(await screen.findByRole('header', { name: 'Leave this rating?' })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Keep answering' }));

    await waitFor(() =>
      expect(screen.queryByRole('header', { name: 'Leave this rating?' })).toBeNull(),
    );
    expect(screen.getByText('Have you played padel before?')).toBeTruthy();
    expect(transport.requestsTo('POST', abandonmentPath(PADEL_RUN))).toEqual([]);
    expect(screen).toHavePathname(`/question/${PADEL_RUN}`);
  });
});

// ---------------------------------------------------------------------------
// Modal semantics — the sheet is a modal, not a card at the bottom of the screen
// ---------------------------------------------------------------------------

describe('the confirm as a modal', () => {
  it('hides the question behind it from a screen reader, and gives it back on close', async () => {
    await resumePadel();
    expect(screen.getByLabelText('Confirm answer')).toBeTruthy();

    openTheConfirm();
    expect(await screen.findByRole('header', { name: 'Leave this rating?' })).toBeTruthy();

    // Nothing behind the sheet is reachable while it is open — which is what focus being
    // trapped means to someone using VoiceOver or TalkBack. The queries below exclude
    // subtrees hidden from assistive technology, so this is the behaviour, not the props.
    expect(screen.queryByLabelText('Confirm answer')).toBeNull();
    expect(screen.queryByText('Have you played padel before?')).toBeNull();
    expect(screen.queryByLabelText('I play regularly')).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: 'Keep answering' }));

    expect(await screen.findByText('Have you played padel before?')).toBeTruthy();
    expect(screen.getByLabelText('Confirm answer')).toBeTruthy();
  });

  it('returns accessibility focus to the control that opened it', async () => {
    const focus = jest.spyOn(AccessibilityInfo, 'setAccessibilityFocus');
    try {
      await resumePadel();
      focus.mockClear();

      openTheConfirm();
      expect(await screen.findByRole('header', { name: 'Leave this rating?' })).toBeTruthy();
      // Focus moves into the sheet rather than being left on a screen the player can no
      // longer reach.
      expect(focus).toHaveBeenCalledTimes(1);

      fireEvent.press(screen.getByRole('button', { name: 'Keep answering' }));
      await waitFor(() => expect(focus).toHaveBeenCalledTimes(2));
    } finally {
      focus.mockRestore();
    }
  });
});

// ---------------------------------------------------------------------------
// Continue later — nothing is sent, and nothing is lost
// ---------------------------------------------------------------------------

describe('continuing later', () => {
  it('leaves the questionnaire without a destructive call', async () => {
    await resumePadel();
    openTheConfirm();

    fireEvent.press(await screen.findByLabelText(/^Continue later\./));

    // Out of the questionnaire, and out of it against a server that still reports the
    // run as unfinished — because it is. Landing anywhere but back on the question is
    // the whole test: the gate reads the player's decision as well as the server's fact.
    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('POST', abandonmentPath(PADEL_RUN))).toEqual([]);
    // Nothing at all was written. Not the abandonment, not anything else.
    expect(transport.requests.filter((r) => r.method !== 'GET')).toEqual([]);
  });

  it('resumes at the outstanding question on the next launch, answers intact', async () => {
    // Two answers in already: the run's outstanding question is the second one, and that
    // is where a relaunch has to land — not at the start of the questionnaire.
    await resumePadel(PADEL_SECOND);
    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Continue later\./));
    await waitFor(() => expect(screen).toHavePathname('/welcome'));

    await relaunch();

    // The deferral died with the process, which is exactly what makes this true. The
    // transcript never lived on the device either — the server reproduces the question.
    await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_RUN}`));
    expect(
      await screen.findByText(
        'How often do you play a controlled overhead and recover your position?',
      ),
    ).toBeTruthy();
    expect(screen.getByLabelText('Difficulty: discriminating')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Abandonment — the run ends, and the flow moves on
// ---------------------------------------------------------------------------

describe('abandoning a sport', () => {
  it('ends the run and starts the next sport the player chose', async () => {
    await walkInWithTwoSports();

    stubAbandonment(PADEL_RUN);
    transport.on('POST', '/api/v1/assessments', () => json(TENNIS_OPENING, 201));

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Padel\./));

    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_RUN}`));
    expect(await screen.findByText('Have you played tennis before?')).toBeTruthy();

    expect(transport.requestsTo('POST', abandonmentPath(PADEL_RUN))).toHaveLength(1);
    const [started] = transport.requestsTo('POST', '/api/v1/assessments').slice(-1);
    expect(started?.body).toEqual({ sport: 'TENNIS' });

    // The padel question is gone and there is no way back to it. Abandoning is not back
    // navigation, and no path returns a player to a question they have answered.
    expect(screen.queryByText('Have you played padel before?')).toBeNull();
    expect(screen.queryByLabelText('Back')).toBeNull();
    // A sport that was abandoned was still chosen, so the queue is not renumbered.
    expect(screen.getByLabelText('Rating 2 of 2')).toBeTruthy();
  });

  it('ends onboarding when it was the only sport', async () => {
    await resumePadel();
    stubAbandonment(PADEL_RUN);

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Padel\./));

    // Onboarding ends and the entry gate answers for an unrated player with no run left,
    // exactly as it does from the result screen. There is nowhere else this can go: the
    // run produced nothing, so `/done` would have only its empty state to show, and
    // answering *stop* with two more screens is the wrong response to what was asked.
    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('POST', abandonmentPath(PADEL_RUN))).toHaveLength(1);
    // Nothing was started in its place: there was nothing after it in the queue.
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toEqual([]);
  });

  it('leaves through the done screen when the run already produced a rating', async () => {
    // Padel was rated in this pass; tennis is the last sport, and the player stops there.
    // Abandoning is still the end of the run, so the closing screens are still owed: the
    // done screen accounts for the rating they did make, and the data screen says what
    // was kept and that no one can hand-edit a Level. Ending on an abandonment is not a
    // reason to be told none of it.
    useOnboardingPass.getState().record({ assessmentId: PADEL_RUN, sport: 'padel' });

    stubGate({ runs: [runInProgress('TENNIS', TENNIS_RUN)] });
    transport.on('GET', stepPath(TENNIS_RUN), () => json(TENNIS_OPENING));
    transport.on('GET', stepPath(PADEL_RUN), () => json(PADEL_FINISHED));
    stubAbandonment(TENNIS_RUN);

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_RUN}`));

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Tennis\./));

    await waitFor(() => expect(screen).toHavePathname('/done'));
    // The abandonment still happened — this is a different destination, not a different
    // operation. The tennis run is ended on the server exactly as before.
    expect(transport.requestsTo('POST', abandonmentPath(TENNIS_RUN))).toHaveLength(1);
  });

  it('leaves cleanly even when the gate still has an answer cached', async () => {
    await resumePadel();
    stubAbandonment(PADEL_RUN);

    // A warm gate: the launch answer is still in the cache and it says this run is
    // unfinished. That was true a moment ago and is about to stop being true.
    queryClient.setQueryData(onboardingKeys.runInProgress(), {
      assessmentId: PADEL_RUN,
      sport: 'padel',
    });

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Padel\./));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    // Not even briefly: a stale "resume" would put the player back on a question
    // belonging to a run that no longer exists.
    expect(screen.queryByText('Have you played padel before?')).toBeNull();
  });

  it("touches no other sport's assessment", async () => {
    // Rated at padel already, and half way through a tennis run that is not this one.
    stubGate({ ratings: [PADEL_RATING], runs: [runInProgress('TENNIS', TENNIS_RUN)] });
    transport.on('GET', stepPath(TENNIS_RUN), () => json(TENNIS_OPENING));
    stubAbandonment(TENNIS_RUN);

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_RUN}`));

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Tennis\./));

    // Into the app: this pass produced nothing, so there is no account to give. The padel
    // rating is older than this run — the player never answered a padel question today —
    // and abandoning tennis did not cost them the sport they were already rated at.
    await waitFor(() => expect(screen).toHavePathname('/'));

    // One abandonment, naming one run. Nothing was sent about padel, whose rating and
    // whose stream are none of this operation's business.
    const abandonments = transport.requests.filter((r) => r.path.endsWith('/abandonment'));
    expect(abandonments.map((r) => r.path)).toEqual([abandonmentPath(TENNIS_RUN)]);
  });

  it('is not resumed on a later launch, and the sport can be started again', async () => {
    await resumePadel();
    stubAbandonment(PADEL_RUN);

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Padel\./));
    await waitFor(() => expect(screen).toHavePathname('/welcome'));

    // The run is over on the server, so the sport reports nothing in progress. The gate
    // has no run to resume and no rating, so onboarding starts from the beginning.
    transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
    const RESTARTED = opening(
      '3c2d1e0f-4a5b-4c6d-8e7f-9a0b1c2d3e4f',
      'Have you played padel before?',
    );
    transport.on('POST', '/api/v1/assessments', () => json(RESTARTED, 201));
    await relaunch();

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    fireEvent.press(screen.getByLabelText('Get started'));
    expect(await screen.findByLabelText('Padel')).toBeTruthy();
    fireEvent.press(screen.getByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Rate 1 sport'));

    // A fresh run, from the opening question — not the old one picked back up.
    await waitFor(() =>
      expect(screen).toHavePathname('/question/3c2d1e0f-4a5b-4c6d-8e7f-9a0b1c2d3e4f'),
    );
    expect(screen.getByText('Question 1')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Failure — and why a retry cannot make it worse
// ---------------------------------------------------------------------------

describe('when abandoning does not go through', () => {
  it('can be retried in place, and succeeds', async () => {
    await resumePadel();

    transport.on('POST', abandonmentPath(PADEL_RUN), networkFailure());
    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Padel\./));

    expect(
      await screen.findByText("We couldn't reach Rakieta. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen.getByRole('alert')).toBeTruthy();
    // Still on the question, still in the run: a failed abandonment abandons nothing.
    expect(screen).toHavePathname(`/question/${PADEL_RUN}`);

    // Abandonment is a state transition and a second one is a no-op on the server, so
    // pressing again is safe however far the first attempt actually got.
    stubAbandonment(PADEL_RUN);
    fireEvent.press(screen.getByLabelText(/^Stop rating Padel\./));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('POST', abandonmentPath(PADEL_RUN))).toHaveLength(2);
  });

  it('keeps the confirm open when the next sport fails to start, and retries the pair', async () => {
    await walkInWithTwoSports();

    stubAbandonment(PADEL_RUN);
    // The abandonment lands and the connection drops before the next sport can start —
    // the moment where a confirm that closed itself would leave the failure nowhere.
    transport.on('POST', '/api/v1/assessments', networkFailure());

    openTheConfirm();
    fireEvent.press(await screen.findByLabelText(/^Stop rating Padel\./));

    // The abandonment stands — only the departure failed, and the confirm is where the
    // player can see that and try again.
    expect(
      await screen.findByText("We couldn't reach Rakieta. Check your connection and try again."),
    ).toBeTruthy();

    transport.on('POST', '/api/v1/assessments', () => json(TENNIS_OPENING, 201));
    fireEvent.press(screen.getByLabelText(/^Stop rating Padel\./));

    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_RUN}`));
    expect(transport.requestsTo('POST', abandonmentPath(PADEL_RUN))).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// A run that ended somewhere else
// ---------------------------------------------------------------------------

describe('a run abandoned elsewhere', () => {
  it('never claims a rating is ready', async () => {
    // Both terminal states arrive with no outstanding question. Reading "nothing left to
    // ask" as "there is a result" would announce a padel rating to a player who stopped
    // rating padel on another device — and there is no rating, because abandoning
    // discards the answers rather than scoring them.
    //
    // Reached the way it happens in life: a link to a run that is already over, with the
    // server reporting nothing in progress for the sport.
    stubGate();
    transport.on('GET', stepPath(PADEL_RUN), () => json(PADEL_ABANDONED));

    await launchSignedIn(`/question/${PADEL_RUN}?sport=padel`);

    // Straight out of the questionnaire, the same way abandoning from here leaves.
    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(screen.queryByText('Your rating is ready')).toBeNull();
  });
});

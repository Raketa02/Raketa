/**
 * The door into a sport she holds no rating at, walked end to end.
 *
 * `ADR-0084` closes the sport bar's one open cost with a **destination rather than a
 * better sentence**, and this is the whole of it as a player meets it: three of five
 * chips lie to a one-sport player until she taps one, and the lie survives exactly one
 * tap. Driven through the real route tree with only `fetch` faked, like every other flow
 * suite here — the router, the http client, the mappers, the stores and both features'
 * screens all run.
 *
 * It lives in `onboarding/` rather than in `now/` because everything but the first tap is
 * onboarding's: Now knows an address and nothing else.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { DEFAULT_SPORT_FILTER, selectSportFilter } from '@/features/now/types';
import { door, nowPathFor, shelf, stubNow } from '@/test-support/now';
import {
  launchSignedIn,
  runInProgress,
  stubGate as stubGateWith,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  networkFailure,
  transcriptOf,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useOnboardingPass } from '../store/onboardingPass.store';

const SQUASH_RUN = 'd4e5f6a7-8b9c-4d0e-8f1a-2b3c4d5e6f70';
const TENNIS_RUN = 'e5f6a7b8-9c0d-4e1f-8a2b-3c4d5e6f7081';

const stepPath = (assessmentId: string) => `/api/v1/assessments/${assessmentId}`;

/** A padel player: what the gate reads on the way into the app. */
const PADEL_RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

const SQUASH_RESULT: Wire['ResultResponse'] = {
  mu: 1.9,
  sigma: 0.71,
  confidence: 26,
  questions_asked: 1,
  range: { low: 1.19, high: 2.61 },
  band: { name: 'Improver', lower: 1.6, upper: 2.7 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  calibration_priority: 'standard',
};

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

/**
 * The screen a chip for an unrated sport composes: a door where the ranked shelves would
 * be, and the two light shelves beneath it.
 */
function unratedScreen(code: Wire['DoorCode']): Wire['NowResponse'] {
  return {
    offers: { stamp: 1, cards: [] },
    your_matches: { stamp: 1, cards: [] },
    shelves: {
      stamp: 1,
      shelves: [door(code), shelf('newPlayers', []), shelf('newClubs', [])],
    },
    debt: null,
  };
}

const ON_NOW = 'Your matches';

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useOnboardingPass.getState().reset();
  // The chip outlives a navigation on purpose — that is what puts her back on the sport
  // she took up — so it also outlives a test unless it is put back.
  selectSportFilter(DEFAULT_SPORT_FILTER);
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

/**
 * A padel player standing on Now, tapping the Squash chip.
 *
 * `runs` is what the server says she has left unfinished — which the gate reads and, since
 * `ADR-0084`, no longer acts on.
 */
async function tapAnUnratedChip(
  code: Wire['DoorCode'],
  runs: readonly Wire['InProgressAssessmentResponse'][] = [],
) {
  stubGateWith(transport, { ratings: [PADEL_RATING], runs });
  transport.on('GET', nowPathFor('SQUASH'), () => json(unratedScreen(code)));

  await launchSignedIn();
  expect(await screen.findByText(ON_NOW)).toBeTruthy();

  fireEvent.press(screen.getByLabelText('Squash'));
}

describe('a chip for a sport she holds no rating at', () => {
  it('shows the ask where the ranked shelves would be, above the two light ones', async () => {
    await tapAnUnratedChip('noRunYet');

    // The sentence is worded from the chip she is holding, because the block carries no
    // sport of its own.
    expect(await screen.findByText(/We have not placed you at Squash yet/)).toBeTruthy();
    expect(screen.getByLabelText('Take the Squash questions')).toBeTruthy();

    // Beneath it, and that is the argument rather than a leftover: she sees there are
    // squash clubs here before spending two minutes.
    expect(screen.getByText('New on Raketa')).toBeTruthy();
    expect(screen.getByText('New clubs')).toBeTruthy();
  });

  it('says something different when a run is already parked', async () => {
    await tapAnUnratedChip('runParked');

    expect(
      await screen.findByText('Your Squash questions are waiting where you left them.'),
    ).toBeTruthy();
    expect(screen.getByLabelText('Pick up where you left off')).toBeTruthy();
  });

  it('draws no ask on a rated sport whose city happens to be empty', async () => {
    // The inference `ADR-0084` refuses: an empty screen in a sport she **is** rated at
    // looks identical from here, and the phone holds no rule that could tell them apart.
    stubGateWith(transport, { ratings: [PADEL_RATING] });
    transport.on('GET', nowPathFor('PADEL'), () =>
      json<Wire['NowResponse']>({
        offers: { stamp: 1, cards: [] },
        your_matches: { stamp: 1, cards: [] },
        shelves: { stamp: 1, shelves: [] },
        debt: null,
      }),
    );

    await launchSignedIn();
    expect(await screen.findByText(ON_NOW)).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Padel'));

    expect(await screen.findByText('Nothing open in Padel right now')).toBeTruthy();
    expect(screen.queryByText(/questions/)).toBeNull();
  });
});

describe('taking up the sport', () => {
  /** The one request the door makes, answering with whichever run the server holds. */
  function stubStart(assessmentId: string) {
    transport.on('POST', '/api/v1/assessments', () => json(outstanding(assessmentId), 201));
  }

  /** The answer that finishes the run, and the squash rating the server holds after it. */
  function stubTheLastAnswer() {
    transport.on('POST', `${stepPath(SQUASH_RUN)}/answers`, () => {
      transport.on('GET', stepPath(SQUASH_RUN), () => json(finished(SQUASH_RUN, SQUASH_RESULT)));
      stubGateWith(transport, {
        ratings: [PADEL_RATING, { ...PADEL_RATING, sport: 'SQUASH' }],
      });
      transport.on('GET', nowPathFor('SQUASH'), () => json(unratedScreen('noRunYet')));
      return json(finished(SQUASH_RUN, SQUASH_RESULT));
    });
  }

  it('opens the questionnaire for the sport she tapped', async () => {
    await tapAnUnratedChip('noRunYet');
    stubStart(SQUASH_RUN);

    fireEvent.press(await screen.findByLabelText('Take the Squash questions'));

    await waitFor(() => expect(screen).toHavePathname(`/question/${SQUASH_RUN}`));
    expect(await screen.findByText('Squash · Rating 1 of 1')).toBeTruthy();

    const [started] = transport.requestsTo('POST', '/api/v1/assessments');
    expect(started?.body).toEqual({ sport: 'SQUASH' });
  });

  it('continues a parked run where it stopped, and asks for it the same way', async () => {
    // Two sentences, **one behaviour**: `POST /assessments` is idempotent per player and
    // sport and hands back the parked run's outstanding question, so the phone never
    // learns the difference and holds no rule about resuming (`ADR-0053`).
    await tapAnUnratedChip('runParked', [runInProgress('SQUASH', SQUASH_RUN)]);
    transport.on('POST', '/api/v1/assessments', () =>
      json(
        {
          ...outstanding(SQUASH_RUN),
          questions_asked: 4,
          transcript: transcriptOf(4),
        },
        200,
      ),
    );

    fireEvent.press(await screen.findByLabelText('Pick up where you left off'));

    await waitFor(() => expect(screen).toHavePathname(`/question/${SQUASH_RUN}`));
    // Standing on the fifth question, not the first: age is not an input anywhere, and
    // the transcript is the server's.
    expect(await screen.findByText('Question 5')).toBeTruthy();
  });

  it('opens one run however many times the retry is pressed', async () => {
    // The door was one tap; a failed start puts a *Try again* in front of her, and two
    // presses inside one tick must not open two runs. The server's own idempotency would
    // hand both the same run, and the two navigations would then race over it.
    await tapAnUnratedChip('noRunYet');
    transport.on('POST', '/api/v1/assessments', networkFailure());

    fireEvent.press(await screen.findByLabelText('Take the Squash questions'));
    const retry = await screen.findByLabelText('Try again');

    stubStart(SQUASH_RUN);
    fireEvent.press(retry);
    fireEvent.press(retry);

    await waitFor(() => expect(screen).toHavePathname(`/question/${SQUASH_RUN}`));
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toHaveLength(2);
  });

  it('turns away a link that names nothing this build can rate', async () => {
    // The door's param is untrusted input and becomes a request body. A link that does
    // not survive validation lands on welcome — never on a run for a sport nobody asked
    // for, which is what a default would quietly start.
    stubGateWith(transport, { ratings: [PADEL_RATING] });

    await launchSignedIn('/rate/quidditch');

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toEqual([]);
  });

  it('turns away the one chip that is not a sport', async () => {
    // `all` is a filter, not a sport, and the server composes no door under it — so a
    // link naming it is the same class of thing as a misspelling.
    stubGateWith(transport, { ratings: [PADEL_RATING] });

    await launchSignedIn('/rate/all');

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toEqual([]);
  });

  it('lands back on Now, filtered to the new sport, and passes no closing screens', async () => {
    await tapAnUnratedChip('noRunYet');
    stubStart(SQUASH_RUN);

    fireEvent.press(await screen.findByLabelText('Take the Squash questions'));
    await waitFor(() => expect(screen).toHavePathname(`/question/${SQUASH_RUN}`));

    stubTheLastAnswer();

    fireEvent.press(await screen.findByLabelText('Usually'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));

    // `result → editor → back`, and the editor does not exist yet (`Raketa02/Raketa#105`).
    await waitFor(() => expect(screen).toHavePathname(`/result/${SQUASH_RUN}`));

    // The control says where it goes. *See your ratings* on a button that lands on the
    // home screen would be the app naming one destination and taking another.
    fireEvent.press(await screen.findByLabelText('See what’s on'));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByText(ON_NOW)).toBeTruthy();

    // Filtered to the sport she just took up. Asserted as the chip she can see rather
    // than as a second request: `ADR-0054` gives Now four occasions to ask and coming
    // back to a screen it already holds is none of them.
    expect(screen.getByRole('radio', { name: 'Squash', selected: true })).toBeTruthy();
    expect(screen.queryByRole('radio', { name: 'All', selected: true })).toBeNull();
  });

  it('decides that filter from the walk rather than from what the chip happened to hold', async () => {
    // The same landing, with the chip put back to `all` while she was answering.
    //
    // Without this the claim above is satisfied by an accident: Now unmounts when she
    // leaves it, so nothing can move the selection while she is in the questionnaire, and
    // the chip she tapped is simply still there. That makes *lands filtered to the new
    // sport* a property of who happens to be mounted rather than of the walk — true today
    // and quietly false the day anything else touches the selection.
    await tapAnUnratedChip('noRunYet');
    stubStart(SQUASH_RUN);

    fireEvent.press(await screen.findByLabelText('Take the Squash questions'));
    await waitFor(() => expect(screen).toHavePathname(`/question/${SQUASH_RUN}`));

    stubTheLastAnswer();
    fireEvent.press(await screen.findByLabelText('Usually'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));
    await waitFor(() => expect(screen).toHavePathname(`/result/${SQUASH_RUN}`));

    selectSportFilter(DEFAULT_SPORT_FILTER);
    fireEvent.press(await screen.findByLabelText('See what’s on'));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByText(ON_NOW)).toBeTruthy();
    expect(screen.getByRole('radio', { name: 'Squash', selected: true })).toBeTruthy();

    // And never through the account of a walk: one sport picked up from the home screen
    // is not one, so neither closing screen is passed.
    expect(screen.queryByText('These are hypotheses, not verdicts')).toBeNull();
  });
});

describe('a run in progress no longer takes the screen', () => {
  it('parks it for a player who already holds a rating', async () => {
    // `ADR-0084`: four squash questions answered on a tram must never stand between her
    // and the padel match she has paid for.
    stubGateWith(transport, {
      ratings: [PADEL_RATING],
      runs: [runInProgress('TENNIS', TENNIS_RUN)],
    });
    stubNow(transport);

    await launchSignedIn();

    expect(await screen.findByText(ON_NOW)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('takes the screen for a player holding no rating at all', async () => {
    stubGateWith(transport, { runs: [runInProgress('TENNIS', TENNIS_RUN)] });
    transport.on('GET', stepPath(TENNIS_RUN), () => json(outstanding(TENNIS_RUN)));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/question/${TENNIS_RUN}`));
  });
});

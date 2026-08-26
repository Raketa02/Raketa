/**
 * Onboarding, driven through the real route tree and the network boundary.
 *
 * Only `fetch` is faked. The router, the http client, its timeouts, error mapping, the
 * mappers, the use-cases, the hooks, the store and the screens all run for real — so a
 * pass here means the flow works end to end minus the socket.
 *
 * The gate's outcomes are routing behaviour, so they are asserted as routing: which screen
 * a launch lands on. These tests live outside `src/app/` and import the route files, per
 * docs/architecture.md Part 16.
 *
 * Every assertion is about what a player can see or what left the device. None reads a
 * store's internals or a hook's return shape.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import {
  clearStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { refreshTokens } from '@/features/auth/types';
import {
  ONBOARDING_ROUTES,
  RUNS_IN_PROGRESS_PATH,
  SPORTS_SERVED,
  launchSignedIn,
  runInProgress,
  stubGate as stubGateWith,
  stubRunsInProgress,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  transcriptOf,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { onboardingKeys } from '../hooks/onboardingKeys';
import { useOnboardingPass } from '../store/onboardingPass.store';

const ASSESSMENT_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';

const RATING: Wire['RatingResponse'] = {
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

const OPENING_STEP: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 0,
  transcript: transcriptOf(0),
  question: {
    id: 'q-played',
    category: 'Recent activity',
    tier: null,
    situation: 'Before anything else',
    text: 'Have you played padel before?',
    qualifier: 'Any level counts',
    options: [
      { id: 'never', text: 'Never played' },
      { id: 'some', text: 'A few times' },
    ],
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
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
});

// ---------------------------------------------------------------------------
// The entry gate — every outcome
// ---------------------------------------------------------------------------

describe('where a launch lands', () => {
  it('sends a signed-out player to sign in', async () => {
    setSessionStatus('unauthenticated');

    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/' });

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    // The gate's reads are authenticated, and firing them without a session would only
    // ever produce a 401 for the rotation to chase.
    expect(transport.requests).toHaveLength(0);
  });

  it('sends a signed-in player with no ratings into onboarding', async () => {
    stubGate();

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(screen.getByText("Let's find your level")).toBeTruthy();
  });

  it('sends a player with a rating and a Player profile into the app', async () => {
    stubGate({ ratings: [RATING], hasPlayerProfile: true });

    await launchSignedIn();

    // A player who finished onboarding lands here on every later launch. **Both** facts are
    // what the gate reads now: a rating says the first part is behind them, and a committed
    // Player profile says the second one is — so this is also the proof that neither part
    // is re-offered to someone who has already been through it.
    expect(await screen.findByText('Inside the app')).toBeTruthy();
    expect(screen.getByText('ada · ada@example.com')).toBeTruthy();
    expect(screen).toHavePathname('/');
    // Not through onboarding, and not through the questionnaire it would have started.
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toEqual([]);
  });

  it('sends a registered player who has not been rated yet into onboarding', async () => {
    // The other half of the same rule, and the case that makes it worth stating: signing
    // up and closing the app leaves a player with an account and no rating, so the next
    // launch owes them the questionnaire rather than the app.
    stubGate({ ratings: [] });

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(screen.queryByText('Inside the app')).toBeNull();
    // And **not** into the second part, which this player has no rating to have earned.
    // They have no Player profile either, so the two branches are both live here and the
    // order between them is what decides — ratings first, always.
    expect(screen).not.toHavePathname('/tags');
  });

  it('sends a rated player with no Player profile into the social steps', async () => {
    // The hole ADR-0090 closes, as routing. This player rated padel, reached the social
    // steps and closed the app: they hold a rating, so the gate used to drop them into the
    // app past the second part, permanently and with no route back to it.
    stubGate({ ratings: [RATING], hasPlayerProfile: false });

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/tags'));
    expect(screen.getByText('Setting up · Step 1 of 6')).toBeTruthy();
    // The first step, never the one they were on. The draft is client-held and died with
    // the process, so there is no middle of the part to be resumed to.
    expect(screen.queryByText('Inside the app')).toBeNull();
  });

  it('resumes an unfinished run ahead of the social steps, not after them', async () => {
    // Both of the later branches would answer for this player — they hold a rating and no
    // profile — and neither may. Answers already given are never stranded behind a screen
    // asking about something else.
    stubGate({
      ratings: [RATING],
      hasPlayerProfile: false,
      runs: [runInProgress('TENNIS', ASSESSMENT_ID)],
    });
    transport.on('GET', `/api/v1/assessments/${ASSESSMENT_ID}`, () => json(OPENING_STEP));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
    expect(await screen.findByText('Recent activity')).toBeTruthy();
  });

  it('enters the app on finishing, not back into onboarding off a stale gate read', async () => {
    // The launch that cached the answer "no ratings". It is correct at the time, it is
    // fresh for 30s, and it stays in the cache for five minutes — while the player spends
    // several of those minutes actually doing the questionnaire.
    // The profile is committed, which takes the second part out of this test's way: what is
    // being pinned here is the *ratings* read going stale, and a gate that answered
    // `social-steps` would prove it by accident, from the other branch.
    stubGate({ hasPlayerProfile: true });

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/welcome'));

    // The run finishes: the server now holds a rating, and completion marks the gate's two
    // reads stale — which is all it can do, because the gate's queries are unmounted for
    // the whole of onboarding and an invalidated query with no observers does not refetch.
    //
    // The re-read is **held open**, which is the whole point. On a phone it takes a round
    // trip, and the question is what the gate does in the meantime: the stale copy still
    // says "no ratings", and acting on it redirects into `(onboarding)` — which unmounts
    // this layout and its queries, so the corrected answer never arrives and the player is
    // left in the questionnaire for good. A test that lets the redirect happen and then
    // waits for it to be undone proves nothing, because on a device it is not undone.
    let answerRatings = () => {};
    const held = new Promise<void>((resolve) => {
      answerRatings = resolve;
    });
    transport.on('GET', '/api/v1/ratings', async () => {
      await held;
      return json<Wire['RatingsResponse']>({ ratings: [RATING] });
    });
    stubRunsInProgress(transport, []);
    queryClient.invalidateQueries({ queryKey: onboardingKeys.runInProgress() });
    queryClient.invalidateQueries({ queryKey: onboardingKeys.ratings() });

    // "Start playing".
    router.replace('/');

    // While the re-read is in flight the gate has no answer, and rendering nothing is the
    // only honest thing to do with a question it cannot yet answer.
    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/ratings')).toHaveLength(2));
    expect(screen).not.toHavePathname('/welcome');
    expect(screen.queryByText("Let's find your level")).toBeNull();

    answerRatings();

    expect(await screen.findByText('Inside the app')).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('resumes an assessment that was left unfinished', async () => {
    stubGate({ runs: [runInProgress('TENNIS', ASSESSMENT_ID)] });
    transport.on('GET', `/api/v1/assessments/${ASSESSMENT_ID}`, () => json(OPENING_STEP));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
    // The category is the heading, and the sport comes back with it — a resumed run has
    // no queue, because the queue was never persisted.
    expect(await screen.findByText('Recent activity')).toBeTruthy();
    expect(screen.getByText('Tennis · Rating 1 of 1')).toBeTruthy();
  });

  it('asks whether any run is unfinished with one request, not one per sport', async () => {
    stubGate();

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    // The whole point of the collection form. Four requests on every cold launch, for an
    // answer that is almost always "no", is what this replaced — so the count is the
    // assertion, and asserting the *route* as well is what stops a fan-out reappearing
    // under per-sport paths that this count would never see.
    expect(transport.requestsTo('GET', RUNS_IN_PROGRESS_PATH)).toHaveLength(1);
    expect(
      transport.requests.filter((request) => request.path.startsWith(RUNS_IN_PROGRESS_PATH)),
    ).toHaveLength(1);
  });

  it('resumes the first run in registry order when two sports are unfinished', async () => {
    const tennisRun = 'b7c8d9e0-1f2a-4b3c-8d4e-5f6a7b8c9d0e';
    // Registry order — padel, tennis, squash, badminton — which is the order the server
    // sends them in, and the order today's fan-out resolved ties by. Padel is first, so
    // padel is what a player with both unfinished goes back to.
    stubGate({
      runs: [runInProgress('PADEL', ASSESSMENT_ID), runInProgress('TENNIS', tennisRun)],
    });
    transport.on('GET', `/api/v1/assessments/${ASSESSMENT_ID}`, () => json(OPENING_STEP));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
    expect(await screen.findByText('Padel · Rating 1 of 1')).toBeTruthy();
    // And the run it did not route to is not read: the gate picks one, and only that one
    // is re-read for its outstanding question.
    expect(transport.requestsTo('GET', `/api/v1/assessments/${tennisRun}`)).toEqual([]);
  });

  it('says so rather than guessing, when the collection read answers the wrong shape', async () => {
    stubGate();
    // The route answers two shapes off one path, chosen by a parameter this call omits.
    // A step arriving here is the route answering a question the gate did not ask, and
    // reading it as an empty collection would send a player with an unfinished run past
    // the gate — silently, and only for the player it hurts.
    transport.on('GET', RUNS_IN_PROGRESS_PATH, () => json(OPENING_STEP));

    await launchSignedIn();

    expect(await screen.findByText("We couldn't pick up where you left off")).toBeTruthy();
    expect(screen).not.toHavePathname('/welcome');
  });

  it('asks both gate questions at once rather than one after the other', async () => {
    stubGate();

    // Hold the ratings answer open. If the two reads were sequenced, nothing else would
    // reach the socket until it came back — so the second read arriving *while this is
    // still in flight* is the proof, and counting requests after both finished would
    // prove nothing.
    let answerRatings = () => {};
    const held = new Promise<void>((resolve) => {
      answerRatings = resolve;
    });
    transport.on('GET', '/api/v1/ratings', async () => {
      await held;
      return json<Wire['RatingsResponse']>({ ratings: [] });
    });

    await launchSignedIn();

    await waitFor(() => expect(transport.requestsTo('GET', RUNS_IN_PROGRESS_PATH)).toHaveLength(1));

    answerRatings();
    await waitFor(() => expect(screen).toHavePathname('/welcome'));
  });

  it('says so, and offers a retry, when the gate cannot be read', async () => {
    // A terminal failure rather than a dropped connection: a dropped connection is
    // retried automatically with backoff, and this test is about the gate's behaviour
    // rather than the retry policy's timing.
    stubGate();
    transport.on('GET', '/api/v1/ratings', () => errorResponse(403, 'forbidden'));

    await launchSignedIn();

    expect(await screen.findByText("We couldn't pick up where you left off")).toBeTruthy();
    // No guess in either direction: sending an unrated player into the app skips
    // onboarding, and sending a rated one into onboarding re-rates them.
    expect(screen).not.toHavePathname('/welcome');

    stubGate();
    fireEvent.press(screen.getByLabelText('Try again'));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
  });

  it('sends the player to sign in when the gate 401s and the refresh is rejected', async () => {
    // Coming back to the app after long enough that the access token expired and the
    // refresh token is spent. The session really is over, and "your session has ended"
    // behind a Try again button is the one thing a retry cannot fix — every press
    // re-reads with credentials that no longer exist.
    stubGate();
    transport.on('GET', '/api/v1/ratings', () => errorResponse(401, 'unauthorized'));
    transport.on('GET', RUNS_IN_PROGRESS_PATH, () => errorResponse(401, 'unauthorized'));
    transport.on('POST', '/api/v1/auth/refresh', () => errorResponse(401, 'invalid_refresh_token'));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(screen.queryByText("We couldn't pick up where you left off")).toBeNull();
  });

  it('sends the player to sign in when the gate is refused and there is no credential to rotate', async () => {
    // The state a half-finished teardown used to leave: the keychain empty while the
    // session machine still said `authenticated`. Every gate read then goes out with no
    // Authorization header and is refused — and a 401 about no credential is one the
    // rotation cannot classify, so nothing rotates and nothing ends.
    //
    // What the player saw was "your session has ended" above a Try again button, on a
    // screen whose retry re-sent the same headerless request. The recovery is not a
    // retry; it is admitting the session is over.
    stubGate();
    transport.on('GET', '/api/v1/ratings', () => errorResponse(401, 'unauthorized'));
    transport.on('GET', RUNS_IN_PROGRESS_PATH, () => errorResponse(401, 'unauthorized'));

    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/' });
    setSessionStatus('authenticated');

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(screen.queryByText("We couldn't pick up where you left off")).toBeNull();
    // Nothing was rotated, because there was nothing to rotate it with.
    expect(transport.requestsTo('POST', '/api/v1/auth/refresh')).toEqual([]);
  });

  it('says the connection is out rather than rendering nothing, when launched offline', async () => {
    stubGate();
    // `networkMode: 'online'` *pauses* a query instead of failing it, so the gate's two
    // reads never resolve and never error. Without a branch for that, the app renders a
    // blank screen for as long as the connection stays dead.
    onlineManager.setOnline(false);

    await launchSignedIn();

    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(transport.requests).toHaveLength(0);

    onlineManager.setOnline(true);

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
  });
});

// ---------------------------------------------------------------------------
// Welcome, the picker, and the first question
// ---------------------------------------------------------------------------

describe('walking into the questionnaire', () => {
  async function reachThePicker() {
    stubGate();
    transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/welcome'));

    fireEvent.press(screen.getByLabelText('Get started'));
    await waitFor(() => expect(screen).toHavePathname('/sports'));
  }

  it('sets expectations before the first question, in two cards and no more', async () => {
    stubGate();
    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/welcome'));

    expect(screen.getByText('You get a starting level for each sport')).toBeTruthy();
    expect(screen.getByText('It takes about a minute per sport')).toBeTruthy();

    // *Nothing here is permanent* and the note about answering for a normal match were both
    // true and both cut: this screen's job is to get a player into the questionnaire, and
    // the result screen says what a starting estimate is worth at the moment there is one to
    // say it about.
    expect(screen.queryByText('Nothing here is permanent')).toBeNull();
    expect(screen.queryByText(/not your best day/)).toBeNull();
  });

  it('counts the sports chosen on the control that continues', async () => {
    await reachThePicker();

    expect(await screen.findByLabelText('Padel')).toBeTruthy();
    expect(screen.getByLabelText('Choose a sport to continue')).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Padel'));
    expect(screen.getByLabelText('Rate 1 sport')).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Tennis'));
    expect(screen.getByLabelText('Rate 2 sports')).toBeTruthy();

    // Tapping a chosen sport again removes it, and the count follows.
    fireEvent.press(screen.getByLabelText('Tennis'));
    expect(screen.getByLabelText('Rate 1 sport')).toBeTruthy();
  });

  it('says which sports are selected in words, not only by their border', async () => {
    await reachThePicker();

    expect(await screen.findByLabelText('Padel')).toBeTruthy();
    expect(screen.queryByText('Selected')).toBeNull();

    fireEvent.press(screen.getByLabelText('Padel'));

    expect(screen.getByText('Selected')).toBeTruthy();
    // And as state to a screen reader, which is the half a border cannot carry.
    expect(screen.getByRole('button', { name: 'Padel', selected: true })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Tennis', selected: true })).toBeNull();
  });

  it('starts the first chosen sport and lands on its opening question', async () => {
    await reachThePicker();

    transport.on('POST', '/api/v1/assessments', () => json(OPENING_STEP, 201));

    expect(await screen.findByLabelText('Tennis')).toBeTruthy();
    // Chosen second, so tennis is second in the queue — order is the only thing the
    // selection carries.
    fireEvent.press(screen.getByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Tennis'));
    fireEvent.press(screen.getByLabelText('Rate 2 sports'));

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));

    const [started] = transport.requestsTo('POST', '/api/v1/assessments');
    expect(started?.body).toEqual({ sport: 'PADEL' });

    expect(await screen.findByText('Recent activity')).toBeTruthy();
    // Which sport of how many, in the eyebrow and nowhere else: the indicator under the
    // header measures the run's questions now, not the pass's sports (ADR-0020), and a
    // filled rectangle was never readable at any font size anyway.
    expect(screen.getByText('Padel · Rating 1 of 2')).toBeTruthy();

    // The response *is* the next question, so it is written into the cache rather than
    // asked for a second time.
    expect(transport.requestsTo('GET', `/api/v1/assessments/${ASSESSMENT_ID}`)).toEqual([]);
  });

  it('sends one start, however many times the control is pressed', async () => {
    await reachThePicker();

    // Held open, so the second press lands while the first is still in flight.
    let answer = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('POST', '/api/v1/assessments', async () => {
      await held;
      return json(OPENING_STEP, 201);
    });

    expect(await screen.findByLabelText('Padel')).toBeTruthy();
    fireEvent.press(screen.getByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Rate 1 sport'));

    await waitFor(() =>
      expect(transport.requestsTo('POST', '/api/v1/assessments')).toHaveLength(1),
    );
    fireEvent.press(screen.getByLabelText('Starting…'));

    answer();
    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));

    // The blocked button is **UX, not correctness**, and the correctness now exists
    // behind it: `POST /assessments` guards on an unfinished run, and the assessment's
    // stream id is derived from (player, sport, attempt) so two starts that both read
    // before either appends collide on one stream instead of stranding a second run.
    expect(transport.requestsTo('POST', '/api/v1/assessments')).toHaveLength(1);
  });

  it('never writes the sport selection to the server', async () => {
    await reachThePicker();

    expect(await screen.findByLabelText('Squash')).toBeTruthy();
    fireEvent.press(screen.getByLabelText('Squash'));
    fireEvent.press(screen.getByLabelText('Badminton'));

    // The queue orders the next few assessments and is nothing else. Choosing sports is
    // not a write, and there is no endpoint it could be one against.
    const writes = transport.requests.filter((request) => request.method !== 'GET');
    expect(writes).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Links into the middle of onboarding
// ---------------------------------------------------------------------------

/** Well-formed, and pointing at a run this player has no business being handed. */
const STRANGE_LINK_ID = 'e5f6a7b8-9c0d-4e1f-8a2b-3c4d5e6f7a8b';

describe('a link into the middle of onboarding', () => {
  // Onboarding happens once, at the beginning, and there is no re-take from inside the
  // app. So surviving param validation is not the same as belonging here: a well-formed
  // link naming a sport this player never chose is not a shortcut into a flow already
  // under way, and drawing it a questionnaire meant drawing progress with no denominator.
  it('sends a question link for a sport this player never chose back to the beginning', async () => {
    stubGate();
    // A pass is running over padel — the player is mid-onboarding — and the link names
    // squash.
    useOnboardingPass.getState().begin(['padel']);

    await launchSignedIn(`/question/${STRANGE_LINK_ID}?sport=squash`);

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    // Turned away before anything was asked of the server, rather than after a request
    // whose answer would have been rendered into a screen with nothing honest to show.
    expect(transport.requestsTo('GET', `/api/v1/assessments/${STRANGE_LINK_ID}`)).toEqual([]);
  });

  it('sends a result link for a sport this player never chose back to the beginning', async () => {
    // A result is a screen inside onboarding, so it carries the same rule for the same
    // reason — it belongs at the beginning, not at somebody's rating.
    stubGate();
    useOnboardingPass.getState().begin(['padel']);

    await launchSignedIn(`/result/${STRANGE_LINK_ID}?sport=squash`);

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('GET', `/api/v1/assessments/${STRANGE_LINK_ID}`)).toEqual([]);
  });

  it('welcomes back to the beginning rather than through the gate, so a real run cannot loop', async () => {
    // The trap this avoids: the gate answers *resume* for an outstanding run, so sending
    // a turned-away player through `/` would redirect them straight back to the question
    // that turned them away. Welcome is a screen, and the picker hands the run back
    // anyway — starting a sport with an unfinished run returns that run.
    stubGate({ runs: [runInProgress('SQUASH', STRANGE_LINK_ID)] });
    useOnboardingPass.getState().begin(['padel']);

    await launchSignedIn(`/question/${STRANGE_LINK_ID}?sport=squash`);

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    // Still there a beat later: not bouncing between the gate and the question.
    expect(await screen.findByLabelText('Get started')).toBeTruthy();
    expect(screen).toHavePathname('/welcome');
  });

  it('still admits a run resumed with no pass, which is the gate doing its job', async () => {
    // The other side of the same rule, and the one that must not regress: the gate
    // redirects to an outstanding question with no picker in between, and that run is a
    // genuine pass of one sport.
    stubGate({ runs: [runInProgress('TENNIS', ASSESSMENT_ID)] });
    transport.on('GET', `/api/v1/assessments/${ASSESSMENT_ID}`, () => json(OPENING_STEP));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
    expect(await screen.findByText('Tennis · Rating 1 of 1')).toBeTruthy();
  });
});

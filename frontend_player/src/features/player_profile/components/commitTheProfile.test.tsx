/**
 * The end of onboarding: the six steps, the one write that ends them, and the app.
 *
 * Driven through the real route tree with only the socket faked, like every other flow suite
 * here — the router, the http client, the mappers, the use case, the hooks, the draft and the
 * screens all run for real. What is being proved is the **part as a unit**: a player arrives
 * from the last result, answers six screens, changes their mind and finds their answers where
 * they left them, presses finish once, and every one of those answers reaches the server in a
 * single request that cannot be made twice.
 *
 * The walk itself — the order of the six, the back control, the draft surviving a round trip
 * — is `socialSteps.test.tsx`. This one is about the commit: what is in the body, what the
 * key protects, what a failure leaves behind, and where the player ends up.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  SPORTS_SERVED,
  launchSignedIn,
  resetLocation,
  stubGate as stubGateWith,
  stubLocation,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { fakeLocation } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  neverResponds,
  transcriptOf,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useProfileDraft } from '../store/profileDraft.store';

import { OPT_IN_ANSWERS, OPT_IN_FINISH_LABEL } from './optInPresentation';

const COMMIT_PATH = '/api/v1/players/me/profile';
const PADEL_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';

/** One rating: the first part is behind this player, and the second one is not. */
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

/**
 * The fix the phone gives, and the area it is rounded to before anything holds it.
 *
 * Two decimal places is the coarsening `locationArea` applies the moment a fix is read, and
 * it is the pair the body below is expected to carry — the metres never reach the draft, so
 * they can never reach the wire.
 */
const FIX = { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 };
const AREA = { latitude: 41.39, longitude: 2.17 };

const YES = OPT_IN_ANSWERS.find((answer) => answer.accepted)?.label ?? '';

/** What the commit answers with. Nothing in the app reads it; the status is what differs. */
const PROFILE: Wire['PlayerProfileResponse'] = {
  player_id: '11111111-2222-4333-8444-555555555555',
  social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
  photo_ids: [],
  availability: [{ day: 3, part: 'EVENING' }],
  location: AREA,
  search_radius_km: 10,
  proposals_opt_in: {
    accepted: true,
    copy_version: 'proposals-opt-in.v2',
    surface: 'ONBOARDING',
    answered_at: '2026-08-25T10:00:00Z',
  },
  created_at: '2026-08-25T10:00:00Z',
  updated_at: '2026-08-25T10:00:00Z',
};

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

const commits = () => transport.requestsTo('POST', COMMIT_PATH);
const keysSent = () => commits().map((request) => request.headers['Idempotency-Key']);
const bodyOf = (request: RecordedRequest | undefined) =>
  request?.body as Wire['CommitPlayerProfileRequest'] | undefined;

/**
 * The commit route, answering the way the real one does.
 *
 * **201 the first time a key arrives and 200 for every repeat of it**, with the same body
 * either way — which is the whole of what makes a double tap and a retry safe. The keys it
 * has already served are kept here rather than counted, because *this exact request again*
 * and *a second commit* are different things and only the key can tell them apart.
 *
 * It also re-stubs the gate, because that is what the server would now say: this player has
 * a Player profile. Without it the next launch — and the gate on the way into the app —
 * would read a `GET /users/me` from before the commit and send the player back into the
 * steps they just finished.
 */
function stubCommit() {
  transport.on('POST', COMMIT_PATH, (request) => {
    const key = request.headers['Idempotency-Key'] ?? '';
    const replay = keysCommitted.has(key);
    keysCommitted.add(key);
    stubGate({ ratings: [RATING], hasPlayerProfile: true });
    return json(PROFILE, replay ? 200 : 201);
  });
}

/**
 * **Every key this fake server has created a profile under.** One entry is one profile.
 *
 * Kept across re-stubs, so a suite that swaps the responder mid-test — a failure, then a
 * retry — still counts what the server as a whole did rather than what the last responder
 * saw. Cleared per test in `beforeEach`.
 */
let keysCommitted: Set<string>;

/** A launch by a player the gate owes the second part to, landing on its first step. */
async function enterTheSocialSteps() {
  stubGate({ ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);
  stubLocation(fakeLocation({ fix: FIX }));
  stubCommit();

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/tags'));
}

/** Two tags at the floor, which is the only step of the six that insists on an answer. */
async function answerTheTags() {
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/photos'));
}

/**
 * From the photos step to the last one, answering each screen the way that screen wants.
 *
 * No photo, because this walk adds none and none is a complete answer. One cell of the week,
 * because a blank one is an answer too and a body carrying an empty list proves less than
 * one carrying the cell that was actually ticked. The area from the device. The radius left
 * at the served default, which is an answer the step wrote when it opened.
 */
async function walkOnToTheLastStep() {
  fireEvent.press(screen.getByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/availability'));

  fireEvent.press(screen.getByLabelText('Wednesday evening'));
  fireEvent.press(screen.getByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/location'));

  fireEvent.press(screen.getByLabelText('Use my location'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/radius'));

  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/opt-in'));
}

/** The whole part, answered and standing on the finish with it open. */
async function reachTheFinish() {
  await enterTheSocialSteps();
  await answerTheTags();
  await walkOnToTheLastStep();
  fireEvent.press(screen.getByLabelText(YES));
}

const finish = () => screen.getByLabelText(OPT_IN_FINISH_LABEL);

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  keysCommitted = new Set();
  // What killing the app does. The draft is in memory and never persisted, so every test
  // here starts the part with nothing in it.
  useProfileDraft.getState().reset();
});

afterEach(() => {
  transport.restore();
  resetLocation();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// The one request
// ---------------------------------------------------------------------------

describe('finishing the part', () => {
  it('sends every answer from all six steps in one request', async () => {
    await reachTheFinish();

    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    // One write, not six. A partial commit — the tags saved and the consent lost — is the
    // worst outcome this part has available to it, which is why the whole of it is one body.
    expect(bodyOf(commits()[0])).toEqual({
      social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
      // No photo is a complete answer, sent as itself rather than left out for the server
      // to default — the same value arrived at by two routes, one of them a guess.
      photo_ids: [],
      availability: [{ day: 3, part: 'EVENING' }],
      // The area, not the fix. The metres the device reported were discarded on the way in
      // and there is nothing above `locationArea` that ever held them.
      location: AREA,
      // The served default, written into the draft when the step opened — so a screen the
      // player walked straight past is still a screen they answered.
      search_radius_km: 10,
      proposals_opt_in: { accepted: true, copy_version: 'proposals-opt-in.v2' },
    });
  });

  it('sends the opt-in with the copy version the player was shown', async () => {
    // The evidence half of the answer. Consent gathered against one sentence is not consent
    // to a different one, so a record that cannot name its words evidences nothing.
    await reachTheFinish();

    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    expect(bodyOf(commits()[0])?.proposals_opt_in.copy_version).toBe('proposals-opt-in.v2');
  });

  it('sends a declined opt-in as a recorded no, and finishes just the same', async () => {
    // No is a whole answer, and it must reach the server as one. Sending nothing, or sending
    // the player to a different ending, would be the product treating a refusal as a failure.
    await enterTheSocialSteps();
    await answerTheTags();
    await walkOnToTheLastStep();
    fireEvent.press(screen.getByLabelText(OPT_IN_ANSWERS.find((a) => !a.accepted)?.label ?? ''));

    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    expect(bodyOf(commits()[0])?.proposals_opt_in).toEqual({
      accepted: false,
      copy_version: 'proposals-opt-in.v2',
    });
    // The data screen, not the summary: a player reaches the second part *from* the
    // summary now, so landing back on it would show the same account of the same walk
    // twice — the second time after six questions that had nothing to do with it.
    await waitFor(() => expect(screen).toHavePathname('/data'));
  });

  it('says it is finishing rather than announcing itself disabled, while it is in flight', async () => {
    // A busy button is not a disabled button (design-system 6.1). A request going out is not
    // a part that is short of an answer, and a control that announced *choose yes or no
    // above to finish* while the answer was already on its way would be describing a screen
    // that does not exist.
    await reachTheFinish();
    transport.on('POST', COMMIT_PATH, neverResponds());

    fireEvent.press(finish());

    const control = await screen.findByLabelText('Finishing…');
    expect(control.props.accessibilityState).toMatchObject({ busy: true });
    expect(control.props.accessibilityHint).toBe(
      'Sends everything you answered and finishes setting up',
    );
  });

  it('carries an idempotency key', async () => {
    await reachTheFinish();

    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    // The header the route requires. Its shape is the contract's — 1 to 128 characters — and
    // a key the endpoint refuses is a commit that never lands.
    const key = keysSent()[0] ?? '';
    expect(key.length).toBeGreaterThan(0);
    expect(key.length).toBeLessThanOrEqual(128);
  });

  it('sends what the player changed their mind about, not what they first said', async () => {
    // The whole reason the draft exists, proved where it matters: an answer corrected on the
    // way back has to be the one that reaches the server.
    await reachTheFinish();

    fireEvent.press(screen.getByLabelText('Back to How far should we look for players?'));
    await waitFor(() => expect(screen).toHavePathname('/radius'));
    // One served step further out, through the control a player who cannot drag uses.
    fireEvent(await screen.findByLabelText('How far to look'), 'accessibilityAction', {
      nativeEvent: { actionName: 'increment' },
    });
    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));

    // Still answered, still open: walking back cost nothing.
    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    expect(bodyOf(commits()[0])?.search_radius_km).toBe(11);
    expect(bodyOf(commits()[0])?.social_tag_ids).toEqual(['PLAYS_TO_WIN', 'HERE_TO_IMPROVE']);
  });
});

// ---------------------------------------------------------------------------
// A photo that has not landed yet
// ---------------------------------------------------------------------------

describe('a photo still on its way up when the player reaches the finish', () => {
  /**
   * One picked photo, still going up.
   *
   * **Put there through the store's own API rather than by holding the socket open**, and
   * the reason is the harness rather than the app: `expo-router/testing-library` installs
   * jest's fake timers and every `waitFor` runs the pending ones, so an upload that has not
   * answered by the next navigation is timed out by the app's own timeout policy. In
   * production an upload outlives the screen it was started from — that is the photos step's
   * whole design — so reaching step six with one still in flight is an ordinary thing to do
   * and an impossible thing to stage here.
   *
   * `changePhotos` is the same call the photos step makes, and it derives `photoIds` from
   * the workbench exactly as it does there — so what this arranges is a real state, and
   * every assertion below is about what a player sees.
   */
  function aPhotoIsStillArriving() {
    act(() => {
      useProfileDraft.getState().changePhotos(() => [
        {
          uri: 'file:///one.jpg',
          mimeType: 'image/jpeg',
          upload: { kind: 'uploading', progress: 0.4 },
        },
      ]);
    });
  }

  it('holds the finish shut, says why, and asks for nothing', async () => {
    await reachTheFinish();
    aPhotoIsStillArriving();

    // Answered, and still shut — on the one thing the player is not being asked to do
    // anything about. It resolves itself, so there is no control here at all.
    expect(finish().props.accessibilityState?.disabled).toBe(true);
    expect(finish().props.accessibilityHint).toBe('Waiting for a photo to finish uploading');
    expect(screen.getByText('One moment — a photo is still arriving')).toBeTruthy();
    expect(screen.queryByLabelText(/^Set /)).toBeNull();
    expect(commits()).toEqual([]);
  });

  it('opens it again the moment the photo lands, and sends the photo with it', async () => {
    // The body names photos by the ids the server gave back, so a commit sent while one was
    // in flight would quietly leave out a picture the player watched upload — which is the
    // partial commit this whole part is built to make impossible.
    await reachTheFinish();
    aPhotoIsStillArriving();

    act(() => {
      useProfileDraft
        .getState()
        .changePhotos((photos) =>
          photos.map((photo) => ({ ...photo, upload: { kind: 'uploaded', photoId: 'photo-1' } })),
        );
    });

    expect(finish().props.accessibilityState?.disabled).toBe(false);
    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    expect(bodyOf(commits()[0])?.photo_ids).toEqual(['photo-1']);
  });
});

// ---------------------------------------------------------------------------
// One profile, whatever the finger and the connection do
// ---------------------------------------------------------------------------

describe('a double tap on the finish', () => {
  it('produces one profile, because both presses are the same commit', async () => {
    await reachTheFinish();

    // Two presses before a render can block the second — which is the ordinary case on a
    // slow connection, not the exotic one. The disabled control is a courtesy and is always
    // one render behind the finger; the key is the defence.
    fireEvent.press(finish());
    fireEvent.press(finish());
    await waitFor(() => expect(screen).toHavePathname('/data'));

    // **Exactly one profile**, whatever reached the socket. Every request carried the same
    // key, so the server created one and answered the repeat with it; a key minted per press
    // would have created a second. The request count is deliberately not pinned — how many
    // presses beat the control's disabled state is a render-timing detail, and the whole
    // point is that it does not matter.
    expect(keysCommitted.size).toBe(1);
    expect(new Set(keysSent())).toHaveProperty('size', 1);
  });
});

// ---------------------------------------------------------------------------
// A commit that does not land
// ---------------------------------------------------------------------------

describe('a failed commit', () => {
  it('keeps the player on the step with the draft intact, and claims nothing', async () => {
    await reachTheFinish();
    transport.on('POST', COMMIT_PATH, networkFailure());

    fireEvent.press(finish());

    expect(
      await screen.findByText(/We couldn't reach Raketa. Check your connection and try again./),
    ).toBeTruthy();
    expect(screen.getByRole('alert')).toBeTruthy();
    // Nothing was lost, and the screen says so — the one question a player who just answered
    // six screens actually has.
    expect(screen.getByText(/Nothing you answered was lost/)).toBeTruthy();

    // Still here. The prototype navigated away unconditionally, which is exactly the
    // behaviour not to inherit: it would have told a player they were set up when nothing
    // had been written at all.
    expect(screen).toHavePathname('/opt-in');
    expect(screen.getByLabelText(YES).props.accessibilityState?.selected).toBe(true);
    expect(screen.queryByText(/Inside the app/)).toBeNull();

    // And the retry is the control that failed, open rather than stuck busy.
    expect(finish().props.accessibilityState?.disabled).toBe(false);
  });

  it('retries under the same key, so the retry cannot make a second profile', async () => {
    await reachTheFinish();
    transport.on('POST', COMMIT_PATH, networkFailure());
    fireEvent.press(finish());
    await screen.findByText(/Nothing you answered was lost/);

    stubCommit();
    fireEvent.press(finish());
    await waitFor(() => expect(screen).toHavePathname('/data'));

    // Two attempts, one key, one profile. The failed attempt may well have reached the
    // server and been recorded before the connection dropped; the retry replays it rather
    // than doubling it.
    expect(keysSent()).toHaveLength(2);
    expect(new Set(keysSent())).toHaveProperty('size', 1);
    expect(keysCommitted.size).toBe(1);
  });

  it('says what a refusal means without pretending it worked', async () => {
    // A 400 the client cannot fix by pressing again — a tag id this platform no longer
    // serves, say. It is still a failure that leaves the draft where it was, and it still
    // must not read as success.
    await reachTheFinish();
    transport.on('POST', COMMIT_PATH, () => errorResponse(400, 'unknown_social_tag'));

    fireEvent.press(finish());

    expect(await screen.findByText(/Check the details above and try again./)).toBeTruthy();
    expect(screen).toHavePathname('/opt-in');
    expect(commits()).toHaveLength(1);
  });

  it('asks for the week itself when the server refuses an empty one', async () => {
    // The step will not continue on a blank grid, and the commit refuses one anyway — a
    // disabled control is absent from a replayed request and from an older build. When the
    // refusal arrives, *try again* is the one sentence that is not true: the identical body
    // fails identically, so the screen names the answer and offers the step that takes it.
    await reachTheFinish();
    transport.on('POST', COMMIT_PATH, () => errorResponse(400, 'availability_grid_empty'));

    fireEvent.press(finish());

    expect(await screen.findByText(/One ticked slot of the twenty-one is enough/)).toBeTruthy();
    expect(screen.queryByText(/Try again — this can only ever set you up once/)).toBeNull();

    // And the way back, which is the half a player cannot do without.
    fireEvent.press(screen.getByLabelText('Set when you usually play'));
    await waitFor(() => expect(screen).toHavePathname('/availability'));
  });
});

// ---------------------------------------------------------------------------
// The other side of it
// ---------------------------------------------------------------------------

describe('once the commit has landed', () => {
  async function commitAndLeave() {
    await reachTheFinish();
    fireEvent.press(finish());
    // **The data screen, not the summary.** The ratings summary is the screen a player now
    // enters the second part *from*, so the commit lands one screen further on: what Raketa
    // keeps, and then the app.
    await waitFor(() => expect(screen).toHavePathname('/data'));
  }

  it('continues into what is kept, and then the app', async () => {
    await commitAndLeave();

    expect(screen.getByText('What we keep from setting up')).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Start playing'));
    expect(await screen.findByText('Inside the app')).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('offers no way back into the second part', async () => {
    await commitAndLeave();

    // Nothing behind the data screen: every move inside the part replaced, so there is no
    // history entry holding one of the six, and the part itself is over.
    expect(screen.queryByLabelText(/^Back to /)).toBeNull();

    fireEvent.press(screen.getByLabelText('Start playing'));

    expect(await screen.findByText('Inside the app')).toBeTruthy();
    // The gate's fourth branch is answered now, so the way it used to turn this player round
    // into the steps is closed.
    expect(screen).toHavePathname('/');
  });

  it('lands a relaunch in the app rather than back in the steps', async () => {
    await commitAndLeave();

    // The process dies with everything in it — the cache and the draft both. What is left
    // is what the server holds, which is a rating and a Player profile.
    screen.unmount();
    queryClient.clear();
    useProfileDraft.getState().reset();

    await launchSignedIn();

    expect(await screen.findByText('Inside the app')).toBeTruthy();
    expect(screen).toHavePathname('/');
    // And no second commit was made on the way: nothing about launching writes anything.
    expect(commits()).toHaveLength(1);
    expect(keysCommitted.size).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Where the part is entered from
// ---------------------------------------------------------------------------

describe('arriving from the last result', () => {
  const stepPath = (assessmentId: string) => `/api/v1/assessments/${assessmentId}`;

  const OUTSTANDING: Wire['AssessmentStepResponse'] = {
    assessment_id: PADEL_ID,
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

  const RESULT: Wire['ResultResponse'] = {
    mu: 2.71,
    sigma: 0.62,
    confidence: 30,
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

  const FINISHED: Wire['AssessmentStepResponse'] = {
    assessment_id: PADEL_ID,
    status: 'completed',
    questions_asked: RESULT.questions_asked,
    transcript: transcriptOf(RESULT.questions_asked),
    question: null,
    result: RESULT,
  };

  it('shows the ratings the walk produced, and only then the six steps', async () => {
    // The one walk that proves the order. A player is owed the number they just spent a
    // minute per sport producing **before** anything else is asked of them, so the result
    // leads to the summary, the summary is the door into the second part, and the commit at
    // the end of the six lands on what Raketa keeps.
    stubGate();
    stubProfileOptions(transport);
    stubLocation(fakeLocation({ fix: FIX }));
    stubCommit();
    transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
    transport.on('POST', '/api/v1/assessments', () => json(OUTSTANDING, 201));
    transport.on('POST', `${stepPath(PADEL_ID)}/answers`, () => {
      transport.on('GET', stepPath(PADEL_ID), () => json(FINISHED));
      stubGate({ ratings: [RATING], hasPlayerProfile: false });
      return json(FINISHED);
    });

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    fireEvent.press(screen.getByLabelText('Get started'));
    await waitFor(() => expect(screen).toHavePathname('/sports'));
    fireEvent.press(await screen.findByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Rate 1 sport'));

    await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_ID}`));
    fireEvent.press(await screen.findByLabelText('Usually'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));
    await waitFor(() => expect(screen).toHavePathname(`/result/${PADEL_ID}`));

    // The last sport leads to the summary, whatever else the player still owes.
    fireEvent.press(await screen.findByLabelText('See your ratings'));
    await waitFor(() => expect(screen).toHavePathname('/done'));

    // With the rating this walk produced on it — the account the player earned, given to
    // them at the moment they earned it rather than six screens later.
    expect(await screen.findByLabelText('Padel level: 2,71')).toBeTruthy();

    // And the summary is the door into the second part. The control says so, rather than
    // saying *Continue* to somebody about to answer six more questions.
    //
    // Awaited, because *does this player still owe a profile* is a read, and until it lands
    // the screen takes the fail-safe answer — *they are set up* — and offers the plain
    // continue. That default is the safe one either way: it leads to the data screen and
    // then to the gate, which turns a player who really is owed the part straight into it.
    fireEvent.press(await screen.findByLabelText('Finish setting up'));
    await waitFor(() => expect(screen).toHavePathname('/tags'));

    await answerTheTags();
    await walkOnToTheLastStep();
    fireEvent.press(screen.getByLabelText(YES));
    fireEvent.press(finish());

    // The commit lands on what is kept, not back on the summary they have already read.
    await waitFor(() => expect(screen).toHavePathname('/data'));
    expect(commits()).toHaveLength(1);
  });
});

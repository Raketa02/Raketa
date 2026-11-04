/**
 * The end of onboarding: the six steps, the one write that ends them, and the app.
 *
 * Driven through the real route tree with only the socket faked, like every other flow suite
 * here — the router, the http client, the mappers, the use case, the hooks, the draft and the
 * screens all run for real. What is being proved is the **part as a unit**: a player arrives
 * from the naming, answers six screens, changes their mind and finds their answers where they
 * left them, presses finish once on *Who you play with*, and every one of those answers reaches
 * the server in a single request that cannot be made twice — and lands on Home
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §1, #730). The
 * whole sign-up, in its eight screens, is `onboardingFlow.test`'s.
 *
 * **The finish is on *Who you play with*** ([#582](https://github.com/Raketa02/Raketa/issues/582)):
 * the radius and the proposals question left the part, so the step that asks who a player is
 * matched with is the last one, and it carries the finish the opt-in used to.
 *
 * The walk itself — the order of the six, the back control, the draft surviving a round
 * trip — is `socialSteps.test.tsx`. This one is about the commit: what is in the body, what
 * the key protects, what a failure leaves behind, and where the player ends up. The intro's
 * three refusals are here too, because they are the commit's: the line is fenced at the
 * write, and the write is this request.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  HOME_TAB_LINE,
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
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useProfileDraft } from '../store/profileDraft.store';

import { FINISH_LABEL } from './commitPresentation';
import { CHANGE_INTRO_LABEL, INTRO_FIELD_LABEL } from './introPresentation';

const COMMIT_PATH = '/api/v1/players/me/profile';

/** One rating — which the steps neither need nor read: a level is asked where play begins. */
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

/** What the commit answers with. Nothing in the app reads it; the status is what differs. */
const PROFILE: Wire['PlayerProfileResponse'] = {
  player_id: '11111111-2222-4333-8444-555555555555',
  social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
  photo_ids: [],
  weekly_hours: [{ day: 3, hour: 19 }],
  location: AREA,
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

/** Two tags at the floor — the first of the three steps that insist on an answer. */
async function answerTheTags() {
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/intro'));
}

/**
 * From the intro step to the last one, answering each screen on the way as that screen wants
 * it, and leaving the last one for the caller.
 *
 * No intro, unless the walk wrote one before calling this: *Next* on an empty box carries
 * nothing, which is the ordinary end of that step. No photo, because this walk adds none and
 * none is a complete answer. One cell of the week: the floor is one, and a body carrying the
 * cell that was actually ticked proves more than a count. The area from the device.
 */
async function walkOnToTheLastStep() {
  fireEvent.press(screen.getByLabelText('Next'));
  await waitFor(() => expect(screen).toHavePathname('/photos'));

  fireEvent.press(screen.getByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/availability'));

  fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
  fireEvent.press(screen.getByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/location'));

  fireEvent.press(screen.getByLabelText('Use my location'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/gender'));
}

/**
 * *Woman* on the last step, because that half of it has no default and the part cannot finish
 * without an answer. The preference beside it is left at its opening `Anyone`, which is what
 * every player holds until somebody narrows it.
 */
function answerAboutYou() {
  fireEvent.press(screen.getByLabelText('Woman'));
}

/** The whole part, answered and standing on the finish with it open. */
async function reachTheFinish() {
  await enterTheSocialSteps();
  await answerTheTags();
  await walkOnToTheLastStep();
  answerAboutYou();
}

const finish = () => screen.getByLabelText(FINISH_LABEL);

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

    // One write, not six. A partial commit — the tags saved and the week lost — is the worst
    // outcome this part has available to it, which is why the whole of it is one body.
    //
    // **No `intro` key at all.** This walk pressed *Next* on an empty box, and a player who
    // wrote nothing has no intro rather than an empty one — so the field is left out, never
    // sent as `''` or `null` for the server to read as the same answer by a second route.
    expect(bodyOf(commits()[0])).toEqual({
      social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
      // No photo is a complete answer, sent as itself rather than left out for the server
      // to default — the same value arrived at by two routes, one of them a guess.
      photo_ids: [],
      weekly_hours: [{ day: 3, hour: 19 }],
      // The area, not the fix. The metres the device reported were discarded on the way in
      // and there is nothing above `locationArea` that ever held them.
      location: AREA,
      // No radius and no proposals answer: neither is asked any more, and neither is sent.
      gender: 'WOMAN',
      // The widest preference, sent as itself for the reason the empty photo list is: the
      // field has a default on the wire, and an omission would land the same value by a
      // second route decided on the other side.
      gender_preference: 'ANY',
    });
  });

  it('sends the line the player wrote, trimmed, and leaves it out when they skipped', async () => {
    // Karol writes a line and continues; Ola taps Skip with one half-typed. Both reach the
    // same commit, and only one of them carries an intro — the other's box was cleared by
    // the skip, because *skip* means *no intro* and not *whatever was in the box*.
    await enterTheSocialSteps();
    await answerTheTags();
    fireEvent.changeText(
      screen.getByLabelText(INTRO_FIELD_LABEL),
      '  Moved from Wrocław in May. Needs opponents. ',
    );
    await walkOnToTheLastStep();
    answerAboutYou();

    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));
    expect(bodyOf(commits()[0])?.intro).toBe('Moved from Wrocław in May. Needs opponents.');

    // And the other player. A fresh part, a line started and then skipped.
    screen.unmount();
    queryClient.clear();
    useProfileDraft.getState().reset();
    keysCommitted = new Set();
    await enterTheSocialSteps();
    await answerTheTags();
    fireEvent.changeText(screen.getByLabelText(INTRO_FIELD_LABEL), 'Actually, never m');
    fireEvent.press(screen.getByLabelText('Skip'));
    await waitFor(() => expect(screen).toHavePathname('/photos'));

    // Walking back finds the box empty: what was skipped is gone, not merely unsent.
    fireEvent.press(screen.getByLabelText('Back to Say it in your own words'));
    await waitFor(() => expect(screen).toHavePathname('/intro'));
    expect(screen.getByLabelText(INTRO_FIELD_LABEL).props.value).toBe('');

    await walkOnToTheLastStep();
    answerAboutYou();
    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(2));
    expect(bodyOf(commits()[1])).not.toHaveProperty('intro');
  });

  it('holds the finish shut until the player answers about themselves', async () => {
    // The question on this very screen, and the one half of it with no default: `prefer not
    // to say` is a choice somebody makes, never one made for them. So the step's own hint
    // says what is missing, rather than one of the hints that send a player back.
    await enterTheSocialSteps();
    await answerTheTags();
    await walkOnToTheLastStep();

    expect(finish().props.accessibilityState?.disabled).toBe(true);
    expect(finish().props.accessibilityHint).toBe('Choose an answer about you to finish');
    expect(screen.queryByLabelText(/^Set /)).toBeNull();

    fireEvent.press(screen.getByLabelText('Man'));

    expect(finish().props.accessibilityState?.disabled).toBe(false);
  });

  it('sends prefer not to say as an answer, and finishes just the same', async () => {
    // A whole answer, and it must reach the server as one. Sending nothing, or sending the
    // player to a different ending, would be the product treating it as a refusal.
    await enterTheSocialSteps();
    await answerTheTags();
    await walkOnToTheLastStep();
    fireEvent.press(screen.getByLabelText('Prefer not to say'));

    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    expect(bodyOf(commits()[0])?.gender).toBe('PREFER_NOT_TO_SAY');
    // And on to Home, as any finish is.
    await waitFor(() => expect(screen).toHavePathname('/'));
  });

  it('says it is finishing rather than announcing itself disabled, while it is in flight', async () => {
    // A busy button is not a disabled button (design-system 6.1). A request going out is not
    // a part that is short of an answer, and a control that announced *choose an answer
    // about you to finish* while the answer was already on its way would be describing a
    // screen that does not exist.
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

    fireEvent.press(screen.getByLabelText('Back to Where do you play?'));
    await waitFor(() => expect(screen).toHavePathname('/location'));
    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/gender'));

    // Still answered after the round trip — and then changed, both halves of it.
    expect(screen.getByLabelText('Woman').props.accessibilityState?.selected).toBe(true);
    fireEvent.press(screen.getByLabelText('Man'));
    fireEvent.press(screen.getByLabelText('Men only'));

    fireEvent.press(finish());
    await waitFor(() => expect(commits()).toHaveLength(1));

    expect(bodyOf(commits()[0])?.gender).toBe('MAN');
    expect(bodyOf(commits()[0])?.gender_preference).toBe('MEN_ONLY');
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
   * whole design — so reaching the last step with one still in flight is an ordinary thing to do
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
      useProfileDraft.getState().changePhotos((photos) =>
        photos.map((photo) => ({
          ...photo,
          upload: { kind: 'uploaded', photoId: 'photo-1', review: 'allowed' } as const,
        })),
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
    await waitFor(() => expect(screen).toHavePathname('/'));

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
    expect(screen).toHavePathname('/gender');
    expect(screen.getByLabelText('Woman').props.accessibilityState?.selected).toBe(true);
    expect(screen.queryByText(HOME_TAB_LINE)).toBeNull();

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
    await waitFor(() => expect(screen).toHavePathname('/'));

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
    expect(screen).toHavePathname('/gender');
    expect(commits()).toHaveLength(1);
  });

  /**
   * **The intro's three refusals, each in its own sentence and each with the way back**
   * (ADR-0170 §2, [#445](https://github.com/Raketa02/Raketa/issues/445)).
   *
   * The fence is the server's pattern, so a phone number typed on step two is refused here,
   * four screens later. What the player reads is the *reason's* sentence — what to change —
   * and never what was matched; the control under it is back to the intro, with the line
   * still in the box, because the draft was never touched by a failure.
   */
  describe.each([
    ['too_long', 'Keep it under 250 characters.'],
    ['multiline', 'One line, no line breaks.'],
    [
      'contains_contact',
      'Leave out phone numbers, emails, links and handles — people reach you in the chat.',
    ],
  ])('a line the server refused as %s', (reason, sentence) => {
    it('says what to change, and takes the player back to the intro with the line still there', async () => {
      await enterTheSocialSteps();
      await answerTheTags();
      // Tomek's line. What is in it is the server's to judge — this fake refuses whatever
      // arrives — so the walk sends an ordinary sentence and the refusal is still the one
      // the reason names.
      fireEvent.changeText(screen.getByLabelText(INTRO_FIELD_LABEL), 'Call me on 600 700 800');
      await walkOnToTheLastStep();
      answerAboutYou();
      transport.on('POST', COMMIT_PATH, () =>
        json(
          {
            code: 'intro_not_admitted',
            message: 'intro is not one the platform admits',
            trace_id: 'trace-test',
            details: { reason },
          } satisfies Wire['ErrorResponse'],
          400,
        ),
      );

      fireEvent.press(finish());

      // The reason's sentence, as an alert, and neither *try again* nor the pattern.
      expect(await screen.findByText(sentence)).toBeTruthy();
      expect(screen.getByRole('alert')).toBeTruthy();
      expect(screen.queryByText(/Try again — this can only ever set you up once/)).toBeNull();
      expect(screen).toHavePathname('/gender');

      // And the way back, to the step that takes the line — with the line still in the box.
      fireEvent.press(screen.getByLabelText(CHANGE_INTRO_LABEL));
      await waitFor(() => expect(screen).toHavePathname('/intro'));
      expect(screen.getByLabelText(INTRO_FIELD_LABEL).props.value).toBe('Call me on 600 700 800');
    });
  });

  it('asks for the week itself when the server refuses an empty one', async () => {
    // The step will not continue on a blank grid, and the commit refuses one anyway — a
    // disabled control is absent from a replayed request and from an older build. When the
    // refusal arrives, *try again* is the one sentence that is not true: the identical body
    // fails identically, so the screen names the answer and offers the step that takes it.
    await reachTheFinish();
    transport.on('POST', COMMIT_PATH, () => errorResponse(400, 'weekly_hours_empty'));

    fireEvent.press(finish());

    expect(await screen.findByText(/One hour of the week is enough/)).toBeTruthy();
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
    // **Home, and nothing between.** *What Raketa keeps* stood here and recorded nothing.
    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
  }

  it('lands on Home', async () => {
    await commitAndLeave();

    expect(screen).toHavePathname('/');
    expect(screen.queryByText('What we keep from setting up')).toBeNull();
  });

  it('offers no way back into the steps', async () => {
    await commitAndLeave();

    // Every move inside the steps replaced, so there is no history entry holding one of the
    // six, and the gate's profile branch is answered now.
    expect(screen.queryByLabelText(/^Back to /)).toBeNull();
    expect(screen.queryByText(/^Setting up · Step/)).toBeNull();
  });

  it('lands a relaunch in the app rather than back in the steps', async () => {
    await commitAndLeave();

    // The process dies with everything in it — the cache and the draft both. What is left
    // is what the server holds, which is a rating and a Player profile.
    screen.unmount();
    queryClient.clear();
    useProfileDraft.getState().reset();

    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    // And no second commit was made on the way: nothing about launching writes anything.
    expect(commits()).toHaveLength(1);
    expect(keysCommitted.size).toBe(1);
  });
});

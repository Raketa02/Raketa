/**
 * Onboarding, driven through the real route tree and the network boundary.
 *
 * Only `fetch` is faked. The router, the http client, its timeouts, error mapping, the
 * mappers, the use-cases, the hooks, the store and the screens all run for real — so a
 * pass here means the flow works end to end minus the socket.
 *
 * **Onboarding is a nickname and a profile** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §1, [#730](https://github.com/Raketa02/Raketa/issues/730)): sign-up, the naming, the six profile
 * steps and Home — eight screens, and no questionnaire. A level is asked where play begins, by the
 * door on a group's tabs (`levelWherePlayBegins.test`). The gate's outcomes are routing behaviour,
 * so they are asserted as routing: which screen a launch lands on. These tests live outside
 * `src/app/` and import the route files, per docs/architecture.md Part 16.
 *
 * Every assertion is about what a player can see or what left the device. None reads a
 * store's internals or a hook's return shape.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';

import {
  beginSession,
  clearStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { TIMEOUT_MS } from '@/shared/lib/http';
import { queryClient } from '@/shared/lib/query-client';
import { fetchCurrentUserAtLaunch, refreshTokens, restoreSession } from '@/features/auth/types';
import {
  GATE_USER,
  launchSignedIn,
  HOME_TAB_LINE,
  ONBOARDING_ROUTES,
  resetLocation,
  runInProgress,
  RUNS_IN_PROGRESS_PATH,
  SPORTS_SERVED,
  splashHoldsStanding,
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
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FROM_HOME } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

const ASSESSMENT_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';

const ME_PATH = '/api/v1/users/me';
const RATINGS_PATH = '/api/v1/ratings';
const ASSESSMENTS_PATH = '/api/v1/assessments';

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

/** The first profile step's eyebrow — where every launch owed the steps lands. */
const STEP_ONE = /^Setting up · Step 1 of 6/;

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

/**
 * Nothing about the questionnaire was asked or shown on the way. **On Home the ratings are read**
 * — its *Get your level* card asks whether there are any (#731) — so a walk that ends there says
 * so; nothing on the way asks, and with no group to be in there is no card and no run looked for.
 */
function expectNoQuestionnaire({ onHome }: { readonly onHome: boolean }) {
  if (!onHome) expect(transport.requestsTo('GET', RATINGS_PATH)).toEqual([]);
  expect(transport.requestsTo('GET', RUNS_IN_PROGRESS_PATH)).toEqual([]);
  expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toEqual([]);
  expect(screen.queryByText('Which sports do you play?')).toBeNull();
}

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
  resetLocation();
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
    // The gate's read is authenticated, and firing it without a session would only ever
    // produce a 401 for the rotation to chase.
    expect(transport.requests).toHaveLength(0);
  });

  it('sends a player with no nickname yet to the naming step, before anything else', async () => {
    // The gate's first destination (ADR-0199 §3): sign-up creates the account with no nickname,
    // and every destination after this one says the player's nickname. What the step does is its
    // own suite's, `theNaming.test.tsx`; this is the routing.
    stubGate({ nickname: null });

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/name'));
    expect(screen.getByText('How should people see you?')).toBeTruthy();
  });

  it('sends a named player with no Player profile to the profile steps, from their first', async () => {
    // Rated in nothing — the commonest shape there is, since sign-up asks no skill question —
    // and still owed nothing but the six steps.
    stubGate();

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/tags'));
    expect(screen.getByText(STEP_ONE)).toBeTruthy();
    expectNoQuestionnaire({ onHome: false });
  });

  it('sends a player with a rating and a run left halfway to the profile steps all the same', async () => {
    // Neither routes anywhere (ADR-0200 §1): the steps are what is owed, and the run waits for
    // the door where play begins.
    stubGate({ ratings: [RATING], runs: [runInProgress('TENNIS', ASSESSMENT_ID)] });

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/tags'));
    expect(screen.getByText(STEP_ONE)).toBeTruthy();
  });

  it('sends a player with a Player profile into the app, rated in nothing', async () => {
    stubGate({ hasPlayerProfile: true });

    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expectNoQuestionnaire({ onHome: true });
  });

  it('opens the app normally on an unfinished run, and leaves it unread', async () => {
    // **Leaving halfway never takes over the app** (ADR-0200 §5). The gate used to resume this
    // run on every launch until it was finished; it is offered now where play begins, as
    // *Carry on*, and nowhere else.
    stubGate({ hasPlayerProfile: true, runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
    transport.on('GET', `${ASSESSMENTS_PATH}/${ASSESSMENT_ID}`, () => json(OPENING_STEP));

    await launchSignedIn();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(screen.queryByText('Have you played padel before?')).toBeNull();
    expect(transport.requestsTo('GET', `${ASSESSMENTS_PATH}/${ASSESSMENT_ID}`)).toEqual([]);
  });

  it('waits for the re-read a device still holds the old answer for', async () => {
    // The gate's one read, at the state a **phone** is actually in: the launch's own answer —
    // *no Player profile* — still cached and merely stale, while the server now says the steps
    // are done. Acting on the cached copy would redirect back into the steps, which unmounts this
    // layout and cancels the re-read, so the stale copy would stand for good.
    stubGate();
    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/tags'));

    let answerMe = () => {};
    const held = new Promise<void>((resolve) => {
      answerMe = resolve;
    });
    transport.on('GET', ME_PATH, async () => {
      await held;
      return json<Wire['MeResponse']>({ ...GATE_USER, has_player_profile: true });
    });
    // Everything stale, as a foreground leaves it.
    void queryClient.invalidateQueries();

    router.replace('/');

    await waitFor(() => expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(2));
    expect(screen).not.toHavePathname('/tags');
    expect(screen.queryByText(STEP_ONE)).toBeNull();

    answerMe();

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('says so, and offers a retry, when the gate cannot be read', async () => {
    // A terminal failure rather than a dropped connection: a dropped connection is retried
    // automatically with backoff, and this test is about the gate rather than the retry policy.
    stubGate();
    transport.on('GET', ME_PATH, () => errorResponse(403, 'forbidden'));

    await launchSignedIn();

    expect(await screen.findByText("We couldn't pick up where you left off")).toBeTruthy();
    // No guess in either direction: into the app skips the steps, and into the steps asks a
    // set-up player again.
    expect(screen).not.toHavePathname('/tags');

    stubGate();
    fireEvent.press(screen.getByLabelText('Try again'));

    await waitFor(() => expect(screen).toHavePathname('/tags'));
  });

  it('says so after the first unanswered read, rather than a blank screen through every retry', async () => {
    // A connection that is up and reaches nothing — a weak signal, a captive portal, a server
    // that is not there. Each read waits out the request timeout, and the gate drew nothing
    // through all three: 49 seconds of an empty screen before a word.
    stubGate();
    transport.on('GET', ME_PATH, neverResponds());

    await launchSignedIn();
    expect(screen.queryByText("We couldn't pick up where you left off")).toBeNull();
    await act(async () => {
      jest.advanceTimersByTime(TIMEOUT_MS.request);
    });

    expect(await screen.findByText("We couldn't pick up where you left off")).toBeTruthy();
    expect(transport.requestsTo('GET', ME_PATH).length).toBeLessThan(3);
    // Still trying underneath, and the control says so rather than offering a second attempt
    // on top of the one in flight.
    expect(screen.getByRole('button', { name: 'Trying again…' })).toBeTruthy();

    // Every retry spent: the screen is the same, and the control is the player's again. The
    // async advance, because each retry starts in a microtask after its backoff.
    await act(() => jest.advanceTimersByTimeAsync(3 * TIMEOUT_MS.request));
    expect(await screen.findByRole('button', { name: 'Try again' })).toBeTruthy();
    expect(screen.getByText("We couldn't pick up where you left off")).toBeTruthy();
    expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(3);
  });

  it('keeps the screen up, saying it is trying, while Try again is asked', async () => {
    // A read with no answer yet is not *pending* once one has failed: going blank for the
    // retry is the same empty screen, on the one press the player made to get past it.
    stubGate();
    transport.on('GET', ME_PATH, () => errorResponse(403, 'forbidden'));

    await launchSignedIn();
    await screen.findByText("We couldn't pick up where you left off");

    let answerMe = () => {};
    const held = new Promise<void>((resolve) => {
      answerMe = resolve;
    });
    transport.on('GET', ME_PATH, async () => {
      await held;
      return json<Wire['MeResponse']>(GATE_USER);
    });
    fireEvent.press(screen.getByRole('button', { name: 'Try again' }));

    expect(await screen.findByRole('button', { name: 'Trying again…' })).toBeTruthy();
    expect(screen.getByText("We couldn't pick up where you left off")).toBeTruthy();

    answerMe();

    await waitFor(() => expect(screen).toHavePathname('/tags'));
  });

  it("opens on the launch's own failure, and tries again by itself", async () => {
    // Bootstrap's validation is the gate's first read. It could not reach the server, so the
    // first frame after the splash says so — rather than asking again behind an empty screen.
    stubGate();
    transport.on('GET', ME_PATH, networkFailure());
    await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
    // The root layout's step, composed as it composes it.
    await restoreSession(() => fetchCurrentUserAtLaunch(queryClient));

    stubGate();
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/' });

    expect(screen.getByText("We couldn't pick up where you left off")).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Trying again…' })).toBeTruthy();

    await waitFor(() => expect(screen).toHavePathname('/tags'));
    expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(2);
  });

  it("says it is waiting, not that it failed, when the launch's read failed offline", async () => {
    // The launch's read fails at once with no connection. What the gate says next is the
    // connection's, not the failure's: it resumes by itself, so nothing coral and no button.
    stubGate();
    transport.on('GET', ME_PATH, networkFailure());
    await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
    await restoreSession(() => fetchCurrentUserAtLaunch(queryClient));
    onlineManager.setOnline(false);

    stubGate();
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/' });

    expect(screen.getByText("You're offline. This will load as soon as you're back.")).toBeTruthy();
    expect(screen.queryByText("We couldn't pick up where you left off")).toBeNull();

    onlineManager.setOnline(true);

    await waitFor(() => expect(screen).toHavePathname('/tags'));
  });

  it('sends the player to sign in when the gate 401s and the refresh is rejected', async () => {
    // The session really is over, and *your session has ended* behind a Try again button is
    // the one thing a retry cannot fix.
    stubGate();
    transport.on('GET', ME_PATH, () => errorResponse(401, 'unauthorized'));
    transport.on('POST', '/api/v1/auth/refresh', () => errorResponse(401, 'invalid_refresh_token'));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(screen.queryByText("We couldn't pick up where you left off")).toBeNull();
  });

  it('sends the player to sign in when the gate is refused and there is no credential to rotate', async () => {
    // The keychain empty while the session machine still says `authenticated`: the read goes
    // out with no Authorization header and is refused, and the recovery is admitting the
    // session is over, not a retry.
    stubGate();
    transport.on('GET', ME_PATH, () => errorResponse(401, 'unauthorized'));

    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/' });
    setSessionStatus('authenticated');

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(screen.queryByText("We couldn't pick up where you left off")).toBeNull();
    expect(transport.requestsTo('POST', '/api/v1/auth/refresh')).toEqual([]);
  });

  it('says it is waiting rather than rendering nothing, when launched offline', async () => {
    stubGate();
    // `networkMode: 'online'` *pauses* a query instead of failing it, so without a branch for
    // that the app renders a blank screen for as long as the connection stays dead.
    onlineManager.setOnline(false);

    await launchSignedIn();

    expect(
      await screen.findByText("You're offline. This will load as soon as you're back."),
    ).toBeTruthy();
    expect(transport.requests).toHaveLength(0);

    onlineManager.setOnline(true);

    await waitFor(() => expect(screen).toHavePathname('/tags'));
  });

  /**
   * **The entry gate holds the splash while it is still asking** (ADR-0209 §3). *Pending* draws
   * nothing — the one blank state after startup — and the splash fading into it would be the blank
   * frame the brief forbids. An answer lets go, whichever it is: a destination, or either of the two
   * screens saying the gate could not be read.
   */
  describe('the splash', () => {
    it('is held while the gate is still asking who this is, and let go when it answers', async () => {
      stubGate();
      let answerMe = () => {};
      const held = new Promise<void>((resolve) => {
        answerMe = resolve;
      });
      transport.on('GET', ME_PATH, async () => {
        await held;
        return json<Wire['MeResponse']>({ ...GATE_USER, has_player_profile: true });
      });

      await launchSignedIn();
      await waitFor(() => expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(1));

      expect(splashHoldsStanding()).toBe(1);

      answerMe();

      expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
      expect(splashHoldsStanding()).toBe(0);
    });

    it('is let go on the screen saying the gate could not be read', async () => {
      stubGate();
      transport.on('GET', ME_PATH, () => errorResponse(403, 'forbidden'));

      await launchSignedIn();

      expect(await screen.findByText("We couldn't pick up where you left off")).toBeTruthy();
      expect(splashHoldsStanding()).toBe(0);
    });

    it('is let go on the screen saying it is waiting for a connection', async () => {
      stubGate();
      onlineManager.setOnline(false);

      await launchSignedIn();

      expect(
        await screen.findByText("You're offline. This will load as soon as you're back."),
      ).toBeTruthy();
      expect(splashHoldsStanding()).toBe(0);
    });

    it('is never held for a signed-out launch, which asks the gate nothing', async () => {
      setSessionStatus('unauthenticated');

      renderRouter(ONBOARDING_ROUTES, { initialUrl: '/' });

      await waitFor(() => expect(screen).toHavePathname('/sign-in'));
      expect(splashHoldsStanding()).toBe(0);
    });
  });

  it('claims nothing was tried, and offers no retry for a query that resumes itself', async () => {
    stubGate();
    onlineManager.setOnline(false);

    await launchSignedIn();
    await screen.findByText("You're offline. This will load as soon as you're back.");

    expect(
      screen.queryByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeNull();
    expect(screen.queryByLabelText('Try again')).toBeNull();

    onlineManager.setOnline(true);
    await waitFor(() => expect(screen).toHavePathname('/tags'));
  });
});

// ---------------------------------------------------------------------------
// A sign-up, end to end
// ---------------------------------------------------------------------------

describe('a sign-up', () => {
  const COMMIT_PATH = '/api/v1/players/me/profile';
  const FIX = { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 };

  /**
   * The server behind Ania's sign-up: an account with no nickname, a naming that records one, and
   * a commit that sets her up — each re-stubbing `/users/me` as the server would now answer it.
   */
  function stubAniasSignUp() {
    transport.on('POST', '/api/v1/users', () =>
      json<Wire['UserResponse']>({ ...GATE_USER, nickname: null }, 201),
    );
    transport.on('POST', '/api/v1/auth/login', () =>
      json<Wire['TokenResponse']>({
        access_token: 'access-1',
        refresh_token: 'refresh-1',
        token_type: 'bearer',
        expires_in: 900,
      }),
    );
    stubGate({ nickname: null });
    transport.on('PUT', '/api/v1/users/me/name', () => {
      stubGate({ nickname: 'ania.k' });
      return json<Wire['UserResponse']>({ ...GATE_USER, nickname: 'ania.k' });
    });
    stubProfileOptions(transport);
    stubLocation(fakeLocation({ fix: FIX }));
    transport.on('POST', COMMIT_PATH, () => {
      stubGate({ nickname: 'ania.k', hasPlayerProfile: true });
      return json<Wire['PlayerProfileResponse']>(
        {
          player_id: GATE_USER.id,
          social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
          photo_ids: [],
          weekly_hours: [{ day: 3, hour: 19 }],
          location: { latitude: 41.39, longitude: 2.17 },
          created_at: '2026-11-04T10:00:00Z',
          updated_at: '2026-11-04T10:00:00Z',
        },
        201,
      );
    });
  }

  /** Every screen the walk stood on, in order, as the router reported it. */
  const visited: string[] = [];
  async function onTo(path: string) {
    await waitFor(() => expect(screen).toHavePathname(path));
    visited.push(path);
  }

  it('walks to Home in eight screens, with no questionnaire on the way', async () => {
    visited.length = 0;
    setSessionStatus('unauthenticated');
    stubAniasSignUp();

    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/sign-up' });

    // 1. Sign-up.
    await onTo('/sign-up');
    fireEvent.changeText(screen.getByLabelText('Email'), 'ania@example.com');
    fireEvent.changeText(screen.getByLabelText('Password'), 'hunter2hunter2');
    fireEvent.changeText(screen.getByLabelText('Repeat password'), 'hunter2hunter2');
    fireEvent.press(screen.getByLabelText('I am 18 or over'));
    fireEvent.press(screen.getByLabelText('Create account'));

    // 2. How should people see you? — one box, a Nickname.
    await onTo('/name');
    fireEvent.changeText(screen.getByLabelText('Nickname'), 'ania.k');
    fireEvent.press(screen.getByLabelText('Continue'));

    // 3. What kind of player are you? — straight after the naming: no values, no mission, no
    // vision, and no sports.
    await onTo('/tags');
    expect(screen.getByText('What kind of player are you?')).toBeTruthy();
    fireEvent.press(await screen.findByLabelText('Plays to win'));
    fireEvent.press(screen.getByLabelText('Here to improve'));
    fireEvent.press(screen.getByLabelText('Continue'));

    // 4. Say it in your own words.
    await onTo('/intro');
    fireEvent.press(screen.getByLabelText('Next'));

    // 5. Your court photos.
    await onTo('/photos');
    fireEvent.press(screen.getByLabelText('Continue'));

    // 6. When do you usually play?
    await onTo('/availability');
    fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
    fireEvent.press(screen.getByLabelText('Continue'));

    // 7. Where do you play?
    await onTo('/location');
    fireEvent.press(screen.getByLabelText('Use my location'));
    fireEvent.press(await screen.findByLabelText('Continue'));

    // 8. Who do you want to play with? — and *Finish* lands on Home, with no data screen between.
    await onTo('/gender');
    fireEvent.press(screen.getByLabelText('Woman'));
    fireEvent.press(screen.getByLabelText('Finish'));

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(visited).toEqual([
      '/sign-up',
      '/name',
      '/tags',
      '/intro',
      '/photos',
      '/availability',
      '/location',
      '/gender',
    ]);
    expect(transport.requestsTo('POST', COMMIT_PATH)).toHaveLength(1);
    expectNoQuestionnaire({ onHome: true });
  });
});

// ---------------------------------------------------------------------------
// The sports picker
// ---------------------------------------------------------------------------

describe('the sports picker', () => {
  /** The picker opened with no group to return to — Home's (#731 draws its card). */
  async function reachThePicker() {
    stubGate({ hasPlayerProfile: true });
    transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));

    await launchSignedIn('/sports');
    expect(await screen.findByText('Which sports do you play?')).toBeTruthy();
  }

  it('ticks nothing for her: she chooses her sports herself', async () => {
    await reachThePicker();

    expect(await screen.findByLabelText('Padel')).toBeTruthy();
    expect(screen.queryByText('Selected')).toBeNull();
    expect(screen.getByLabelText('Choose a sport to continue')).toBeTruthy();
  });

  it('counts the sports chosen on the control that continues', async () => {
    await reachThePicker();

    fireEvent.press(await screen.findByLabelText('Padel'));
    expect(screen.getByLabelText('Rate 1 sport')).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Tennis'));
    expect(screen.getByLabelText('Rate 2 sports')).toBeTruthy();

    // Tapping a chosen sport again removes it, and the count follows.
    fireEvent.press(screen.getByLabelText('Tennis'));
    expect(screen.getByLabelText('Rate 1 sport')).toBeTruthy();
  });

  it('says which sports are selected in words, not only by their border', async () => {
    await reachThePicker();

    fireEvent.press(await screen.findByLabelText('Padel'));

    expect(screen.getByText('Selected')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Padel', selected: true })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Tennis', selected: true })).toBeNull();
  });

  it('starts the first chosen sport and lands on its opening question', async () => {
    await reachThePicker();
    transport.on('POST', ASSESSMENTS_PATH, () => json(OPENING_STEP, 201));

    // Chosen second, so tennis is second in the queue — order is the only thing the
    // selection carries.
    fireEvent.press(await screen.findByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Tennis'));
    fireEvent.press(screen.getByLabelText('Rate 2 sports'));

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));

    const [started] = transport.requestsTo('POST', ASSESSMENTS_PATH);
    expect(started?.body).toEqual({ sport: 'PADEL' });
    expect(await screen.findByText('Recent activity')).toBeTruthy();
    expect(screen.getByText('Padel · Rating 1 of 2')).toBeTruthy();
    // The response *is* the next question, so it is written into the cache rather than
    // asked for a second time.
    expect(transport.requestsTo('GET', `${ASSESSMENTS_PATH}/${ASSESSMENT_ID}`)).toEqual([]);
  });

  it('sends one start, however many times the control is pressed', async () => {
    await reachThePicker();

    let answer = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('POST', ASSESSMENTS_PATH, async () => {
      await held;
      return json(OPENING_STEP, 201);
    });

    fireEvent.press(await screen.findByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Rate 1 sport'));

    await waitFor(() => expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(1));
    fireEvent.press(screen.getByLabelText('Starting…'));

    answer();
    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(1);
  });

  it('never writes the sport selection to the server', async () => {
    await reachThePicker();

    fireEvent.press(await screen.findByLabelText('Squash'));
    fireEvent.press(screen.getByLabelText('Badminton'));

    const writes = transport.requests.filter((request) => request.method !== 'GET');
    expect(writes).toEqual([]);
  });

  it('turns back to where it was opened from, having started nothing', async () => {
    // Opened from inside the app, by `replace`, so there is nothing behind it to pop to: its
    // back control is the way out, and it is Home for a picker opened with no group.
    await reachThePicker();
    fireEvent.press(await screen.findByLabelText('Padel'));

    fireEvent.press(screen.getByLabelText('Back'));

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Links into the middle of the questionnaire
// ---------------------------------------------------------------------------

/** Well-formed, and pointing at a run this player has no business being handed. */
const STRANGE_LINK_ID = 'e5f6a7b8-9c0d-4e1f-8a2b-3c4d5e6f7a8b';

describe('a link into the middle of the questionnaire', () => {
  // Every door begins a pass, and a link is none of them. So surviving param validation is not
  // the same as belonging here: a well-formed link naming a sport outside the running pass is not
  // a shortcut into a flow already under way.
  it('sends a question link for a sport outside the running pass to Home, asking nothing', async () => {
    stubGate({ hasPlayerProfile: true });
    useOnboardingPass.getState().begin(['padel'], FROM_HOME);

    await launchSignedIn(`/question/${STRANGE_LINK_ID}?sport=squash`);

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(transport.requestsTo('GET', `${ASSESSMENTS_PATH}/${STRANGE_LINK_ID}`)).toEqual([]);
  });

  it('sends a result link for a sport outside the running pass to Home', async () => {
    stubGate({ hasPlayerProfile: true });
    useOnboardingPass.getState().begin(['padel'], FROM_HOME);

    await launchSignedIn(`/result/${STRANGE_LINK_ID}?sport=squash`);

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(transport.requestsTo('GET', `${ASSESSMENTS_PATH}/${STRANGE_LINK_ID}`)).toEqual([]);
  });

  it('stays on Home, rather than bouncing back to a run that is really unfinished', async () => {
    // The trap this used to avoid by sending the player to welcome: the gate answered *resume*
    // for an outstanding run. It resumes nothing now, so Home is as safe a place as any.
    stubGate({ hasPlayerProfile: true, runs: [runInProgress('SQUASH', STRANGE_LINK_ID)] });
    useOnboardingPass.getState().begin(['padel'], FROM_HOME);

    await launchSignedIn(`/question/${STRANGE_LINK_ID}?sport=squash`);

    expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('admits a run reached with no pass running, as a pass of one sport', async () => {
    stubGate({ hasPlayerProfile: true, runs: [runInProgress('TENNIS', ASSESSMENT_ID)] });
    transport.on('GET', `${ASSESSMENTS_PATH}/${ASSESSMENT_ID}`, () => json(OPENING_STEP));

    await launchSignedIn(`/question/${ASSESSMENT_ID}?sport=tennis`);

    expect(await screen.findByText('Tennis · Rating 1 of 1')).toBeTruthy();
  });
});

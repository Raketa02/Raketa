/**
 * Onboarding's second part, walked through the real route tree and the network boundary.
 *
 * The same harness every onboarding flow suite uses — only `fetch` is faked, and the
 * router, the http client, the hooks, the store and the screens all run for real. What is
 * being proved here is **the walk itself**: six routes in one order, a draft that survives
 * moving between them in both directions, and a part that cannot be entered from its
 * middle. What each step asks is each step's own suite; this one answers whatever is on
 * screen and keeps walking.
 *
 * Every assertion is about what a player can see, where they land, or what left the device.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  stubGate as stubGateWith,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { useProfileDraft } from '../store/profileDraft.store';

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
 * The six steps in order: what each says it is, what its eyebrow reads, and the back
 * control it offers.
 *
 * The first step's eyebrow carries its own rule as well as its position — the tag floor
 * belongs on the screen rather than only inside a disabled button — which is why the line
 * is per step here rather than composed from the index.
 */
const STEPS = [
  {
    path: '/tags',
    title: 'What kind of player are you?',
    eyebrow: 'Setting up · Step 1 of 6 · Pick 2 to 6',
    back: undefined,
  },
  {
    path: '/photos',
    title: 'Your court photos',
    eyebrow: 'Setting up · Step 2 of 6 · On-court only — up to three',
    back: 'Back to What kind of player are you?',
  },
  {
    path: '/availability',
    title: 'When do you usually play?',
    eyebrow: 'Setting up · Step 3 of 6',
    back: 'Back to Your court photos',
  },
  {
    path: '/location',
    title: 'Where do you play?',
    eyebrow: 'Setting up · Step 4 of 6',
    back: 'Back to When do you usually play?',
  },
  {
    path: '/radius',
    title: 'How far will you travel?',
    eyebrow: 'Setting up · Step 5 of 6',
    back: 'Back to Where do you play?',
  },
  {
    path: '/opt-in',
    title: 'May we suggest games?',
    eyebrow: 'Setting up · Step 6 of 6',
    back: 'Back to How far will you travel?',
  },
] as const;

/**
 * The first step that still stands in for itself, and the one this suite answers to prove
 * the draft survives a walk.
 *
 * It moves as tickets land. Photos was it, then availability, and both are the wrong step
 * to have used anyway: each may be passed with nothing at all, so *an answer that is still
 * there* has to be asked of a step that insists on one.
 */
const FIRST_PLACEHOLDER_STEP = 3;

/** The steps of the six that may be walked past with nothing answered at all. */
const OPTIONAL_STEPS = [1, 2];

/**
 * Answer whatever step is on screen.
 *
 * Three of the six are built and each wants something different — two tags at the floor,
 * and nothing at all on the photos and availability steps, both of which continue from
 * empty. The rest still stand in for themselves. This suite is about the walk, so it
 * answers each of them the way that step wants and says nothing else about any of them.
 */
function answerTheStep(index: number) {
  if (index >= FIRST_PLACEHOLDER_STEP) {
    fireEvent.press(screen.getByLabelText('Answer this step'));
    return;
  }
  // Optional, and each has its own suite: the photos step reaches the device, and the
  // availability grid ships empty on purpose.
  if (OPTIONAL_STEPS.includes(index)) return;

  fireEvent.press(screen.getByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
}

/** The first step's continue is blocked until its floor is met; the rest are not. */
async function continueFromTheFirstStep() {
  answerTheStep(0);
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/photos'));
}

/** Walk from the photos step as far as `index`, answering each step on the way. */
async function walkOnTo(index: number) {
  for (let step = 1; step < index; step += 1) {
    answerTheStep(step);
    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname(STEPS[step + 1]!.path));
  }
}

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

/** A launch by a player the gate owes the second part to, landing on its first step. */
async function enterTheSocialSteps() {
  stubGate({ ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  // The first step is drawn from a served vocabulary, so the walk starts once it is on
  // screen rather than once the route has changed.
  await screen.findByLabelText('Pick 2 tags to continue');
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  // What killing the app does. The draft is in memory and never persisted, so a new process
  // starts the part with nothing in it.
  useProfileDraft.getState().reset();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// Walking the part
// ---------------------------------------------------------------------------

describe('walking forward through the second part', () => {
  it('visits the six steps in order, saying which one of how many', async () => {
    await enterTheSocialSteps();

    for (const [index, step] of STEPS.entries()) {
      expect(screen).toHavePathname(step.path);
      expect(screen.getByText(step.title)).toBeTruthy();
      // Story 12: the player should know these screens end. Unlike the questionnaire, this
      // part can say how many there are, because six is six whatever anybody answers.
      expect(screen.getByText(step.eyebrow)).toBeTruthy();

      if (index < STEPS.length - 1) {
        answerTheStep(index);
        fireEvent.press(await screen.findByLabelText('Continue'));
        await waitFor(() => expect(screen).toHavePathname(STEPS[index + 1]!.path));
      }
    }
  });

  it('ends at the last step rather than navigating on to something that does not exist', async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    for (let step = 2; step < STEPS.length; step += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
    }

    await waitFor(() => expect(screen).toHavePathname('/opt-in'));
    // What follows the last step is the profile commit, and a commit is not a screen. Until
    // it exists the part ends here rather than claiming the account was set up.
    expect(screen.queryByLabelText('Continue')).toBeNull();
    expect(screen.getByText(/Finishing sends everything at once/)).toBeTruthy();
  });
});

describe('walking back through the second part', () => {
  it('offers a back control on every step after the first, and none on the first', async () => {
    await enterTheSocialSteps();

    // Story 11, and the boundary ADR-0090 makes hard: behind step one is a rated
    // Assessment's review, and an answer is revisable for as long as its run is and no
    // longer. There is no control here that could reach it.
    expect(screen.queryByLabelText(/^Back to /)).toBeNull();

    await continueFromTheFirstStep();
    expect(screen.getByLabelText(STEPS[1]!.back!)).toBeTruthy();

    for (let index = 2; index < STEPS.length; index += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
      await waitFor(() => expect(screen).toHavePathname(STEPS[index]!.path));
      expect(screen.getByLabelText(STEPS[index]!.back!)).toBeTruthy();
    }
  });

  it('leads from every step to the one before it, all the way back to the first', async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    for (let step = 2; step < STEPS.length; step += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
    }
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));

    for (let index = STEPS.length - 1; index > 0; index -= 1) {
      fireEvent.press(screen.getByLabelText(STEPS[index]!.back!));
      await waitFor(() => expect(screen).toHavePathname(STEPS[index - 1]!.path));
    }

    expect(screen).toHavePathname('/tags');
    // Back reaches the first step and stops. It never reaches the result, the review or
    // anything else in part one — every move inside the part replaces, so no history entry
    // holding a part-one screen exists to walk into.
    expect(screen.queryByLabelText(/^Back to /)).toBeNull();
  });
});

describe('the draft the part holds', () => {
  it('still holds an answer the player walks back to', async () => {
    // The whole reason the draft exists: checking one thing must not cost the player the
    // rest, and an answer they gave must still be there when they return to it.
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(FIRST_PLACEHOLDER_STEP);

    fireEvent.press(screen.getByLabelText('Answer this step'));
    expect(await screen.findByLabelText('Answered')).toBeTruthy();

    // Forward to the end, then all the way back.
    for (let step = FIRST_PLACEHOLDER_STEP + 1; step < STEPS.length; step += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
    }
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));
    for (let index = STEPS.length - 1; index > FIRST_PLACEHOLDER_STEP; index -= 1) {
      fireEvent.press(screen.getByLabelText(STEPS[index]!.back!));
      await waitFor(() => expect(screen).toHavePathname(STEPS[index - 1]!.path));
    }

    expect(screen).toHavePathname(STEPS[FIRST_PLACEHOLDER_STEP]!.path);
    expect(screen.getByLabelText('Answered')).toBeTruthy();
  });

  it("keeps each step's answer to itself", async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(FIRST_PLACEHOLDER_STEP);

    // The next step is unanswered, and answering it must not have been done on its behalf
    // by the step before — nothing is claimed for a player who has not said it.
    expect(screen.getByLabelText('Answer this step')).toBeTruthy();
  });

  it('writes nothing to the server anywhere in the part', async () => {
    await enterTheSocialSteps();
    // Everything the gate asked on the way in, plus the one read the first step is drawn
    // from. What the part costs *after* it is on screen is measured from here — counting
    // writes only would let a step that started reading on every render pass.
    const onArrival = transport.requests.length;

    await continueFromTheFirstStep();
    for (let step = 2; step < STEPS.length; step += 1) {
      answerTheStep(step - 1);
      fireEvent.press(screen.getByLabelText('Continue'));
      await waitFor(() => expect(screen).toHavePathname(STEPS[step]!.path));
    }
    fireEvent.press(screen.getByLabelText('Answer this step'));

    const afterArrival = transport.requests.slice(onArrival);

    // The part is the checkpoint unit: **nothing is written until the one commit at the
    // end**, which is why moving between steps is free in both directions and why leaving
    // restarts at step one. Not one write, in either direction, on any of the six.
    //
    // A photo is the one thing the part does send, and only when a player adds one — the
    // bytes go up as they are picked and become part of a profile when the commit names
    // them. This walk adds none, so nothing leaves here at all.
    expect(afterArrival.filter((request) => request.method !== 'GET')).toEqual([]);

    // And the only thing read is who the player is, which step two's court poster is drawn
    // from — the auth feature's own query rather than a second one against the same route.
    // The count is not pinned because it cannot be: the router harness runs on fake timers
    // and `waitFor` advances them, so Query's five-minute collection can fire mid-walk and
    // the read happens once or not at all. What must not change is that there is nothing
    // *else* in the list.
    expect(afterArrival.map((request) => request.path)).toEqual(
      afterArrival.map(() => '/api/v1/users/me'),
    );
  });
});

// ---------------------------------------------------------------------------
// Getting into the part, and the ways that must not work
// ---------------------------------------------------------------------------

describe('a link naming a step in the middle of the part', () => {
  it('is sent to the beginning rather than into the middle', async () => {
    // Story 7. The draft is client-held and starts empty, so continuing from step five
    // would commit a Player profile built from four screens the player never saw — with
    // the tag selection, the week and the consent all missing.
    stubGate({ ratings: [RATING], hasPlayerProfile: false });
    stubProfileOptions(transport);

    await launchSignedIn('/radius');

    await waitFor(() => expect(screen).toHavePathname('/tags'));
    expect(await screen.findByText(STEPS[0]!.eyebrow)).toBeTruthy();
  });

  it('is not turned away once the player is genuinely inside the part', async () => {
    // The other half of the same rule, and the one that must not regress: reaching step
    // five by walking there is exactly what the part is for.
    await enterTheSocialSteps();

    await continueFromTheFirstStep();
    for (let step = 2; step <= 4; step += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
      await waitFor(() => expect(screen).toHavePathname(STEPS[step]!.path));
    }

    expect(screen).toHavePathname('/radius');
  });
});

describe('killing the app mid-part', () => {
  it('restarts at the first step with nothing answered, and the rating untouched', async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(FIRST_PLACEHOLDER_STEP);
    fireEvent.press(screen.getByLabelText('Answer this step'));
    expect(await screen.findByLabelText('Answered')).toBeTruthy();

    // The process dies: the query cache and the in-memory draft go with it. Nothing was
    // ever written, so there is nothing on the server to come back to — which is exactly
    // what makes the part, rather than the step, the checkpoint.
    screen.unmount();
    queryClient.clear();
    useProfileDraft.getState().reset();

    await launchSignedIn();

    // Step one, not step two: the Skill rating survived — it is what sends them back here
    // rather than to welcome — and the six answers did not.
    await waitFor(() => expect(screen).toHavePathname('/tags'));
    // Nothing picked: the control is still asking for the floor, and the two tags chosen on
    // the way through are gone with the process that held them.
    expect(await screen.findByLabelText('Pick 2 tags to continue')).toBeTruthy();
    expect(screen.getByLabelText('Plays to win').props.accessibilityState?.selected).toBe(false);
  });
});

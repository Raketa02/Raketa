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
  PROFILE_OPTIONS_PATH,
  launchSignedIn,
  resetLocation,
  stubGate as stubGateWith,
  stubLocation,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { fakeLocation } from '@/test-support/platform';
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
 * The seven steps in order: what each says it is, what its eyebrow reads, the back control
 * it offers, and the label it continues with.
 *
 * **The eyebrow is per step rather than composed from the index**, because three of the
 * seven do something else with the line. Two carry a rule as well as a position — the tag floor
 * and the week's floor of one both belong on the screen rather than only inside a disabled
 * button. The last gives the position up entirely: *before finishing* already says where
 * the player is, and what that line has to carry is that one question is the whole of what
 * is left.
 *
 * `forward` is *Continue* on five of the seven. The location step names what leaving without
 * an area costs, because a location is what search and matchmaking are worked out from —
 * and this walk is the one that leaves without one. The last step finishes rather than
 * continuing: there is nothing in front of it but the commit. The week's control also says
 * what is missing while nothing is ticked, but this walk answers every step it is on, so
 * *Continue* is what it meets.
 */
const STEPS = [
  {
    path: '/tags',
    title: 'What kind of player are you?',
    eyebrow: 'Setting up · Step 1 of 7 · Pick 2 to 6',
    back: undefined,
    forward: 'Continue',
  },
  {
    path: '/photos',
    title: 'Your court photos',
    eyebrow: 'Setting up · Step 2 of 7 · On-court only — up to three',
    back: 'Back to What kind of player are you?',
    forward: 'Continue',
  },
  {
    path: '/availability',
    title: 'When do you usually play?',
    eyebrow: 'Setting up · Step 3 of 7 · Tick at least one',
    back: 'Back to Your court photos',
    forward: 'Continue',
  },
  {
    path: '/location',
    title: 'Where do you play?',
    eyebrow: 'Setting up · Step 4 of 7',
    back: 'Back to When do you usually play?',
    forward: 'Continue without matching',
  },
  {
    path: '/radius',
    title: 'How far should we look for players?',
    eyebrow: 'Setting up · Step 5 of 7',
    back: 'Back to Where do you play?',
    forward: 'Continue',
  },
  {
    path: '/gender',
    title: 'Who do you want to play with?',
    eyebrow: 'Setting up · Step 6 of 7',
    back: 'Back to How far should we look for players?',
    forward: 'Continue',
  },
  {
    path: '/opt-in',
    title: 'May we suggest games?',
    eyebrow: 'The one thing we ask before finishing',
    back: 'Back to Who do you want to play with?',
    forward: 'Finish — show me players',
  },
] as const;

/** The last step's two answers. Either one is a whole answer; neither is ever pre-ticked. */
const OPT_IN = { yes: 'Yes — suggest games', no: "No — don't suggest games" } as const;

/**
 * The step this suite gives a real answer to and comes back for.
 *
 * The **first** one. The week insists on an answer too since ADR-0102, but photos, the
 * location and the radius may each be walked past untouched, and walking back to step one
 * is the longest round trip the part has — which is what this is really measuring.
 */
const ANSWERED_STEP = 0;

/**
 * The steps of the seven that may be walked past with nothing answered at all.
 *
 * Three steps, three different reasons. Photos are genuinely optional — no photo is a
 * complete answer to *add some photos*. **The location step is not**: it can be *passed*
 * with nothing, at the cost of search and matchmaking, and this walk is the one that pays
 * it, which is why its forward control is labelled differently. The radius is not optional
 * either — it opens at the **served default**, so walking past it without touching the
 * slider is an answer rather than an absence.
 *
 * **The week left this list**, and it is the only step that ever has. It was here for the
 * same reason photos are, and ADR-0102 took the reason away: a blank grid was being scored
 * as a measured zero, so it is asked for rather than guessed at.
 *
 * **The gender step never joined it.** Half of that screen *is* pre-answered — the
 * preference opens unconstrained, which is what every player already holds — but the answer
 * about the player is required and has no default anybody may give on their behalf.
 */
const OPTIONAL_STEPS = [1, 3, 4];

/**
 * Answer whatever step is on screen.
 *
 * Each of the seven wants something different — two tags at the floor, one cell of the week,
 * nothing at all on the three that may be walked past, one answer about the player, and one
 * of two answers on the last,
 * which has no default in either direction. This suite is about the walk, so it answers
 * each of them the way that step wants and says nothing else about any of them.
 */
function answerTheStep(index: number) {
  if (index === STEPS.length - 1) {
    fireEvent.press(screen.getByLabelText(OPT_IN.yes));
    return;
  }
  // Optional, and each has its own suite: the photos step reaches the device, the location
  // step can be passed at a cost it names, and the radius opens at the served default.
  if (OPTIONAL_STEPS.includes(index)) return;

  // The week's floor is one of twenty-one, so one cell is the whole of what step three
  // asks for. Its own suite is where the grid itself is exercised.
  if (STEPS[index]!.path === '/availability') {
    fireEvent.press(screen.getByLabelText('Wednesday evening'));
    return;
  }

  // The answer about the player, which is the half of that screen with no default. The
  // preference below it is already `Anyone` and is left alone here — its own suite is where
  // narrowing, and what narrowing costs, is exercised.
  if (STEPS[index]!.path === '/gender') {
    fireEvent.press(screen.getByLabelText('Woman'));
    return;
  }

  fireEvent.press(screen.getByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
}

/**
 * Press the forward control of the step at `from`.
 *
 * Named per step rather than as one string: six of the seven say *Continue* and one says
 * what it costs to leave it empty, and a helper that hunted for either would stop noticing
 * which screen it was on.
 *
 * **Waited for, not read.** Two of the seven draw their control from the served options, and
 * a suite that walks the part under fake timers can outrun a query whose cache was
 * collected while nothing was observing it. Waiting is what a player does too.
 */
async function continueFrom(from: number) {
  fireEvent.press(await screen.findByLabelText(STEPS[from]!.forward));
}

/** The first step's continue is blocked until its floor is met; the rest are not. */
async function continueFromTheFirstStep() {
  answerTheStep(0);
  fireEvent.press(await screen.findByLabelText(STEPS[0]!.forward));
  await waitFor(() => expect(screen).toHavePathname('/photos'));
}

/** Walk from the photos step as far as `index`, answering each step on the way. */
async function walkOnTo(index: number) {
  for (let step = 1; step < index; step += 1) {
    answerTheStep(step);
    await continueFrom(step);
    await waitFor(() => expect(screen).toHavePathname(STEPS[step + 1]!.path));
  }
}

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

/** A launch by a player the gate owes the second part to, landing on its first step. */
async function enterTheSocialSteps() {
  stubGate({ ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);
  // A phone nobody has asked yet. This suite never presses the location step's control, so
  // no prompt is shown and no fix is read — what it needs from the device is only that it
  // is *described*, rather than being whatever a mocked native module answers.
  stubLocation(fakeLocation());

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
  resetLocation();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// Walking the part
// ---------------------------------------------------------------------------

describe('walking forward through the second part', () => {
  it('visits the seven steps in order, each saying where in the part it is', async () => {
    await enterTheSocialSteps();

    for (const [index, step] of STEPS.entries()) {
      expect(screen).toHavePathname(step.path);
      expect(screen.getByText(step.title)).toBeTruthy();
      // Story 12: the player should know these screens end. Unlike the questionnaire, this
      // part can say how many there are, because six is six whatever anybody answers — and
      // the last one says it in words instead, because it is the one asking to finish.
      expect(screen.getByText(step.eyebrow)).toBeTruthy();

      if (index < STEPS.length - 1) {
        answerTheStep(index);
        fireEvent.press(await screen.findByLabelText(step.forward));
        await waitFor(() => expect(screen).toHavePathname(STEPS[index + 1]!.path));
      }
    }
  });

  it('ends at the last step, which finishes rather than continuing', async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(STEPS.length - 1);

    await waitFor(() => expect(screen).toHavePathname('/opt-in'));
    // Nothing in front of it: what follows the last step is the commit, and a commit is not
    // a screen. So there is no *Continue* here — the one control that leaves is the finish.
    expect(screen.queryByLabelText('Continue')).toBeNull();
    expect(screen.getByLabelText(STEPS[6]!.forward)).toBeTruthy();
  });

  it('will not finish a part that walked past the area, and offers the way back to it', async () => {
    // This walk pressed *Continue without matching* on step four, which is allowed and is
    // the cost that step names. The commit is where it is collected: finding players near
    // you works from one thing, and a profile without it takes part in nothing. So the part
    // insists once more, here, with the way back one press away — rather than trapping the
    // player on step four behind an OS prompt.
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(STEPS.length - 1);
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));

    // Answered either way — so what is holding the finish is not the consent question.
    fireEvent.press(screen.getByLabelText(OPT_IN.yes));

    const finish = screen.getByLabelText(STEPS[6]!.forward);
    expect(finish.props.accessibilityState?.disabled).toBe(true);
    // Not merely grey: the reason is on screen, and it is readable without sight.
    expect(finish.props.accessibilityHint).toBe('Set the area you play in to finish');
    expect(screen.getByText('We still need the area you play in')).toBeTruthy();

    // And nothing was sent. A part that cannot be committed does not half-commit.
    expect(transport.requests.filter((request) => request.method === 'POST')).toEqual([]);

    fireEvent.press(screen.getByLabelText('Set the area you play in'));
    await waitFor(() => expect(screen).toHavePathname('/location'));
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
      answerTheStep(index - 1);
      await continueFrom(index - 1);
      await waitFor(() => expect(screen).toHavePathname(STEPS[index]!.path));
      expect(screen.getByLabelText(STEPS[index]!.back!)).toBeTruthy();
    }
  });

  it('leads from every step to the one before it, all the way back to the first', async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(STEPS.length - 1);
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

    // Forward to the end, then all the way back to where the answer was given.
    for (let step = 2; step < STEPS.length; step += 1) {
      answerTheStep(step - 1);
      await continueFrom(step - 1);
      await waitFor(() => expect(screen).toHavePathname(STEPS[step]!.path));
    }
    for (let index = STEPS.length - 1; index > ANSWERED_STEP; index -= 1) {
      fireEvent.press(screen.getByLabelText(STEPS[index]!.back!));
      await waitFor(() => expect(screen).toHavePathname(STEPS[index - 1]!.path));
    }

    expect(screen).toHavePathname(STEPS[ANSWERED_STEP]!.path);
    // Both tags still picked, and the continue no longer asking for a floor that is met.
    expect((await screen.findByLabelText('Plays to win')).props.accessibilityState?.selected).toBe(
      true,
    );
    expect(screen.getByLabelText('Here to improve').props.accessibilityState?.selected).toBe(true);
    expect(screen.getByLabelText('Continue')).toBeTruthy();
  });

  it("keeps each step's answer to itself", async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(STEPS.length - 1);

    // The last step is unanswered, and answering it must not have been done on its behalf
    // by the five before it — nothing is claimed for a player who has not said it, and on
    // this one that is the difference between a consent record and a guess.
    expect(screen.getByLabelText(OPT_IN.yes).props.accessibilityState?.selected).toBe(false);
    expect(screen.getByLabelText(OPT_IN.no).props.accessibilityState?.selected).toBe(false);
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
      await continueFrom(step - 1);
      await waitFor(() => expect(screen).toHavePathname(STEPS[step]!.path));
    }
    answerTheStep(STEPS.length - 1);

    const afterArrival = transport.requests.slice(onArrival);

    // The part is the checkpoint unit: **nothing is written until the one commit at the
    // end**, which is why moving between steps is free in both directions and why leaving
    // restarts at step one. Not one write, in either direction, on any of the seven.
    //
    // A photo is the one thing the part does send, and only when a player adds one — the
    // bytes go up as they are picked and become part of a profile when the commit names
    // them. This walk adds none, so nothing leaves here at all.
    expect(afterArrival.filter((request) => request.method !== 'GET')).toEqual([]);

    // And the only things read are who the player is — which step two's court poster is
    // drawn from, through the auth feature's own query rather than a second one against the
    // same route — and the served options, which step one's chips and step five's slider
    // are both built from.
    //
    // Neither count is pinned, because neither can be: the router harness runs on fake
    // timers and `waitFor` advances them, so Query's five-minute collection can fire
    // mid-walk and either read happens once, twice or not at all. What must not change is
    // that there is nothing *else* in the list.
    const READ_ON_THE_WAY = ['/api/v1/users/me', PROFILE_OPTIONS_PATH];
    expect(afterArrival.filter((request) => !READ_ON_THE_WAY.includes(request.path))).toEqual([]);
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
    await walkOnTo(4);

    expect(screen).toHavePathname('/radius');
  });
});

describe('killing the app mid-part', () => {
  it('restarts at the first step with nothing answered, and the rating untouched', async () => {
    await enterTheSocialSteps();
    await continueFromTheFirstStep();
    await walkOnTo(STEPS.length - 1);
    answerTheStep(STEPS.length - 1);
    expect(screen.getByLabelText(OPT_IN.yes).props.accessibilityState?.selected).toBe(true);

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

/**
 * Onboarding's second part, walked through the real route tree and the network boundary.
 *
 * The same harness every onboarding flow suite uses — only `fetch` is faked, and the
 * router, the http client, the hooks, the store and the screens all run for real. What is
 * being proved here is the walk itself: six routes in one order, a draft that survives
 * moving between them in both directions, and a part that cannot be entered from its
 * middle. What each step *asks* is not built yet, and that is the point of landing the
 * skeleton first.
 *
 * Every assertion is about what a player can see, where they land, or what left the device.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { launchSignedIn, stubGate as stubGateWith } from '@/test-support/onboardingRouter';
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

/** The six steps in order, with the back control each one offers. */
const STEPS = [
  { path: '/tags', title: 'What kind of player are you?', back: undefined },
  { path: '/photos', title: 'Add a photo', back: 'Back to What kind of player are you?' },
  { path: '/availability', title: 'When do you usually play?', back: 'Back to Add a photo' },
  { path: '/location', title: 'Where do you play?', back: 'Back to When do you usually play?' },
  { path: '/radius', title: 'How far will you travel?', back: 'Back to Where do you play?' },
  { path: '/opt-in', title: 'May we suggest games?', back: 'Back to How far will you travel?' },
] as const;

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

/** A launch by a player the gate owes the second part to, landing on its first step. */
async function enterTheSocialSteps() {
  stubGate({ ratings: [RATING], hasPlayerProfile: false });

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
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
      expect(screen.getByText(`Setting up · Step ${index + 1} of 6`)).toBeTruthy();

      if (index < STEPS.length - 1) {
        fireEvent.press(screen.getByLabelText('Continue'));
        await waitFor(() => expect(screen).toHavePathname(STEPS[index + 1]!.path));
      }
    }
  });

  it('ends at the last step rather than navigating on to something that does not exist', async () => {
    await enterTheSocialSteps();
    for (let step = 1; step < STEPS.length; step += 1) {
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

    for (let index = 1; index < STEPS.length; index += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
      await waitFor(() => expect(screen).toHavePathname(STEPS[index]!.path));
      expect(screen.getByLabelText(STEPS[index]!.back!)).toBeTruthy();
    }
  });

  it('leads from every step to the one before it, all the way back to the first', async () => {
    await enterTheSocialSteps();
    for (let step = 1; step < STEPS.length; step += 1) {
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
    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/photos'));

    fireEvent.press(screen.getByLabelText('Answer this step'));
    expect(await screen.findByLabelText('Answered')).toBeTruthy();

    // Forward to the end, then all the way back.
    for (let step = 2; step < STEPS.length; step += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
    }
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));
    for (let index = STEPS.length - 1; index > 1; index -= 1) {
      fireEvent.press(screen.getByLabelText(STEPS[index]!.back!));
      await waitFor(() => expect(screen).toHavePathname(STEPS[index - 1]!.path));
    }

    expect(screen).toHavePathname('/photos');
    expect(screen.getByLabelText('Answered')).toBeTruthy();
  });

  it("keeps each step's answer to itself", async () => {
    await enterTheSocialSteps();
    fireEvent.press(screen.getByLabelText('Answer this step'));
    expect(await screen.findByLabelText('Answered')).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/photos'));

    // The next step is unanswered, and answering it must not have been done on its behalf
    // by the step before — nothing is claimed for a player who has not said it.
    expect(screen.getByLabelText('Answer this step')).toBeTruthy();
  });

  it('sends nothing to the server anywhere in the part', async () => {
    await enterTheSocialSteps();
    // Everything the gate asked on the way in. What the part itself costs is measured from
    // here — counting writes only would let a step that started *reading* pass.
    const onArrival = transport.requests.length;

    for (let step = 1; step < STEPS.length; step += 1) {
      fireEvent.press(screen.getByLabelText('Answer this step'));
      fireEvent.press(screen.getByLabelText('Continue'));
      await waitFor(() => expect(screen).toHavePathname(STEPS[step]!.path));
    }
    fireEvent.press(screen.getByLabelText('Answer this step'));

    // The part is the checkpoint unit: nothing is written until the one commit at the end,
    // which is why moving between steps is free in both directions and why leaving restarts
    // at step one. The commit is a later ticket, so today the whole part is silent — not
    // one request, in either direction, on any of the six.
    expect(transport.requests.slice(onArrival)).toEqual([]);
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

    await launchSignedIn('/radius');

    await waitFor(() => expect(screen).toHavePathname('/tags'));
    expect(screen.getByText('Setting up · Step 1 of 6')).toBeTruthy();
  });

  it('is not turned away once the player is genuinely inside the part', async () => {
    // The other half of the same rule, and the one that must not regress: reaching step
    // five by walking there is exactly what the part is for.
    await enterTheSocialSteps();

    for (let step = 1; step <= 4; step += 1) {
      fireEvent.press(screen.getByLabelText('Continue'));
      await waitFor(() => expect(screen).toHavePathname(STEPS[step]!.path));
    }

    expect(screen).toHavePathname('/radius');
  });
});

describe('killing the app mid-part', () => {
  it('restarts at the first step with nothing answered, and the rating untouched', async () => {
    await enterTheSocialSteps();
    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/photos'));
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
    expect(screen.getByLabelText('Answer this step')).toBeTruthy();
    expect(screen.queryByLabelText('Answered')).toBeNull();
  });
});

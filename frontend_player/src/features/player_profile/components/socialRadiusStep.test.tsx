/**
 * The radius step, driven through the real route tree with only the socket faked.
 *
 * The router, the http client, the domain rules, the draft and the screen all run for real.
 * Every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told — the figure on screen *is* the draft's answer, so nothing
 * here reads the store.
 *
 * **Two of these are the ticket rather than the screen.** The control has to be operable
 * without a drag, because a drag-only slider is unusable with a screen reader and with a
 * keyboard; and none of the four numbers may be this app's, because they are served,
 * re-validated on the write path, and product's to retune without a client release. So one
 * suite here retunes them and expects the screen to follow.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  PROFILE_OPTIONS_SERVED,
  launchSignedIn,
  stubGate as stubGateWith,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { useProfileDraft } from '../store/profileDraft.store';

import { RADIUS_LABEL } from './radiusPresentation';

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

let transport: Transport;

/** The slider itself, which is the only thing on this screen a player operates. */
const theSlider = () => screen.getByLabelText(RADIUS_LABEL);

/**
 * The figure, or the plain words, as a pair of eyes finds them.
 *
 * Both are drawn for whoever is looking and **hidden from whoever is listening**: the
 * control announces the two of them as one value, and read again on the way past they
 * would be a second and a third reading of the same number. So these are looked for past
 * the accessibility tree — which is exactly the claim, rather than a way around it.
 */
const drawn = (text: string) => screen.getByText(text, { includeHiddenElements: true });

/** The same, waited for — the bounds are a query, and a step re-entered asks for them again. */
const findDrawn = (text: string) => screen.findByText(text, { includeHiddenElements: true });

/** What the control announces it holds, which is the value rather than its drawing. */
const announced = () => theSlider().props.accessibilityValue;

function adjust(action: 'increment' | 'decrement') {
  fireEvent(theSlider(), 'accessibilityAction', { nativeEvent: { actionName: action } });
}

/** A launch by a player the gate owes the second part to, walked as far as step five. */
async function reachTheRadiusStep(served?: Wire['PlayerProfileOptionsResponse']) {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport, served);

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/photos'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/availability'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/location'));
  fireEvent.press(screen.getByLabelText('Continue without matching'));

  await waitFor(() => expect(screen).toHavePathname('/radius'));
  await screen.findByLabelText(RADIUS_LABEL);
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useProfileDraft.getState().reset();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

describe('what the step opens at', () => {
  it('shows the served default as a figure and in plain words', async () => {
    await reachTheRadiusStep();

    // Story 64: a sensible default, so the step can be passed without a decision.
    expect(drawn('10 km')).toBeTruthy();
    // Story 63: a number in kilometres means nothing to a player who does not think in
    // kilometres, so the same distance is said twice.
    expect(drawn('Across your town')).toBeTruthy();
  });

  /**
   * The whole point of the four served numbers. A build that hardcoded 1, 50 and 10 would
   * pass every other assertion in this file and fail this one.
   */
  it('opens wherever the server says, not where this build was written', async () => {
    await reachTheRadiusStep({
      ...PROFILE_OPTIONS_SERVED,
      search_radius: { minimum_km: 5, maximum_km: 40, step_km: 5, default_km: 25 },
    });

    expect(drawn('25 km')).toBeTruthy();
    expect(announced()).toEqual({
      min: 5,
      max: 40,
      now: 25,
      text: '25 kilometres, your town and the ones around it',
    });
  });

  /**
   * The bounds are editable server-side without a client release, and nothing there forces
   * the step to divide the range: 2 + 5n reaches 17 and then 22, so a maximum of 21 is a
   * radius no player may hold. What the control announces has to be one they can.
   */
  it('announces a maximum a player can actually be driven to', async () => {
    await reachTheRadiusStep({
      ...PROFILE_OPTIONS_SERVED,
      search_radius: { minimum_km: 2, maximum_km: 21, step_km: 5, default_km: 7 },
    });

    expect(announced().max).toBe(17);

    for (let press = 0; press < 4; press += 1) adjust('increment');
    expect(announced().now).toBe(17);
  });

  it('can be passed without touching the slider at all', async () => {
    await reachTheRadiusStep();

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));
  });
});

describe('operating it without a drag', () => {
  /**
   * The thing sliders universally get wrong. A control that can only be dragged is
   * unusable with a screen reader and with a hardware keyboard, so the two actions are the
   * mechanism rather than a courtesy.
   */
  it('offers an increment and a decrement, each moving exactly one served step', async () => {
    await reachTheRadiusStep();

    expect(theSlider().props.accessibilityRole).toBe('adjustable');
    expect(theSlider().props.accessibilityActions).toEqual([
      { name: 'increment', label: 'Further out' },
      { name: 'decrement', label: 'Closer in' },
    ]);

    adjust('increment');
    expect(drawn('11 km')).toBeTruthy();

    adjust('decrement');
    adjust('decrement');
    expect(drawn('9 km')).toBeTruthy();
  });

  it('moves by the served step rather than by a kilometre it chose itself', async () => {
    await reachTheRadiusStep({
      ...PROFILE_OPTIONS_SERVED,
      search_radius: { minimum_km: 5, maximum_km: 40, step_km: 5, default_km: 25 },
    });

    adjust('increment');
    expect(drawn('30 km')).toBeTruthy();
  });

  /** Nowhere past an end to go, and going nowhere is not going outside the served range. */
  it('stops at each end of the served range', async () => {
    await reachTheRadiusStep({
      ...PROFILE_OPTIONS_SERVED,
      search_radius: { minimum_km: 5, maximum_km: 15, step_km: 5, default_km: 10 },
    });

    adjust('increment');
    adjust('increment');
    adjust('increment');
    // The announced value rather than the figure: at the top of the range the figure and
    // the box reserving its width say the same thing, which is the reservation working.
    expect(announced().now).toBe(15);

    for (let press = 0; press < 5; press += 1) adjust('decrement');
    expect(announced().now).toBe(5);
  });

  /**
   * The figure and the words are one fact drawn twice, so they are announced as one value.
   * Read as two, they would say the control has two.
   */
  it('announces the figure and the words as one value, and keeps it current', async () => {
    await reachTheRadiusStep();

    adjust('decrement');
    drawn('9 km');

    expect(announced()).toEqual({
      min: 1,
      max: 50,
      now: 9,
      text: '9 kilometres, across your town',
    });
  });

  it('changes the plain-word reading when the distance becomes a different kind of decision', async () => {
    await reachTheRadiusStep({
      ...PROFILE_OPTIONS_SERVED,
      search_radius: { minimum_km: 1, maximum_km: 50, step_km: 1, default_km: 3 },
    });

    expect(drawn('A short ride away')).toBeTruthy();

    adjust('increment');
    adjust('increment');
    adjust('increment');
    expect(drawn('6 km')).toBeTruthy();
    expect(drawn('Across your town')).toBeTruthy();
  });
});

describe('the answer the part holds', () => {
  /**
   * Story 10, on the step that has a default: walking back to check something and forward
   * again must not quietly reset a number the player chose.
   */
  it('is still there after walking away from the step and back to it', async () => {
    await reachTheRadiusStep();

    adjust('increment');
    adjust('increment');
    expect(drawn('12 km')).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));

    fireEvent.press(screen.getByLabelText('Back to How far will you travel?'));
    await waitFor(() => expect(screen).toHavePathname('/radius'));

    // Awaited, not read: the bounds are a query with no observer while the player is on
    // step six, so re-entering the step asks for them again. The *answer* is the draft's
    // and never went anywhere — which is the whole assertion.
    expect(await findDrawn('12 km')).toBeTruthy();
  });
});

describe('what the step says the number does', () => {
  /**
   * The glossary's whole point: the radius **filters when the player searches and weights
   * when the engine proposes**. Saying only the first would let a player set a small radius
   * believing it removes them from everything; saying only the second would make the
   * control look advisory when a search obeys it exactly.
   */
  it('says both of the things the same number does', async () => {
    await reachTheRadiusStep();

    expect(screen.getByText(/nobody further out comes back/)).toBeTruthy();
    expect(screen.getByText(/players closer to you come first/)).toBeTruthy();
  });
});

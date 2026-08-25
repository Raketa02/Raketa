/**
 * The Proposals opt-in step, driven through the real route tree with only the socket faked.
 *
 * The router, the http client, the domain rule, the draft and the screen all run for real.
 * Almost every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told.
 *
 * **The one exception reads the store, and it is the reason this step exists.** The copy
 * version stamped beside the answer is deliberately never drawn — it is an identifier for a
 * consent record, not a sentence for a player — so *is the wording captured with the
 * answer* has no on-screen form to assert. Reading the draft is the only way to prove it,
 * and the alternative is to prove nothing.
 *
 * The other suite this file leans on is `optInPresentation.test.ts`, which guards the words
 * themselves: this one proves they reach the screen, that one proves they are the approved
 * ones and that the card promises nothing the switch does not deliver.
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

import {
  OPT_IN_FINISH_LABEL,
  OPT_IN_PROMISES,
  PROPOSALS_OPT_IN_COPY_VERSION,
  optInAnswerLabel,
} from './optInPresentation';

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

const YES = optInAnswerLabel(true);
const NO = optInAnswerLabel(false);

const control = (label: string) => screen.getByLabelText(label);
const isSelected = (label: string) => control(label).props.accessibilityState?.selected;
const finish = () => control(OPT_IN_FINISH_LABEL);

/** What the part is holding, which for this step is the half that is never drawn. */
const recorded = () => useProfileDraft.getState().draft?.proposalsOptIn;

/** A launch by a player the gate owes the second part to, walked to the last of the six. */
async function reachTheOptInStep() {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);

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
  fireEvent.press(await screen.findByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/opt-in'));
  await screen.findByLabelText(OPT_IN_FINISH_LABEL);
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

describe('what the step opens with', () => {
  /**
   * The invariant the whole screen is built around: **never pre-ticked**. A control drawn
   * already chosen would make the record evidence of a press nobody made.
   */
  it('has neither answer selected, and nothing in the draft', async () => {
    await reachTheOptInStep();

    expect(isSelected(YES)).toBe(false);
    expect(isSelected(NO)).toBe(false);
    // Absent, not `false`. A recorded refusal and an unasked question are different facts.
    expect(recorded()).toBeUndefined();
  });

  it('keeps the finish closed until the player has answered', async () => {
    await reachTheOptInStep();

    expect(finish().props.accessibilityState?.disabled).toBe(true);
    // Not merely grey: a player who cannot see the control is told why it will not move.
    expect(finish().props.accessibilityHint).toBe('Choose yes or no above to finish');
  });

  /**
   * Story: there is one way past this screen and it is an answer. A skip, a dismiss, a
   * close or a decide-later would produce a player who is neither opted in nor opted out,
   * and someone downstream would have to guess which.
   */
  it('offers no way past it that is not an answer', async () => {
    await reachTheOptInStep();

    expect(screen.queryByLabelText(/skip/i)).toBeNull();
    expect(screen.queryByLabelText(/dismiss/i)).toBeNull();
    expect(screen.queryByLabelText(/close/i)).toBeNull();
    expect(screen.queryByLabelText(/later/i)).toBeNull();
    expect(screen.queryByText(/maybe later/i)).toBeNull();
    // Back is the part's own move and reaches the step before this one, never past it.
    expect(screen.getByLabelText('Back to How far will you travel?')).toBeTruthy();
  });
});

describe('answering it', () => {
  it('records yes with the words it was given against, and opens the finish', async () => {
    await reachTheOptInStep();

    fireEvent.press(control(YES));

    expect(isSelected(YES)).toBe(true);
    expect(isSelected(NO)).toBe(false);
    expect(finish().props.accessibilityState?.disabled).toBe(false);
    // The copy version is the evidence half of the answer and travels with it, always.
    expect(recorded()).toEqual({ accepted: true, copyVersion: PROPOSALS_OPT_IN_COPY_VERSION });
  });

  /**
   * **No is a complete answer, not an abandoned setup.** A finish that stayed shut on a
   * refusal would be the product withholding the rest of itself until it got the answer it
   * wanted, which is the failure this card's copy is written against.
   */
  it('records no exactly as completely, and opens the finish just the same', async () => {
    await reachTheOptInStep();

    fireEvent.press(control(NO));

    expect(isSelected(NO)).toBe(true);
    expect(finish().props.accessibilityState?.disabled).toBe(false);
    expect(recorded()).toEqual({ accepted: false, copyVersion: PROPOSALS_OPT_IN_COPY_VERSION });
  });

  it('lets the player change their mind before finishing, and the last answer wins', async () => {
    await reachTheOptInStep();

    fireEvent.press(control(YES));
    fireEvent.press(control(NO));

    expect(isSelected(NO)).toBe(true);
    expect(isSelected(YES)).toBe(false);
    expect(recorded()?.accepted).toBe(false);

    fireEvent.press(control(YES));
    expect(recorded()?.accepted).toBe(true);
  });

  /**
   * Design-system 13 and the acceptance criterion together: selection reaches a screen
   * reader as **state**, and the sighted half is the chip's ink fill — a luminance
   * inversion rather than a change of hue. Neither half is the whole fact, and the state is
   * announced whether or not the answer is the selected one, so *not chosen* is
   * distinguishable from *not a choice*.
   */
  it('announces the answer as state rather than leaving it to the fill', async () => {
    await reachTheOptInStep();

    expect(isSelected(YES)).toBe(false);
    expect(isSelected(NO)).toBe(false);

    fireEvent.press(control(YES));

    expect(isSelected(YES)).toBe(true);
    expect(isSelected(NO)).toBe(false);
  });

  it('is still there after walking back to the step before it and returning', async () => {
    await reachTheOptInStep();
    fireEvent.press(control(NO));

    fireEvent.press(control('Back to How far will you travel?'));
    await waitFor(() => expect(screen).toHavePathname('/radius'));
    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));

    expect(isSelected(NO)).toBe(true);
    expect(isSelected(YES)).toBe(false);
  });
});

describe('the card the answer is given against', () => {
  it('makes each promise as one thing to read rather than two halves', async () => {
    await reachTheOptInStep();

    for (const promise of OPT_IN_PROMISES) {
      expect(control(`${promise.term} ${promise.detail}`)).toBeTruthy();
    }
  });

  /**
   * The load-bearing correction. Without it the card reads as *disappear or be suggested
   * to*, which is a choice nobody is being offered — **opting out stops the engine pushing,
   * not the player existing.**
   */
  it('says what saying no leaves untouched', async () => {
    await reachTheOptInStep();

    expect(screen.getByText(/You stay findable in search either way/)).toBeTruthy();
  });

  it('says beside the controls that neither was ticked for the player', async () => {
    await reachTheOptInStep();

    expect(screen.getByText('Never pre-ticked. Skipping is not consent.')).toBeTruthy();
  });
});

describe('what the step sends', () => {
  it('sends nothing at all, whichever answer is given', async () => {
    await reachTheOptInStep();
    const onArrival = transport.requests.length;

    fireEvent.press(control(YES));
    fireEvent.press(control(NO));
    fireEvent.press(finish());

    // The part is the checkpoint unit: the answer joins the client-held draft and the whole
    // of it goes in one commit at the end. Nothing here writes, and the finish that will is
    // its own ticket.
    expect(transport.requests.slice(onArrival).filter((r) => r.method !== 'GET')).toEqual([]);
  });
});

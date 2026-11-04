/**
 * The intro step, driven through the real route tree with only `fetch` faked.
 *
 * The same harness the rest of onboarding uses: the router, the store, the draft and the
 * screen all run. What is being proved is what a player can see and operate on **this**
 * screen — the counter, the two shape refusals the step will not let past, and the two
 * controls' names. What the line does at the commit, and the three refusals the server
 * sends back, are `commitTheProfile.test.tsx`'s; the walk is `socialSteps.test.tsx`'s.
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

import { INTRO_CAP } from '../domain/intro';
import { useProfileDraft } from '../store/profileDraft.store';

import { INTRO_FIELD_LABEL, INTRO_NEXT_LABEL, INTRO_SKIP_LABEL } from './introPresentation';

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

const box = () => screen.getByLabelText(INTRO_FIELD_LABEL);
const next = () => screen.getByLabelText(INTRO_NEXT_LABEL);
const write = (line: string) => fireEvent.changeText(box(), line);

/** Through the tags — the only door in — to the step under test. */
async function reachTheIntroStep() {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/intro'));
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

describe('what the step offers', () => {
  it('names the box, counts from nought, and offers Next and Skip side by side', async () => {
    await reachTheIntroStep();

    expect(screen.getByText('Say it in your own words')).toBeTruthy();
    expect(screen.getByText('Setting up · Step 2 of 6')).toBeTruthy();
    // The label is drawn and is the name, never a placeholder that vanishes on the first
    // keystroke.
    expect(screen.getByText('Your intro')).toBeTruthy();
    expect(box().props.accessibilityHint).toBe('One line, up to 250 characters. Optional.');
    expect(screen.getByText('0 / 250')).toBeTruthy();
    expect(screen.getByLabelText('0 of 250 characters')).toBeTruthy();

    // Both, whatever is in the box: the step is optional and the screen says so by offering
    // the way past rather than by leaving Next open on an empty box and hoping.
    expect(next().props.accessibilityState?.disabled).toBe(false);
    expect(next().props.accessibilityHint).toBe('Goes to Your court photos');
    expect(screen.getByLabelText(INTRO_SKIP_LABEL).props.accessibilityHint).toBe(
      'Goes to Your court photos with no intro',
    );
  });

  it('draws no paragraph of rules — the contact rule is said only when it is broken', async () => {
    // ADR-0200 §9: the rule line under the box is gone. A phone number is refused with the
    // refusal's own sentence, at the commit or on You's save, and only to somebody who typed one.
    await reachTheIntroStep();

    expect(screen.queryByText(/Other players read this on your card/)).toBeNull();
    expect(screen.queryByText(/Leave out phone numbers/)).toBeNull();
  });
});

describe('the counter', () => {
  it('counts what is typed, in characters and not in bytes', async () => {
    await reachTheIntroStep();

    write('Moved from Wrocław in May.');
    expect(screen.getByText('26 / 250')).toBeTruthy();

    // An emoji is one character to the server and two units to JavaScript; the counter
    // agrees with the server, so a line of them reads as the length the cap is read against.
    write('🎾🎾🎾');
    expect(screen.getByText('3 / 250')).toBeTruthy();
  });

  it('counts the line as the cap reads it, so the spaces around it are not counted', async () => {
    // The counter and the refusal read the same trimmed line: 250 characters wrapped
    // in spaces is at the cap and says so, rather than reading `254 / 250` beside an open
    // Next.
    await reachTheIntroStep();

    write(`  ${'a'.repeat(INTRO_CAP)}  `);

    expect(screen.getByText('250 / 250')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(next().props.accessibilityState?.disabled).toBe(false);
  });
});

describe('a line at the cap', () => {
  it('takes 250 characters, counts them all, and lets the line through', async () => {
    await reachTheIntroStep();
    const atTheCap = 'a'.repeat(INTRO_CAP);

    write(atTheCap);

    expect(INTRO_CAP).toBe(250);
    expect(screen.getByText('250 / 250')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    fireEvent.press(next());
    await waitFor(() => expect(screen).toHavePathname('/photos'));
    expect(useProfileDraft.getState().draft?.intro).toBe(atTheCap);
  });
});

describe('a line the server would refuse on shape', () => {
  it('shuts Next on one over the cap, says so under the box, and keeps counting', async () => {
    await reachTheIntroStep();

    write('a'.repeat(INTRO_CAP + 3));

    // The box took the whole paste — nothing was swallowed — and the sentence under it is
    // the refusal's own, as an alert. The counter shows the overrun rather than clamping.
    expect(box().props.value).toHaveLength(INTRO_CAP + 3);
    expect(screen.getByText('253 / 250')).toBeTruthy();
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByText('Keep it under 250 characters.')).toBeTruthy();
    expect(next().props.accessibilityState?.disabled).toBe(true);
    // A blocked control names what is wrong rather than merely being grey.
    expect(next().props.accessibilityHint).toBe('Keep it under 250 characters.');

    // Trimmed to the cap, it opens again with nothing said.
    write('a'.repeat(INTRO_CAP));
    expect(screen.queryByRole('alert')).toBeNull();
    expect(next().props.accessibilityState?.disabled).toBe(false);
  });

  it('shuts Next on a pasted line break, in the other sentence', async () => {
    await reachTheIntroStep();

    write('Two games in.\nStill learning the city.');

    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByText('One line, no line breaks.')).toBeTruthy();
    expect(next().props.accessibilityState?.disabled).toBe(true);
  });

  it('lets Skip past a refused line, and clears it on the way', async () => {
    // Skip is never shut: a player who pasted too much and would rather write nothing has
    // the way past, and what they skipped is gone rather than carried.
    await reachTheIntroStep();
    write('a'.repeat(INTRO_CAP + 1));

    fireEvent.press(screen.getByLabelText(INTRO_SKIP_LABEL));
    await waitFor(() => expect(screen).toHavePathname('/photos'));

    expect(useProfileDraft.getState().draft?.intro).toBe('');
  });
});

describe('the line in the draft', () => {
  it('is held as typed, and is still there after a round trip to the next step', async () => {
    await reachTheIntroStep();
    write('Will travel for a hard game. ');

    fireEvent.press(next());
    await waitFor(() => expect(screen).toHavePathname('/photos'));
    fireEvent.press(screen.getByLabelText('Back to Say it in your own words'));
    await waitFor(() => expect(screen).toHavePathname('/intro'));

    // Untrimmed: the box is exactly as it was left, and the trimming is the commit's. The
    // counter reads the line and not the box, so the trailing space is not in it.
    expect(box().props.value).toBe('Will travel for a hard game. ');
    expect(screen.getByText('28 / 250')).toBeTruthy();
  });
});

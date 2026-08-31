/**
 * The shell, walked the way a player walks it: through the real route tree, with the real
 * bar, and only `fetch` faked.
 *
 * **The one rule here that cannot be seen is the one this suite exists for.** A shell built
 * out of `<Tabs>` passes every visible assertion below and still fails *back goes where I
 * came from* — the tab bar looks right, every screen is reachable, nothing throws, and a
 * player who left the deck and came back lands on the deck. So the assertions are about the
 * **stack**: what is underneath, and whether there is anything underneath at all.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { GATE_USER, launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { enterPlay } from './shellNavigation';
import { FIND_A_GAME_COPY, PLACEHOLDER_COPY } from './shellCopy';

/** One rating and a committed profile: the gate's fourth answer is *the app*. */
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

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A player standing on the tab the entry gate lands them on. */
async function launchIntoTheApp() {
  await launchSignedIn();
  expect(await screen.findByText(PLACEHOLDER_COPY.now.line)).toBeTruthy();
}

/** Press one of the five columns by the name the bar gives it. */
function pressTab(label: string) {
  fireEvent.press(screen.getByLabelText(label));
}

describe('what a player lands on', () => {
  it('opens on Now, with the bar under it', async () => {
    await launchIntoTheApp();

    expect(screen).toHavePathname('/');
    expect(screen.getAllByRole('tab').map((tab) => tab.props.accessibilityLabel)).toEqual([
      'Now',
      'Around',
      'Play',
      'Chats',
      'You',
    ]);
  });

  it('lights the tab the player is on, and only that one', async () => {
    await launchIntoTheApp();

    const selected = () =>
      screen
        .getAllByRole('tab')
        .filter((tab) => tab.props.accessibilityState?.selected === true)
        .map((tab) => tab.props.accessibilityLabel);

    expect(selected()).toEqual(['Now']);

    pressTab('Chats');
    await waitFor(() => expect(selected()).toEqual(['Chats']));
  });
});

describe('the four placeholders', () => {
  it.each([
    ['Around', PLACEHOLDER_COPY.around],
    ['Chats', PLACEHOLDER_COPY.chats],
    ['You', PLACEHOLDER_COPY.you],
  ])('says what belongs on %s rather than apologising', async (label, copy) => {
    await launchIntoTheApp();

    pressTab(label);

    expect(await screen.findByText(copy.line)).toBeTruthy();
  });

  it('never tells the player nothing is happening', async () => {
    // Now is where a send lands, so a placeholder asserting emptiness would be lying one tap
    // after a challenge went out. What the lines *say* is `shellCopy.test.ts`'s; this is the
    // rendered half — the tab a launch actually opens on, with the sentence on it.
    await launchIntoTheApp();

    expect(screen.queryByText(/nothing is happening/i)).toBeNull();
  });

  it('keeps the way out of a session on You, where it belongs', async () => {
    // The account panel outlived the screen it used to be: sign-out is the only way back
    // to the beginning, and the tab whose citation is *your profile* is where it goes.
    await launchIntoTheApp();

    pressTab('You');

    expect(await screen.findByText(PLACEHOLDER_COPY.you.line)).toBeTruthy();
    expect(await screen.findByText(`${GATE_USER.nickname} · ${GATE_USER.email}`)).toBeTruthy();
    expect(screen.getByLabelText('Sign out')).toBeTruthy();
  });

  it('lets a player out of the session from inside the shell', async () => {
    // The one flow the shell moved: sign-out used to be the screen a player landed on, and
    // is now three screens inside a stack the guard has to unwind from.
    transport.on('POST', '/api/v1/auth/logout', () => json({ message: 'Logged out' }));
    await launchIntoTheApp();

    pressTab('You');
    fireEvent.press(await screen.findByLabelText('Sign out'));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  });
});

describe('⚡Play', () => {
  it('always opens Find a game, from whichever tab the player was on', async () => {
    await launchIntoTheApp();

    pressTab('Around');
    await waitFor(() => expect(screen).toHavePathname('/around'));

    pressTab('Play');

    expect(await screen.findByText(FIND_A_GAME_COPY.line)).toBeTruthy();
    expect(screen).toHavePathname('/play');
  });

  it('stays lit for the screen it opened', async () => {
    await launchIntoTheApp();

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    const play = screen.getAllByRole('tab')[2];
    expect(play?.props.accessibilityState?.selected).toBe(true);
  });

  it('leaves Now underneath, so back leaves Play entirely', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    // The platform's own back, which is what the rule is about: Find a game does not refuse
    // to be the last screen, it has Now underneath it.
    act(() => router.back());

    expect(await screen.findByText(PLACEHOLDER_COPY.now.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('is entered the same way from inside the tab as from the bar', async () => {
    // The reset's second caller. #268's *Find a game* segment re-enters the tab from inside
    // it, and re-entering has to mean the arrangement arriving means — otherwise a player on
    // the deck who taps it goes *back* rather than to the start.
    await launchIntoTheApp();
    pressTab('Chats');
    await waitFor(() => expect(screen).toHavePathname('/chats'));

    act(() => enterPlay());

    expect(await screen.findByText(FIND_A_GAME_COPY.line)).toBeTruthy();
    expect(screen).toHavePathname('/play');
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
  });

  it('re-enters rather than going back when it is pressed from inside Play', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    // And the stack has not grown a second Find a game to walk back through.
    expect(router.canGoBack()).toBe(true);
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(router.canGoBack()).toBe(false);
  });
});

describe('the shell keeps no per-tab history', () => {
  it('leaves nothing behind a flanking tab', async () => {
    await launchIntoTheApp();

    pressTab('Around');

    await waitFor(() => expect(screen).toHavePathname('/around'));
    // Not `[Now, Around]`: switching tabs replaces, so there is no cross-tab back to walk.
    expect(router.canGoBack()).toBe(false);
  });

  it('throws away Play depth when the player leaves, and does not restore it', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('Chats');
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    // Play's two screens went with it. This is the assertion `<Tabs>` fails silently.
    expect(router.canGoBack()).toBe(false);

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
  });
});

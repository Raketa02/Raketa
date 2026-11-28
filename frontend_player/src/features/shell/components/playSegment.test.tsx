/**
 * **Play's two segments, walked** — Groups | Explore, and the phone remembering which one a player
 * left it on ([#512](https://github.com/Rakieta02/Rakieta/issues/512),
 * [ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)).
 *
 * The real route tree and the real shell, with only the socket faked. *A relaunch* is the process
 * ending and a new one starting: the Query cache and the session go, and what is saved on the
 * device — the keychain, the phone's preferences and the last good datafile — stays.
 *
 * **Every walk runs with `explore` served on** ([#826](https://github.com/Rakieta02/Rakieta/issues/826)):
 * the switcher is drawn only on an explicit on, and off is the gate's suite
 * (`theExploreGate.test.tsx`). `launchWithExplore` serves it and waits on it before Play is pressed,
 * because Play reads the feature flag once, when it mounts.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { FIND_A_GAME_NEXT_TEST_ID } from '@/features/find_a_game_next/types';
import { endSession, clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  launchWithExplore,
  stubGate,
  stubProfileOptions,
  stubProfileSurface,
  type GateStub,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { PLAY_COPY } from './shellCopy';

const PADEL_RATING: Wire['RatingResponse'] = {
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

/** Somebody else, signing in on the same phone. */
const BORIS = '99999999-8888-4777-8666-555555555555';

let transport: Transport;

function stubAPlayer(overrides: GateStub = {}) {
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true, ...overrides });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
}

beforeEach(() => {
  transport = installTransport();
  stubAPlayer();
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

async function relaunch() {
  screen.unmount();
  queryClient.clear();
  resetSessionStatus();
  await launchWithExplore(transport);
}

async function pressPlay() {
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

const segment = (name: string, selected: boolean) =>
  screen.findByRole('button', { name, selected });

async function expectGroups() {
  expect(await segment(PLAY_COPY.segment.groups, true)).toBeTruthy();
  expect(screen.queryByTestId(FIND_A_GAME_NEXT_TEST_ID)).toBeNull();
}

async function expectExplore() {
  expect(await segment(PLAY_COPY.segment.explore, true)).toBeTruthy();
  expect(screen.getByTestId(FIND_A_GAME_NEXT_TEST_ID)).toBeTruthy();
}

describe('Play’s segments', () => {
  it('opens on Groups', async () => {
    await launchWithExplore(transport);

    await pressPlay();

    await expectGroups();
    expect(await segment(PLAY_COPY.segment.explore, false)).toBeTruthy();
  });

  it('draws Explore as a blank page, and goes back to Groups', async () => {
    await launchWithExplore(transport);
    await pressPlay();
    await expectGroups();

    fireEvent.press(screen.getByRole('button', { name: PLAY_COPY.segment.explore }));
    await expectExplore();

    fireEvent.press(screen.getByRole('button', { name: PLAY_COPY.segment.groups }));
    await expectGroups();
  });

  it('comes back on the segment the player left, after the app is closed', async () => {
    await launchWithExplore(transport);
    await pressPlay();
    fireEvent.press(await segment(PLAY_COPY.segment.explore, false));
    await expectExplore();

    await relaunch();
    await pressPlay();

    await expectExplore();
  });

  it('comes back on it when the player leaves the tab and returns', async () => {
    await launchWithExplore(transport);
    await pressPlay();
    fireEvent.press(await segment(PLAY_COPY.segment.explore, false));
    await expectExplore();

    fireEvent.press(screen.getByLabelText('Home'));
    await waitFor(() => expect(screen).toHavePathname('/'));
    await pressPlay();

    await expectExplore();
  });
});

describe('what the phone remembers, and for whom', () => {
  it('starts somebody else on this phone on Groups', async () => {
    await savePhonePreference(GATE_USER.id, 'playSegment', 'explore');
    stubAPlayer({ id: BORIS });

    await launchWithExplore(transport);
    await pressPlay();

    await expectGroups();
  });

  it('forgets the segment when the player signs out', async () => {
    await launchWithExplore(transport);
    await pressPlay();
    fireEvent.press(await segment(PLAY_COPY.segment.explore, false));
    await expectExplore();

    screen.unmount();
    await endSession('requested');
    queryClient.clear();
    resetSessionStatus();
    await launchWithExplore(transport);
    await pressPlay();

    await expectGroups();
  });

  // ADR-0188 §4: a value this build does not recognise is the default, never an error.
  it('opens on Groups when what was saved is not a segment', async () => {
    await savePhonePreference(GATE_USER.id, 'playSegment', 'find-a-game');

    await launchWithExplore(transport);
    await pressPlay();

    await expectGroups();
  });
});

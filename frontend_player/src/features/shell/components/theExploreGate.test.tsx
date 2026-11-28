/**
 * **Play's Explore, behind `explore`** — the *Groups | Explore* switcher drawn only on an explicit
 * **on**, through the real route tree, the real shell and the real Featurevisor SDK, with the
 * datafile stubbed at the socket exactly as every API response is
 * ([#826](https://github.com/Rakieta02/Rakieta/issues/826),
 * [ADR-0206](../../../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)).
 *
 * **Off is the code default**, and off is Play titled *Groups* over the groups list, with no
 * switcher and no way into Explore. So every walk that proves a *saved* datafile is still in force
 * saves **on** and expects the switcher: with the default off, a walk that saved off would pass
 * with the saved copy broken.
 *
 * What is asserted is what a player could see — the title or the switcher, which segment is lit,
 * and whether Explore's page is drawn — and what the phone still holds. How the SDK was called is
 * not, and neither is which players a rule reaches: the flags repo's specs own that.
 *
 * Every walk waits on the datafile before it presses Play. The gate reads its feature flag once,
 * when Play mounts, so a datafile still in flight at that moment is — correctly — the next rung
 * down, and a walk that raced it would be asserting the race.
 */

import { focusManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { FIND_A_GAME_NEXT_TEST_ID } from '@/features/find_a_game_next/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import {
  DATAFILE_PATH,
  GATE_USER,
  datafileFor,
  datafileSettled,
  launchSignedIn,
  stubDatafile,
  stubGate,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { PLAY_COPY } from './shellCopy';

const ON = datafileFor({ explore: 'on' });
const OFF = datafileFor({ explore: 'off' });

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

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A cold launch into the app, with the datafile answered before anything is asked of it. */
async function launch(datafiles = 1) {
  await launchSignedIn();
  await datafileSettled(transport, datafiles);
}

/**
 * The process ends and a new one starts: the Query cache and the session go, and what is saved on
 * the device — the keychain, the phone's preferences and the last good datafile — stays.
 */
async function relaunch(datafiles: number) {
  screen.unmount();
  queryClient.clear();
  resetSessionStatus();
  await launch(datafiles);
}

/** The app comes back to the front, which is when a running app fetches the datafile again. */
async function foreground(datafiles: number) {
  act(() => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
  });
  await datafileSettled(transport, datafiles);
}

async function pressPlay() {
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

async function leaveForHome() {
  fireEvent.press(screen.getByLabelText('Home'));
  await waitFor(() => expect(screen).toHavePathname('/'));
}

const segmentNamed = (name: string) => screen.queryByRole('button', { name });

/**
 * **Off**: the Administrator's Groups pattern — the title *Groups*, a header to a listener, over
 * the groups list with + New and Join in it, and no switcher and no Explore.
 */
async function expectGroupsTitled() {
  expect(await screen.findByRole('header', { name: PLAY_COPY.title })).toBeTruthy();
  expect(segmentNamed(PLAY_COPY.segment.groups)).toBeNull();
  expect(segmentNamed(PLAY_COPY.segment.explore)).toBeNull();
  expect(screen.getByTestId('groups-list')).toBeTruthy();
  expect(screen.getByRole('button', { name: 'New group' })).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Join a group' })).toBeTruthy();
  expect(screen.queryByTestId(FIND_A_GAME_NEXT_TEST_ID)).toBeNull();
}

/** **On**: today's Play — the switcher, Groups first, on the segment named. */
async function expectSwitcherOn(selected: 'groups' | 'explore') {
  const lit = PLAY_COPY.segment[selected];
  expect(await screen.findByRole('button', { name: lit, selected: true })).toBeTruthy();

  const segments = screen
    .getAllByRole('button')
    .map((button) => button.props.accessibilityLabel)
    .filter((label) => label === PLAY_COPY.segment.groups || label === PLAY_COPY.segment.explore);
  expect(segments).toEqual([PLAY_COPY.segment.groups, PLAY_COPY.segment.explore]);
  expect(screen.queryByRole('header', { name: PLAY_COPY.title })).toBeNull();

  if (selected === 'explore') {
    expect(screen.getByTestId(FIND_A_GAME_NEXT_TEST_ID)).toBeTruthy();
  } else {
    expect(screen.queryByTestId(FIND_A_GAME_NEXT_TEST_ID)).toBeNull();
  }
}

describe('Play, by what the datafile says', () => {
  // A first launch with the flags host unreachable and nothing saved: the app as it ships.
  it('is titled Groups, with no switcher, when nothing is served', async () => {
    await launch();

    await pressPlay();

    await expectGroupsTitled();
  });

  it('is titled Groups, with no switcher, when Explore is off', async () => {
    stubDatafile(transport, OFF);
    await launch();

    await pressPlay();

    await expectGroupsTitled();
  });

  it('brings the switcher back, Groups first, when Explore is on', async () => {
    stubDatafile(transport, ON);
    await launch();

    await pressPlay();

    await expectSwitcherOn('groups');
  });
});

/**
 * **A saved `explore` is read past, and never written** (ADR-0188's choice stays the player's): off,
 * Play shows Groups and the phone still holds `explore`; on, it opens on Explore, which is *on
 * means today*.
 */
describe('the segment the phone remembers', () => {
  it('shows Groups over a saved Explore while it is off, and leaves the saved choice alone', async () => {
    await savePhonePreference(GATE_USER.id, 'playSegment', 'explore');
    await launch();

    await pressPlay();
    await expectGroupsTitled();
    await leaveForHome();
    await pressPlay();
    await expectGroupsTitled();

    expect(await readPhonePreference(GATE_USER.id, 'playSegment')).toBe('explore');
  });

  it('opens on a saved Explore when it is on', async () => {
    await savePhonePreference(GATE_USER.id, 'playSegment', 'explore');
    stubDatafile(transport, ON);
    await launch();

    await pressPlay();

    await expectSwitcherOn('explore');
  });
});

describe('a change that arrives while Play is on screen', () => {
  /**
   * Explore never appears under the player's thumb, and the change is clean the next time they open
   * the tab. It arrives the way it does on a device — the app comes back to the front and fetches
   * again.
   */
  it('takes effect at Play’s next mount, not before', async () => {
    await launch();
    await pressPlay();
    await expectGroupsTitled();

    stubDatafile(transport, ON);
    await foreground(2);

    await expectGroupsTitled();

    await leaveForHome();
    await pressPlay();

    await expectSwitcherOn('groups');
  });
});

/**
 * ADR-0206 §10: a format this build does not read is refused, and whichever datafile was in force
 * stays in force — the saved one, or else the code default. Each refused datafile says the
 * opposite of what is expected, so a refusal that was read would fail the walk.
 */
describe('a datafile in a format this build does not read', () => {
  it('leaves the saved datafile in force', async () => {
    stubDatafile(transport, ON);
    await launch();

    stubDatafile(transport, datafileFor({ explore: 'off' }, { schemaVersion: '3' }));
    await relaunch(2);
    await pressPlay();

    await expectSwitcherOn('groups');
  });

  it('leaves the code default in force when nothing is saved', async () => {
    stubDatafile(transport, datafileFor({ explore: 'on' }, { schemaVersion: '3' }));
    await launch();

    await pressPlay();

    await expectGroupsTitled();
  });

  it('keeps the datafile fetched earlier when a later one is refused mid-session', async () => {
    stubDatafile(transport, ON);
    await launch();

    transport.on('GET', DATAFILE_PATH, () =>
      json(datafileFor({ explore: 'off' }, { schemaVersion: '3' })),
    );
    await foreground(2);
    await pressPlay();

    await expectSwitcherOn('groups');
  });
});

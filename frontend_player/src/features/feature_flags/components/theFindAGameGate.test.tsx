/**
 * **The first gate, walked** — Find a game behind `find_a_game`, through the real route tree, the
 * real shell and the real Featurevisor SDK, with the datafile stubbed at the socket exactly as
 * every API response is ([#479](https://github.com/Raketa02/Raketa/issues/479),
 * [ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)).
 *
 * What is asserted is what a player could see: which screen the Play tab draws, and where a route
 * under it lands. How the SDK was called is not, and neither is which players a rule reaches — the
 * flags repo's specs own that. The one rule here that names a player is the tester walk, and it is
 * about the app sending the mark, not about the rule.
 *
 * Every walk waits on the datafile before it mounts the screen it asks about. A gate reads its flag
 * once, when it mounts, so a datafile still in flight at that moment is — correctly — the next rung
 * down, and a walk that raced it would be asserting the race.
 */

import { focusManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { FIND_A_GAME_NEXT_TEST_ID } from '@/features/find_a_game_next/types';
import { FIND_A_GAME_TITLE, endPlaySession } from '@/features/play/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  DATAFILE_PATH,
  datafileFor,
  datafileSettled,
  launchSignedIn,
  stubDatafile,
  stubGate,
  stubProfileOptions,
  stubProfileSurface,
  type GateStub,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

const ON = datafileFor({ find_a_game: 'on' });
const OFF = datafileFor({ find_a_game: 'off' });

/** A search id that survives the builder's and the pool's param checks, and that nobody ran. */
const SOME_SEARCH = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';

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
  endPlaySession();
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
 * the device — the keychain, and the last good datafile — stays.
 */
async function relaunch(datafiles: number) {
  screen.unmount();
  queryClient.clear();
  resetSessionStatus();
  await launch(datafiles);
}

async function pressPlay() {
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

async function expectFindAGame() {
  expect(await screen.findByText(FIND_A_GAME_TITLE)).toBeTruthy();
  expect(screen.queryByTestId(FIND_A_GAME_NEXT_TEST_ID)).toBeNull();
}

async function expectThePlaceholder() {
  expect(await screen.findByTestId(FIND_A_GAME_NEXT_TEST_ID)).toBeTruthy();
  expect(screen.queryByText(FIND_A_GAME_TITLE)).toBeNull();
}

describe('the Play tab, by what the datafile says', () => {
  it('shows Find a game when the feature is on', async () => {
    stubDatafile(transport, ON);
    await launch();

    await pressPlay();

    await expectFindAGame();
  });

  // A first launch with the flags host unreachable and nothing saved: the app as it ships.
  it('shows Find a game when there is no datafile and nothing cached', async () => {
    await launch();

    await pressPlay();

    await expectFindAGame();
  });

  it('shows the empty placeholder when the feature is off, and keeps the tab bar', async () => {
    stubDatafile(transport, OFF);
    await launch();

    await pressPlay();

    await expectThePlaceholder();
    // Story 23: an empty screen, not a dead end — every column is still there to leave by.
    expect(screen.getByLabelText('Play')).toBeTruthy();
    expect(screen.getByLabelText(/^Chats/)).toBeTruthy();
  });

  /**
   * The mark is the one context attribute read off the player's own account (ADR-0180 §9). A
   * datafile that keeps the feature from the testers and gives it to everyone else can only answer
   * *off* here if the app told it this player is one.
   */
  it('sends the tester mark to the evaluation', async () => {
    stubAPlayer({ isTester: true });
    stubDatafile(
      transport,
      datafileFor(
        {},
        {
          segments: {
            testers: { conditions: [{ attribute: 'isTester', operator: 'equals', value: true }] },
          },
          features: {
            find_a_game: {
              bucketBy: 'playerId',
              traffic: [
                { key: 'testers', segments: 'testers', percentage: 0 },
                { key: 'everyone', segments: '*', percentage: 100000 },
              ],
            },
          },
        },
      ),
    );
    await launch();

    await pressPlay();

    await expectThePlaceholder();
  });
});

/**
 * A link to the builder or the pool with **no search behind it** — nothing on the Play tab could
 * have started one while the feature is off. A search the player already ran is let through, and
 * `play/components/pool.test.tsx` walks that half: the toggle arriving mid-search.
 */
describe('the routes under Play while the feature is off', () => {
  beforeEach(() => stubDatafile(transport, OFF));

  it('sends a link to the builder back to Play', async () => {
    await launch();

    act(() => router.push({ pathname: '/play/builder', params: { search: SOME_SEARCH } }));

    await waitFor(() => expect(screen).toHavePathname('/play'));
    await expectThePlaceholder();
  });

  it('sends a link to the pool back to Play', async () => {
    await launch();

    act(() => router.push({ pathname: '/play/pool', params: { search: SOME_SEARCH, seat: '1' } }));

    await waitFor(() => expect(screen).toHavePathname('/play'));
    await expectThePlaceholder();
  });
});

describe('a change that arrives while Play is on screen', () => {
  /**
   * Story 21 and 22: the screen is not pulled out from under the player, and the change is clean
   * the next time they open the tab. The toggle arrives the way it does on a device — the app
   * comes back to the front and fetches again.
   */
  it('takes effect at the next mount, not before', async () => {
    stubDatafile(transport, ON);
    await launch();
    await pressPlay();
    await expectFindAGame();

    stubDatafile(transport, OFF);
    act(() => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
    });
    await datafileSettled(transport, 2);

    await expectFindAGame();

    fireEvent.press(screen.getByLabelText('Now'));
    await waitFor(() => expect(screen).toHavePathname('/'));
    await pressPlay();

    await expectThePlaceholder();
  });
});

describe('when the fresh datafile cannot be used', () => {
  /** The last good datafile was saved by an earlier launch — this walk's first. */
  async function aLaunchThatSavedOff() {
    stubDatafile(transport, OFF);
    await launch();
    await pressPlay();
    await expectThePlaceholder();
  }

  it('uses the cached datafile when the fetch fails', async () => {
    await aLaunchThatSavedOff();

    transport.on('GET', DATAFILE_PATH, networkFailure());
    await relaunch(2);
    await pressPlay();

    await expectThePlaceholder();
  });

  // ADR-0180 §10: a format this build does not read is refused, and the last good one stays. Were
  // it read, this one would turn Find a game back on.
  it('falls back to the cache when the schema version is unknown', async () => {
    await aLaunchThatSavedOff();

    stubDatafile(transport, datafileFor({ find_a_game: 'on' }, { schemaVersion: '3' }));
    await relaunch(2);
    await pressPlay();

    await expectThePlaceholder();
  });

  it('keeps the datafile fetched earlier when a later one is refused mid-session', async () => {
    stubDatafile(transport, OFF);
    await launch();

    transport.on('GET', DATAFILE_PATH, () =>
      json(datafileFor({ find_a_game: 'on' }, { schemaVersion: '3' })),
    );
    act(() => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
    });
    await datafileSettled(transport, 2);
    await pressPlay();

    await expectThePlaceholder();
  });
});

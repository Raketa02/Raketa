/**
 * **Classic play, walked** — the old loop behind `classic_play`, through the real route tree, the
 * real shell and the real Featurevisor SDK, with the datafile stubbed at the socket exactly as
 * every API response is ([#550](https://github.com/Raketa02/Raketa/issues/550),
 * [ADR-0189](../../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §6,
 * [ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)).
 *
 * It was the first gate's suite — Find a game behind `find_a_game` (#479) — and the flag grew into
 * the one that brings the whole old loop back: the bar's Players and Chats columns and Play's Find
 * a game, together. So there are two things to watch, read two ways. **The bar follows the flag**:
 * it is mounted before any datafile has been read and stays mounted, so it changes when one lands.
 * **Play's root reads it once, when it mounts**, and changes at the next entry to the tab.
 *
 * **Off is the code default**, and off is Home · Play · You over Play › Groups. So every walk that
 * proves a *cached* or *refused* datafile is still in use saves **on** and expects the old loop:
 * with the default off, a walk that saved off would pass with the cache broken.
 *
 * What is asserted is what a player could see: which columns the bar draws, which screen the Play
 * tab draws, and where a route under it lands. How the SDK was called is not, and neither is which
 * players a rule reaches — the flags repo's specs own that. The one rule here that names a player
 * is the tester walk, and it is about the app sending the mark, not about the rule.
 *
 * Every walk about Play waits on the datafile before it mounts the screen it asks about. A gate
 * reads its flag once, when it mounts, so a datafile still in flight at that moment is — correctly
 * — the next rung down, and a walk that raced it would be asserting the race.
 */

import { focusManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { FIND_A_GAME_TITLE, endPlaySession } from '@/features/play/types';
import { PLAY_COPY } from '@/features/shell/types';
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

const ON = datafileFor({ classic_play: 'on' });
const OFF = datafileFor({ classic_play: 'off' });

/** The bar as it ships, and the bar with the old loop back. */
const SHIPPED_BAR = ['Home', 'Play', 'You'];
const CLASSIC_BAR = ['Home', 'Players', 'Play', 'Chats', 'You'];

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

/** The app comes back to the front, which is when a running app fetches the datafile again. */
async function foreground(datafiles: number) {
  act(() => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
  });
  await datafileSettled(transport, datafiles);
}

/** Every column the bar draws, by the name it speaks. */
function bar(): string[] {
  return screen.getAllByRole('tab').map((tab) => tab.props.accessibilityLabel);
}

async function pressPlay() {
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

async function expectFindAGame() {
  expect(await screen.findByText(FIND_A_GAME_TITLE)).toBeTruthy();
  expect(screen.queryByRole('button', { name: PLAY_COPY.segment.groups })).toBeNull();
}

/** Play › Groups — what the tab opens on with Classic play off (#512). */
async function expectGroups() {
  expect(
    await screen.findByRole('button', { name: PLAY_COPY.segment.groups, selected: true }),
  ).toBeTruthy();
  expect(screen.queryByText(FIND_A_GAME_TITLE)).toBeNull();
}

describe('the bar, by what the datafile says', () => {
  // A first launch with the flags host unreachable and nothing saved: the app as it ships.
  it('is Home, Play and You when there is no datafile and nothing cached', async () => {
    await launch();

    expect(bar()).toEqual(SHIPPED_BAR);
  });

  it('is Home, Play and You when Classic play is off', async () => {
    stubDatafile(transport, OFF);
    await launch();

    expect(bar()).toEqual(SHIPPED_BAR);
  });

  it('brings Players and Chats back, in their places, when Classic play is on', async () => {
    stubDatafile(transport, ON);
    await launch();

    await waitFor(() => expect(bar()).toEqual(CLASSIC_BAR));
  });

  it('opens the deck and the inbox from the two columns it brings back', async () => {
    stubDatafile(transport, ON);
    transport.on('POST', '/api/v1/deck', () => json(NOBODY_DEALT));
    await launch();

    fireEvent.press(await screen.findByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));

    fireEvent.press(screen.getByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(screen.getByRole('tab', { name: 'Chats', selected: true })).toBeTruthy();
  });

  /**
   * **The bar is chrome, not a gated screen, and it follows the flag.** Nothing is pulled out from
   * under the player — Find a game stays on screen, read when it mounted — and the columns change
   * the moment the datafile reaches the app, which is ADR-0180's *next cold start or foreground*.
   */
  it('follows a change that arrives while the app is open, and leaves the screen alone', async () => {
    stubDatafile(transport, ON);
    await launch();
    await pressPlay();
    await expectFindAGame();
    expect(bar()).toEqual(CLASSIC_BAR);

    stubDatafile(transport, OFF);
    await foreground(2);

    await waitFor(() => expect(bar()).toEqual(SHIPPED_BAR));
    await expectFindAGame();
  });

  it('keeps the old loop’s columns from the cached datafile when the fetch fails', async () => {
    stubDatafile(transport, ON);
    await launch();
    await waitFor(() => expect(bar()).toEqual(CLASSIC_BAR));

    transport.on('GET', DATAFILE_PATH, networkFailure());
    await relaunch(2);

    await waitFor(() => expect(bar()).toEqual(CLASSIC_BAR));
  });
});

describe('the Play tab, by what the datafile says', () => {
  it('shows Find a game when Classic play is on', async () => {
    stubDatafile(transport, ON);
    await launch();

    await pressPlay();

    await expectFindAGame();
  });

  it('shows Groups when there is no datafile and nothing cached', async () => {
    await launch();

    await pressPlay();

    await expectGroups();
  });

  it('shows Groups when Classic play is off, and keeps the tab bar', async () => {
    stubDatafile(transport, OFF);
    await launch();

    await pressPlay();

    await expectGroups();
    // Every column the bar draws is still there to leave by.
    expect(bar()).toEqual(SHIPPED_BAR);
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
            classic_play: {
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

    await expectGroups();
    expect(bar()).toEqual(SHIPPED_BAR);
  });
});

/**
 * A link to the builder or the pool with **no search behind it** — nothing on the Play tab could
 * have started one while Classic play is off. A search the player already ran is let through, and
 * `play/components/pool.test.tsx` walks that half: the toggle arriving mid-search.
 */
describe('the routes under Play while Classic play is off', () => {
  beforeEach(() => stubDatafile(transport, OFF));

  it('sends a link to the builder back to Play', async () => {
    await launch();

    act(() => router.push({ pathname: '/play/builder', params: { search: SOME_SEARCH } }));

    await waitFor(() => expect(screen).toHavePathname('/play'));
    await expectGroups();
  });

  it('sends a link to the pool back to Play', async () => {
    await launch();

    act(() => router.push({ pathname: '/play/pool', params: { search: SOME_SEARCH, seat: '1' } }));

    await waitFor(() => expect(screen).toHavePathname('/play'));
    await expectGroups();
  });
});

describe('a change that arrives while Play is on screen', () => {
  /**
   * Story 21 and 22: the screen is not pulled out from under the player, and the change is clean
   * the next time they open the tab. The toggle arrives the way it does on a device — the app
   * comes back to the front and fetches again.
   */
  it('takes effect on Play at the next mount, not before', async () => {
    stubDatafile(transport, ON);
    await launch();
    await pressPlay();
    await expectFindAGame();

    stubDatafile(transport, OFF);
    await foreground(2);

    await expectFindAGame();

    fireEvent.press(screen.getByLabelText('Home'));
    await waitFor(() => expect(screen).toHavePathname('/'));
    await pressPlay();

    await expectGroups();
  });
});

/**
 * Each of these saves **on**, because on is the one answer only a datafile can give: with the
 * code default off, a walk that saved off would pass with the cache broken.
 */
describe('when the fresh datafile cannot be used', () => {
  /** The last good datafile was saved by an earlier launch — this walk's first. */
  async function aLaunchThatSavedOn() {
    stubDatafile(transport, ON);
    await launch();
    await pressPlay();
    await expectFindAGame();
  }

  it('uses the cached datafile when the fetch fails', async () => {
    await aLaunchThatSavedOn();

    transport.on('GET', DATAFILE_PATH, networkFailure());
    await relaunch(2);
    await pressPlay();

    await expectFindAGame();
  });

  // ADR-0180 §10: a format this build does not read is refused, and the last good one stays. Were
  // it read, this one would turn Classic play off.
  it('falls back to the cache when the schema version is unknown', async () => {
    await aLaunchThatSavedOn();

    stubDatafile(transport, datafileFor({ classic_play: 'off' }, { schemaVersion: '3' }));
    await relaunch(2);
    await pressPlay();

    await expectFindAGame();
    expect(bar()).toEqual(CLASSIC_BAR);
  });

  it('keeps the datafile fetched earlier when a later one is refused mid-session', async () => {
    stubDatafile(transport, ON);
    await launch();

    transport.on('GET', DATAFILE_PATH, () =>
      json(datafileFor({ classic_play: 'off' }, { schemaVersion: '3' })),
    );
    await foreground(2);
    await pressPlay();

    await expectFindAGame();
    expect(bar()).toEqual(CLASSIC_BAR);
  });
});

/** An empty deal with nobody in range: Players draws its ending, and this suite is not about it. */
const NOBODY_DEALT: Wire['ShortlistResponse'] = {
  search: {
    search_id: 'd0d1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b',
    at: '2026-09-01T18:00:00Z',
    surface: 'DECK',
    mode: null,
    ruleset_version: 'ruleset-v1',
    engine_version: 'matchfit-v1',
    optimised_for: 'SEARCHER',
    index_stale: false,
    pool: {
      sport: 'PADEL',
      radius_km_used: 12,
      players_in_range: 0,
      window: 'THIS_WEEK',
      post_gate: true,
    },
    radius_clamp: false,
    sorts_available: [],
    rung_offers: null,
    prompts: [],
  },
  candidates: [],
};

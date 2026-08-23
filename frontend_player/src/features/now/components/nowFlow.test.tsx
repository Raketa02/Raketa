/**
 * Now, driven through the real route tree and the network boundary.
 *
 * The same shape as the onboarding suite, and deliberately the same shape: only
 * `fetch` is faked. The router, the http client, its timeouts, error mapping, the
 * mappers, the use-cases, the hooks, the store and the screens all run for real,
 * so a pass here means the screen works end to end minus the socket.
 *
 * **Every assertion is about what a player can see or what left the device.** The
 * four asks are asserted on the transport's transcript, because *how often the app
 * talks to the server* is the whole of `ADR-0054` and is invisible from the render
 * tree.
 *
 * `renderRouter` installs jest's fake timers, which is what makes the fourth ask —
 * a countdown reaching zero — assertable at all: the clock can be moved to a
 * moment the server named, and the transcript read on either side of it.
 */

import { focusManager, onlineManager } from '@tanstack/react-query';
import { RefreshControl } from 'react-native';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { router } from 'expo-router';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  clubCard,
  emptyNow,
  matchCard,
  nowPathFor,
  personCard,
  shelf,
  stubNow,
} from '@/test-support/now';
import { launchSignedIn, stubGate as stubGateWith } from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { nowKeys } from '../hooks/nowKeys';
import { useSportFilterStore } from '../store/sportFilter.store';

import { REGION_ID } from './NowRegions';
import { SHIMMER_ID } from './NowShimmer';

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

const NOW_ALL = nowPathFor('all');
const NOW_SQUASH = nowPathFor('SQUASH');

let transport: Transport;

/** How many times the whole screen has been composed for the default chip. */
const composes = () => transport.requestsTo('GET', NOW_ALL).length;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useSportFilterStore.getState().reset();
  focusManager.setFocused(true);
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

/** A signed-in, already-rated player: the gate's `app` outcome, which is Now. */
async function launchOnNow(body: Wire['NowResponse'] = emptyNow()) {
  stubGateWith(transport, { ratings: [RATING] });
  stubNow(transport, body);

  await launchSignedIn();
  await screen.findByTestId(REGION_ID.yourMatches);
}

// ---------------------------------------------------------------------------
// The screen
// ---------------------------------------------------------------------------

describe('Now is the app’s home', () => {
  it('is what a signed-in, rated player lands on', async () => {
    await launchOnNow();

    expect(screen).toHavePathname('/');
    expect(screen.getByText('Your matches')).toBeTruthy();
  });

  it('renders all three regions present and empty for a player with nothing', async () => {
    // `ADR-0070`: a shelf with nothing is absent, a *region* with nothing is present
    // and empty — one code path, and a shape she recognises rather than a blank page.
    await launchOnNow();

    expect(screen.getByTestId(REGION_ID.offers)).toBeTruthy();
    expect(screen.getByTestId(REGION_ID.yourMatches)).toBeTruthy();
    expect(screen.getByTestId(REGION_ID.shelves)).toBeTruthy();

    expect(screen.getByText('No matches booked')).toBeTruthy();
    expect(screen.getByText('Nothing open in your sports right now')).toBeTruthy();
  });

  it('draws a card in each region from the composed answer', async () => {
    await launchOnNow({
      offers: {
        stamp: 1,
        cards: [matchCard({ matchId: 'offer-1', situation: 'seatOffered' })],
      },
      your_matches: {
        stamp: 1,
        cards: [matchCard({ matchId: 'mine-1', situation: 'confirmed' })],
      },
      shelves: {
        stamp: 1,
        shelves: [
          shelf('bestFit', [matchCard({ matchId: 'feed-1', situation: 'forming' })]),
          shelf('newPlayers', [personCard('p-1', 'ada')]),
          shelf('newClubs', [clubCard('c-9', 'Kraków Padel')]),
        ],
      },
      debt: null,
    });

    // The situation's sentence, from the client's own table — no copy crosses the wire.
    expect(
      screen.getByText('A seat is being offered to you — nobody else can take it for the hour.'),
    ).toBeTruthy();
    // The shelf's title, from its code — likewise.
    expect(screen.getByText('Best fit for you')).toBeTruthy();
    expect(screen.getByText('New on Raketa')).toBeTruthy();
    expect(screen.getByText('ada')).toBeTruthy();
    expect(screen.getByText('Kraków Padel')).toBeTruthy();
  });

  it('draws the spine and drops the status line for a situation it has never heard of', async () => {
    // An old phone meeting a thirty-seventh name. It never skips the card: an app
    // hiding a match the player has paid for reads as *your app lost my booking*.
    await launchOnNow({
      ...emptyNow(),
      your_matches: {
        stamp: 1,
        cards: [
          {
            ...matchCard({ matchId: 'mine-1' }),
            situation: {
              situation: 'seatTransferred' as Wire['Situation'],
              facts: { hold: null, cause: null },
            },
          },
        ],
      },
    });

    // The spine: the club and the price are still there.
    expect(screen.getByText(/Sunset Padel/)).toBeTruthy();
    expect(screen.getByText(/38,00/)).toBeTruthy();
    // And nothing pretends to name the situation.
    expect(screen.queryByText('Forming')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The four asks, and nothing else
// ---------------------------------------------------------------------------

describe('the four asks', () => {
  it('composes on arrival — a cold open', async () => {
    await launchOnNow();

    expect(composes()).toBe(1);
  });

  it('composes when the app comes back to the foreground', async () => {
    await launchOnNow();

    act(() => focusManager.setFocused(false));
    act(() => focusManager.setFocused(true));

    await waitFor(() => expect(composes()).toBe(2));
  });

  it('composes on pull, and keeps the screen while it does', async () => {
    await launchOnNow({
      ...emptyNow(),
      your_matches: { stamp: 1, cards: [matchCard({ matchId: 'mine-1' })] },
    });

    fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');

    await waitFor(() => expect(composes()).toBe(2));
    // The screen is still there — a pull keeps what she is reading exactly where it
    // is and puts its indicator at the top. It is never the shimmer.
    expect(screen.queryByTestId(SHIMMER_ID)).toBeNull();
    expect(screen.getByTestId(REGION_ID.yourMatches)).toBeTruthy();
  });

  it('composes when an action invalidates the screen', async () => {
    // `ADR-0054`'s third ask. Nothing on this screen is an action yet — when the
    // routes that are (`#89`, `#91`, `#92`) land, they hand Now its update in their
    // own response and this becomes a cache write rather than a fetch.
    await launchOnNow();

    await act(async () => {
      await queryClient.invalidateQueries({ queryKey: nowKeys.all });
    });

    await waitFor(() => expect(composes()).toBe(2));
  });

  it('asks nothing when a route is popped back off', async () => {
    // Arrival is the app *foregrounding*, not a screen becoming visible. A screen
    // becoming visible again is not one of the four.
    await launchOnNow();

    act(() => router.push('/account'));
    await waitFor(() => expect(screen).toHavePathname('/account'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));

    expect(composes()).toBe(1);
  });

  it('asks nothing when the screen is left, unmounted, and returned to', () => {
    // The stronger half of the same rule, and the one a push/pop cannot reach:
    // pushing keeps Now mounted, so *mounting* is where the rule can quietly break.
    // Replacing the route destroys the screen, and coming back rebuilds it from the
    // cache without a request — a screen becoming visible is none of the four asks,
    // however it became visible.
    return (async () => {
      await launchOnNow();

      act(() => router.replace('/account'));
      await waitFor(() => expect(screen).toHavePathname('/account'));
      act(() => router.replace('/'));
      await screen.findByTestId(REGION_ID.yourMatches);

      expect(composes()).toBe(1);
    })();
  });
});

describe('a countdown reaching zero', () => {
  const MINUTE = 60 * 1000;
  const WINDOW = 2 * 60 * MINUTE;

  /**
   * The clock the fixtures are written against, and the drift the launch itself
   * costs.
   *
   * `renderRouter` runs on jest's fake timers, and every `waitFor` inside the
   * launch advances them — so *now* has moved by an unknown amount by the time the
   * screen is on screen. Measuring that once, here, is what makes the assertions
   * below about the countdown rather than about the harness.
   */
  const at = (base: number, offset: number) => new Date(base + offset).toISOString();

  it('produces no request at all until it lands, and exactly one when it does', async () => {
    const base = Date.now();

    await launchOnNow({
      ...emptyNow(),
      your_matches: {
        stamp: 1,
        cards: [matchCard({ matchId: 'mine-1', clock: at(base, WINDOW) })],
      },
    });

    expect(composes()).toBe(1);
    const drift = Date.now() - base;

    // All but the last minute of a two-hour window. Nothing ticks, nothing polls,
    // nothing asks — the transport's transcript is the assertion.
    await act(async () => {
      jest.advanceTimersByTime(WINDOW - drift - MINUTE);
    });
    expect(composes()).toBe(1);

    await act(async () => {
      jest.advanceTimersByTime(MINUTE);
    });
    await waitFor(() => expect(composes()).toBe(2));
  });

  it('watches a live seat claim’s five minutes as well as the card’s own clock', async () => {
    const base = Date.now();

    await launchOnNow({
      ...emptyNow(),
      offers: {
        stamp: 1,
        cards: [
          matchCard({
            matchId: 'offer-1',
            situation: 'seatOffered',
            clock: at(base, 12 * WINDOW),
            seatClaimExpiresAt: at(base, WINDOW),
          }),
        ],
      },
    });

    const drift = Date.now() - base;
    await act(async () => {
      jest.advanceTimersByTime(WINDOW - drift + MINUTE);
    });

    // The claim lapses first, so that is the ask — no precedence rule needed.
    await waitFor(() => expect(composes()).toBe(2));
  });

  it('asks nothing on a screen whose moments have all passed', async () => {
    const base = Date.now();

    await launchOnNow({
      ...emptyNow(),
      your_matches: {
        stamp: 1,
        cards: [matchCard({ matchId: 'mine-1', clock: at(base, -MINUTE) })],
      },
    });

    await act(async () => {
      jest.advanceTimersByTime(WINDOW);
    });

    expect(composes()).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Loading, and the staleness the screen never admits
// ---------------------------------------------------------------------------

describe('what loading looks like', () => {
  it('shows a shimmer on a cold open, with nothing restored from the last launch', async () => {
    stubGateWith(transport, { ratings: [RATING] });
    transport.on('GET', NOW_ALL, () => new Promise<Response>(() => {}));

    await launchSignedIn();

    expect(await screen.findByTestId(SHIMMER_ID)).toBeTruthy();
    // Nothing is tappable and no dead offer has been resurrected, because nothing
    // was kept: there is no cache persister anywhere in this app.
    expect(screen.queryByTestId(REGION_ID.shelves)).toBeNull();
  });

  it('says nothing at all about staleness when a refresh fails over a live screen', async () => {
    await launchOnNow({
      ...emptyNow(),
      your_matches: { stamp: 1, cards: [matchCard({ matchId: 'mine-1' })] },
    });

    // 403, not a 5xx: a 5xx is retried automatically, and this test is about what the
    // screen says rather than about the retry policy.
    transport.on('GET', NOW_ALL, () => errorResponse(403, 'forbidden'));
    fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    await waitFor(() => expect(composes()).toBeGreaterThan(1));

    // She keeps reading what she had. No marker, no dot, no banner.
    expect(screen.getByTestId(REGION_ID.yourMatches)).toBeTruthy();
    expect(screen.queryByTestId(SHIMMER_ID)).toBeNull();
  });

  it('says the screen did not load when a cold open fails, and offers the pull', async () => {
    stubGateWith(transport, { ratings: [RATING] });
    transport.on('GET', NOW_ALL, () => errorResponse(403, 'forbidden'));

    await launchSignedIn();

    expect(
      await screen.findByText('Something went wrong at our end. Pull down to try again.'),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The sport bar
// ---------------------------------------------------------------------------

describe('the sport bar', () => {
  it('is five fixed chips, whatever this player is rated at', async () => {
    // One rating, five chips. Hiding a sport hides the business; the lie a fixed row
    // tells survives exactly one tap, after which the door tells the truth (`#94`).
    await launchOnNow();

    for (const label of ['All', 'Padel', 'Tennis', 'Squash', 'Badminton']) {
      expect(screen.getByLabelText(label)).toBeTruthy();
    }
  });

  it('starts at All, and says so to a screen reader', async () => {
    await launchOnNow();

    expect(screen.getByRole('radio', { name: 'All', selected: true })).toBeTruthy();
    expect(screen.getByRole('radio', { name: 'Squash', selected: false })).toBeTruthy();
  });

  it('re-composes the whole screen for the chosen sport, strip included', async () => {
    // The filter applies to every region and shelf: one selection means one thing.
    // A switch is a **new request**, never a filter over a payload holding every
    // sport — so the strip changing is the proof that the server did the filtering.
    await launchOnNow({
      ...emptyNow(),
      your_matches: { stamp: 1, cards: [matchCard({ matchId: 'padel-1' })] },
    });

    stubNow(
      transport,
      {
        ...emptyNow(),
        your_matches: {
          stamp: 1,
          cards: [matchCard({ matchId: 'squash-1', clubName: 'Squash House' })],
        },
      },
      'SQUASH',
    );

    fireEvent.press(screen.getByRole('radio', { name: 'Squash' }));

    await waitFor(() => expect(transport.requestsTo('GET', NOW_SQUASH)).toHaveLength(1));
    expect(await screen.findByText('Squash House · indoor · 2,4 km')).toBeTruthy();
    expect(screen.queryByText('Sunset Padel · indoor · 2,4 km')).toBeNull();
    // And the empty city names the sport rather than "your sports".
    expect(screen.getByText('Nothing open in Squash right now')).toBeTruthy();
  });

  it('survives stepping out for two minutes', async () => {
    await launchOnNow();
    stubNow(transport, emptyNow(), 'SQUASH');
    fireEvent.press(screen.getByRole('radio', { name: 'Squash' }));
    await waitFor(() => expect(transport.requestsTo('GET', NOW_SQUASH)).toHaveLength(1));

    act(() => focusManager.setFocused(false));
    await act(async () => {
      jest.advanceTimersByTime(2 * 60 * 1000);
    });
    act(() => focusManager.setFocused(true));

    expect(screen.getByRole('radio', { name: 'Squash', selected: true })).toBeTruthy();
  });

  it('resets to All after half an hour away', async () => {
    // A remembered filter can hide a match she has paid for and is playing tomorrow.
    // That is a different class of mistake from showing her too much.
    await launchOnNow();
    stubNow(transport, emptyNow(), 'SQUASH');
    fireEvent.press(screen.getByRole('radio', { name: 'Squash' }));
    await waitFor(() => expect(transport.requestsTo('GET', NOW_SQUASH)).toHaveLength(1));

    act(() => focusManager.setFocused(false));
    await act(async () => {
      jest.advanceTimersByTime(31 * 60 * 1000);
    });
    act(() => focusManager.setFocused(true));

    await waitFor(() =>
      expect(screen.getByRole('radio', { name: 'All', selected: true })).toBeTruthy(),
    );
  });
});

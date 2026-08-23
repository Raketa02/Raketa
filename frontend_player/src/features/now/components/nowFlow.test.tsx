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
import { RefreshControl, StyleSheet } from 'react-native';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { router } from 'expo-router';

import { refreshTokens } from '@/features/auth/types';
import { FIT_BADGE_ID, theme } from '@/shared/ui';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  clubCard,
  door,
  emptyNow,
  fit,
  fitReason,
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

import { ACTION_ROW_ID } from './ActionRow';
import { CLOCK_ID } from './CardClock';
import { FIT_REASON_ID, FIT_WARNING_ID } from './NowCards';
import { DOOR_ID } from './NowDoor';
import { REGION_ID, TAIL_CARD_ID } from './NowRegions';
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
              facts: {
                counts: { seats: 4, paid: 2, held: 0, turned_up: null },
                court_total: { amount: 15200, currency: 'PLN' },
                hold: null,
                cause: null,
              },
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
// The door, as a block in the shelves list
// ---------------------------------------------------------------------------

describe('the door into an unrated sport', () => {
  /**
   * `ADR-0084` puts the door **in the shelves list, in order**. What this suite owns is
   * the drawing of it; the walk through the questionnaire it opens is onboarding's, in
   * `features/onboarding/components/theDoor.test.tsx`.
   */
  const withDoor = (code: Wire['DoorCode']): Wire['NowResponse'] => ({
    ...emptyNow(),
    shelves: { stamp: 1, shelves: [door(code), shelf('newClubs', [clubCard('c-9', 'Kraków')])] },
  });

  it('draws where it arrives, with the light shelf beneath it', async () => {
    await launchOnNow(withDoor('noRunYet'));

    expect(screen.getByTestId(DOOR_ID)).toBeTruthy();
    expect(screen.getByText('New clubs')).toBeTruthy();
  });

  it('draws no block at all for a code this build has never heard of', async () => {
    // What an old build gets, and what `ADR-0084` accepts when it puts the door *in* the
    // list: one entry missing from a list the phone already iterates. A card holding a
    // blank sentence over a button that says nothing is worse than the missing row — and
    // it is the shape a *nearly* tolerant renderer produces, so it is asserted as the
    // block's absence rather than as the absence of its words.
    await launchOnNow(withDoor('reRate' as Wire['DoorCode']));

    expect(screen.queryByTestId(DOOR_ID)).toBeNull();
    expect(screen.getByText('New clubs')).toBeTruthy();
  });

  it('draws none on a rated sport whose shelves are simply empty', async () => {
    // The inference `ADR-0053` leaves the phone no rules to draw: an empty city looks
    // identical from here, and only the server can tell the two apart.
    await launchOnNow();

    expect(screen.queryByTestId(DOOR_ID)).toBeNull();
    expect(screen.getByText('Nothing open in your sports right now')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The action row: three slots, zero variants
// ---------------------------------------------------------------------------

describe('the action row', () => {
  /** A screen holding exactly one card in the strip, so a query names one thing. */
  async function launchWithCard(card: Wire['MatchCardResponse']) {
    await launchOnNow({ ...emptyNow(), your_matches: { stamp: 1, cards: [card] } });
  }

  it('draws each slot exactly when its own field is present', async () => {
    // `ADR-0088`: one row, and each slot appears when its field is present. Three
    // fields, three slots, and no variant between them.
    await launchWithCard(
      matchCard({
        matchId: 'mine-1',
        situation: 'confirmed',
        clock: '2099-01-01T18:00:00Z',
        act: 'gettingIn',
        mayDepart: true,
      }),
    );

    expect(screen.getByTestId(CLOCK_ID)).toBeTruthy();
    expect(screen.getByLabelText('Getting in, Sunset Padel')).toBeTruthy();
    expect(screen.getByLabelText('Leave this match at Sunset Padel')).toBeTruthy();
  });

  it('draws none of them when the card carries none, and still renders the row', async () => {
    // The empty row is a zero-height spacer and not an omission: `native-kit.md`
    // §3 gives the row `marginTop: auto` so footers align across cards of differing
    // height, and an element that is not rendered pushes nothing — so the
    // twenty-six cards that name no act would get the slab of empty night back.
    await launchWithCard(matchCard({ matchId: 'mine-1', situation: 'forming' }));

    const row = screen.getByTestId(ACTION_ROW_ID);

    expect(row).toBeTruthy();
    expect(row.children).toHaveLength(0);
    expect(screen.queryByTestId(CLOCK_ID)).toBeNull();
    expect(screen.queryByRole('button', { name: /Take the seat/ })).toBeNull();
  });

  it('gives a card that names no act no button and no tappable body', async () => {
    // `ADR-0083`, restated by `ADR-0088`: twenty-six of the thirty-six name none,
    // and that is not a hole to be patched with a button opening something
    // irrelevant. The card itself is not a tap target either.
    await launchWithCard(matchCard({ matchId: 'mine-1', situation: 'rescue' }));

    expect(screen.getByText(/the seat stays funded/)).toBeTruthy();
    expect(screen.queryAllByRole('button')).toHaveLength(0);
  });

  it('never draws a control the situation alone would imply', async () => {
    // The act is a **spine** fact. `forming` is the situation a shelf card offering
    // a seat wears, and a card that named `takeSeat` from the situation would be a
    // rule on the phone — which is the whole of `ADR-0053`.
    await launchWithCard(matchCard({ matchId: 'mine-1', situation: 'forming' }));

    expect(screen.queryByRole('button', { name: /Take the seat/ })).toBeNull();
  });

  it('draws the act and the exit for a situation it has never heard of', async () => {
    // The sharp version of `ADR-0070`'s unknown-name rule: an old phone meeting a
    // thirty-seventh situation loses **one sentence**, and keeps the ability to
    // take the seat and to leave. The act and `mayDepart` are spine facts, so
    // nothing about them depends on naming the situation.
    await launchWithCard({
      ...matchCard({ matchId: 'mine-1', act: 'takeSeat', mayDepart: true }),
      situation: {
        situation: 'seatTransferred' as Wire['Situation'],
        facts: {
          counts: { seats: 4, paid: 2, held: 0, turned_up: null },
          court_total: { amount: 15200, currency: 'PLN' },
          hold: null,
          cause: null,
        },
      },
    });

    expect(screen.queryByText('Forming')).toBeNull();
    expect(screen.getByLabelText(/Take the seat · 38,00/)).toBeTruthy();
    expect(screen.getByLabelText('Leave this match at Sunset Padel')).toBeTruthy();
  });

  it('draws no exit at all where the server says she may not leave', async () => {
    // Absent rather than refusing (`ADR-0086`): no door is offered that will not
    // open, and the phone never works out whether she holds a seat.
    await launchWithCard(matchCard({ matchId: 'mine-1', situation: 'completed' }));

    expect(screen.queryByLabelText(/^Leave this match/)).toBeNull();
  });

  it('renders the act’s amount through the repo’s shared table', async () => {
    // `38,00 zł` — comma decimal, non-breaking space before the suffix. The same
    // characters here and in the club console, because both implement
    // `docs/value-formatting.md` and neither reaches for `Intl`.
    await launchWithCard(matchCard({ matchId: 'mine-1', act: 'takeSeat', amount: 247425 }));

    expect(screen.getByText(`Take the seat · 2\u00a0474,25\u00a0zł`)).toBeTruthy();
  });

  it('gives a shelf card no button and no exit, whatever its spine carries', async () => {
    // `ADR-0088`: the shelf card reaches its act through its **body**, and gains
    // neither the state card's labelled button nor an exit. The body-as-control half
    // is asserted in *the shelves* below; what is asserted here is that neither
    // drawn control appears on one.
    await launchOnNow({
      ...emptyNow(),
      shelves: {
        stamp: 1,
        shelves: [
          shelf('bestFit', [matchCard({ matchId: 'feed-1', act: 'takeSeat', mayDepart: true })]),
        ],
      },
    });

    expect(screen.getByText('Best fit for you')).toBeTruthy();
    expect(screen.queryByText(/^Take the seat/)).toBeNull();
    expect(screen.queryByLabelText(/^Leave this match/)).toBeNull();
    expect(screen.queryByTestId(ACTION_ROW_ID)).toBeNull();
  });

  it('names the club on every control, so a dozen cards are not a dozen shrugs', async () => {
    // `ADR-0086` records that the two icons it replaced had **nothing** for a
    // label. What is drawn stays short; what is announced carries the card.
    await launchWithCard(
      matchCard({ matchId: 'mine-1', act: 'enterResult', mayDepart: true, clubName: 'Wola Padel' }),
    );

    expect(screen.getByText('Enter the score')).toBeTruthy();
    expect(screen.getByLabelText('Enter the score, Wola Padel')).toBeTruthy();
    expect(screen.getByLabelText('Leave this match at Wola Padel')).toBeTruthy();
  });
});

describe('a live seat claim wins the card', () => {
  it('takes the clock slot and the act, whatever the situation named', async () => {
    // `ADR-0081` worried about the alternative in as many words: *"a card counting
    // 1:30 to pay under a button offering anything else is two instructions."* The
    // card's own clock is two days out; the claim's five minutes are what shows.
    const base = Date.now();
    const inFiveMinutes = new Date(base + 5 * 60 * 1000).toISOString();

    await launchOnNow({
      ...emptyNow(),
      offers: {
        stamp: 1,
        cards: [
          matchCard({
            matchId: 'offer-1',
            situation: 'seatOpened',
            clock: '2099-01-01T18:00:00Z',
            seatClaimExpiresAt: inFiveMinutes,
            act: 'finishPaying',
          }),
        ],
      },
    });

    // The act the wire named, not the one `seatOpened` would suggest.
    expect(screen.getByText(/^Finish paying/)).toBeTruthy();
    expect(screen.queryByText(/^Take the seat/)).toBeNull();

    // And the clock is the claim's five minutes rather than the card's own moment,
    // which would have read in thousands of days.
    expect(screen.getByTestId(CLOCK_ID).props.children).toMatch(/^[0-5]:\d\d$/);
  });

  it('shows no exit while a payment is running', async () => {
    // Abandoning a payment must not be dressed as leaving. The server says so —
    // `mayDepart` is false under a live claim — and the card simply obeys.
    const inFiveMinutes = new Date(Date.now() + 5 * 60 * 1000).toISOString();

    await launchOnNow({
      ...emptyNow(),
      offers: {
        stamp: 1,
        cards: [
          matchCard({
            matchId: 'offer-1',
            situation: 'seatOpened',
            seatClaimExpiresAt: inFiveMinutes,
            act: 'finishPaying',
            mayDepart: false,
          }),
        ],
      },
    });

    expect(screen.queryByLabelText(/^Leave this match/)).toBeNull();
  });
});

describe('the countdown repaints and never fetches', () => {
  const MINUTE = 60 * 1000;

  const reading = () => String(screen.getByTestId(CLOCK_ID).props.children);

  it('redraws every second inside ten minutes, and asks for nothing', async () => {
    const inFiveMinutes = new Date(Date.now() + 5 * MINUTE).toISOString();

    await launchOnNow({
      ...emptyNow(),
      your_matches: {
        stamp: 1,
        cards: [matchCard({ matchId: 'mine-1', clock: inFiveMinutes })],
      },
    });

    const first = reading();
    expect(composes()).toBe(1);

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    const second = reading();

    // Twice, because a clock that ticked once and stopped is the shape a timer
    // that forgets to re-arm produces, and one tick cannot tell them apart.
    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    const third = reading();

    expect(new Set([first, second, third]).size).toBe(3);
    // A repaint is drawing, never a fifth occasion to ask (`ADR-0088`).
    expect(composes()).toBe(1);
  });

  it('reads the clock afresh when a pull brings a new screen', async () => {
    // A screen whose moments have all passed arms nothing at all, so *now* stops
    // moving. Without a fresh reading when the next answer lands, the first thing
    // she sees after explicitly asking is a countdown minutes out of date — on the
    // one occasion she asked.
    const base = Date.now();
    const passed = new Date(base - MINUTE).toISOString();

    await launchOnNow({
      ...emptyNow(),
      your_matches: { stamp: 1, cards: [matchCard({ matchId: 'mine-1', clock: passed })] },
    });

    await act(async () => {
      jest.advanceTimersByTime(5 * MINUTE);
    });

    stubNow(transport, {
      ...emptyNow(),
      your_matches: {
        stamp: 2,
        cards: [
          matchCard({
            matchId: 'mine-1',
            clock: new Date(Date.now() + 5 * MINUTE).toISOString(),
          }),
        ],
      },
    });
    fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');

    // Five minutes, not the ten a clock five minutes behind would have printed.
    await waitFor(() => expect(screen.getByTestId(CLOCK_ID).props.children).toMatch(/^[45]:/));
  });

  it('redraws once a minute above ten, so a second changes nothing', async () => {
    const inThirtyMinutes = new Date(Date.now() + 30 * MINUTE).toISOString();

    await launchOnNow({
      ...emptyNow(),
      your_matches: {
        stamp: 1,
        cards: [matchCard({ matchId: 'mine-1', clock: inThirtyMinutes })],
      },
    });

    const before = reading();

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    expect(reading()).toBe(before);

    await act(async () => {
      jest.advanceTimersByTime(MINUTE);
    });
    expect(reading()).not.toBe(before);
    expect(composes()).toBe(1);
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
// The shelves: the tail card, the fit badge, emphasis, and the body as a control
// ---------------------------------------------------------------------------

describe('the shelves', () => {
  const REASON = fitReason('travel', { code: 'travel', minutes: 14, radius: null });

  /** A screen whose only content is one shelf of one card. */
  const oneShelf = (
    code: Wire['ShelfCode'],
    cards: Wire['ShelfResponse']['cards'],
  ): Wire['NowResponse'] => ({
    ...emptyNow(),
    shelves: { stamp: 1, shelves: [shelf(code, cards)] },
  });

  /** Index into a list, refusing an absent element rather than asserting one away. */
  function nth<T>(list: readonly T[], index: number): T {
    const item = list[index];
    if (item === undefined) throw new Error(`no element at ${index} of ${list.length}`);
    return item;
  }

  /** The badges on screen, in the order they were drawn. */
  const badges = () => screen.queryAllByTestId(FIT_BADGE_ID);

  const isEmphatic = (badge: ReturnType<typeof badges>[number]) =>
    StyleSheet.flatten(badge.props.style).backgroundColor === theme.color.coralInk;

  it('renders a shelf from its code, and a code this build has never met stays reserved', async () => {
    // `recentlyViewed` is reserved on the wire with no producer (`ADR-0085`), so its
    // return is a **server** change: nothing here is added the day it arrives, and
    // this asserts that by composing one and finding it whole — title and tail card.
    await launchOnNow(oneShelf('recentlyViewed', [matchCard({ matchId: 'feed-1' })]));

    expect(screen.getByText('Recently viewed')).toBeTruthy();
    expect(screen.getAllByTestId(TAIL_CARD_ID)).toHaveLength(1);
  });

  it('ends every shelf in a card into Find, and opens it on a tap', async () => {
    // A shelf running out is a door and not a wall. The tail card is **not** in the
    // contract — the client appends it from the shelf's code and the sport it holds.
    await launchOnNow({
      ...emptyNow(),
      shelves: {
        stamp: 1,
        shelves: [
          shelf('bestFit', [matchCard({ matchId: 'feed-1' })]),
          shelf('newPlayers', [personCard('p-1', 'ada')]),
          shelf('newClubs', [clubCard('c-9', 'Kraków Padel')]),
        ],
      },
    });

    expect(screen.getAllByTestId(TAIL_CARD_ID)).toHaveLength(3);
    // Each names its own shelf, because a screen holds up to five reading the same.
    expect(screen.getByLabelText('See more in Find: Best fit for you')).toBeTruthy();
    expect(screen.getByLabelText('See more in Find: New clubs')).toBeTruthy();

    fireEvent.press(screen.getByLabelText('See more in Find: Best fit for you'));

    await waitFor(() => expect(screen).toHavePathname('/find'));
  });

  it('puts the tail card at the end of the shelf and not at the head of it', async () => {
    // *Ends* in a card into Find: a door at the front of a row nobody has scrolled is
    // an exit offered before the thing it is an exit from.
    await launchOnNow(oneShelf('bestFit', [matchCard({ matchId: 'feed-1', clubName: 'Wola' })]));

    const inOrder = screen.getAllByText(/Wola|See more in Find/);

    expect(String(nth(inOrder, inOrder.length - 1).props.children)).toBe('See more in Find');
  });

  it('draws no tail card on a shelf whose code it cannot address', async () => {
    // The same answer the title gets: a door this build cannot open is worse than no
    // door, and both facts are missing at the same moment for the same reason.
    await launchOnNow(
      oneShelf('somethingNew' as Wire['ShelfCode'], [matchCard({ matchId: 'feed-1' })]),
    );

    expect(screen.getByTestId(REGION_ID.shelves)).toBeTruthy();
    expect(screen.queryAllByTestId(TAIL_CARD_ID)).toHaveLength(0);
  });

  it('prints a number on the badge, clamped, and up to three reasons under it', async () => {
    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({
          matchId: 'feed-1',
          fit: fit({ score: 100, reasons: [REASON, REASON, REASON] }),
        }),
      ]),
    );

    // 100 never reaches a pill: certainty is never warranted.
    expect(screen.getByText('✦ 99')).toBeTruthy();
    expect(screen.getByLabelText('Fit 99')).toBeTruthy();
    expect(screen.getAllByTestId(FIT_REASON_ID)).toHaveLength(3);
    expect(screen.getAllByText('It is close to you.')).toHaveLength(3);
  });

  it('answers an unsure estimate with a warning and never a percentage', async () => {
    // `ADR-0037`: coverage ranks and gates and *never becomes a second gauge on the
    // card*. What an uncertain estimate becomes is words.
    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({ matchId: 'feed-1', fit: fit({ score: 74, unsure: true, reasons: [REASON] }) }),
      ]),
    );

    expect(screen.getByTestId(FIT_WARNING_ID)).toBeTruthy();
    expect(screen.getByText('Early days for this match — this is a rough guess.')).toBeTruthy();
    expect(screen.queryByText(/%/)).toBeNull();
  });

  it('says nothing at all where the estimate is not unsure', async () => {
    // The negative half, and the one that decides whether the warning is worth
    // anything: the fit-model delta rejects a threshold that fires on *"acceptable
    // but not great"* because *"warning about that would teach players to ignore
    // warnings"*. A card warning on every suggestion is that failure, drawn.
    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({ matchId: 'feed-1', fit: fit({ score: 74, unsure: false, reasons: [REASON] }) }),
      ]),
    );

    expect(screen.getAllByTestId(FIT_REASON_ID)).toHaveLength(1);
    expect(screen.queryByTestId(FIT_WARNING_ID)).toBeNull();
    expect(screen.queryByText(/rough guess/)).toBeNull();
  });

  it('draws no badge at all on a card the server did not score', async () => {
    await launchOnNow(oneShelf('bestFit', [matchCard({ matchId: 'feed-1' })]));

    expect(badges()).toHaveLength(0);
    expect(screen.queryAllByTestId(FIT_REASON_ID)).toHaveLength(0);
  });

  it('shouts on the one card the wire flagged, and on no other', async () => {
    // The flag is the composed screen's (`ADR-0032`, `ADR-0037`). Both cards below
    // clear 90 and one is loud, so a client comparing against the score fails here.
    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({ matchId: 'feed-1', fit: fit({ score: 93 }) }),
        matchCard({ matchId: 'feed-2', fit: fit({ score: 99 }), emphasis: true }),
      ]),
    );

    expect(badges().filter(isEmphatic)).toHaveLength(1);
    // And the one that shouts is the flagged one, not the higher-scoring first card.
    expect(screen.getByLabelText('Fit 99, the pick of this screen')).toBeTruthy();
    expect(screen.getByLabelText('Fit 93')).toBeTruthy();
  });

  it('leaves every card quiet on a screen the server flagged nothing on', async () => {
    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({ matchId: 'feed-1', fit: fit({ score: 99 }) }),
        matchCard({ matchId: 'feed-2', fit: fit({ score: 95 }) }),
      ]),
    );

    expect(badges()).toHaveLength(2);
    expect(badges().filter(isEmphatic)).toHaveLength(0);
  });

  it('makes a shelf card’s body the control when it names an act', async () => {
    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({ matchId: 'feed-1', act: 'takeSeat', clubName: 'Wola Padel' }),
      ]),
    );

    // The act's own label, and the club beside it — a screen holds a dozen of these
    // and the visible half of a whole-card control is the card.
    const body = screen.getByLabelText(/^Take the seat · .+, Wola Padel$/);

    expect(body.props.accessibilityRole).toBe('button');
    // It presses without throwing; where it goes is `Raketa02/Raketa#89`'s.
    fireEvent.press(body);
  });

  it('leaves a shelf card inert all the way through when it names none', async () => {
    // `ADR-0083`'s converse: a card with no act has no button **and its body is not a
    // tap target either**, so an inert card does not swallow a press.
    await launchOnNow(
      oneShelf('bestFit', [matchCard({ matchId: 'feed-1', clubName: 'Wola Padel' })]),
    );

    // The card is drawn — the spine is there — and nothing on it is operable.
    expect(screen.getAllByText(/Wola Padel/).length).toBeGreaterThan(0);
    expect(screen.queryByLabelText(/^Take the seat/)).toBeNull();
    expect(screen.queryByRole('button', { name: /Wola Padel/ })).toBeNull();
  });

  it('keeps a shelf card’s clock empty, whatever moment the wire put on it', async () => {
    // `ADR-0088`: the clock is *the next moment something happens to the viewer*, and
    // on a match she holds no stake in, nothing does. The server sends the match's own
    // boundary here and the card draws the tag instead.
    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({ matchId: 'feed-1', clock: '2099-01-01T18:00:00Z', situation: 'forming' }),
      ]),
    );

    expect(screen.queryByTestId(CLOCK_ID)).toBeNull();
    expect(screen.getByText('Forming')).toBeTruthy();
  });

  it('replaces the tone tag with the countdown while her own claim runs', async () => {
    // Replacing rather than joining: that row is already two crowded groups, and
    // while a player holds 1:30 to pay, *Forming* is not the news.
    const inFiveMinutes = new Date(Date.now() + 5 * 60 * 1000).toISOString();

    await launchOnNow(
      oneShelf('bestFit', [
        matchCard({
          matchId: 'feed-1',
          clock: '2099-01-01T18:00:00Z',
          seatClaimExpiresAt: inFiveMinutes,
          situation: 'forming',
        }),
      ]),
    );

    expect(String(screen.getByTestId(CLOCK_ID).props.children)).toMatch(/^[0-5]:\d\d$/);
    expect(screen.queryByText('Forming')).toBeNull();
  });

  it('does not reshuffle or replace a shelf when she taps a card', async () => {
    // A match she joined stays put until she next asks for a fresh screen: her tap
    // may carry an update, and an update is never allowed to carry shelves.
    await launchOnNow({
      ...emptyNow(),
      shelves: {
        stamp: 1,
        shelves: [
          shelf('bestFit', [
            matchCard({ matchId: 'feed-1', act: 'takeSeat', clubName: 'Wola Padel' }),
            matchCard({ matchId: 'feed-2', clubName: 'Sunset Padel' }),
          ]),
          shelf('newClubs', [clubCard('c-9', 'Kraków Padel')]),
        ],
      },
    });

    const order = () => screen.getAllByRole('header').map((node) => String(node.props.children));
    const before = order();
    const asks = composes();

    fireEvent.press(screen.getByLabelText(/^Take the seat · .+, Wola Padel$/));

    expect(order()).toEqual(before);
    expect(screen.getAllByTestId(TAIL_CARD_ID)).toHaveLength(2);
    expect(composes()).toBe(asks);
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

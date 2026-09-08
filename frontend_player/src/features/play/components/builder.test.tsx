/**
 * **The builder**, walked the way a player walks it: the real route tree, the real shell, the
 * real stores, and only `fetch` faked.
 *
 * What is asserted is the set of claims a build session could quietly undo, and most of them
 * are about a request that must **not** happen:
 *
 * - **⚡ is one request** whether the court is empty or half-built, and `locked_seats` is the
 *   only difference between the two.
 * - **A swap costs nothing.** Every arrangement crosses, so trading two seats is a selection
 *   out of a response already held — and only a *membership* change round-trips.
 * - **The client computes no forecast number.** Every figure on screen is one the server sent,
 *   which is checkable by sending a number no arithmetic over the fixtures could produce.
 * - **The shortfall is per seat**, in the four codes, with the remedy on the pool.
 * - **A withheld seat is marked rather than emptied**, and the marked player stays in the
 *   forecast.
 * - **A seated player's Fit is reachable**, by a name on the forecast card and by a hold on
 *   the seat — and a hold is never the only way in, because there is no long-press gesture in
 *   the accessibility API.
 */

import { AccessibilityInfo, StyleSheet, View, type ViewStyle } from 'react-native';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { onlineManager } from '@tanstack/react-query';

import { offlineMessage, type AppError } from '@/shared/errors';
import { queryClient } from '@/shared/lib/query-client';
import {
  BAND_HAS_NO_COUNT,
  IN_YOUR_AREA,
  OPINION_BAND_NAME,
  OPINION_CARD_TITLE_DRAWN,
  OWN_RECORD_TITLE,
  PLAYER_SCORE_NAME,
  YOU_MARK,
  RECORD_CARD_TITLE_DRAWN,
  RECORD_TITLE,
  RECORD_UNAVAILABLE,
  STRAND_NAME,
  fitRowLabel,
  opinionFigure,
  recordCloseLabel,
  strandFraction,
  varietyValue,
} from '@/features/player_record/types';
import { BALANCE_SOFT, POSTER_LABEL, courtSeatCount, theme } from '@/shared/ui';
import { NO_TAGS_IN_COMMON, socialTagChip } from '@/shared/vocabulary/socialTagPresentation';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import {
  PROFILE_SURFACE_SERVED,
  launchSignedIn,
  stubGate,
  stubInterest,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { usePlayPreferences } from '../store/playPreferences.store';
import { endPlaySession, usePlaySession } from '../store/playSession.store';

import {
  courtSummaryLabel,
  provisionalForecastAnnouncement,
  seatLabel,
  seatedNameLabel,
  splitRowLabel,
  whyFitSheetLabel,
  SWAP_TOGGLE_LABEL,
} from './accessibilityPresentation';
import { courtEntryLabel } from './findAGamePresentation';
import { balanceLabel, balanceWord } from './balancePresentation';
import {
  ALREADY_EVENEST,
  EVEN_IT_OUT_LABEL,
  PICK_PLAYERS_LABEL,
  PROVISIONAL_WORD,
  RETRY_FORECAST_LABEL,
  SIDE_HEADINGS,
  START_OVER_LABEL,
  arrangedYourWayLine,
  fillSeatsLabel,
  sideName,
} from './builderPresentation';
import { WITHHELD_SEAT_LINE, optimisedForLine, unfilledSeatLine } from './courtPresentation';
import { playErrorMessage } from './playErrorMessage';
import { promptControls, promptCopy } from './promptPresentation';
import { engineFillStatus, poolRankingStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';

/** The two waits' headlines, taken from their own copy rather than spelled here. */
const POOL_RANKING = poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline;
const ENGINE_FILL = engineFillStatus({ playersInRange: undefined, seats: 4 }).headline;
/** The count off ⚡'s own response — and therefore the one thing on screen that says it landed. */
const ENGINE_FILL_COUNT = engineFillStatus({ playersInRange: 7, seats: 4 }).count ?? '';

const SEARCHES = '/api/v1/searches';
const LINEUPS = '/api/v1/lineups';
const FORECASTS = '/api/v1/forecasts';
const DECLINES = '/api/v1/prompt-declines';
const RADIUS = '/api/v1/players/me/search-radius';

const SEARCH_ID = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';
const LINEUP_ID = 'a1b2c3d4-0000-4000-8000-00000000000f';
const ME = 'aaaaaaaa-0000-4000-8000-000000000000';
const B = 'bbbbbbbb-0000-4000-8000-000000000001';
const C = 'cccccccc-0000-4000-8000-000000000002';
const D = 'dddddddd-0000-4000-8000-000000000003';

const NAMES: Readonly<Record<string, string>> = { [B]: 'bea_k', [C]: 'cyryl', [D]: 'dorota_w' };
const LEVELS: Readonly<Record<string, number>> = { [B]: 2.8, [C]: 2.71, [D]: 2.9 };

function rating(sport: Wire['Sport']): Wire['RatingResponse'] {
  return {
    sport,
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

function card(playerId: string): Wire['CandidateSchema'] {
  return {
    player_id: playerId,
    fit: 78,
    distance_km: 4,
    player_card: {
      nickname: NAMES[playerId] ?? 'anon',
      area_code: 'A+050612+0019938',
      social_tags: [],
      level: LEVELS[playerId] ?? 2.7,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    concerns: [],
    terms: [],
    degraded_terms: [],
    modifiers: [],
    liveness_reasons: [],
  };
}

function envelope(
  searchId: string,
  over: Partial<Wire['SearchEnvelope']> = {},
): Wire['SearchEnvelope'] {
  return {
    search_id: searchId,
    at: '2026-08-31T18:00:00Z',
    surface: 'SHORTLIST',
    mode: 'FOR_FUN',
    ruleset_version: 'ruleset-v1',
    engine_version: 'matchfit-v1',
    optimised_for: 'SEARCHER',
    index_stale: false,
    pool: {
      sport: 'PADEL',
      radius_km_used: 12,
      players_in_range: 7,
      window: 'THIS_WEEK',
      post_gate: true,
    },
    radius_clamp: false,
    sorts_available: ['BEST_FIT'],
    rung_offers: null,
    ...over,
  };
}

const shortlist = (prompts?: readonly Wire['PromptSchema'][]): Wire['ShortlistResponse'] => ({
  search: envelope(SEARCH_ID, prompts === undefined ? {} : { prompts: [...prompts] }),
  candidates: [card(B), card(C), card(D)],
});

/** One way round, with a **figure no arithmetic over these fixtures could produce**. */
function arrangement(
  partner: string,
  opponents: readonly string[],
  facts: { id: number; pct: number; current?: boolean; evenest?: boolean; provisional?: boolean },
): Wire['ArrangementSchema'] {
  const seat = (index: number, relationship: Wire['Relationship'], playerId?: string) => ({
    seat_index: index,
    relationship,
    ...(playerId === undefined ? {} : { player_id: playerId }),
  });

  return {
    pairing_id: facts.id,
    is_current: facts.current ?? false,
    is_evenest: facts.evenest ?? false,
    sides: {
      A: [seat(0, 'SELF', ME), seat(1, 'PARTNER', partner)],
      B: [seat(2, 'OPPONENT', opponents[0]), seat(3, 'OPPONENT', opponents[1])],
    },
    forecast: {
      pct: facts.pct,
      sigma_group: 0.41,
      provisional: facts.provisional ?? false,
      assumption: facts.provisional === true ? 'EMPTY_SEAT_MATCHES_ITS_PARTNER' : null,
    },
    // Derived from this fixture's own pct, so the three ways round stay one
    // computation the way the server's are: the evenest reads the smallest gap.
    split: {
      your_side: 3.2,
      their_side: 3.2 - (100 - facts.pct) / 100,
      gap: (100 - facts.pct) / 100,
    },
  };
}

/**
 * The three ways round one four, with the evenest at 91 — and **`is_current` on none of them**,
 * because the two routes that return arrangements mean different things by it
 * ([#289](https://github.com/Raketa02/Raketa/issues/289)): a line-up marks the **evenest**, and
 * a forecast marks **the seat order the request sent**. Marking it once here would make one of
 * those two fixtures a lie, and it is the fixture the swap tests are read against.
 */
const THREE_WAYS = [
  arrangement(B, [C, D], { id: 1, pct: 78 }),
  arrangement(C, [B, D], { id: 2, pct: 91, evenest: true }),
  arrangement(D, [B, C], { id: 3, pct: 64 }),
];

/** A line-up opens on the closest game these four can play, so `is_current` is `is_evenest`. */
const LINEUP_WAYS = THREE_WAYS.map((one) => ({ ...one, is_current: one.is_evenest }));

/** Who the engine seated beside you in one way round — the thing a pairing *is*. */
const partnerIn = (one: Wire['ArrangementSchema']) =>
  one.sides.A.find((seat) => seat.relationship === 'PARTNER')?.player_id;

/** The seat order one forecast request asked about, which is what its `is_current` names. */
const seatOrderOf = (body: unknown): readonly string[] => (body as Wire['ForecastRequest']).players;

interface FullCourt {
  readonly optimisedFor?: Wire['OptimisedFor'];
  readonly candidates?: Wire['LineupResponse']['candidates'];
  /** The questions this fill raises. Absent on every fixture that is not about them. */
  readonly prompts?: readonly Wire['PromptSchema'][];
}

/** ⚡'s answer with every seat taken. */
function seatedFour(over: FullCourt = {}): Wire['LineupResponse'] {
  return {
    search: envelope(LINEUP_ID, {
      surface: 'LINEUP',
      ...(over.optimisedFor === undefined ? {} : { optimised_for: over.optimisedFor }),
      ...(over.prompts === undefined ? {} : { prompts: [...over.prompts] }),
    }),
    candidates: over.candidates ?? [card(B), card(C), card(D)],
    // `LineupSchema.seats` is *the court in the arrangement marked `is_current`*, and that is
    // now the evenest one — so the seating here is the C pairing's, not the B one's.
    lineup: {
      seats: [
        { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
        { side: 'A', seat_index: 1, relationship: 'PARTNER', player_id: C },
        { side: 'B', seat_index: 2, relationship: 'OPPONENT', player_id: B },
        { side: 'B', seat_index: 3, relationship: 'OPPONENT', player_id: D },
      ],
      arrangements: LINEUP_WAYS,
      group_reason: 'EVENEST_ARRANGEMENT',
    },
  };
}

/** ⚡'s answer three of four, which is an honest answer and a `200`. */
function threeOfFour(reason: Wire['UnfilledReason']): Wire['LineupResponse'] {
  return {
    search: envelope(LINEUP_ID, { surface: 'LINEUP' }),
    candidates: [card(B), card(C)],
    lineup: {
      seats: [
        { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
        { side: 'A', seat_index: 1, relationship: 'PARTNER', player_id: B },
        { side: 'B', seat_index: 2, relationship: 'OPPONENT', player_id: C },
        { side: 'B', seat_index: 3, relationship: 'OPPONENT', unfilled_reason: reason },
      ],
      arrangements: [
        {
          ...arrangement(B, [C], { id: 1, pct: 73, current: true, provisional: true }),
          sides: {
            A: [
              { seat_index: 0, relationship: 'SELF', player_id: ME },
              { seat_index: 1, relationship: 'PARTNER', player_id: B },
            ],
            B: [
              { seat_index: 2, relationship: 'OPPONENT', player_id: C },
              { seat_index: 3, relationship: 'OPPONENT' },
            ],
          },
        },
      ],
    },
  };
}

/**
 * `POST /forecasts` answers with every way round and marks **the one the request asked about**,
 * which is the opposite of what a line-up's `is_current` names and the reason a client that
 * sends an arrangement can draw a swap at all.
 */
const forecastFor = (players: readonly string[]): Wire['ForecastResponse'] => ({
  arrangements: THREE_WAYS.map((one) => ({ ...one, is_current: partnerIn(one) === players[0] })),
  engine_version: 'matchfit-v1',
  ruleset_version: 'ruleset-v1',
});

let transport: Transport;
let announced: jest.SpyInstance;

/** What a listener was told, in order. §20.9's regions are all polite and all queued. */
const spoken = () => announced.mock.calls.map(([message]) => message as string);

beforeEach(() => {
  announced = jest
    .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
    .mockImplementation(() => undefined);
  transport = installTransport();
  stubGate(transport, { id: ME, ratings: [rating('PADEL')], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubInterest(transport);
  transport.on('POST', SEARCHES, () => json(shortlist()));
  transport.on('POST', LINEUPS, () => json(seatedFour()));
  transport.on('POST', FORECASTS, ({ body }) => json(forecastFor(seatOrderOf(body))));
  transport.on('POST', DECLINES, () => noContent());
  transport.on('PUT', RADIUS, () => json<Wire['SearchRadiusResponse']>({ search_radius_km: 22 }));
});

afterEach(async () => {
  announced.mockRestore();
  transport.restore();
  // One test takes the connection away, and `onlineManager` is a singleton.
  onlineManager.setOnline(true);
  queryClient.clear();
  usePlayPreferences.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

const seat = (place: Parameters<typeof seatLabel>[0], playerId: string) =>
  screen.getByLabelText(
    seatLabel(place, { kind: 'player', name: NAMES[playerId] ?? '', level: LEVELS[playerId] ?? 0 }),
  );

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

/** The nearest ancestor that paints a bed — the panel a face is standing in. */
const bedOf = (node: ReturnType<typeof screen.getByLabelText> | null): string | undefined => {
  for (let up = node; up !== null; up = up.parent) {
    const painted = flatten(up.props.style)?.backgroundColor;
    if (typeof painted === 'string') return painted;
  }
  return undefined;
};

/** The side panel's own button — `{side}, {name}, player record`. */
const named = (place: Parameters<typeof seatedNameLabel>[0], playerId: string) =>
  screen.getByLabelText(seatedNameLabel(place, { name: NAMES[playerId] ?? '', self: false }));

/** Your own face, which opens the same sheet retitled. */
const yourFace = (place: Parameters<typeof seatedNameLabel>[0]) =>
  screen.getByLabelText(seatedNameLabel(place, { name: 'You', self: true }));

/** `SH.whyfit`'s accessible name, which is deliberately not its visible `Why ✦ 78`. */
const WHY_FIT = whyFitSheetLabel(78);

/** The shape `playErrorMessage` reads — the code, never the backend's own message. */
const refusal = (code: string): AppError => ({ recovery: 'business-conflict', code }) as AppError;

const summary = (filled: number) => courtSummaryLabel({ sportName: 'Padel', filled, seats: 4 });

/** Search, spend the latch, and arrive on the court the search minted. */
async function openTheBuilder() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await screen.findByLabelText('Tuesday evening');

  fireEvent.press(screen.getByLabelText(courtEntryLabel(courtSeatCount('padel'))));
  // The floor runs from the **answer**, so the latch has to be up before the clock is driven —
  // advancing it first would spend the hold on a request that has not come back.
  await screen.findByText(POOL_RANKING);
  act(() => jest.advanceTimersByTime(searchingFloorMs({ kind: 'pool' })));

  await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  await screen.findByLabelText(summary(1));
}

/** ⚡, and the fill's own floor — `650 plus 550 a seat`, spent before the court is reachable. */
async function pressFill(filled = 1) {
  fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled })));
  await screen.findByText(ENGINE_FILL);
  // The floor is the **court's** seat count, not the answer's: it is how long the fill's
  // presentation runs, and a court is four seats whether or not four people sat down.
  act(() =>
    jest.advanceTimersByTime(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: false })),
  );
  await waitFor(() => expect(screen.queryByText(ENGINE_FILL)).toBeNull());
}

describe('arriving', () => {
  /**
   * **The gesture, drawn.** This screen is pushed and Find a game stays underneath it, so the
   * platform's own back already lands there — 10.3's chevron is opt-in for exactly the screens
   * that can say where it goes, and this is one. It adds no behaviour, which is the point: a
   * thumb should not have to know a swipe exists to get back out of a court it opened.
   */
  it('draws a way back to the screen underneath it', async () => {
    await openTheBuilder();

    fireEvent.press(screen.getByLabelText('Back'));

    await waitFor(() => expect(screen).toHavePathname('/play'));
  });

  it('opens on an empty court that seats you, with the seats it has still open', async () => {
    await openTheBuilder();

    expect(screen.getByLabelText(seatLabel('YOUR_SIDE', { kind: 'you' }))).toBeTruthy();
    // The open seats are the **court's** own statement now: the line that counted them under
    // the picture said what the picture already showed, and went with the block beneath it.
    expect(screen.getAllByLabelText(/empty$/)).toHaveLength(3);
    // Nothing has been asked about nobody: `ForecastRequest.players` is *one, two or three*.
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(0);
  });

  /**
   * **Your own seat has a face before anybody has answered for it**
   * ([#282](https://github.com/Raketa02/Raketa/issues/282)).
   *
   * A poster is a function of an id, and the id is the account's — so the one seat on an
   * empty court is drawn from `GET /users/me` rather than waiting for an arrangement to name
   * you with `Relationship.SELF`. One poster, because the other three seats are empty and an
   * empty seat draws a plus.
   */
  it('draws your own poster on a court nobody has answered for', async () => {
    await openTheBuilder();

    expect(screen.getAllByLabelText(POSTER_LABEL, { includeHiddenElements: true })).toHaveLength(1);
  });

  it('offers both branches, and neither is drawn once the court is full', async () => {
    await openTheBuilder();

    expect(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 }))).toBeTruthy();
    expect(screen.getByLabelText(PICK_PLAYERS_LABEL)).toBeTruthy();

    await pressFill();

    await waitFor(() => expect(screen.queryByLabelText(PICK_PLAYERS_LABEL)).toBeNull());
  });
});

describe('⚡ — the engine fills the seats', () => {
  it('sends no `locked_seats` from an empty court, and seats everybody', async () => {
    await openTheBuilder();
    await pressFill();

    expect(await screen.findByLabelText(summary(4))).toBeTruthy();
    expect(transport.requestsTo('POST', LINEUPS)[0]?.body).toEqual({
      sport: 'PADEL',
      mode: 'FOR_FUN',
    });
    // The evenest pairing's seating, which is what `is_current` names on a line-up: C beside
    // you, B across the net.
    expect(seat('YOUR_PARTNER', C)).toBeTruthy();
    expect(seat('THEIR_SIDE', B)).toBeTruthy();
  });

  /**
   * **The completing-a-game context, and it is the same request.** `locked_seats` is *"a
   * property of what you send rather than of where you send it"*, so hand-seating somebody and
   * pressing ⚡ has no second route and no second shape.
   *
   * The seating is driven through the store because the screen that seats people is the pool
   * ([#272](https://github.com/Raketa02/Raketa/issues/272)); what is asserted here is the half
   * this ticket owns — the request ⚡ sends once somebody is on the court.
   */
  it('sends whoever is already seated, which is what makes ⚡ complete a game', async () => {
    await openTheBuilder();
    act(() => usePlaySession.getState().seat(SEARCH_ID, B));

    await waitFor(() => expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(1));
    // *Fill the rest*, because the engine fills around `locked_seats` and never over them.
    await pressFill(2);

    expect(transport.requestsTo('POST', LINEUPS)[0]?.body).toEqual({
      sport: 'PADEL',
      mode: 'FOR_FUN',
      locked_seats: [B],
    });
  });

  /**
   * ⚡ answers with every arrangement, so the court it lands on already has its number: asking
   * again would be Part 7's *"immediately refetch what you were just handed"*.
   */
  it('needs no forecast request, because the fill already answered with one', async () => {
    await openTheBuilder();
    await pressFill();

    await screen.findByLabelText(summary(4));
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(0);
  });

  /** The count is `players_in_range` off the response, and never a number grown to fill a wait. */
  it('prints the pool the fill read, and only once there is a response', async () => {
    await openTheBuilder();

    fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 })));
    await screen.findByText(ENGINE_FILL);

    expect(await screen.findByText('7 in range')).toBeTruthy();
    act(() =>
      jest.advanceTimersByTime(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: false })),
    );
    await waitFor(() => expect(screen.queryByText('7 in range')).toBeNull());
  });
});

describe('the forecast', () => {
  it('renders the number the server sent, and computes none of its own', async () => {
    await openTheBuilder();
    await pressFill();

    // 91 is on no path any arithmetic over these levels would reach — it is read, or it is
    // not on screen at all.
    expect(await screen.findByText('91%')).toBeTruthy();
    // Part 13: the tint is never the only carrier, so the word is drawn beside the figure.
    expect(screen.getByText(balanceWord(91))).toBeTruthy();
  });

  /**
   * **A swap is a selection.** Every arrangement crossed with the fill, so trading two seats
   * moves the figure with no request behind it.
   */
  it('moves the figure on a swap without asking the server anything', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('YOUR_PARTNER', C));
    fireEvent.press(seat('THEIR_SIDE', B));

    expect(await screen.findByText('78%')).toBeTruthy();
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(0);
  });

  /** **Change sides, never seats**: the four are the same four after a trade. */
  it('keeps everybody on the court through a swap', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('YOUR_PARTNER', C));
    fireEvent.press(seat('THEIR_SIDE', B));

    await screen.findByText('78%');
    expect(screen.getByLabelText(summary(4))).toBeTruthy();
    expect(usePlaySession.getState().lineup?.seats).toHaveLength(3);
  });

  /** Only **membership** round-trips: taking somebody off is a different four. */
  it('asks again when somebody leaves the court', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(screen.getByLabelText(`Remove ${NAMES[B]} from their side`));

    await waitFor(() => expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(1));
    expect(transport.requestsTo('POST', FORECASTS)[0]?.body).toEqual({
      sport: 'PADEL',
      mode: 'FOR_FUN',
      search_id: LINEUP_ID,
      players: [C, D],
    });
  });

  /**
   * §20.9's **third live region**, and the one nobody else had claimed: the forecast is the
   * only figure in the tab that changes while focus is elsewhere, because a swap moves the
   * number and leaves focus on the seat that moved.
   */
  it('announces the figure it changed, with the word and not a bare percentage', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('YOUR_PARTNER', C));
    fireEvent.press(seat('THEIR_SIDE', B));

    await screen.findByText('78%');
    expect(spoken()).toContain(
      provisionalForecastAnnouncement({ pct: 78, provisional: false, assumption: null }),
    );
  });

  /** Paused, not failed: a membership change offline says so rather than drawing nothing. */
  it('says a forecast made offline is waiting rather than showing an empty card', async () => {
    await openTheBuilder();
    act(() => onlineManager.setOnline(false));

    act(() => usePlaySession.getState().seat(SEARCH_ID, B));

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(0);
  });

  /**
   * **The figure and its caveat are one thing** (ADR-0108), and the mark is one word beneath
   * the tinted number.
   */
  it('marks a provisional figure provisional, and states what it assumed', async () => {
    transport.on('POST', LINEUPS, () => json(threeOfFour('NO_CANDIDATE_ABOVE_FLOOR')));
    await openTheBuilder();
    await pressFill();

    expect(await screen.findByText('73%')).toBeTruthy();
    expect(screen.getByText(PROVISIONAL_WORD)).toBeTruthy();
    expect(screen.getByText(/It settles as you add/)).toBeTruthy();
  });
});

describe('what the court says about itself', () => {
  /**
   * §11's four codes — what replaced AC-69's *"Only found 2"*.
   *
   * **Per seat is where the seat says it**: each open seat's own accessible name carries its
   * own code (§20.4), which is what a listener navigates by. The line beneath the court is
   * §11's **sentence**, in the visible register and hidden from a listener, so the same
   * shortfall is not announced twice.
   */
  it('states the shortfall on the seat, and beneath the court in its own words', async () => {
    transport.on('POST', LINEUPS, () => json(threeOfFour('NO_ADMISSIBLE_COMBINATION')));
    await openTheBuilder();
    await pressFill();

    await screen.findByLabelText(summary(3));
    // The seat, per seat.
    expect(
      screen.getByLabelText(
        seatLabel('THEIR_SIDE', { kind: 'empty', unfilled: 'NO_ADMISSIBLE_COMBINATION' }),
      ),
    ).toBeTruthy();
    // And the sentence, once, in the register a reader reads — **drawn and hidden**, which is
    // 6.8's own answer to the same question: a line that repeats what the element above it
    // already announces is announced twice, so it is decoration to a listener.
    expect(
      screen.getByText(unfilledSeatLine('NO_ADMISSIBLE_COMBINATION'), {
        includeHiddenElements: true,
      }),
    ).toBeTruthy();
    expect(screen.queryByText(unfilledSeatLine('NO_ADMISSIBLE_COMBINATION'))).toBeNull();
    // Never the spoken name printed as body copy: *Their side, empty* is a name, not a line.
    expect(screen.queryByText(/^Their side, empty/, { includeHiddenElements: true })).toBeNull();
  });

  /** And the remedy is the pool, which is the screen the ladder is on and this one is not. */
  it('routes the remedy for an unfilled seat to the pool', async () => {
    transport.on('POST', LINEUPS, () => json(threeOfFour('POOL_EXHAUSTED')));
    await openTheBuilder();
    await pressFill();

    fireEvent.press(
      await screen.findByLabelText(
        seatLabel('THEIR_SIDE', { kind: 'empty', unfilled: 'POOL_EXHAUSTED' }),
      ),
    );

    await waitFor(() => expect(screen).toHavePathname('/play/pool'));
  });

  /**
   * **`optimised_for: GROUP` is rendered**, in the same voice a provisional figure is: the
   * engine filled the seats around somebody, so the four may be a worse individual match than
   * an empty court would have given — said before it is discovered.
   */
  it('says when the answer stopped being optimised for the searcher', async () => {
    transport.on('POST', LINEUPS, () => json(seatedFour({ optimisedFor: 'GROUP' })));
    await openTheBuilder();
    await pressFill();

    const line = optimisedForLine('GROUP');
    expect(line).toBeDefined();
    expect(await screen.findByText(line ?? '')).toBeTruthy();
  });

  it('says nothing at all about an answer optimised for the searcher', async () => {
    await openTheBuilder();
    await pressFill();

    await screen.findByLabelText(summary(4));
    expect(screen.queryByText(optimisedForLine('GROUP') ?? '')).toBeNull();
  });

  /**
   * **A withheld seat is marked, not emptied**, and the mark is a **set difference** against the
   * rows the record still holds — a withheld row carries one field and no id, so there is
   * nothing else to derive it from.
   *
   * The row is driven off a line-up's own `candidates`, which is the union the contract has:
   * *"branch on `withheld`"*. The derivation does not care which route produced the rows.
   */
  it('marks a seat whose player the record no longer describes, and keeps them seated', async () => {
    transport.on('POST', LINEUPS, () =>
      json(seatedFour({ candidates: [card(B), card(C), { withheld: true }] })),
    );
    await openTheBuilder();
    await pressFill();

    await screen.findByLabelText(summary(4));
    // The seat still holds somebody — the court is four of four — and it states the fact, in
    // both registers: the seat's own name for a listener, and the sentence for a reader.
    expect(screen.getByLabelText(seatLabel('THEIR_SIDE', { kind: 'withheld' }))).toBeTruthy();
    expect(screen.getByText(WITHHELD_SEAT_LINE, { includeHiddenElements: true })).toBeTruthy();
    // And they are still in the line-up, so they are still in the forecast: dropping them
    // would force a second cause for *provisional*.
    expect(usePlaySession.getState().lineup?.seats).toEqual([C, B, D]);
    expect(screen.getByText('91%')).toBeTruthy();
  });

  /** The court never says **why**: four gates reach one sentence, and naming one names a person. */
  it('states the fact and never the cause', async () => {
    transport.on('POST', LINEUPS, () =>
      json(seatedFour({ candidates: [card(B), card(C), { withheld: true }] })),
    );
    await openTheBuilder();
    await pressFill();

    await screen.findByLabelText(summary(4));
    for (const word of [/blocked/i, /suspended/i, /hold/i, /preference/i]) {
      expect(screen.queryByText(word)).toBeNull();
    }
  });

  /** A dock, never a refusal: nobody is removed from the court for it. */
  it('states a shared-slot dock without emptying anybody', async () => {
    transport.on('POST', LINEUPS, () => {
      const answer = seatedFour();
      return json({ ...answer, lineup: { ...answer.lineup, dock: 'NO_SHARED_SLOTS' } });
    });
    await openTheBuilder();
    await pressFill();

    expect(await screen.findByLabelText(summary(4))).toBeTruthy();
    expect(screen.getByText(unfilledSeatLine('NO_SHARED_SLOTS'))).toBeTruthy();
  });
});

/**
 * **Who is this person?** — which had no answer anywhere in the product until
 * [#384](https://github.com/Raketa02/Raketa/issues/384).
 *
 * A face was a picture of a person that opened a weights-and-contributions table. It now opens
 * the person, and the pairing's arithmetic is a row inside what opens — so the two gestures that
 * used to give one answer twice give two different answers
 * ([#285](https://github.com/Raketa02/Raketa/issues/285) deleted the hold; this deleted what was
 * left of the duplication).
 *
 * What is asserted here is the shape of the answer rather than the sheet's contents, and most
 * of it is about something that must **not** happen: no button promising a Fit, no distance on
 * your own record, no Fit row where there is no pairing, no claim about tags out of the app's
 * own ignorance, and no retry on a refusal that would answer identically.
 */
describe('who this person is', () => {
  const RECORD_OF = (playerId: string) => `/api/v1/players/${playerId}/record?sport=PADEL`;
  const OWN_RECORD = '/api/v1/players/me/record?sport=PADEL';

  function record(over: Partial<Wire['PlayerRecordResponse']> = {}): Wire['PlayerRecordResponse'] {
    return {
      is_self: false,
      nickname: NAMES[C] ?? 'cyryl',
      area_code: 'A+050612+0019938',
      social_tags: ['PLAYS_TO_WIN'],
      sports: [{ sport: 'PADEL', level: 2.71, band: 'Established' }],
      skill: {
        sport: 'PADEL',
        level: 2.71,
        band: 'Established',
        confidence: 77,
        counted_games: 21,
        likely_range: { low: 2.55, high: 2.87 },
        last_five: ['WIN', 'WIN', 'LOSS'],
      },
      reliability: {
        player_score: 93,
        strands: [
          { strand: 'SHOWS_UP', good: 9, opportunities: 9, pct: 100 },
          { strand: 'ANSWERS_CHALLENGES', good: 11, opportunities: 11, pct: 100 },
          { strand: 'ANSWERS_RESULTS', good: 8, opportunities: 10, pct: 80 },
        ],
      },
      variety: { distinct_opponents: 14, games_played: 20 },
      sportsmanship: { average: 4.7, raters: 17 },
      ...over,
    };
  }

  /** Every square drawn on screen, found by the one size only the run of form draws. */
  function squares(): readonly ViewStyle[] {
    return screen
      .UNSAFE_getAllByType(View)
      .map((box) => flatten(box.props.style))
      .filter((style): style is ViewStyle => style?.width === theme.size.recordSquare);
  }

  async function openAFace() {
    transport.on('GET', RECORD_OF(C), () => json(record()));
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(named('YOUR_PARTNER', C));
  }

  it('opens the record on a tap, which is the gesture a listener can reach', async () => {
    await openAFace();

    expect(await screen.findByLabelText(recordCloseLabel(false))).toBeTruthy();
    expect(screen.getByText(RECORD_TITLE)).toBeTruthy();
    expect(await screen.findByText(NAMES[C] ?? '')).toBeTruthy();
  });

  /**
   * **The face names the record it opens, and no longer names the Fit.** A button promising
   * *why fit 78* that opened a photograph and a run of form would be the one kind of label that
   * is worse than none.
   */
  it('says what it opens, and no face on the card announces a Fit', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    expect(screen.queryAllByLabelText(/why fit/i)).toHaveLength(0);
    expect(screen.getAllByLabelText(/player record$/)).toHaveLength(3);
  });

  /**
   * **The shortcut is gone, and its removal is asserted rather than assumed.**
   *
   * A `longPress` on a `Pressable` with no `onLongPress` is silently a no-op, so a hold that
   * quietly came back — or one that never left — would show no symptom anywhere else.
   */
  it('opens nothing from a hold on the seat, because the face is the route', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent(seat('YOUR_PARTNER', C), 'longPress');

    expect(screen.queryByText(RECORD_TITLE)).toBeNull();
    // And the tap's own act did not fire underneath it either.
    expect(screen).toHavePathname('/play/builder');
  });

  it('hides the two side headings, because each face says its own side', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    for (const heading of [SIDE_HEADINGS.yours, SIDE_HEADINGS.theirs]) {
      expect(screen.queryByText(heading)).toBeNull();
      expect(screen.getByText(heading, { includeHiddenElements: true })).toBeTruthy();
    }
  });

  /**
   * **The face is what made the hold deletable** — the route is a control with a picture of
   * the person on it rather than a gesture nothing advertises.
   *
   * Counted through the poster's own name, because every seeded card here has no `photo_url`:
   * four seats and four row entries is eight posters, where before the row drew none.
   */
  it('draws a face for every seat, which is what the row is a control over', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    expect(screen.getAllByLabelText(POSTER_LABEL, { includeHiddenElements: true })).toHaveLength(8);
  });

  /**
   * **Your own face is a control for the first time.** It opens the ungated route, which is the
   * one that answers a held player — the reader this screen most exists for — and the sheet
   * retitles to the outside view rather than reading as a settings screen.
   */
  it('opens your own record retitled, and says nothing about where you are', async () => {
    // The searcher's own area, which the envelope carries and no route serves today (#279).
    // Served here so the self case is exercised rather than passing by absence: the two codes
    // are then equal by construction, and a line that dropped only the kilometres would tell
    // somebody they are in their own area.
    const full = seatedFour();
    transport.on('POST', LINEUPS, () =>
      json({ ...full, search: { ...full.search, my_area_code: 'A+050612+0019938' } }),
    );
    transport.on('GET', OWN_RECORD, () => json(record({ is_self: true, nickname: 'me_myself' })));
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(yourFace('YOUR_SIDE'));

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
    expect(screen.queryByText(RECORD_TITLE)).toBeNull();
    // **Waited for**, because the title is drawn while the sheet is still filling: every
    // assertion below is about something the record does *not* say, and a skeleton says none of
    // it either.
    expect(await screen.findByText(`me_myself ${YOU_MARK}`)).toBeTruthy();
    // Neither half of the identity line: nought kilometres from yourself is not a fact, and
    // neither is being in your own area.
    expect(screen.queryByText('4 km')).toBeNull();
    expect(screen.queryByText(new RegExp(IN_YOUR_AREA))).toBeNull();
    expect(transport.requestsTo('GET', OWN_RECORD)).toHaveLength(1);
  });

  /**
   * **A pairing fact appears only where a pairing is in hand.** Your own seat carries no
   * candidate row, because no route serves a searcher their own — so the record opened from
   * your own face offers nothing to explain, exactly as one opened later from a chat will not.
   */
  it('offers the Fit breakdown from a seated face and from nowhere without a pairing', async () => {
    await openAFace();

    fireEvent.press(await screen.findByLabelText(fitRowLabel(78)));

    expect(await screen.findByLabelText(WHY_FIT)).toBeTruthy();
  });

  it('offers no Fit row on your own record', async () => {
    transport.on('GET', OWN_RECORD, () => json(record({ is_self: true })));
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(yourFace('YOUR_SIDE'));
    // The record, not the title: the title is drawn while the sheet is still filling, and a
    // skeleton offers no Fit row either.
    await screen.findByText(`${NAMES[C] ?? ''} ${YOU_MARK}`);

    expect(screen.queryByLabelText(fitRowLabel(78))).toBeNull();
  });

  /**
   * **The card is headed with the rule it enforces**, and every row on it prints the pair it was
   * measured over: a perfect record over nine games and one over forty draw the same bar, so the
   * bar is never the claim ([#385](https://github.com/Raketa02/Raketa/issues/385)).
   */
  it('draws the counted rows and the variety pair, each with its raw fraction', async () => {
    await openAFace();
    await screen.findByText(NAMES[C] ?? '');

    expect(screen.getByText(RECORD_CARD_TITLE_DRAWN)).toBeTruthy();
    for (const strand of ['SHOWS_UP', 'ANSWERS_CHALLENGES', 'ANSWERS_RESULTS'] as const) {
      expect(screen.getByText(STRAND_NAME[strand])).toBeTruthy();
    }
    expect(screen.getByText(strandFraction({ good: 8, opportunities: 10 }))).toBeTruthy();
    // The share **and** the pair: a bare `70%` would break the rule the card just made.
    expect(screen.getByText(varietyValue({ distinctOpponents: 14, gamesPlayed: 20 }))).toBeTruthy();
  });

  /**
   * **What other players said stands outside the counted card**, under a heading naming its own
   * author — because that card's heading is a promise about authorship and this is the one thing
   * on the sheet people wrote ([#387](https://github.com/Raketa02/Raketa/issues/387)).
   */
  it('draws the average and the count of raters, in a block of its own', async () => {
    await openAFace();
    await screen.findByText(NAMES[C] ?? '');

    expect(screen.getByText(OPINION_CARD_TITLE_DRAWN)).toBeTruthy();
    expect(screen.getByText(opinionFigure({ average: 4.7, raters: 17 }))).toBeTruthy();
  });

  /**
   * **The subject is answered with a band and never with the figure.** An average beside a count
   * lets them subtract each new rating out and name it, and they know who they played — so the
   * arm is chosen from `is_self` at the wire boundary, and a response carrying both draws the
   * band. Asserted end to end here, because that is where a response can carry both.
   */
  it('draws a band and no count on your own record, whatever the response carried', async () => {
    transport.on('GET', OWN_RECORD, () =>
      json(record({ is_self: true, nickname: 'me_myself', sportsmanship_band: 'GOOD' })),
    );
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(yourFace('YOUR_SIDE'));
    await screen.findByText(`me_myself ${YOU_MARK}`);

    expect(screen.getByText(OPINION_BAND_NAME.GOOD)).toBeTruthy();
    expect(screen.getByText(BAND_HAS_NO_COUNT)).toBeTruthy();
    // Neither half on its own either: the average is what a subtraction starts from, and the
    // count is what makes each new answer name itself.
    expect(screen.queryByText(opinionFigure({ average: 4.7, raters: 17 }))).toBeNull();
    expect(screen.queryByText(/4,7/)).toBeNull();
    expect(screen.queryByText(/17 players/)).toBeNull();
  });

  /**
   * **A newcomer's record is a short sheet, never a card of noughts.** Nothing has fallen due
   * for most players on this platform today, and *we have not seen enough* must not be drawn as
   * *they are bad at this* — which is what a heading over an empty box would say.
   *
   * Nobody has rated them either, and that is a **fourth** absence rather than the same one:
   * rating is a favour, nothing records that a card was ignored, and a player with a full
   * record of counted games may have been rated by nobody. Both blocks go, and so does every
   * sentence either of them would have said about a Player Score that is not on the sheet.
   */
  it('draws no record card, no opinion and no Player Score, for somebody nothing has fallen due for', async () => {
    transport.on('GET', RECORD_OF(C), () => {
      const {
        reliability: _reliability,
        variety: _variety,
        sportsmanship: _sportsmanship,
        ...rest
      } = record();
      return json(rest);
    });
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(named('YOUR_PARTNER', C));
    await screen.findByText(NAMES[C] ?? '');

    expect(screen.queryByText(RECORD_CARD_TITLE_DRAWN)).toBeNull();
    expect(screen.queryByText(OPINION_CARD_TITLE_DRAWN)).toBeNull();
    expect(screen.queryByText(new RegExp(PLAYER_SCORE_NAME))).toBeNull();
  });

  /**
   * **A run of three is drawn as three.** The gap where the other two would be is the honest
   * statement, and it is at the end, where the newest results are not yet.
   */
  it('draws a short run short and never pads it', async () => {
    await openAFace();
    await screen.findByText(NAMES[C] ?? '');

    expect(squares()).toHaveLength(3);
  });

  /**
   * **The band is a key the server sent, never a number this client banded.** Served here as
   * *Advanced* over a Level that sits in Established, so a client deriving one from the other
   * would say the wrong word.
   */
  it('draws the band it was served rather than one derived from the Level', async () => {
    transport.on('GET', RECORD_OF(C), () =>
      json(
        record({
          skill: { ...record().skill!, band: 'Advanced' },
          sports: [{ sport: 'PADEL', level: 2.71, band: 'Advanced' }],
        }),
      ),
    );
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');
    fireEvent.press(named('YOUR_PARTNER', C));

    expect(await screen.findByLabelText(/Advanced/)).toBeTruthy();
  });

  /**
   * **No overlap passed is not *nothing in common*.** This fixture's candidates carry no tag
   * terms, so the engine made no comparison — the tags are drawn as facts about their owner and
   * the amber claim is never written.
   */
  it('draws their tags untinted and claims nothing about common ground', async () => {
    await openAFace();

    expect(
      await screen.findByText(socialTagChip({ id: 'PLAYS_TO_WIN', shared: false })),
    ).toBeTruthy();
    expect(screen.queryByText(NO_TAGS_IN_COMMON)).toBeNull();
  });

  /**
   * **One line and nothing else**, whatever the cause. Never disclosed, blocked either way,
   * held and no such player answer the same code with the same body, and a control offering to
   * ask again would be offering to receive the same refusal.
   */
  it('draws one line for a record that cannot be opened, and no way to ask again', async () => {
    transport.on('GET', RECORD_OF(C), () => errorResponse(404, 'record_unavailable'));
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(named('YOUR_PARTNER', C));

    expect(await screen.findByText(RECORD_UNAVAILABLE)).toBeTruthy();
    expect(screen.queryByLabelText(/try again/i)).toBeNull();
    // The sheet is still up, and it is still the sheet: a refusal is not a screen of its own.
    expect(screen.getByText(RECORD_TITLE)).toBeTruthy();
  });

  /** Nothing is read for a face nobody tapped: four faces, and no request until one is. */
  it('reads nothing until a face is tapped', async () => {
    transport.on('GET', RECORD_OF(C), () => json(record()));
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    expect(transport.requestsTo('GET', RECORD_OF(C))).toHaveLength(0);

    fireEvent.press(named('YOUR_PARTNER', C));
    await screen.findByText(NAMES[C] ?? '');

    expect(transport.requestsTo('GET', RECORD_OF(C))).toHaveLength(1);
  });

  /**
   * **A withheld seat keeps its face and is not a control.** The record route answers `404` for
   * a row the product has since agreed not to show, and a face that opened an apology is what
   * this rule has always refused.
   */
  it('draws no button for a player the record no longer describes', async () => {
    transport.on('POST', LINEUPS, () =>
      json(seatedFour({ candidates: [card(B), card(C), { withheld: true }] })),
    );
    await openTheBuilder();
    await pressFill();
    await screen.findByLabelText(summary(4));

    // The two the record still holds a row for, and your own seat, which opens the other route.
    expect(named('YOUR_PARTNER', C)).toBeTruthy();
    expect(named('THEIR_SIDE', B)).toBeTruthy();
    expect(yourFace('YOUR_SIDE')).toBeTruthy();
    // Four seats, three ways in.
    expect(screen.queryAllByLabelText(/player record$|how others see you$/)).toHaveLength(3);
    // The withheld face is still **drawn** — a face that opens nothing is not a face that
    // vanished, and a panel holds one box per seat rather than only the seats it can describe.
    // The withheld handle's `?` is `playerName`'s unknown, and it reaches the panel's own line
    // the way every handle does: joined into the side's name.
    // Two of them, and both are drawings: the bar's segment and the panel's own line.
    expect(
      screen.getAllByText(sideName([NAMES[B] ?? '', '?'], SIDE_HEADINGS.theirs), {
        includeHiddenElements: true,
      }),
    ).toHaveLength(2);
  });

  /** The same rule on the shortcut: a seat with nothing behind it carries no gesture. */
  it('holds nothing on a seat whose player the record no longer describes', async () => {
    transport.on('POST', LINEUPS, () =>
      json(seatedFour({ candidates: [card(B), card(C), { withheld: true }] })),
    );
    await openTheBuilder();
    await pressFill();
    await screen.findByLabelText(summary(4));

    fireEvent(screen.getByLabelText(seatLabel('THEIR_SIDE', { kind: 'withheld' })), 'longPress');

    expect(screen.queryByText(RECORD_TITLE)).toBeNull();
  });

  /**
   * **It opens tall and stays that size.** The header and the scroll are `BottomSheet`'s; what
   * is this sheet's own is the standing height, so a skeleton three lines tall does not grow
   * into most of the screen when the answer lands and read as two different surfaces.
   */
  it('opens at one height whether or not the record has landed yet', async () => {
    transport.on('GET', RECORD_OF(C), () => json(record()));
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(named('YOUR_PARTNER', C));
    const standing = tallestStanding();

    await screen.findByText(NAMES[C] ?? '');

    expect(standing).toBeGreaterThan(0);
    expect(tallestStanding()).toBe(standing);
  });

  /** The sheet's body's own floor, found by the one style in the tree that carries a minimum. */
  function tallestStanding(): number {
    return Math.max(
      0,
      ...screen
        .UNSAFE_getAllByType(View)
        .map((box) => flatten(box.props.style)?.minHeight)
        .filter((floor): floor is number => typeof floor === 'number'),
    );
  }

  /** The faces are unaffected by the swap toggle: the route stays open while the shortcut shuts. */
  it('keeps the faces a way in while the toggle is on', async () => {
    transport.on('GET', RECORD_OF(C), () => json(record()));
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(named('YOUR_PARTNER', C));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
  });
});

/**
 * **Nothing in Play retries without the player asking**, and *a retry belongs to the act that
 * failed*. The builder has two acts and they fail differently: ⚡ is a recording write whose
 * own control is the retry, and the forecast is the one wait in the tab that gains a control
 * of its own — a player who has stopped changing seats would otherwise sit with no number.
 */
describe('when it fails', () => {
  it('states ⚡s refusal over the control that failed, and retries nothing on its own', async () => {
    transport.on('POST', LINEUPS, () => errorResponse(409, 'locked_seat_not_available'));
    await openTheBuilder();

    fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 })));

    expect(
      await screen.findByText(playErrorMessage(refusal('locked_seat_not_available'))),
    ).toBeTruthy();
    // One attempt, and the control that failed is still there to be pressed again.
    expect(transport.requestsTo('POST', LINEUPS)).toHaveLength(1);
    expect(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 }))).toBeTruthy();
  });

  it('takes the wait down on a refusal rather than holding it over one', async () => {
    transport.on('POST', LINEUPS, () => errorResponse(503, 'matchmaking_unavailable'));
    await openTheBuilder();

    fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 })));

    // A refusal has nothing to hold for: the sentence and the retry are already on the screen
    // underneath, and a latch over them would bury both.
    await screen.findByText(playErrorMessage(refusal('matchmaking_unavailable')));
    expect(screen.queryByText(ENGINE_FILL)).toBeNull();
  });

  it('gives the forecast a control of its own, because no other control would ask again', async () => {
    transport.on('POST', FORECASTS, () => errorResponse(503, 'matchmaking_unavailable'));
    await openTheBuilder();
    act(() => usePlaySession.getState().seat(SEARCH_ID, B));

    expect(
      await screen.findByText(playErrorMessage(refusal('matchmaking_unavailable'))),
    ).toBeTruthy();
    // The read-back gives up the app-wide retry too, so one failure is one request.
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(1);

    fireEvent.press(screen.getByLabelText(RETRY_FORECAST_LABEL));

    await waitFor(() => expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(2));
  });

  /** Paused, not failed: `networkMode: 'online'` holds the write until the connection returns. */
  it('says a fill offline is waiting rather than covering the screen with a latch', async () => {
    await openTheBuilder();
    act(() => onlineManager.setOnline(false));

    fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 })));

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(screen.queryByText(ENGINE_FILL)).toBeNull();
  });
});

/**
 * **The court fills, and the wait is under it rather than over it.**
 *
 * `motion.hold.fill` has been `650 plus 550 a seat` since before anything drew a seat landing:
 * the latch covered the whole screen for the sum and handed back a court that was already
 * complete, so the stagger was paid for and never seen. What it is for is the arrival — people
 * sitting down at a game, one after another, which is what `POST /lineups` has just done.
 *
 * Nothing is delayed by any of it. The whole line-up is in memory before the first seat
 * appears; this is presentation over a completed answer, which `the-play-screens.md` §3
 * licenses by name.
 */
describe('the fill', () => {
  /** The court's own summary, which is the one element that counts the seats out loud. */
  const drawn = (filled: number) =>
    screen.getAllByLabelText(summary(filled), { includeHiddenElements: true });

  /**
   * Press ⚡ and wait for the **answer**, which is the moment the seats start arriving.
   *
   * The count is what says so: it is `players_in_range` off the response, absent while the
   * request is in flight, so its appearance is the one observable edge between *looking* and
   * *landing* — and driving the clock before it would spend the stagger on a request that has
   * not come back.
   */
  async function fillLands() {
    fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 })));
    await screen.findByText(ENGINE_FILL);
    await screen.findByText(ENGINE_FILL_COUNT);
  }

  /**
   * The end of the beat, from the screen's side. **Where** each seat lands in time is
   * `seatReveal`'s own suite — a boundary no snapshot can tell apart from the millisecond
   * either side of it — and what is asserted here is the half only the screen knows: the
   * line-up is committed when the last seat has landed, and not when the response did.
   */
  it('commits the line-up at the end of the beat rather than on the response', async () => {
    await openTheBuilder();
    await fillLands();

    // The answer is in memory and the court is still yours alone.
    expect(drawn(1)).toBeTruthy();

    act(() =>
      jest.advanceTimersByTime(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: false })),
    );

    await waitFor(() => expect(screen.queryByText(ENGINE_FILL)).toBeNull());
    expect(drawn(4)).toBeTruthy();
  });

  /**
   * The court is never taken away, and nothing that describes a finished line-up appears over
   * a court that has not finished landing.
   */
  it('leaves the court on screen and holds back everything that reads it', async () => {
    await openTheBuilder();

    await fillLands();

    // The court is there, under the wait rather than behind it.
    expect(drawn(1)).toBeTruthy();
    // And nothing about a four that is still arriving: no forecast, no swap toggle, and
    // neither of the two ways of filling a court that is being filled.
    expect(screen.queryByText('91%')).toBeNull();
    expect(screen.queryByLabelText(SWAP_TOGGLE_LABEL)).toBeNull();
    expect(screen.queryByLabelText(fillSeatsLabel({ seats: 4, filled: 1 }))).toBeNull();
    expect(screen.queryByLabelText(PICK_PLAYERS_LABEL)).toBeNull();

    act(() =>
      jest.advanceTimersByTime(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: false })),
    );

    expect(await screen.findByText('91%')).toBeTruthy();
  });
});

/**
 * **The forecast card, and the one sentence that says what *Even it out* would buy.**
 *
 * Every arrangement crosses, so the evenest one's own percentage is a **read** rather than a
 * calculation — which is what makes it sayable at all. The card used to draw the control and
 * no account of it: a player looking at a court arranged their way was offered a button and
 * told nothing about what pressing it changes.
 */
describe('the forecast card', () => {
  /** The two halves as the card labels them, once the evenest pairing has seated C beside you. */
  const YOURS = sideName(['You', NAMES[C] ?? ''], SIDE_HEADINGS.yours);
  const THEIRS = sideName([NAMES[B] ?? '', NAMES[D] ?? ''], SIDE_HEADINGS.theirs);

  /**
   * **The evidence behind the percentage**, and none of it computed here.
   *
   * The three figures are `split`'s, on the Skill scale: the fixture's evenest reads `3,20`
   * against `3,11` with a gap of `0,09`, and a card that averaged the seated players' levels —
   * 2,80 · 2,71 · 2,90 — could not produce any of them.
   */
  it('prints both side strengths and the gap, and names neither half twice', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    expect(screen.getByText('Pairing forecast')).toBeTruthy();
    expect(screen.getByText('3,20')).toBeTruthy();
    expect(screen.getByText('3,11')).toBeTruthy();
    expect(screen.getByText('0,09')).toBeTruthy();
    // **The row is three figures.** Who each half is, is said by the panel under it and by
    // this row's own spoken name — printing the two joined phrases here as well named these
    // four people three times on one card.
    expect(screen.queryByText(YOURS)).toBeNull();
    expect(screen.queryByText(THEIRS)).toBeNull();
    expect(
      screen.getByLabelText(
        splitRowLabel(
          { yours: YOURS, theirs: THEIRS },
          { yourSide: 3.2, theirSide: 3.11, gap: 0.09 },
        ),
      ),
    ).toBeTruthy();
  });

  /**
   * **The two things a panel is**: a 44pt box per person, and a bed that is the bar's own.
   *
   * [6.5](../../../../docs/design-system.md#65-touch-targets) bounds horizontal hit-slop by
   * the neighbour, so two faces in a row cannot each grow into the gap they share — each is
   * centred in its own 44 × 44 box instead, which is geometry nothing can spend. The bed is
   * `BALANCE_SOFT`'s rather than a colour chosen here, for the reason `BALANCE_INK` exists:
   * one place decides which amber, so the panel and the bar four lines above it cannot pick
   * two.
   */
  it('gives every face a 44pt box, and paints their side in the bar’s own tone', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    const face = flatten(named('THEIR_SIDE', B).props.style);

    expect(face?.width).toBe(theme.size.minTouch);
    expect(face?.height).toBe(theme.size.minTouch);

    // 91% is `ok`, and the panel's bed is that tone's soft. Yours is the neutral half — the
    // bar paints it `night` and never a tone — so the two beds are deliberately not a pair.
    expect(bedOf(named('THEIR_SIDE', B))).toBe(BALANCE_SOFT.ok);
    expect(bedOf(named('YOUR_PARTNER', C))).toBe(theme.color.line2);
  });

  /**
   * **One element and not six** (§20.1): the two names, the two strengths and the gap are one
   * claim, and six stops is a listener navigating a table that is drawn as a row.
   */
  it('speaks the split row as one element', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    expect(
      screen.getByLabelText(
        splitRowLabel(
          { yours: YOURS, theirs: THEIRS },
          { yourSide: 3.2, theirSide: 3.11, gap: 0.09 },
        ),
      ),
    ).toBeTruthy();
  });

  /**
   * **The bar draws the split and announces nothing.** 7.11's two-segment form has always
   * drawn exactly this and was unused here only because nothing served an advantage; what
   * keeps it silent is that the row two lines above prints all three of its numbers, so its
   * own name would be the fourth reading of one fact (§20.1's merge rule, 6.8).
   */
  it('labels both segments of the bar and keeps it out of the accessibility tree', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    // Twice in the tree and **never** to a listener: the bar's segment label and the panel's
    // own line, both drawings of what the split row above states as one element. The fixtures'
    // handles carry no word break, so the drawn form and the whole one are the same string
    // here — `playerName.test.ts` is where the cut itself is pinned.
    expect(screen.getAllByText(YOURS, { includeHiddenElements: true })).toHaveLength(2);
    expect(screen.getAllByText(THEIRS, { includeHiddenElements: true })).toHaveLength(2);
    expect(screen.queryByText(YOURS)).toBeNull();
    expect(screen.queryByText(THEIRS)).toBeNull();
    expect(screen.queryByLabelText(balanceLabel(91))).toBeNull();
  });

  /**
   * **The whole behaviour this card is judged on, in one walk** — asserted rather than assumed
   * because it rests on a backend field: `is_current` on a line-up is the **evenest**
   * arrangement ([#289](https://github.com/Raketa02/Raketa/issues/289)), so a full doubles
   * court opens with nothing left to press.
   */
  it('opens shut on the evenest, lights on a swap, and shuts again when pressed', async () => {
    await openTheBuilder();
    await pressFill();

    // Open: the closest game these four can play, and the control says so rather than offering
    // to do what has been done.
    expect(await screen.findByText('91%')).toBeTruthy();
    expect(screen.getByText(ALREADY_EVENEST)).toBeTruthy();
    expect(screen.getByLabelText(EVEN_IT_OUT_LABEL).props.accessibilityState?.disabled).toBe(true);

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('YOUR_PARTNER', C));
    fireEvent.press(seat('THEIR_SIDE', B));

    // Arranged by hand: the figure moved, the control is live, and the sentence quotes what
    // pressing it would buy.
    expect(await screen.findByText('78%')).toBeTruthy();
    expect(screen.getByText(arrangedYourWayLine('91%'))).toBeTruthy();
    expect(screen.queryByText(ALREADY_EVENEST)).toBeNull();
    expect(screen.getByLabelText(EVEN_IT_OUT_LABEL).props.accessibilityState?.disabled).toBe(false);

    fireEvent.press(screen.getByLabelText(EVEN_IT_OUT_LABEL));

    expect(await screen.findByText('91%')).toBeTruthy();
    expect(screen.getByText(ALREADY_EVENEST)).toBeTruthy();
    expect(screen.getByLabelText(EVEN_IT_OUT_LABEL).props.accessibilityState?.disabled).toBe(true);
    // Three arrangements crossed with the fill, so all of that was a selection.
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(0);
  });

  /**
   * **Trading the two opponents is the same game.** A pairing is who is beside you, so the
   * seats move, the figure holds, and no sentence is owed for it — decided, not overlooked.
   */
  it('moves the seats and holds the figure when the two opponents trade', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');
    const saidBefore = spoken().length;

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('THEIR_SIDE', B));
    fireEvent.press(seat('THEIR_SIDE', D));

    // The court changed — their half reads the other way round — and nothing else did. Drawn
    // rather than spoken: the panel and the bar say who is on a half, and the split row above
    // them says it once as part of one element.
    expect(
      await screen.findAllByText(sideName([NAMES[D] ?? '', NAMES[B] ?? ''], SIDE_HEADINGS.theirs), {
        includeHiddenElements: true,
      }),
    ).toHaveLength(2);
    expect(screen.getByText('91%')).toBeTruthy();
    expect(screen.getByText(ALREADY_EVENEST)).toBeTruthy();
    expect(spoken()).toHaveLength(saidBefore);
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(0);
  });

  /** Both acts on the four are in the card, because both are acts on the four. */
  it('empties the court from inside the card', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('91%');

    fireEvent.press(screen.getByLabelText(START_OVER_LABEL));

    expect(await screen.findByLabelText(summary(1))).toBeTruthy();
    expect(screen.queryByText('91%')).toBeNull();
  });
});

/**
 * **The same card with two people on it** — one arrangement, nothing to rearrange, and a
 * heading that says which of the two things it is drawing.
 *
 * Singles is where the split stops being two pairs and becomes two players: `your_side` is you
 * and `their_side` is your opponent, so the row prints two levels and the difference between
 * them. *Even it out* is not drawn at all, because a court with one way round has nothing the
 * control could select.
 */
describe('singles', () => {
  const TENNIS_POOL: Wire['SearchEnvelope']['pool'] = {
    sport: 'TENNIS',
    radius_km_used: 12,
    players_in_range: 7,
    window: 'THIS_WEEK',
    post_gate: true,
  };

  const TENNIS_SEATS = courtSeatCount('tennis');
  const TENNIS_RANKING = poolRankingStatus({
    playersInRange: undefined,
    sportName: 'Tennis',
  }).headline;
  const TENNIS_FILL = engineFillStatus({
    playersInRange: undefined,
    seats: TENNIS_SEATS,
  }).headline;

  const tennisCourt = (filled: number) =>
    courtSummaryLabel({ sportName: 'Tennis', filled, seats: TENNIS_SEATS });

  const tennisShortlist = (): Wire['ShortlistResponse'] => ({
    search: envelope(SEARCH_ID, { pool: TENNIS_POOL }),
    candidates: [card(B)],
  });

  /** One way round, because there is one. The split is two player strengths and their gap. */
  const tennisLineup = (): Wire['LineupResponse'] => ({
    search: envelope(LINEUP_ID, { surface: 'LINEUP', pool: TENNIS_POOL }),
    candidates: [card(B)],
    lineup: {
      seats: [
        { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
        { side: 'B', seat_index: 1, relationship: 'OPPONENT', player_id: B },
      ],
      arrangements: [
        {
          pairing_id: 1,
          is_current: true,
          is_evenest: true,
          sides: {
            A: [{ seat_index: 0, relationship: 'SELF', player_id: ME }],
            B: [{ seat_index: 1, relationship: 'OPPONENT', player_id: B }],
          },
          forecast: { pct: 84, sigma_group: 0.4, provisional: false, assumption: null },
          split: { your_side: 2.71, their_side: 2.8, gap: -0.09 },
        },
      ],
    },
  });

  beforeEach(() => {
    stubGate(transport, { id: ME, ratings: [rating('TENNIS')], hasPlayerProfile: true });
    stubProfileSurface(transport, {
      ...PROFILE_SURFACE_SERVED,
      play_intents: { TENNIS: 'FOR_FUN' },
    });
    transport.on('POST', SEARCHES, () => json(tennisShortlist()));
    transport.on('POST', LINEUPS, () => json(tennisLineup()));
  });

  /** Search, spend the latch, and let the engine seat the one empty seat a match has. */
  async function openTheMatch() {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    await screen.findByLabelText('Tuesday evening');

    fireEvent.press(screen.getByLabelText(courtEntryLabel(TENNIS_SEATS)));
    await screen.findByText(TENNIS_RANKING);
    act(() => jest.advanceTimersByTime(searchingFloorMs({ kind: 'pool' })));

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    await screen.findByLabelText(tennisCourt(1));

    fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: TENNIS_SEATS, filled: 1 })));
    await screen.findByText(TENNIS_FILL);
    act(() =>
      jest.advanceTimersByTime(
        searchingFloorMs({ kind: 'fill', seats: TENNIS_SEATS, collapsed: false }),
      ),
    );
    await waitFor(() => expect(screen.queryByText(TENNIS_FILL)).toBeNull());
  }

  it('draws the same card with two players, and no way to rearrange them', async () => {
    await openTheMatch();

    expect(await screen.findByText('84%')).toBeTruthy();
    // The other heading — one per court shape, and the mode is already in the eyebrow.
    expect(screen.getByText('Balance forecast')).toBeTruthy();
    expect(screen.getByText('2,71')).toBeTruthy();
    expect(screen.getByText('2,80')).toBeTruthy();
    // Signed, as it was served: the sign is which way the match leans, and stripping it here
    // would be this screen doing arithmetic over a number it was handed.
    expect(screen.getByText('\u22120,09')).toBeTruthy();
    expect(
      screen.getByLabelText(
        splitRowLabel(
          { yours: 'You', theirs: NAMES[B] ?? '' },
          { yourSide: 2.71, theirSide: 2.8, gap: -0.09 },
        ),
      ),
    ).toBeTruthy();

    // One arrangement, so nothing to select — and *Start over* alone in the row.
    expect(screen.queryByLabelText(EVEN_IT_OUT_LABEL)).toBeNull();
    expect(screen.getByLabelText(START_OVER_LABEL)).toBeTruthy();
  });
});

/**
 * **The questions ⚡ raises, and the beat there is nowhere to put them in.**
 *
 * `POST /lineups` mints a search like `POST /searches` does, so it raises prompts like one.
 * Find a game asks them between the latch lifting and the court being pushed; here the court
 * **is** what the fill landed on, so the sheet stands in front of an answer that is already on
 * screen — and the one prompt whose *yes* is a request for the week grid never reaches a screen
 * that has no grid ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 */
describe('the question ⚡ raised', () => {
  const KEEP_THIS_RADIUS = promptCopy({ prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 }).title;
  const REFRESH_YOUR_TIMES = promptCopy({ prompt: 'REFRESH_YOUR_TIMES' }).title;

  const raising = (prompts: readonly Wire['PromptSchema'][]) =>
    transport.on('POST', LINEUPS, () => json(seatedFour({ prompts })));

  it('waits for the latch, and is asked over the court the fill landed on', async () => {
    raising([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await openTheBuilder();

    fireEvent.press(screen.getByLabelText(fillSeatsLabel({ seats: 4, filled: 1 })));
    await screen.findByText(ENGINE_FILL);
    await waitFor(() => expect(transport.requestsTo('POST', LINEUPS)).toHaveLength(1));

    // The answer is in memory and the question is not on screen: the wait is what the sheet
    // is behind, and the court is what the wait lifts onto.
    expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull();

    act(() =>
      jest.advanceTimersByTime(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: false })),
    );

    expect(await screen.findByText(KEEP_THIS_RADIUS)).toBeTruthy();
    // Nothing was pushed: the court under the sheet is the one ⚡ filled.
    expect(screen).toHavePathname('/play/builder');
  });

  it('writes its yes through the route that owns the value, and no decline', async () => {
    raising([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await openTheBuilder();
    await pressFill();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').accept));

    await waitFor(() => expect(transport.requestsTo('PUT', RADIUS)).toHaveLength(1));
    expect(transport.requestsTo('PUT', RADIUS)[0]?.body).toEqual({ search_radius_km: 22 });
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
    // Answered, and the court ⚡ filled is what the sheet closes onto — nothing was pushed.
    await waitFor(() => expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull());
    expect(screen.getByLabelText(summary(4))).toBeTruthy();
  });

  it('is a decline when it is dismissed, written about the question and never the value', async () => {
    raising([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await openTheBuilder();
    await pressFill();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').close));

    await waitFor(() => expect(transport.requestsTo('POST', DECLINES)).toHaveLength(1));
    expect(transport.requestsTo('POST', DECLINES)[0]?.body).toEqual({
      prompt: 'KEEP_THIS_RADIUS',
      sport: 'PADEL',
    });
    // Answered, and the court it was asked over is reachable again.
    await waitFor(() => expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull());
    expect(screen.getByLabelText(summary(4))).toBeTruthy();
  });

  /**
   * Dropped rather than truncated to, which is why the fixture puts it first: what the sheet
   * asks is the next question a screen with no week grid can honour.
   */
  it('is never the one whose yes is a week grid this screen does not have', async () => {
    raising([{ prompt: 'REFRESH_YOUR_TIMES' }, { prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await openTheBuilder();
    await pressFill();

    expect(await screen.findByText(KEEP_THIS_RADIUS)).toBeTruthy();
    expect(screen.queryByText(REFRESH_YOUR_TIMES)).toBeNull();
  });

  it('leaves the court alone where the only question raised is that one', async () => {
    raising([{ prompt: 'REFRESH_YOUR_TIMES' }]);
    await openTheBuilder();
    await pressFill();

    // No sheet at all — the filled court is reachable, which it would not be behind one.
    expect(await screen.findByLabelText(summary(4))).toBeTruthy();
    expect(screen.queryByText(REFRESH_YOUR_TIMES)).toBeNull();
  });

  /**
   * **A question already answered on Find a game is not asked again by ⚡**
   * ([#287](https://github.com/Raketa02/Raketa/issues/287)).
   *
   * The flow is two taps: search on an improvised week, dismiss *Keep these times?*, press ⚡.
   * ⚡ mints a search of its own, so a memory keyed by the minted id could not see that the
   * question had been put — and `KEEP_THESE_TIMES` is precisely the prompt whose decline
   * writes **no durable row** (`promptSuppresses`), so nothing on the server declines to raise
   * it a second time either. The visit's own list in `playSession` is the whole of what stands
   * between *not now* and the identical sheet two taps later.
   */
  it('does not ask again what Find a game already asked over the same week', async () => {
    const keepTheseTimes: Wire['PromptSchema'] = {
      prompt: 'KEEP_THESE_TIMES',
      slots: [{ day: 1, part: 'MORNING' }],
    };
    const KEEP_THESE_TIMES = promptCopy({
      prompt: 'KEEP_THESE_TIMES',
      week: [],
      profileWeek: [],
    }).title;

    // One improvised week, and both searches over it raise the same question about it.
    transport.on('POST', SEARCHES, () => json(shortlist([keepTheseTimes])));
    raising([keepTheseTimes]);

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByLabelText('Monday morning'));

    fireEvent.press(screen.getByLabelText(courtEntryLabel(courtSeatCount('padel'))));
    await screen.findByText(POOL_RANKING);
    act(() => jest.advanceTimersByTime(searchingFloorMs({ kind: 'pool' })));

    // Asked once, on the screen the week is edited on, and dismissed — which is *not now*.
    await screen.findByText(KEEP_THESE_TIMES);
    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THESE_TIMES').close));
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    await screen.findByLabelText(summary(1));

    await pressFill();

    // The court ⚡ filled is reachable, which it would not be behind a second sheet.
    expect(await screen.findByLabelText(summary(4))).toBeTruthy();
    expect(screen.queryByText(KEEP_THESE_TIMES)).toBeNull();
    // And *not now* was written once, about the question, by the one screen that asked it.
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });
});

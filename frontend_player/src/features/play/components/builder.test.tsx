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
 */

import { AccessibilityInfo } from 'react-native';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { onlineManager } from '@tanstack/react-query';

import { offlineMessage, type AppError } from '@/shared/errors';
import { queryClient } from '@/shared/lib/query-client';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import {
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
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { usePlayPreferences } from '../store/playPreferences.store';
import { endPlaySession, usePlaySession } from '../store/playSession.store';

import {
  courtSummaryLabel,
  provisionalForecastAnnouncement,
  seatLabel,
  SWAP_TOGGLE_LABEL,
} from './accessibilityPresentation';
import { balanceWord } from './balancePresentation';
import { CANDIDATE_POSTER_LABEL } from './playerCardPresentation';
import {
  PICK_PLAYERS_LABEL,
  PROVISIONAL_WORD,
  RETRY_FORECAST_LABEL,
  fillSeatsLabel,
  seatsOpenLine,
} from './builderPresentation';
import { WITHHELD_SEAT_LINE, optimisedForLine, unfilledSeatLine } from './courtPresentation';
import { playErrorMessage } from './playErrorMessage';
import { engineFillStatus, poolRankingStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';

/** The two waits' headlines, taken from their own copy rather than spelled here. */
const POOL_RANKING = poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline;
const ENGINE_FILL = engineFillStatus({ playersInRange: undefined }).headline;

const SEARCHES = '/api/v1/searches';
const LINEUPS = '/api/v1/lineups';
const FORECASTS = '/api/v1/forecasts';

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

const shortlist = (): Wire['ShortlistResponse'] => ({
  search: envelope(SEARCH_ID),
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
  };
}

const THREE_WAYS = [
  arrangement(B, [C, D], { id: 1, pct: 78, current: true }),
  arrangement(C, [B, D], { id: 2, pct: 91, evenest: true }),
  arrangement(D, [B, C], { id: 3, pct: 64 }),
];

interface FullCourt {
  readonly optimisedFor?: Wire['OptimisedFor'];
  readonly candidates?: Wire['LineupResponse']['candidates'];
}

/** ⚡'s answer with every seat taken. */
function seatedFour(over: FullCourt = {}): Wire['LineupResponse'] {
  return {
    search: envelope(LINEUP_ID, {
      surface: 'LINEUP',
      ...(over.optimisedFor === undefined ? {} : { optimised_for: over.optimisedFor }),
    }),
    candidates: over.candidates ?? [card(B), card(C), card(D)],
    lineup: {
      seats: [
        { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
        { side: 'A', seat_index: 1, relationship: 'PARTNER', player_id: B },
        { side: 'B', seat_index: 2, relationship: 'OPPONENT', player_id: C },
        { side: 'B', seat_index: 3, relationship: 'OPPONENT', player_id: D },
      ],
      arrangements: THREE_WAYS,
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

const forecastResponse = (): Wire['ForecastResponse'] => ({
  arrangements: THREE_WAYS,
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
  transport.on('POST', FORECASTS, () => json(forecastResponse()));
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

/** The shape `playErrorMessage` reads — the code, never the backend's own message. */
const refusal = (code: string): AppError => ({ recovery: 'business-conflict', code }) as AppError;

const summary = (filled: number) => courtSummaryLabel({ sportName: 'Padel', filled, seats: 4 });

/** Search, spend the latch, and arrive on the court the search minted. */
async function openTheBuilder() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await screen.findByLabelText('Tuesday evening');

  fireEvent.press(screen.getByLabelText('Search'));
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
  it('opens on an empty court that seats you, with the seats it has still open', async () => {
    await openTheBuilder();

    expect(screen.getByLabelText(seatLabel('YOUR_SIDE', { kind: 'you' }))).toBeTruthy();
    expect(screen.getByText(seatsOpenLine(3))).toBeTruthy();
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

    expect(
      screen.getAllByLabelText(CANDIDATE_POSTER_LABEL, { includeHiddenElements: true }),
    ).toHaveLength(1);
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
    expect(seat('YOUR_PARTNER', B)).toBeTruthy();
    expect(seat('THEIR_SIDE', C)).toBeTruthy();
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

    // 78 is on no path any arithmetic over these levels would reach — it is read, or it is
    // not on screen at all.
    expect(await screen.findByText('78%')).toBeTruthy();
    // Part 13: the tint is never the only carrier, so the word is drawn beside the figure.
    expect(screen.getByText(balanceWord(78))).toBeTruthy();
  });

  /**
   * **A swap is a selection.** Every arrangement crossed with the fill, so trading two seats
   * moves the figure with no request behind it.
   */
  it('moves the figure on a swap without asking the server anything', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('78%');

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('YOUR_PARTNER', B));
    fireEvent.press(seat('THEIR_SIDE', C));

    expect(await screen.findByText('91%')).toBeTruthy();
    expect(transport.requestsTo('POST', FORECASTS)).toHaveLength(0);
  });

  /** **Change sides, never seats**: the four are the same four after a trade. */
  it('keeps everybody on the court through a swap', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('78%');

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('YOUR_PARTNER', B));
    fireEvent.press(seat('THEIR_SIDE', C));

    await screen.findByText('91%');
    expect(screen.getByLabelText(summary(4))).toBeTruthy();
    expect(usePlaySession.getState().lineup?.seats).toHaveLength(3);
  });

  /** Only **membership** round-trips: taking somebody off is a different four. */
  it('asks again when somebody leaves the court', async () => {
    await openTheBuilder();
    await pressFill();
    await screen.findByText('78%');

    fireEvent.press(screen.getByLabelText(`Remove ${NAMES[B]} from your side`));

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
    await screen.findByText('78%');

    fireEvent.press(screen.getByLabelText(SWAP_TOGGLE_LABEL));
    fireEvent.press(seat('YOUR_PARTNER', B));
    fireEvent.press(seat('THEIR_SIDE', C));

    await screen.findByText('91%');
    expect(spoken()).toContain(
      provisionalForecastAnnouncement({ pct: 91, provisional: false, assumption: null }),
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
    expect(usePlaySession.getState().lineup?.seats).toEqual([B, C, D]);
    expect(screen.getByText('78%')).toBeTruthy();
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

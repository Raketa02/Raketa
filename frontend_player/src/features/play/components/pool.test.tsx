/**
 * **The pool**, walked the way a player walks it: search, court, *Pick players myself*, and
 * the list with the ladder under it. Real route tree, real shell, real stores, only `fetch`
 * faked.
 *
 * What is asserted is the set of claims a build session could quietly undo:
 *
 * - **The ladder is here**, and every *widen* sentence is gated by `radius_clamp`.
 * - **Taking a rung cites the offer and sends no widening** — the backend reads it off the
 *   offer it made — and it replaces the list, leaving a standing statement in place of *back*.
 * - **A rung priced at nobody is a sentence rather than a button.**
 * - **The sort row is the server's list**, it vanishes when that list is empty, and the way
 *   back to the returned order survives leaving it.
 * - **The Best-fit comparator adds no `+12`.** The lift is an admission the engine already
 *   made, and re-applying it would score the wire's own ranking twice.
 * - **The pin is not that `+12`**: somebody who already said yes sits first in the served order
 *   with the number they were served, and drops into their honest place on any re-sort.
 * - **One coral *best match* tag, on the highest number, and only where the order is about the
 *   number at all.**
 * - **The header prints the balance word beneath the tinted number**, with the assumption as
 *   the sentence and no second badge.
 * - **The re-read happens here**, writes the whole record back, and is what makes a withheld
 *   row leave the list.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { router } from 'expo-router';
import { StyleSheet, type TextStyle } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import { queryClient } from '@/shared/lib/query-client';
import { courtSeatCount } from '@/shared/ui';
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
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { usePlayPreferences } from '../store/playPreferences.store';
import { endPlaySession, usePlaySession } from '../store/playSession.store';

import {
  rungOfferLabel,
  searchWeekCellLabel,
  poolHeaderLabel,
  seatLabel,
  splitRowLabel,
} from './accessibilityPresentation';
import { balanceLabel, balanceWord } from './balancePresentation';
import { PICK_PLAYERS_LABEL, PROVISIONAL_WORD, searchFacts } from './builderPresentation';
import { levelRow } from './playerCardPresentation';
import {
  POOL_COURT_LABEL,
  POOL_TITLE,
  poolLadderTitle,
  poolSeatedLine,
  replacingLine,
  rungCount,
  takenRungLine,
  terminalReachLine,
  zeroRungLine,
} from './poolPresentation';
import { courtEntryLabel, WEEK_ADDED_FOR_THIS_SEARCH } from './findAGamePresentation';
import { forecastAssumption, relaxationOffer, sortLabel } from './searchPresentation';
import { promptControls, promptCopy } from './promptPresentation';
import { poolRankingStatus } from './searchingPresentation';

const SEARCHES = '/api/v1/searches';
const DECLINES = '/api/v1/prompt-declines';
const RADIUS = '/api/v1/players/me/search-radius';
const FORECASTS = '/api/v1/forecasts';

const SEARCH_ID = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';
const WIDER_ID = 'f1a2b3c4-d5e6-4f70-8a9b-0c1d2e3f4a5c';
const ME = 'aaaaaaaa-0000-4000-8000-000000000000';
const B = 'bbbbbbbb-0000-4000-8000-000000000001';
const C = 'cccccccc-0000-4000-8000-000000000002';
const D = 'dddddddd-0000-4000-8000-000000000003';

const NAMES: Readonly<Record<string, string>> = { [B]: 'bea_k', [C]: 'cyryl', [D]: 'dorota_w' };

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

/** One row, with the two facts the pool's own assertions read: the fit, and the distance. */
function card(
  playerId: string,
  over: Partial<Wire['CandidateSchema']> = {},
): Wire['CandidateSchema'] {
  return {
    player_id: playerId,
    fit: 78,
    distance_km: 4,
    player_card: {
      nickname: NAMES[playerId] ?? 'anon',
      area_code: 'A+050612+0019938',
      social_tags: [],
      level: 2.8,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    concerns: [],
    terms: [],
    degraded_terms: [],
    modifiers: [],
    liveness_reasons: [],
    ...over,
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
      radius_km_used: 15,
      players_in_range: 6,
      window: 'THIS_WEEK',
      post_gate: true,
    },
    radius_clamp: false,
    sorts_available: ['BEST_FIT', 'CLOSEST'],
    rung_offers: null,
    ...over,
  };
}

const TIMES_RUNG: Wire['RungOfferSchema'] = {
  rung: 'A',
  ask: 'TIMES',
  candidates_above_floor: 7,
  window: 'THIS_WEEK',
  // A cell outside the profile's own week, which is the only kind a times rung offers: the
  // engine tests the additions somebody in range has ticked and the searcher has not.
  slot: { day: 4, part: 'EVENING' },
};

const RADIUS_RUNG: Wire['RungOfferSchema'] = {
  rung: 'B',
  ask: 'RADIUS',
  candidates_above_floor: 9,
  window: 'THIS_WEEK',
  radius_km: 22,
};

function shortlist(over: Partial<Wire['SearchEnvelope']> = {}): Wire['ShortlistResponse'] {
  return {
    search: envelope(SEARCH_ID, over),
    candidates: [card(B), card(C), card(D)],
  };
}

/** A forecast a client could not have computed: the figure is nothing arithmetic here gives. */
const forecastResponse = (): Wire['ForecastResponse'] => ({
  arrangements: [
    {
      pairing_id: 1,
      is_current: true,
      is_evenest: true,
      sides: {
        A: [
          { seat_index: 0, relationship: 'SELF', player_id: ME },
          { seat_index: 1, relationship: 'PARTNER', player_id: B },
        ],
        B: [
          { seat_index: 2, relationship: 'OPPONENT' },
          { seat_index: 3, relationship: 'OPPONENT' },
        ],
      },
      forecast: {
        pct: 67,
        sigma_group: 0.41,
        provisional: true,
        assumption: 'EMPTY_SEAT_MATCHES_ITS_PARTNER',
      },
      // A provisional arrangement carries a split like any other, under the
      // assumption the forecast is carried under.
      split: { your_side: 3.2, their_side: 3.53, gap: -0.33 },
    },
  ],
  engine_version: 'matchfit-v1',
  ruleset_version: 'ruleset-v1',
});

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { id: ME, ratings: [rating('PADEL')], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubInterest(transport);
  transport.on('POST', SEARCHES, () => json(shortlist()));
  transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(shortlist()));
  transport.on('POST', FORECASTS, () => json(forecastResponse()));
  transport.on('POST', DECLINES, () => noContent());
  transport.on('PUT', RADIUS, () => json<Wire['SearchRadiusResponse']>({ search_radius_km: 22 }));
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  usePlayPreferences.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Search, spend the latch, land on the court, and open the pool against its first hole. */
async function openThePool() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await screen.findByLabelText('Tuesday evening');

  fireEvent.press(screen.getByLabelText(courtEntryLabel(courtSeatCount('padel'))));
  await screen.findByText(
    poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline,
  );
  act(() => jest.advanceTimersByTime(2000));

  await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  fireEvent.press(await screen.findByLabelText(PICK_PLAYERS_LABEL));
  await waitFor(() => expect(screen).toHavePathname('/play/pool'));
  // Settled on the pool's **own** control rather than on its title: the title is the three
  // facts the search ran under now, which is the same string the court underneath still draws.
  await screen.findByLabelText(POOL_COURT_LABEL);
}

/**
 * The same walk on a Sport with **two** seats — the one shape the singles copy is read on.
 *
 * The Sport is swapped at the gate rather than by pressing a chip: *Find a game* draws its
 * chips from `GET /ratings`, so a player rated in one Sport arrives with it already chosen.
 */
async function openTheSinglesPool(
  over: Partial<Wire['SearchEnvelope']> = {},
  rows: readonly Wire['CandidateSchema'][] = [card(B), card(C)],
) {
  stubGate(transport, { id: ME, ratings: [rating('TENNIS')], hasPlayerProfile: true });
  // Declared as well as rated: a rated-but-undeclared Sport opens ADR-0094's interstitial
  // before the grid, which is a different screen from the one this walk is about.
  stubProfileSurface(transport, { ...PROFILE_SURFACE_SERVED, play_intents: { TENNIS: 'FOR_FUN' } });
  const singles = () => ({
    search: envelope(SEARCH_ID, {
      pool: {
        sport: 'TENNIS' as const,
        radius_km_used: 15,
        players_in_range: 6,
        window: 'THIS_WEEK' as const,
        post_gate: true,
      },
      ...over,
    }),
    candidates: [...rows],
  });
  transport.on('POST', SEARCHES, () => json(singles() as Wire['ShortlistResponse']));
  transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () =>
    json(singles() as Wire['ShortlistResponse']),
  );

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await screen.findByLabelText('Tuesday evening');

  fireEvent.press(screen.getByLabelText(courtEntryLabel(courtSeatCount('tennis'))));
  await screen.findByText(
    poolRankingStatus({ playersInRange: undefined, sportName: 'Tennis' }).headline,
  );
  act(() => jest.advanceTimersByTime(2000));

  await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  fireEvent.press(await screen.findByLabelText(PICK_PLAYERS_LABEL));
  await waitFor(() => expect(screen).toHavePathname('/play/pool'));
  // Settled on the pool's **own** control rather than on its title: the title is the three
  // facts the search ran under now, which is the same string the court underneath still draws.
  await screen.findByLabelText(POOL_COURT_LABEL);
}

const addLabel = (playerId: string) => `Add ${NAMES[playerId]} to the court`;

/** A rung control's whole spoken name: the offer, and the price printed on it. */
const rungLabel = (
  offer: { readonly ask: 'TIMES' } | { readonly ask: 'RADIUS'; readonly radiusKm: number },
  above: number,
) =>
  rungOfferLabel(
    relaxationOffer(offer),
    rungCount({ candidatesAboveFloor: above, window: 'THIS_WEEK' }, 'THIS_WEEK'),
  );

describe('arriving', () => {
  it('draws the ranked list, and re-reads the record it was opened on', async () => {
    await openThePool();

    expect(await screen.findByLabelText(addLabel(B))).toBeTruthy();
    expect(screen.getByLabelText(addLabel(C))).toBeTruthy();

    // The record is immutable and the gates are live, so the pool visit is where a row the
    // product has since agreed not to show can leave the list.
    await waitFor(() =>
      expect(transport.requestsTo('GET', `${SEARCHES}/${SEARCH_ID}`)).toHaveLength(1),
    );
  });

  /**
   * A withheld row carries one field and no person, so it cannot be drawn — and its leaving is
   * what makes a seat on the court behind it go blank.
   */
  it('drops a row the live gates no longer admit', async () => {
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () =>
      json({
        search: envelope(SEARCH_ID),
        candidates: [card(B), { withheld: true }, card(D)],
      } as Wire['ShortlistResponse']),
    );

    await openThePool();

    await waitFor(() => expect(screen.queryByLabelText(addLabel(C))).toBeNull());
    expect(screen.getByLabelText(addLabel(B))).toBeTruthy();
  });

  /** The re-read writes the **whole** record back, origin and all, or the court loses its sport. */
  it('keeps the origin, so the court it came from still knows what it is for', async () => {
    await openThePool();
    await waitFor(() =>
      expect(transport.requestsTo('GET', `${SEARCHES}/${SEARCH_ID}`)).toHaveLength(1),
    );

    fireEvent.press(screen.getByLabelText(addLabel(B)));
    // The eyebrow is written from the origin's sport and mode, neither of which crosses on a
    // read-back: a record rebuilt from the response alone would have lost both.
    expect(screen.getByText('Padel · doubles · for fun')).toBeTruthy();
  });
});

/**
 * A forecast for a court with somebody **across the net** — B beside you, C opposite, one seat
 * still open. The split is the engine's own working and nothing here derives it.
 */
const crossedForecast = (full = false): Wire['ForecastResponse'] => ({
  arrangements: [
    {
      pairing_id: 1,
      is_current: true,
      is_evenest: true,
      sides: {
        A: [
          { seat_index: 0, relationship: 'SELF', player_id: ME },
          { seat_index: 1, relationship: 'PARTNER', player_id: B },
        ],
        B: [
          { seat_index: 2, relationship: 'OPPONENT', player_id: C },
          ...(full ? [{ seat_index: 3, relationship: 'OPPONENT' as const, player_id: D }] : []),
          ...(full ? [] : [{ seat_index: 3, relationship: 'OPPONENT' as const }]),
        ],
      },
      forecast: {
        pct: 84,
        sigma_group: 0.4,
        provisional: !full,
        assumption: full ? null : 'EMPTY_SEAT_MATCHES_ITS_PARTNER',
      },
      split: { your_side: 2.73, their_side: 2.67, gap: 0.06 },
    },
  ],
  engine_version: 'matchfit-v1',
  ruleset_version: 'ruleset-v1',
});

describe('the header', () => {
  /**
   * **The screen is named for what it is here to do, over the facts it was searched under.**
   *
   * The pair was tried the other way round for a day — the facts promoted to the title and
   * *Pick players* dropped — and it put this screen and the court it is pushed over under one
   * heading, which named the search on both and the screen on neither. A title's first job is
   * telling you which of two you are on.
   */
  it('is named for what it is here to do, with the search facts above it', async () => {
    await openThePool();

    expect(screen.getByRole('header', { name: POOL_TITLE })).toBeTruthy();
    // The court underneath is called something else, which is the whole of the reversal.
    expect(screen.queryByRole('header', { name: 'Build a doubles' })).toBeNull();
    // Drawn here too — and more than once on the stack, because the court underneath is still
    // mounted and carries the same eyebrow. That the two share this line is the point; what
    // they must not share is the heading, which the assertion above is about.
    expect(
      screen.getAllByText(searchFacts({ sportName: 'Padel', seats: 4, mode: 'FOR_FUN' }), {
        includeHiddenElements: true,
      }).length,
    ).toBeGreaterThan(0);
  });

  /**
   * **The Sport is under the picture, not on it.**
   *
   * [7.12](../../../../docs/design-system.md#712-the-court)'s caption is a band *inside* the
   * drawing, absolutely positioned along the bottom edge over its own gradient — which at the
   * header's width lands across the near baseline of a court that has four faces on it. Out
   * here it is the same eyebrow, centred on the same width, and the picture is left to be a
   * picture. Asserted on the drawn style, because *under* and *inside* are the same string in
   * both places and only the box tells them apart.
   */
  it('draws the sport under the court rather than inside it', async () => {
    await openThePool();

    // Hidden, and it always was: the element around the picture announces `poolHeaderLabel`,
    // which opens with the Sport — so the word is drawn for a reader and merged for a listener
    // (§20.1). Moving it out of the drawing did not change which of the two it is.
    const shown = { includeHiddenElements: true };
    await screen.findByLabelText(POOL_COURT_LABEL);
    // The screens under this one are still mounted and name the Sport too, so the header's own
    // word is picked out by the register it is in: an uppercased eyebrow, which is the caption's
    // and nothing else's on this stack.
    const eyebrows = screen
      .getAllByText(sportLabel('padel'), shown)
      .map((node) => StyleSheet.flatten(node.props.style as TextStyle))
      .filter((style) => style?.textTransform === 'uppercase');

    expect(eyebrows).toHaveLength(1);
    expect(eyebrows[0]?.position).toBeUndefined();
    expect(eyebrows[0]?.textAlign).toBe('center');
  });

  /**
   * The court is underneath and this screen **pops** back onto it — the same `back` the row's
   * own *back to the court* control performs, drawn once at the top of the screen so the way
   * out of the second level of Play is not a gesture a player has to know about.
   */
  it('draws a way back to the court it is filling', async () => {
    await openThePool();

    fireEvent.press(screen.getByLabelText('Back'));

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  });

  it('draws the court it is filling, and gains a seat on every add', async () => {
    await openThePool();

    // You, and nobody else — the honest picture before anything has been added. The count is
    // what is asserted rather than the name: `You` is also a tab and a head-to-head row.
    expect(await screen.findByText(poolSeatedLine({ filled: 1, seats: 4 }))).toBeTruthy();

    fireEvent.press(screen.getByLabelText(addLabel(B)));

    expect(await screen.findByText(poolSeatedLine({ filled: 2, seats: 4 }))).toBeTruthy();
    // The handles are drawn in the band and spoken here; the card prints no names line.
    expect(
      screen.getByLabelText(
        poolHeaderLabel({
          sportName: 'Padel',
          filled: 2,
          seats: 4,
          names: ['You', NAMES[B] ?? ''],
        }),
      ),
    ).toBeTruthy();
  });

  /**
   * The engine answers from the first add, and gets there by assuming the empty seat matches
   * the player opposite — so over a one-sided court the figure is the assumption talking.
   *
   * **Nothing stands in its place.** A sentence naming the act that would make it a reading
   * was drawn here until 2026-09-09; the list underneath is already offering that act on every
   * row, so what the card does now is not draw the block at all.
   */
  it('withholds the reading while everybody added is beside you', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    // The count is the header's proof of life: the card is on screen and the seat did land.
    expect(await screen.findByText(poolSeatedLine({ filled: 2, seats: 4 }))).toBeTruthy();
    expect(screen.queryByText(formatPercent(67))).toBeNull();
    expect(screen.queryByText(balanceWord(67))).toBeNull();
    expect(screen.queryByLabelText(splitRowLabel(SIDES, SPLIT))).toBeNull();
  });

  /**
   * And from the first player across the net it is a reading of a real game — drawn with the
   * engine's own caveat, because a seat is still open and ADR-0108 makes the figure and its
   * caveat one thing.
   */
  it('reads the game from the first player across the net, as a figure and a pair', async () => {
    transport.on('POST', FORECASTS, () => json(crossedForecast()));

    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));
    fireEvent.press(await screen.findByLabelText(addLabel(C)));

    expect(await screen.findByText(formatPercent(84))).toBeTruthy();

    // The figure stands alone: no balance word under it and no caveat sentence beneath the
    // bar. Both readings survive in the spoken name, which is where the tint never was.
    expect(screen.queryByText(balanceWord(84))).toBeNull();
    expect(screen.queryByText(forecastAssumption('EMPTY_SEAT_MATCHES_ITS_PARTNER'))).toBeNull();
    expect(screen.queryByText(PROVISIONAL_WORD)).toBeNull();

    // Every figure in the split row is the engine's; §11.3's check is looking for arithmetic.
    expect(screen.getByLabelText(splitRowLabel(SIDES, SPLIT))).toBeTruthy();
  });

  /**
   * Every seat filled, and every handle printed **whole** on the way.
   *
   * This is the pool's half of `the-play-components.md` §5: the 46pt seat label may cut a
   * 64-character handle to four characters *because* this line prints it in full, so a header
   * that truncated would take the licence away from the court behind it.
   */
  it('names everybody as the court fills, and cuts nobody short', async () => {
    transport.on('POST', FORECASTS, () => json(crossedForecast(true)));

    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));
    fireEvent.press(await screen.findByLabelText(addLabel(C)));
    fireEvent.press(await screen.findByLabelText(addLabel(D)));

    expect(await screen.findByText(poolSeatedLine({ filled: 4, seats: 4 }))).toBeTruthy();
    console.log(
      'LABEL>>>',
      screen
        .UNSAFE_getAllByProps({ accessible: true })
        .map((n) => n.props.accessibilityLabel)
        .filter((l) => typeof l === 'string' && l.includes('of 4')),
    );
  });

  /**
   * The bar is drawn and **hidden**, because the split row above it prints all three of its
   * numbers — so it is found by its segment labels rather than by an accessible name.
   */
  it('draws the balance bar, labelled by side, and keeps it out of the tree', async () => {
    transport.on('POST', FORECASTS, () => json(crossedForecast()));

    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));
    fireEvent.press(await screen.findByLabelText(addLabel(C)));

    await screen.findByText(formatPercent(84));

    // In the tree and **never** to a listener. The fixtures' handles carry no word break, so
    // the drawn form and the whole one are the same string here.
    expect(
      screen.getAllByText(SIDES.yours, { includeHiddenElements: true }).length,
    ).toBeGreaterThan(0);
    expect(screen.queryByLabelText(balanceLabel(84))).toBeNull();
  });

  /**
   * A withheld row carries one field and no card, so there is no handle to print — and the
   * header answers the unknown's own character rather than inventing one. The re-read is what
   * produces it: the record is immutable and the gates are live.
   */
  it('says the unknown for a seated player the re-read no longer describes', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));
    await screen.findByText(poolSeatedLine({ filled: 2, seats: 4 }));

    // The gates drop B between the mint and the read-back, so the seat stays and the name goes.
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () =>
      json({
        search: envelope(SEARCH_ID),
        candidates: [{ withheld: true }, card(C), card(D)],
      } as Wire['ShortlistResponse']),
    );
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    fireEvent.press(await screen.findByLabelText(PICK_PLAYERS_LABEL));

    expect(
      await screen.findByLabelText(
        poolHeaderLabel({ sportName: 'Padel', filled: 2, seats: 4, names: ['You', '?'] }),
      ),
    ).toBeTruthy();
  });

  /**
   * A singles court arrives on the same card, counted for two seats rather than four — and
   * with the same silence under it, because nobody is across the net there either.
   */
  it('counts a singles court for two, and reads nothing over one empty seat', async () => {
    await openTheSinglesPool();

    expect(await screen.findByText(poolSeatedLine({ filled: 1, seats: 2 }))).toBeTruthy();
    expect(screen.queryByLabelText(splitRowLabel(SIDES, SPLIT))).toBeNull();
  });

  /**
   * The pool was pushed over the court and `ShellScreen` draws no chevron of its own, so this
   * is the way back rather than a convenience beside one.
   *
   * **The pathname is what is asserted, never the title going away.** A `push` onto the builder
   * also takes the pool's title off screen, so a test written that way passes over a control
   * that grows the stack every time it is pressed.
   */
  it('pops back to the court it is a picture of', async () => {
    await openThePool();
    fireEvent.press(await screen.findByText(POOL_COURT_LABEL));

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    // And it is a pop: going back again leaves Play rather than landing on the pool.
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play'));
  });
});

/** The two halves as the split row names them, and the figures it prints. */
const SIDES = { yours: `You + ${NAMES[B] ?? ''}`, theirs: NAMES[C] ?? '' };
const SPLIT = { yourSide: 2.73, theirSide: 2.67, gap: 0.06 };

describe('the sort row', () => {
  it('draws the server’s own list and nothing it did not offer', async () => {
    await openThePool();

    expect(await screen.findByLabelText(sortLabel('BEST_FIT'))).toBeTruthy();
    expect(screen.getByLabelText(sortLabel('CLOSEST'))).toBeTruthy();
    expect(screen.queryByLabelText(sortLabel('EVENEST'))).toBeNull();
    expect(screen.queryByLabelText(sortLabel('MOST_RELIABLE'))).toBeNull();
  });

  it('is not drawn at all when the server offers nothing', async () => {
    transport.on('POST', SEARCHES, () => json(shortlist({ sorts_available: [] })));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(shortlist({ sorts_available: [] })));

    await openThePool();

    await waitFor(() => expect(screen.queryByLabelText(sortLabel('CLOSEST'))).toBeNull());
    expect(screen.queryByLabelText(sortLabel('BEST_FIT'))).toBeNull();
  });

  /**
   * *Best fit* is withheld precisely when the returned order already is best-fit order, so a
   * row drawn from `sorts_available` alone would make *Closest* a one-way door.
   */
  it('gains the way back once the player has left the order they arrived in', async () => {
    const offered = { sorts_available: ['CLOSEST'] as Wire['SortOption'][] };
    transport.on('POST', SEARCHES, () => json(shortlist(offered)));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(shortlist(offered)));

    await openThePool();

    expect(await screen.findByLabelText(sortLabel('CLOSEST'))).toBeTruthy();
    expect(screen.queryByLabelText(sortLabel('BEST_FIT'))).toBeNull();

    fireEvent.press(screen.getByLabelText(sortLabel('CLOSEST')));

    expect(await screen.findByLabelText(sortLabel('BEST_FIT'))).toBeTruthy();
  });

  /**
   * §C5 specified the comparator as *"the fit score plus 12 for anyone who said yes to you"*.
   * The engine already lifted them, as an **admission** rather than a bonus — so the fixture
   * puts a lifted row eight points behind, where a client-side `+12` would move it first.
   */
  it('sorts Best fit on the printed number, adding no lift of its own', async () => {
    const rows: Wire['ShortlistResponse'] = {
      search: envelope(SEARCH_ID),
      candidates: [
        card(C, { fit: 71, inclusion_reason: 'INTEREST_LIFT' }),
        card(B, { fit: 79 }),
        card(D, { fit: 74 }),
      ],
    };
    transport.on('POST', SEARCHES, () => json(rows));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(rows));

    await openThePool();
    fireEvent.press(await screen.findByLabelText(sortLabel('BEST_FIT')));

    const order = screen
      .getAllByLabelText(/^Add .* to the court$/)
      .map((control) => control.props.accessibilityLabel as string);

    expect(order).toEqual([addLabel(B), addLabel(D), addLabel(C)]);
  });
});

/** A competitive pool on the four-seat Sport `openThePool()` walks. */
function servedCompetitive(candidates: readonly Wire['CandidateSchema'][]) {
  const rows: Wire['ShortlistResponse'] = {
    search: envelope(SEARCH_ID, { mode: 'COMPETITIVE' }),
    candidates: [...candidates],
  };
  transport.on('POST', SEARCHES, () => json(rows));
  transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(rows));
}

/**
 * **What's at stake, on the two courts** — the plumbing half of
 * [#312](https://github.com/Raketa02/Raketa/issues/312).
 *
 * The rule itself is `domain/atStake`'s and is unit-tested there. What only a walk can show is
 * that the seat count the card is handed is the **search's own Sport** counted, rather than a
 * constant or the wrong screen's: the same served row draws the boxes on tennis and does not
 * on padel, and nothing about the row changed between the two.
 */
describe('what is at stake, on the two courts', () => {
  const AT_STAKE = { win_delta: 0.08, loss_delta: -0.05 };

  it('draws the pair on a singles court, as served', async () => {
    await openTheSinglesPool({ mode: 'COMPETITIVE' }, [card(B, { at_stake: AT_STAKE })]);
    await screen.findByLabelText(addLabel(B));

    expect(screen.getByText('Win, counted')).toBeTruthy();
    expect(screen.getByText('+0,08')).toBeTruthy();
    expect(screen.getByText('Lose, counted')).toBeTruthy();
    expect(screen.getByText('\u22120,05')).toBeTruthy();
  });

  it('hides it on a doubles court, where three seats are still unknown', async () => {
    servedCompetitive([card(B, { at_stake: AT_STAKE })]);

    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(screen.queryByText('Win, counted')).toBeNull();
    expect(screen.queryByText('Lose, counted')).toBeNull();
  });

  it('is not on a for-fun pool at all, which draws the other card', async () => {
    // The field never crosses in for fun — *a counted result is meaningless rather than
    // unavailable* — and the surface a for-fun pool draws has no box for it either. Served
    // anyway here, so the absence on screen is the pool's own rather than the fixture's.
    const rows: Wire['ShortlistResponse'] = {
      search: envelope(SEARCH_ID),
      candidates: [card(B, { at_stake: AT_STAKE })],
    };
    transport.on('POST', SEARCHES, () => json(rows));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(rows));

    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(screen.queryByText('Win, counted')).toBeNull();
  });
});

/**
 * **The record block, walked from the wire** — three fields the pool had never carried before
 * [#312](https://github.com/Raketa02/Raketa/issues/312).
 *
 * The drawing and the two spellings of absence are asserted on the card; what only a walk shows
 * is that the fields survive the mapper and reach the block with nothing lost on the way.
 */
describe('the record block on a pool row', () => {
  it('draws what the platform watched, straight off the served card', async () => {
    servedCompetitive([
      card(B, {
        player_card: {
          ...card(B).player_card,
          player_score: 74,
          counted_games: 29,
          last_five: ['WIN', 'LOSS', 'WIN'],
        },
      }),
    ]);

    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(screen.getByText('Player Score')).toBeTruthy();
    expect(screen.getByText('74')).toBeTruthy();
    expect(screen.getByText('Counted')).toBeTruthy();
    expect(screen.getByText('29')).toBeTruthy();
    // Three counted results, so *Last 5* draws three squares and a gap — the run's length is
    // the statement, and it is `candidateCards.test.tsx` that counts them.
    expect(screen.getByText('Last 5')).toBeTruthy();
  });

  it('draws none of the three for a row the platform has watched do nothing', async () => {
    servedCompetitive([card(B)]);

    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(screen.queryByText('Player Score')).toBeNull();
    expect(screen.queryByText('Last 5')).toBeNull();
    expect(screen.queryByText('Counted')).toBeNull();
  });
});

/**
 * **The pin and the tag** — [#310](https://github.com/Raketa02/Raketa/issues/310)'s three rules,
 * walked on a competitive pool because that is the card the two tags are drawn on.
 *
 * The fixture is the one that separates a pin from the `+12` above it: the lifted row is
 * **eight points behind** the top of the list, so the served order draws it first with a 71
 * printed beside it, and every chip drops it back to where 71 belongs.
 */
describe('the pin and the best match', () => {
  /** C already said yes and scores least; B has the highest number and D sits between them. */
  function servedWithALift(over: Partial<Wire['SearchEnvelope']> = {}) {
    const rows: Wire['ShortlistResponse'] = {
      search: envelope(SEARCH_ID, { mode: 'COMPETITIVE', ...over }),
      candidates: [
        card(B, { fit: 79, distance_km: 9 }),
        card(D, { fit: 74, distance_km: 5 }),
        card(C, { fit: 71, distance_km: 2, inclusion_reason: 'INTEREST_LIFT' }),
      ],
    };
    transport.on('POST', SEARCHES, () => json(rows));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(rows));
  }

  const drawnOrder = () =>
    screen
      .getAllByLabelText(/^Add .* to the court$/)
      .map((control) => control.props.accessibilityLabel as string);

  it('lifts somebody who already said yes above two higher numbers, and prints their own', async () => {
    servedWithALift();
    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(drawnOrder()).toEqual([addLabel(C), addLabel(B), addLabel(D)]);
    // The whole of *a pin is not a bonus*: the row moved and the figure did not — 71 is what
    // the wire served and 71 is what the pill prints, on the row now sitting first.
    expect(screen.getByText('71')).toBeTruthy();
    expect(screen.getByText('Wants to play you')).toBeTruthy();
  });

  it('drops them into their honest place on a re-sort, with the tag still on them', async () => {
    servedWithALift();
    await openThePool();
    fireEvent.press(await screen.findByLabelText(sortLabel('CLOSEST')));

    expect(drawnOrder()).toEqual([addLabel(C), addLabel(D), addLabel(B)]);

    fireEvent.press(screen.getByLabelText(sortLabel('BEST_FIT')));

    expect(drawnOrder()).toEqual([addLabel(B), addLabel(D), addLabel(C)]);
    // The tag travels with the card wherever it lands — it is a fact about the person.
    expect(screen.getByText('Wants to play you')).toBeTruthy();
  });

  it('puts one coral tag on the highest number in the order the rows arrived in', async () => {
    servedWithALift();
    await openThePool();
    await screen.findByLabelText(addLabel(B));

    // Exactly one, and on B — who is second on screen, because the pin moved a lower row above
    // them and the tag is about the number rather than about the position.
    expect(screen.getAllByText('Best match')).toHaveLength(1);
  });

  it('hides it under the orderings that are not about the number', async () => {
    servedWithALift();
    await openThePool();
    fireEvent.press(await screen.findByLabelText(sortLabel('CLOSEST')));

    expect(screen.queryByText('Best match')).toBeNull();

    fireEvent.press(screen.getByLabelText(sortLabel('BEST_FIT')));

    expect(screen.getAllByText('Best match')).toHaveLength(1);
  });

  /**
   * The wrinkle: `BEST_FIT` is withheld exactly when the returned order already **is** fit
   * order, so a tag keyed to a tapped chip would never show on most searches. Here the server
   * offers nothing at all and the tag is still drawn.
   */
  it('is drawn on a search whose sort row could never offer best fit', async () => {
    servedWithALift({ sorts_available: [] });
    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(screen.queryByLabelText(sortLabel('BEST_FIT'))).toBeNull();
    expect(screen.getAllByText('Best match')).toHaveLength(1);
  });

  it('gives a row that would carry both tags only the green one', async () => {
    const rows: Wire['ShortlistResponse'] = {
      search: envelope(SEARCH_ID, { mode: 'COMPETITIVE' }),
      candidates: [
        card(B, { fit: 88, inclusion_reason: 'INTEREST_LIFT' }),
        card(D, { fit: 74 }),
        card(C, { fit: 71 }),
      ],
    };
    transport.on('POST', SEARCHES, () => json(rows));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(rows));

    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(screen.getByText('Wants to play you')).toBeTruthy();
    // Not moved to the runner-up: the coral tag names the best match or nobody.
    expect(screen.queryByText('Best match')).toBeNull();
  });
});

describe('the ladder', () => {
  const thin = { rung_offers: [TIMES_RUNG, RADIUS_RUNG] };

  function offerRungs(over: Partial<Wire['SearchEnvelope']> = thin) {
    transport.on('POST', SEARCHES, () => json(shortlist(over)));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(shortlist(over)));
  }

  it('prices each rung with the total above the floor, and never a delta', async () => {
    offerRungs();
    await openThePool();

    expect(await screen.findByText(poolLadderTitle({ rows: 3, radiusKmUsed: 15 }))).toBeTruthy();
    // ADR-0099 §5: the count is printed **on** the button, so it is in the control's own name
    // as well as under it — the line beneath has no action and merges into it (§20.1).
    expect(screen.getByLabelText(rungLabel({ ask: 'TIMES' }, 7))).toBeTruthy();
    expect(screen.getByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 22 }, 9))).toBeTruthy();
    // Visible, and hidden from a listener — the control above it already says the price.
    expect(
      screen.getByText(rungCount({ candidatesAboveFloor: 9, window: 'THIS_WEEK' }, 'THIS_WEEK'), {
        includeHiddenElements: true,
      }),
    ).toBeTruthy();
    expect(
      screen.queryByText(rungCount({ candidatesAboveFloor: 9, window: 'THIS_WEEK' }, 'THIS_WEEK')),
    ).toBeNull();
  });

  it('is drawn on no other Play screen', async () => {
    offerRungs();
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    await screen.findByLabelText('Tuesday evening');

    // Find a game holds the same envelope and offers nothing off it.
    expect(screen.queryByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 22 }, 9))).toBeNull();
  });

  /**
   * The bit says *a widening offer hit the slider's ceiling*, **not** *the searcher is at the
   * ceiling*: `radius_ladder` clamps such a rung down to 50 km and offers it anyway, so a
   * searcher at 26 km is offered 39 and 50 with the bit set. Reading it as a gate would take a
   * real one-tap widening away from exactly the player the ladder was built for.
   */
  it('keeps a clamped answer’s radius rung, because the offer is still real', async () => {
    offerRungs({ rung_offers: [{ ...RADIUS_RUNG, radius_km: 50 }], radius_clamp: true });
    await openThePool();

    expect(
      await screen.findByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 50 }, 9)),
    ).toBeTruthy();
  });

  /**
   * The searcher already at the maximum, which is the case the bit exists to count. Nothing is
   * left to offer, so the copy states the reach rather than asking for a widening they cannot
   * give — and suppressing the sentence would leave them with no account of why.
   */
  it('states the reach as a fact when the ceiling left no rung at all', async () => {
    offerRungs({ rung_offers: [], radius_clamp: true });
    await openThePool();

    expect(
      await screen.findByText(
        terminalReachLine({
          radiusKmUsed: 15,
          playersInRange: 6,
          radiusClamp: true,
          tookRadiusFrom: undefined,
        }),
      ),
    ).toBeTruthy();
  });

  /** A control that provably returns an empty list is a control lying about being useful. */
  it('states a rung priced at nobody rather than offering it', async () => {
    offerRungs({ rung_offers: [{ ...RADIUS_RUNG, candidates_above_floor: 0, radius_km: 32 }] });
    await openThePool();

    expect(await screen.findByText(zeroRungLine({ ask: 'RADIUS', radiusKm: 32 }))).toBeTruthy();
    expect(screen.queryByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 32 }, 0))).toBeNull();
  });

  /** `null` is *nobody needed offers*. The list is the answer, and no block is drawn. */
  it('draws nothing at all on a list long enough that nobody priced a rung', async () => {
    await openThePool();

    await waitFor(() => expect(screen.getByLabelText(addLabel(B))).toBeTruthy());
    expect(screen.queryByText(poolLadderTitle({ rows: 3, radiusKmUsed: 15 }))).toBeNull();
  });

  it('cites the offer, sends no widening, and replaces the list with a standing statement', async () => {
    offerRungs();
    transport.on('POST', SEARCHES, (request) =>
      json(
        (request.body as { readonly offered_by_search_id?: string }).offered_by_search_id ===
          undefined
          ? shortlist(thin)
          : {
              search: envelope(WIDER_ID, {
                pool: {
                  sport: 'PADEL',
                  radius_km_used: 22,
                  players_in_range: 11,
                  window: 'THIS_WEEK',
                  post_gate: true,
                },
                rung_offers: [],
              }),
              candidates: [card(B)],
            },
      ),
    );

    await openThePool();
    fireEvent.press(await screen.findByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 22 }, 9)));

    await screen.findByText(
      poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline,
    );
    act(() => jest.advanceTimersByTime(2000));

    await waitFor(() =>
      expect(
        screen.getByText(takenRungLine({ ask: 'RADIUS', radiusKm: 22, profileRadiusKm: 15 })),
      ).toBeTruthy(),
    );

    const [, widened] = transport.requestsTo('POST', SEARCHES);
    expect(widened?.body).toEqual({
      sport: 'PADEL',
      mode: 'FOR_FUN',
      offered_by_search_id: SEARCH_ID,
      rung: 'B',
    });
    // The widening itself is not sent: the backend reads it off the offer it made.
    expect(widened?.body).not.toHaveProperty('radius_km');
  });
});

/**
 * §8 of [#223](https://github.com/Raketa02/Raketa/issues/223): the cell a times rung adds
 * **visibly ticks**, marked as this-search-only — otherwise the grid the player just filled in
 * disagrees with the search that ran, with nothing on either screen to say so.
 *
 * It is drawn on *Find a game*, two pushes back, because that is where the grid is
 * ([#283](https://github.com/Raketa02/Raketa/issues/283)); the pool has no grid, and a tick
 * drawn where nobody is looking is not the requirement.
 */
describe('the cell a times rung adds', () => {
  const THURSDAY_EVENING = { day: 4, part: 'evening' } as const;

  async function takeTheTimesRung() {
    transport.on('POST', SEARCHES, (request) =>
      json(
        (request.body as { readonly offered_by_search_id?: string }).offered_by_search_id ===
          undefined
          ? shortlist({ rung_offers: [TIMES_RUNG, RADIUS_RUNG] })
          : { search: envelope(WIDER_ID, { rung_offers: [] }), candidates: [card(B)] },
      ),
    );
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () =>
      json(shortlist({ rung_offers: [TIMES_RUNG, RADIUS_RUNG] })),
    );

    await openThePool();
    fireEvent.press(await screen.findByLabelText(rungLabel({ ask: 'TIMES' }, 7)));
    await screen.findByText(
      poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline,
    );
    act(() => jest.advanceTimersByTime(2000));
    await waitFor(() =>
      expect(screen.getByText(takenRungLine({ ask: 'TIMES', profileRadiusKm: 15 }))).toBeTruthy(),
    );
  }

  /** Back out of the pool, off the court, and onto the screen the week is edited on. */
  async function backToFindAGame() {
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play'));
  }

  it('is marked on the grid the week is edited on, and announced as this search’s', async () => {
    await takeTheTimesRung();
    await backToFindAGame();

    expect(await screen.findByLabelText(searchWeekCellLabel(THURSDAY_EVENING, true))).toBeTruthy();
    expect(screen.getByText(WEEK_ADDED_FOR_THIS_SEARCH)).toBeTruthy();
  });

  /**
   * **A climb that adds no cell takes the mark with it.** The court still holds the strict
   * record, so leaving this pool and opening it again against another seat offers the ladder a
   * second time — and a radius rung taken there runs on the week *without* the added cell. A
   * mark left standing would be the grid disagreeing with the search that ran, which is the
   * disagreement §8 exists to close, pointed the other way.
   */
  it('is dropped by a later radius rung, which ran on the week without it', async () => {
    await takeTheTimesRung();

    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    fireEvent.press(await screen.findByLabelText(PICK_PLAYERS_LABEL));
    await waitFor(() => expect(screen).toHavePathname('/play/pool'));

    fireEvent.press(await screen.findByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 22 }, 9)));
    await screen.findByText(
      poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline,
    );
    act(() => jest.advanceTimersByTime(2000));
    await waitFor(() =>
      expect(
        screen.getByText(takenRungLine({ ask: 'RADIUS', radiusKm: 22, profileRadiusKm: 15 })),
      ).toBeTruthy(),
    );

    await backToFindAGame();

    expect(await screen.findByLabelText(searchWeekCellLabel(THURSDAY_EVENING, false))).toBeTruthy();
    expect(screen.queryByText(WEEK_ADDED_FOR_THIS_SEARCH)).toBeNull();
  });

  /**
   * Pressing it is an ordinary tick, and the two facts cannot both stand on one square: from
   * that press the cell is the player's own ask, travelling on every search from here.
   */
  it('becomes the player’s own week the moment they tick it themselves', async () => {
    await takeTheTimesRung();
    await backToFindAGame();

    fireEvent.press(await screen.findByLabelText(searchWeekCellLabel(THURSDAY_EVENING, true)));

    const ticked = await screen.findByLabelText(searchWeekCellLabel(THURSDAY_EVENING, false));
    expect(ticked.props.accessibilityState).toEqual(expect.objectContaining({ checked: true }));
    expect(screen.queryByText(WEEK_ADDED_FOR_THIS_SEARCH)).toBeNull();
  });

  /**
   * The whole reason it is not written into the working copy. `week` is what travels as
   * `availability_override`, so a cell put there would carry a this-search-only widening into
   * every later ask — ADR-0099's conflation, arriving from the client.
   */
  it('does not join the week, so the next search asks for the profile’s grid', async () => {
    await takeTheTimesRung();
    await backToFindAGame();

    fireEvent.press(screen.getByLabelText(courtEntryLabel(courtSeatCount('padel'))));

    await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(3));
    const [, , next] = transport.requestsTo('POST', SEARCHES);
    expect(next?.body).not.toHaveProperty('availability_override');
    // And the mark goes with the list it was about: this search cites no offer.
    expect(usePlaySession.getState().addedForThisSearch).toBeUndefined();
  });
});

describe('adding somebody', () => {
  it('builds the line-up on this screen and writes nothing outbound', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    expect(usePlaySession.getState().lineup).toEqual({
      originSearchId: SEARCH_ID,
      seats: [B],
    });
    expect(transport.requestsTo('POST', '/api/v1/interest')).toHaveLength(0);
  });

  /**
   * A row for somebody already on the court carries an *Add* that could do nothing, which is
   * the same objection that keeps a sort nobody can act on off this screen.
   */
  it('takes a seated player off the list rather than offering them again', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    await waitFor(() => expect(screen.queryByLabelText(addLabel(B))).toBeNull());
    expect(screen.getByLabelText(addLabel(C))).toBeTruthy();
  });

  /**
   * **A court with no seat left still draws every row, and the control on each says no.**
   *
   * Read on a singles court, which is the one shape a pool can fill without emptying its own
   * list: two seats, so one add is a full court, and the row for everybody else is still on
   * screen to be checked. The rows are worth reading whether or not there is a seat — the
   * ladder is still there, the way back is the header's — so the answer is a **dead control**
   * rather than a vanished one: a list that silently changed shape says nothing about why.
   */
  it('draws the add dead once the court has no seat left, rather than taking it away', async () => {
    await openTheSinglesPool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    await waitFor(() => expect(screen.queryByLabelText(addLabel(B))).toBeNull());
    const add = screen.getByLabelText(addLabel(C));

    // Both registers: dimmed for a reader, `disabled` for a listener — never colour alone.
    expect(add.props.accessibilityState?.disabled).toBe(true);

    fireEvent.press(add);
    expect(usePlaySession.getState().lineup).toEqual({ originSearchId: SEARCH_ID, seats: [B] });
  });

  /**
   * G7's *"leaving the pool halfway through replacing somebody should be forgotten"* is
   * satisfied by the pop: the route unmounts and takes the pending seat with it, so leaving
   * without adding anybody has changed nothing at all.
   */
  it('leaves the court untouched when the pool is left without an addition', async () => {
    await openThePool();
    await screen.findByLabelText(addLabel(B));

    expect(usePlaySession.getState().lineup).toBeUndefined();
  });
});

describe('the two cards', () => {
  /**
   * The pool draws **one shape twice** — competitive and social are the same card at the same
   * radius with different contents, and neither floats: #219 B3's argument is about a card
   * that translates and rotates out under a thumb, which reaches the deck alone
   * (`candidateCards.test.tsx` holds the shadow itself).
   */
  it('draws the social card for a game for fun', async () => {
    await openThePool();

    // The level row states all three facts, and the social card is the one that draws it —
    // the competitive card puts both levels side by side instead.
    const rows = await screen.findAllByText(
      levelRow({ level: 2.8, band: 'Established', range: { low: 2.55, high: 2.87 } }),
    );

    expect(rows).toHaveLength(3);
  });

  it('draws the competitive card, with both levels, on a competitive search', async () => {
    const competitive: Wire['ShortlistResponse'] = {
      search: envelope(SEARCH_ID, { mode: 'COMPETITIVE' }),
      candidates: [
        card(B, {
          terms: [
            {
              term: 'LEVEL_FIT',
              weight: 26,
              value: 0.8,
              contribution: 21,
              evidence: {
                kind: 'level_fit',
                my_mu: 2.71,
                their_mu: 2.8,
                delta: 0.09,
                direction: 'ABOVE',
              },
            },
          ],
        }),
      ],
    };
    transport.on('POST', SEARCHES, () => json(competitive));
    transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(competitive));

    await openThePool();

    // The head-to-head band, which is the one place the searcher's **own** level is drawn.
    expect(await screen.findByText(formatLevel(2.71))).toBeTruthy();
    // Theirs, twice: the photo panel prints what they published and the band prints the side
    // of the comparison the advantage was computed from (#309).
    expect(screen.getAllByText(formatLevel(2.8))).toHaveLength(2);

    // The panel's third fact is the search's own Sport, which the screen holds and the wire
    // never sends on a candidate.
    expect(screen.getByText(sportLabel('padel'))).toBeTruthy();
  });
});

describe('replacing somebody', () => {
  /**
   * The pool is opened **against a seat**, and where that seat is occupied the add is a
   * replacement — said before it happens, because the court is one screen away and a silent
   * swap of one handle for another is a destruction found out about afterwards.
   *
   * **Driven through the route rather than off the court** (2026-09-09). A tap on an occupied
   * seat opened this; it trades two seats now, and the court's own way to change who is on it
   * is the clear badge and then the hole it leaves — the walk the test below this one takes.
   * The seat is a route parameter, so the state is still one the pool can be put in, and this
   * is what it says when it is: a screen that stopped saying *replacing* while still replacing
   * somebody is the silent destruction the sentence exists to prevent.
   */
  it('names whom an add would replace, and swaps exactly them', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));

    act(() =>
      router.push({ pathname: '/play/pool', params: { search: SEARCH_ID, seat: String(1) } }),
    );
    await waitFor(() => expect(screen).toHavePathname('/play/pool'));

    expect(await screen.findByText(replacingLine(NAMES[B] ?? ''))).toBeTruthy();

    fireEvent.press(screen.getByLabelText(addLabel(C)));

    expect(usePlaySession.getState().lineup).toEqual({
      originSearchId: SEARCH_ID,
      seats: [C],
    });
  });

  /**
   * **The court's own way to change who is on it**, now that a tap on a seat trades.
   *
   * Two acts where there was one, and both were already on the seat: the × takes somebody off
   * — drawn on exactly the seats a replacement was ever allowed against — and the hole it
   * leaves opens the pool, which is the row every empty seat has always had. Nothing says
   * *replacing*, because by then there is nobody in the seat to replace.
   */
  it('takes somebody off with the badge, and the hole they leave opens the pool', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));

    fireEvent.press(await screen.findByLabelText(`Remove ${NAMES[B]} from your side`));
    fireEvent.press(
      await screen.findByLabelText(seatLabel('YOUR_PARTNER', { kind: 'empty', unfilled: null })),
    );
    await waitFor(() => expect(screen).toHavePathname('/play/pool'));

    expect(screen.queryByText(replacingLine(NAMES[B] ?? ''))).toBeNull();

    fireEvent.press(screen.getByLabelText(addLabel(C)));

    expect(usePlaySession.getState().lineup).toEqual({
      originSearchId: SEARCH_ID,
      seats: [C],
    });
  });
});

/**
 * **The questions a climb raises**, on the fourth surface `SH.saveav` reaches
 * ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 *
 * `POST /searches` raises prompts wherever it is called and taking a rung calls it, so what is
 * asserted here is the beat — a climb replaces the list in place, so the sheet stands in front
 * of an answer already on screen — and the one question this screen cannot honour.
 */
describe('the question a climb raised', () => {
  const KEEP_THIS_RADIUS = promptCopy({ prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 }).title;
  const REFRESH_YOUR_TIMES = promptCopy({ prompt: 'REFRESH_YOUR_TIMES' }).title;
  const KEEP_THESE_TIMES = promptCopy({
    prompt: 'KEEP_THESE_TIMES',
    week: [],
    profileWeek: [],
  }).title;

  /** A pool with one radius rung on it, whose climb answers raising `prompts`. */
  function ladderRaising(prompts: readonly Wire['PromptSchema'][]) {
    transport.on('POST', SEARCHES, (request) =>
      json(
        (request.body as { readonly offered_by_search_id?: string }).offered_by_search_id ===
          undefined
          ? shortlist({ rung_offers: [RADIUS_RUNG] })
          : {
              search: envelope(WIDER_ID, {
                pool: {
                  sport: 'PADEL',
                  radius_km_used: 22,
                  players_in_range: 11,
                  window: 'THIS_WEEK',
                  post_gate: true,
                },
                // A search that took a rung is offered none, which is what unmounts the
                // control the sheet would otherwise hand focus back to.
                rung_offers: [],
                prompts: [...prompts],
              }),
              candidates: [card(B)],
            },
      ),
    );
  }

  /** Take the widening, and spend the pool's own floor so the latch lifts onto the new list. */
  async function climb() {
    fireEvent.press(await screen.findByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 22 }, 9)));
    await screen.findByText(
      poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline,
    );
    act(() => jest.advanceTimersByTime(2000));
  }

  it('waits for the latch, and is asked over the list the climb replaced', async () => {
    ladderRaising([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await openThePool();

    fireEvent.press(await screen.findByLabelText(rungLabel({ ask: 'RADIUS', radiusKm: 22 }, 9)));
    await screen.findByText(
      poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline,
    );
    await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(2));

    // The answer is in memory and the question is not on screen: the wait is what the sheet
    // is behind, and the widened list is what the wait lifts onto.
    expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull();

    act(() => jest.advanceTimersByTime(2000));

    expect(await screen.findByText(KEEP_THIS_RADIUS)).toBeTruthy();
    // Nothing was pushed: the list under the sheet is the one the climb wrote.
    expect(screen).toHavePathname('/play/pool');
  });

  /**
   * The hinge ADR-0099 leaves open, drawn where the evidence is. Taking the rung wrote no
   * radius; saying *yes* to the offer that follows it does, through the route that owns the
   * value — which is what makes the two acts different rather than merely sequential.
   */
  it('writes its yes through the route that owns the value, and takes no rung with it', async () => {
    ladderRaising([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await openThePool();
    await climb();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').accept));

    await waitFor(() => expect(transport.requestsTo('PUT', RADIUS)).toHaveLength(1));
    expect(transport.requestsTo('PUT', RADIUS)[0]?.body).toEqual({ search_radius_km: 22 });
    // Two searches: the one the pool opened on and the climb. Answering ran neither.
    expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(2);
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });

  it('is a decline when it is dismissed, written about the question and never the value', async () => {
    ladderRaising([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await openThePool();
    await climb();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').close));

    await waitFor(() => expect(transport.requestsTo('POST', DECLINES)).toHaveLength(1));
    expect(transport.requestsTo('POST', DECLINES)[0]?.body).toEqual({
      prompt: 'KEEP_THIS_RADIUS',
      sport: 'PADEL',
    });
    expect(transport.requestsTo('PUT', RADIUS)).toEqual([]);
  });

  /**
   * The profile's own week is the client's half of `KEEP_THESE_TIMES`, and this screen holds
   * it — so the diff is drawn against the week the profile actually has rather than against an
   * empty one this screen substituted for a read that had not landed.
   */
  it('draws the week the climb ran on against the one the profile holds', async () => {
    ladderRaising([
      {
        prompt: 'KEEP_THESE_TIMES',
        slots: [
          { day: 2, part: 'EVENING' },
          { day: 1, part: 'MORNING' },
        ],
      },
    ]);
    await openThePool();
    await climb();
    await screen.findByText(KEEP_THESE_TIMES);

    // The stub's profile week is Tuesday evening and Saturday morning.
    expect(screen.getByLabelText('Monday morning, newly added')).toBeTruthy();
    expect(screen.getByLabelText('Saturday morning, dropped')).toBeTruthy();
  });

  /**
   * Dropped rather than truncated to, which is why the fixture puts it first: *"there is no
   * grid on this screen"* is the same sentence that sends a rung's added cell two pushes back.
   */
  it('is never the one whose yes is a week grid this screen does not have', async () => {
    ladderRaising([
      { prompt: 'REFRESH_YOUR_TIMES' },
      { prompt: 'KEEP_THIS_RADIUS', radius_km: 22 },
    ]);
    await openThePool();
    await climb();

    expect(await screen.findByText(KEEP_THIS_RADIUS)).toBeTruthy();
    expect(screen.queryByText(REFRESH_YOUR_TIMES)).toBeNull();
  });

  it('leaves the widened list alone where the only question raised is that one', async () => {
    ladderRaising([{ prompt: 'REFRESH_YOUR_TIMES' }]);
    await openThePool();
    await climb();

    // No sheet at all — the standing statement the climb wrote is reachable, which it would
    // not be behind one.
    expect(
      await screen.findByText(takenRungLine({ ask: 'RADIUS', radiusKm: 22, profileRadiusKm: 15 })),
    ).toBeTruthy();
    expect(screen.queryByText(REFRESH_YOUR_TIMES)).toBeNull();
  });
});

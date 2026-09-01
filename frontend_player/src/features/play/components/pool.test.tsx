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
 * - **The header prints the balance word beneath the tinted number**, with the assumption as
 *   the sentence and no second badge.
 * - **The re-read happens here**, writes the whole record back, and is what makes a withheld
 *   row leave the list.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { router } from 'expo-router';

import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import { queryClient } from '@/shared/lib/query-client';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import {
  launchSignedIn,
  stubGate,
  stubInterest,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { usePlayPreferences } from '../store/playPreferences.store';
import { endPlaySession, usePlaySession } from '../store/playSession.store';

import { rungOfferLabel, seatLabel } from './accessibilityPresentation';
import { balanceWord } from './balancePresentation';
import { PICK_PLAYERS_LABEL, PROVISIONAL_WORD } from './builderPresentation';
import { levelRow } from './playerCardPresentation';
import {
  POOL_TITLE,
  poolLadderTitle,
  replacingLine,
  rungCount,
  takenRungLine,
  terminalReachLine,
  zeroRungLine,
} from './poolPresentation';
import { forecastAssumption, relaxationOffer, sortLabel } from './searchPresentation';
import { poolRankingStatus } from './searchingPresentation';

const SEARCHES = '/api/v1/searches';
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
  slot: '6:MORNING',
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
    },
  ],
  engine_version: 'matchfit-v1',
  ruleset_version: 'ruleset-v1',
});

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [rating('PADEL')], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubInterest(transport);
  transport.on('POST', SEARCHES, () => json(shortlist()));
  transport.on('GET', `${SEARCHES}/${SEARCH_ID}`, () => json(shortlist()));
  transport.on('POST', FORECASTS, () => json(forecastResponse()));
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

  fireEvent.press(screen.getByLabelText('Search'));
  await screen.findByText(
    poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline,
  );
  act(() => jest.advanceTimersByTime(2000));

  await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  fireEvent.press(await screen.findByLabelText(PICK_PLAYERS_LABEL));
  await waitFor(() => expect(screen).toHavePathname('/play/pool'));
  await screen.findByText(POOL_TITLE);
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

describe('the running forecast', () => {
  /**
   * §B13 drew the percentage tinted with *provisional* beneath it and no reading beside it,
   * which is Part 13's colour-only failure. The word under the number is the **balance** word;
   * `provisional` is the sentence, and it is the whole of the caveat.
   */
  it('prints the balance word beneath the number, with provisional as the sentence', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    expect(await screen.findByText(formatPercent(67))).toBeTruthy();
    expect(screen.getByText(balanceWord(67))).toBeTruthy();
    expect(screen.getByText(forecastAssumption('EMPTY_SEAT_MATCHES_ITS_PARTNER'))).toBeTruthy();
    // One word slot, and the balance reading is what it spends it on.
    expect(screen.queryByText(PROVISIONAL_WORD)).toBeNull();
  });
});

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

    // The head-to-head row, which is the one place the searcher's **own** level is drawn.
    expect(await screen.findByText(formatLevel(2.71))).toBeTruthy();
    expect(screen.getByText(formatLevel(2.8))).toBeTruthy();
  });
});

describe('replacing somebody', () => {
  /**
   * The pool is opened **against a seat**, and where that seat is occupied the add is a
   * replacement — said before it happens, because the court is one screen away and a silent
   * swap of one handle for another is a destruction found out about afterwards.
   */
  it('names whom an add would replace, and swaps exactly them', async () => {
    await openThePool();
    fireEvent.press(await screen.findByLabelText(addLabel(B)));

    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));

    fireEvent.press(
      await screen.findByLabelText(
        seatLabel('YOUR_PARTNER', { kind: 'player', name: NAMES[B] ?? '', level: 2.8 }),
      ),
    );
    await waitFor(() => expect(screen).toHavePathname('/play/pool'));

    expect(await screen.findByText(replacingLine(NAMES[B] ?? ''))).toBeTruthy();

    fireEvent.press(screen.getByLabelText(addLabel(C)));

    expect(usePlaySession.getState().lineup).toEqual({
      originSearchId: SEARCH_ID,
      seats: [C],
    });
  });
});

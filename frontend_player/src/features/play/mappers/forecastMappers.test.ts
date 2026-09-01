/**
 * The builder's wire boundary: the two asks, and what an unknown code costs on the way back.
 *
 * Every assertion here is about a **narrowing decision** rather than about a renaming. An old
 * build holding a phone for eight months is the state §3 legislates for, and the four codes on
 * these two responses are dropped or kept for four different reasons.
 */

import type { components } from '@/generated/schema';

import {
  toArrangements,
  toForecastRequest,
  toLineupAnswer,
  toRunLineupRequest,
} from './forecastMappers';

type Wire = components['schemas'];

const ME = 'aaaaaaaa-0000-4000-8000-000000000000';
const B = 'bbbbbbbb-0000-4000-8000-000000000001';
const C = 'cccccccc-0000-4000-8000-000000000002';

function forecast(overrides: Partial<Wire['ForecastSchema']> = {}): Wire['ForecastSchema'] {
  return {
    pct: 78,
    sigma_group: 0.41,
    provisional: false,
    assumption: null,
    ...overrides,
  };
}

function arrangement(
  overrides: Partial<Wire['ArrangementSchema']> = {},
): Wire['ArrangementSchema'] {
  return {
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
        { seat_index: 3, relationship: 'OPPONENT' },
      ],
    },
    forecast: forecast(),
    ...overrides,
  };
}

function lineupResponse(lineup: Partial<Wire['LineupSchema']> = {}): Wire['LineupResponse'] {
  return {
    search: {
      search_id: '11111111-0000-4000-8000-000000000001',
      at: '2026-08-31T18:00:00Z',
      surface: 'LINEUP',
      mode: 'FOR_FUN',
      ruleset_version: 'ruleset-v1',
      engine_version: 'matchfit-v1',
      optimised_for: 'GROUP',
      index_stale: false,
      pool: {
        sport: 'PADEL',
        radius_km_used: 12,
        players_in_range: 7,
        window: 'THIS_WEEK',
        post_gate: true,
      },
      radius_clamp: false,
      sorts_available: [],
      rung_offers: null,
    },
    candidates: [],
    lineup: {
      seats: [
        { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
        { side: 'A', seat_index: 1, relationship: 'PARTNER', player_id: B },
        { side: 'B', seat_index: 2, relationship: 'OPPONENT', player_id: C },
        { side: 'B', seat_index: 3, relationship: 'OPPONENT', unfilled_reason: 'POOL_EXHAUSTED' },
      ],
      arrangements: [arrangement()],
      ...lineup,
    },
  };
}

describe('the two asks', () => {
  /**
   * *"Send none and the engine fills every seat"* — so an empty list is **omitted** rather than
   * sent, because an empty array would be the same claim spelled a second way and the contract
   * only has one spelling of it.
   */
  it('omits `locked_seats` on ⚡ over an empty court', () => {
    const body = toRunLineupRequest({
      sport: 'padel',
      mode: 'FOR_FUN',
      lockedSeats: [],
      sentWeek: undefined,
    });

    expect(body).toEqual({ sport: 'PADEL', mode: 'FOR_FUN' });
    expect('locked_seats' in body).toBe(false);
    expect('availability_override' in body).toBe(false);
  });

  /** Hand-seating somebody and pressing ⚡ is the same request with a list on it. */
  it('sends the people already seated, in seat order', () => {
    expect(
      toRunLineupRequest({
        sport: 'padel',
        mode: 'COMPETITIVE',
        lockedSeats: [B, C],
        sentWeek: [{ day: 2, part: 'evening' }],
      }),
    ).toEqual({
      sport: 'PADEL',
      mode: 'COMPETITIVE',
      locked_seats: [B, C],
      availability_override: [{ day: 2, part: 'EVENING' }],
    });
  });

  /** An **empty** week is a cleared week and a legal ask — the absence #247 stopped conflating. */
  it('sends a cleared week rather than dropping it', () => {
    const body = toRunLineupRequest({
      sport: 'padel',
      mode: 'FOR_FUN',
      lockedSeats: [],
      sentWeek: [],
    });

    expect(body.availability_override).toEqual([]);
  });

  /** The forecast's `search_id` is the **Origin key**, and the players are in seat order. */
  it('cites the origin search and names the people beside you', () => {
    expect(
      toForecastRequest({
        sport: 'padel',
        mode: 'FOR_FUN',
        searchId: '11111111-0000-4000-8000-000000000001',
        players: [B, C],
      }),
    ).toEqual({
      sport: 'PADEL',
      mode: 'FOR_FUN',
      search_id: '11111111-0000-4000-8000-000000000001',
      players: [B, C],
    });
  });
});

describe('the answer', () => {
  it('flattens both sides into seat order and keeps every way round', () => {
    const [only] = toArrangements([arrangement()]);

    expect(only?.seats.map((seat) => seat.seatIndex)).toEqual([0, 1, 2, 3]);
    expect(only?.seats.map((seat) => seat.relationship)).toEqual([
      'SELF',
      'PARTNER',
      'OPPONENT',
      'OPPONENT',
    ]);
    // An open seat is the absence of an id rather than a hole in the list.
    expect(only?.seats[3]?.playerId).toBeUndefined();
  });

  /**
   * **Omitted stays omitted.** *"There was nothing to be best by here"* — an incomplete four, a
   * singles line-up, every forecast — is a different statement from *this one is not the best*,
   * and a `?? false` would collapse them.
   */
  it('keeps `is_best` absent where the engine computed no objective', () => {
    const [only] = toArrangements([arrangement()]);
    expect(only && 'isBest' in only).toBe(false);

    const [best] = toArrangements([arrangement({ is_best: false })]);
    expect(best?.isBest).toBe(false);
  });

  /** The figure and its caveat are one object, and `provisional` is passed rather than derived. */
  it('carries the caveat inside the figure', () => {
    const [only] = toArrangements([
      arrangement({
        forecast: forecast({
          provisional: true,
          assumption: 'EMPTY_SEAT_MATCHES_ITS_PARTNER',
        }),
      }),
    ]);

    expect(only?.forecast).toEqual({
      pct: 78,
      sigmaGroup: 0.41,
      provisional: true,
      assumption: 'EMPTY_SEAT_MATCHES_ITS_PARTNER',
    });
  });

  /**
   * An assumption this build has no words for **still leaves the figure provisional**. The
   * boolean is the engine's and is never re-derived from the code beside it, so a screen that
   * cannot state the caveat can still say there is one.
   */
  it('drops an assumption it cannot read and keeps the fact that there was one', () => {
    const [only] = toArrangements([
      arrangement({ forecast: forecast({ provisional: true, assumption: 'SOMETHING_NEWER' }) }),
    ]);

    expect(only?.forecast.provisional).toBe(true);
    expect(only?.forecast.assumption).toBeNull();
  });

  it('reads the court, the shortfall and the reason this four won', () => {
    const answer = toLineupAnswer(
      lineupResponse({ group_reason: 'EVENEST_ARRANGEMENT', dock: 'NO_SHARED_SLOTS' }),
    );

    expect(answer.court.seats).toEqual([
      { seatIndex: 0, relationship: 'SELF', playerId: ME, unfilled: null },
      { seatIndex: 1, relationship: 'PARTNER', playerId: B, unfilled: null },
      { seatIndex: 2, relationship: 'OPPONENT', playerId: C, unfilled: null },
      { seatIndex: 3, relationship: 'OPPONENT', unfilled: 'POOL_EXHAUSTED' },
    ]);
    expect(answer.court.groupReason).toBe('EVENEST_ARRANGEMENT');
    expect(answer.court.dock).toBe('NO_SHARED_SLOTS');
  });

  /** *Omitted rather than sent as null*, and the two mean different things — so both read null. */
  it('reads an absent reason and an absent dock as nothing said', () => {
    const answer = toLineupAnswer(lineupResponse());

    expect(answer.court.groupReason).toBeNull();
    expect(answer.court.dock).toBeNull();
  });

  /** The envelope's own new field, which is the whole of what a hand-seated court has to say. */
  it('carries whom the answer was optimised for', () => {
    expect(toLineupAnswer(lineupResponse()).envelope.optimisedFor).toBe('GROUP');
  });

  /**
   * **A seat this build cannot place is dropped**, and it is the one drop in this file.
   *
   * `SELF` and `PARTNER` are what a court reads a *side* off — no route serves a searcher their
   * own id, so a relationship it cannot name leaves the seat unplaceable. Drawing it at a guess
   * would put somebody in the wrong half, which is the one thing the vocabulary exists to stop
   * a client doing; drawing nothing is visible, and drawing it wrongly is not.
   */
  it('drops a seat whose relationship this build cannot place', () => {
    const [only] = toArrangements([
      arrangement({
        sides: {
          A: [{ seat_index: 0, relationship: 'REFEREE' as Wire['Relationship'], player_id: ME }],
          B: [{ seat_index: 1, relationship: 'OPPONENT', player_id: C }],
        },
      }),
    ]);

    expect(only?.seats).toEqual([{ seatIndex: 1, relationship: 'OPPONENT', playerId: C }]);
  });

  /**
   * **An unfilled reason it cannot read is dropped and the seat stands.** An open seat with
   * nothing to say is the state a *forecast's* own open seats are already in — the searcher
   * simply has not filled them — so nothing on screen is left unaccounted for.
   */
  it('drops a shortfall code it cannot read, and keeps the seat', () => {
    const answer = toLineupAnswer(
      lineupResponse({
        seats: [
          {
            side: 'B',
            seat_index: 3,
            relationship: 'OPPONENT',
            unfilled_reason: 'NOBODY_WITHIN_A_MILE' as Wire['UnfilledReason'],
          },
        ],
      }),
    );

    expect(answer.court.seats).toEqual([
      { seatIndex: 3, relationship: 'OPPONENT', unfilled: null },
    ]);
  });

  it('drops a group reason it has no sentence for', () => {
    const answer = toLineupAnswer(
      lineupResponse({ group_reason: 'BEST_VIBES' as Wire['GroupReason'] }),
    );

    expect(answer.court.groupReason).toBeNull();
  });
});

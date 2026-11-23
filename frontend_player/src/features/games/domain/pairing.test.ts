/**
 * **The two rules the court's pairing carries into `domain/`**: whose row is drawn first, and
 * which of the route's refusals is an answer rather than a failure.
 *
 * The shapes themselves are types and carry no rule — the figures are the server's, and
 * a client never computes a gap, a range or a band from them.
 */

import { AppError } from '@/shared/errors';
import type { SocialVibeColumn } from '@/shared/vocabulary/socialVibeGrid';

import type { GameSeat } from './game';
import { pairingCardOf, pairingRefusedByName, sidesForReader, type Pairing } from './pairing';

const ME = 'me-1111-4444-8888-000000000001';
const PARTNER = 'partner-11-4444-8888-000000002';
const OPPONENT = 'opp-111111-4444-8888-00000003';

const seat = (playerId: string, side: 'A' | 'B'): GameSeat => ({ playerId, side });

describe('pairingRefusedByName', () => {
  const refused = (status: number, code: string) =>
    new AppError('not-found', 'terminal', 'refused', { status, code });

  /**
   * The route's three refusals are **answers**: no game of yours has that id, the game has
   * happened, or the account is held. Each is *no pairing to draw* rather than a failure to
   * retry, and the block draws nothing either way — what the name buys is that a refusal is
   * never reported or retried as an outage.
   */
  it.each([
    [404, 'game_not_found'],
    [409, 'pairing_is_history'],
    [403, 'account_held'],
  ])('is true for %s %s', (status, code) => {
    expect(pairingRefusedByName(refused(status, code))).toBe(true);
  });

  /** Branch on the code, never on the status: a 409 with another name is not this refusal. */
  it('is false for a status without one of the three names', () => {
    expect(pairingRefusedByName(refused(409, 'something_else'))).toBe(false);
    expect(
      pairingRefusedByName(new AppError('network-unavailable', 'retryable-automatically', 'x')),
    ).toBe(false);
  });
});

describe('sidesForReader', () => {
  /** The same order as two halves — one split, read by the bar's labels and the row's names. */
  it('splits the court into yours and theirs, you first on yours', () => {
    const court = [seat(OPPONENT, 'A'), seat(PARTNER, 'B'), seat(ME, 'B')];

    expect(sidesForReader(court, ME)).toEqual({
      yours: [seat(ME, 'B'), seat(PARTNER, 'B')],
      theirs: [seat(OPPONENT, 'A')],
    });
  });

  it('has no halves for a reader holding no seat', () => {
    expect(sidesForReader([seat(OPPONENT, 'A')], ME)).toBeUndefined();
  });
});

describe('pairingCardOf', () => {
  const RIVAL = 'rival-1111-4444-8888-00000004';

  /** The table as the composer's tiles stand: you first, then the others. */
  const COLUMNS: readonly SocialVibeColumn[] = [
    { playerId: ME, isYou: true },
    { playerId: OPPONENT, isYou: false, name: 'zofia.b', photoUrl: 'https://img/zofia' },
    { playerId: RIVAL, isYou: false, name: 'ania.k' },
    { playerId: PARTNER, isYou: false, name: 'kuba.w' },
  ];

  /** A For-fun court as #835 serves it: the vibe, and the forecast still sent for older apps. */
  const PAIRING: Pairing = {
    readAt: '2026-09-12T09:00:00Z',
    forecast: { pct: 90 },
    split: { yourSide: 2.7, theirSide: 2.71, gap: -0.01 },
    atStake: { winDelta: 0.08, lossDelta: -0.08 },
    seats: [],
    vibe: {
      pct: 67,
      rows: [
        // Carried in the reader's direction — you, your side, theirs — not the columns' order.
        { tag: 'STAYS_FOR_A_DRINK', carriedBy: [ME, PARTNER] },
        { tag: 'GENEROUS_ON_LINE_CALLS', carriedBy: [ME, OPPONENT, RIVAL] },
        { tag: 'HERE_FOR_A_REGULAR_GAME', carriedBy: [ME] },
      ],
    },
  };

  describe('on For fun', () => {
    /** ADR-0207 §5: the Social vibe card where *A friendly — nothing moves.* stood. */
    it('is the Social vibe card, the served % over the columns handed in', () => {
      const card = pairingCardOf('FRIENDLY', PAIRING, COLUMNS);

      expect(card?.kind).toBe('vibe');
      if (card?.kind !== 'vibe') return;
      expect(card.grid.pct).toBe(67);
      expect(card.grid.columns).toEqual(COLUMNS);
    });

    /** The rows are the read's, in its order; the dots stand in the columns' order. */
    it('puts a dot under every carrier, in the columns’ order', () => {
      const card = pairingCardOf('FRIENDLY', PAIRING, COLUMNS);
      if (card?.kind !== 'vibe') throw new Error('no vibe card');

      expect(card.grid.rows.map((row) => [row.tag, row.dots])).toEqual([
        ['STAYS_FOR_A_DRINK', [true, false, false, true]],
        ['GENEROUS_ON_LINE_CALLS', [true, true, true, false]],
        ['HERE_FOR_A_REGULAR_GAME', [true, false, false, false]],
      ]);
    });

    /** Pale volt where somebody else carries it; grey where only you do. */
    it('shares a row somebody else carries, and keeps one only you carry yours', () => {
      const card = pairingCardOf('FRIENDLY', PAIRING, COLUMNS);
      if (card?.kind !== 'vibe') throw new Error('no vibe card');

      expect(card.grid.rows.map((row) => row.shared)).toEqual([true, true, false]);
    });

    /** A carrier with no column draws no dot, so it cannot band the row either. */
    it('shares a row only through a carrier the grid draws', () => {
      const card = pairingCardOf(
        'FRIENDLY',
        {
          ...PAIRING,
          vibe: { pct: 40, rows: [{ tag: 'SHARES_A_LIFT', carriedBy: [ME, 'gone'] }] },
        },
        COLUMNS,
      );
      if (card?.kind !== 'vibe') throw new Error('no vibe card');

      expect(card.grid.rows).toEqual([
        { tag: 'SHARES_A_LIFT', dots: [true, false, false, false], shared: false },
      ]);
    });

    /** The forecast still sent for older apps is ignored, and nothing stands in for a vibe. */
    it('is nothing when the pairing sends no vibe, whatever forecast it sends', () => {
      const { vibe: _none, ...withoutVibe } = PAIRING;

      expect(pairingCardOf('FRIENDLY', withoutVibe, COLUMNS)).toBeUndefined();
    });
  });

  describe('on a competitive game', () => {
    /** Unchanged: the forecast, its split and the stakes, as a booked game drew them. */
    it('is the forecast with its split and the stakes', () => {
      expect(pairingCardOf('COUNTED', PAIRING, COLUMNS)).toEqual({
        kind: 'forecast',
        forecast: { pct: 90 },
        split: { yourSide: 2.7, theirSide: 2.71, gap: -0.01 },
        atStake: { winDelta: 0.08, lossDelta: -0.08 },
      });
    });

    it('is the forecast with no tiles when nothing is at stake', () => {
      const { atStake: _none, ...unpriced } = PAIRING;

      expect(pairingCardOf('COUNTED', unpriced, COLUMNS)).toEqual({
        kind: 'forecast',
        forecast: { pct: 90 },
        split: { yourSide: 2.7, theirSide: 2.71, gap: -0.01 },
      });
    });

    /** ADR-0161 §4: no forecast is no card, and a vibe a read sent anyway is never drawn. */
    it('is nothing without a forecast, even with a vibe', () => {
      const { forecast: _f, split: _s, ...unforecast } = PAIRING;

      expect(pairingCardOf('COUNTED', unforecast, COLUMNS)).toBeUndefined();
    });
  });

  /** A kind this build cannot read keeps today's drawing: the forecast, if one is served. */
  it('draws the forecast for a kind this build cannot read', () => {
    expect(pairingCardOf(undefined, PAIRING, COLUMNS)?.kind).toBe('forecast');
  });
});

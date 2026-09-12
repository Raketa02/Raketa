/**
 * The pairing's wire boundary: `GamePairingResponse` in, a {@link Pairing} out, and **every figure
 * carried as served** — no rounding, no subtraction, no band from a Level.
 */

import type { Wire } from '@/test-support/transport';

import { toPairing } from './pairingMappers';

const READ_AT = '2026-09-12T09:00:00Z';

const SEAT: Wire['GamePairingSeatSchema'] = {
  player_id: 'me',
  level: 2.71,
  band: 'Established',
  range: { low: 2.55, high: 2.87 },
  confidence: 74,
};

function wire(over: Partial<Wire['GamePairingResponse']> = {}): Wire['GamePairingResponse'] {
  return {
    read_at: READ_AT,
    forecast: { pct: 90, sigma_group: 0.4, provisional: false, assumption: null },
    split: { your_side: 2.7, their_side: 2.71, gap: -0.01 },
    at_stake: { win_delta: 0.08, loss_delta: -0.08 },
    seats: [SEAT, { ...SEAT, player_id: 'them', level: 2.8, confidence: 88 }],
    ...over,
  };
}

describe('the pairing off the wire', () => {
  it('carries the three blocks and the seats as served, and the instant they were read at', () => {
    expect(toPairing(wire())).toEqual({
      readAt: READ_AT,
      forecast: { pct: 90 },
      split: { yourSide: 2.7, theirSide: 2.71, gap: -0.01 },
      atStake: { winDelta: 0.08, lossDelta: -0.08 },
      seats: [
        {
          playerId: 'me',
          level: 2.71,
          band: 'Established',
          range: { low: 2.55, high: 2.87 },
          confidence: 74,
        },
        {
          playerId: 'them',
          level: 2.8,
          band: 'Established',
          range: { low: 2.55, high: 2.87 },
          confidence: 88,
        },
      ],
    });
  });

  /** The gap is signed by the engine and read in the reader's direction. Its sign is kept. */
  it('keeps the gap’s sign as served', () => {
    expect(
      toPairing(wire({ split: { your_side: 2.8, their_side: 2.6, gap: 0.2 } })).split?.gap,
    ).toBe(0.2);
  });

  /** ADR-0161 §4: the forecast and the split are one computation and are omitted together. */
  it('has neither forecast nor split when the wire omitted them', () => {
    const pairing = toPairing(wire({ forecast: undefined, split: undefined }));

    expect(pairing.forecast).toBeUndefined();
    expect(pairing.split).toBeUndefined();
    expect(pairing.atStake).toEqual({ winDelta: 0.08, lossDelta: -0.08 });
  });

  /**
   * A half of one computation is not drawable — the block prints the two strengths under the
   * percentage — so a response carrying one without the other is read as carrying neither.
   */
  it('drops a forecast that arrived without its split, and a split without its forecast', () => {
    expect(toPairing(wire({ split: undefined })).forecast).toBeUndefined();
    expect(toPairing(wire({ forecast: undefined })).split).toBeUndefined();
  });

  /**
   * *Omitted, never provisional* (ADR-0161 §4): a line-up is frozen at the plan, so the flag is
   * never `true` on a game today. The engine's own rule for the flag is that the failure guarded
   * against is *a screen showing the number without its caveat* — and this screen draws no
   * caveat, so a provisional figure, should one ever cross, is an absence here.
   */
  it('reads a provisional forecast as no forecast', () => {
    const pairing = toPairing(
      wire({
        forecast: { pct: 90, sigma_group: 0.4, provisional: true, assumption: 'SHORT_SIDE' },
      }),
    );

    expect(pairing.forecast).toBeUndefined();
    expect(pairing.split).toBeUndefined();
  });

  it('has nothing at stake on a friendly, where the wire omits it', () => {
    expect(toPairing(wire({ at_stake: undefined })).atStake).toBeUndefined();
  });

  it('names nobody when nobody on the court holds a rating', () => {
    expect(toPairing(wire({ seats: [] })).seats).toEqual([]);
  });
});

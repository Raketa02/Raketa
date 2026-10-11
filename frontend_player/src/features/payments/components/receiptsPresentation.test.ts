/**
 * What a receipt row says: the seller, the game, the amount signed by which way it went, and what
 * the movement leaves to explain — the fee kept on a refund, the day a hold was let go (#644).
 */

import type { Receipt } from '../domain/receipts';

import {
  receiptAmount,
  receiptClub,
  receiptLabel,
  receiptLine,
  receiptNote,
} from './receiptsPresentation';

function receipt(extra: Partial<Receipt> = {}): Receipt {
  return {
    seatChargeId: 's-1',
    kind: 'CHARGE',
    club: { id: 'c-1', name: 'Bonarka Arena' },
    sport: 'padel',
    // 16:00 in Warsaw.
    startsAt: '2026-09-30T14:00:00Z',
    amountGrosze: 2800,
    movedAt: '2026-09-30T14:00:00Z',
    ...extra,
  };
}

/** Ivan's leave after the cut-off, his seat taken: 1,76 zł kept on his 40 zł (Q113). */
const REFUND = receipt({ kind: 'REFUND', amountGrosze: 3824, keptGrosze: 176 });

/** A leave before the cut-off: the 40 zł hold let go on Monday 28 September, 11:00 in Warsaw. */
const RELEASED = receipt({
  kind: 'RELEASED',
  amountGrosze: 4000,
  movedAt: '2026-09-28T09:00:00Z',
});

describe('a receipt row', () => {
  it('reads as mock 49 for a charge: the club, Padel · Today · 16:00, −28 zł · paid', () => {
    expect(receiptClub(receipt())).toBe('Bonarka Arena');
    expect(receiptLine(receipt(), { kind: 'today' })).toBe('Padel · Today · 16:00');
    expect(receiptAmount(receipt())).toBe('−28 zł · paid');
    expect(receiptNote(receipt())).toBeUndefined();
  });

  it('signs a refund with a plus, grosze and all, with exactly what was kept under it', () => {
    expect(receiptAmount(REFUND)).toBe('+38,24 zł · refunded');
    expect(receiptNote(REFUND)).toBe('1,76 zł kept on your payment');
  });

  /** The club cancelled after the cut-off: everything back, and nothing kept to say. */
  it('says nothing kept under a refund in full, nor where the read gave no fee', () => {
    expect(receiptNote(receipt({ kind: 'REFUND', keptGrosze: 0 }))).toBeUndefined();
    expect(receiptNote(receipt({ kind: 'REFUND' }))).toBeUndefined();
  });

  it('reads a hold let go unsigned, nothing having moved — with the day it was let go', () => {
    expect(receiptAmount(RELEASED)).toBe('40 zł held · released');
    expect(receiptNote(RELEASED)).toBe('Released 28 Sep');
  });

  it('names the date for a game further off, and a club that is gone as a club', () => {
    expect(receiptLine(receipt(), { kind: 'dated', day: '2026-09-26' })).toBe(
      'Padel · 26 Sep · 16:00',
    );
    expect(receiptClub(receipt({ club: { id: 'c-1' } }))).toBe('A club');
  });

  it('is spoken whole, saying which way the money went and what is left to explain', () => {
    expect(receiptLabel(receipt(), { kind: 'yesterday' })).toBe(
      'Bonarka Arena, Padel · Yesterday · 16:00, 28 zł paid',
    );
    expect(receiptLabel(REFUND, { kind: 'today' })).toBe(
      'Bonarka Arena, Padel · Today · 16:00, 38,24 zł refunded, 1,76 zł kept on your payment',
    );
    expect(receiptLabel(RELEASED, { kind: 'today' })).toBe(
      'Bonarka Arena, Padel · Today · 16:00, 40 zł held, released 28 Sep',
    );
  });
});

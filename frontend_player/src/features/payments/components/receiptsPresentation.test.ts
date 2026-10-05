/** What a receipt row says: the seller, the game, and the amount signed by which way it went. */

import type { Receipt } from '../domain/receipts';

import { receiptAmount, receiptClub, receiptLabel, receiptLine } from './receiptsPresentation';

function receipt(extra: Partial<Receipt> = {}): Receipt {
  return {
    seatChargeId: 's-1',
    kind: 'CHARGE',
    club: { id: 'c-1', name: 'Bonarka Arena' },
    sport: 'padel',
    // 16:00 in Warsaw.
    startsAt: '2026-09-30T14:00:00Z',
    amountGrosze: 2800,
    ...extra,
  };
}

describe('a receipt row', () => {
  it('reads as mock 49 for a charge: the club, Padel · Today · 16:00, −28 zł', () => {
    expect(receiptClub(receipt())).toBe('Bonarka Arena');
    expect(receiptLine(receipt(), { kind: 'today' })).toBe('Padel · Today · 16:00');
    expect(receiptAmount(receipt())).toBe('−28 zł');
  });

  it('signs a refund with a plus, grosze and all', () => {
    expect(receiptAmount(receipt({ kind: 'REFUND', amountGrosze: 2658 }))).toBe('+26,58 zł');
  });

  it('names the date for a game further off, and a club that is gone as a club', () => {
    expect(receiptLine(receipt(), { kind: 'dated', day: '2026-09-26' })).toBe(
      'Padel · 26 Sep · 16:00',
    );
    expect(receiptClub(receipt({ club: { id: 'c-1' } }))).toBe('A club');
  });

  it('is spoken whole, saying which way the money went', () => {
    expect(receiptLabel(receipt(), { kind: 'yesterday' })).toBe(
      'Bonarka Arena, Padel · Yesterday · 16:00, 28 zł paid',
    );
    expect(receiptLabel(receipt({ kind: 'REFUND' }), { kind: 'today' })).toBe(
      'Bonarka Arena, Padel · Today · 16:00, 28 zł refunded',
    );
  });
});

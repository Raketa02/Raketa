/**
 * A seat charge and the receipts off the wire: the facts the confirmation draws without the secret,
 * the secret only for the press that uses it, and the receipts in the server's order.
 */

import type { Wire } from '@/test-support/transport';

import { toPaymentToConfirm, toReceipts, toSeatCharge } from './seatChargeMappers';

const CLUB: Wire['SellerSchema'] = {
  id: 'b0000000-0000-4000-8000-000000000001',
  name: 'Bonarka Arena',
};

function charge(extra: Partial<Wire['SeatChargeResponse']> = {}): Wire['SeatChargeResponse'] {
  return {
    seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
    proposal_id: 'c0000000-0000-4000-8000-000000000001',
    status: 'FAILED',
    refusal: 'AUTHENTICATION_REQUIRED',
    amount_grosze: 3200,
    sport: 'PADEL',
    starts_at: '2026-10-03T14:00:00Z',
    club: CLUB,
    to_confirm: {
      client_secret: 'pi_1_secret_abc',
      connected_account_id: 'acct_club',
      publishable_key: 'pk_test_raketa',
    },
    ...extra,
  };
}

describe('a seat charge', () => {
  it('reads what the confirmation draws, and never the secret', () => {
    const read = toSeatCharge(charge());

    expect(read).toEqual({
      seatChargeId: 'a2000000-0000-4000-8000-000000000001',
      refusal: 'AUTHENTICATION_REQUIRED',
      amountGrosze: 3200,
      sport: 'padel',
      startsAt: '2026-10-03T14:00:00Z',
      club: { id: CLUB.id, name: 'Bonarka Arena' },
      awaitsYou: true,
    });
    expect(JSON.stringify(read)).not.toContain('secret');
  });

  it('says a payment that no longer waits does not, and a club that is gone has no name', () => {
    expect(
      toSeatCharge(charge({ to_confirm: null, status: 'CAPTURED', club: { ...CLUB, name: null } })),
    ).toMatchObject({ awaitsYou: false, club: { id: CLUB.id } });
  });

  it('hands the press the key, the club’s account and the secret — or nothing once it no longer waits', () => {
    expect(toPaymentToConfirm(charge())).toEqual({
      publishableKey: 'pk_test_raketa',
      accountId: 'acct_club',
      clientSecret: 'pi_1_secret_abc',
    });
    expect(toPaymentToConfirm(charge({ to_confirm: null }))).toBeNull();
  });
});

describe('the receipts', () => {
  it('keeps the server’s order and the club as the seller', () => {
    const receipt = (id: string, name: string): Wire['ReceiptSchema'] => ({
      seat_charge_id: id,
      kind: 'CHARGE',
      club: { ...CLUB, name },
      sport: 'PADEL',
      starts_at: '2026-09-30T14:00:00Z',
      amount_grosze: 2800,
      card_fee_grosze: null,
      paid_at: '2026-09-29T18:00:00Z',
    });

    expect(
      toReceipts({ receipts: [receipt('r-2', 'Bonarka Arena'), receipt('r-1', 'Ogrody 33')] }),
    ).toEqual([
      {
        seatChargeId: 'r-2',
        kind: 'CHARGE',
        club: { id: CLUB.id, name: 'Bonarka Arena' },
        sport: 'padel',
        startsAt: '2026-09-30T14:00:00Z',
        amountGrosze: 2800,
      },
      expect.objectContaining({ seatChargeId: 'r-1', club: { id: CLUB.id, name: 'Ogrody 33' } }),
    ]);
  });
});

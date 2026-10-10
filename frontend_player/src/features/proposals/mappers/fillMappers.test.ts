/**
 * A yes's answer off the wire — the seats left, the booking it made, and this player's own refused
 * share — in the words `fillOutcome` decides by.
 */

import type { Wire } from '@/test-support/transport';

import { liveYes } from '@/test-support/groupDeck';

import { toPaymentsToConfirm, toYesAnswer } from './fillMappers';

const PROPOSAL = 'c0000000-0000-4000-8000-000000000001';

describe('a yes’s answer', () => {
  it('reads a vote counted, with nothing booked and nothing refused', () => {
    const wire: Wire['YesAnswerResponse'] = {
      proposal_id: PROPOSAL,
      open_seats: 2,
      waiting_for_the_club: false,
    };

    expect(toYesAnswer(wire)).toEqual({
      proposalId: PROPOSAL,
      openSeats: 2,
      booked: null,
      waitingForTheClub: false,
      yourPayment: null,
    });
  });

  it('reads a full game sent to an On request club to confirm', () => {
    const wire: Wire['YesAnswerResponse'] = {
      proposal_id: PROPOSAL,
      open_seats: 0,
      booked: null,
      waiting_for_the_club: true,
      your_payment: null,
    };

    expect(toYesAnswer(wire).waitingForTheClub).toBe(true);
  });

  it('reads the booking and the Game it opened', () => {
    const wire: Wire['YesAnswerResponse'] = {
      proposal_id: PROPOSAL,
      open_seats: 0,
      booked: { booking_id: PROPOSAL, game_id: 'a1000000-0000-4000-8000-000000000001' },
      waiting_for_the_club: false,
      your_payment: null,
    };

    expect(toYesAnswer(wire).booked).toEqual({
      bookingId: PROPOSAL,
      gameId: 'a1000000-0000-4000-8000-000000000001',
    });
  });

  it('reads this player’s refused share, by its payment and its reason', () => {
    const wire: Wire['YesAnswerResponse'] = {
      proposal_id: PROPOSAL,
      open_seats: 1,
      booked: null,
      waiting_for_the_club: false,
      your_payment: {
        seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
        refusal: 'DECLINED',
      },
    };

    expect(toYesAnswer(wire).yourPayment).toEqual({
      seatChargeId: 'a2000000-0000-4000-8000-000000000001',
      refusal: 'DECLINED',
    });
  });

  it('reads the time to pay — this player’s own, and the payment the game waits for (#625)', () => {
    const wire: Wire['YesAnswerResponse'] = {
      proposal_id: PROPOSAL,
      open_seats: 0,
      booked: null,
      waiting_for_the_club: false,
      your_payment: {
        seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
        refusal: 'AUTHENTICATION_REQUIRED',
        confirm_by: '2026-10-06T12:40:00Z',
      },
      payment_awaited_until: '2026-10-06T12:40:00Z',
    };

    expect(toYesAnswer(wire)).toMatchObject({
      yourPayment: { confirmBy: '2026-10-06T12:40:00Z' },
      paymentAwaitedUntil: '2026-10-06T12:40:00Z',
    });
  });

  it('reads no time to pay from a null, or an older server’s silence', () => {
    const wire: Wire['YesAnswerResponse'] = {
      proposal_id: PROPOSAL,
      open_seats: 1,
      waiting_for_the_club: false,
      your_payment: {
        seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
        refusal: 'DECLINED',
        confirm_by: null,
      },
      payment_awaited_until: null,
    };

    expect(toYesAnswer(wire).yourPayment).not.toHaveProperty('confirmBy');
    expect(toYesAnswer(wire)).not.toHaveProperty('paymentAwaitedUntil');
  });
});

describe('the payments to confirm', () => {
  const waiting = (refusal: Wire['PaymentRefusal'], confirmBy: string | null = null) => ({
    ...liveYes(),
    seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
    refusal,
    confirm_by: confirmBy,
    time_to: confirmBy === null ? null : ('FIX_THE_CARD' as const),
  });

  it('reads each as the live yes it reopened, with its payment', () => {
    const wire = waiting('DECLINED');

    expect(toPaymentsToConfirm({ payments: [wire] })).toEqual([
      expect.objectContaining({
        proposalId: wire.proposal_id,
        groupId: wire.pool_id,
        sport: 'padel',
        kind: 'competitive',
        shareGrosze: 2800,
        seatChargeId: 'a2000000-0000-4000-8000-000000000001',
        refusal: 'DECLINED',
      }),
    ]);
  });

  it('carries the time to pay while it runs, and none once it ran out (#625)', () => {
    const [timed, lapsed] = toPaymentsToConfirm({
      payments: [waiting('AUTHENTICATION_REQUIRED', '2026-10-06T12:40:00Z'), waiting('DECLINED')],
    });

    expect(timed?.confirmBy).toBe('2026-10-06T12:40:00Z');
    expect(lapsed).not.toHaveProperty('confirmBy');
  });

  it('leaves out a refusal that does not wait for the player', () => {
    expect(toPaymentsToConfirm({ payments: [waiting('TERMS_NEEDED')] })).toEqual([]);
  });
});

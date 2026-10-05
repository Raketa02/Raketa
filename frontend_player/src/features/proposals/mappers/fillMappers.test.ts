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
});

describe('the payments to confirm', () => {
  const waiting = (refusal: Wire['PaymentRefusal']) => ({
    ...liveYes(),
    seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
    refusal,
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

  it('leaves out a refusal that does not wait for the player', () => {
    expect(toPaymentsToConfirm({ payments: [waiting('TERMS_NEEDED')] })).toEqual([]);
  });
});

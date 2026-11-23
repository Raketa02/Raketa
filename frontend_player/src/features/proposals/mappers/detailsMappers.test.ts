import type { Wire } from '@/test-support/transport';

import { ANIA, EWA, KAROL, deckCard, proposalDetails, youTile } from '@/test-support/groupDeck';

import { toProposalDetails } from './detailsMappers';

describe('a game still filling, in detail', () => {
  it('reads the status, what the reader may do, the seats, WHERE with its distance and the book-by', () => {
    const card = deckCard({
      in_count: 1,
      sides: { yours: [youTile(), KAROL({ is_in: true })], theirs: [ANIA(), EWA()] },
    });
    const details = toProposalDetails(proposalDetails(card));

    expect(details).toMatchObject({
      proposalId: card.proposal_id,
      groupId: 'a0000000-0000-4000-8000-000000000005',
      type: 'PICKED_FOR_YOU',
      kind: 'competitive',
      sport: 'padel',
      status: 'FILLING',
      actions: ['YES', 'NO'],
      inCount: 1,
      seats: 4,
      where: { id: card.club.id, name: 'Bonarka Arena', distanceKm: 3.1 },
      shareGrosze: 3200,
      deadline: card.deadline,
      forecast: { pct: 87, provisional: false },
    });
    expect(details?.sides.yours[1]).toMatchObject({ name: 'karol.t', isIn: true });
    expect(details).not.toHaveProperty('yourPayment');
    expect(details).not.toHaveProperty('challenger');
  });

  it('reads the payment to confirm, and no distance for a reader with no Location area', () => {
    const wire: Wire['ProposalDetailsResponse'] = {
      ...proposalDetails(deckCard()),
      actions: ['CONFIRM_PAYMENT'],
      your_payment: {
        seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
        refusal: 'DECLINED',
      },
      where: { id: 'b0000000-0000-4000-8000-000000000001', name: null, distance_km: null },
    };

    expect(toProposalDetails(wire)).toMatchObject({
      yourPayment: { seatChargeId: 'a2000000-0000-4000-8000-000000000001', refusal: 'DECLINED' },
      where: { id: 'b0000000-0000-4000-8000-000000000001' },
    });
    expect(toProposalDetails(wire)?.where).not.toHaveProperty('distanceKm');
  });

  it('carries the payment the game waits for, and the reader’s own time to pay (#625)', () => {
    const card = deckCard();
    const waiting = proposalDetails(card, {
      status: 'WAITING_FOR_A_PAYMENT',
      actions: ['LEAVE', 'CONFIRM_PAYMENT'],
      payment_due_by: '2026-10-06T12:40:00Z',
      your_payment: {
        seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
        refusal: 'AUTHENTICATION_REQUIRED',
        confirm_by: '2026-10-06T12:40:00Z',
      },
    });

    expect(toProposalDetails(waiting)).toMatchObject({
      status: 'WAITING_FOR_A_PAYMENT',
      paymentDueBy: '2026-10-06T12:40:00Z',
      yourPayment: { confirmBy: '2026-10-06T12:40:00Z' },
    });
    expect(toProposalDetails(proposalDetails(card))).not.toHaveProperty('paymentDueBy');
    expect(
      toProposalDetails(proposalDetails(card, { payment_due_by: undefined })),
    ).not.toHaveProperty('paymentDueBy');
  });

  it('is nothing for a sport this build cannot name', () => {
    const wire = { ...proposalDetails(deckCard()), sport: 'CURLING' as Wire['Sport'] };
    expect(toProposalDetails(wire)).toBeUndefined();
  });
});

describe('the kind’s own card (#833, #839)', () => {
  it('reads a competitive game’s full forecast — the figure, both sides and the signed gap — and what is at stake', () => {
    const wire = proposalDetails(deckCard(), {
      forecast: { pct: 73, provisional: false, your_side: 2.65, their_side: 2.74, gap: -0.09 },
      at_stake: { win_delta: 0.08, loss_delta: -0.07 },
    });

    expect(toProposalDetails(wire)).toMatchObject({
      forecast: {
        pct: 73,
        provisional: false,
        split: { yourSide: 2.65, theirSide: 2.74, gap: -0.09 },
      },
      atStake: { winDelta: 0.08, lossDelta: -0.07 },
    });
  });

  // An older server (before #833) sends the card's forecast and no `at_stake`: no block — never a
  // block of blanks, and never a read that fails over a field it did not know to send.
  it('reads no forecast and no stakes from an older server’s read', () => {
    const { at_stake: _unsent, ...older } = proposalDetails(deckCard());
    const wire = {
      ...older,
      forecast: { pct: 87, provisional: false },
    } as unknown as Wire['ProposalDetailsResponse'];

    expect(toProposalDetails(wire)).not.toHaveProperty('forecast');
    expect(toProposalDetails(wire)).not.toHaveProperty('atStake');
    expect(toProposalDetails(wire)).toMatchObject({ status: 'FILLING' });
  });

  it('reads no forecast and no stakes where the read sends none', () => {
    const wire = proposalDetails(deckCard(), { forecast: null, at_stake: null });

    expect(toProposalDetails(wire)).not.toHaveProperty('forecast');
    expect(toProposalDetails(wire)).not.toHaveProperty('atStake');
  });
});

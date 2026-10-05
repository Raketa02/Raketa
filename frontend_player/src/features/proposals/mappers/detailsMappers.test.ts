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
    expect(details?.sides.yours[1]).toMatchObject({ name: 'Karol Tomaszewski', isIn: true });
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

  it('is nothing for a sport this build cannot name', () => {
    const wire = { ...proposalDetails(deckCard()), sport: 'CURLING' as Wire['Sport'] };
    expect(toProposalDetails(wire)).toBeUndefined();
  });
});

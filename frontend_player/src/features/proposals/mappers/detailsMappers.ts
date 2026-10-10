/**
 * **A game still filling, off the wire** — `GET /proposals/{id}` (#542) read into the domain's
 * shape ([#557](https://github.com/Raketa02/Raketa/issues/557)). The deck mapper's narrowings for
 * the same fields — the tiles, the challenger, the forecast and the grid are a card's — and a sport
 * this build cannot name, or a game cell outside the week, is nothing to draw.
 */

import { toSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { ProposalDetails } from '../domain/details';

import { toChallenger, toClub, toDeckSides, toForecast, toKind, toOverlap } from './deckMappers';
import { toYourPayment } from './fillMappers';
import { toAnswerBy, toPaymentDueBy } from './homeMappers';

type Schemas = components['schemas'];

export function toProposalDetails(
  wire: Schemas['ProposalDetailsResponse'],
): ProposalDetails | undefined {
  const sport = toSport(wire.sport);
  const overlap = toOverlap(wire.overlap);
  if (sport === undefined || overlap === undefined) return undefined;

  return {
    proposalId: wire.proposal_id,
    groupId: wire.pool_id,
    type: wire.type,
    kind: toKind(wire.kind),
    sport,
    ...toChallenger(wire.challenger),
    readAt: wire.read_at,
    status: wire.status,
    actions: wire.actions,
    ...(wire.your_payment === null ? {} : { yourPayment: toYourPayment(wire.your_payment) }),
    inCount: wire.in_count,
    seats: wire.seats,
    startsAt: wire.starts_at,
    where: {
      ...toClub(wire.where),
      ...(wire.where.distance_km === null ? {} : { distanceKm: wire.where.distance_km }),
    },
    shareGrosze: wire.share_grosze,
    deadline: wire.book_by,
    noFreeCancellation: wire.no_free_cancellation,
    clubConfirms: wire.club_confirms,
    ...toAnswerBy(wire.answer_by),
    ...toPaymentDueBy(wire),
    sides: toDeckSides(wire.sides),
    ...toForecast(wire.forecast),
    overlap,
  };
}

/**
 * **A game still filling, off the wire** — `GET /proposals/{id}` (#542) read into the domain's
 * shape ([#557](https://github.com/Raketa02/Raketa/issues/557)). The deck mapper's narrowings for
 * the same fields — the tiles, the challenger and the grid are a card's — and a sport this build
 * cannot name, or a game cell outside the week, is nothing to draw. **The forecast is the details'
 * own** since #833: the card's figure with both side strengths and the signed gap, and what is at
 * stake beside it.
 */

import { toSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { ProposalDetails } from '../domain/details';

import { toChallenger, toClub, toDeckSides, toKind, toOverlap } from './deckMappers';
import { toYourPayment } from './fillMappers';
import { toPaymentDueBy } from './homeMappers';

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
    ...toPaymentDueBy(wire),
    sides: toDeckSides(wire.sides),
    ...toDetailsForecast(wire.forecast),
    ...toAtStake(wire.at_stake),
    overlap,
  };
}

/**
 * The forecast as a server sends it — the full one since #833, or **an older server's**, the card's
 * figure alone, with no strengths and no gap.
 */
type ServedForecast = Pick<Schemas['DetailsForecastSchema'], 'pct' | 'provisional'> &
  Partial<Pick<Schemas['DetailsForecastSchema'], 'your_side' | 'their_side' | 'gap'>>;

/**
 * A competitive game's full forecast — the figure, and the two side strengths and the signed gap it
 * was read from, nested as the block draws them (#833). **Nothing from an older server** that sends
 * the figure alone: the block needs both halves, and a block of blanks is worse than none.
 */
function toDetailsForecast(wire: ServedForecast | null): Pick<ProposalDetails, 'forecast'> {
  if (wire === null) return {};
  const { your_side: yourSide, their_side: theirSide, gap } = wire;
  if (yourSide === undefined || theirSide === undefined || gap === undefined) return {};
  return {
    forecast: { pct: wire.pct, provisional: wire.provisional, split: { yourSide, theirSide, gap } },
  };
}

/** What is at stake for the reader — the pair, or nothing; absent from an older server's read. */
function toAtStake(
  wire: Schemas['DetailsAtStakeSchema'] | null | undefined,
): Pick<ProposalDetails, 'atStake'> {
  return wire === null || wire === undefined
    ? {}
    : { atStake: { winDelta: wire.win_delta, lossDelta: wire.loss_delta } };
}

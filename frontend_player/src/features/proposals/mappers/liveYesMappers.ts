/**
 * **The live yeses, off the wire** — the wire boundary for You › Payments' *LIVE YESES* (#554).
 *
 * The deck mapper's narrowings, for the same fields: a club's `null` name becomes an absent one,
 * the kind is read into the switch's spelling, and the sport into the app's own — a yes in a sport
 * this build cannot name is dropped rather than drawn under no sport, as a card outside the week
 * is. `book_by` arrives as the card's `deadline`, which is what the card calls it.
 */

import { toSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { LiveYes, LiveYeses } from '../domain/liveYes';

import { toClub, toKind } from './deckMappers';

type Schemas = components['schemas'];

export function toLiveYes(wire: Schemas['LiveYesSchema']): LiveYes | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  return {
    proposalId: wire.proposal_id,
    groupId: wire.pool_id,
    sport,
    kind: toKind(wire.kind),
    startsAt: wire.starts_at,
    club: toClub(wire.club),
    shareGrosze: wire.share_grosze,
    deadline: wire.book_by,
    ...(wire.indoor === null ? {} : { indoor: wire.indoor }),
  };
}

export function toLiveYeses(wire: Schemas['LiveYesesResponse']): LiveYeses {
  return {
    yeses: wire.yeses.map(toLiveYes).filter((yes): yes is LiveYes => yes !== undefined),
  };
}

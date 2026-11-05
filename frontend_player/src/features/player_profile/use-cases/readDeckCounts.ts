/**
 * Read how many cards each kind deals the player now in one sport, across their groups
 * (ADR-0201 §6) — what You › *What kind of game* counts a change of intent in.
 *
 * A pass-through over one request and one mapper, the uniform-strict shape `docs/architecture.md`
 * Part 1 sanctions: the rule that reads the counts is `domain/intentChangeCost`'s.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getDeckCounts } from '../api/playerProfileApi';
import type { DeckCounts } from '../domain/intentChangeCost';
import { toDeckCounts } from '../mappers/playerProfileMappers';

export interface ReadDeckCountsOptions {
  readonly signal?: AbortSignal;
}

export function readDeckCounts(
  sport: Sport,
  { signal }: ReadDeckCountsOptions = {},
): Promise<DeckCounts> {
  return getDeckCounts({ wireSport: toWireSport(sport), signal }).then(toDeckCounts);
}

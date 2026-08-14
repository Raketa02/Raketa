/**
 * A difficulty tier, as a tag.
 *
 * The engine's tiers are `basic` / `standard` / `discriminating`, and only the last gets
 * emphasis — a discriminating question is the one asked to separate players who have
 * already proved they are good, which is worth marking as different in kind.
 *
 * **An unrecognised tier renders with the default treatment rather than disappearing.**
 * Old app versions live on real phones for months and the engine will add tiers this build
 * has never seen; dropping the tag would silently hide something the engine said was worth
 * saying. The same fallback rule the evidence trail needs (#25), applied to the one place
 * this slice already meets it.
 *
 * The **label is the server's word**, not a translation of it: the tier names are the
 * engine's vocabulary, and restating them here would be a second copy to drift.
 */

import type { TagVariant } from '@/shared/ui';

export interface DifficultyTag {
  readonly label: string;
  readonly variant: TagVariant;
}

const VARIANT_BY_TIER: Readonly<Record<string, TagVariant>> = {
  basic: 'base',
  standard: 'base',
  discriminating: 'hot',
};

export function difficultyTag(tier: string): DifficultyTag {
  return { label: tier, variant: VARIANT_BY_TIER[tier] ?? 'base' };
}

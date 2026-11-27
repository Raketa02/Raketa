/**
 * How many Social tags a selection may hold, and what happens at each end.
 *
 * **Both numbers are served** (`GET /player-profile/options`) and the profile commit
 * re-validates against the same two, so a picker that reads them here cannot disagree with
 * the endpoint that accepts them. Nothing in this file knows what they are.
 *
 * ## The ceiling refuses; it does not rotate
 *
 * A ninth press is answered with `refused`, and the refusal carries **no selection** —
 * there is deliberately nothing for a caller to write back. Dropping the oldest to make
 * room would remove a choice the player made without telling them, and the ceiling exists
 * so a profile stays a signal rather than a checklist. Removal is never blocked: the
 * ceiling blocks adding and never blocks correcting.
 *
 * ## No renderer, no store, no served response
 *
 * The picker is the first screen to obey these rules and the You tab's *Tags* is the second
 * (ADR-0179 §2) — the same two numbers, the same refusal, a different screen. So the rules
 * are a function of a selection and its bounds, which is also what makes them testable
 * without mounting anything.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';

/** Both ends included: a selection of exactly `minimum` is enough, and one of exactly `maximum` is legal. */
export interface SocialTagSelectionBounds {
  readonly minimum: number;
  readonly maximum: number;
}

/**
 * What one press did.
 *
 * The two accepting arms carry the new selection; `refused` carries a reason and nothing
 * else, which is the type saying *nothing changed* rather than a comment saying it.
 */
export type SocialTagSelectionChange =
  | { readonly kind: 'selected'; readonly selection: readonly SocialTagId[] }
  | { readonly kind: 'removed'; readonly selection: readonly SocialTagId[] }
  | { readonly kind: 'refused'; readonly reason: 'at-the-ceiling' };

/**
 * Press a tag: add it, remove it, or refuse it because the selection is full.
 *
 * Removal is checked **first**, so a press on a selected tag at the ceiling removes it
 * rather than being refused for being a ninth — it is not one.
 *
 * The selection is appended to in **press order**. What a player picked first is a fact
 * about them, and re-sorting to the vocabulary's order would throw it away before the
 * commit ever saw it.
 */
export function toggleSocialTag(
  selection: readonly SocialTagId[],
  tagId: SocialTagId,
  bounds: SocialTagSelectionBounds,
): SocialTagSelectionChange {
  if (selection.includes(tagId)) {
    return { kind: 'removed', selection: selection.filter((held) => held !== tagId) };
  }
  if (selection.length >= bounds.maximum) {
    return { kind: 'refused', reason: 'at-the-ceiling' };
  }
  return { kind: 'selected', selection: [...selection, tagId] };
}

/**
 * Whether this selection may be continued from, and how far short it is if not.
 *
 * A **count**, not a sentence: the words belong to whichever screen is asking, and there
 * are going to be two of them. What the rule owes them is the number that makes a blocked
 * control say what is missing rather than merely being grey.
 */
export type SocialTagSelectionStanding =
  { readonly kind: 'short'; readonly missing: number } | { readonly kind: 'ready' };

export function selectionStanding(
  selection: readonly SocialTagId[],
  bounds: SocialTagSelectionBounds,
): SocialTagSelectionStanding {
  const missing = bounds.minimum - selection.length;
  return missing > 0 ? { kind: 'short', missing } : { kind: 'ready' };
}

/**
 * Whether two selections are the same answer — **by membership, never by order.**
 *
 * The profile holds its tags in the vocabulary's order whatever order the picker pressed
 * them in, and a draft is appended to in press order; so a draft that re-ordered the same
 * tags has nothing to save, and *Save* on the You tab is shut by this rather than by an
 * array comparison that would open it on nothing.
 */
export function sameSelection(a: readonly SocialTagId[], b: readonly SocialTagId[]): boolean {
  return a.length === b.length && a.every((tagId) => b.includes(tagId));
}

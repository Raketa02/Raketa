/**
 * The deck card's one reading of the Social tag overlap — **shared first**.
 *
 * `socialTagOverlap` answers *which of their tags the reader also chose* off the engine's own
 * `matched[]`, and it keeps the person's order by default: on the competitive card the row is
 * *what they published*, and re-ordering it by what the reader has in common would be a
 * different list. The deck card takes the other side of that trade
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7): up to six tags wrap over a photograph, and the volt *· you too* is the one thing on the
 * row a player is deciding on — so the shared ones lead and are never the ones cut off, and the
 * rest keep the person's own order behind them. One surface, one ordering, stated here and
 * applied by `socialTagOverlap` **before its cap** when asked for it, rather than sorted in a
 * component after the cap has already chosen.
 *
 * There was a second reading, a **count** for a *Shared tags* tile under the row. The tile went
 * on 2026-09-15 — the row it counted is directly above it, leading with the shared ones — and
 * the count went with it; the overlap's three spellings of absence stay the row's own.
 */

import type { SharedTag } from '@/shared/vocabulary/socialTagOverlap';

/**
 * The marked tags with the shared ones first, and the rest in the person's own order.
 *
 * Over the marked list rather than over the row, because it has to run **before the cap**:
 * `socialTagOverlap` applies it there when asked for the deck's order, so a shared tag is never
 * the one a seventh would cut off.
 */
export function sharedFirst(tags: readonly SharedTag[]): readonly SharedTag[] {
  return [...tags.filter((tag) => tag.shared), ...tags.filter((tag) => !tag.shared)];
}

/**
 * The deck card's two readings of the Social tag overlap — **shared first**, and **a count**.
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
 * The count is the *Shared tags* tile's, and it keeps the overlap's three spellings of absence
 * apart in the one register a tile has: **nought is a claim** — compared, nothing matched — and
 * *we do not know* is a dash. A tile printing `0` for an unread comparison would be the card
 * making a claim out of its own ignorance, which is `socialTagOverlap`'s third spelling arriving
 * through a number.
 */

import type { SharedTag, SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

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

/** How many tags the two share — or `undefined` where the platform does not know. */
export function sharedTagCount(row: SocialTagOverlap): number | undefined {
  switch (row.kind) {
    case 'shared':
      return row.tags.filter((tag) => tag.shared).length;
    case 'none-in-common':
      return 0;
    case 'unknown':
    case 'hidden':
      return undefined;
  }
}

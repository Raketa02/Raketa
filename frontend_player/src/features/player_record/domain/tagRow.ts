/**
 * **What the record's Social tag row draws** — their tags, and whichever register the reader is
 * entitled to.
 *
 * Two facts meet here and they come from different places, which is the whole reason this is a
 * rule rather than a prop passed through:
 *
 * - **The tags are the record's.** They are live, they are the subject's own fact, and they are
 *   what this sheet exists to show. A record opened from a chat with no search behind it still
 *   draws them.
 * - **The claim is the pairing's.** *You too* is the engine's `matched[]`, published on the
 *   search that returned them, and it is never recomputed from a profile read. So the caller
 *   hands one down and this decides which register it licenses.
 *
 * ## The row is not the recorded card's row
 *
 * Handing the card's own answer straight to the drawing was the obvious shape and it is wrong
 * twice over. A candidate whose tag terms **stood down** carries no tags on its card at all, so
 * the row would be hidden for somebody whose record plainly holds six; and a tag published
 * *since* the search would be missing from a sheet whose whole promise is that it is current.
 *
 * ## What is tinted, and what a tint is never allowed to become
 *
 * Only what the engine matched. A tag the reader also holds but which the engine never compared
 * — added after the search, or in a column that stood down — draws **untinted**, because *you
 * too* is a published judgement rather than a set intersection this client is free to perform.
 *
 * ## The claim about nothing survives, and the silence does not become one
 *
 * `none-in-common` is the one arm that is a claim about **everything**, and it stands as the
 * engine made it: compared, both columns live, nothing matched. Every other absence — no
 * overlap passed at all, a comparison this build cannot read, a comparison that matched none of
 * the tags still standing — draws the tags and says nothing, which is *we do not know* rather
 * than *there is nothing*.
 */

import { SOCIAL_TAG_ROW_CAP, type SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

export function recordTagRow(
  tags: readonly SocialTagId[],
  overlap: SocialTagOverlap | undefined,
): SocialTagOverlap {
  // The claim comes first: it is drawn **in the row's place**, so it outranks having tags to
  // draw. Six untinted tags under a line saying none of them matched is the surface answering
  // one question twice.
  if (overlap?.kind === 'none-in-common') return { kind: 'none-in-common' };

  const drawn = tags.slice(0, SOCIAL_TAG_ROW_CAP);
  if (drawn.length === 0) return { kind: 'hidden' };

  if (overlap?.kind === 'shared') {
    const matched = new Set(overlap.tags.filter((tag) => tag.shared).map((tag) => tag.id));
    return { kind: 'shared', tags: drawn.map((id) => ({ id, shared: matched.has(id) })) };
  }

  return { kind: 'unknown', tags: drawn };
}

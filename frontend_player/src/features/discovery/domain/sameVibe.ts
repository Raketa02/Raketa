/**
 * **A Same vibe player** — somebody who shares at least one Social tag with the reader, who they'd
 * enjoy a court and a coffee with ([#803](https://github.com/Raketa02/Raketa/issues/803); ADR-0204 §6;
 * the Home rows mechanics §8; the backend's #795 `SameVibePlayerSchema`).
 *
 * The rules are the server's — who is on the row, the **vibe %** (1 − ½ⁿ for n shared tags), the
 * order (more in common first, ties to fewer of theirs not shared), fresh before gaps — and this
 * feature draws its answer. **Skill plays no part**, so the reader sees the row with no level. What is
 * left here is where a request from the row was found.
 */

import type { FoundIn, FriendRelation } from '@/features/friends/types';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

/**
 * **Where a request from this row was found** — the tile's round button, the vibe sheet's worded one
 * and the record its face opens all send it, naming nothing else: the other person's Home reads *6
 * things in common*, counted when it is read (the mechanics §12).
 */
export const FOUND_THROUGH_TAGS: FoundIn = { from: 'SAME_VIBE' };

export interface SameVibePlayer {
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Their first photograph; absent draws their court poster. */
  readonly photoUrl?: string;
  /** **The vibe %** — the server's, one of 50, 75, 88, 94, 97, 98: the white circle, *98%*. */
  readonly vibePercent: number;
  /** **How many tags the two hold**, as the server counted them — *6 things in common*. */
  readonly inCommon: number;
  /**
   * **The tags they share**, in the vocabulary's own order — the tile's green chips, and the *· you
   * too* on the sheet. One this build cannot name is left off; `inCommon` still counts it.
   */
  readonly sharedTags: readonly SocialTagId[];
  /** Where the reader stands with them — the round friend button. */
  readonly relation: FriendRelation;
}

/**
 * The challenge row's own numbers, and the one piece of arithmetic they exist for.
 *
 * It is here rather than in `theme.ts` on `CANDIDATE_PANEL`'s precedent: the design system holds
 * drawn objects and control vocabulary, and a challenge row is a composition that names a domain
 * noun ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md)
 * §0). What the system does own is what the row *borrows* — 5.4's semantic bar, `CandidatePhoto`'s
 * 33 % corner, and the type roles.
 *
 * ## The conversation row holds the same three numbers, and they are spelled twice
 *
 * `conversations/components/conversationGeometry.ts` is the second copy of the face, the
 * overlap and the cluster, and this is the note that records it
 * ([#363](https://github.com/Raketa02/Raketa/issues/363)). **A third row is the signal to move
 * them**, which is `recoveryMessage.ts`'s own stated rule and the one
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §5 follows
 * when it names exactly one promotion for this whole map.
 *
 * **The three homes that were tried and are wrong are worth naming.** `theme.ts` is refused above.
 * The **shell**, which owns the tab and both its empty lines, cannot hold them: `shell/types.ts`
 * re-exports `TabShell`, which mounts `challenges`, so a row reading a number out of it at module
 * scope is a cycle that resolves to `undefined` at `StyleSheet.create` time — found by running the
 * suite, not by reading. And `shared/ui/` would say the design system owns a row's face, which
 * [#338](https://github.com/Raketa02/Raketa/issues/338) §5 refused in as many words when it
 * refused the avatar. What **did** move is the part that is genuinely about handles rather than
 * about this row: §15's list rule and the measured character budget are
 * `shared/formatting/handleList.ts`'s, beside `playerName()`.
 *
 * ## The handle line's budget
 *
 * §15 refuses to shorten a name, so a list of them gives way by dropping whole names — the
 * rule is `handleList.ts`'s, and what this module owes it is **how much room the words actually
 * have**. Everything to the left and right of that column is reserved at its **widest**: the
 * cluster at the number of faces the row will draw, the two gaps, and the urgency stripe — which
 * is reserved **even on the rows that do not draw one**, so that every row in the section holds
 * its handles to the same rule and the list does not measure itself differently per row.
 *
 * **It is a function of the device rather than a constant**, because a constant would have to be
 * the narrowest phone's and would then spend a 430pt screen's extra 110 points on nothing.
 */

import { charactersThatFit } from '@/shared/formatting/handleList';
import { theme } from '@/shared/ui';

/**
 * The row's face, at the weight #335 chose — **the challenge is a card, not a dense row.**
 *
 * 38, drawn and measured on `prototype/chats-tab`, which is that ticket's primary source: its
 * variant C gave the challenge card weight and the conversation row stayed a row, and the
 * resolution took *"variant B's conversation row, with C's weighting on the challenge card."*
 *
 * It is a **face**, so its corner is `CandidatePhoto`'s 33 % of its own box and this module
 * states no radius: #338 §5 refused the avatar outright, and the one owner of that share is the
 * component that draws the photograph-or-poster switch.
 */
export const ROW_FACE = 38;

/**
 * How far each face after the first is pulled back over the one before it.
 *
 * A share of the face rather than a gap in points, so the cluster keeps its proportions at any
 * face size. `prototype/chats-tab` drew it.
 */
export const FACE_OVERLAP = 0.38;

/** How wide the cluster of faces is, for however many the row draws. */
export function faceClusterWidth(faces: number): number {
  return faces <= 0 ? 0 : ROW_FACE * (1 + (faces - 1) * (1 - FACE_OVERLAP));
}

/** How many characters of handle the row's text column can hold, on this screen. */
export function handleBudget(screenWidth: number, faces: number): number {
  const column =
    screenWidth -
    2 * theme.size.gutter -
    2 * theme.space.md -
    faceClusterWidth(faces) -
    theme.space.md -
    theme.space.md -
    theme.size.semanticBar;

  return charactersThatFit(column);
}

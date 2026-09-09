/**
 * The conversation row's own numbers — **the same three the challenge row holds, and one
 * subtraction it does not.**
 *
 * `challenges/components/challengeRowGeometry.ts` is the first copy and carries the argument for
 * both: not `theme.ts`, because a Chats row is a composition that names a domain noun rather than
 * a drawn object the design system owns; not the **shell**, whose `types.ts` re-exports `TabShell`
 * and would make a row reading a number at module scope a cycle; and not `shared/ui/`, which would
 * say the design system owns a face after
 * [#338](https://github.com/Raketa02/Raketa/issues/338) §5 refused exactly that. **A third row is
 * the signal to move them** ([#363](https://github.com/Raketa02/Raketa/issues/363)).
 *
 * **One face size, because one is all that was drawn.**
 * [#335](https://github.com/Raketa02/Raketa/issues/335) resolved the tab as *"variant B's
 * conversation row, with C's weighting on the challenge card"*, and 38 is the number that
 * prototype published. The weighting that shipped is the challenge row's **stripe and its
 * obligation line**, not a second face size: no device in this repository has drawn a smaller one,
 * and #338 §1's rule for this map is a number only for what a device drew. Inventing one here
 * would be the guess that rule exists to refuse.
 *
 * **What genuinely differs is the trailing edge.** The challenge row reserves the urgency stripe
 * and the gap before it on every row in its section, so that a section holds all its handles to
 * one rule; this row draws nothing there and charges for nothing — which is the whole of the
 * difference between the two budgets, and the reason the arithmetic is spelled out rather than
 * parameterised across a feature boundary.
 */

import { charactersThatFit } from '@/shared/formatting/handleList';
import { theme } from '@/shared/ui';

/** The row's face. The challenge row's number, and the only one this tab has drawn. */
export const ROW_FACE = 38;

/** How far each face after the first is pulled back over the one before it. */
export const FACE_OVERLAP = 0.38;

/** How wide the cluster of faces is, for however many the row draws. */
export function faceClusterWidth(faces: number): number {
  return faces <= 0 ? 0 : ROW_FACE * (1 + (faces - 1) * (1 - FACE_OVERLAP));
}

/**
 * How many characters of handle the row's text column can hold, on this screen.
 *
 * The page gutters, the card's own padding, the cluster at the number of faces the row will draw,
 * and the gap between the cluster and the words. Nothing is kept for a trailing edge, because
 * nothing is drawn there.
 */
export function handleBudget(screenWidth: number, faces: number): number {
  const column =
    screenWidth -
    2 * theme.size.gutter -
    2 * theme.space.md -
    faceClusterWidth(faces) -
    theme.space.md;

  return charactersThatFit(column);
}

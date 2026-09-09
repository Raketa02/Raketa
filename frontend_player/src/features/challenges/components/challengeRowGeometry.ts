/**
 * The challenge row's own numbers, and the one piece of arithmetic they exist for.
 *
 * It is here rather than in `theme.ts` on `CANDIDATE_PANEL`'s precedent: the design system
 * holds drawn objects and control vocabulary, and a challenge row is a composition that names a
 * domain noun ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md)
 * §0). What the system does own is what the row *borrows* — 5.4's semantic bar, `CandidatePhoto`'s
 * 33 % corner, and the type roles.
 *
 * ## The handle line's budget, and why it is measured in characters
 *
 * §15 refuses to shorten a nickname, so a list of them gives way by dropping whole names — and
 * *which* names fit is a question about width, on a screen this module cannot measure. React
 * Native will happily tail-truncate a `Text`, and where it lands is inside a handle.
 *
 * So the budget is computed from the screen's own width and spent in **characters at the widest
 * character a handle may contain**, which in Archivo Bold is `@` at a shade over one em. That is
 * deliberately conservative: dropping a name that would have fitted keeps §15's rule and puts
 * the dropped name whole on the screen behind the row, where letting the ellipsis land inside a
 * handle breaks it outright.
 *
 * **It is a function of the device rather than a constant**, because a constant would have to be
 * the narrowest phone's and would then spend a 430pt screen's extra 110 points on nothing.
 * `challengeRowGeometry.test.ts` derives `WIDEST_HANDLE_EM` from the real face in the bundle, so
 * an Archivo release that redraws the letters goes red rather than truncating on somebody's
 * phone — the arrangement `tabBarLabelCap.test.ts` and `onCourtMarkFit.test.ts` already use.
 */

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

/**
 * The widest character a handle may contain, as a share of the type role's size.
 *
 * Archivo Bold's `@` is 1,0010 em and is the widest glyph in the repertoire a nickname can be
 * written in; this rounds up. Derived rather than chosen — see the module note and the test.
 */
export const WIDEST_HANDLE_EM = 1.01;

/** How wide the cluster of faces is, for however many the row draws. */
export function faceClusterWidth(faces: number): number {
  return faces <= 0 ? 0 : ROW_FACE * (1 + (faces - 1) * (1 - FACE_OVERLAP));
}

/**
 * How many characters of handle the row's text column can hold, on this screen.
 *
 * Everything to the left and right of that column is reserved at its **widest**: the cluster at
 * the number of faces the row will draw, the two gaps, and the urgency stripe — which is
 * reserved even on the rows that do not draw one, so that every row in the section holds its
 * handles to the same rule and the list does not measure itself differently per row.
 */
export function handleBudget(screenWidth: number, faces: number): number {
  const column =
    screenWidth -
    2 * theme.size.gutter -
    2 * theme.space.md -
    faceClusterWidth(faces) -
    theme.space.md -
    theme.space.md -
    theme.size.semanticBar;

  return Math.max(Math.floor(column / (theme.type.cardTitle.fontSize * WIDEST_HANDLE_EM)), 1);
}

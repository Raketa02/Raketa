/**
 * The conversation's own numbers — **the row's three, and the header's one subtraction more.**
 *
 * It was `conversationRowGeometry.ts` until the room behind the row was built. The rename is the
 * file following what is in it: the header draws the same faces and the same handle line against
 * different chrome, and two files holding one face size is how a person ends up two sizes on two
 * screens — which is the drift the number's own home is chosen to prevent.
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

import { charactersThatFit, WIDEST_HANDLE_EM } from '@/shared/formatting/handleList';
import { theme } from '@/shared/ui';

/**
 * The face, everywhere in this feature.
 *
 * The challenge row's number, and **the only one this tab has drawn** — the header takes it
 * unchanged rather than inventing a second. #338 §1's rule for this map is a number only for what
 * a device drew, and no device in this repository has drawn a smaller face; a header face picked
 * by eye would be one person at two sizes two taps apart.
 */
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

/**
 * How many characters of handle the **header's** words can hold, on this screen.
 *
 * The row's arithmetic against the header's chrome, which differs at both ends: there is a back
 * chevron on the left and, where there is a game, a `Details` control on the right — and the
 * control is charged for on **every** room rather than only the ones that draw it, so a header
 * does not reflow its handles when a line-up completes.
 *
 * The chevron is `h1` and its reachable area is the header's own; what is subtracted is the
 * `space.sm` gaps 10.3 sets between its parts, the cluster, and the two controls.
 *
 * **And the characters are counted at `h1`, because that is what the title is set in.** Until
 * [#401](https://github.com/Raketa02/Raketa/issues/401) they were counted at the rows' `cardTitle`,
 * six points smaller — nearly half again as many characters — so this budget said a line fitted
 * that did not. The header's title is not capped at one line, so what that drew was not a handle
 * cut in the middle but a **second line**: the whole point of dropping names to a budget is to
 * keep the header one line tall, and a count taken at the wrong size defeats it silently. The
 * stems that ticket draws are shorter inputs to the same rule, and the rule is only worth anything
 * if the count is honest.
 */
export function headerHandleBudget(screenWidth: number, faces: number): number {
  const column =
    screenWidth -
    2 * theme.size.gutter -
    theme.type.h1.fontSize -
    theme.space.sm -
    faceClusterWidth(faces) -
    theme.space.sm -
    DETAILS_WIDTH -
    theme.space.sm;

  return charactersThatFit(column, theme.type.h1);
}

/** `Details`, whose length is the only thing about the word this arithmetic reads. */
const DETAILS_LETTERS = 7;

/**
 * What the `Details` control takes, **reserved whether or not it is drawn.**
 *
 * A `sm` button holding one seven-character word at `type.btn`, with 6.1's own horizontal padding
 * either side. The character is `WIDEST_HANDLE_EM` — Archivo Bold's widest glyph — which is an
 * **upper bound** rather than a measurement of this particular word, and that is the right
 * direction for a budget: over-reserving drops a name that would have fitted, where
 * under-reserving draws a handle under the control.
 */
export const DETAILS_WIDTH =
  Math.ceil(DETAILS_LETTERS * theme.type.btn.fontSize * WIDEST_HANDLE_EM) + 2 * theme.space.md;

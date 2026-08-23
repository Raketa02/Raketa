/**
 * The one-line captions a shelf may carry, by code.
 *
 * A code and not a sentence, on `ADR-0070`'s rule; `ADR-0066` requires the
 * caption to be **composed by the server** and the client to **evaluate
 * nothing**, and both hold — the server decides whether a caption fires and
 * which one it is, and the phone draws the one it was handed.
 *
 * **A plain lookup rather than a function, deliberately.** The three copy tables
 * beside this one take a payload because they have one to read; a caption has
 * nothing to compute, and a parameter no row reads is the shape `ADR-0071`
 * refuses. It becomes a function on the day a caption names something.
 */

import type { AssertTrue, CaptionCode, IsClosedUnion } from './codes';

/**
 * Total over the one code v1 composes.
 *
 * It fires only when a term the ranking **actually reads** is undeclared —
 * hours, price, radius-and-anchor, competitive or social. A player who declined
 * all four sees nothing on Now, forever, at whatever percentage: *"Your profile
 * is 40 % complete"* never appears on this screen.
 */
export const CAPTION_COPY: Readonly<Record<CaptionCode, string>> = {
  undeclaredPreferences:
    'Ordered on what we know — some of your preferences for this sport are not set.',
};

/** Fails to compile if `CaptionCode` ever arrives as a bare string. */
export type CaptionCodeIsClosed = AssertTrue<IsClosedUnion<CaptionCode>>;

/** The caption, or `undefined` for a code this build has never heard of. */
export function captionCopy(code: string): string | undefined {
  return (CAPTION_COPY as Readonly<Record<string, string | undefined>>)[code];
}

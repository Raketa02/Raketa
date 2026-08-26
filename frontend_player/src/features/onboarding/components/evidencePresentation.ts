/**
 * How the evidence trail is drawn — and only that.
 *
 * The trail's words are the server's: every label, detail and sentence is authored there so
 * wording can be corrected without an App Store release, and every direction is computed by
 * the engine from that category's own evidence against the final estimate, so retuning a
 * constant moves the explanation with it. **This file decides nothing about the rating.** It
 * answers one question per row: how do I draw what I was sent?
 *
 * **A direction this build cannot read draws no mark at all**, rather than a default one.
 * A word this build cannot read is not grounds for drawing an arrow — the row still shows
 * what the category said, which is the part the client did not invent, and old app versions
 * live on real phones for months.
 *
 * The widener treatment that used to live here is gone with the list it drew — see
 * `EvidenceTrail`. The data is still mapped; nothing renders it.
 */

export interface DirectionMark {
  /** A shape, so the direction survives not being able to see colour. */
  readonly glyph: string;
  /** And a word, because a shape alone is not readable either. */
  readonly word: string;
  /** The same fact in a sentence, for the row's accessible name. */
  readonly spoken: string;
}

const MARKS: Readonly<Record<string, DirectionMark>> = {
  up: { glyph: '▲', word: 'Above', spoken: 'above your level' },
  down: { glyph: '▼', word: 'Below', spoken: 'below your level' },
  neutral: { glyph: '—', word: 'In line', spoken: 'in line with your level' },
};

/** `undefined` for a direction this build cannot read — the row draws without a mark. */
export function directionMark(direction: string): DirectionMark | undefined {
  return MARKS[direction];
}

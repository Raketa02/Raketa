/**
 * How the evidence trail is drawn and what the card calls itself — and only that.
 *
 * The trail's *rows* are the server's: every label is authored there so wording can be
 * corrected without an App Store release, and every direction is computed by the engine from
 * that category's own evidence against the final estimate, so retuning a constant moves the
 * explanation with it. **This file decides nothing about the rating.** It answers two
 * questions: how do I draw what I was sent, and what does the card say about itself?
 *
 * ## The heading and its lede are the app's own, and they are the fix
 *
 * The card used to be headed *what moved your level* over four figures, and that heading is
 * the reason the card read as broken. It promised an account that adds up, the four numbers
 * do not add up to anything — they are not weighted, and no operation on them produces the
 * Level — so a player who tried to reconcile them was doing arithmetic the card had invited
 * and the engine never performed. The wire carries no weights, and none may be invented here.
 *
 * What the figures genuinely are is *what each part of the game said when read on its own*,
 * and the heading now says exactly that. The lede names the comparison the drawing makes, so
 * the mark on each scale is a thing a player has been told about rather than a coral line
 * they have to interpret. **It quotes the Level rather than restating any rule about it**:
 * the number is the server's, formatted once by the caller.
 *
 * **A direction this build cannot read draws no mark at all**, rather than a default one. A
 * word this build cannot read is not grounds for drawing an arrow — the row still shows what
 * the category said and where it sits, which is the part the client did not invent, and old
 * app versions live on real phones for months.
 *
 * The widener treatment that used to live here is gone with the list it drew — see
 * `EvidenceTrail`. The data is still mapped; nothing renders it.
 */

/**
 * What the card is called.
 *
 * It names the reading rather than the arithmetic. *What moved your level* was a claim about
 * causation the response cannot support; this is a claim about what the rows are, which it
 * can.
 */
export const TRAIL_HEADING = 'How each part of your game reads';

/**
 * The sentence under the heading: each row is read alone, and the Level is the mark.
 *
 * Two facts and no more. **That the rows are independent** is what stops a player looking for
 * an average, and **that the mark is their Level** is what makes the drawing legible — a
 * coral line nobody named is decoration, and this is the same mark the level bar above the
 * card already carries under a legend.
 */
export function trailLede(level: string): string {
  return `Each one read on its own. Your level, ${level}, is the mark on every scale.`;
}

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

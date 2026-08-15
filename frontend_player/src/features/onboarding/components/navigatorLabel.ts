/**
 * What the question navigator says to a screen reader.
 *
 * **Position and count, and never a total.** The navigator is a row of rectangles, which
 * is not readable at any font size, so this is the whole of it in words — and it must not
 * quietly restore the denominator the drawing refuses to claim. The engine decides it has
 * heard enough only after an answer arrives; "question 5 of 9" would be a promise nobody
 * in the system is in a position to make.
 *
 * Whether the question being shown is one already answered is part of the position: a
 * player who walked back two questions is somewhere different from a player being asked
 * one, and the only sighted difference is a segment's fill.
 */

export function navigatorLabel(at: number, answered: number): string {
  const here = at <= answered ? `Question ${at}, already answered` : `Question ${at}`;
  if (answered === 0) return `${here}. No answers given yet.`;

  const behind = answered === 1 ? '1 answer given so far' : `${answered} answers given so far`;
  return `${here}. ${behind}.`;
}

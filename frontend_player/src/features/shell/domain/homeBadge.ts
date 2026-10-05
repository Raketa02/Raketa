/**
 * **Home's badge — the games that need you, from both loops** ([#556](https://github.com/Raketa02/Raketa/issues/556);
 * the Games & Fill in screens A1).
 *
 * Two halves, each its own feature's answer: the Classic games that need you (`plans`, which already
 * leaves out every Game a booking stands for) and the booked ones (`proposals`: the server's
 * `needing_you`, a result, a score to agree, a seat open, a payment to confirm). The bar draws their
 * sum, and nothing at all when it is nought — each half already answers `undefined` for *nothing to
 * draw*, and so does the whole.
 */
export function homeBadge(classic: number | undefined, booked: number): number | undefined {
  const sum = (classic ?? 0) + booked;
  return sum === 0 ? undefined : sum;
}

/**
 * **The column has to add up on screen**, and this is the arithmetic that makes it.
 *
 * *"A breakdown that does not add up is the claim failing"* is the contract's own sentence,
 * and two things break it in rendering
 * ([#233](https://github.com/Raketa02/Raketa/issues/233) §3). Neither is a rounding
 * preference; both are the sheet's whole promise.
 *
 * ## Rounding — largest-remainder apportionment, against the printed sub-total
 *
 * Contributions are floats. Seven rows rounded independently need not sum to the rounded
 * total: `17,4 + 17,4 + 17,4` prints `17 + 17 + 17 = 51` under a printed total of `52`. So the
 * rows are **apportioned** — every row takes its floor, and the points left over go to the
 * rows with the largest fractional parts, one each, in the order they arrived. The printed
 * column then sums to the printed sub-total exactly, for every input, which is the property
 * this file exists to hold.
 *
 * Ties go to the row the engine ranked higher, because `terms[]` arrives *ranked by
 * contribution* and nothing on this side sorts — so a tie broken by position is a tie broken
 * by the arithmetic that produced it rather than by a comparator somebody chose.
 *
 * ## The modifiers — `applied` is derived, and the list is never summed
 *
 * The printed `fit` is **not** what the terms sum to: `fit = Σcontributions + applied`, and
 * `applied` is not on the wire. `record_rows.py` forbids re-adding the modifier rows in
 * writing — *"the budget was applied by the type that produced it, and `ModifierStack.applied`
 * is the only total anybody may read"* — because the rows carry **pre-budget** entry points
 * and `MODIFIER_BUDGET` clamps their sum. So the figure is derived by **subtraction from two
 * published numbers**, which is not a rule re-encoded client-side; re-summing the rows would
 * be a wrong number that looks like a plausible one.
 *
 * It is derived against the **printed** sub-total rather than the raw sum, so that the step
 * from the terms to the number in the pill is exactly what the screen shows. Fit is served as
 * *"the printed number, out of a hundred"* and the pill draws it as served; rounding it here
 * is what keeps the three figures one arithmetic rather than three roundings.
 */

import type { ScoredTerm } from './evidence';

/** One row of the sheet, with the two figures it prints already resolved. */
export interface WhyFitRow {
  readonly term: ScoredTerm;
  /** The renormalised share of a hundred, as a whole number — §3's *weight rounds*. */
  readonly weight: number;
  /** This row's contribution **as printed**, apportioned so the column sums exactly. */
  readonly contribution: number;
}

export interface WhyFitColumn {
  /** In the order they arrived: ranked by contribution, and nothing here sorts. */
  readonly rows: readonly WhyFitRow[];
  /** What the rows sum to, printed once beneath them. */
  readonly subtotal: number;
  /**
   * `fit − Σcontributions`, and the block's heading figure. Signed: an adjustment may be
   * negative, and the sign is part of the number rather than of the sentence.
   */
  readonly applied: number;
  /** The number in the pill, as the rest of this arithmetic is written against it. */
  readonly fit: number;
}

export function whyFitColumn(candidate: {
  readonly fit: number;
  readonly terms: readonly ScoredTerm[];
}): WhyFitColumn {
  const raw = candidate.terms.map((term) => term.contribution);
  const subtotal = Math.round(raw.reduce((total, one) => total + one, 0));
  const apportioned = apportion(raw, subtotal);
  const fit = Math.round(candidate.fit);

  return {
    rows: candidate.terms.map((term, at) => ({
      term,
      weight: Math.round(term.weight),
      // `?? 0` cannot fire — the arrays are the same length by construction — and it is here
      // because `noUncheckedIndexedAccess` is on and a cast would be a worse answer.
      contribution: apportioned[at] ?? 0,
    })),
    subtotal,
    applied: fit - subtotal,
    fit,
  };
}

/**
 * Whole numbers summing **exactly** to `total`, closest to the shares given.
 *
 * The Hare quota's remainder step, and the reason it is a function rather than three lines at
 * the call site: the property it holds is *the printed column sums to the printed total*, and
 * that is a statement about every input rather than about the one on screen.
 */
function apportion(shares: readonly number[], total: number): readonly number[] {
  const floors = shares.map(Math.floor);
  const spent = floors.reduce((sum, one) => sum + one, 0);
  // Never negative: the floors sum to no more than the shares, and the total is their sum
  // rounded — so at worst it is half a point short of a figure already rounded down.
  const left = Math.max(total - spent, 0);

  const order = shares
    .map((share, at) => ({ at, fraction: share - Math.floor(share) }))
    // Largest fraction first; a tie keeps the engine's own ranking, which is `at`.
    .sort((one, other) => other.fraction - one.fraction || one.at - other.at)
    .slice(0, left);

  const raised = new Set(order.map((one) => one.at));
  return floors.map((floor, at) => (raised.has(at) ? floor + 1 : floor));
}

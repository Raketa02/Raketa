/**
 * One property, asserted rather than sampled: **the printed column sums to the printed
 * sub-total**, and the sub-total plus the printed adjustment is the number in the pill.
 *
 * That is the sheet's whole claim — *"a breakdown that does not add up is the claim failing"* —
 * and it is the kind of claim that is true of the fixture somebody wrote and false of the
 * candidate that ships. So the arithmetic is driven over generated inputs as well as over the
 * case that motivated it.
 */

import type { Evidence, ScoredTerm } from './evidence';
import type { Term } from './vocabulary';

import { whyFitColumn } from './whyFitColumn';

const EVIDENCE: Evidence = { kind: 'reliability', score: 82, floorBreached: false };

function term(contribution: number, weight = 10): ScoredTerm {
  return { term: 'RELIABILITY' as Term, weight, value: 0.8, contribution, evidence: EVIDENCE };
}

const sum = (numbers: readonly number[]) => numbers.reduce((total, one) => total + one, 0);

describe('the column adds up', () => {
  it('apportions the rounding rather than rounding each row on its own', () => {
    // 17,4 three times is 52,2 — a sub-total of 52 over three rows that each round to 17.
    const column = whyFitColumn({ fit: 52, terms: [term(17.4), term(17.4), term(17.4)] });

    expect(column.subtotal).toBe(52);
    expect(sum(column.rows.map((row) => row.contribution))).toBe(52);
  });

  it('gives the spare point to the largest fraction, and ties to the higher-ranked row', () => {
    const column = whyFitColumn({ fit: 40, terms: [term(20.5), term(19.2)] });

    // 39,7 → 40. The floors are 20 and 19; the point goes to ,5 rather than to ,2.
    expect(column.rows.map((row) => row.contribution)).toEqual([21, 19]);
  });

  it('holds for every shape of input', () => {
    for (let seed = 1; seed <= 200; seed += 1) {
      const contributions = Array.from(
        { length: (seed % 7) + 1 },
        (_, at) => ((seed * 37 + at * 13) % 400) / 10,
      );
      const column = whyFitColumn({ fit: 78, terms: contributions.map((one) => term(one)) });

      expect(sum(column.rows.map((row) => row.contribution))).toBe(column.subtotal);
      expect(column.subtotal + column.applied).toBe(column.fit);
    }
  });

  it('draws no rows and no sub-total when nothing fired', () => {
    const column = whyFitColumn({ fit: 0, terms: [] });

    expect(column.rows).toEqual([]);
    expect(column.subtotal).toBe(0);
  });
});

describe('the step to the pill', () => {
  /**
   * `applied` is `fit − Σcontributions`, and it is derived rather than re-summed: the modifier
   * rows carry pre-budget entry points and their sum is clamped, so adding them up would be a
   * wrong number that looks like a plausible one (`record_rows.py`).
   */
  it('is the whole difference between the sub-total and the printed Fit', () => {
    const column = whyFitColumn({ fit: 78, terms: [term(40), term(32)] });

    expect(column.subtotal).toBe(72);
    expect(column.applied).toBe(6);
  });

  it('is signed, because an adjustment may take points away', () => {
    const column = whyFitColumn({ fit: 70, terms: [term(40), term(35)] });

    expect(column.applied).toBe(-5);
  });

  it('is nought where the engine adjusted nothing — the block has nothing to head', () => {
    const column = whyFitColumn({ fit: 75, terms: [term(40), term(35)] });

    expect(column.applied).toBe(0);
  });
});

describe('the weight', () => {
  it('is the renormalised share as a whole number', () => {
    const column = whyFitColumn({ fit: 78, terms: [term(40, 26.4), term(32, 17.6)] });

    expect(column.rows.map((row) => row.weight)).toEqual([26, 18]);
  });
});

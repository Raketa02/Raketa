/**
 * The four adjustments.
 *
 * All four print — *"a modifier that could move a score without owing a sentence would be
 * Liveness wearing stage 4's clothes"* — and none of them prints a figure: the block's total
 * is derived once, above the rows, and never re-added from them.
 */

import { MODIFIER_CODES } from '../domain/vocabulary';

import {
  MODIFIERS_HEADING,
  TERM_SUBTOTAL_LABEL,
  adjustmentsTotal,
  modifierLine,
} from './modifierPresentation';

describe('every modifier owes a sentence', () => {
  it('gives all four their own words', () => {
    const lines = MODIFIER_CODES.map(modifierLine);

    expect(lines.every((line) => line.length > 0)).toBe(true);
    expect(new Set(lines).size).toBe(MODIFIER_CODES.length);
  });

  it('states the floor breach here and nowhere else', () => {
    // The reliability reason line prints the score and never the breach: one dock printed
    // twice reads as two.
    expect(modifierLine('RELIABILITY_FLOOR_BREACH')).toBe('Their record sits under the bar');
  });

  it('prints no figure on a row', () => {
    // `record_rows.py` forbids summing the list, so no row may look like a term in a column.
    for (const line of MODIFIER_CODES.map(modifierLine)) expect(line).not.toMatch(/\d/);
  });
});

describe('the block around them', () => {
  it('heads the eight terms and the adjustments separately', () => {
    expect(TERM_SUBTOTAL_LABEL).toBe('The eight terms');
    expect(MODIFIERS_HEADING).toBe('Then the engine adjusted it');
  });

  it('states the derived figure as one it was given', () => {
    expect(adjustmentsTotal('+4')).toBe('+4 from adjustments');
  });
});

/**
 * **The tile's chips, fitted to three lines** (#803; the Home rows screens §6.2; the README's override
 * 8) — as many whole chips as fit, the last place a *+N more* when more remain, from widths measured
 * on the screen.
 */

import { linesTaken, tagsThatFit } from './tagFit';

/** A 100-wide line, 6 between chips — the tile's own gap. */
const LINE = { lineWidth: 100, gap: 6, lines: 3 } as const;
/** *+1 more* … *+5 more*, each a little wider than the last digit's room needs. */
const MORE = [30, 30, 30, 30, 30];

describe('linesTaken — chips laid left to right, wrapping when the next one does not fit', () => {
  it('puts chips side by side while they fit, gaps between them', () => {
    expect(linesTaken([47, 47], 100, 6)).toBe(1);
    // 47 + 6 + 48 = 101: the second wraps.
    expect(linesTaken([47, 48], 100, 6)).toBe(2);
  });

  it('takes no line for no chip, and a line of its own for one wider than the line', () => {
    expect(linesTaken([], 100, 6)).toBe(0);
    expect(linesTaken([20, 140, 20], 100, 6)).toBe(3);
  });
});

describe('tagsThatFit', () => {
  it('draws every chip when all of them fit in three lines', () => {
    expect(tagsThatFit({ ...LINE, widths: [60, 60, 60], moreWidths: MORE })).toBe(3);
    expect(tagsThatFit({ ...LINE, widths: [40, 40, 40, 40, 40, 40], moreWidths: MORE })).toBe(6);
  });

  it('counts the rest with +N more beside the last chip that leaves it room', () => {
    // One chip to a line, so the fourth has no line: +1 more stands beside the third (60 + 6 + 30).
    expect(tagsThatFit({ ...LINE, widths: [60, 60, 60, 60], moreWidths: MORE })).toBe(3);
    // A wider third leaves +1 more no room (70 + 6 + 30 = 106), so it gives way: +2 more beside the
    // second.
    expect(tagsThatFit({ ...LINE, widths: [60, 60, 70, 60], moreWidths: MORE })).toBe(2);
  });

  it('keeps a chip on the third line beside +N more where both fit', () => {
    // Two to a line: 40 · 40 | 40 · 40 | 40 · +2 more (40 + 6 + 30 = 76).
    expect(tagsThatFit({ ...LINE, widths: [40, 40, 40, 40, 40, 40, 40], moreWidths: MORE })).toBe(
      5,
    );
  });

  it('reads the width of +N more for the count it says', () => {
    // +1 more at 30 fits beside the fifth chip (55 + 6 + 30); at 60 it does not, so the fifth gives
    // way to +2 more on the third line alone.
    const widths = [40, 40, 40, 40, 55, 40];
    expect(tagsThatFit({ ...LINE, widths, moreWidths: [30, 30, 30, 30, 30] })).toBe(5);
    expect(tagsThatFit({ ...LINE, widths, moreWidths: [60, 30, 30, 30, 30] })).toBe(4);
  });

  it('never draws +N more for nothing: a last chip that fits beats the count of it', () => {
    expect(tagsThatFit({ ...LINE, widths: [95, 95, 95], moreWidths: MORE })).toBe(3);
  });

  it('draws only +N more when not one chip fits beside it', () => {
    expect(tagsThatFit({ ...LINE, lines: 1, widths: [80, 80], moreWidths: MORE })).toBe(0);
  });

  it('draws nothing for no chips', () => {
    expect(tagsThatFit({ ...LINE, widths: [], moreWidths: [] })).toBe(0);
  });
});

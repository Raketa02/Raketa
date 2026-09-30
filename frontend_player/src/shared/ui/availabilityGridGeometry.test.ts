/**
 * Where a finger is on the week grid, and which hours a drag crossed to get there.
 *
 * The worked field below is the grid's own shape at an easy scale: seven columns of 30pt and
 * sixteen rows of 20pt, 4pt apart — 234 × 380. Every expected cell is counted off that drawing
 * by hand, never recomputed the way the module computes it.
 */

import { cellUnder, cellsCrossed, type CellField } from './availabilityGridGeometry';

const FIELD: CellField = { width: 234, height: 380, rows: 16, columns: 7, gap: 4 };

describe('the cell under a finger', () => {
  it('is the cell the point is inside', () => {
    expect(cellUnder({ x: 0, y: 0 }, FIELD)).toEqual({ row: 0, column: 0 });
    // The second column starts at 34 and the second row at 24.
    expect(cellUnder({ x: 39, y: 29 }, FIELD)).toEqual({ row: 1, column: 1 });
    expect(cellUnder({ x: 233, y: 379 }, FIELD)).toEqual({ row: 15, column: 6 });
  });

  it('is the cell before a gap, so no point between two cells presses nothing', () => {
    // 30 to 34 is the gap after the first column; 20 to 24 the gap under the first row.
    expect(cellUnder({ x: 32, y: 22 }, FIELD)).toEqual({ row: 0, column: 0 });
  });

  it('is the nearest edge cell for a finger that has left the grid', () => {
    // A drag that runs off the bottom still means the last hour, as a slider dragged past its
    // end still means the end of it.
    expect(cellUnder({ x: -10, y: 500 }, FIELD)).toEqual({ row: 15, column: 0 });
    expect(cellUnder({ x: 1000, y: -5 }, FIELD)).toEqual({ row: 0, column: 6 });
  });

  it('is no cell at all before the grid has been laid out', () => {
    expect(cellUnder({ x: 10, y: 10 }, { ...FIELD, width: 0, height: 0 })).toBeUndefined();
  });
});

describe('the cells a drag crossed', () => {
  it('is nothing while the finger stays on one cell', () => {
    expect(cellsCrossed({ row: 4, column: 2 }, { row: 4, column: 2 })).toEqual([]);
  });

  it('is every hour down a column, the one it arrived on included, the one it left not', () => {
    // A finger moving fast is sampled far apart — 18:00 to 21:00 in one step — and the two
    // hours in between were still crossed.
    expect(cellsCrossed({ row: 11, column: 1 }, { row: 14, column: 1 })).toEqual([
      { row: 12, column: 1 },
      { row: 13, column: 1 },
      { row: 14, column: 1 },
    ]);
  });

  it('runs back up a column as well as down it', () => {
    expect(cellsCrossed({ row: 3, column: 5 }, { row: 1, column: 5 })).toEqual([
      { row: 2, column: 5 },
      { row: 1, column: 5 },
    ]);
  });

  it('is every day along an hour', () => {
    expect(cellsCrossed({ row: 12, column: 0 }, { row: 12, column: 3 })).toEqual([
      { row: 12, column: 1 },
      { row: 12, column: 2 },
      { row: 12, column: 3 },
    ]);
  });

  it('steps one cell at a time along a slanting drag, never jumping one', () => {
    expect(cellsCrossed({ row: 0, column: 0 }, { row: 2, column: 4 })).toEqual([
      { row: 1, column: 1 },
      { row: 1, column: 2 },
      { row: 2, column: 3 },
      { row: 2, column: 4 },
    ]);
  });
});

/**
 * The week grid's paint arithmetic, per design-system 6.8 — two rules, and no React in either.
 *
 * Kept apart from the component for `swipeRowGeometry`'s reason: a rule about numbers is
 * testable as numbers, and a rule that only exists inside a gesture callback is one a test can
 * reach only by driving touches at a rendered tree. What the grid does is attach these to the
 * finger; what is decided is here.
 *
 * ## Which cell a finger is over
 *
 * The cells area is a field of equal cells with equal gaps, so a point's cell is a division —
 * against the field as laid out, never against the theme's numbers, which the phone's width and
 * Dynamic Type have already moved. **A gap belongs to the cell before it**, so no point between
 * two cells presses nothing, and **a finger that has left the field is over the nearest edge
 * cell**: a drag run off the bottom still means 22:00, as a slider dragged past its end still
 * means the end of it.
 *
 * ## Which cells a drag crossed
 *
 * A finger is sampled, not traced, and a fast one arrives three hours further down between two
 * samples. Every cell on the straight line between them was crossed and is painted, stepping
 * one cell at a time along the longer axis so no hour in a run is ever jumped.
 */

/** A cell by where it is drawn: its row (an hour) and its column (a day), both from 0. */
export interface GridPosition {
  readonly row: number;
  readonly column: number;
}

/** The cells area as laid out: its size, how many cells it holds each way, and the gap. */
export interface CellField {
  readonly width: number;
  readonly height: number;
  readonly rows: number;
  readonly columns: number;
  readonly gap: number;
}

/** A point in the cells area's own coordinates. */
export interface FieldPoint {
  readonly x: number;
  readonly y: number;
}

/**
 * The cell under `point` — see the module note. `undefined` before the field has been laid out:
 * a press then is a press on a grid that is not on screen yet.
 */
export function cellUnder(point: FieldPoint, field: CellField): GridPosition | undefined {
  if (field.width <= 0 || field.height <= 0) return undefined;
  return {
    row: along(point.y, field.height, field.rows, field.gap),
    column: along(point.x, field.width, field.columns, field.gap),
  };
}

/**
 * The index along one axis: `count` cells and `count - 1` gaps share `length`, so one cell and
 * the gap after it are `(length + gap) / count`.
 */
function along(at: number, length: number, count: number, gap: number): number {
  const pitch = (length + gap) / count;
  return Math.min(count - 1, Math.max(0, Math.floor(at / pitch)));
}

/**
 * The cells a drag crossed from `from` to `to` — `to` included, `from` not, since it was
 * painted when the finger was on it. Empty while the finger stays on one cell.
 */
export function cellsCrossed(from: GridPosition, to: GridPosition): readonly GridPosition[] {
  const rows = to.row - from.row;
  const columns = to.column - from.column;
  const steps = Math.max(Math.abs(rows), Math.abs(columns));
  return Array.from({ length: steps }, (_, index) => {
    const share = (index + 1) / steps;
    return {
      row: from.row + Math.round(rows * share),
      column: from.column + Math.round(columns * share),
    };
  });
}

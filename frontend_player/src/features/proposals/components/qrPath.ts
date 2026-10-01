/**
 * **A check-in payload as a QR code's drawing** — the matrix `qrcode` encodes, as one SVG path
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); the mechanics §15.1: *a QR code to show
 * at the club desk*).
 *
 * One path rather than a rectangle per module: a payload naming a booking and a player is a hundred
 * characters, version 5 or so — 37 modules a side, some seven hundred of them dark — and one element
 * draws them where seven hundred would each be a native view. Each **run** of dark modules in a row
 * is one closed rectangle of the path, so the shape is exact at any size the box scales it to.
 *
 * **Level M**: a phone screen is clean, but a desk's camera reads it through glare and a cracked
 * glass, and the fifteen per cent M restores is what the payload's size can afford.
 */

import { create } from 'qrcode/lib/core/qrcode';

/** What a drawing needs of the matrix: its side, and whether a module is dark. */
export interface QrMatrix {
  readonly size: number;
  readonly get: (row: number, col: number) => number;
}

/** The modules a side, and the dark ones as one path in module units. */
export interface QrDrawing {
  readonly size: number;
  readonly path: string;
}

/** Every run of dark modules, row by row, as closed rectangles of one path. */
export function darkRunsPath(matrix: QrMatrix): string {
  let path = '';
  for (let row = 0; row < matrix.size; row += 1) {
    let col = 0;
    while (col < matrix.size) {
      if (matrix.get(row, col) === 0) {
        col += 1;
        continue;
      }
      const start = col;
      while (col < matrix.size && matrix.get(row, col) !== 0) col += 1;
      const run = col - start;
      path += `M${start} ${row}h${run}v1h-${run}z`;
    }
  }
  return path;
}

export function qrDrawing(payload: string): QrDrawing {
  const { modules } = create(payload, { errorCorrectionLevel: 'M' });
  return { size: modules.size, path: darkRunsPath(modules) };
}

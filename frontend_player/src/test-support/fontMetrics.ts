/**
 * Just enough of a TrueType file to measure a word, for the tests that derive this app's
 * text caps.
 *
 * **In `test-support/` because it is not app code**, exactly as `contrast.ts` is: the app
 * draws words; it never measures them. A `theme.ts` that checked its own arithmetic would be
 * the app refusing to launch over a drawing detail, and a red build is where a human
 * reconciles it (`bandEdges.test.ts`).
 *
 * It moved here for `contrast.ts`'s own reason, one register over: *"there are now two tables
 * of derived ratios … two copies of a luminance formula drift the same way, and more quietly,
 * because the numbers still look like numbers."* There are now **two** derived caps — the tab
 * bar's `labelMaxScale` and the photo panel's `ON_COURT_MAX_SCALE` — and a second copy
 * of a `cmap` walk drifts in exactly that silence.
 *
 * The alternative to reading the face is a hard-coded *"about 0,6em per character"*, which is
 * the guess this file exists to replace: a cap picked by eye is a guess that fails on one
 * word, on one phone, at one OS setting, as an ellipsis nobody who built the surface will
 * ever see.
 *
 * `head` for the em square, `cmap` format 4 for character → glyph, `hmtx` for the advance.
 * Nothing here kerns: RN lays a label out with no kerning pairs applied at these sizes, and a
 * measurement that kerned would be smaller than the drawing rather than safer than it.
 */

import { readFileSync } from 'node:fs';

export interface Face {
  readonly unitsPerEm: number;
  /** Advance width of one character, in font units. Throws where the face has no glyph. */
  advance: (codePoint: number) => number;
  /** Whether the face draws this character at all — `advance`'s question without the throw. */
  draws: (codePoint: number) => boolean;
}

/**
 * A face out of `@expo-google-fonts`, by the family name a type role names.
 *
 * Resolved as a bare specifier so nothing here depends on how `.npmrc` happens to lay
 * `node_modules` out, and a role pointed at a weight the package does not ship fails on the
 * read — before a single number is computed.
 */
export function readFace(path: string): Face {
  const ttf = readFileSync(require.resolve(path));

  // Offset table: sfntVersion, then a directory of tag / checksum / offset / length.
  const tables = new Map<string, number>();
  const count = ttf.readUInt16BE(4);
  for (let i = 0; i < count; i++) {
    const record = 12 + i * 16;
    tables.set(ttf.toString('ascii', record, record + 4), ttf.readUInt32BE(record + 8));
  }
  const table = (tag: string): number => {
    const offset = tables.get(tag);
    if (offset === undefined) throw new Error(`${path} has no ${tag} table`);
    return offset;
  };

  const unitsPerEm = ttf.readUInt16BE(table('head') + 18);
  // `hmtx` stores one advance per glyph up to this many, then repeats the last for the
  // monospaced tail. Every glyph these tests measure is well inside the array.
  const metrics = ttf.readUInt16BE(table('hhea') + 34);
  const hmtx = table('hmtx');

  // cmap: take the Unicode BMP subtable, which is format 4 in every font this app loads.
  const cmap = table('cmap');
  let segments = 0;
  for (let i = 0; i < ttf.readUInt16BE(cmap + 2); i++) {
    const record = cmap + 4 + i * 8;
    const platform = ttf.readUInt16BE(record);
    const encoding = ttf.readUInt16BE(record + 2);
    const subtable = cmap + ttf.readUInt32BE(record + 4);
    const unicodeBmp = (platform === 3 && encoding === 1) || platform === 0;
    if (unicodeBmp && ttf.readUInt16BE(subtable) === 4) segments = subtable;
  }
  if (segments === 0) throw new Error(`${path} has no format 4 Unicode cmap`);

  const segX2 = ttf.readUInt16BE(segments + 6);
  const ends = segments + 14;
  const starts = ends + segX2 + 2;
  const deltas = starts + segX2;
  const ranges = deltas + segX2;

  const glyphOf = (codePoint: number): number => {
    for (let i = 0; i < segX2 / 2; i++) {
      if (codePoint > ttf.readUInt16BE(ends + i * 2)) continue;
      const start = ttf.readUInt16BE(starts + i * 2);
      if (codePoint < start) return 0;
      const delta = ttf.readInt16BE(deltas + i * 2);
      const rangeOffset = ttf.readUInt16BE(ranges + i * 2);
      if (rangeOffset === 0) return (codePoint + delta) & 0xffff;
      const glyph = ttf.readUInt16BE(ranges + i * 2 + rangeOffset + (codePoint - start) * 2);
      return glyph === 0 ? 0 : (glyph + delta) & 0xffff;
    }
    return 0;
  };

  return {
    unitsPerEm,
    advance: (codePoint) => {
      const glyph = glyphOf(codePoint);
      if (glyph === 0) throw new Error(`${path} does not draw U+${codePoint.toString(16)}`);
      return ttf.readUInt16BE(hmtx + Math.min(glyph, metrics - 1) * 4);
    },
    draws: (codePoint) => glyphOf(codePoint) !== 0,
  };
}

/** A word's width at a size, in points, plus whatever tracking the role adds per character. */
export function widthOf(face: Face, word: string, size: number, tracking = 0): number {
  const characters = [...word];
  const advances = characters.reduce((sum, c) => sum + face.advance(c.codePointAt(0)!), 0);
  return (advances / face.unitsPerEm) * size + characters.length * tracking;
}

/**
 * The largest 0,1 step of `maxFontSizeMultiplier` that still fits.
 *
 * RN takes the multiplier as given and nothing rounds it, so the step is this file's choice:
 * a cap quoted to three decimals is a number nobody can read against a design, and a tenth is
 * the granularity every OS text-size slider moves in anyway.
 */
export function largestStepThatFits(width: number, available: number): number {
  return Math.floor((available / width) * 10) / 10;
}

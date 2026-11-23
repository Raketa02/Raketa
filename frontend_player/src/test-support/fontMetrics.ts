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
 * **`widthOf` never kerns**: RN lays a label out with no kerning pairs applied at these sizes, and
 * a measurement that kerned would be smaller than the drawing rather than safer than it.
 *
 * **But the face can say how it kerns** (`kerning`, out of `GPOS`), and `hhea` says how tall its
 * line box is (`ascender`, `descender`), for the one drawing that sets its letters itself: the
 * splash's wordmark, whose seven letters are placed one by one from the font's own numbers, and
 * whose pin (`splashWordmark.test.ts`) reads those numbers back here.
 *
 * **The width every derived cap is computed at is here too**, on the same argument: it was
 * declared identically in four suites, each with its own comment saying it is not a token, and
 * four copies of a fact about the device population drift the same silent way two copies of a
 * luminance formula do.
 */

import { readFileSync } from 'node:fs';

/**
 * The narrowest phone the app supports, in points — iPhone SE / iPhone 8.
 *
 * Every cap this app derives is computed against it, because a cap that fits the widest phone
 * is not a cap. **Not a token**: it is a fact about the device population rather than a value
 * any component reads, and `theme.ts` holds only what components read.
 */
export const NARROWEST_SCREEN = 320;

export interface Face {
  readonly unitsPerEm: number;
  /** How far the line box reaches above the baseline, in font units (`hhea`). */
  readonly ascender: number;
  /** How far it reaches below, in font units — negative, as the font stores it (`hhea`). */
  readonly descender: number;
  /** The space a line adds under its box, in font units (`hhea`); iOS adds it to a line's height. */
  readonly lineGap: number;
  /**
   * The same three numbers as `OS/2` states them, which a platform reads instead of `hhea`'s when
   * the font sets `USE_TYPO_METRICS` (`useTypo`).
   */
  readonly typo: {
    readonly ascender: number;
    readonly descender: number;
    readonly lineGap: number;
    readonly useTypo: boolean;
  };
  /** Advance width of one character, in font units. Throws where the face has no glyph. */
  advance: (codePoint: number) => number;
  /** Whether the face draws this character at all — `advance`'s question without the throw. */
  draws: (codePoint: number) => boolean;
  /**
   * How much the face moves `right` when it follows `left`, in font units: the `kern` feature's
   * pair adjustments in `GPOS`, negative to tighten. 0 for a pair the face does not kern.
   */
  kerning: (left: number, right: number) => number;
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

  const drawnGlyph = (codePoint: number): number => {
    const glyph = glyphOf(codePoint);
    if (glyph === 0) throw new Error(`${path} does not draw U+${codePoint.toString(16)}`);
    return glyph;
  };

  return {
    unitsPerEm,
    ascender: ttf.readInt16BE(table('hhea') + 4),
    descender: ttf.readInt16BE(table('hhea') + 6),
    lineGap: ttf.readInt16BE(table('hhea') + 8),
    typo: {
      ascender: ttf.readInt16BE(table('OS/2') + 68),
      descender: ttf.readInt16BE(table('OS/2') + 70),
      lineGap: ttf.readInt16BE(table('OS/2') + 72),
      // fsSelection's bit 7.
      useTypo: (ttf.readUInt16BE(table('OS/2') + 62) & 0x80) !== 0,
    },
    advance: (codePoint) => {
      const glyph = drawnGlyph(codePoint);
      return ttf.readUInt16BE(hmtx + Math.min(glyph, metrics - 1) * 4);
    },
    draws: (codePoint) => glyphOf(codePoint) !== 0,
    kerning: (left, right) => pairKerning(ttf, table('GPOS'), drawnGlyph(left), drawnGlyph(right)),
  };
}

/**
 * The `kern` feature's adjustment of the pair `left` → `right`, read the way a shaper applies it:
 * each of the feature's lookups in turn, each lookup's subtables until one applies, and the
 * adjustments of the lookups that applied added up. A pair subtable applies when it covers the
 * left glyph and — in the per-glyph format — lists the right one; the per-class format applies to
 * any pair it covers, whatever its value, which is how a font says *not this pair* after a broader
 * subtable would have kerned it. Extension lookups are followed to the pair subtable they wrap.
 *
 * Only the first glyph's advance is read (`XAdvance` of the first value record): that is what
 * kerning moves.
 */
function pairKerning(ttf: Buffer, gpos: number, left: number, right: number): number {
  const u16 = (offset: number) => ttf.readUInt16BE(offset);

  const featureList = gpos + u16(gpos + 6);
  const lookupList = gpos + u16(gpos + 8);

  const kernLookups = new Set<number>();
  for (let i = 0; i < u16(featureList); i++) {
    const record = featureList + 2 + i * 6;
    if (ttf.toString('ascii', record, record + 4) !== 'kern') continue;
    const feature = featureList + u16(record + 4);
    for (let j = 0; j < u16(feature + 2); j++) kernLookups.add(u16(feature + 4 + j * 2));
  }

  let total = 0;
  for (const index of kernLookups) {
    const lookup = lookupList + u16(lookupList + 2 + index * 2);
    for (let s = 0; s < u16(lookup + 4); s++) {
      let subtable = lookup + u16(lookup + 6 + s * 2);
      let type = u16(lookup);
      if (type === 9) {
        type = u16(subtable + 2);
        subtable += ttf.readUInt32BE(subtable + 4);
      }
      if (type !== 2) continue;
      const adjustment = pairAdjustment(ttf, subtable, left, right);
      if (adjustment === null) continue;
      total += adjustment;
      break;
    }
  }
  return total;
}

/** One pair-positioning subtable's adjustment for the pair, or `null` where it does not apply. */
function pairAdjustment(ttf: Buffer, subtable: number, left: number, right: number): number | null {
  const u16 = (offset: number) => ttf.readUInt16BE(offset);

  const covered = coverageIndex(ttf, subtable + u16(subtable + 2), left);
  if (covered < 0) return null;

  const firstFormat = u16(subtable + 4);
  const secondFormat = u16(subtable + 6);
  const recordSize = 2 * (fieldsIn(firstFormat) + fieldsIn(secondFormat));
  // `XAdvance` follows `XPlacement` and `YPlacement` when the record carries them.
  const xAdvance = (record: number) =>
    (firstFormat & 0x4) === 0 ? 0 : ttf.readInt16BE(record + 2 * fieldsIn(firstFormat & 0x3));

  if (u16(subtable) === 1) {
    const set = subtable + u16(subtable + 10 + covered * 2);
    for (let i = 0; i < u16(set); i++) {
      const pair = set + 2 + i * (2 + recordSize);
      if (u16(pair) === right) return xAdvance(pair + 2);
    }
    return null;
  }

  const leftClass = classOf(ttf, subtable + u16(subtable + 8), left);
  const rightClass = classOf(ttf, subtable + u16(subtable + 10), right);
  const rightClasses = u16(subtable + 14);
  // A class past the table's own count is a subtable that does not apply, as a shaper reads it —
  // never an index into whatever bytes follow.
  if (leftClass >= u16(subtable + 12) || rightClass >= rightClasses) return null;
  return xAdvance(subtable + 16 + (leftClass * rightClasses + rightClass) * recordSize);
}

/** How many 16-bit fields a value record of this format carries. */
function fieldsIn(format: number): number {
  let fields = 0;
  for (let bits = format; bits !== 0; bits >>= 1) fields += bits & 1;
  return fields;
}

/** The glyph's index in a coverage table, or −1 where it is not covered. */
function coverageIndex(ttf: Buffer, coverage: number, glyph: number): number {
  const u16 = (offset: number) => ttf.readUInt16BE(offset);
  if (u16(coverage) === 1) {
    for (let i = 0; i < u16(coverage + 2); i++) {
      if (u16(coverage + 4 + i * 2) === glyph) return i;
    }
    return -1;
  }
  for (let i = 0; i < u16(coverage + 2); i++) {
    const range = coverage + 4 + i * 6;
    if (glyph >= u16(range) && glyph <= u16(range + 2)) return u16(range + 4) + glyph - u16(range);
  }
  return -1;
}

/** The glyph's class in a class definition table; 0, the class of everything unlisted, otherwise. */
function classOf(ttf: Buffer, definition: number, glyph: number): number {
  const u16 = (offset: number) => ttf.readUInt16BE(offset);
  if (u16(definition) === 1) {
    const first = u16(definition + 2);
    const count = u16(definition + 4);
    return glyph >= first && glyph < first + count ? u16(definition + 6 + (glyph - first) * 2) : 0;
  }
  for (let i = 0; i < u16(definition + 2); i++) {
    const range = definition + 4 + i * 6;
    if (glyph >= u16(range) && glyph <= u16(range + 2)) return u16(range + 4);
  }
  return 0;
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

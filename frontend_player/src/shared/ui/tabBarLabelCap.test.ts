/**
 * `theme.size.tabBar.labelMaxScale`, derived rather than chosen.
 *
 * The tab bar has exactly one Dynamic Type mechanism. Part 13 requires text to scale with the
 * OS setting, names the tab bar as the one place a **fixed height** is the design, and permits
 * `allowFontScaling={false}` only inside the level bar's drawn geometry — so the label may
 * neither be frozen nor grow without bound, and `maxFontSizeMultiplier` is what is left.
 *
 * The number it is set to is the whole question. Pick it by eye and it is a guess that fails
 * on one word, on one phone, at one OS setting, as an ellipsis nobody who built the bar will
 * ever see. So it is **measured**: this file reads the advance widths out of the Archivo Bold
 * that ships in the bundle, lays the five shipped labels out at `type.tag`'s size in the
 * narrowest phone's column, and computes the largest step that still fits. `theme.ts` carries
 * the answer and this file is where it comes from — the same arrangement `bandEdges.test.ts`
 * and `textOnMedia.test.ts` use, and for the same reason: a `theme.ts` that checked its own
 * arithmetic would be the app refusing to launch over a drawing detail, and a red build is
 * where a human reconciles it.
 *
 * **What makes it go red:** a sixth tab, a longer label, a different type role, a different
 * weight, a change to the grid step between the columns, or an Archivo release that redraws
 * the letters. Every one of those is a real change to the answer, and none of them announces
 * itself at 9,5pt.
 *
 * Font metrics are read straight from the `.ttf` — `head` for the em square, `cmap` format 4
 * for character → glyph, `hmtx` for the advance. Roughly sixty lines, and the alternative is
 * a hard-coded *"about 0,6em per character"*, which is the guess this file exists to replace.
 */

import { readFileSync } from 'node:fs';

import { TAB_BAR_TABS } from './TabBar';
import { theme } from './theme';

/**
 * The narrowest phone the app supports, in points — iPhone SE / iPhone 8, and the width
 * `profileControlGeometry.test.ts` decides the other three drawn controls at.
 *
 * Not a token: it is a fact about the device population, not a value any component reads.
 */
const NARROWEST_SCREEN = 320;

/**
 * The bar is equal columns edge to edge — no gutter, unlike every scrolling screen — so a
 * column is the screen divided by the number of tabs. 64pt on the narrowest phone.
 */
const COLUMN = NARROWEST_SCREEN / TAB_BAR_TABS.length;

/**
 * What is left of a column for the word.
 *
 * A label allowed the full 64 would touch its neighbour at the cap, so the smallest step on
 * the 3pt grid is held on each side. That is a design value, not a fudge factor: 6.5 bounds
 * horizontal slop by the neighbour for the same reason.
 */
const AVAILABLE = COLUMN - 2 * theme.space.xxs;

/**
 * The face the label is drawn in, by construction rather than by assertion — built from the
 * role's own `fontFamily`, and resolved as a bare specifier so nothing here depends on how
 * `.npmrc` happens to lay `node_modules` out. A role pointed at a face the package does not
 * ship fails on the read, before a single number is computed.
 */
const FONT_FILE = `@expo-google-fonts/archivo/${theme.type.tag.fontFamily}.ttf`;

// ---------------------------------------------------------------------------
// Just enough of a TrueType file to measure a word
// ---------------------------------------------------------------------------

interface Face {
  readonly unitsPerEm: number;
  /** Advance width of one character, in font units. */
  advance: (codePoint: number) => number;
}

function readFace(path: string): Face {
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
  // monospaced tail. Every glyph here is well inside the array.
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
  };
}

const archivoBold = readFace(FONT_FILE);

/** A word's width at a size, in points, plus whatever tracking the role adds per character. */
function widthOf(word: string, size: number, tracking = 0): number {
  const characters = [...word];
  const advances = characters.reduce((sum, c) => sum + archivoBold.advance(c.codePointAt(0)!), 0);
  return (advances / archivoBold.unitsPerEm) * size + characters.length * tracking;
}

/** The largest 0,1 step that still fits. RN takes the multiplier as given; nothing rounds it. */
function largestStepThatFits(width: number, available: number): number {
  return Math.floor((available / width) * 10) / 10;
}

const LONGEST = TAB_BAR_TABS.map((t) => t.label).reduce((a, b) =>
  widthOf(b, theme.type.tag.fontSize) > widthOf(a, theme.type.tag.fontSize) ? b : a,
);

// ---------------------------------------------------------------------------

describe('the face being measured', () => {
  it('is a weight the app actually loads', () => {
    // The read above proves the file exists in the package. This proves the app puts it on
    // the device: a role pointed at an Archivo weight `bootstrap/fonts.ts` does not register
    // renders in the system font, and the measurement would then be of a face nothing draws.
    expect(Object.values(theme.font.sans)).toContain(theme.type.tag.fontFamily);
  });

  it('reads a 1000-unit em and draws every character the five labels use', () => {
    expect(archivoBold.unitsPerEm).toBe(1000);
    for (const { label } of TAB_BAR_TABS) {
      for (const character of label) {
        expect(archivoBold.advance(character.codePointAt(0)!)).toBeGreaterThan(0);
      }
    }
  });
});

describe('the column the label has to fit', () => {
  it('is the screen divided five ways, with no gutter', () => {
    expect(COLUMN).toBe(64);
    expect(AVAILABLE).toBe(58);
  });
});

describe('the cap', () => {
  it('is derived from the longest shipped label', () => {
    expect(LONGEST).toBe('Around');
    expect(theme.size.tabBar.labelMaxScale).toBe(
      largestStepThatFits(widthOf(LONGEST, theme.type.tag.fontSize), AVAILABLE),
    );
  });

  it('keeps every one of the five inside its column at the cap', () => {
    for (const { label } of TAB_BAR_TABS) {
      const scaled = widthOf(label, theme.type.tag.fontSize) * theme.size.tabBar.labelMaxScale;
      expect(scaled).toBeLessThanOrEqual(AVAILABLE);
    }
  });

  it('is the largest step that does: one more overflows the column', () => {
    const overflowing =
      widthOf(LONGEST, theme.type.tag.fontSize) * (theme.size.tabBar.labelMaxScale + 0.1);
    expect(overflowing).toBeGreaterThan(AVAILABLE);
  });

  it('is a scale and not a licence — the bar is still bounded', () => {
    // `allowFontScaling={false}` is what this replaces, so the cap must actually be a cap.
    expect(theme.size.tabBar.labelMaxScale).toBeGreaterThan(1);
  });
});

describe('why the label is `tag` and not `eyebrow`', () => {
  it('costs the column nothing in tracking', () => {
    expect(theme.type.tag).not.toHaveProperty('letterSpacing');
  });

  it('would lose 8,6pt of a 64pt column to eyebrow tracking, and cap lower for it', () => {
    // The other member of the 9.5 pair, drawn the way an eyebrow is drawn: uppercase, tracked.
    const tracking = theme.type.eyebrow.letterSpacing;
    const eyebrowWidth = widthOf(LONGEST.toUpperCase(), theme.type.eyebrow.fontSize, tracking);
    const flat = widthOf(LONGEST.toUpperCase(), theme.type.eyebrow.fontSize);

    expect(eyebrowWidth - flat).toBeCloseTo(8.6, 1);
    expect(largestStepThatFits(eyebrowWidth, AVAILABLE)).toBeLessThan(
      theme.size.tabBar.labelMaxScale,
    );
  });
});

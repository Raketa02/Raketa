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
 * Font metrics are read straight from the `.ttf`, by `test-support/fontMetrics.ts` — the
 * alternative is a hard-coded *"about 0,6em per character"*, which is the guess that file
 * exists to replace. It moved there when the photo panel's ON COURT mark needed the same
 * measurement ([#313](https://github.com/Raketa02/Raketa/issues/313)): two derived caps and
 * one `cmap` walk, on `contrast.ts`'s argument for the luminance formula.
 */

import {
  NARROWEST_SCREEN,
  largestStepThatFits,
  readFace,
  widthOf,
} from '@/test-support/fontMetrics';

import { TAB_BAR_TABS } from './TabBar';
import { theme } from './theme';

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

const archivoBold = readFace(FONT_FILE);

/** This file's five labels, at this file's face — the two the shared helper takes every time. */
const width = (word: string, size: number, tracking = 0): number =>
  widthOf(archivoBold, word, size, tracking);

const LONGEST = TAB_BAR_TABS.map((t) => t.label).reduce((a, b) =>
  width(b, theme.type.tag.fontSize) > width(a, theme.type.tag.fontSize) ? b : a,
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
      largestStepThatFits(width(LONGEST, theme.type.tag.fontSize), AVAILABLE),
    );
  });

  it('keeps every one of the five inside its column at the cap', () => {
    for (const { label } of TAB_BAR_TABS) {
      const scaled = width(label, theme.type.tag.fontSize) * theme.size.tabBar.labelMaxScale;
      expect(scaled).toBeLessThanOrEqual(AVAILABLE);
    }
  });

  it('is the largest step that does: one more overflows the column', () => {
    const overflowing =
      width(LONGEST, theme.type.tag.fontSize) * (theme.size.tabBar.labelMaxScale + 0.1);
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
    const eyebrowWidth = width(LONGEST.toUpperCase(), theme.type.eyebrow.fontSize, tracking);
    const flat = width(LONGEST.toUpperCase(), theme.type.eyebrow.fontSize);

    expect(eyebrowWidth - flat).toBeCloseTo(8.6, 1);
    expect(largestStepThatFits(eyebrowWidth, AVAILABLE)).toBeLessThan(
      theme.size.tabBar.labelMaxScale,
    );
  });
});

/**
 * `theme.size.tabBar.labelMaxScale`, held against the words it caps.
 *
 * The tab bar has exactly one Dynamic Type mechanism. Part 13 requires text to scale with the
 * OS setting, names the tab bar as the one place a **fixed height** is the design, and permits
 * `allowFontScaling={false}` only inside the level bar's drawn geometry — so the label may
 * neither be frozen nor grow without bound, and `maxFontSizeMultiplier` is what is left.
 *
 * **1,6 was derived over five columns** — the largest step at which *Players*, the longest of
 * five labels, still fit a 64pt column on the narrowest phone. The bar is three columns since
 * the old loop's Players and Chats left it ([#576](https://github.com/Raketa02/Raketa/issues/576)),
 * and the five-column fit went with them: at a third of the screen every word fits at more than
 * twice the cap, so the column's width no longer decides the number. **The cap stays where the
 * five left it** — the bar's height is what the cap bounds now, and `TabBar.test.tsx` holds that —
 * and this file holds the three words inside their columns at it, measured, so a fourth tab or a
 * longer word goes red here rather than truncating on somebody's phone.
 *
 * **What makes it go red:** a fourth tab, a longer label, a different type role, a different
 * weight, a change to the grid step between the columns, or an Archivo release that redraws
 * the letters. None of them announces itself at 9,5pt.
 *
 * Font metrics are read straight from the `.ttf`, by `test-support/fontMetrics.ts` — the
 * alternative is a hard-coded *"about 0,6em per character"*, which is the guess that file
 * exists to replace.
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
 * column is the screen divided by the number of tabs. A third of 320pt on the narrowest phone.
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

/** This file's three labels, at this file's face — the two the shared helper takes every time. */
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

  it('reads a 1000-unit em and draws every character the three labels use', () => {
    expect(archivoBold.unitsPerEm).toBe(1000);
    for (const { label } of TAB_BAR_TABS) {
      for (const character of label) {
        expect(archivoBold.advance(character.codePointAt(0)!)).toBeGreaterThan(0);
      }
    }
  });
});

describe('the column the label has to fit', () => {
  it('is the screen divided three ways, with no gutter', () => {
    expect(TAB_BAR_TABS).toHaveLength(3);
    expect(COLUMN).toBeCloseTo(106.67, 2);
  });
});

describe('the cap', () => {
  it('keeps every one of the three inside its column at the cap', () => {
    for (const { label } of TAB_BAR_TABS) {
      const scaled = width(label, theme.type.tag.fontSize) * theme.size.tabBar.labelMaxScale;
      expect(scaled).toBeLessThanOrEqual(AVAILABLE);
    }
  });

  it('is no longer the width’s answer: the longest word fits at more than twice it', () => {
    expect(LONGEST).toBe('Home');
    expect(largestStepThatFits(width(LONGEST, theme.type.tag.fontSize), AVAILABLE)).toBeGreaterThan(
      2 * theme.size.tabBar.labelMaxScale,
    );
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

  it('would spend 1,43pt a letter on air under eyebrow tracking', () => {
    // The other member of the 9.5 pair, drawn the way an eyebrow is drawn: uppercase, tracked.
    const tracking = theme.type.eyebrow.letterSpacing;
    const eyebrowWidth = width(LONGEST.toUpperCase(), theme.type.eyebrow.fontSize, tracking);
    const flat = width(LONGEST.toUpperCase(), theme.type.eyebrow.fontSize);

    expect(eyebrowWidth - flat).toBeCloseTo(LONGEST.length * tracking, 1);
  });
});

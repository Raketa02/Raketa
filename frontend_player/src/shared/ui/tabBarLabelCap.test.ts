/**
 * `theme.size.tabBar.labelMaxScale`, held against the words it caps — and the dock's column and
 * marker held against them at it (10.2, ADR-0210 §5, #883).
 *
 * The tab bar has exactly one Dynamic Type mechanism. Part 13 requires text to scale with the
 * OS setting, names the tab bar as the one place a **fixed height** is the design, and permits
 * `allowFontScaling={false}` only inside the level bar's drawn geometry — so the label may
 * neither be frozen nor grow without bound, and `maxFontSizeMultiplier` is what is left.
 *
 * **1,6 was derived over five columns** — the largest step at which *Players*, the longest of
 * five labels, still fit a 64pt column on the narrowest phone. The bar is three columns since
 * the old loop's Players and Chats left it ([#576](https://github.com/Rakieta02/Rakieta/issues/576)),
 * and the five-column fit went with them. **The cap stays where the five left it, and it now holds
 * the column's content inside the selection marker**: the dock is 54 at every text size, and an 18pt
 * icon, the grid's smallest step and one line of `tag` at the cap must stand inside the 75 × 42
 * capsule behind them. This file holds that, the words inside their columns, and the marker's widest
 * stretch inside the narrowest phone's column — measured, so a fourth tab, a longer word or a larger
 * icon goes red here rather than on somebody's phone.
 *
 * **What makes it go red:** a fourth tab, a longer label, a different type role, a different
 * weight, a larger icon, a smaller marker, a change to the dock's insets, or an Archivo release that
 * redraws the letters. None of them announces itself at 9,5pt.
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

import { ADMINISTRATOR_TAB_BAR_TABS, TAB_BAR_TABS } from './TabBar';
import { MARKER_WIDEST } from './tabMarkerMotion';
import { theme } from './theme';

const { tabBar } = theme.size;

/** The dock's hairline: the columns are laid inside it. */
const HAIRLINE = 1;

/**
 * **A column on the narrowest phone, measured on the dock's outer edge** — the screen less the
 * dock's 12 either side, over the three tabs: (320 − 24) ÷ 3 = 98,7 (ADR-0210 §2).
 */
const COLUMN = (NARROWEST_SCREEN - 2 * tabBar.sideInset) / TAB_BAR_TABS.length;

/** **The column as built** — the same, inside the 1pt hairline the dock is bounded by. */
const COLUMN_AS_BUILT =
  (NARROWEST_SCREEN - 2 * tabBar.sideInset - 2 * HAIRLINE) / TAB_BAR_TABS.length;

/**
 * What is left of the marker for the word: the smallest step on the 3pt grid held on each side,
 * so a label at the cap never touches the capsule's ends. A design value, not a fudge factor.
 */
const AVAILABLE = tabBar.marker.width - 2 * theme.space.xxs;

/** One line of `tag` at the cap — React Native scales the line height with the font. */
const LINE_AT_CAP = theme.type.tag.lineHeight * tabBar.labelMaxScale;

/**
 * **The marker's widest stretch** — the motion's own, never a copy: 1,30 of its width, which a
 * two-column trip peaks at and nothing draws past (ADR-0210 §8's calibration, #884).
 */
const PEAK_STRETCH = MARKER_WIDEST;

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

/**
 * **Every word a dock draws** — the player's three and the Administrator's two, which stand on the
 * same 75pt marker. The column is the player's: three to a dock is the narrower.
 */
const LABELS = [...TAB_BAR_TABS, ...ADMINISTRATOR_TAB_BAR_TABS].map((tab) => tab.label);

const LONGEST = LABELS.reduce((a, b) =>
  width(b, theme.type.tag.fontSize) > width(a, theme.type.tag.fontSize) ? b : a,
);

/** The column's content, top to bottom: the icon, the gap, the label's line. */
const contentHeight = (icon: number, line: number) => icon + theme.space.xxs + line;

// ---------------------------------------------------------------------------

describe('the face being measured', () => {
  it('is a weight the app actually loads', () => {
    // The read above proves the file exists in the package. This proves the app puts it on
    // the device: a role pointed at an Archivo weight `bootstrap/fonts.ts` does not register
    // renders in the system font, and the measurement would then be of a face nothing draws.
    expect(Object.values(theme.font.sans)).toContain(theme.type.tag.fontFamily);
  });

  it('reads a 1000-unit em and draws every character the labels use', () => {
    expect(archivoBold.unitsPerEm).toBe(1000);
    for (const label of LABELS) {
      for (const character of label) {
        expect(archivoBold.advance(character.codePointAt(0)!)).toBeGreaterThan(0);
      }
    }
  });
});

describe('the column the content has to fit', () => {
  it('is the narrowest phone less the dock’s side insets, divided three ways — 98,7', () => {
    expect(TAB_BAR_TABS).toHaveLength(3);
    expect(COLUMN).toBeCloseTo(98.67, 2);
  });

  it('is 98 as built, inside the hairline', () => {
    expect(COLUMN_AS_BUILT).toBeCloseTo(98, 2);
  });
});

/** **Fit one: an 18pt icon and the capped label inside the 75 × 42 marker.** */
describe('the icon and the capped label inside the marker', () => {
  it('stand inside its 42 top to bottom at the cap — 18 + 3 + 19,2 = 40,2', () => {
    expect(contentHeight(tabBar.icon, LINE_AT_CAP)).toBeCloseTo(40.2, 5);
    expect(contentHeight(tabBar.icon, LINE_AT_CAP)).toBeLessThanOrEqual(tabBar.marker.height);
  });

  it('would not at 20 — 42,2 — which is why the icon is 18', () => {
    expect(contentHeight(20, LINE_AT_CAP)).toBeGreaterThan(tabBar.marker.height);
  });

  it('keeps every word on either dock inside the marker’s width at the cap', () => {
    for (const label of LABELS) {
      const scaled = width(label, theme.type.tag.fontSize) * tabBar.labelMaxScale;
      expect(scaled).toBeLessThanOrEqual(AVAILABLE);
    }
  });

  it('keeps the icon inside the marker’s width too', () => {
    expect(tabBar.icon).toBeLessThanOrEqual(AVAILABLE);
  });

  it('is decided by the height, not the width: the longest word fits wider than the cap', () => {
    expect(LONGEST).toBe('Groups');
    expect(largestStepThatFits(width(LONGEST, theme.type.tag.fontSize), AVAILABLE)).toBeGreaterThan(
      tabBar.labelMaxScale,
    );
  });

  it('leaves the dock 54 — the marker stands inside it with room above and below', () => {
    expect(tabBar.marker.height).toBeLessThan(tabBar.height - 2 * HAIRLINE);
  });

  it('is a scale and not a licence — the bar is still bounded', () => {
    // `allowFontScaling={false}` is what this replaces, so the cap must actually be a cap.
    expect(tabBar.labelMaxScale).toBeGreaterThan(1);
  });
});

/** **Fit three: the marker's widest stretch inside the 320 phone's column.** */
describe('the marker inside its column', () => {
  it('stretches to 97,5 at its peak, inside the 98,7 column on the dock’s outer edge', () => {
    const peak = tabBar.marker.width * PEAK_STRETCH;

    expect(peak).toBeCloseTo(97.5, 5);
    expect(peak).toBeLessThanOrEqual(COLUMN);
  });

  it('stays inside the column as built, inside the hairline', () => {
    expect(tabBar.marker.width * PEAK_STRETCH).toBeLessThanOrEqual(COLUMN_AS_BUILT);
  });

  it('rests with room either side of it in that column', () => {
    expect(COLUMN_AS_BUILT - tabBar.marker.width).toBeGreaterThan(2 * theme.space.sm);
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

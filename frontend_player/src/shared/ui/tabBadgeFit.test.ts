/**
 * The tab bar's badge geometry, derived rather than chosen — **because a device has to draw it, and
 * this file stands in for one** until the phone walk (#885).
 *
 * [10.2](../../docs/design-system.md#102-the-tab-bar) places the badge on Home's 18pt icon: it rises
 * 4 above the icon's box and sits 3 back over its right edge, out of the layout, so a count never
 * changes the dock's 54 (ADR-0210 §5, #883). The numbers are checked against the real IBM Plex Mono
 * in the bundle, in the narrowest phone's column and inside the dock at the label's cap, so a mark
 * that would truncate, overflow its column or cross the dock's edge goes red here rather than on
 * somebody's home screen.
 *
 * **What makes it go red:** a fourth tab, a different type role for the digit, a larger icon, a
 * higher rise, a shorter dock, or a Plex release that redraws the figures. Every one of those is a
 * real change to the answer, and none of them announces itself at 13pt.
 *
 * The arrangement is `tabBarLabelCap.test.ts`'s, one mark over: `theme.ts` carries the answer
 * and this file is where it comes from, because a `theme.ts` that checked its own arithmetic
 * would be the app refusing to launch over a drawing detail.
 */

import { NARROWEST_SCREEN, readFace, widthOf } from '@/test-support/fontMetrics';

import { TAB_BAR_TABS } from './TabBar';
import { theme } from './theme';

const { tabBar } = theme.size;
const { badge, badgeRise } = tabBar;

/** The dock's hairline: the columns are laid inside it, and the badge must not cross it. */
const HAIRLINE = 1;

/** A column on the narrowest phone as built: inside the dock's side insets and its hairline. */
const COLUMN = (NARROWEST_SCREEN - 2 * tabBar.sideInset - 2 * HAIRLINE) / TAB_BAR_TABS.length;

const plexMono = readFace(`@expo-google-fonts/ibm-plex-mono/${theme.num.xs.fontFamily}.ttf`);

/** A tabular digit's advance, which is every digit's advance — that is what tabular means. */
const DIGIT = widthOf(plexMono, '0', theme.num.xs.fontSize, theme.num.xs.letterSpacing);

/** The badge, drawn for a count of this many digits. */
function badgeWidth(digits: number): number {
  return Math.max(badge, digits * DIGIT + 2 * theme.space.xxs);
}

/**
 * **How far the badge's top stands inside the dock's top edge** at a text scale: the column's
 * content — the icon, the gap, one line of `tag` — is centred in the dock, and the badge rises 4
 * above the icon's box.
 */
function badgeTopAt(scale: number): number {
  const content = tabBar.icon + theme.space.xxs + theme.type.tag.lineHeight * scale;
  return (tabBar.height - content) / 2 - badgeRise;
}

describe('the digit inside the mark', () => {
  it('is a mono role, because 1.4 is categorical about counts', () => {
    expect(theme.num.xs.fontFamily).toMatch(/Mono/);
  });

  /**
   * It was the smallest mono role there was when the badge was drawn, and no seventh step
   * was added for one mark. `numTiny` arrived beneath it on 2026-09-16 for the radar's four
   * small figures (Part 16), and the badge **did not move down to it**: its 18 pt box is `xs`'s
   * 17 pt line box rounded to the grid, and a digit a step smaller would leave the box it
   * derived. So the role is pinned by name, and the roles below it are named too — `tag`, a Level
   * in a Join request's tag, arrived on 2026-09-30 (#529) and the badge did not move to it either.
   */
  it('is the mono role the badge was derived from, with only tiny and tag beneath it', () => {
    const smaller = Object.entries(theme.num)
      .filter(([, role]) => role.fontSize < theme.num.xs.fontSize)
      .map(([name]) => name);

    expect(smaller).toEqual(['tiny', 'tag']);
  });

  it('fits inside the mark with room on every side, at one digit', () => {
    expect(badgeWidth(1)).toBe(badge);
    expect(DIGIT + 2 * theme.space.xxs).toBeLessThanOrEqual(badge);
    expect(theme.num.xs.lineHeight).toBeLessThanOrEqual(badge);
  });

  it('is tabular, so a count going from 1 to 2 does not reflow the column', () => {
    expect(theme.tabular.fontVariant).toContain('tabular-nums');
    expect(widthOf(plexMono, '1', theme.num.xs.fontSize)).toBeCloseTo(
      widthOf(plexMono, '8', theme.num.xs.fontSize),
      5,
    );
  });
});

/** **Fit two: Home's badge inside the dock at the cap.** */
describe('the mark inside the dock', () => {
  it('stands 6,5 inside the dock’s top edge at the default text size', () => {
    expect(badgeTopAt(1)).toBeCloseTo(6.5, 5);
  });

  it('stands 2,9 inside it at the label’s cap, clear of the hairline', () => {
    expect(badgeTopAt(tabBar.labelMaxScale)).toBeCloseTo(2.9, 5);
    expect(badgeTopAt(tabBar.labelMaxScale)).toBeGreaterThan(HAIRLINE);
  });

  it('rises 4, its own number now the ring it was borrowed from has gone', () => {
    expect(badgeRise).toBe(4);
    expect(theme.size.tabBar).not.toHaveProperty('ringGap');
  });

  it('stays inside its own column at a two-digit count, on the narrowest phone', () => {
    // The icon box is centred in the column; the badge starts `space.xxs` back from its right
    // edge and grows outward from there.
    const left = (COLUMN - tabBar.icon) / 2 + tabBar.icon - theme.space.xxs;

    expect(left + badgeWidth(2)).toBeLessThanOrEqual(COLUMN);
  });

  it('overlaps the mark it belongs to rather than floating beside it', () => {
    expect(theme.space.xxs).toBeGreaterThan(0);
    expect(theme.space.xxs).toBeLessThan(tabBar.icon / 2);
  });
});

describe('the fill', () => {
  it('is 6.1 `primary`’s treatment rather than a colour added to the palette', () => {
    // White on `coral` is 3,89 — the one pairing Rule C refuses outright. `coralInk` publishes
    // 5,89, and it is not the marker's `coralSoft`: *a thing to attend to* and *where you are* are
    // kept apart by fill (1.2).
    expect(theme.color.coralInk).not.toBe(theme.color.coral);
    expect(theme.color.coralInk).not.toBe(theme.color.coralSoft);
  });
});

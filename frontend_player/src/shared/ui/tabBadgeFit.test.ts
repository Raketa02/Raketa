/**
 * The tab bar's badge geometry, derived rather than chosen — **because no device has drawn it.**
 *
 * [10.2](../../docs/design-system.md#102-the-tab-bar) decided the badge whole and deliberately
 * wrote no number: #338 §1's rule for this map is *ownership now, a number only for what a
 * prototype drew*, and `prototype/chats-tab` drew the screen and not the bar. So the diameter,
 * the rise and the type role arrive with the ticket that draws them
 * ([#360](https://github.com/Raketa02/Raketa/issues/360)) — and this file is what stands in for
 * the device: the numbers are checked against the real IBM Plex Mono in the bundle, in the
 * narrowest phone's column, so a mark that would truncate or overflow goes red here rather than
 * on somebody's home screen.
 *
 * **What makes it go red:** a fourth tab, a different type role for the digit, a change to the
 * bar's top padding, or a Plex release that redraws the figures. Every one of those is a real
 * change to the answer, and none of them announces itself at 13pt.
 *
 * The arrangement is `tabBarLabelCap.test.ts`'s, one mark over: `theme.ts` carries the answer
 * and this file is where it comes from, because a `theme.ts` that checked its own arithmetic
 * would be the app refusing to launch over a drawing detail.
 */

import { NARROWEST_SCREEN, readFace, widthOf } from '@/test-support/fontMetrics';

import { TAB_BAR_TABS } from './TabBar';
import { theme } from './theme';

/** The bar is equal columns edge to edge, so a column is the screen over the three tabs. */
const COLUMN = NARROWEST_SCREEN / TAB_BAR_TABS.length;

const { badge, badgeRise } = theme.size.tabBar;

const plexMono = readFace(`@expo-google-fonts/ibm-plex-mono/${theme.num.xs.fontFamily}.ttf`);

/** A tabular digit's advance, which is every digit's advance — that is what tabular means. */
const DIGIT = widthOf(plexMono, '0', theme.num.xs.fontSize, theme.num.xs.letterSpacing);

/** The badge, drawn for a count of this many digits. */
function badgeWidth(digits: number): number {
  return Math.max(badge, digits * DIGIT + 2 * theme.space.xxs);
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

describe('the mark against the bar it sits on', () => {
  it('rises no further than the padding the bar already spends on the ring', () => {
    // 10.2: the ring's 4pt comes out of the bar's own 6pt top padding, leaving 2pt of
    // clearance to the hairline. The badge takes the same 4 and no more, so the bar's height
    // is the same on every screen in the app.
    expect(badgeRise).toBe(theme.size.tabBar.ringGap + theme.size.tabBar.ringStroke);
    expect(badgeRise).toBeLessThan(theme.space.xs);
  });

  it('stays inside its own column at a two-digit count, on the narrowest phone', () => {
    // The icon box is centred in the column; the badge starts `space.xxs` back from its right
    // edge and grows outward from there.
    const left = (COLUMN - theme.size.tabIcon) / 2 + theme.size.tabIcon - theme.space.xxs;

    expect(left + badgeWidth(2)).toBeLessThanOrEqual(COLUMN);
  });

  it('overlaps the mark it belongs to rather than floating beside it', () => {
    expect(theme.space.xxs).toBeGreaterThan(0);
    expect(theme.space.xxs).toBeLessThan(theme.size.tabIcon / 2);
  });
});

describe('the fill', () => {
  it('is the disc’s own treatment rather than a colour added to the palette', () => {
    // White on `coral` is 3,89 — the one pairing Rule C refuses outright, and the correction
    // the Play disc one column away already took once. `coralInk` publishes 5,89.
    expect(theme.color.coralInk).not.toBe(theme.color.coral);
  });
});

/**
 * The three controls onboarding's second part introduces, pinned at the one width where
 * their geometry can fail.
 *
 * `docs/design-system.md` 6.8, 6.9 and 6.10 each make an arithmetic claim — *this hour cell is
 * reachable up to its neighbours and no further*, *this remove control reaches 44pt without
 * crossing into its neighbour*, *this slider's row is the touch minimum* — and every one of
 * them is a division by a screen width. Part 13 locks 44 × 44pt as the minimum reachable area, and
 * 6.5 bounds horizontal hit-slop by the neighbour, so a target that clears 44 on a wide
 * phone and misses it on a narrow one is a rule that holds for most players and quietly
 * fails the rest.
 *
 * **The narrowest phone is where all three are decided.** Content width is screen width
 * less two gutters ([Part 0.2](../../../docs/design-system.md#02-what-replaces-the-frame)),
 * so on a 320pt device there are 290pt to divide. That is the number 7.9 already reasons
 * against for the question navigator, and it is the number that shows seven columns cannot
 * reach the minimum: 7 × 44 = 308 does not fit in 290.
 *
 * **6.8's week of hours is the one control here that is under the minimum on purpose**
 * (mock 36, ADR-0189 §5): seven days across and sixteen hours down cannot be 44pt in either
 * axis, so the grid is drawn to fit the page and a drag paints a run. What is pinned for it
 * is what it keeps — reachable areas that tile the grid without overlapping, a cell width that
 * survives Dynamic Type on the narrowest phone, and a paint intent that claims a drag before
 * the page can take it as a scroll.
 *
 * A test and not a runtime assertion, for the reason `bandEdges.test.ts` gives: a
 * `theme.ts` that checked its own arithmetic would be the app refusing to launch over a
 * drawing detail. A red build is where a human reconciles it.
 *
 * Deliberately scoped to the three new controls. A sweep over every entry in `theme.hit`
 * would also fail — the segmented control is 25pt visual against `{ top: 9, bottom: 9 }`,
 * which is 43 — and that is a pre-existing defect in a component nothing builds today,
 * not something this file should silently re-baseline.
 *
 * Every assertion here is one a change to `theme.ts` could genuinely break. Values the
 * theme derives rather than states — the footnote's two lines of `type.tiny` — are not
 * pinned, because an assertion that restates a derivation cannot fail.
 */

import { HOURS } from '@/shared/vocabulary/week';

import { theme } from './theme';
import { NARROWEST_SCREEN } from '@/test-support/fontMetrics';

/** Part 0.2: content width is screen width less both gutters. Never a fixed 362. */
const NARROWEST_CONTENT = NARROWEST_SCREEN - 2 * theme.size.gutter;

/** What a `hitSlop` adds to a visual, in one axis. */
function reachable(visual: number, before: number, after: number): number {
  return visual + before + after;
}

describe('the narrowest content width', () => {
  it('is the 290pt figure the design system reasons against', () => {
    expect(NARROWEST_CONTENT).toBe(290);
  });

  it('cannot fit seven columns at the touch minimum', () => {
    expect(7 * theme.size.minTouch).toBeGreaterThan(NARROWEST_CONTENT);
  });
});

describe('the hour cell (6.8)', () => {
  const { availability } = theme.size;
  const slop = theme.hit.availabilityCell;

  /** What the grid has to divide: the content width, less the card it sits inside. */
  const insideTheCard = NARROWEST_CONTENT - 2 * availability.cardPadding;

  /**
   * Seven cells share whatever the hour-label column leaves, inside the card. The label column
   * is content-sized so it grows with Dynamic Type, capped by `labelMaxRatio` — so this is the
   * *worst* case, the cell width at the largest text setting the cap allows.
   */
  const narrowestCell =
    (insideTheCard -
      insideTheCard * availability.labelMaxRatio -
      availability.labelGutter -
      (availability.columns - 1) * availability.gap) /
    availability.columns;

  /**
   * The reason the cell is not 44pt tall: sixteen hours at the minimum, with their gaps, are
   * taller than the shortest phone in the population is — before a header, a button or a tab
   * bar has taken anything. A grid that scrolled under the finger painting it would paint the
   * wrong hours.
   */
  it('could not draw sixteen hours at the touch minimum on any page', () => {
    const SHORTEST_SCREEN = 667;
    expect(
      HOURS.length * theme.size.minTouch + (HOURS.length - 1) * availability.gap,
    ).toBeGreaterThan(SHORTEST_SCREEN);
  });

  /**
   * The neighbour rule, read in both axes: each cell reaches half the gap on every side and not
   * a point more, so two cells' reachable areas meet exactly — no dead point between them, and
   * no point that belongs to both.
   */
  it('reaches exactly half the gap on every side, so the reachable areas tile the grid', () => {
    expect(slop.top + slop.bottom).toBe(availability.gap);
    expect(slop.left + slop.right).toBe(availability.gap);
  });

  /** Stated as a figure, so the next change to the cell, the gap or the slop is a choice. */
  it('is reachable 24pt high, one hour to the next', () => {
    expect(reachable(availability.cellHeight, slop.top, slop.bottom)).toBe(24);
  });

  /**
   * The label column's cap is the one thing standing between Dynamic Type and a cell too
   * narrow to aim at, so the width left at the cap is stated — and the margin it keeps.
   */
  it('is still more than 23pt wide on the narrowest phone with the labels at their cap', () => {
    expect(narrowestCell).toBeGreaterThan(23);
    expect(reachable(narrowestCell, slop.left, slop.right)).toBeGreaterThan(27);
  });

  /**
   * A drag down a column is the grid's only if the grid claims it first. Both platforms begin
   * a scroll once a finger has moved their touch slop — 8dp on Android, about 10pt on iOS — so
   * the paint intent sits under the smaller of the two.
   */
  it('claims a drag before either platform would begin a scroll', () => {
    const ANDROID_TOUCH_SLOP = 8;
    expect(availability.paintIntent).toBeLessThan(ANDROID_TOUCH_SLOP);
    expect(availability.paintIntent).toBeGreaterThan(0);
  });
});

describe('the photo tile (6.9)', () => {
  const { photoTile } = theme.size;

  const tileWidth =
    (NARROWEST_CONTENT - (photoTile.columns - 1) * photoTile.gap) / photoTile.columns;
  const tileHeight = tileWidth / photoTile.aspectRatio;

  it('is its own touch target several times over', () => {
    expect(tileWidth).toBeGreaterThanOrEqual(theme.size.minTouch);
    expect(tileHeight).toBeGreaterThanOrEqual(theme.size.minTouch);
  });

  it('grows its remove control to the touch minimum by hit-slop', () => {
    const { top, bottom, left, right } = theme.hit.photoRemove;
    expect(reachable(photoTile.remove, top, bottom)).toBe(theme.size.minTouch);
    expect(reachable(photoTile.remove, left, right)).toBe(theme.size.minTouch);
  });

  /**
   * The claim 6.9 makes for anchoring that square *inside* the tile rather than over its
   * corner. 6.5 bounds horizontal slop by the neighbour, so an overhanging control could
   * take at most half the 9pt gap — and the 4,5pt it took would be the next tile's. This
   * asserts the alternative genuinely falls short, which is the whole argument: if it
   * reached 44 the design would be free to overhang and take the corner back.
   */
  it('could not have reached the minimum by overhanging the tile edge', () => {
    const overhanging = reachable(photoTile.remove, theme.hit.photoRemove.left, photoTile.gap / 2);
    expect(overhanging).toBeLessThan(theme.size.minTouch);
  });

  it('leaves the tile a press area after the remove square takes its corner', () => {
    const remaining = tileWidth * tileHeight - theme.size.minTouch ** 2;
    expect(remaining).toBeGreaterThan(theme.size.minTouch ** 2);
  });

  it('draws its foot strip and the bar inside it to the system bar height', () => {
    expect(photoTile.progressBar).toBe(theme.size.bar);
    expect(photoTile.progressBar).toBeLessThan(photoTile.strip);
  });
});

describe('the radius slider (6.10)', () => {
  const { radiusSlider } = theme.size;

  /**
   * The row, not the thumb, is the touch surface — a press anywhere on it moves the value
   * there. That is what makes the slider reachable without a `hitSlop` entry, and it is
   * also why 6.10 gives it no horizontal bound: the slider owns the full content width and
   * has no neighbour to steal from.
   */
  it('makes its whole row the touch minimum, so the thumb needs no hit-slop', () => {
    expect(radiusSlider.row).toBe(theme.size.minTouch);
  });

  it('fits the thumb and its ring inside that row', () => {
    expect(radiusSlider.thumb + 2 * radiusSlider.thumbRing).toBeLessThanOrEqual(radiusSlider.row);
  });

  it('draws its track at the system bar height, like every other bar in the app', () => {
    expect(radiusSlider.trackHeight).toBe(theme.size.bar);
  });

  it('rings the thumb thickly enough to read against the fill behind it', () => {
    expect(radiusSlider.thumbRing).toBeGreaterThanOrEqual(theme.size.levelBar.markRing);
  });
});

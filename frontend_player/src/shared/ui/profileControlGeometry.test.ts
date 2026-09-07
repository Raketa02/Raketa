/**
 * The three controls onboarding's second part introduces, pinned at the one width where
 * their geometry can fail.
 *
 * `docs/design-system.md` 6.8, 6.9 and 6.10 each make an arithmetic claim — *this cell is
 * 44pt without hit-slop*, *this remove control reaches 44pt without crossing into its
 * neighbour*, *this slider's row is the touch minimum* — and every one of them is a
 * division by a screen width. Part 13 locks 44 × 44pt as the minimum reachable area, and
 * 6.5 bounds horizontal hit-slop by the neighbour, so a target that clears 44 on a wide
 * phone and misses it on a narrow one is a rule that holds for most players and quietly
 * fails the rest.
 *
 * **The narrowest phone is where all three are decided.** Content width is screen width
 * less two gutters ([Part 0.2](../../../docs/design-system.md#02-what-replaces-the-frame)),
 * so on a 320pt device there are 290pt to divide. That is the number 7.9 already reasons
 * against for the question navigator, and it is the number that ruled out laying the
 * availability grid out as seven columns: 7 × 44 = 308 does not fit in 290, no hit-slop
 * closes the deficit, and the widest phone in the population does not close it either.
 *
 * **6.8 now draws its grid inside a card**, which takes another 24pt off the width before
 * the three cells divide it. That is why `cardPadding` appears in the arithmetic below: the
 * bound the section claims is still met, and it is met with less room than it used to be.
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

import { theme } from './theme';

/**
 * The narrowest phone the app supports, and the only width these assertions run at.
 *
 * iPhone SE / iPhone 8 in points. Not a token: it is a fact about the device population,
 * not a value any component reads, and `theme.ts` holds only what components read.
 */
const NARROWEST_SCREEN = 320;

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

  it('cannot fit seven columns at the touch minimum, which is why days are rows', () => {
    expect(7 * theme.size.minTouch).toBeGreaterThan(NARROWEST_CONTENT);
  });
});

describe('the availability cell (6.8)', () => {
  const { availability } = theme.size;

  /** What the grid has to divide: the content width, less the card it sits inside. */
  const insideTheCard = NARROWEST_CONTENT - 2 * availability.cardPadding;

  /**
   * Three cells share whatever the day-label column leaves, inside the card. The label
   * column is content-sized so it grows with Dynamic Type, capped by `labelMaxRatio` — so
   * this is the *worst* case, the cell width at the largest text setting the cap allows.
   */
  const widestLabelColumn = insideTheCard * availability.labelMaxRatio;
  const cellWidth =
    (insideTheCard -
      widestLabelColumn -
      availability.labelGutter -
      (availability.columns - 1) * availability.gap) /
    availability.columns;

  it('reaches the touch minimum by height alone, with no hit-slop to grant', () => {
    expect(availability.cellHeight).toBe(theme.size.minTouch);
  });

  it('clears the touch minimum in width even with the label column at its cap', () => {
    expect(cellWidth).toBeGreaterThanOrEqual(theme.size.minTouch);
  });

  /**
   * The card is what makes that assertion worth re-reading rather than inheriting: it takes
   * 24pt off the width, and the margin over the minimum is what is left of what the layout
   * used to have. Stated so the next person adding padding to the card can see the room they
   * are spending.
   */
  it('is left 15,5pt of room over the minimum once the card has taken its padding', () => {
    expect(cellWidth - theme.size.minTouch).toBeCloseTo(15.5, 1);
  });

  /**
   * The other axis, and the property no other control in the app has: this cell reaches the
   * minimum in **both** directions without a `hitSlop` entry to grant it either one.
   */
  it('needs no hit-slop in either axis', () => {
    expect(theme.hit).not.toHaveProperty('availability');
  });

  /**
   * The label column's cap is the only thing standing between Dynamic Type and a cell too
   * narrow to hit, so it is worth stating what it may not grow to: a cap that let the
   * labels take a third of the card would still pass the assertion above today, and would
   * stop passing it the moment the gap, the padding or the gutter moved.
   */
  it('caps the label column well short of what would starve the cells', () => {
    const capThatWouldStarveThem = 1 - (availability.columns * theme.size.minTouch) / insideTheCard;
    expect(availability.labelMaxRatio).toBeLessThan(capThatWouldStarveThem);
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

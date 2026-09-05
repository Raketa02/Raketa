/**
 * `ON_COURT_MAX_SCALE`, and the three drawings it ruled out — measured rather than argued.
 *
 * #302 and #313 both draw the mark as a small shield top right carrying **✓ ON COURT**. What
 * this file establishes is that none of that fits a 74pt panel, and it establishes it the way
 * [`tabBarLabelCap.test.ts`](../../../../shared/ui/tabBarLabelCap.test.ts) establishes the tab
 * bar's cap: by reading the advance widths out of the Archivo Bold that ships in the bundle,
 * rather than by a hard-coded *"about 0,6em per character"*. A drawing ruled out by eye is a
 * drawing somebody puts back.
 *
 * Two numbers do all the work. `ON COURT` is **51,19pt** at `type.tag`, and the panel's corner
 * radius is **33 % of its own width** — so the box is 74pt wide only well below the corner,
 * and at the mark's own top edge it is 57,2. Everything below follows from those.
 *
 * **What makes it go red:** re-wording the mark, re-sizing the panel, changing the radius
 * ratio, moving the mark's inset, a different type role, or an Archivo release that redraws
 * the letters. Every one of those is a real change to the answer and none announces itself at
 * 9,5pt.
 */

import { largestStepThatFits, readFace, widthOf } from '@/test-support/fontMetrics';
import { theme } from '@/shared/ui';

import { ON_COURT_MARK } from '../playerCardPresentation';

import { CANDIDATE_PANEL, candidatePhotoRadius } from './CandidatePhoto';
import { ON_COURT_MAX_SCALE } from './OnCourtMark';

const archivoBold = readFace(`@expo-google-fonts/archivo/${theme.type.tag.fontFamily}.ttf`);

/** The mark as it is drawn — the style shouts it, so the measurement shouts it too. */
const WORDS = ON_COURT_MARK.toUpperCase();

const width = (word: string) => widthOf(archivoBold, word, theme.type.tag.fontSize);

/**
 * How much narrower the panel is than its own width, at a height `y` from its top — one side.
 *
 * The corner is a quarter circle of radius `r` centred at `(r, r)`, so a horizontal line at
 * `y < r` meets it `r − √(r² − (r−y)²)` in from the edge. `overflow: 'hidden'` on the panel
 * means that curve is a **clip**: a label crossing it loses its first letter rather than
 * overhanging.
 */
function cornerInset(y: number): number {
  const r = candidatePhotoRadius(CANDIDATE_PANEL.width);
  return y >= r ? 0 : r - Math.sqrt(r * r - (r - y) ** 2);
}

/** What the panel leaves for a label whose own top edge sits `y` down from the panel's. */
function usableWidth(y: number): number {
  return CANDIDATE_PANEL.width - 2 * cornerInset(y);
}

/** The mark's top edge: the panel's content layer is padded by one grid step. */
const TOP = theme.space.xs;

describe('the panel the mark has to fit', () => {
  it('is a third of its own width at the corner, which is what narrows the top', () => {
    expect(candidatePhotoRadius(CANDIDATE_PANEL.width)).toBeCloseTo(24.42, 2);
    // Two thirds of the panel's width, at the height the mark is drawn at. The mark is
    // centred because of this number and not as a composition choice.
    expect(usableWidth(TOP)).toBeCloseTo(57.22, 2);
    expect(usableWidth(TOP)).toBeLessThan(CANDIDATE_PANEL.width);
  });

  it('is wide enough for the words, centred, with the grid step clear on each side', () => {
    expect(width(WORDS)).toBeCloseTo(51.19, 2);
    expect(usableWidth(TOP) - width(WORDS)).toBeGreaterThanOrEqual(2 * theme.space.xxs);
  });

  it('clips a label flush against its own left padding', () => {
    // The other half of *centred is geometry*: the content layer's padding is one grid step,
    // and at the mark's top edge the curve has not cleared that column yet. A left-aligned
    // mark loses its first letter to the corner; a centred one takes the middle of what is
    // left and clears both curves.
    expect(cornerInset(TOP)).toBeGreaterThan(theme.space.xs);
  });
});

describe('the cap', () => {
  it('is the largest step the panel leaves', () => {
    expect(ON_COURT_MAX_SCALE).toBe(largestStepThatFits(width(WORDS), usableWidth(TOP)));
  });

  it('is a bound rather than a freeze — the one thing Part 13 will not have', () => {
    expect(ON_COURT_MAX_SCALE).toBeGreaterThan(1);
  });

  it('is the largest that does: one more step runs into the corner', () => {
    expect(width(WORDS) * (ON_COURT_MAX_SCALE + 0.1)).toBeGreaterThan(usableWidth(TOP));
  });
});

describe('the drawings the arithmetic ruled out', () => {
  it('has no ✓ to draw: Archivo does not ship one', () => {
    // U+2713. The face the app loads has no glyph for it, so a text tick renders in a
    // per-platform fallback whose advance nothing here could measure and whose weight nothing
    // here would control — ADR-0135's argument about U+26A1, one surface over.
    expect(archivoBold.draws(0x2713)).toBe(false);
    expect(archivoBold.draws(0x2714)).toBe(false);
    // The letters it does draw, so the assertion above is about that character rather than
    // about a font file this test failed to read.
    for (const character of WORDS.replace(' ', '')) {
      expect(archivoBold.draws(character.codePointAt(0)!)).toBe(true);
    }
  });

  it('leaves the app’s own drawn tick no room beside the words at all', () => {
    // `theme.size.availability.tick` is the box `shared/ui/Tick` actually draws into — the
    // mark family's one 12 x 12 (6.8), read off the token the component reads rather than
    // written as 12, so a family drawn at a new size re-derives this rather than outliving it.
    // It does not cost the words their headroom; it costs them the drawing, at the system's
    // own text size and before any scaling is asked for.
    const besideATick = usableWidth(TOP) - theme.size.availability.tick;

    expect(besideATick).toBeLessThan(width(WORDS));
    expect(largestStepThatFits(width(WORDS), besideATick)).toBeLessThan(1);
  });

  it('leaves a chip inset from the corner too narrow for the words at all', () => {
    // A `Tag`-shaped shield: inset from the panel's edge by the smallest grid step, with the
    // tag's own horizontal padding inside it. It comes out under the word's own width, which
    // is why *top right* is not a placement this panel has.
    const chip = usableWidth(TOP) - 2 * theme.space.xxs - 2 * theme.space.xs;

    expect(chip).toBeLessThan(width(WORDS));
  });
});

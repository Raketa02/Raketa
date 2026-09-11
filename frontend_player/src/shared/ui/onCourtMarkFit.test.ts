/**
 * `ON_COURT_MAX_SCALE`, the mark's own two words, and the three drawings the arithmetic ruled
 * out — measured rather than argued.
 *
 * #302 and #313 both draw the mark as a small shield top right carrying **✓ ON COURT**. What
 * this file establishes is that none of that fits a 74pt panel, and it establishes it the way
 * [`tabBarLabelCap.test.ts`](./tabBarLabelCap.test.ts) establishes the tab bar's cap: by
 * reading the advance widths out of the Archivo Bold that ships in the bundle, rather than by
 * a hard-coded *"about 0,6em per character"*. A drawing ruled out by eye is a drawing somebody
 * puts back.
 *
 * Two numbers do all the work. `ON COURT` is **51,19pt** at `type.tag`, and a panel's corner
 * radius is **33 % of its own width** — so a panel is its full width only well below the
 * corner, and at the mark's own top edge it is narrower. Everything below follows from those.
 *
 * **Both sizes are derived here and neither is scaled from the other**
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)). The card's 74pt panel leaves 57,22
 * and the record sheet's 112pt panel leaves 78,45 — the corner takes a *different fraction* of
 * a different width, so multiplying one cap by the widths' ratio would be arithmetic over the
 * wrong quantity. The ruled-out drawings are asserted at the card's size, which is the one
 * they were drawn against and the tighter of the two.
 *
 * **What makes it go red:** re-wording the mark, re-sizing either panel, changing the radius
 * ratio, moving the mark's inset, a different type role, or an Archivo release that redraws
 * the letters. Every one of those is a real change to the answer and none announces itself at
 * 9,5pt.
 */

import { largestStepThatFits, readFace, widthOf } from '@/test-support/fontMetrics';

import { ON_COURT_CLAUSE, ON_COURT_MARK, ON_COURT_MAX_SCALE } from './OnCourtMark';
import { PHOTO_PANEL, playerPhotoRadius, type PhotoPanelSize } from './PlayerPhoto';
import { theme } from './theme';

const archivoBold = readFace(`@expo-google-fonts/archivo/${theme.type.tag.fontFamily}.ttf`);

/** The mark as it is drawn — the style shouts it, so the measurement shouts it too. */
const WORDS = ON_COURT_MARK.toUpperCase();

const width = (word: string) => widthOf(archivoBold, word, theme.type.tag.fontSize);

/**
 * How much narrower a panel is than its own width, at a height `y` from its top — one side.
 *
 * The corner is a quarter circle of radius `r` centred at `(r, r)`, so a horizontal line at
 * `y < r` meets it `r − √(r² − (r−y)²)` in from the edge. `overflow: 'hidden'` on the panel
 * means that curve is a **clip**: a label crossing it loses its first letter rather than
 * overhanging.
 */
function cornerInset(panelWidth: number, y: number): number {
  const r = playerPhotoRadius(panelWidth);
  return y >= r ? 0 : r - Math.sqrt(r * r - (r - y) ** 2);
}

/** What a panel leaves for a label whose own top edge sits `y` down from the panel's. */
function usableWidth(size: PhotoPanelSize, y: number = TOP): number {
  const panelWidth = PHOTO_PANEL[size].width;
  return panelWidth - 2 * cornerInset(panelWidth, y);
}

/** The mark's top edge: the panel's content layer is padded by one grid step. */
const TOP = theme.space.xs;

/** The two sizes, so a third one added to `PHOTO_PANEL` arrives here rather than untested. */
const SIZES = Object.keys(PHOTO_PANEL) as readonly PhotoPanelSize[];

describe('the panel the mark has to fit', () => {
  it('is a third of its own width at the corner, which is what narrows the top', () => {
    expect(playerPhotoRadius(PHOTO_PANEL.card.width)).toBeCloseTo(24.42, 2);
    expect(playerPhotoRadius(PHOTO_PANEL.record.width)).toBeCloseTo(36.96, 2);

    // Two thirds of the card's width at the height the mark is drawn at, and rather more of
    // the record panel's. The mark is centred because of these numbers and not as a
    // composition choice.
    expect(usableWidth('card')).toBeCloseTo(57.22, 2);
    expect(usableWidth('record')).toBeCloseTo(78.45, 2);

    for (const size of SIZES) {
      expect(usableWidth(size)).toBeLessThan(PHOTO_PANEL[size].width);
    }
  });

  it('is wide enough for the words, centred, with the grid step clear on each side', () => {
    expect(width(WORDS)).toBeCloseTo(51.19, 2);

    for (const size of SIZES) {
      expect(usableWidth(size) - width(WORDS)).toBeGreaterThanOrEqual(2 * theme.space.xxs);
    }
  });

  it('clips a label flush against its own left padding', () => {
    // The other half of *centred is geometry*: the content layer's padding is one grid step,
    // and at the mark's top edge the curve has not cleared that column yet. A left-aligned
    // mark loses its first letter to the corner; a centred one takes the middle of what is
    // left and clears both curves. It is true at both sizes, and more so at the larger, whose
    // corner is deeper.
    for (const size of SIZES) {
      expect(cornerInset(PHOTO_PANEL[size].width, TOP)).toBeGreaterThan(theme.space.xs);
    }
  });
});

describe('the cap', () => {
  it('is the largest step each panel leaves', () => {
    for (const size of SIZES) {
      expect(ON_COURT_MAX_SCALE[size]).toBe(largestStepThatFits(width(WORDS), usableWidth(size)));
    }
  });

  it('is a bound rather than a freeze — the one thing Part 13 will not have', () => {
    for (const size of SIZES) {
      expect(ON_COURT_MAX_SCALE[size]).toBeGreaterThan(1);
    }
  });

  it('is the largest that does: one more step runs into the corner', () => {
    for (const size of SIZES) {
      expect(width(WORDS) * (ON_COURT_MAX_SCALE[size] + 0.1)).toBeGreaterThan(usableWidth(size));
    }
  });

  it('is re-derived per panel rather than scaled from the card’s', () => {
    // The record panel is 112/74 = 1,514 times as wide, and its cap is NOT the card's cap
    // times that: the corner eats a different fraction of each. A caller who reached for a
    // multiplier would land here.
    const scaled = ON_COURT_MAX_SCALE.card * (PHOTO_PANEL.record.width / PHOTO_PANEL.card.width);

    expect(ON_COURT_MAX_SCALE.record).not.toBeCloseTo(scaled, 1);
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
    const besideATick = usableWidth('card') - theme.size.availability.tick;

    expect(besideATick).toBeLessThan(width(WORDS));
    expect(largestStepThatFits(width(WORDS), besideATick)).toBeLessThan(1);
  });

  it('leaves a chip inset from the corner too narrow for the words at all', () => {
    // A `Tag`-shaped shield: inset from the panel's edge by the smallest grid step, with the
    // tag's own horizontal padding inside it. It comes out under the word's own width, which
    // is why *top right* is not a placement the card's panel has.
    const chip = usableWidth('card') - 2 * theme.space.xxs - 2 * theme.space.xs;

    expect(chip).toBeLessThan(width(WORDS));
  });
});

/**
 * The mark's two words, and the clause a listener gets instead of them.
 *
 * They arrived here with the component that draws them, from Play's own copy deck: the record
 * sheet's header draws the same mark, and a second copy of *On court* is a second thing to
 * keep in step with a pinned geometry test one screen up.
 */
describe('the ON COURT mark’s words', () => {
  it('carries no figure in either register', () => {
    // ADR-0133's clause survives ADR-0138 untouched — the confidence never crosses on any
    // route — so there is nothing here to print a number from and nothing here that prints
    // one. Asserted on the strings, because the card beside them draws a Fit and a forecast
    // and a *no percentages on the card* assertion would be about those instead.
    expect(ON_COURT_MARK).not.toMatch(/\d/);
    expect(ON_COURT_CLAUSE).not.toMatch(/\d/);
  });

  it('leads with the photograph when it is spoken, and not when it is drawn', () => {
    // Two words over somebody's picture are plainly about the picture; a clause in a run of
    // sentences is not, and *on court* between a Level and a forecast is one comma away from
    // activity recency — which no card carries at any granularity.
    expect(ON_COURT_MARK).toBe('On court');
    expect(ON_COURT_CLAUSE.startsWith('Photo')).toBe(true);
  });

  it('is sentence case, because the capitals are the panel’s treatment', () => {
    // The Sport beneath it is uppercased by the same style rather than by its own string.
    // A pre-shouted constant would be the one place in this deck where a style decision is
    // spelled into the copy.
    expect(ON_COURT_MARK).not.toBe(ON_COURT_MARK.toUpperCase());
  });
});

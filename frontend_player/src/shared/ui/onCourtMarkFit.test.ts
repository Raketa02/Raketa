/**
 * `ON_COURT_MAX_SCALE`, the mark's own two words with the tick before them, and the drawings
 * the arithmetic ruled out — measured rather than argued.
 *
 * #302 and #313 both draw the mark as a small shield top right carrying **✓ ON COURT**. What
 * this file establishes is that a shield does not fit a 74pt panel, that 6.8's 12 × 12 tick
 * does not either, and that the tick the mark **does** carry since
 * [ADR-0169](../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7 fits only because it is sized to the words and the mark sits lower on the panel.
 * It establishes all of it the way [`tabBarLabelCap.test.ts`](./tabBarLabelCap.test.ts)
 * establishes the tab bar's cap: by reading the advance widths out of the Archivo Bold that
 * ships in the bundle, rather than by a hard-coded *"about 0,6em per character"*. A drawing
 * ruled out by eye is a drawing somebody puts back.
 *
 * Three numbers do all the work. `ON COURT` is **51,19pt** at `type.tag`, the tick beside it
 * is **6,84pt** plus the grid's smallest step, and a panel's corner radius is **33 % of its own
 * width** — so a panel is its full width only well below the corner, and at the mark's own top
 * edge it is narrower. Everything below follows from those.
 *
 * **Both sizes are derived here and neither is scaled from the other**
 * ([#384](https://github.com/Rakieta02/Rakieta/issues/384)). The corner takes a *different
 * fraction* of a different width, so multiplying one cap by the widths' ratio would be
 * arithmetic over the wrong quantity. The ruled-out drawings are asserted at the card's size,
 * which is the one they were drawn against and the tighter of the two.
 *
 * **What makes it go red:** re-wording the mark, re-sizing either panel, changing the radius
 * ratio, moving the mark's inset, resizing the tick, a different type role, or an Archivo
 * release that redraws the letters. Every one of those is a real change to the answer and none
 * announces itself at 9,5pt.
 */

import { largestStepThatFits, readFace, widthOf } from '@/test-support/fontMetrics';

import { ON_COURT_CLAUSE, ON_COURT_MARK, ON_COURT_MAX_SCALE, onCourtTickBox } from './OnCourtMark';
import { MARK_TOP } from './PhotoPanel';
import { PHOTO_PANEL, playerPhotoRadius, type PhotoPanelSize } from './PlayerPhoto';
import { theme } from './theme';

const archivoBold = readFace(`@expo-google-fonts/archivo/${theme.type.tag.fontFamily}.ttf`);

/** The mark as it is drawn — the style shouts it, so the measurement shouts it too. */
const WORDS = ON_COURT_MARK.toUpperCase();

const width = (word: string) => widthOf(archivoBold, word, theme.type.tag.fontSize);

/** The tick and the step between it and the words — the part of the line that does not scale. */
const TICK_AND_GAP = onCourtTickBox(theme.type.tag.fontSize) + theme.space.xxs;

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
function usableWidth(size: PhotoPanelSize, y: number = MARK_TOP): number {
  const panelWidth = PHOTO_PANEL[size].width;
  return panelWidth - 2 * cornerInset(panelWidth, y);
}

/** What is left for the **words** once the tick and its gap have taken their share. */
const forTheWords = (size: PhotoPanelSize) => usableWidth(size) - TICK_AND_GAP;

/** The two sizes, so a third one added to `PHOTO_PANEL` arrives here rather than untested. */
const SIZES = Object.keys(PHOTO_PANEL) as readonly PhotoPanelSize[];

describe('the panel the mark has to fit', () => {
  it('is a third of its own width at the corner, which is what narrows the top', () => {
    expect(playerPhotoRadius(PHOTO_PANEL.card.width)).toBeCloseTo(24.42, 2);
    expect(playerPhotoRadius(PHOTO_PANEL.record.width)).toBeCloseTo(36.96, 2);

    for (const size of SIZES) {
      expect(usableWidth(size)).toBeLessThan(PHOTO_PANEL[size].width);
    }
  });

  /**
   * The mark's top edge is at **`space.md`** down the panel, not `space.xs` — moved when the
   * tick arrived (ADR-0169 §7). At 6pt the corner leaves 57,22 of a 74pt panel, which held the
   * words alone with 6pt clear and holds the words and a tick with nothing; at 12pt it leaves
   * 67,20, which holds both with the grid's smallest step clear on each side. The Level and the
   * Sport sit well below either, so nothing else moved.
   */
  it('sits at space.md, which is what makes room for the tick', () => {
    expect(MARK_TOP).toBe(theme.space.md);

    expect(usableWidth('card', theme.space.xs)).toBeCloseTo(57.22, 2);
    expect(usableWidth('card')).toBeCloseTo(67.2, 1);
    expect(usableWidth('record')).toBeCloseTo(92.6, 1);
  });

  it('is wide enough for the tick and the words, centred, with the grid step clear on each side', () => {
    expect(width(WORDS)).toBeCloseTo(51.19, 2);
    expect(onCourtTickBox(theme.type.tag.fontSize)).toBeCloseTo(6.84, 2);

    for (const size of SIZES) {
      expect(forTheWords(size) - width(WORDS)).toBeGreaterThanOrEqual(2 * theme.space.xxs);
    }
  });

  it('would clip the tick and the words at the old space.xs inset', () => {
    // The whole reason the mark moved: at `space.xs` the card panel has no room for both.
    const atOneStep = usableWidth('card', theme.space.xs) - TICK_AND_GAP;

    expect(atOneStep).toBeLessThan(width(WORDS) + 2 * theme.space.xxs);
  });

  it('clips a label flush against its own left padding', () => {
    // The other half of *centred is geometry*: the content layer's padding is one grid step,
    // and at the mark's top edge the curve has not cleared that column yet on the record
    // panel, and only just on the card's. A left-aligned mark loses its first letter to the
    // corner; a centred one takes the middle of what is left and clears both curves.
    expect(cornerInset(PHOTO_PANEL.record.width, MARK_TOP)).toBeGreaterThan(theme.space.xs);
    expect(cornerInset(PHOTO_PANEL.card.width, MARK_TOP)).toBeGreaterThan(0);
  });
});

describe('the cap', () => {
  it('is the largest step each panel leaves the words, beside a tick that does not scale', () => {
    for (const size of SIZES) {
      expect(ON_COURT_MAX_SCALE[size]).toBe(largestStepThatFits(width(WORDS), forTheWords(size)));
    }
  });

  it('is a bound rather than a freeze — the one thing Part 13 will not have', () => {
    for (const size of SIZES) {
      expect(ON_COURT_MAX_SCALE[size]).toBeGreaterThan(1);
    }
  });

  it('is the largest that does: one more step runs into the corner', () => {
    for (const size of SIZES) {
      expect(width(WORDS) * (ON_COURT_MAX_SCALE[size] + 0.1)).toBeGreaterThan(forTheWords(size));
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
  it('has no ✓ to type: Archivo does not ship one', () => {
    // U+2713. The face the app loads has no glyph for it, so a text tick renders in a
    // per-platform fallback whose advance nothing here could measure and whose weight nothing
    // here would control — ADR-0135's argument about U+26A1, one surface over. That is why the
    // tick the mark carries is drawn (`onCourtTickBox`), never typed.
    expect(archivoBold.draws(0x2713)).toBe(false);
    expect(archivoBold.draws(0x2714)).toBe(false);
    // The letters it does draw, so the assertion above is about that character rather than
    // about a font file this test failed to read.
    for (const character of WORDS.replace(' ', '')) {
      expect(archivoBold.draws(character.codePointAt(0)!)).toBe(true);
    }
  });

  it('leaves 6.8’s own 12 × 12 tick no headroom beside the words', () => {
    // `theme.size.availability.tick` is the box `shared/ui/Tick` draws into — the mark
    // family's one 12 x 12 (6.8). Even two steps down it leaves the words a cap of 1,0 at
    // best, which is `allowFontScaling={false}` under another name — the one thing Part 13
    // will not have — and that is why the mark's tick is a share of its own font size instead.
    const besideTheBigTick = usableWidth('card') - theme.size.availability.tick - theme.space.xxs;

    expect(largestStepThatFits(width(WORDS), besideTheBigTick)).toBeLessThanOrEqual(1);
  });

  it('leaves a chip inset from the corner too narrow for the words at all', () => {
    // A `Tag`-shaped shield: inset from the panel's edge by the smallest grid step, with the
    // tag's own horizontal padding inside it, at the old `space.xs` inset the designs drew it
    // at. It comes out under the word's own width, which is why *top right* is not a
    // placement the card's panel has.
    const chip = usableWidth('card', theme.space.xs) - 2 * theme.space.xxs - 2 * theme.space.xs;

    expect(chip).toBeLessThan(width(WORDS));
  });
});

/**
 * The mark's two words, and the clause a listener gets instead of them.
 *
 * They arrived here with the component that draws them, from Play's own copy deck: the record
 * sheet's header and the deck card draw the same mark, and a second copy of *On court* is a
 * second thing to keep in step with a pinned geometry test one screen up.
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
    // The Sport beneath it is uppercased by the same style rather than by its own string, and
    // the deck card lower-cases the same words after its tick. A pre-shouted constant would be
    // the one place in this deck where a style decision is spelled into the copy.
    expect(ON_COURT_MARK).not.toBe(ON_COURT_MARK.toUpperCase());
  });
});

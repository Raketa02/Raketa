/**
 * `theme.size.gameCard.footMaxScale`, the tile foot's text cap, and `tileNarrowest`, the floor it is
 * derived against — measured, not argued ([#865](https://github.com/Raketa02/Raketa/issues/865); the
 * tab menu log §6.4; design system 7.22).
 *
 * **A deck tile is a fixed box now** — one shape per court (#864) — so the design system's rule for
 * text in a fixed box applies to its foot: it *"may neither be frozen nor grow without bound"*, and
 * `maxFontSizeMultiplier` is what [Part 13](../../../../docs/design-system.md) leaves. This is the
 * tab bar's mechanism ([`tabBarLabelCap.test.ts`](../../../shared/ui/tabBarLabelCap.test.ts)) and
 * the ON COURT mark's ([`onCourtMarkFit.test.ts`](../../../shared/ui/onCourtMarkFit.test.ts)), third
 * instance: the advance widths are read out of the Archivo Bold and the IBM Plex Mono Medium that
 * ship in the bundle, never a hard-coded *"about 0,6em per character"*.
 *
 * **The tile it is derived against is the smallest the card draws**: the narrowest phone's column,
 * 128.5 wide, at the doubles shape, 73.4 tall — where a short card's tiles stop (`deckCardGeometry`).
 * Two things have to fit it, and both stop at **1.3**:
 * - **across**, every line the box never cuts — the level line at its longest, *2,71 · paid* (an
 *   IBM Plex Mono line of eleven characters), the IN and FRIEND tags beside a name, and the open
 *   seat's share figure;
 * - **down**, the tallest foot a tile draws — **a rescue's open seat**, *You complete it* over its
 *   price, 61 at 1.0 inside its dashed stroke and padding.
 *
 * **What the box cuts, as it always has**: the name (ADR-0199 §1 — whole, cut by the box), *You
 * complete it* and the open seat's price line past its figure. *You complete it* fills the narrowest
 * tile at 1.0 in both its registers — the floor holds it, and that is what makes the floor the
 * narrowest phone's column — and a cap derived over it would be 1.0, which is `allowFontScaling=
 * {false}` under another name (the ON COURT mark's Sport, 7.15): it is capped with the rest and cut
 * above. *27 zł · court booked* is wider than the narrowest tile at 1.0 already, and than every
 * column but a 412's: the figure is whole and the words after it are cut — as before this cap.
 *
 * **What makes it go red:** a longer level line or tag, another type role or weight in the foot, a
 * change to the foot's or the open seat's padding, the gutter, the card's body padding, the doubles
 * shape, or a font release that redraws the letters. None of them announces itself at 9.5pt.
 */

import { formatLevel, formatZloty } from '@/shared/formatting/ratingFormat';
import { theme } from '@/shared/ui/theme';
import {
  NARROWEST_SCREEN,
  type Face,
  largestStepThatFits,
  readFace,
  widthOf,
} from '@/test-support/fontMetrics';

import { CARD_TAG } from './CardTag';
import { BASE } from './deckCardGeometry';
import { LINE_JOIN, openSeatUnder } from './deckPresentation';
import { OPEN_SEAT, TILE_FOOT } from './GameTiles';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = PROPOSALS_COPY;
const { footMaxScale: CAP, tileNarrowest: NARROWEST, doublesTile } = theme.size.gameCard;

/** The foot's three roles — the name's and the open seat's words, the tags, and the figures. */
const NAME = theme.type.h2;
const TAG = theme.type.tag;
const FIGURE = theme.num.xs;

const archivoBold = readFace(`@expo-google-fonts/archivo/${NAME.fontFamily}.ttf`);
const plexMono = readFace(`@expo-google-fonts/ibm-plex-mono/${FIGURE.fontFamily}.ttf`);

/** The narrowest tile, at the doubles shape — the shorter of the two. */
const TILE = { width: NARROWEST, height: NARROWEST / doublesTile };

/** What a foot leaves its words across; and what an open seat does, inside its stroke. */
const FOOT_ACROSS = TILE.width - 2 * TILE_FOOT.padX;
const SEAT_ACROSS = TILE.width - 2 * OPEN_SEAT.stroke - 2 * OPEN_SEAT.pad;

/**
 * A line's width at its role's size, the role's tracking unscaled — the wider of the two readings,
 * since the tracking is negative and a platform that scales it draws the line narrower.
 */
function across(face: Face, words: string, role: { fontSize: number }, tracking = 0) {
  return {
    scaled: widthOf(face, words, role.fontSize),
    fixed: [...words].length * tracking,
  };
}

const LEVEL_LINE = `${formatLevel(2.71)}${LINE_JOIN}${COPY.paid}`;
/** A seat's share as wide as one gets: three figures and grosze. */
const WIDE_SHARE = formatZloty(19950);

const level = across(plexMono, LEVEL_LINE, FIGURE, FIGURE.letterSpacing);
const share = across(plexMono, WIDE_SHARE, FIGURE, FIGURE.letterSpacing);
/** IN and FRIEND, whole, each in its tag's padding and a step from what stands before it. */
const tags = {
  scaled:
    widthOf(archivoBold, COPY.in, TAG.fontSize) + widthOf(archivoBold, COPY.friend, TAG.fontSize),
  fixed: 2 * (2 * CARD_TAG.padX + TILE_FOOT.beside),
};

/** The open seat, down: its stroke and padding, *You complete it*, the step, and its price line. */
const seatDown = {
  scaled: NAME.lineHeight + FIGURE.lineHeight,
  fixed: 2 * OPEN_SEAT.stroke + 2 * OPEN_SEAT.pad + OPEN_SEAT.lines,
};
/** A player's foot, down: its padding, the name row — the name's line, taller than a tag — the step, the level. */
const footDown = {
  scaled: NAME.lineHeight + FIGURE.lineHeight,
  fixed: 2 * TILE_FOOT.padY + TILE_FOOT.lines,
};

const stepOf = (part: { scaled: number; fixed: number }, room: number) =>
  largestStepThatFits(part.scaled, room - part.fixed);

const at = (part: { scaled: number; fixed: number }, scale: number) =>
  part.scaled * scale + part.fixed;

describe('the faces being measured', () => {
  it('are weights the app loads, and draw every character the foot’s lines use', () => {
    expect(Object.values(theme.font.sans)).toContain(NAME.fontFamily);
    expect(TAG.fontFamily).toBe(NAME.fontFamily);
    expect(Object.values(theme.font.mono)).toContain(FIGURE.fontFamily);
    for (const character of `${LEVEL_LINE}${WIDE_SHARE}${COPY.youCompleteIt}`) {
      expect(plexMono.draws(character.codePointAt(0)!)).toBe(true);
    }
  });
});

describe('the tile the cap is derived against', () => {
  it('is the narrowest phone’s column, at the doubles shape — the smallest tile the card draws', () => {
    // A 320pt screen less two 15pt gutters, the card body's 12 either side and the 9 between.
    const column = (NARROWEST_SCREEN - 2 * theme.size.gutter - 2 * BASE.pad - BASE.across) / 2;
    expect(column).toBe(128.5);
    expect(NARROWEST).toBe(column);
    expect(TILE.height).toBeCloseTo(73.43, 2);
  });
});

describe('the cap', () => {
  it('is the largest step at which every line the box never cuts fits across, and the open seat down', () => {
    const steps = [
      stepOf(level, FOOT_ACROSS),
      stepOf(tags, FOOT_ACROSS),
      stepOf(share, SEAT_ACROSS),
      stepOf(seatDown, TILE.height),
      stepOf(footDown, TILE.height),
    ];
    expect(CAP).toBe(Math.min(...steps));
  });

  it('is held by the level line across and the open seat down, both at 1.3', () => {
    // *2,71 · paid*: 80.74 at 1.0 in a foot 110.5 across. The open seat: 61 at 1.0 in 73.43.
    expect(at(level, 1)).toBeCloseTo(80.74, 2);
    expect(at(seatDown, 1)).toBe(61);
    expect(stepOf(level, FOOT_ACROSS)).toBe(1.3);
    expect(stepOf(seatDown, TILE.height)).toBe(1.3);
  });

  it('is the largest that does: one more step runs the level line out and the open seat over', () => {
    expect(at(level, CAP + 0.1)).toBeGreaterThan(FOOT_ACROSS);
    expect(at(seatDown, CAP + 0.1)).toBeGreaterThan(TILE.height);
  });

  it('is a bound rather than a freeze', () => {
    expect(CAP).toBeGreaterThan(1);
  });

  it('never draws a word under the 9.5pt type floor: it only ever caps growth, at roles at or over it', () => {
    for (const role of [NAME, TAG, FIGURE]) expect(role.fontSize).toBeGreaterThanOrEqual(9.5);
    expect(TAG.fontSize).toBe(9.5);
  });
});

describe('the floor holds the foot', () => {
  it('fits a player’s foot and a rescue’s open seat down the narrowest tile at the cap', () => {
    // 52 and 61 at 1.0; 63.1 and 72.1 at 1.3.
    expect(at(footDown, 1)).toBe(52);
    expect(at(footDown, CAP)).toBeLessThanOrEqual(TILE.height);
    expect(at(seatDown, CAP)).toBeLessThanOrEqual(TILE.height);
  });

  it('holds *You complete it* whole at 1.0 in both its registers — the floor is what it needs', () => {
    // Your tile's, in the Level's mono: 110.1 in 110.5. The open seat's, in the name's role: 104.94
    // in 107.5. A tile any narrower would cut it at the OS's default text size.
    const yours = across(plexMono, COPY.youCompleteIt, FIGURE, FIGURE.letterSpacing);
    const seat = across(archivoBold, COPY.youCompleteIt, NAME, NAME.letterSpacing);
    expect(at(yours, 1)).toBeCloseTo(110.1, 1);
    expect(at(yours, 1)).toBeLessThanOrEqual(FOOT_ACROSS);
    expect(at(seat, 1)).toBeLessThanOrEqual(SEAT_ACROSS);
    // …and no further: its own cap would be 1.0, a freeze — so it is capped with the rest, and cut.
    expect(stepOf(yours, FOOT_ACROSS)).toBe(1);
    expect(stepOf(seat, SEAT_ACROSS)).toBe(1);
  });

  it('holds the open seat’s figure whole; the price line past it is cut, as it was before the cap', () => {
    const line = across(
      plexMono,
      openSeatUnder(formatZloty(2700), true),
      FIGURE,
      FIGURE.letterSpacing,
    );
    expect(at(share, CAP)).toBeLessThanOrEqual(SEAT_ACROSS);
    // *27 zł · court booked*, 146.8 at 1.0, against 107.5 here — and 153.5 on a 412's tile.
    expect(at(line, 1)).toBeCloseTo(146.8, 1);
    expect(at(line, 1)).toBeGreaterThan(SEAT_ACROSS);
  });
});

/**
 * The Games card's tiles and the room around them, as numbers (#864, #865; the tab menu log §2,
 * §6.2–§6.5).
 *
 * **The rooms are the evidence, not a mock.** Each phone below is the card's stage once the second
 * row of tabs is gone: the content width (the screen less two 15pt gutters) and the height the
 * decision log's §2 budget leaves the card — its doubles tile *without the row* times two, plus the
 * 288.4 the rest of a doubles card takes. The blocks are the same budget's, checked against the
 * user's A32 read over adb (a tile 160.5 × 84.3 today, the ribbon 30, the court block 71.5): the
 * ribbon 30, the *vs* line 12, the forecast row 22, the week grid 81, the court block 71 and the
 * hairline 0.4. With the paddings and the gaps that is 264.4 on singles, as the log adds it up, and
 * 288.4 on doubles, which add the *vs* line and its two 6pt gaps.
 *
 * **The grid is measured by its words** (#865): its cells shrink with the card's other boxes, so
 * the card measures only what does not — the grade over the day letters, 42 (the grade's line 20,
 * the 6 under it, the grid's 4, the letters' line 12) — and its three rows of 9pt cells, each with
 * the grid's 4 above it, are the geometry's: 39, and 81 in all.
 *
 * Every expected size is the log's own table (§6.2), or counted off it by hand in the comment
 * beside it — never recomputed the way the module computes it.
 */

import { theme } from '@/shared/ui/theme';

import {
  BASE,
  blocksLaidOut,
  cardGeometry,
  sameLength,
  tileRatio,
  type CardBlocks,
  type CardGeometry,
  type CourtShape,
  type Size,
} from './deckCardGeometry';

const BLOCKS: CardBlocks = {
  ribbon: 30,
  vs: 12,
  headline: 22,
  gridWords: 42,
  court: 71,
  hairline: 0.4,
};

const PHONES = {
  /** The smallest phone the app installs on, 320 × 568 — the card already did not fit (§2). */
  se: { width: 290, height: 276.4 },
  /** A 360 × 800 Android — the one phone where 1.75 leaves its column (§6.2). */
  small: { width: 330, height: 452.2 },
  /** The user's A32, 384 × 853 dp. */
  a32: { width: 354, height: 501.2 },
  /** A 390 × 844 iPhone. */
  iphone: { width: 360, height: 491 },
  /** A 412 × 915 Android. */
  tall: { width: 382, height: 567.2 },
} as const satisfies Record<string, Size>;

const RATIO: Readonly<Record<CourtShape, number>> = { doubles: 1.75, singles: 3 / 4 };

/**
 * **The largest OS text size React Native reports** — iOS's largest accessibility size, *AX5*, at
 * 3.571 (`fontScale`); Android's tops out at 2.0. The card's words grow with it and are measured
 * so: each block's lines at that size over its fixed paddings — the ribbon is a fixed 30, the
 * grid's 6 and 4 do not scale, and the court block keeps its 27 of padding and border, its 6
 * between the tag row and the line, and the line on one line, the least it can take.
 */
const LARGEST = 3.571;

function blocksAt(scale: number): CardBlocks {
  return {
    ribbon: 30,
    vs: 12 * scale,
    headline: 22 * scale,
    gridWords: (20 + 12) * scale + 6 + 4,
    // The tag row is the taller of the tag (12 a line, 3 above and below) and the share (17).
    court: 27 + Math.max(12 * scale + 6, 17 * scale) + 6 + 20 * scale,
    hairline: 0.4,
  };
}

const geometry = (stage: Size, court: CourtShape, blocks: CardBlocks = BLOCKS) =>
  cardGeometry({ stage, shape: court, blocks });

/**
 * The card's column, top to bottom, as the card draws it from these numbers: the ribbon, the body's
 * padding, the tiles and the *vs* line, the versions line, the hairline in its gap, the forecast,
 * the grid's words and its three rows of cells, and the court block.
 */
function drawnHeight(court: CourtShape, blocks: CardBlocks, at: CardGeometry): number {
  const tiles =
    court === 'doubles'
      ? 2 * at.tiles.height + 2 * at.tiles.aroundVs + (blocks.vs ?? 0)
      : at.tiles.height;
  const cells = 3 * (9 + 4) * at.scale;
  return (
    blocks.ribbon +
    2 * at.padY +
    tiles +
    (blocks.versions === undefined ? 0 : at.underTiles + blocks.versions) +
    2 * at.aroundHair +
    blocks.hairline +
    (blocks.headline === undefined ? 0 : blocks.headline + at.between) +
    blocks.gridWords +
    cells +
    at.between +
    blocks.court
  );
}

describe('the tile keeps its shape', () => {
  it.each(Object.entries(PHONES))('on %s, at 1.75 : 1 for doubles and 3:4 for singles', (_, at) => {
    for (const court of ['doubles', 'singles'] as const) {
      for (const blocks of [BLOCKS, blocksAt(LARGEST)]) {
        const { tiles } = geometry(at, court, blocks);
        expect(tiles.width / tiles.height).toBeCloseTo(RATIO[court], 6);
      }
    }
  });

  it('carries the shapes as theme values — the details’ 1.75 named for both screens, and 3:4', () => {
    expect(theme.size.gameCard.doublesTile).toBe(1.75);
    expect(theme.size.gameCard.singlesTile).toBe(3 / 4);
    // The shape a tile stands at before the card is laid out.
    expect(tileRatio('doubles')).toBe(1.75);
    expect(tileRatio('singles')).toBe(3 / 4);
  });
});

describe('the sizes are the log’s, for the same room (§6.2)', () => {
  it.each([
    // phone, doubles w × h, singles w × h — the table in #864 and the log's §6.2, where the tiles
    // fill their column
    ['a32', [160.5, 92], [160.5, 214]],
    ['iphone', [163.5, 93], [163.5, 218]],
    ['tall', [174.5, 100], [174.5, 233]],
  ] as const)('on %s', (phone, doubles, singles) => {
    const two = geometry(PHONES[phone], 'doubles').tiles;
    const one = geometry(PHONES[phone], 'singles').tiles;
    expect(two.width).toBeCloseTo(doubles[0], 0);
    expect(two.height).toBeCloseTo(doubles[1], 0);
    expect(one.width).toBeCloseTo(singles[0], 0);
    expect(one.height).toBeCloseTo(singles[1], 0);
  });
});

describe('width-bound by default', () => {
  it.each([
    ['a32', 'doubles'],
    ['a32', 'singles'],
    ['iphone', 'doubles'],
    ['iphone', 'singles'],
    ['tall', 'doubles'],
    ['tall', 'singles'],
  ] as const)(
    'on %s, %s tiles are as wide as their column, and nothing shrinks',
    (phone, court) => {
      const at = geometry(PHONES[phone], court);
      expect(at.bound).toBe('width');
      expect(at.scale).toBe(1);
      expect(at.tiles.inset).toBe(0);
      expect(at.padY).toBe(BASE.pad);
    },
  );
});

describe('short room shrinks every box in proportion, and never a word (§6.5)', () => {
  it('on a 360 Android the tiles, the paddings, the gaps and the grid’s cells give up the same share', () => {
    // Doubles. The words take 30 + 12 + 0.4 + 22 + 42 + 71 = 177.4 and never shrink; the boxes take
    // the paddings 24, the vs gaps 12, the hairline's 18, the grid's and the court's 9 + 9, the
    // cells 39 and two tiles 148.5 / 1.75 = 84.86 each: 280.71 at rest. The stage leaves them
    // 452.2 − 177.4 = 274.8 — 0.9789 of it.
    const at = geometry(PHONES.small, 'doubles');
    expect(at.bound).toBe('height');
    expect(at.scale).toBeCloseTo(0.9789, 4);
    expect(at.tiles.height).toBeCloseTo(83.07, 2);
    expect(at.tiles.width).toBeCloseTo(145.37, 2);
    expect(at.padY / BASE.pad).toBeCloseTo(at.scale, 6);
    expect(at.tiles.aroundVs / BASE.aroundVs).toBeCloseTo(at.scale, 6);
    expect(at.aroundHair / BASE.aroundHair).toBeCloseTo(at.scale, 6);
    expect(at.between / BASE.between).toBeCloseTo(at.scale, 6);
    expect(drawnHeight('doubles', BLOCKS, at)).toBeCloseTo(PHONES.small.height, 6);
  });

  it('and singles the same way: 286.8 of 297 at rest, 0.9657', () => {
    // The words: 30 + 0.4 + 22 + 42 + 71 = 165.4. The boxes: 24 + 18 + 18 + 39 + 198 = 297.
    const at = geometry(PHONES.small, 'singles');
    expect(at.bound).toBe('height');
    expect(at.scale).toBeCloseTo(0.9657, 4);
    expect(at.tiles.width).toBeCloseTo(143.4, 1);
    expect(at.tiles.height).toBeCloseTo(191.2, 1);
    expect(drawnHeight('singles', BLOCKS, at)).toBeCloseTo(PHONES.small.height, 6);
  });

  it('keeps a shrunk tile centred in its column, which does not narrow', () => {
    for (const court of ['doubles', 'singles'] as const) {
      const at = geometry(PHONES.small, court);
      expect(at.tiles.width + 2 * at.tiles.inset).toBeCloseTo(148.5, 6);
      expect(at.tiles.across).toBe(BASE.across);
      // The sides are the card's width, which the room does not take: only its height is short.
      expect(at.padX).toBe(BASE.pad);
    }
  });

  it('keeps the words at their size: every text block is drawn as measured, at any text size', () => {
    // The card's height is its boxes, shrunk, and its words as laid out — so a card that fills its
    // stage with the blocks it was given has scaled nothing it was given.
    for (const blocks of [BLOCKS, { ...BLOCKS, court: 81, versions: 12.5 }]) {
      const at = geometry(PHONES.small, 'doubles', blocks);
      expect(at.scale).toBeLessThan(1);
      expect(drawnHeight('doubles', blocks, at)).toBeCloseTo(PHONES.small.height, 6);
    }
  });

  it('a taller block leaves the boxes less room', () => {
    // Ten more for the court line: 264.8 of 280.71, 0.9433 — a tile 84.86 × 0.9433 = 80.05.
    const wrapped = geometry(PHONES.small, 'doubles', { ...BLOCKS, court: 81 });
    expect(wrapped.tiles.height).toBeCloseTo(80.05, 2);
  });
});

describe('the floor: the narrowest tile, which the foot fills at its cap (§6.4)', () => {
  it('is the narrowest phone’s column, at the tile’s shape — the theme’s, and no height of its own', () => {
    // (320 − 2 × 15 − 2 × 12 − 9) / 2 = 128.5: 73.43 tall on doubles, 171.33 on singles.
    expect(theme.size.gameCard.tileNarrowest).toBe(128.5);
    expect(theme.size.gameCard).not.toHaveProperty('tileMin');
  });

  it('stops a 360 Android’s tiles at 128.5 wide, every box at the same share, where the words grow', () => {
    // At the largest text size the words take more than the stage: the boxes stop at the share
    // that leaves the tiles their floor, 128.5 / 148.5 = 0.8653, and the card is taller than its
    // stage — the deck scrolls.
    for (const court of ['doubles', 'singles'] as const) {
      const at = geometry(PHONES.small, court, blocksAt(LARGEST));
      expect(at.bound).toBe('floor');
      expect(at.tiles.width).toBeCloseTo(128.5, 6);
      expect(at.scale).toBeCloseTo(0.8653, 4);
      expect(at.between / BASE.between).toBeCloseTo(at.scale, 6);
      expect(drawnHeight(court, blocksAt(LARGEST), at)).toBeCloseTo(at.least, 6);
      expect(at.least).toBeGreaterThan(PHONES.small.height);
    }
  });

  it('is the same tile at every text size — the foot is capped, so its words never ask for more', () => {
    for (const phone of Object.values(PHONES)) {
      const two = geometry(phone, 'doubles', blocksAt(LARGEST)).tiles;
      expect(two.width).toBeCloseTo(128.5, 6);
      expect(two.height).toBeCloseTo(73.43, 2);
      expect(geometry(phone, 'singles', blocksAt(LARGEST)).tiles.height).toBeCloseTo(171.33, 2);
    }
  });

  it('leaves the narrowest phone nothing to shrink: its tiles are already at their floor', () => {
    // A 320's column is the floor itself, so the card stands at rest and is taller than its stage:
    // 288.4 + 2 × 73.43 = 435.26 on doubles, 264.4 + 171.33 = 435.73 on singles, against 276.4.
    const two = geometry(PHONES.se, 'doubles');
    const one = geometry(PHONES.se, 'singles');
    expect(two.bound).toBe('floor');
    expect(one.bound).toBe('floor');
    expect(two.scale).toBe(1);
    expect(two.tiles).toMatchObject({ width: 128.5, inset: 0 });
    expect(two.tiles.height).toBeCloseTo(73.43, 2);
    expect(one.tiles.height).toBeCloseTo(171.33, 2);
    expect(two.least).toBeCloseTo(435.26, 2);
    expect(one.least).toBeCloseTo(435.73, 2);
    expect(two.between).toBe(BASE.between);
  });

  it('never draws a tile wider than its column, even where the column is narrower than the floor', () => {
    // A narrow, short window — split screen: a column of (210 − 33) / 2 = 88.5, so a doubles tile
    // as wide as it is 50.6 tall, under the floor. The column wins: tiles that overlapped would be
    // worse than a tile under the floor.
    const narrow = { width: 210, height: 300 };
    for (const court of ['doubles', 'singles'] as const) {
      const { tiles } = geometry(narrow, court);
      expect(tiles.inset).toBe(0);
      expect(tiles.width).toBeCloseTo(88.5, 6);
      expect(tiles.width / tiles.height).toBeCloseTo(RATIO[court], 6);
    }
    expect(geometry({ width: 210, height: 600 }, 'doubles').tiles.height).toBeCloseTo(50.57, 2);
  });
});

describe('the card’s least height, and where the deck scrolls (§6.5)', () => {
  it('is the card with its tiles at their floor and every box at that share', () => {
    // A 360 doubles card: 177.4 of words and 280.71 of boxes × 0.8653 = 420.31.
    expect(geometry(PHONES.small, 'doubles').least).toBeCloseTo(420.31, 2);
    // A card that fits says so too: its least is under its stage.
    expect(geometry(PHONES.a32, 'doubles').least).toBeLessThan(PHONES.a32.height);
  });

  it.each([
    ['se', true],
    ['small', false],
    ['a32', false],
    ['iphone', false],
    ['tall', false],
  ] as const)('at 1.0, the base card on %s scrolls: %s', (phone, scrolls) => {
    // The base card: no weekly-cap line over the stage and no *N people are In* line on it.
    for (const court of ['doubles', 'singles'] as const) {
      const at = geometry(PHONES[phone], court);
      expect(at.bound === 'floor').toBe(scrolls);
      expect(at.least > PHONES[phone].height).toBe(scrolls);
    }
  });

  it('at the largest text size, every phone scrolls', () => {
    for (const phone of Object.values(PHONES)) {
      for (const court of ['doubles', 'singles'] as const) {
        const at = geometry(phone, court, blocksAt(LARGEST));
        expect(at.bound).toBe('floor');
        expect(at.least).toBeGreaterThan(phone.height);
      }
    }
  });

  it('does not depend on the stage’s height — the deck can lay the stage out at it', () => {
    const at = geometry(PHONES.se, 'doubles');
    expect(geometry({ ...PHONES.se, height: at.least }, 'doubles').least).toBe(at.least);
    // And the card drawn at its least fills it exactly.
    const there = geometry({ ...PHONES.se, height: at.least }, 'doubles');
    expect(drawnHeight('doubles', BLOCKS, there)).toBeCloseTo(at.least, 6);
  });
});

describe('a block measured again', () => {
  // The A32's scale, 1.875: a pixel is 0.533pt.
  const PIXEL = 1 / 1.875;

  it('is the same block where it moved by less than a pixel’s rounding', () => {
    // A block moved by the gaps lands on another fraction of a pixel, and Yoga rounds its top and
    // its bottom: the same 71pt court block reads 133 pixels or 134 (70.93 or 71.47) — never more
    // than a pixel apart.
    expect(sameLength(133 * PIXEL, 134 * PIXEL, PIXEL)).toBe(true);
    expect(sameLength(71, 71, PIXEL)).toBe(true);
  });

  it('is a new height where it grew by more — a line wrapping, a larger text size', () => {
    expect(sameLength(71, 81, PIXEL)).toBe(false);
    expect(sameLength(71, 72.2, PIXEL)).toBe(false);
  });

  it('is new where it had never been measured', () => {
    expect(sameLength(undefined, 71, PIXEL)).toBe(false);
  });
});

describe('spare height is spread evenly between the card’s blocks (§6.3)', () => {
  it('a doubles card shares it across its five gaps, and still fills its stage', () => {
    // A32: 501.2 − 288.4 − 2 × 91.71 = 29.37 to spare, 5.87 to each gap: the tiles and the vs line
    // twice, the tiles and the forecast (the hairline in its middle), the forecast and the grid,
    // the grid and the court block.
    const at = geometry(PHONES.a32, 'doubles');
    const grown = [
      at.tiles.aroundVs - BASE.aroundVs,
      at.tiles.aroundVs - BASE.aroundVs,
      2 * (at.aroundHair - BASE.aroundHair),
      at.between - BASE.between,
      at.between - BASE.between,
    ];
    for (const share of grown) expect(share).toBeCloseTo(5.87, 2);
    expect(drawnHeight('doubles', BLOCKS, at)).toBeCloseTo(PHONES.a32.height, 6);
  });

  it('a singles card shares it across its three', () => {
    // 412 × 915: 567.2 − 264.4 − 232.67 = 70.13 to spare, 23.38 to each gap.
    const at = geometry(PHONES.tall, 'singles');
    expect(2 * (at.aroundHair - BASE.aroundHair)).toBeCloseTo(23.38, 2);
    expect(at.between - BASE.between).toBeCloseTo(23.38, 2);
    expect(drawnHeight('singles', BLOCKS, at)).toBeCloseTo(PHONES.tall.height, 6);
  });

  it('nothing stretches: the tiles are the same size on a taller card, and only the gaps grow', () => {
    const taller = { ...PHONES.a32, height: PHONES.a32.height + 100 };
    expect(geometry(taller, 'doubles').tiles.height).toBe(
      geometry(PHONES.a32, 'doubles').tiles.height,
    );
    expect(
      geometry(taller, 'doubles').between - geometry(PHONES.a32, 'doubles').between,
    ).toBeCloseTo(20, 6);
  });

  it('keeps the versions line under the tiles at its own gap, and the card the stage’s height', () => {
    const versions: CardBlocks = { ...BLOCKS, versions: 12.5 };
    for (const phone of [PHONES.iphone, PHONES.tall]) {
      for (const court of ['doubles', 'singles'] as const) {
        const at = geometry(phone, court, versions);
        // Never a share of the spare: its gap at rest, or shrunk with the rest — on a 390 iPhone
        // the line's 21.5 tips a doubles card into shrinking (475.26 + 21.5 > 491).
        expect(at.underTiles).toBeCloseTo(BASE.underTiles * at.scale, 6);
        expect(drawnHeight(court, versions, at)).toBeCloseTo(phone.height, 6);
      }
    }
    expect(geometry(PHONES.tall, 'doubles', versions).underTiles).toBe(BASE.underTiles);
  });

  it('shares it across one gap fewer where no forecast is drawn', () => {
    // A32 doubles, no forecast row: 501.2 − 288.4 + 22 + 9 − 183.43 = 60.37 to spare, over four.
    const bare: CardBlocks = { ribbon: 30, vs: 12, gridWords: 42, court: 71, hairline: 0.4 };
    const at = geometry(PHONES.a32, 'doubles', bare);
    expect(at.between - BASE.between).toBeCloseTo(15.09, 2);
    expect(at.tiles.aroundVs - BASE.aroundVs).toBeCloseTo(15.09, 2);
    expect(drawnHeight('doubles', bare, at)).toBeCloseTo(PHONES.a32.height, 6);
  });

  it('gives every card on one stage the stage’s height, whatever its blocks — the stack stays one size', () => {
    const wrapped: CardBlocks = { ...BLOCKS, court: 81, versions: 12.5 };
    for (const blocks of [BLOCKS, wrapped]) {
      expect(
        drawnHeight('doubles', blocks, geometry(PHONES.iphone, 'doubles', blocks)),
      ).toBeCloseTo(PHONES.iphone.height, 6);
    }
  });
});

describe('the card is sized once every block it draws has been laid out', () => {
  const LAID = { ribbon: 30, vs: 12, headline: 22, gridWords: 42, court: 71 };
  const DOUBLES = { shape: 'doubles', versions: false, headline: true } as const;

  it('waits for each block the card draws', () => {
    for (const part of Object.keys(LAID) as (keyof typeof LAID)[]) {
      const { [part]: _late, ...answered } = LAID;
      expect(blocksLaidOut(answered, DOUBLES, 0.4)).toBeUndefined();
    }
    expect(blocksLaidOut(LAID, DOUBLES, 0.4)).toEqual(BLOCKS);
  });

  it('waits for the versions line only where it is drawn, and counts it only then', () => {
    expect(blocksLaidOut(LAID, { ...DOUBLES, versions: true }, 0.4)).toBeUndefined();
    expect(blocksLaidOut({ ...LAID, versions: 12.5 }, { ...DOUBLES, versions: true }, 0.4)).toEqual(
      { ...BLOCKS, versions: 12.5 },
    );
    // A line drawn once and gone since: its last height is not the card's any more.
    expect(blocksLaidOut({ ...LAID, versions: 12.5 }, DOUBLES, 0.4)).toEqual(BLOCKS);
  });

  it('never waits for a vs line on singles, or a forecast row on a card that draws none', () => {
    const { vs: _vs, headline: _headline, ...singles } = LAID;
    expect(
      blocksLaidOut(singles, { shape: 'singles', versions: false, headline: false }, 0.4),
    ).toEqual({ ribbon: 30, gridWords: 42, court: 71, hairline: 0.4 });
  });
});

describe('the card’s width', () => {
  it('a wider stage is wider tiles: the column is the stage less the padding and the gap', () => {
    // (382 − 24 − 9) / 2 = 174.5, the 412's column.
    expect(geometry(PHONES.tall, 'doubles').tiles.width).toBeCloseTo(174.5, 6);
    expect(geometry(PHONES.tall, 'doubles').tiles.across).toBe(theme.space.sm);
    expect(geometry(PHONES.tall, 'doubles').padX).toBe(theme.space.md);
  });
});

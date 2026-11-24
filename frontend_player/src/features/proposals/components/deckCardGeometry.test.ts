/**
 * The Games card's tiles and the room around them, as numbers (#864; the tab menu log §2, §6.2,
 * §6.3).
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

const BLOCKS: CardBlocks = { ribbon: 30, vs: 12, headline: 22, grid: 81, court: 71, hairline: 0.4 };

const PHONES = {
  /** The smallest phone the app installs on — the card already did not fit (§2). */
  se: { width: 290, height: 276.4 },
  /** A 360 Android — the one phone where 1.75 leaves its column (§6.2). */
  small: { width: 330, height: 452.2 },
  /** The user's A32, 384 × 853 dp. */
  a32: { width: 354, height: 501.2 },
  /** A 390 iPhone. */
  iphone: { width: 360, height: 491 },
  /** A 412 × 915 Android. */
  tall: { width: 382, height: 567.2 },
} as const satisfies Record<string, Size>;

const RATIO: Readonly<Record<CourtShape, number>> = { doubles: 1.75, singles: 3 / 4 };

const geometry = (stage: Size, court: CourtShape, blocks: CardBlocks = BLOCKS) =>
  cardGeometry({ stage, shape: court, blocks });

/**
 * The card's column, top to bottom, as the card draws it from these numbers: the ribbon, the body's
 * padding, the tiles and the *vs* line, the versions line, the hairline in its gap, the forecast,
 * the grid and the court block.
 */
function drawnHeight(court: CourtShape, blocks: CardBlocks, at: CardGeometry): number {
  const tiles =
    court === 'doubles'
      ? 2 * at.tiles.height + 2 * at.tiles.aroundVs + (blocks.vs ?? 0)
      : at.tiles.height;
  return (
    blocks.ribbon +
    2 * at.pad +
    tiles +
    (blocks.versions === undefined ? 0 : at.underTiles + blocks.versions) +
    2 * at.aroundHair +
    blocks.hairline +
    (blocks.headline === undefined ? 0 : blocks.headline + at.between) +
    blocks.grid +
    at.between +
    blocks.court
  );
}

describe('the tile keeps its shape', () => {
  it.each(Object.entries(PHONES))('on %s, at 1.75 : 1 for doubles and 3:4 for singles', (_, at) => {
    for (const court of ['doubles', 'singles'] as const) {
      const { tiles } = geometry(at, court);
      expect(tiles.width / tiles.height).toBeCloseTo(RATIO[court], 6);
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
    // phone, doubles w × h, singles w × h — the table in #864 and the log's §6.2
    ['small', [143, 82], [141, 188]],
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

describe('width-bound by default, height-bound where the height runs out', () => {
  it.each([
    ['a32', 'doubles'],
    ['a32', 'singles'],
    ['iphone', 'doubles'],
    ['iphone', 'singles'],
    ['tall', 'doubles'],
    ['tall', 'singles'],
  ] as const)('on %s, %s tiles are as wide as their column', (phone, court) => {
    const at = geometry(PHONES[phone], court);
    expect(at.bound).toBe('width');
    expect(at.tiles.inset).toBe(0);
  });

  it('on a 360 Android both shapes are height-bound, narrower and centred in their columns', () => {
    // A column is (330 − 2 × 12 − 9) / 2 = 148.5. Doubles: the room is (452.2 − 288.4) / 2 = 81.9
    // a tile, against the 84.9 its width would want; singles: 187.8 against 198.
    for (const court of ['doubles', 'singles'] as const) {
      const at = geometry(PHONES.small, court);
      expect(at.bound).toBe('height');
      expect(at.tiles.width).toBeLessThan(148.5);
      expect(at.tiles.width + 2 * at.tiles.inset).toBeCloseTo(148.5, 6);
    }
    // 143.3 wide in 148.5: 2.6 either side.
    expect(geometry(PHONES.small, 'doubles').tiles.inset).toBeCloseTo(2.59, 2);
  });

  it('a height-bound card has nothing left over, so its gaps stay at rest', () => {
    const at = geometry(PHONES.small, 'doubles');
    expect(at.tiles.aroundVs).toBe(BASE.aroundVs);
    expect(at.aroundHair).toBe(BASE.aroundHair);
    expect(at.between).toBe(BASE.between);
    expect(drawnHeight('doubles', BLOCKS, at)).toBeCloseTo(PHONES.small.height, 6);
  });

  it('never shrinks a tile below today’s floor, where the card does not fit at all (320 × 568)', () => {
    // A doubles tile would get (276.4 − 288.4) / 2 = −6; a singles tile 12. Both stop at 54, at
    // their shape: 94.5 and 40.5 wide, centred in a 128.5 column.
    const two = geometry(PHONES.se, 'doubles');
    const one = geometry(PHONES.se, 'singles');
    expect(two.bound).toBe('floor');
    expect(one.bound).toBe('floor');
    expect(two.tiles).toMatchObject({ height: 54, width: 94.5, inset: 17 });
    expect(one.tiles).toMatchObject({ height: 54, width: 40.5, inset: 44 });
    expect(two.between).toBe(BASE.between);
  });

  it('never draws a tile wider than its column, even where the column is narrower than the floor', () => {
    // A narrow, short window — split screen: a column of (210 − 33) / 2 = 88.5, so a doubles tile
    // as wide as it is 50.6 tall, under the floor. The column wins: tiles that overlapped would be
    // worse than a tile under 54.
    const narrow = { width: 210, height: 300 };
    for (const court of ['doubles', 'singles'] as const) {
      const { tiles } = geometry(narrow, court);
      expect(tiles.inset).toBeGreaterThanOrEqual(0);
      expect(tiles.width).toBeLessThanOrEqual(88.5);
      expect(tiles.width / tiles.height).toBeCloseTo(RATIO[court], 6);
    }
    expect(geometry({ width: 210, height: 600 }, 'doubles').tiles.height).toBeCloseTo(50.57, 2);
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
    for (const court of ['doubles', 'singles'] as const) {
      const at = geometry(PHONES.iphone, court, versions);
      expect(at.underTiles).toBe(BASE.underTiles);
      expect(drawnHeight(court, versions, at)).toBeCloseTo(PHONES.iphone.height, 6);
    }
  });

  it('shares it across one gap fewer where no forecast is drawn', () => {
    // A32 doubles, no forecast row: 501.2 − 288.4 + 22 + 9 − 183.43 = 60.37 to spare, over four.
    const bare: CardBlocks = { ribbon: 30, vs: 12, grid: 81, court: 71, hairline: 0.4 };
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
  const LAID = { ribbon: 30, vs: 12, headline: 22, grid: 81, court: 71 };
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
    ).toEqual({ ribbon: 30, grid: 81, court: 71, hairline: 0.4 });
  });
});

describe('the measured blocks are what the room is', () => {
  it('a taller block leaves the tiles less room, on a card that was height-bound', () => {
    const wrapped = geometry(PHONES.small, 'doubles', { ...BLOCKS, court: 81 });
    // Ten more for the court line leaves (452.2 − 298.4) / 2 = 76.9 a tile.
    expect(wrapped.tiles.height).toBeCloseTo(76.9, 6);
  });

  it('a wider stage is wider tiles: the column is the stage less the padding and the gap', () => {
    // (382 − 24 − 9) / 2 = 174.5, the 412's column.
    expect(geometry(PHONES.tall, 'doubles').tiles.width).toBeCloseTo(174.5, 6);
    expect(geometry(PHONES.tall, 'doubles').tiles.across).toBe(theme.space.sm);
    expect(geometry(PHONES.tall, 'doubles').pad).toBe(theme.space.md);
  });
});

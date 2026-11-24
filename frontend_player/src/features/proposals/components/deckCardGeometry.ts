/**
 * **The Games card's room, as numbers** — how big its tiles are, where the height they leave goes,
 * and how short the card may get before the deck scrolls
 * ([#864](https://github.com/Raketa02/Raketa/issues/864), [#865](https://github.com/Raketa02/Raketa/issues/865);
 * the tab menu log §6.2–§6.5; design system 7.22). No React in any of it: the card measures, this
 * decides, and `deckCardGeometry.test` holds it to the phones the decision was made on.
 *
 * ## One shape per court, and nothing stretches
 *
 * A tile used to take whatever height the card left it, so its shape changed from phone to phone —
 * 1.90 : 1 on the user's A32, which showed 32pt of face above the name strip. Now it has one shape:
 * **1.75 : 1 on doubles** (`doublesTile`, the details' own) and **3:4 on singles** (`singlesTile`,
 * the photo's crop), the theme's two values and the evidence for them. **Width-bound by default**:
 * a tile is as wide as its column — half the stage less the body's padding and the gap between the
 * two.
 *
 * ## Short room shrinks every box in proportion, and never a word
 *
 * Where the card's height runs out, **its boxes give up the same share of themselves** (`scale`):
 * the tiles at their shape — narrower, and centred in their column (`inset` either side) — the
 * body's padding above and below, every gap between the blocks, and the week grid's cells with the
 * gaps between them, so a cell keeps its shape. **Its words keep their size**: the ribbon, the *vs*
 * line, the forecast or vibe row, the grid's grade and day letters, the court block and the versions
 * line are measured as laid out and passed through as they are, so nothing here can draw a word
 * smaller than its role — none of which is under the 9.5pt type floor — and the tile's own words
 * are capped (`footMaxScale`), never shrunk. The card's sides are its width, which the room does not
 * take: they stay at rest, and so does the gap between two tiles.
 *
 * ## The floor is the narrowest tile, which the foot fills at its cap
 *
 * A tile shrinks no narrower than **`tileNarrowest`** — the narrowest phone's column, 128.5 — at its
 * shape: 73.4 tall on doubles, 171.3 on singles. It is **what the tile's own words need at their
 * cap**, and nothing fixed beside them (it replaced `tileMin`, 54, which was already shorter than a
 * rescue's open seat): the tile foot's cap is derived against this very tile (`gameTileFoot.test`),
 * the largest step at which the level line, the tags and the open seat's figure still fit across it
 * and a rescue's open seat — the tallest foot there is — still fits down it. So the floor does not
 * move with the OS text size: past the cap the foot does not grow, and up to it the foot fits. Where
 * the tiles reach it the other boxes stop at the same share, and the card is as short as it gets.
 *
 * **The column caps even the floor**: in a window narrower than any phone (split screen) a tile is
 * as wide as its column and no wider, under the floor if it must, since tiles that overlapped would
 * be worse.
 *
 * ## Where even that does not fit, the deck scrolls
 *
 * **`least`** is the card with its tiles at their floor and every other box at that share — the
 * least height it is ever drawn at, whatever its stage. Where the stage is shorter (`bound`
 * `floor`) the deck lays the stage out at it and its scroller scrolls, the buttons below the card.
 * It does not depend on the stage's height, so the stage laid out at it gives the same answer and
 * the card fills it exactly. In practice: a 320 × 568 phone, whose column is the floor itself, and
 * the largest text sizes, whose words take the room the boxes would have had.
 *
 * ## The rest of the room is shared evenly
 *
 * On a tall phone a width-bound tile leaves height over. It goes **in equal shares into the gaps
 * between the card's blocks** — the tiles, the *vs* line, the forecast or Social vibe row, the week
 * grid and the court block — so the card still fills its stage, which the three-card stack needs
 * (`DeckStage`), and no box grows. The hairline sits in the middle of its gap, half the share either
 * side. *4 people are In on this game* is a caption to the tiles and stays at its own gap under them.
 *
 * ## A block is measured again only when it changes by more than a pixel
 *
 * Yoga rounds a block's top and bottom to the phone's pixels, so a block the gaps moved can report a
 * height a pixel off what it reported before, which would move the gaps again. Two measurements
 * within a pixel and a half are one height (`sameLength`); a real change — a line wrapping, a larger
 * text size — is a line of text, many pixels.
 *
 * ## The blocks are measured, never assumed
 *
 * The ribbon, the *vs* line, the forecast or vibe row, the grid's words, the court block and the
 * versions line are words, and their height is the OS text size's and the line's wrap. The card lays
 * them out and hands their heights in; nothing here knows a type role. **The grid is measured by its
 * words alone** — the grade over the day letters — because its cells are this module's to shrink:
 * a row of `cell` for each range of the day, each with `cellGap` above it, as `OverlapGrid` draws
 * them.
 */

import { theme } from '@/shared/ui/theme';

import { DAY_RANGES } from '../domain/vocabulary';

/** How many stand on a side: two tiles a side in two rows, or one a side in one row. */
export type CourtShape = 'doubles' | 'singles';

export interface Size {
  readonly width: number;
  readonly height: number;
}

/** The heights of the card's blocks, as the card laid them out. */
export interface CardBlocks {
  readonly ribbon: number;
  /** The *vs* line between the two rows — doubles only. */
  readonly vs?: number;
  /** *4 people are In on this game*, where the card draws it. */
  readonly versions?: number;
  /** The forecast, or the Social vibe row, where the card draws one. */
  readonly headline?: number;
  /** The week grid's words — its grade over its day letters. Its cells are this module's. */
  readonly gridWords: number;
  readonly court: number;
  /** The rule above the forecast — the phone's hairline. */
  readonly hairline: number;
}

/** What the card is sized from: its stage, its court's shape, and its measured blocks. */
export interface CardRoom {
  readonly stage: Size;
  readonly shape: CourtShape;
  readonly blocks: CardBlocks;
}

/**
 * What stopped the tiles: their column's **width**, the card's **height** — every box shrunk to fit
 * it — or the **floor**: the card does not fit at all, and stands at its `least`, taller than its
 * stage.
 */
export type TileBound = 'width' | 'height' | 'floor';

/** The tiles, and the two gaps inside the tiles' block. */
export interface TileGeometry {
  readonly width: number;
  readonly height: number;
  /** How far a tile stands in from each side of its column — nought unless shrunk. */
  readonly inset: number;
  /** Between the two tiles of a row. */
  readonly across: number;
  /** Between a row and the *vs* line, above it and below it. */
  readonly aroundVs: number;
}

export interface CardGeometry {
  readonly bound: TileBound;
  /**
   * The share of its size at rest every box on the card is drawn at — the tiles, the padding above
   * and below, the gaps, the grid's cells — 1 unless the room is short. Never a word's.
   */
  readonly scale: number;
  readonly tiles: TileGeometry;
  /** The body's padding at its sides — the card's width, which the room never takes. */
  readonly padX: number;
  /** The body's padding above the tiles and under the court block. */
  readonly padY: number;
  /** Between the tiles and *4 people are In on this game*. */
  readonly underTiles: number;
  /** Either side of the hairline, between the tiles and the forecast. */
  readonly aroundHair: number;
  /** Between the forecast and the grid, and between the grid and the court block. */
  readonly between: number;
  /**
   * The least height the card is drawn at: its tiles at their floor and every box at that share.
   * Where the stage is shorter, the deck scrolls (see the module note).
   */
  readonly least: number;
}

/** The card's gaps at rest — what each is before any spare height reaches it, or any shrinking. */
export const BASE = {
  pad: theme.space.md,
  across: theme.space.sm,
  aroundVs: theme.space.xs,
  underTiles: theme.space.sm,
  aroundHair: theme.space.sm,
  between: theme.space.sm,
} as const;

const RATIO: Readonly<Record<CourtShape, number>> = {
  doubles: theme.size.gameCard.doublesTile,
  singles: theme.size.gameCard.singlesTile,
};

const ROWS: Readonly<Record<CourtShape, number>> = { doubles: 2, singles: 1 };

/**
 * The grid's rows of cells, one for each range of the day, each with the grid's gap above it —
 * `OverlapGrid`'s drawing.
 */
const GRID_CELLS = DAY_RANGES.length * (theme.size.gameCard.cell + theme.size.gameCard.cellGap);

/** A tile's width over its height on this court — the theme's, with its evidence. */
export function tileRatio(shape: CourtShape): number {
  return RATIO[shape];
}

/**
 * Whether a block measured again is the height it was — within the pixel and a half that Yoga's
 * rounding can move it by (see the module note). `pixel` is one physical pixel, in points.
 */
export function sameLength(was: number | undefined, now: number, pixel: number): boolean {
  return was !== undefined && Math.abs(now - was) < 1.5 * pixel;
}

/** A block of the card whose height the card measures. */
export type MeasuredBlock = 'ribbon' | 'vs' | 'versions' | 'headline' | 'gridWords' | 'court';

/** Which of the optional blocks this card draws — and so waits for. */
export interface DrawnBlocks {
  readonly shape: CourtShape;
  readonly versions: boolean;
  readonly headline: boolean;
}

/**
 * The card's blocks, **once every block it draws has been laid out** — or nothing yet. A block it
 * does not draw is neither waited for nor counted, even where an earlier drawing measured one.
 */
export function blocksLaidOut(
  heights: Readonly<Partial<Record<MeasuredBlock, number>>>,
  drawn: DrawnBlocks,
  hairline: number,
): CardBlocks | undefined {
  const { ribbon, vs, versions, headline, gridWords, court } = heights;
  if (ribbon === undefined || gridWords === undefined || court === undefined) return undefined;
  if (drawn.shape === 'doubles' && vs === undefined) return undefined;
  if (drawn.versions && versions === undefined) return undefined;
  if (drawn.headline && headline === undefined) return undefined;
  return {
    ribbon,
    gridWords,
    court,
    hairline,
    ...(drawn.shape === 'doubles' && vs !== undefined ? { vs } : {}),
    ...(drawn.versions && versions !== undefined ? { versions } : {}),
    ...(drawn.headline && headline !== undefined ? { headline } : {}),
  };
}

/** The tiles' size, every gap on the card and its least height, for this room — see the module note. */
export function cardGeometry({ stage, shape, blocks }: CardRoom): CardGeometry {
  const ratio = RATIO[shape];
  const rows = ROWS[shape];
  const doubles = shape === 'doubles';
  const forecast = blocks.headline !== undefined;
  const versions = blocks.versions !== undefined;

  // The words: drawn as measured, at any size of the boxes around them.
  const words =
    blocks.ribbon +
    (doubles ? (blocks.vs ?? 0) : 0) +
    (blocks.versions ?? 0) +
    blocks.hairline +
    (blocks.headline ?? 0) +
    blocks.gridWords +
    blocks.court;

  const column = (stage.width - 2 * BASE.pad - BASE.across) / 2;
  const tileAtRest = column / ratio;

  // The boxes at rest, with the tiles as wide as their column: what `scale` is a share of.
  const boxes =
    2 * BASE.pad +
    (doubles ? 2 * BASE.aroundVs : 0) +
    (versions ? BASE.underTiles : 0) +
    2 * BASE.aroundHair +
    (forecast ? BASE.between : 0) +
    BASE.between +
    GRID_CELLS +
    rows * tileAtRest;

  // The floor's share: the narrowest tile over this column's, never more than the column itself.
  const floorScale = Math.min(1, theme.size.gameCard.tileNarrowest / column);
  const least = words + floorScale * boxes;
  const fits = (stage.height - words) / boxes;

  const bound: TileBound = fits >= 1 ? 'width' : fits >= floorScale ? 'height' : 'floor';
  const scale = bound === 'width' ? 1 : bound === 'height' ? fits : floorScale;

  // The gaps the spare is shared into: row, vs, row; the tiles and what follows them; the forecast
  // and the grid; the grid and the court block.
  const gaps = (doubles ? 2 : 0) + 1 + (forecast ? 1 : 0) + 1;
  const share = bound === 'width' ? (stage.height - words - boxes) / gaps : 0;

  const width = column * scale;
  return {
    bound,
    scale,
    tiles: {
      width,
      height: tileAtRest * scale,
      inset: (column - width) / 2,
      across: BASE.across,
      aroundVs: BASE.aroundVs * scale + share,
    },
    padX: BASE.pad,
    padY: BASE.pad * scale,
    underTiles: BASE.underTiles * scale,
    aroundHair: BASE.aroundHair * scale + share / 2,
    between: BASE.between * scale + share,
    least,
  };
}

/**
 * **The Games card's room, as numbers** — how big its tiles are, and where the height they leave
 * goes ([#864](https://github.com/Raketa02/Raketa/issues/864); the tab menu log §6.2, §6.3; design
 * system 7.22). No React in any of it: the card measures, this decides, and `deckCardGeometry.test`
 * holds it to the phones the decision was made on.
 *
 * ## One shape per court, and nothing stretches
 *
 * A tile used to take whatever height the card left it, so its shape changed from phone to phone —
 * 1.90 : 1 on the user's A32, which showed 32pt of face above the name strip. Now it has one shape:
 * **1.75 : 1 on doubles** (`doublesTile`, the details' own) and **3:4 on singles** (`singlesTile`,
 * the photo's crop), the theme's two values and the evidence for them.
 *
 * - **Width-bound by default.** A tile is as wide as its column: half the stage less the body's
 *   padding and the gap between the two.
 * - **Height-bound where the height runs out**, at the same shape — narrower, and centred in its
 *   column (`inset` either side). The room is the stage less every other block the card draws.
 * - **Never below the floor**, today's `tileMin`, still at its shape. Where even that does not fit
 *   (a 320 × 568 phone) the card overflows as it did before; #865 makes that a scroll. **The column
 *   caps even the floor**: in a window narrower than any phone (split screen) a tile is as wide as
 *   its column and no wider, under the floor if it must, since tiles that overlapped would be worse.
 *
 * ## A block is measured again only when it changes by more than a pixel
 *
 * Yoga rounds a block's top and bottom to the phone's pixels, so a block the gaps moved can report a
 * height a pixel off what it reported before, which would move the gaps again. Two measurements
 * within a pixel and a half are one height (`sameLength`); a real change — a line wrapping, a larger
 * text size — is a line of text, many pixels.
 *
 * ## The rest of the room is shared evenly
 *
 * On a tall phone a width-bound tile leaves height over. It goes **in equal shares into the gaps
 * between the card's blocks** — the tiles, the *vs* line, the forecast or Social vibe row, the week
 * grid and the court block — so the card still fills its stage, which the three-card stack needs
 * (`DeckStage`), and no block grows. The hairline sits in the middle of its gap, half the share
 * either side. *4 people are In on this game* is a caption to the tiles and stays at its own gap
 * under them.
 *
 * ## The blocks are measured, never assumed
 *
 * The ribbon, the *vs* line, the forecast or vibe row, the grid, the court block and the versions
 * line are words, and their height is the OS text size's and the line's wrap. The card lays them
 * out and hands their heights in; nothing here knows a type role.
 */

import { theme } from '@/shared/ui/theme';

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
  readonly grid: number;
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
 * What stopped the tiles: their column's **width**, the card's **height**, or the **floor** — the
 * card did not fit, and the tiles stand at `tileMin`.
 */
export type TileBound = 'width' | 'height' | 'floor';

/** The tiles, and the two gaps inside the tiles' block. */
export interface TileGeometry {
  readonly width: number;
  readonly height: number;
  /** How far a tile stands in from each side of its column — nought unless height-bound. */
  readonly inset: number;
  /** Between the two tiles of a row. */
  readonly across: number;
  /** Between a row and the *vs* line, above it and below it. */
  readonly aroundVs: number;
}

export interface CardGeometry {
  readonly bound: TileBound;
  readonly tiles: TileGeometry;
  /** The body's padding, every side. */
  readonly pad: number;
  /** Between the tiles and *4 people are In on this game*. */
  readonly underTiles: number;
  /** Either side of the hairline, between the tiles and the forecast. */
  readonly aroundHair: number;
  /** Between the forecast and the grid, and between the grid and the court block. */
  readonly between: number;
}

/** The card's gaps at rest — what each is before any spare height reaches it. */
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
export type MeasuredBlock = 'ribbon' | 'vs' | 'versions' | 'headline' | 'grid' | 'court';

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
  const { ribbon, vs, versions, headline, grid, court } = heights;
  if (ribbon === undefined || grid === undefined || court === undefined) return undefined;
  if (drawn.shape === 'doubles' && vs === undefined) return undefined;
  if (drawn.versions && versions === undefined) return undefined;
  if (drawn.headline && headline === undefined) return undefined;
  return {
    ribbon,
    grid,
    court,
    hairline,
    ...(drawn.shape === 'doubles' && vs !== undefined ? { vs } : {}),
    ...(drawn.versions && versions !== undefined ? { versions } : {}),
    ...(drawn.headline && headline !== undefined ? { headline } : {}),
  };
}

/** The tiles' size and every gap on the card, for this room — see the module note. */
export function cardGeometry({ stage, shape, blocks }: CardRoom): CardGeometry {
  const ratio = RATIO[shape];
  const rows = ROWS[shape];
  const doubles = shape === 'doubles';
  const forecast = blocks.headline !== undefined;

  // Everything on the card but the tiles, with every gap at rest.
  const rest =
    blocks.ribbon +
    2 * BASE.pad +
    (doubles ? (blocks.vs ?? 0) + 2 * BASE.aroundVs : 0) +
    (blocks.versions === undefined ? 0 : BASE.underTiles + blocks.versions) +
    2 * BASE.aroundHair +
    blocks.hairline +
    (forecast ? (blocks.headline ?? 0) + BASE.between : 0) +
    blocks.grid +
    BASE.between +
    blocks.court;

  const column = (stage.width - 2 * BASE.pad - BASE.across) / 2;
  const widthBound = column / ratio;
  const room = (stage.height - rest) / rows;
  const floor = theme.size.gameCard.tileMin;

  const bound: TileBound = widthBound <= room ? 'width' : room >= floor ? 'height' : 'floor';
  // The column caps even the floor: tiles that overlapped would be worse than one under it.
  const height = bound === 'width' ? widthBound : Math.min(Math.max(room, floor), widthBound);
  const width = height === widthBound ? column : height * ratio;

  // The gaps the spare is shared into: row, vs, row; the tiles and what follows them; the forecast
  // and the grid; the grid and the court block.
  const gaps = (doubles ? 2 : 0) + 1 + (forecast ? 1 : 0) + 1;
  const share = Math.max(0, stage.height - rest - rows * height) / gaps;

  return {
    bound,
    tiles: {
      width,
      height,
      inset: (column - width) / 2,
      across: BASE.across,
      aroundVs: BASE.aroundVs + share,
    },
    pad: BASE.pad,
    underTiles: BASE.underTiles,
    aroundHair: BASE.aroundHair + share / 2,
    between: BASE.between + share,
  };
}

/**
 * **Top 10's switcher, opened rightwards, against the line it opens in** — derived rather than
 * seen, because no device has drawn it ([#821](https://github.com/Raketa02/Raketa/issues/821);
 * ADR-0205 §5; home refactor 12, 13; design-system 7.36).
 *
 * `RowSportPill` starts the bar its own inset (`groupPage.filterPad`, 9) before the pill, which
 * stands at the footer's left, and the bar grows to the right across the footer. Two edges matter:
 *
 * - **the line's inner edge**, where `FoldingLine` clips what it holds — the footer's right edge plus
 *   the line's inset (`foldingLine.pad`). Past it the bar is cut;
 * - **the footer's right edge**, the open bar's layer's — Android delivers no touch outside a view's
 *   parent, so a sport past it is drawn and cannot be pressed.
 *
 * The four sports are measured in the real Archivo the pill draws them in (`type.chip`), never an
 * *about 0,6em per letter* (`fontMetrics.ts`' reason). They come to about 304pt of pills and a 322pt
 * bar, not the ~268 #805's notes guessed:
 *
 * - **375pt and wider** (iPhone SE 2 and 3, the minis, and up): every sport inside the footer and the
 *   bar inside the line. Asserted.
 * - **360pt** (the common Android width, the product owner's A32): the bar's round end meets the
 *   line's inner edge, cut by under a point, and the last sport's far ~6pt stand past the footer,
 *   out of reach on Android. Asserted to within a point, so a bar that grows goes red here.
 * - **320pt** (`NARROWEST_SCREEN`, the first iPhone SE): the bar is cut by about 40pt, the last sport
 *   half hidden. Not asserted — a known limit, flagged for the product owner with the device look.
 *
 * **What makes it go red:** a longer sport name, a fifth sport, a wider pill or chevron, a larger
 * `type.chip`, or a narrower line. Each is a real change to the answer.
 */

import { readFace, widthOf } from '@/test-support/fontMetrics';
import { SPORTS } from '@/shared/vocabulary/sport';

import { theme } from './theme';

const archivo = readFace(`@expo-google-fonts/archivo/${theme.type.chip.fontFamily}.ttf`);
const word = (text: string) => widthOf(archivo, text, theme.type.chip.fontSize);

/** The names the Rankings words give the four sports. */
const NAMES = { padel: 'Padel', tennis: 'Tennis', squash: 'Squash', badminton: 'Badminton' };

const PAD = theme.size.groupPage.filterPad;
const LINE = theme.size.foldingLine;

/** A pill in the bar: its inset, the dot, the gap, the name — and the current sport's ‹ after it. */
function pill(name: string, current: boolean): number {
  const fold = current ? theme.space.xs + word('‹') : 0;
  return 2 * theme.space.md + theme.size.sportDot + theme.space.xs + word(name) + fold;
}

/** The bar's row, widest when the longest name is not the current one. */
const ROW = Math.max(
  ...SPORTS.map((current) =>
    SPORTS.reduce((sum, sport) => sum + pill(NAMES[sport], sport === current), 0),
  ),
);
const BAR = ROW + 2 * PAD;

/** The footer of an open line on a phone this wide: the content, less the line's border and inset. */
const footer = (screen: number) => screen - 2 * theme.size.gutter - 2 * LINE.border - 2 * LINE.pad;

/** How far past the line's inner edge the open bar's right end stands — negative inside it. */
const pastTheLine = (screen: number) => BAR - PAD - (footer(screen) + LINE.pad);

it('measures every sport the switcher offers, in the face it draws them in', () => {
  expect(SPORTS).toEqual(['padel', 'tennis', 'squash', 'badminton']);
  expect(archivo.draws('‹'.codePointAt(0)!)).toBe(true);
});

it('opens inside the line with every sport in reach, on a 375pt phone and wider', () => {
  expect(ROW).toBeLessThanOrEqual(footer(375));
  expect(pastTheLine(375)).toBeLessThanOrEqual(0);
});

it('meets the line’s inner edge on a 360pt phone, cut by under a point', () => {
  expect(pastTheLine(360)).toBeLessThan(1);
});

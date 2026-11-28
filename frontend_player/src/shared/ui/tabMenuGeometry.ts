/**
 * **Where the tab's menu stands, and what its catcher covers** (design-system 9.5,
 * [#861](https://github.com/Rakieta02/Rakieta/issues/861); PRD #859) — `TabMenu`'s numbers, pure, so
 * they are tested as numbers: Jest has no layout.
 *
 * Every frame is in **the layer's** coordinates — the page the menu is drawn over, which the caller
 * measures the tab bar and its tab against.
 *
 * - **The card hangs from the tab** that opens it, `size.tabMenu.hang` under its bottom edge, with no
 *   arrow, and stands its **start or end edge on the tab's** (Games' start, Friends' end). It is as
 *   wide as its lines, so it is placed by that one edge — `left` or `right` — and **never past the
 *   gutter**: the edge is held inside it, and the card is never wider than the room from there to
 *   the far gutter.
 * - **The catcher covers the page but the tab bar and its tabs' reach** (`TAB_REACH`): four boxes
 *   round it — above, below and either side — so a press anywhere else closes the menu and does
 *   nothing else, and a press on another tab, or just past one as its slop allows, reaches the bar in
 *   one tap. A box round a hole rather than one box under the bar, because a bar raised over a
 *   catcher is z-order, and z-order is the one thing a test cannot see.
 */

import { theme } from './theme';

/** A measured box, as `onLayout` reports one. */
export interface MenuFrame {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

/** Which of the tab's edges the card stands on. */
export type MenuAlign = 'start' | 'end';

/** The card's place in its layer: one edge set, and how wide it may grow from there. */
export interface MenuPlace {
  readonly top: number;
  readonly left?: number;
  readonly right?: number;
  readonly maxWidth: number;
}

const GUTTER = theme.size.gutter;

export function tabMenuPlace(trigger: MenuFrame, layerWidth: number, align: MenuAlign): MenuPlace {
  const top = trigger.y + trigger.height + theme.size.tabMenu.hang;
  if (align === 'start') {
    const left = Math.max(GUTTER, trigger.x);
    return { top, left, maxWidth: layerWidth - GUTTER - left };
  }
  const right = Math.max(GUTTER, layerWidth - (trigger.x + trigger.width));
  return { top, right, maxWidth: layerWidth - GUTTER - right };
}

/** A box of the catcher, as absolute-position offsets in the layer. */
export interface CatcherBox {
  readonly top: number;
  readonly left: number;
  readonly right?: number;
  readonly bottom?: number;
  readonly width?: number;
  readonly height?: number;
}

/**
 * **How far a tab answers a touch past the bar**, above and below it: 6.5's segment slop, less the
 * track's own padding — 9 − 3 = 6. The catcher leaves this band too, so a tap that would have
 * reached a tab with the menu shut still reaches it with the menu open.
 */
export const TAB_REACH = theme.hit.seg.top - theme.space.xxs;

/**
 * The four boxes that cover the layer but `bar` and the band `reach` deep above and below it — the
 * tabs' own reach. The boxes beside the bar cover the gutters that deep too.
 */
export function catcherAround(
  bar: MenuFrame,
  reach: number,
): {
  readonly above: CatcherBox;
  readonly below: CatcherBox;
  readonly start: CatcherBox;
  readonly end: CatcherBox;
} {
  const top = bar.y - reach;
  const height = bar.height + 2 * reach;
  return {
    above: { top: 0, left: 0, right: 0, height: top },
    below: { top: top + height, left: 0, right: 0, bottom: 0 },
    start: { top, height, left: 0, width: bar.x },
    end: { top, height, left: bar.x + bar.width, right: 0 },
  };
}

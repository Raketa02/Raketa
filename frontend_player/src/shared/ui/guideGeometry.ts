/**
 * The guide's arithmetic, per design-system 9.4 — no React in any of it, for
 * `swipeRowGeometry`'s reason: a rule about numbers is testable as numbers.
 *
 * - **The hole** is the target as measured in the window, grown by `space.xs` on every side so
 *   the figure does not touch the dim's edge, and kept inside the window.
 * - **The bubble** stands under the hole when the hole's middle is in the window's upper half and
 *   over it otherwise, `space.md` clear of it — room for the arrow — and takes the content's
 *   width, gutter to gutter, as a `wide` popover does: it carries a paragraph and a row of
 *   controls, and 7.6's 250 would stack them.
 * - **Or beside it**, when the step asks: to the hole's right, `space.md` clear of it, out to the
 *   right gutter, standing so its arrow is level with the mark. It is for a mark on the far edge of
 *   a tall figure — the level's ⓘ, at the top of a head and a large number — where an arrow from
 *   under the hole lands on whatever is under the figure, and one over the hole has no room under
 *   the status bar. **It needs `size.guideBesideMin` of room**, and a measured mark; without
 *   either it stands under or over the hole, as any step does.
 * - **The arrow** points at what the step names — a figure's own ⓘ mark, which is what the
 *   bubble explains — and at the hole's middle when it names nothing or that did not measure; kept
 *   off the bubble's rounded corners either way. The hole's middle alone missed: a figure that
 *   stretches across its column puts its middle in empty space, far from its mark.
 *
 * **A target that was not measured has no layout**: the test renderer never answers
 * `measureInWindow`, and a view not yet laid out answers zeros. The guide then dims the whole
 * window and stands the bubble in its middle, as the popover centres itself rather than pointing
 * at nothing.
 */

import { theme } from './theme';

export interface GuideRect {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

export interface GuideWindow {
  readonly width: number;
  readonly height: number;
}

/**
 * Where the bubble stands, measured from the window's edges: its top under the hole, its bottom
 * over it, or its top and left beside it.
 */
export type GuideBubbleSpot =
  | {
      readonly side: 'below';
      readonly top: number;
      readonly left: number;
      readonly width: number;
    }
  | {
      readonly side: 'above';
      readonly bottom: number;
      readonly left: number;
      readonly width: number;
    }
  | {
      readonly side: 'right';
      readonly top: number;
      readonly left: number;
      readonly width: number;
    };

export interface GuideLayout {
  readonly hole: GuideRect;
  readonly bubble: GuideBubbleSpot;
  /**
   * Where the arrow's square starts along the bubble's edge that faces the hole, from the bubble's
   * outer corner: from its left for a bubble under or over the hole, from its top for one beside it.
   */
  readonly arrow: number;
}

/** The bubble's outline, which the arrow continues — 7.6's 1pt line. */
export const GUIDE_BUBBLE_BORDER = 1;

/**
 * How far below a beside bubble's top its arrow's middle sits: level with the title's line, inside
 * the outline and the padding — so the title reads as the thing the arrow says.
 */
const BESIDE_ARROW_LEVEL =
  GUIDE_BUBBLE_BORDER + theme.space.md + theme.type.cardTitle.lineHeight / 2;

/**
 * @param pointAt where the arrow points, as measured — the hole's middle when it is `undefined` or
 *   answered zeros, as a view not yet laid out does.
 * @param besideMark the step asks to stand beside its mark, when there is room.
 */
export function guideLayout(
  target: GuideRect | undefined,
  window: GuideWindow,
  pointAt?: GuideRect,
  besideMark = false,
): GuideLayout | undefined {
  if (target === undefined || target.width <= 0 || target.height <= 0) return undefined;

  const pad = theme.space.xs;
  const left = Math.max(0, target.x - pad);
  const top = Math.max(0, target.y - pad);
  const right = Math.min(window.width, target.x + target.width + pad);
  const bottom = Math.min(window.height, target.y + target.height + pad);
  const hole = { x: left, y: top, width: right - left, height: bottom - top };

  const gap = theme.space.md;
  const gutter = theme.size.gutter;
  const arrow = theme.size.popoverArrow;
  const corner = theme.radius.popover;
  const mark = pointAt === undefined || pointAt.width <= 0 ? undefined : pointAt;

  if (besideMark && mark !== undefined) {
    const besideLeft = hole.x + hole.width + gap;
    const besideWidth = window.width - gutter - besideLeft;
    if (besideWidth >= theme.size.guideBesideMin) {
      const level = mark.y + mark.height / 2;
      const besideTop = Math.max(0, level - BESIDE_ARROW_LEVEL);
      return {
        hole,
        bubble: { side: 'right', top: besideTop, left: besideLeft, width: besideWidth },
        arrow: Math.max(corner, level - besideTop - arrow / 2),
      };
    }
  }

  const width = window.width - 2 * gutter;
  const below = hole.y + hole.height / 2 <= window.height / 2;
  const bubble: GuideBubbleSpot = below
    ? { side: 'below', top: hole.y + hole.height + gap, left: gutter, width }
    : { side: 'above', bottom: window.height - hole.y + gap, left: gutter, width };

  const middle = mark === undefined ? hole.x + hole.width / 2 : mark.x + mark.width / 2;
  return {
    hole,
    bubble,
    arrow: clamp(middle - gutter - arrow / 2, corner, width - corner - arrow),
  };
}

/**
 * **The dim with the hole in it**, as one SVG path filled even-odd: the window's rectangle, then
 * the hole's rounded one inside it — a second subpath inside the first is a hole under that rule.
 */
export function spotlightPath(hole: GuideRect, window: GuideWindow): string {
  const r = Math.min(theme.radius.spotlight, hole.width / 2, hole.height / 2);
  const { x, y, width: w, height: h } = hole;
  return [
    `M0 0H${window.width}V${window.height}H0Z`,
    `M${x + r} ${y}H${x + w - r}A${r} ${r} 0 0 1 ${x + w} ${y + r}`,
    `V${y + h - r}A${r} ${r} 0 0 1 ${x + w - r} ${y + h}`,
    `H${x + r}A${r} ${r} 0 0 1 ${x} ${y + h - r}`,
    `V${y + r}A${r} ${r} 0 0 1 ${x + r} ${y}Z`,
  ].join('');
}

function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high);
}

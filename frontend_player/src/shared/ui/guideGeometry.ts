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
 * - **The arrow** points at the hole's middle, kept off the bubble's rounded corners.
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

/** Where the bubble stands: its top under the hole, or its bottom over it, measured from the window's edge. */
export type GuideBubbleSpot =
  | { readonly below: true; readonly top: number; readonly left: number; readonly width: number }
  | {
      readonly below: false;
      readonly bottom: number;
      readonly left: number;
      readonly width: number;
    };

export interface GuideLayout {
  readonly hole: GuideRect;
  readonly bubble: GuideBubbleSpot;
  /** From the bubble's left edge. */
  readonly arrowLeft: number;
}

export function guideLayout(
  target: GuideRect | undefined,
  window: GuideWindow,
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
  const width = window.width - 2 * gutter;
  const below = hole.y + hole.height / 2 <= window.height / 2;
  const bubble: GuideBubbleSpot = below
    ? { below, top: hole.y + hole.height + gap, left: gutter, width }
    : { below, bottom: window.height - hole.y + gap, left: gutter, width };

  const arrow = theme.size.popoverArrow;
  const corner = theme.radius.popover;
  const middle = hole.x + hole.width / 2;
  const arrowLeft = clamp(middle - gutter - arrow / 2, corner, width - corner - arrow);

  return { hole, bubble, arrowLeft };
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

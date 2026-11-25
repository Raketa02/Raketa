/**
 * **Where the bottom of a tab screen stands against the bar** — what the router suites read to see
 * that a list scrolls its last row clear of the bar, and that what stands at the bottom stands above
 * it (ADR-0210 §3, #881).
 *
 * The bar floats over the screen's foot and owns no layout, so nothing ends above it for free any
 * more: each scroller ends at the bar's **reach** plus its own gap, and a pinned button's screen ends
 * at the reach. Jest lays nothing out, so what a suite can observe is the arithmetic: the bar is
 * drawn over the screen at the phone's foot, and a page's end padding, less the bar, is the gap the
 * last row keeps above it.
 *
 * **The bars' heights are worked out here from the theme**, never read back from the bar or the
 * reach — a reach that drifted from the bar it describes would leave a last row under it, and a suite
 * reading the same number as the screen would agree with it. The harness's insets are all zero
 * (`onboardingRouter.tsx`), so the reach is the bar's height alone.
 */

import { StyleSheet, type StyleProp, type ViewStyle } from 'react-native';
import { screen } from 'expo-router/testing-library';

import { TAB_BAR_TEST_ID, theme } from '@/shared/ui';

/** The player's bar at the default text size: hairline, top padding, ⚡Play disc, gap, label, foot. */
export const PLAYERS_BAR =
  1 +
  theme.space.xs +
  theme.size.fab +
  theme.space.xxs +
  theme.type.tag.lineHeight +
  theme.space.md;

/** The administrator's: the same, with the 16pt icon box where the player's has the disc. */
export const ADMINISTRATORS_BAR =
  1 +
  theme.space.xs +
  theme.size.tabIcon +
  theme.space.xxs +
  theme.type.tag.lineHeight +
  theme.space.md;

/** A test instance as any query returns it — only its props and its way up are read. */
interface Placed {
  readonly type: unknown;
  readonly props: { readonly [prop: string]: unknown };
  readonly parent: Placed | null;
}

const flat = (style: unknown) => StyleSheet.flatten(style as StyleProp<ViewStyle>) ?? {};

/** The bar's own frame, flattened — the player's or the administrator's, whichever is drawn. */
export function barFrame(): ViewStyle {
  return flat(screen.getByTestId(TAB_BAR_TEST_ID).props.style);
}

/**
 * **Whether the bar is drawn over the screen** — absolute, edge to edge, at the phone's foot — so it
 * takes no layout and every screen under it draws to the bottom of the phone.
 */
export function barFloats(): boolean {
  const frame = barFrame();
  return (
    frame.position === 'absolute' && frame.left === 0 && frame.right === 0 && frame.bottom === 0
  );
}

/**
 * **The page an element is on** — its outermost scroller, so a rail inside the page (a Home row's,
 * a sport's chips) is passed by. Nothing when the element is in no scroller.
 */
export function pageOf(element: Placed): Placed | undefined {
  let page: Placed | undefined;
  for (let at = element.parent; at !== null; at = at.parent) {
    if ('contentContainerStyle' in at.props && typeof at.type !== 'string') page = at;
  }
  return page;
}

/** **Where a scroller's content ends** — the padding under its last row. */
export function endPadding(scroller: Placed): number {
  const style = flat(scroller.props.contentContainerStyle);
  const end = style.paddingBottom ?? style.paddingVertical ?? style.padding ?? 0;
  if (typeof end !== 'number') throw new Error(`a scroller's end padding is ${String(end)}`);
  return end;
}

/**
 * **How far a scroller's last row stands above a bar of this height** once scrolled to its end —
 * the page running to the phone's foot under the bar, so its end padding less the bar is what is
 * left between them. Negative is a row under the bar.
 */
export function clearanceAbove(scroller: Placed, bar: number = PLAYERS_BAR): number {
  return endPadding(scroller) - bar;
}

/** **A style's distance from the phone's foot**, for something floating at the bottom of a screen. */
export function bottomOf(element: Placed): number {
  const bottom = flat(element.props.style).bottom;
  if (typeof bottom !== 'number') throw new Error(`bottom is ${String(bottom)}`);
  return bottom;
}

/** **What floats an element** — the nearest frame at or over it that is placed absolutely. */
export function floatOf(element: Placed): Placed {
  for (let at: Placed | null = element; at !== null; at = at.parent) {
    if (typeof at.type === 'string' && flat(at.props.style).position === 'absolute') return at;
  }
  throw new Error('nothing floats this element');
}

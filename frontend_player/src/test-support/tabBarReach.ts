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
 * **The reach is worked out here from the theme**, never read back from the bar or the module — a
 * reach that drifted from the dock it describes would leave a last row under it, and a suite reading
 * the same number as the screen would agree with it. The harness's insets are all zero
 * (`onboardingRouter.tsx`), so the dock stands at its least lift, 12, and reaches 12 + 54 = 66
 * (#883).
 */

import { Dimensions, StyleSheet, type StyleProp, type ViewStyle } from 'react-native';
import { getAnimatedStyle } from 'react-native-reanimated';
import { act, screen, within } from 'expo-router/testing-library';

import { TAB_BAR_MARKER_TEST_ID, TAB_BAR_TEST_ID, theme } from '@/shared/ui';

/** The dock's hairline, which its columns and its marker are laid inside. */
const HAIRLINE = 1;

/**
 * **What the player's bar takes at the bottom in the harness** — the dock's least lift and its
 * height, over no inset: 66.
 */
export const PLAYERS_BAR = theme.size.tabBar.lift + theme.size.tabBar.height;

/** **The administrator's** — the same dock with two columns, so the same reach. */
export const ADMINISTRATORS_BAR = theme.size.tabBar.lift + theme.size.tabBar.height;

/** A node as a query hands it back. */
type Found = ReturnType<typeof screen.getByTestId>;

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
 * **Whether the bar is drawn over the screen as the dock** — absolute, 12 in from each side, at its
 * least lift over the harness's zero inset, and 54 tall — so it takes no layout and every screen
 * under it draws to the bottom of the phone.
 */
export function barFloats(): boolean {
  const frame = barFrame();
  const { sideInset, lift, height } = theme.size.tabBar;
  return (
    frame.position === 'absolute' &&
    frame.left === sideInset &&
    frame.right === sideInset &&
    frame.bottom === lift &&
    frame.height === height
  );
}

/** The bar's tabs, in the order it announces them — the bar's own, never a group page's. */
const barTabs = () => within(screen.getByTestId(TAB_BAR_TEST_ID)).getAllByRole('tab');

/** A tab's name as its column speaks it, less Home's count after the comma. */
const nameOf = (tab: { readonly props: { readonly [prop: string]: unknown } }) =>
  String(tab.props.accessibilityLabel).split(',')[0];

/**
 * **The selection marker as its last frame drew it** — read through Reanimated, since the marker
 * travels (#884) and its own `style` prop keeps only its first pose.
 */
function markerDrawn(): ViewStyle {
  const node = screen.getByTestId(TAB_BAR_MARKER_TEST_ID);
  return flat(
    node.props.jestAnimatedStyle === undefined ? node.props.style : getAnimatedStyle(node),
  );
}

/** One of the marker's transform steps. */
function markerStep(step: 'translateX' | 'scaleX' | 'scaleY'): number | undefined {
  const steps = markerDrawn().transform as readonly Record<string, number>[] | undefined;
  return steps?.find((each) => each[step] !== undefined)?.[step];
}

/**
 * **Where the selection marker's centre stands, in the bar's columns** — 0.5 is the first column's
 * middle. The dock's columns divide the window less its side insets and hairlines equally.
 */
export function markerCentre(): number {
  const column =
    (Dimensions.get('window').width - 2 * theme.size.tabBar.sideInset - 2 * HAIRLINE) /
    barTabs().length;
  const style = markerDrawn();
  const centre =
    (typeof style.left === 'number' ? style.left : 0) +
    (markerStep('translateX') ?? 0) +
    Number(style.width) / 2;
  return centre / column;
}

/**
 * **Which tab the selection marker stands under** — the name of the tab whose column its centre is
 * in (its label alone: Home's spoken count is left off), or `undefined` when it is centred in none,
 * as it is mid-slide.
 */
export function markerUnder(): string | undefined {
  const centre = markerCentre();
  const at = Math.floor(centre);
  if (Math.abs(centre - (at + 0.5)) > 0.0001) return undefined;
  const tab = barTabs()[at];
  return tab === undefined ? undefined : nameOf(tab);
}

/**
 * **A walk's clock for a slide**, started where it is called — straight after the press or the
 * landing, whose navigation's flush the slide starts behind. Each read it is handed then lands at
 * its own moment of the slide, however long a `waitFor` or a `findBy` spent polling the fake clock
 * in between; a moment already passed is a broken walk, and says so.
 */
export function slideFromNow(): (ms: number) => void {
  const origin = Date.now();
  return (ms) => {
    const ahead = origin + ms - Date.now();
    if (ahead < 0) throw new Error(`the walk is already ${-ahead} ms past ${ms} into the slide`);
    act(() => jest.advanceTimersByTime(ahead));
  };
}

/** **Whether the marker is at rest** — its own shape, neither stretched nor recoiling. */
export function markerAtRest(): boolean {
  return (markerStep('scaleX') ?? 1) === 1 && (markerStep('scaleY') ?? 1) === 1;
}

/**
 * **How far a tab has coloured in** — its selected layer's opacity, 0 idle and 1 lit (ADR-0210 §8).
 * A column draws its icon and its label each as two stacked layers, idle then selected, which fade
 * together; the four are read in that order.
 */
export function colouredIn(name: string): number {
  const tab = barTabs().find((each) => nameOf(each) === name);
  if (tab === undefined) throw new Error(`the bar has no ${name} tab`);
  const layers = tab
    .findAll(
      (node: Found) => typeof node.type === 'string' && node.props.jestAnimatedStyle !== undefined,
    )
    .map((node: Found) => Number(flat(getAnimatedStyle(node)).opacity));
  if (layers.length !== 4) throw new Error(`the ${name} tab drew ${layers.length} layers, not 4`);
  const [, icon, , label] = layers;
  if (icon !== label)
    throw new Error(`the ${name} tab's icon shows ${icon} and its label ${label}`);
  return icon!;
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

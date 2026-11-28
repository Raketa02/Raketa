/**
 * What every overlay in this app needs, in one place.
 *
 * There are three of them now — the bottom sheet (design-system 9.1), the anchored popover
 * (7.6) and the toast (9.2) — and Part 13 asks the same things of them: siblings hidden from
 * assistive technology, focus moved in and returned to the trigger on close, motion skipped
 * when the OS asks for it, and **an announcement on everything that appears without being
 * asked for**. Each was written inside `BottomSheet` when it was the only overlay; a second
 * copy in `Popover` is how two overlays end up meeting two different halves of one
 * requirement.
 *
 * **The two OS questions are here rather than in a file of their own**, and one of them is now
 * a context. *Is motion reduced* and *is a screen reader running* arrived as this file's
 * business — every overlay skips its animation and announces itself — and they are read by
 * surfaces that are not overlays as well. Splitting them out would be two files whose contents
 * are one paragraph each; what a second home would buy is a second place to answer half of
 * `useCollapsedPresentation`.
 */

import {
  Fragment,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
  type RefObject,
} from 'react';
import { AccessibilityInfo, StyleSheet, View, findNodeHandle } from 'react-native';
import { useReducedMotion as useReducedMotionAtStart } from 'react-native-reanimated';

/** A ref to whatever should hold accessibility focus — a host element, not a component. */
export type FocusTarget = RefObject<View | null>;

/**
 * **The overlay host** — design-system 9.3's root-level layer, which every modal stage on
 * Android is drawn into (`ModalStage.android`), and which hides the app beneath it from a
 * screen reader while any is up.
 *
 * ## Why Android does not get the native `Modal`
 *
 * React Native's `Modal` presents in its own window, and under the New Architecture the size
 * of that window reaches layout as **native state**: the content is laid out at 0 × 0 first
 * and again at the window's size when the dialog reports it — measured on a Galaxy A55, `0 × 0`
 * and then `360 × 702` a frame later. **Reanimated 3.16 loses the second pass whenever any
 * animated style is mounted anywhere in the tree** — a 1 × 1 `useAnimatedStyle` view on the
 * deck pane was enough to collapse the deck's own sheet — and what is left is unusable, not
 * merely mis-sized: the content is a sliver as wide as its own padding at the top-left, and
 * even sized from the window it cannot be pressed, because Android finds no child under the
 * finger inside a 0 × 0 view, the dialog re-dispatches every touch's start, and the second
 * start hands the responder to the modal's own host — every press in the sheet is terminated
 * on the way to its release, and the scroll view never sees a touch at all. The radar is the
 * app's first animated style, so its sheet was the first casualty (2026-09-17).
 *
 * So on Android an overlay is hosted **here, in the tree**, where layout and touch are
 * ordinary: a layer at the root, above every screen and the tab bar, with the platform's back
 * gesture and the sheet's own motion done by the stage. iOS keeps the native window
 * (`ModalStage.tsx`), which is unaffected and carries its own exit animation.
 *
 * ## What the host owes the tree
 *
 * The layers are rendered **as siblings of the app**, so a stage's children keep every
 * context the root provides — the query client, the safe area, reduced motion — and lose any
 * a screen would have given them. None of the app's sheets reads one: every provider is at the
 * root, and no sheet content reads the navigation (`docs/architecture.md` Part 13). A stage
 * re-states its layer on every render, as a portal does, and the host reconciles the same
 * position so the layer's own state — a scroll position, a pressed control — survives.
 *
 * While a layer is up the app beneath takes {@link behindOverlay}: a native window hid the
 * tab bar and the other screens from a screen reader on its own, and a layer in the tree has
 * to say so itself — for the whole app, not only the screen that opened it. **And so does every
 * layer under the newest** ({@link useCoveredLayer}): a sheet opened from inside a sheet leaves
 * the first one up beneath it, and a listener belongs in the one on top.
 *
 * **The order is a context of its own**, apart from `set` and `remove`, and that is load-bearing:
 * a stage takes its layer down when the API it was handed changes, so an API that moved with the
 * order would have every stage take its layer down and put it back up at the end — a new order,
 * a new API, and again, without end. The API never changes; the order re-renders only the stages
 * that read it, and their re-statement leaves the order as it was.
 */
export function OverlayHost({ children }: { readonly children: ReactNode }) {
  const [layers, setLayers] = useState<ReadonlyMap<string, ReactNode>>(() => new Map());
  // The layers' keys, oldest first — moved only when one goes up or comes down, never by the
  // re-statement every stage makes on every render.
  const [order, setOrder] = useState<readonly string[]>([]);
  const set = useCallback((key: string, layer: ReactNode) => {
    setLayers((held) => new Map(held).set(key, layer));
    setOrder((keys) => (keys.includes(key) ? keys : [...keys, key]));
  }, []);
  const remove = useCallback((key: string) => {
    setLayers((held) => {
      if (!held.has(key)) return held;
      const next = new Map(held);
      next.delete(key);
      return next;
    });
    setOrder((keys) => (keys.includes(key) ? keys.filter((held) => held !== key) : keys));
  }, []);
  const layersApi = useMemo<OverlayLayers>(() => ({ set, remove }), [set, remove]);
  const open = layers.size > 0;

  return (
    <OverlayLayersContext.Provider value={layersApi}>
      <OverlayOrderContext.Provider value={order}>
        <View style={s.beneath} {...behindOverlay(open)} testID="overlay-host-beneath">
          {children}
        </View>
        {[...layers].map(([key, layer]) => (
          <Fragment key={key}>{layer}</Fragment>
        ))}
      </OverlayOrderContext.Provider>
    </OverlayLayersContext.Provider>
  );
}

/** What a stage does with the host: put its layer up under its own key, and take it down. */
export interface OverlayLayers {
  readonly set: (key: string, layer: ReactNode) => void;
  readonly remove: (key: string) => void;
}

const OverlayLayersContext = createContext<OverlayLayers | undefined>(undefined);

/** The layers' keys, oldest first — empty where there is no host. See the host's note. */
const OverlayOrderContext = createContext<readonly string[]>([]);

/** The host's layers, or `undefined` where there is no host — a stage then draws in place. */
export function useOverlayLayers(): OverlayLayers | undefined {
  return useContext(OverlayLayersContext);
}

/**
 * **Whether a newer layer is up over this one** — a sheet opened from inside a sheet, as the
 * record's *Block* opens its confirmation (#587). A native window hid the window under it from a
 * screen reader on its own; a layer in the tree hides itself, as the app beneath every layer does.
 * A key that is not up yet is not covered. The newest is the last put up: a sheet that opens a
 * sheet is up first, so the second is newer — two put up in one commit would land the child
 * first, which nothing does.
 */
export function useCoveredLayer(key: string): boolean {
  const order = useContext(OverlayOrderContext);
  return order.includes(key) && key !== order[order.length - 1];
}

const s = StyleSheet.create({
  beneath: { flex: 1 },
});

/**
 * The props a screen puts on its root while one of its overlays is open.
 *
 * Both are needed and neither is redundant: `accessibilityElementsHidden` is iOS and
 * `importantForAccessibility` is Android. **The overlay must not be rendered inside the
 * element carrying these** — it would hide itself along with everything else, which is
 * why both overlays are rendered as a sibling of the screen root rather than where they
 * were triggered.
 */
export function behindOverlay(open: boolean) {
  return {
    accessibilityElementsHidden: open,
    importantForAccessibility: open ? ('no-hide-descendants' as const) : ('auto' as const),
  };
}

/**
 * Move accessibility focus, where there is somewhere to move it to.
 *
 * Silent when the target is absent or unmounted: focus that cannot be placed is not a
 * failure, it is the ordinary state of a control that has just gone away.
 */
export function moveAccessibilityFocus(target: FocusTarget | undefined): void {
  if (target === undefined) return;
  const tag = findNodeHandle(target.current);
  if (tag === null) return;
  AccessibilityInfo.setAccessibilityFocus(tag);
}

/**
 * One OS switch, read once and then followed.
 *
 * Both settings answer the same shape — an initial read that resolves, and an event that
 * fires when the player changes it in Settings while the app is open — and a second copy of
 * that shape is a second place to forget the unmount guard. `live` is that guard: a promise
 * resolving after the screen has gone would set state on nothing.
 */
function useAccessibilityFlag(
  read: () => Promise<boolean>,
  event: 'reduceMotionChanged' | 'screenReaderChanged',
  initial = false,
): boolean {
  const [enabled, setEnabled] = useState(initial);

  useEffect(() => {
    let live = true;
    void read().then((value) => {
      if (live) setEnabled(value);
    });

    const subscription = AccessibilityInfo.addEventListener(event, setEnabled);
    return () => {
      live = false;
      subscription.remove();
    };
    // `read` is a module-level method reference and `event` a literal; both are stable, and
    // listing them keeps the hook honest without re-subscribing on every render.
  }, [read, event]);

  return enabled;
}

/**
 * Whether this tree runs with reduced motion.
 *
 * **It is a context now**, which the hook it replaced predicted in writing: *"a hook rather
 * than a context, deliberately… when something that is always mounted needs it — a press
 * transform, a list entrance — this becomes the context Part 13 describes."* The engine fill's
 * staggered seats are that list entrance, and the deck's card is that press transform. A hook
 * per consumer means an `AccessibilityInfo` listener per consumer, on surfaces that are mounted
 * for as long as the tab is; the OS switch is **one fact about the device**, and reading it in
 * one place is what Part 13's *"a screen reaches a port through its context"* is for.
 *
 * `false` is the value outside a provider, and it is the right one: it is what the app looked
 * like before anybody asked for calm. Every screen is inside `ReducedMotionProvider`, mounted
 * once at the root beside the other providers, so the only trees without one are the unit tests
 * that say so.
 */
export function useReducedMotion(): boolean {
  return useContext(ReducedMotionContext);
}

/**
 * The one place this app asks the OS about motion. `false` outside a provider; inside one, the OS's
 * answer from the first render on.
 */
const ReducedMotionContext = createContext(false);

export interface ReducedMotionProviderProps {
  /**
   * The device, unless a test says otherwise — Part 13's own shape for a port's context. A
   * test that wants a tree in reduced motion wraps it in `value`, rather than mocking
   * `AccessibilityInfo` and awaiting a promise on every render it makes.
   */
  readonly value?: boolean;
  readonly children: ReactNode;
}

/**
 * One subscription to the OS switch, for the whole tree beneath it.
 *
 * Mounted at the root, so nothing else has to wire it up and nothing else may: a second
 * provider inside a screen would be a second answer to a question the device answers once.
 *
 * **Its first answer is already the OS's, never a provisional `false`** (ADR-0209 §2). The
 * asynchronous read lands after the first frame, and the launch's drawn splash decides its variant
 * once, before it. So the state starts from Reanimated's answer — the setting as the process
 * started, which the native side hands the JavaScript runtime as it installs and which is therefore
 * there before anything renders — and the subscription follows the switch from then on.
 */
export function ReducedMotionProvider({ value, children }: ReducedMotionProviderProps) {
  const atStart = useReducedMotionAtStart();
  const os = useAccessibilityFlag(READ_REDUCE_MOTION, 'reduceMotionChanged', atStart);

  return (
    <ReducedMotionContext.Provider value={value ?? os}>{children}</ReducedMotionContext.Provider>
  );
}

/**
 * **Whether the launch's drawn splash still covers this tree**
 * ([ADR-0209](../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §2). For the first seconds of a cold open the first screen is mounted underneath the splash,
 * which is drawn over everything the root draws and swallows every touch until it is gone.
 *
 * Drawing it last covers what is in the tree. Two things it cannot cover that way read this
 * instead:
 *
 * - **iOS's modal stage** is a native window, presented above the whole app, splash and all, so it
 *   is held back while covered and presented as the splash goes (`ModalStage.tsx`). Android's stage
 *   is a layer in the tree and is simply covered with it.
 * - **A toast's hold** would run out unseen under the splash, so it starts once the splash is gone
 *   (`Toast.tsx`).
 *
 * `false` outside the launch gate — the router suites' own root, which draws no splash — and for
 * the rest of the process once the splash has gone. Provided by `shared/lib/bootstrap`'s launch
 * gate, which `shared/ui` cannot import: the gate draws with this module.
 */
export function useCoveredBySplash(): boolean {
  return useContext(SplashCoverContext);
}

const SplashCoverContext = createContext(false);

export interface SplashCoverProviderProps {
  readonly covered: boolean;
  readonly children: ReactNode;
}

/** The launch gate's, around the tree it mounts under the splash; a test's, around one it covers. */
export function SplashCoverProvider({ covered, children }: SplashCoverProviderProps) {
  return <SplashCoverContext.Provider value={covered}>{children}</SplashCoverContext.Provider>;
}

/**
 * Whether a screen reader is running.
 *
 * Not a synonym for reduced motion, and the difference is the point: **a player may have
 * VoiceOver on and reduced motion off**, which is the common case
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §20.11). Anything that
 * asked only about motion would run its full animation in front of the one listener who gets
 * none of the craft and all of the latency.
 */
export function useScreenReader(): boolean {
  return useAccessibilityFlag(READ_SCREEN_READER, 'screenReaderChanged');
}

const READ_REDUCE_MOTION = () => AccessibilityInfo.isReduceMotionEnabled();
const READ_SCREEN_READER = () => AccessibilityInfo.isScreenReaderEnabled();

/**
 * Whether presentation collapses to its end state — **one condition, satisfied by either.**
 *
 * `the-play-screens.md` §3 licenses the fill animation as *"presentation over a completed
 * answer, and the client may take its time."* That permission is granted to craft aimed at
 * sight. A listener gets none of the craft and all of the latency, in front of an answer that
 * is already in memory — so §20.11 makes a running screen reader a **second condition on the
 * same path** as reduced motion rather than a second path.
 *
 * One helper, because two would be two places for a surface to honour one of the conditions
 * and not the other. What collapses is named where it is drawn: the fill animation, the deck's
 * stagger, and the **stagger over** the searching latch's floor, which goes to zero.
 *
 * **The floor itself does not**, and this sentence used to say it did. `motion.hold` had
 * already decided the other way in writing — *a held duration is not an animation: nothing
 * moves, and the player who asked the OS to calm things down is the last one who should get a
 * flash* — and [#269](https://github.com/Rakieta02/Rakieta/issues/269) is where the two met.
 * `searchingWait.ts` is where the split is arithmetic rather than prose.
 */
export function useCollapsedPresentation(): boolean {
  // Both are read, always: `||` between two hook calls would make the second one conditional
  // on the first, which is the rule React enforces by crashing on the render after a change.
  const reduced = useReducedMotion();
  const listening = useScreenReader();

  return reduced || listening;
}

/**
 * A live region: say a value again whenever it changes, and never when it has not.
 *
 * §20.9 names three of these in the Play tab and no fourth — the toast layer, the searching
 * status, and the **provisional forecast**, which is the only figure in the tab that changes
 * while focus is somewhere else. Moving a player across the net changes it while the listener
 * is still on the seat that moved, so nothing else would ever tell them.
 *
 * **An announcement, not an `accessibilityLiveRegion`.** Android's attribute has no iOS
 * equivalent and fires on *re-render* rather than on arrival, which is the wrong event for a
 * figure that is recomputed more often than it changes. Both platforms have an announcement,
 * and this is the same mechanism `ToastHost` uses for the region it owns.
 *
 * `null` is a region with nothing in it, which is silence rather than an empty sentence.
 */
export function useLiveRegion(message: string | null, politeness: Announcement = 'queued'): void {
  useEffect(() => {
    if (message === null || message === '') return;
    announce(message, politeness);
  }, [message, politeness]);
}

/**
 * Whether this announcement may wait its turn, or takes the floor.
 *
 * Part 13 requires that every toast announces. It does not say *how*, and the default
 * mechanism **interrupts** on both platforms: nineteen toasts fire from the Play tab, and one
 * landing mid-card cuts a listener off in the middle of the reason lines they were listening
 * to. So the requirement keeps its force and names its mechanism precisely — `queue`, which
 * is a Part 16 amendment rather than an exception (`the-words.md` §20.10).
 */
export type Announcement = 'queued' | 'interrupting';

/**
 * Say something to a screen reader, politely by default.
 *
 * **`queue` is honoured on iOS and is not a thing on Android.** React Native forwards the
 * option to `UIAccessibility` and falls back to the interrupting call on the other platform,
 * so a queued announcement is a request rather than a guarantee — which is worth knowing here
 * and is not worth a second code path, because interrupting is what the requirement asked for
 * before this amendment and is still the correct floor.
 */
export function announce(message: string, politeness: Announcement = 'queued'): void {
  AccessibilityInfo.announceForAccessibilityWithOptions(message, {
    queue: politeness === 'queued',
  });
}

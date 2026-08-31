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
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
  type RefObject,
} from 'react';
import { AccessibilityInfo, findNodeHandle, type View } from 'react-native';

/** A ref to whatever should hold accessibility focus — a host element, not a component. */
export type FocusTarget = RefObject<View | null>;

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
): boolean {
  const [enabled, setEnabled] = useState(false);

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

/** The one place this app asks the OS about motion. `false` until a provider says otherwise. */
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
 */
export function ReducedMotionProvider({ value, children }: ReducedMotionProviderProps) {
  const os = useAccessibilityFlag(READ_REDUCE_MOTION, 'reduceMotionChanged');

  return (
    <ReducedMotionContext.Provider value={value ?? os}>{children}</ReducedMotionContext.Provider>
  );
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
 * and not the other. What collapses is named where it is drawn: the fill animation, the
 * deck's stagger, and the minimum-display latch, which goes to zero.
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

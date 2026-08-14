/**
 * What every overlay in this app needs, in one place.
 *
 * There are two of them now — the bottom sheet (design-system 9.1) and the anchored
 * popover (7.6) — and Part 13 asks the same three things of both: siblings hidden from
 * assistive technology, focus moved in and returned to the trigger on close, and motion
 * skipped when the OS asks for it. Each was written inside `BottomSheet` when it was the
 * only overlay; a second copy in `Popover` is how two overlays end up meeting two
 * different halves of one requirement.
 */

import { useEffect, useState, type RefObject } from 'react';
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
 * Whether the OS has asked for reduced motion.
 *
 * A hook rather than a context, deliberately: both consumers are overlays, at most one is
 * mounted at a time, and a context would have to be wired into the root layout and every
 * test harness to answer a question two components ask. When something that is *always*
 * mounted needs it — a press transform, a list entrance — this becomes the context
 * Part 13 describes, and this hook is what reads it.
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    let live = true;
    void AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (live) setReduced(enabled);
    });

    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduced);
    return () => {
      live = false;
      subscription.remove();
    };
  }, []);

  return reduced;
}

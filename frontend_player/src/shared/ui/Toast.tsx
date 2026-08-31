/**
 * The toast and its host — [9.2](../../../docs/design-system.md#92-toast), built.
 *
 * ```
 * host   left 15, right 15, above the tab bar + the bottom safe-area inset, layer 40
 * tst    background night, #fff, radius 12, padding 12 x 15, inlineTitle
 * ok     background mintInk        <- Rule C, was mint (4,07)
 * bad    background red
 * ```
 *
 * 9.2 was specified and unbuilt. What it needed is what §G3 #7 asks for and what this file
 * adds: **the queue, the live region and the dismiss.**
 *
 * ## Mounted once, at the overlay host
 *
 * [9.3](../../../docs/design-system.md#93-layer-order) requires a single root-level overlay
 * host, because `zIndex` in React Native is scoped to the parent — a toast raised from inside
 * a card renders inside that card. `ToastHost` is a sibling of the route tree in
 * `src/app/_layout.tsx`, exactly as `EnvironmentBadge` is, and there is one of it. The queue
 * behind it is `shared/store/toast.store.ts`, for the same reason: a queue inside a feature
 * is that feature owning every other feature's toasts.
 *
 * ## The dismiss is the hold, and there is no close control
 *
 * 9.2's rule is `pointerEvents: 'none'` on the container **so a toast never blocks a tap**,
 * and a control inside it is a tap the toast has to eat. So the dismiss is the timer: the
 * head of the queue is shown for `motion.hold.toast` and then the next one takes its place.
 * A player who wants it gone waits 2,6 seconds; a player who wants to press what is under it
 * already can.
 *
 * **Nothing here animates.** 1.5 is *nothing animates that does not have to*, and the
 * prototype's 240 ms rise is the harness being pleased with itself — the message has already
 * been spoken by the time it would have finished arriving. That also means there is no
 * reduced-motion branch to get wrong: a hold is not an animation, which is `motion.hold`'s
 * own rule, and it is the only timing this component has.
 *
 * ## The live region is an announcement, not an `accessibilityLiveRegion`
 *
 * Android's live region attribute has no iOS equivalent and fires on *re-render* rather than
 * on arrival, which on a host that swaps one message for another is the wrong event. Both
 * platforms have an announcement, and Part 13 already asks for one on every toast — so the
 * host announces the head as it arrives, **queued**, with the send confirmation as the single
 * message that interrupts (`the-words.md` §20.10).
 *
 * The toast itself is hidden from assistive technology. It has already been spoken, and a
 * reader that walked into it would hear the sentence a second time — 6.8's argument for
 * hiding its column heads, on a surface where the second reading is 2,6 seconds late.
 */

import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useToastQueue, type Toast as ToastMessage } from '@/shared/store/toast.store';

import { announce } from './overlay';
import { TAB_BAR_HEIGHT } from './TabBar';
import { theme } from './theme';

export function ToastHost() {
  const queue = useToastQueue((state) => state.queue);
  const dismiss = useToastQueue((state) => state.dismiss);
  const insets = useSafeAreaInsets();
  const head = queue[0];

  // Announced as it becomes the head rather than as it is queued: a sentence spoken while
  // three others are still ahead of it is a sentence about a screen the player is not on.
  // Keyed on the toast itself, so two identical messages are two toasts and the second is
  // held for its own 2,6 seconds rather than inheriting what is left of the first one's.
  useEffect(() => {
    if (head === undefined) return;

    announce(head.message, head.politeness);
    const held = setTimeout(() => dismiss(head.id), theme.motion.hold.toast);

    return () => clearTimeout(held);
  }, [head, dismiss]);

  if (head === undefined) return null;

  return (
    // `pointerEvents: 'none'` on the container, per 9.2 — a toast never blocks a tap, which
    // is also why the dismiss is a timer rather than a control.
    <View
      pointerEvents="none"
      style={[s.host, { bottom: TAB_BAR_HEIGHT + insets.bottom + theme.space.sm }]}
    >
      <Toast toast={head} />
    </View>
  );
}

export interface ToastProps {
  readonly toast: ToastMessage;
}

/**
 * One message. Exported because it is 9.2's drawn object and the host is its wiring — a
 * screen never renders one, but a test and a future in-sheet notice read the same shape.
 */
export function Toast({ toast }: ToastProps) {
  return (
    <View
      style={[s.toast, SURFACE[toast.tone]]}
      // Already announced by the host. A reader that walked into it would hear the sentence
      // a second time, 2,6 seconds after the first.
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Text style={s.message}>{toast.message}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  host: {
    position: 'absolute',
    left: theme.space.lg,
    right: theme.space.lg,
    zIndex: theme.layer.toast,
  },
  toast: {
    borderRadius: theme.radius.toast,
    paddingVertical: theme.space.md,
    paddingHorizontal: theme.space.lg,
  },
  message: { ...theme.type.inlineTitle, color: theme.color.surface },
});

const SURFACE = StyleSheet.create({
  base: { backgroundColor: theme.color.night },
  // `mintInk` and not `mint`: white on mint is 4,07:1, which Rule C refuses outright.
  ok: { backgroundColor: theme.color.mintInk },
  bad: { backgroundColor: theme.color.red },
});

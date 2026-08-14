/**
 * The bottom sheet, per design-system 9.1 — and a **real modal**, not a card that
 * happens to sit at the bottom of the screen.
 *
 * ```
 * scrim   rgba(10,52,65,.45)          ← the night colour at 45%, not black
 * sheet   bottom 0, maxHeight 88%, radius 22 22 0 0
 * grab    36 x 4, line, radius 2, centred, marginBottom 9
 * close   28 circle, line2 background, top-right
 * ```
 *
 * ## What "a real modal" costs, and who pays which part
 *
 * Three obligations (design-system Part 13), and they are not all met by the same
 * mechanism:
 *
 * 1. **Siblings hidden from screen readers.** React Native's `Modal` presents in its own
 *    window, which handles it natively — but only for the *other* window. The tree behind
 *    still has to say so itself, which is why the screen root spreads
 *    {@link behindSheet}. That is also the only half of this a test can observe.
 * 2. **Focus moves in, and back to the trigger on close.** Done here with
 *    `AccessibilityInfo.setAccessibilityFocus`: onto the sheet's own heading when it
 *    opens, and onto `returnFocusTo` when it closes — otherwise a screen-reader user is
 *    returned to the top of the screen and has to find their place again.
 * 3. **The Android hardware back gesture dismisses it.** `onRequestClose`, which Android
 *    requires and iOS ignores.
 *
 * The scrim dismisses on tap. That is safe here because a sheet's dismissal is always its
 * *non-committal* option — a sheet that made a destructive choice reachable by tapping
 * outside it would be a different component.
 *
 * **9.3's single root-level overlay host is not needed for this one.** That rule exists
 * because `zIndex` is scoped to the parent in React Native, so an overlay rendered where
 * it was triggered can end up underneath a sibling. A `Modal` is a separate native window
 * and is not in the layer order at all, so it is already out of any dark card's repaint.
 * The popover, which is not a window, is the component that will need the host.
 *
 * Motion is skipped when the OS asks for reduced motion (Part 13), which for a `Modal` is
 * the difference between `slide` and `none`.
 */

import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import {
  AccessibilityInfo,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
  findNodeHandle,
} from "react-native";

import { CloseControl } from "./CloseControl";
import { theme } from "./theme";

/** A ref to whatever should hold accessibility focus — a host element, not a component. */
export type FocusTarget = RefObject<View | null>;

export interface BottomSheetProps {
  readonly visible: boolean;
  /** Dismissal: the scrim, the close control and the Android back gesture all use it. */
  readonly onClose: () => void;
  readonly title: string;
  /** Names the sheet's own close control. Never just "Close" — see `CloseControl`. */
  readonly closeLabel: string;
  /** The control that opened the sheet. Focus returns here when it closes. */
  readonly returnFocusTo?: FocusTarget;
  readonly children: ReactNode;
}

/**
 * The props a screen puts on its root while one of its sheets is open.
 *
 * Both are needed and neither is redundant: `accessibilityElementsHidden` is iOS and
 * `importantForAccessibility` is Android. **The sheet must not be rendered inside the
 * element carrying these** — it would hide itself along with everything else.
 */
export function behindSheet(open: boolean) {
  return {
    accessibilityElementsHidden: open,
    importantForAccessibility: open ? ("no-hide-descendants" as const) : ("auto" as const),
  };
}

export function BottomSheet({
  visible,
  onClose,
  title,
  closeLabel,
  returnFocusTo,
  children,
}: BottomSheetProps) {
  const reducedMotion = useReducedMotion();
  const heading = useRef<View | null>(null);
  const wasVisible = useRef(visible);

  useEffect(() => {
    if (visible === wasVisible.current) return;
    wasVisible.current = visible;
    moveAccessibilityFocus(visible ? heading : returnFocusTo);
  }, [visible, returnFocusTo]);

  return (
    <Modal
      visible={visible}
      transparent
      // Android's hardware back. Required there, ignored on iOS.
      onRequestClose={onClose}
      animationType={reducedMotion ? "none" : "slide"}
    >
      <View style={s.stage}>
        {/* Dismissal, not a control: the sheet's close carries the name, and a second
            unnamed button spanning the screen is noise in the reading order. */}
        <Pressable
          style={s.scrim}
          onPress={onClose}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        />

        <View style={s.sheet} accessibilityViewIsModal>
          <View style={s.grab} />

          <View style={s.head}>
            {/* `accessible` on the wrapper, not the Text: focus has to land on a host
                element this component holds a ref to, and it must be the heading alone
                rather than the row it shares with the close control. */}
            <View ref={heading} accessible accessibilityRole="header" style={s.titleBox}>
              <Text style={s.title}>{title}</Text>
            </View>
            <CloseControl onPress={onClose} accessibilityLabel={closeLabel} />
          </View>

          {children}
        </View>
      </View>
    </Modal>
  );
}

function moveAccessibilityFocus(target: FocusTarget | undefined): void {
  if (target === undefined) return;
  const tag = findNodeHandle(target.current);
  if (tag === null) return;
  AccessibilityInfo.setAccessibilityFocus(tag);
}

/**
 * Whether the OS has asked for reduced motion.
 *
 * Local to the one component in the app that animates. When a second lands, this moves
 * out and is read once from a context, which is what design-system Part 13 asks for —
 * moving it now would be a shared module with one caller.
 */
function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    let live = true;
    void AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (live) setReduced(enabled);
    });

    const subscription = AccessibilityInfo.addEventListener(
      "reduceMotionChanged",
      setReduced,
    );
    return () => {
      live = false;
      subscription.remove();
    };
  }, []);

  return reduced;
}

const s = StyleSheet.create({
  stage: { flex: 1, justifyContent: "flex-end" },
  scrim: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.scrim },
  sheet: {
    backgroundColor: theme.color.surface,
    borderTopLeftRadius: theme.radius.sheet,
    borderTopRightRadius: theme.radius.sheet,
    // A proportion, never a fixed height: the sheet grows with its content and with the
    // OS text size, and stops before it becomes the screen.
    maxHeight: "88%",
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.sm,
    paddingBottom: theme.space.xxl,
    gap: theme.space.sm,
    ...theme.shadow.sheet,
  },
  grab: {
    width: theme.size.grabber.width,
    height: theme.size.grabber.height,
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.line,
    alignSelf: "center",
    marginBottom: theme.space.sm,
  },
  head: {
    flexDirection: "row",
    alignItems: "center",
    gap: theme.space.sm,
    marginBottom: theme.space.xxs,
  },
  titleBox: { flex: 1 },
  title: { ...theme.type.h1, color: theme.color.ink },
});

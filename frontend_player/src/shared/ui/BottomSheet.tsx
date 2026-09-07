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
 *    {@link behindOverlay}. That is also the only half of this a test can observe.
 * 2. **Focus moves in, and back to the trigger on close.** Done with
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
 * `Popover` reaches the same place the same way, so the host has no consumer yet — it
 * becomes necessary for the first overlay that has to stay inside the React tree.
 *
 * Motion is skipped when the OS asks for reduced motion (Part 13), which for a `Modal` is
 * the difference between `slide` and `none`.
 *
 * ## The body scrolls, and that is what makes 88% a cap rather than a guillotine
 *
 * 9.1 stops the sheet at `maxHeight: 88%` so it never becomes the screen. Without a scroll
 * underneath it that number does not bound the sheet, it **truncates** it: the children keep
 * their heights, the column overflows, and whatever is last in it goes off the bottom of the
 * screen — which on a sheet is always the controls, because a sheet reads statement first and
 * answer last. That is not a hypothetical: `SH.saveav` draws a seven-by-three grid above two
 * buttons, and on the narrowest phone the buttons were simply not there.
 *
 * So the head is fixed and **the children are a `ScrollView` that shrinks**, which is what
 * the cap has to mean: at any content height the grab, the title and the close control stay
 * put, and everything below them is reachable. The bottom padding moves onto the scrolled
 * content, or the last control would sit against the edge of the screen at full scroll.
 *
 * **Nothing is pinned.** A footer slot holding the controls outside the scroll was the other
 * way, and it is a bigger claim than this component can make on every caller's behalf: three
 * of the four sheets in the app end in something that is not a control, and a slot that
 * pinned the last child would move a sentence away from the paragraph it belongs to.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { CloseControl } from './CloseControl';
import { moveAccessibilityFocus, useReducedMotion, type FocusTarget } from './overlay';
import { theme } from './theme';

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
      animationType={reducedMotion ? 'none' : 'slide'}
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

          {/* `flexShrink` is what lets the cap apply to this rather than to the sheet's
              last child: without it the ScrollView takes its content's full height and the
              overflow happens one level up, where nothing can scroll it. */}
          <ScrollView style={s.body} contentContainerStyle={s.bodyContent}>
            {children}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  stage: { flex: 1, justifyContent: 'flex-end' },
  scrim: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.scrim },
  sheet: {
    backgroundColor: theme.color.surface,
    borderTopLeftRadius: theme.radius.sheet,
    borderTopRightRadius: theme.radius.sheet,
    // A proportion, never a fixed height: the sheet grows with its content and with the
    // OS text size, and stops before it becomes the screen.
    maxHeight: '88%',
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.sm,
    gap: theme.space.sm,
    ...theme.shadow.sheet,
  },
  // The cap lands here. `flexShrink` without a `flexGrow`, so a short sheet is still the
  // height of its content and only a tall one is bounded.
  body: { flexShrink: 1 },
  // The sheet's own bottom padding, moved onto the scrolled content: on the sheet it would
  // sit below the scroll and leave the last control against the screen edge at full scroll.
  bodyContent: { gap: theme.space.sm, paddingBottom: theme.space.xxl },
  grab: {
    width: theme.size.grabber.width,
    height: theme.size.grabber.height,
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.line,
    alignSelf: 'center',
    marginBottom: theme.space.sm,
  },
  head: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    marginBottom: theme.space.xxs,
  },
  titleBox: { flex: 1 },
  title: { ...theme.type.h1, color: theme.color.ink },
});

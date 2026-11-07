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
 * 1. **Siblings hidden from screen readers.** The stage handles the other window, or the
 *    other layers — but the tree behind still has to say so itself, which is why the screen
 *    root spreads {@link behindOverlay}. That is also the only half of this a test can observe.
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
 * **The sheet sits on `ModalStage`, and where that is depends on the platform.** On iOS it is
 * React Native's `Modal` — a separate native window, out of any dark card's repaint, which is
 * why 9.3's root-level overlay host was not needed for a sheet. On Android it is a layer in
 * the tree, drawn by that host, because the native window is unusable there while Reanimated
 * 3.16 is in the app — its content is 0 × 0 and every press inside it is terminated
 * (`overlay.tsx`'s `OverlayHost` records the measurement). A `Modal` presents in its own
 * window, which handles obligation 1 natively for iOS; the host does it for the whole app on
 * Android; and the screen root's {@link behindOverlay} is what a test can observe on both.
 *
 * Motion is skipped when the OS asks for reduced motion (Part 13), which for the stage is
 * the difference between `slide` and `none`.
 *
 * ## The body scrolls, and that is what makes 88% a cap rather than a guillotine
 *
 * 9.1 stops the sheet at `maxHeight: 88%` so it never becomes the screen. Without a scroll
 * underneath it that number does not bound the sheet, it **truncates** it: the children keep
 * their heights, the column overflows, and whatever is last in it goes off the bottom of the
 * screen — which on a sheet is always the controls, because a sheet reads statement first and
 * answer last. That is not a hypothetical: `SH.saveav` draws the week grid above two
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
 *
 * **A body that is a long list scrolls itself** (`scrollsItself`, #757): *Find a court* lists
 * every court hour of a fortnight, hundreds of rows, and a list that long is virtualised
 * (`docs/architecture.md` Part 12) — which a `VirtualizedList` inside this `ScrollView` would
 * defeat. So the sheet draws no scroll around such a body, and the list lays itself out with
 * `SHEET_LIST`: the same shrink, so the cap still bounds it, and the same bottom padding on its
 * content.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { KeyboardAvoidingView, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { KEYBOARD_AVOIDANCE, dismissKeyboard } from '@/shared/lib/platform/keyboard';

import { CloseControl } from './CloseControl';
import { ModalStage } from './ModalStage';
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
  /**
   * **A mark over a centred title** — the invitation sheet's head (club 5): the close alone on the
   * top row, then the mark and the title under it, centred. Absent, the title shares the top row
   * with the close, as every other sheet's does.
   */
  readonly mark?: ReactNode;
  /**
   * Whether a tap in the sheet keeps the keyboard up — **forwarded, not designed**, as
   * `ShellScreen`'s is. By default a tap on the body outside a field takes the focus back, and
   * React Native does that with a native blur; on iOS, under the New Architecture, Stripe's card
   * field blurred that way traps and the app closes (#552 — the first-yes sheet's crash). So a
   * sheet holding the card field keeps the focus where it is, and the field's own unmount, or a way
   * out of the sheet, releases it. Off everywhere else, which keeps the default.
   */
  readonly keepsKeyboardOnTap?: boolean;
  /**
   * The body is a virtualised list that scrolls itself — see the module note. It takes
   * `SHEET_LIST`'s `style` and `contentContainerStyle`.
   */
  readonly scrollsItself?: boolean;
  readonly children: ReactNode;
}

export function BottomSheet({
  visible,
  onClose,
  title,
  closeLabel,
  returnFocusTo,
  mark,
  keepsKeyboardOnTap = false,
  scrollsItself = false,
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

  /**
   * Every way out goes through here. A field in the sheet may still hold the keyboard — the card's
   * fields do — and a window closed under a focused field is the crash the phone reported, so the
   * keyboard goes first.
   */
  const dismiss = () => {
    dismissKeyboard();
    onClose();
  };

  return (
    <ModalStage
      visible={visible}
      // Android's hardware back. iOS never asks.
      onRequestClose={dismiss}
      animationType={reducedMotion ? 'none' : 'slide'}
      layer="sheet"
    >
      {/* Lifted above the keyboard on iOS, where it covers a field at the bottom of the sheet;
          Android resizes the window itself. */}
      <KeyboardAvoidingView
        style={s.stage}
        behavior={KEYBOARD_AVOIDANCE}
        testID="bottom-sheet-stage"
      >
        {/* Dismissal, not a control: the sheet's close carries the name, and a second
            unnamed button spanning the screen is noise in the reading order. */}
        <Pressable
          style={s.scrim}
          onPress={dismiss}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        />

        <View style={s.sheet} accessibilityViewIsModal testID="bottom-sheet">
          <View style={s.grab} />

          {mark === undefined ? (
            <View style={s.head}>
              {/* `accessible` on the wrapper, not the Text: focus has to land on a host
                  element this component holds a ref to, and it must be the heading alone
                  rather than the row it shares with the close control. */}
              <View ref={heading} accessible accessibilityRole="header" style={s.titleBox}>
                <Text style={s.title}>{title}</Text>
              </View>
              <CloseControl onPress={dismiss} accessibilityLabel={closeLabel} />
            </View>
          ) : (
            <>
              <View style={[s.head, s.headClose]}>
                <CloseControl onPress={dismiss} accessibilityLabel={closeLabel} />
              </View>
              {/* The mark is the thing the title is about, drawn — hidden by the caller, and the
                  heading is still the one element focus lands on. */}
              <View style={s.hero}>
                {mark}
                <View ref={heading} accessible accessibilityRole="header">
                  <Text style={[s.title, s.centred]}>{title}</Text>
                </View>
              </View>
            </>
          )}

          {/* `flexShrink` is what lets the cap apply to this rather than to the sheet's
              last child: without it the ScrollView takes its content's full height and the
              overflow happens one level up, where nothing can scroll it. */}
          {scrollsItself ? (
            children
          ) : (
            <ScrollView
              style={s.body}
              contentContainerStyle={s.bodyContent}
              // A tap on a field or a button while the keyboard is up reaches it, not the keyboard —
              // and a sheet with the card field keeps the keyboard on every tap (the prop's note).
              keyboardShouldPersistTaps={keepsKeyboardOnTap ? 'always' : 'handled'}
            >
              {children}
            </ScrollView>
          )}
        </View>
      </KeyboardAvoidingView>
    </ModalStage>
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
  // The close alone on the top row, at its trailing edge.
  headClose: { justifyContent: 'flex-end' },
  hero: { alignItems: 'center', gap: theme.space.md },
  centred: { textAlign: 'center' },
});

/** **The layout a body that scrolls itself takes** (`scrollsItself`): the cap's shrink, and the padding. */
export const SHEET_LIST = { style: s.body, contentContainerStyle: s.bodyContent } as const;

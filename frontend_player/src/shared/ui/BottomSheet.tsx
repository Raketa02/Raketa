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
 *
 * ## A body that changes height can bring the sheet with it (`layoutTransition`)
 *
 * The sheet sits on the bottom edge, so a body that grows moves the sheet's top edge up. A caller
 * that animates such a change — the record's *Full record* fold — hands its Reanimated layout
 * transition here, and the sheet and its scroll move with the body rather than jumping to the
 * new height. **A transition, never a height animated frame by frame**: under the New
 * Architecture Reanimated commits a layout prop to the shadow tree and skips that commit while
 * React commits anywhere in the app, so a per-frame height froze and jumped (`RecordDetails`).
 * Absent, the sheet takes its new height at once, as every other sheet does, and draws plain views.
 *
 * ## A sheet can close on a swipe down (`closesOnSwipe`)
 *
 * **Needs your answer** closes on ✕, the backdrop or a pull down (#816; 9.1 as amended). The pull is
 * read on **the head**, the grab and the title row, and never on the body: the body holds sideways
 * rails and its own scroll, and a gesture laid over them would steal theirs. Under the finger the
 * sheet follows it down; on release it closes or springs back (`sheetSwipeGeometry`). It is React
 * Native's `Animated` on the native driver, moving `transform` only, as the swipe row and the deck
 * do. A sheet that also moves with its body (`layoutTransition`) is Reanimated's view, which takes
 * no such value, so there the release still closes it but the sheet does not follow the finger.
 * Every other sheet is as it was: nothing on its head claims a touch.
 */

import { useEffect, useMemo, useRef, useState, type ComponentProps, type ReactNode } from 'react';
import {
  Animated as Motion,
  KeyboardAvoidingView,
  PanResponder,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import Animated from 'react-native-reanimated';

import { KEYBOARD_AVOIDANCE, dismissKeyboard } from '@/shared/lib/platform/keyboard';

import { CloseControl } from './CloseControl';
import { ModalStage } from './ModalStage';
import { moveAccessibilityFocus, useReducedMotion, type FocusTarget } from './overlay';
import { claimsTheSheetSwipe, closesOnRelease, sheetDrop } from './sheetSwipeGeometry';
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
   * **One act on the title row**, between the title and the close — the group sheet's one button
   * (#800, home rows 6; 9.1 as amended 2026-11-14). Fixed with the head, never scrolled away from
   * the title it acts on. Not drawn on a sheet with a `mark`, whose close stands alone on its row.
   */
  readonly action?: ReactNode;
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
  /**
   * How the sheet and its scroll follow a body that changes height — a Reanimated layout
   * transition, forwarded, not designed (see the module note). Not applied to a body that
   * scrolls itself.
   */
  readonly layoutTransition?: SheetLayoutTransition;
  /**
   * **A pull down on the head closes it** — see the module note. Off by default. A pull that closes
   * calls `onClose` and leaves the sheet where the finger left it, for the window to take away, so a
   * caller that asks for it closes the sheet when asked.
   */
  readonly closesOnSwipe?: boolean;
  readonly children: ReactNode;
}

/** What `BottomSheet`'s `layoutTransition` takes: Reanimated's own `layout`. */
export type SheetLayoutTransition = ComponentProps<typeof Animated.View>['layout'];

export function BottomSheet({
  visible,
  onClose,
  title,
  closeLabel,
  returnFocusTo,
  mark,
  action,
  keepsKeyboardOnTap = false,
  scrollsItself = false,
  layoutTransition,
  closesOnSwipe = false,
  children,
}: BottomSheetProps) {
  const reducedMotion = useReducedMotion();
  // Reanimated's views only where a caller moves the sheet; every other sheet keeps plain ones.
  const moves = layoutTransition !== undefined;
  // React Native's own animated view where the sheet follows a pull down (the module note).
  const follows = closesOnSwipe && !moves;
  const Sheet = moves ? Animated.View : follows ? Motion.View : View;
  const Body = moves ? Animated.ScrollView : ScrollView;
  const moving = moves ? { layout: layoutTransition } : {};
  const heading = useRef<View | null>(null);
  const wasVisible = useRef(visible);
  /** How far below its place a pull has the sheet — 0 at rest. Made once, not on every render. */
  const [drop] = useState(() => new Motion.Value(0));
  /** When the finger last moved, on the touch's own clock — what a flick's speed is read against. */
  const lastMoveAt = useRef(0);

  useEffect(() => {
    if (visible === wasVisible.current) return;
    wasVisible.current = visible;
    // A sheet closed by a pull opens again where it belongs.
    if (visible) drop.setValue(0);
    moveAccessibilityFocus(visible ? heading : returnFocusTo);
  }, [visible, returnFocusTo, drop]);

  /**
   * Every way out goes through here. A field in the sheet may still hold the keyboard — the card's
   * fields do — and a window closed under a focused field is the crash the phone reported, so the
   * keyboard goes first.
   */
  const dismiss = () => {
    dismissKeyboard();
    onClose();
  };

  /**
   * What the pull's handlers read when they run — made once, so a render mid-pull never drops the
   * gesture, and reading the render that is on screen rather than the one they were made in (the
   * swipe row's pattern).
   */
  const now = useRef({ dismiss, reducedMotion });
  now.current = { dismiss, reducedMotion };

  const pull = useMemo(() => {
    if (!closesOnSwipe) return undefined;
    const settle = () => {
      if (now.current.reducedMotion) {
        drop.setValue(0);
        return;
      }
      Motion.timing(drop, {
        toValue: 0,
        duration: theme.motion.settle,
        useNativeDriver: true,
      }).start();
    };
    return PanResponder.create({
      // Never on the press itself: ✕ is on the head, and a tap has to reach it.
      onMoveShouldSetPanResponder: (_event, gesture) => claimsTheSheetSwipe(gesture),
      onPanResponderTerminationRequest: () => false,
      onPanResponderMove: (event, gesture) => {
        lastMoveAt.current = event.nativeEvent.timestamp;
        drop.setValue(sheetDrop(gesture.dy));
      },
      onPanResponderRelease: (event, gesture) => {
        const still = event.nativeEvent.timestamp - lastMoveAt.current;
        if (closesOnRelease({ dy: gesture.dy, vy: gesture.vy, still })) now.current.dismiss();
        else settle();
      },
      onPanResponderTerminate: settle,
    });
  }, [closesOnSwipe, drop]);

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
          testID="bottom-sheet-scrim"
        />

        <Sheet
          style={[s.sheet, follows ? { transform: [{ translateY: drop }] } : undefined]}
          accessibilityViewIsModal
          testID="bottom-sheet"
          {...moving}
        >
          {/* The head: what a pull is read on, where the sheet asks for one. Its gap is the
              sheet's own, so the grab and the title stand where they always have. */}
          <View style={s.top} {...(pull === undefined ? {} : pull.panHandlers)}>
            <View style={s.grab} />

            {mark === undefined ? (
              <View style={s.head}>
                {/* `accessible` on the wrapper, not the Text: focus has to land on a host
                    element this component holds a ref to, and it must be the heading alone
                    rather than the row it shares with the close control. */}
                <View ref={heading} accessible accessibilityRole="header" style={s.titleBox}>
                  <Text style={s.title}>{title}</Text>
                </View>
                {action}
                <CloseControl onPress={dismiss} accessibilityLabel={closeLabel} />
              </View>
            ) : (
              <>
                <View style={[s.head, s.headClose]}>
                  <CloseControl onPress={dismiss} accessibilityLabel={closeLabel} />
                </View>
                {/* The mark is the thing the title is about, drawn — hidden by the caller, and
                    the heading is still the one element focus lands on. */}
                <View style={s.hero}>
                  {mark}
                  <View ref={heading} accessible accessibilityRole="header">
                    <Text style={[s.title, s.centred]}>{title}</Text>
                  </View>
                </View>
              </>
            )}
          </View>

          {/* `flexShrink` is what lets the cap apply to this rather than to the sheet's
              last child: without it the ScrollView takes its content's full height and the
              overflow happens one level up, where nothing can scroll it. */}
          {scrollsItself ? (
            children
          ) : (
            <Body
              style={s.body}
              contentContainerStyle={s.bodyContent}
              // A tap on a field or a button while the keyboard is up reaches it, not the keyboard —
              // and a sheet with the card field keeps the keyboard on every tap (the prop's note).
              keyboardShouldPersistTaps={keepsKeyboardOnTap ? 'always' : 'handled'}
              {...moving}
            >
              {children}
            </Body>
          )}
        </Sheet>
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
    gap: theme.space.sm,
    ...theme.shadow.sheet,
  },
  // The grab and the head, in one view a pull is read on: the sheet's own gap between them, and the
  // sheet's top padding and gutters taken inside it, so the strip over the grab and the gutters
  // beside the title are the head's to pull too. Every sheet stands exactly where it did.
  top: {
    gap: theme.space.sm,
    paddingTop: theme.space.sm,
    marginHorizontal: -theme.size.gutter,
    paddingHorizontal: theme.size.gutter,
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

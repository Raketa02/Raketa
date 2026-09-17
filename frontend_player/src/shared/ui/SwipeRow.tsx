/**
 * The swipe row, per design-system 6.15 — a list row that slides left to reveal **one** control
 * behind it, and nothing else.
 *
 * ## The swipe reveals; it never acts
 *
 * [#231](https://github.com/Raketa02/Raketa/issues/231) §3 refused a swipe on the deck because
 * *the cheapest gesture in the app must not carry the most durable act*, and that argument is kept
 * here by construction rather than by restraint: what a swipe does is move the card aside and show
 * a button. The act is the button's, and every caller so far puts a confirmation behind it
 * ([ADR-0165](../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §6). So the worst a stray thumb can do is uncover a word.
 *
 * ## Built on `PanResponder`, and it must not take the list's scroll
 *
 * React Native's own responder system, as the radius slider already drags — neither
 * `react-native-gesture-handler` nor `reanimated` is used for it (ADR-0165 §6; both are in the
 * app since ADR-0176, for the radar's field alone). The row **never
 * claims the touch when it lands**: the card under the finger is a door, and a tap has to reach it.
 * It claims on a *move*, and only once `swipeRowGeometry`'s rule says the finger has travelled the
 * intent distance across and further across than down — until then every move is the list's, and a
 * drift down the screen scrolls the list exactly as it did before this row could move. Once
 * claimed, the list may not take the gesture back (`onPanResponderTerminationRequest: false`), on
 * the slider's own argument: a row that lost the finger to a scroll would be left half open.
 *
 * ## Where the card goes
 *
 * Under the finger it tracks exactly, clamped to the control's width — no elastic, no overshoot.
 * On release it **settles** to one of two places, revealed or closed, over `motion.settle`, which
 * is skipped under reduced motion and under a running screen reader (`useCollapsedPresentation`),
 * where it is drawn at rest.
 *
 * ## What the control is, and what colour it is not
 *
 * 6.1 `dark`'s fill at the row's full height — `night`, `night2` under the finger, the label in
 * `surface` — and **not coral**: §1.2's coral list is closed, and picking the meaning lands on
 * `ink`, as the rules say it will. The act a swipe reveals is the one the screens draw `secondary`,
 * because taking yourself off a court is never the primary act on a screen about arranging one; a
 * `secondary` surface would vanish against the paper behind a card, so the revealed control takes
 * the one filled variant with no meaning attached.
 *
 * ## What a screen reader gets
 *
 * A swipe is a gesture a screen reader consumes before the row sees it, so the swipe is **never the
 * only path** (`the-words.md` §20.12). Two things follow. The control behind a closed row is hidden
 * from assistive technology — a listener must not be offered a button they cannot see, in the
 * middle of a list of doors — and the caller puts the same act on the card as an
 * `accessibilityAction`, which is how a listener reaches it. Revealed, the control is an ordinary
 * button with its word on its face.
 *
 * ## A longer word wraps, and the control holds it
 *
 * `reveal` was sized so *Leave the game* sits on one line with `space.md` either side; *Remove
 * the challenge* ([#428](https://github.com/Raketa02/Raketa/issues/428)) does not fit that and
 * wraps to two, which the row's full height holds. The label is centred so the second line sits
 * under the first rather than left of it, and the width does not grow for the word: `reveal` is how
 * far the card travels, and a control that widened per caller would move the card different
 * distances on neighbouring rows.
 *
 * ## `reveal` absent means the row does not move
 *
 * No responder is attached and nothing is drawn behind the card: *a swipe that reveals nothing on
 * rows where there is nothing to do* (#420 story 30) is a row that does not answer the gesture at
 * all, not one that slides to show an empty space. A row whose control is withdrawn while it is
 * open closes.
 */

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Animated, PanResponder, Pressable, StyleSheet, Text, View } from 'react-native';

import { useCollapsedPresentation } from './overlay';
import { claimsTheSwipe, settlesTo, shifted, type SwipeRest } from './swipeRowGeometry';
import { theme } from './theme';

const REVEAL = theme.size.swipeRow.reveal;

/** The one control a swipe uncovers: its word, and what pressing it does. */
export interface RevealedControl {
  readonly label: string;
  readonly onPress: () => void;
}

export interface SwipeRowProps {
  /** The row itself — a card, and usually a door. It is what slides. */
  readonly children: ReactNode;
  /** What is behind the card, or nothing — and with nothing, the row does not move at all. */
  readonly reveal?: RevealedControl;
}

export function SwipeRow({ children, reveal }: SwipeRowProps) {
  const collapsed = useCollapsedPresentation();
  const [rest, setRest] = useState<SwipeRest>('closed');
  /** Where the card is drawn, in points left of home. Driven directly during a swipe. */
  const shift = useRef(new Animated.Value(0)).current;
  /** Where the card was when the touch was claimed — the base every move is measured from. */
  const claimedAt = useRef(0);

  /**
   * The pan handlers are created once, so they must not close over a render's values. The ref
   * holds whatever the current render knows — where the row rests, and whether motion is
   * collapsed — so a swipe reads the row as it is on screen rather than as it was when the
   * handlers were made.
   */
  const now = useRef({ rest, collapsed });
  now.current = { rest, collapsed };

  const settle = useRef((to: SwipeRest) => {
    const x = to === 'revealed' ? -REVEAL : 0;
    setRest(to);
    if (now.current.collapsed) {
      shift.setValue(x);
      return;
    }
    Animated.timing(shift, {
      toValue: x,
      duration: theme.motion.settle,
      useNativeDriver: true,
    }).start();
  }).current;

  const responder = useRef(
    PanResponder.create({
      // Never on the press itself: the card is a door, and a tap has to reach it.
      onMoveShouldSetPanResponder: (_event, gesture) => claimsTheSwipe(gesture, now.current.rest),
      // The list may not take the gesture back mid-swipe — the slider's own rule.
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        claimedAt.current = now.current.rest === 'revealed' ? -REVEAL : 0;
      },
      onPanResponderMove: (_event, gesture) => {
        shift.setValue(shifted(claimedAt.current + gesture.dx));
      },
      onPanResponderRelease: (_event, gesture) => {
        settle(settlesTo(claimedAt.current + gesture.dx));
      },
      // The system took the touch — a call, a notification. The card still has to land.
      onPanResponderTerminate: (_event, gesture) => {
        settle(settlesTo(claimedAt.current + gesture.dx));
      },
    }),
  ).current;

  // A control withdrawn from under an open row: close, rather than frame an empty space.
  useEffect(() => {
    if (reveal === undefined && rest === 'revealed') settle('closed');
  }, [reveal, rest, settle]);

  const revealed = rest === 'revealed';

  return (
    <View {...(reveal === undefined ? {} : responder.panHandlers)}>
      {reveal === undefined ? null : (
        <View
          style={s.behind}
          // Behind a closed card the control is not on screen, and a listener must not be
          // offered it there: the caller's `accessibilityAction` on the card is their way to it.
          accessibilityElementsHidden={!revealed}
          importantForAccessibility={revealed ? 'auto' : 'no-hide-descendants'}
        >
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={reveal.label}
            onPress={() => {
              // The swipe only reveals. The row closes behind the press, so whatever the act
              // opens returns to a list at rest.
              settle('closed');
              reveal.onPress();
            }}
            style={({ pressed }) => [s.control, pressed ? s.controlPressed : undefined]}
          >
            <Text style={s.controlLabel}>{reveal.label}</Text>
          </Pressable>
        </View>
      )}

      <Animated.View style={{ transform: [{ translateX: shift }] }}>{children}</Animated.View>
    </View>
  );
}

const s = StyleSheet.create({
  // The control's box: the full height of the row, at its right edge, as wide as the card
  // travels — so a card fully aside shows the whole control and nothing past it.
  behind: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    right: 0,
    width: REVEAL,
  },
  // 6.1 `dark`'s fill and press, at the row's height rather than a button's — see the module
  // note for why it is not coral.
  control: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.card,
    backgroundColor: theme.color.night,
  },
  controlPressed: { backgroundColor: theme.color.night2 },
  // Centred, because a word longer than the reveal wraps to a second line — *Remove the
  // challenge* does (#428) — and the control is the row's full height, which holds two; a
  // second line left-aligned under a centred first would read as a mistake. The width does not
  // grow for it: `reveal` is how far the card travels, not how long a word may be.
  controlLabel: {
    ...theme.type.btn,
    color: theme.color.surface,
    textAlign: 'center',
    paddingHorizontal: theme.space.sm,
  },
});

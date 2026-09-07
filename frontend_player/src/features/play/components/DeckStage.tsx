/**
 * The one thing on the deck that moves: **a card arriving, and a card leaving.**
 *
 * It animates in, and translates and rotates out — *"a transient object being manipulated
 * rather than a surface a finger rests on"*, which is
 * [#219](https://github.com/Raketa02/Raketa/issues/219) B3's whole argument and the reason the
 * deck card is the only user of `radius.deckCard` and the fourth shadow.
 *
 * ## The card leaves in the direction of the answer
 *
 * *Let's play* sends it **right** and *Not today* sends it **left**, which is the two buttons'
 * own order on the card underneath. It is the deck's one piece of feedback that is not a
 * sentence: the toast names the person and the answer a beat later, and this says which of the
 * two buttons was pressed at the instant it was pressed — worth having, because the two are 1:2
 * in width and a thumb lands on the wrong one.
 *
 * The direction is the whole of what the answer changes here. The travel, the turn, the fade
 * and the duration are one pair of animations mirrored, rather than two, because *left* and
 * *right* are the same act about two answers and a second set of numbers would be two things
 * to keep in step.
 *
 * ## It is a leaving animation and never a promise of a gesture
 *
 * [#231](https://github.com/Raketa02/Raketa/issues/231) §3 decided against a swipe, and **not
 * on cost**: `RadiusSlider` already drags on the built-in `PanResponder` at zero new
 * dependencies. The argument is that *Show them again* was struck, leaving `PASS_SUPPRESS` at
 * thirty days per account with nothing that reverses one — so a swipe would put the cheapest
 * gesture in the app on the most durable act in the feature, and it would flatten the 1:2
 * ratio the layout uses to say which answer is which. So this component has **no responder,
 * no pan and no drag threshold**, and neither `react-native-gesture-handler` nor
 * `react-native-reanimated` is added for it. What is left is `Animated`, which React Native
 * ships.
 *
 * ## The durations live here rather than in the theme
 *
 * `theme.motion` is *"one entrance, one sheet, one popover, one fade"* and holds the two
 * **shared** floors beside them; the engine fill's 550-per-seat stagger is deliberately not
 * there because *"it is the court's own and belongs beside the animation it drives"*. This is
 * the same case — one surface, one pair of animations, and numbers that mean nothing anywhere
 * else. The arrival borrows the system's `motion.rise`, because a card appearing is the
 * entrance every other surface in the app already uses; only the departure is the deck's own.
 *
 * ## Collapsed presentation lands the card, and still lands it
 *
 * `useCollapsedPresentation()` is one condition satisfied by **either** reduced motion or a
 * running screen reader (§20.11). Under it there is no travel and no fade — but `onLeft` is
 * still called, because it is not a decoration: it is what tells the screen the card is gone
 * and what unlocks the two buttons. A callback that only fired when the animation ran would
 * leave a listener holding a deck that never advances, which is the failure the whole
 * collapse rule exists to prevent.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { Animated } from 'react-native';

import { theme, useCollapsedPresentation } from '@/shared/ui';

/**
 * How long a card takes to leave — the prototype's `cardout`, kept.
 *
 * Shorter than the arrival on purpose: the answer has already been given, and the only thing
 * this beat buys is seeing that it landed. Long enough to read as *that one is gone*, short
 * enough that a player answering ten cards is not waiting on it nine times.
 */
const LEAVING_MS = 240;

/**
 * How far a leaving card travels, and how far it turns — the prototype's `cardout`, **grown to
 * carry a direction**.
 *
 * `cardout` shifted 40 points and turned 3 degrees, which reads as a card settling because it
 * was the only way a card could leave. Once the two answers leave opposite ways the movement
 * has to be legible as a *direction* within the 240 ms before the fade takes it, which 40
 * points is not: at the width of a deck card it is a nudge either way.
 *
 * Both numbers are **magnitudes**, and the answer supplies the sign.
 */
const LEAVING_SHIFT = 160;
const LEAVING_TURN = 8;

/** Where an arriving card comes from — `cardin`, at the system's own entrance duration. */
const ARRIVING_LIFT = 10;
const ARRIVING_SCALE = 0.98;

/**
 * The two answers, as the two ways off the screen. **Named for the answer and not for the
 * direction**: which way a yes goes is this component's decision, and a prop spelling it
 * `'right'` would put that decision in every caller.
 */
export type DeckExit = 'yes' | 'no';

export interface DeckStageProps {
  /**
   * The answer this card was given and is leaving on, or `undefined` while it is still being
   * decided.
   *
   * The screen owns it, because *which card is showing* is derived from the deal minus the one
   * leaving, and is deliberately held nowhere else (`playSession`).
   */
  readonly leaving: DeckExit | undefined;
  /**
   * The card has gone. Called once, whether it travelled or not.
   *
   * This unlocks the two buttons and advances the deck, so it is a **fact** rather than an
   * animation's courtesy.
   */
  readonly onLeft: () => void;
  readonly children: ReactNode;
}

export function DeckStage({ leaving, onLeft, children }: DeckStageProps) {
  const collapsed = useCollapsedPresentation();
  // A yes goes right, a pass goes left. Held as a **sign** rather than as two interpolations,
  // so the one that is mid-flight when a refusal returns the card is the one reset to nought.
  const way = leaving === 'yes' ? 1 : -1;
  // One value per phase, and each drives every transform in it: a card is one object moving,
  // where four values would be four things able to be halfway through different animations.
  const arrival = useRef(new Animated.Value(0)).current;
  const departure = useRef(new Animated.Value(0)).current;
  // A ref rather than a dependency: the handler closes over the card that was answered, and
  // re-running the flight because a parent re-rendered would restart a card mid-exit.
  const landed = useRef(onLeft);
  landed.current = onLeft;

  useEffect(() => {
    if (collapsed) {
      arrival.setValue(1);
      return;
    }

    const rise = Animated.timing(arrival, {
      toValue: 1,
      duration: theme.motion.rise,
      useNativeDriver: true,
    });
    rise.start();
    return () => rise.stop();
  }, [collapsed, arrival]);

  useEffect(() => {
    if (leaving === undefined) {
      // **A card that comes back comes back straight.** An answer refused puts the card on
      // screen again, and a stopped `Animated.Value` keeps whatever fraction of the flight it
      // reached — so without this the returned card sits shifted and turned, mid-exit, on the
      // one path the screen documents as recoverable.
      departure.setValue(0);
      return;
    }

    if (collapsed) {
      landed.current();
      return;
    }

    const flight = Animated.timing(departure, {
      toValue: 1,
      duration: LEAVING_MS,
      useNativeDriver: true,
    });
    flight.start(({ finished }) => {
      if (finished) landed.current();
    });

    // Unmounted mid-flight — the deal was replaced, or the tab was left. Stopping is what
    // keeps the callback from firing into a screen that is no longer there.
    return () => flight.stop();
  }, [leaving, collapsed, departure]);

  return (
    <Animated.View
      // Remounted per card by the caller's `key`, so the arrival runs once per person rather
      // than once per render.
      style={{
        opacity: leaving === undefined ? arrival : departure.interpolate(FADE_OUT),
        transform: [
          { translateX: departure.interpolate(slideOut(way)) },
          { translateY: arrival.interpolate(LIFT_IN) },
          { scale: arrival.interpolate(SCALE_IN) },
          { rotate: departure.interpolate(turnOut(way)) },
        ],
      }}
    >
      {children}
    </Animated.View>
  );
}

const FADE_OUT = { inputRange: [0, 1], outputRange: [1, 0] };
const slideOut = (way: number) => ({ inputRange: [0, 1], outputRange: [0, LEAVING_SHIFT * way] });
const turnOut = (way: number) => ({
  inputRange: [0, 1],
  outputRange: ['0deg', `${LEAVING_TURN * way}deg`],
});
const LIFT_IN = { inputRange: [0, 1], outputRange: [ARRIVING_LIFT, 0] };
const SCALE_IN = { inputRange: [0, 1], outputRange: [ARRIVING_SCALE, 1] };

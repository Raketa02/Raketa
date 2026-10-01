/**
 * **The Undo toast** — 9.2's toast with a draining ring and one action: *Booking in 10 s · Undo*
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the Games & Fill in screens A2.4, A10;
 * the mechanics §6.5).
 *
 * ```
 * ┌──────────────────────────────────────────┐
 * │ (◔)  Booking in 7 s                Undo  │   night, radius toast, padding md × lg
 * └──────────────────────────────────────────┘
 *  ring   size.undo.ring, onDarkHair track, volt arc draining clockwise to nothing
 *  words  inlineTitle, surface — the caller's, re-rendered as the count moves
 *  Undo   inlineTitle 700, volt, a button named for what it undoes, hit.btn
 * ```
 *
 * **Not the queue's toast.** 9.2's toast never blocks a tap and has no control, which is why its
 * dismiss is a timer; this one *is* a control, and its window is the whole point — so it is its own
 * component, placed by whoever holds the window, never pushed onto the queue. It neither arrives
 * nor leaves on an animation (1.5): the ring is the one thing that moves, because it is the time.
 *
 * **The ring drains on the UI thread** (Reanimated, as the radar's rings move), from what is left of
 * the window to nothing, linearly — a second is a second. Under reduced motion it stands at the
 * caller's whole-second count instead, stepping as the words do.
 *
 * The words are not a live region: a count that changes every second would talk over everything.
 * The caller announces the toast once, as it arrives.
 */

import { useEffect } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated, {
  Easing,
  useAnimatedProps,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Circle } from 'react-native-svg';

import { useReducedMotion } from './overlay';
import { theme } from './theme';

export interface UndoToastProps {
  /** *Booking in 7 s* — the caller's words. */
  readonly message: string;
  /** *Undo* */
  readonly actionLabel: string;
  /** The action's spoken name — what it undoes, never just *Undo*. */
  readonly actionAccessibilityLabel: string;
  readonly onAction: () => void;
  /** When the window closes (ms since the epoch) and how long it is: the ring drains to it. */
  readonly endsAt: number;
  readonly windowMs: number;
}

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

const { ring: RING, ringStroke: STROKE } = theme.size.undo;
const RADIUS = (RING - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function UndoToast({
  message,
  actionLabel,
  actionAccessibilityLabel,
  onAction,
  endsAt,
  windowMs,
}: UndoToastProps) {
  const reducedMotion = useReducedMotion();
  /** The share of the window left, 1 → 0. */
  const left = useSharedValue(1);

  // The drain: from what is left to nothing, once per window.
  useEffect(() => {
    if (reducedMotion) return;
    const remaining = Math.max(0, endsAt - Date.now());
    left.value = Math.min(1, remaining / windowMs);
    left.value = withTiming(0, { duration: remaining, easing: Easing.linear });
  }, [endsAt, windowMs, reducedMotion, left]);

  // Under reduced motion the ring stands where the words are, re-read as the caller re-renders.
  useEffect(() => {
    if (!reducedMotion) return;
    left.value = Math.min(1, Math.max(0, endsAt - Date.now()) / windowMs);
  });

  const animatedProps = useAnimatedProps(() => ({
    strokeDashoffset: CIRCUMFERENCE * (1 - left.value),
  }));

  return (
    <View style={s.toast} testID="undo-toast">
      <Svg
        width={RING}
        height={RING}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <Circle
          cx={RING / 2}
          cy={RING / 2}
          r={RADIUS}
          stroke={theme.color.onDarkHair}
          strokeWidth={STROKE}
          fill="none"
        />
        <AnimatedCircle
          cx={RING / 2}
          cy={RING / 2}
          r={RADIUS}
          stroke={theme.color.volt}
          strokeWidth={STROKE}
          strokeDasharray={CIRCUMFERENCE}
          animatedProps={animatedProps}
          strokeLinecap="round"
          fill="none"
          // From twelve o'clock, draining clockwise.
          transform={`rotate(-90 ${RING / 2} ${RING / 2})`}
        />
      </Svg>
      <Text style={s.message}>{message}</Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={actionAccessibilityLabel}
        onPress={onAction}
        hitSlop={theme.hit.btn}
        style={({ pressed }) => [s.action, pressed ? s.pressed : undefined]}
      >
        <Text style={s.actionWords}>{actionLabel}</Text>
      </Pressable>
    </View>
  );
}

const s = StyleSheet.create({
  toast: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    backgroundColor: theme.color.night,
    borderRadius: theme.radius.toast,
    paddingVertical: theme.space.md,
    paddingHorizontal: theme.space.lg,
  },
  message: { ...theme.type.inlineTitle, color: theme.color.surface, flex: 1 },
  action: { paddingHorizontal: theme.space.xs },
  actionWords: {
    ...theme.type.inlineTitle,
    fontFamily: theme.font.sans[700],
    color: theme.color.volt,
  },
  pressed: { opacity: 0.7 },
});

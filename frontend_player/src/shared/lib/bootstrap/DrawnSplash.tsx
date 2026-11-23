/**
 * **The drawn splash** — the first thing a player sees, drawn rather than played from a file, so it
 * begins on the first frame the app paints
 * ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md),
 * `docs/specs/splash-screen/`).
 *
 * **Today it is the ground**: a flat `splashGroundEdge` field, the launch window's own colour, with a
 * radial glow that comes on over the first 0.39 s, so the launch window lightens into it rather than
 * jumping. The lockup (#855) and the ball (#856) are drawn over it. Under reduced motion the glow is
 * simply there.
 *
 * **The fade is the whole splash's opacity**, glow and all, linear over 0.5 s. The launch gate holds
 * that value and moves it, because when the fade begins is the gate's to say; this only draws it.
 * Motion runs on the UI thread and moves only opacity.
 *
 * Nothing speaks it (ADR-0198): the ground is a picture, and the splash adds no announcement.
 */

import { useId, useRef } from 'react';
import { StyleSheet } from 'react-native';
import Animated, {
  Easing,
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

import { theme } from '@/shared/ui/theme';

import { LAUNCH_CLOCK } from './launchClock';

/**
 * **The glow, in the splash's own box** (`objectBoundingBox`): centred horizontally and 42 % down,
 * its ring reaching half the box each way, and `splashGroundEdge` from three quarters of the way out
 * — the brief's *"to the night colour at three quarters of the way to the edges and beyond"*. In
 * the box rather than in points, so the ellipse is the screen's own shape on every phone, as the
 * mock draws it.
 */
const GLOW = { cx: 0.5, cy: 0.42, r: 0.5, edgeFrom: 0.75 } as const;

export interface DrawnSplashProps {
  /** Reduced motion, as the launch gate decided it once, before the first frame. */
  readonly reduced: boolean;
  /** The whole splash's opacity: 1 until the launch gate fades it. */
  readonly opacity: SharedValue<number>;
  /** The splash's first layout: the launch window may go, and the launch's clock starts. Once. */
  readonly onFirstLayout: () => void;
}

export function DrawnSplash({ reduced, opacity, onFirstLayout }: DrawnSplashProps) {
  const glow = useSharedValue(reduced ? 1 : 0);
  const laidOut = useRef(false);

  const onLayout = () => {
    if (laidOut.current) return;
    laidOut.current = true;
    // The variant is the gate's, decided once: under it the glow is already lit, and otherwise it
    // comes on whatever Reanimated later hears from the OS.
    if (!reduced) {
      glow.value = withTiming(1, {
        duration: LAUNCH_CLOCK.glowIn,
        easing: Easing.linear,
        reduceMotion: ReduceMotion.Never,
      });
    }
    onFirstLayout();
  };

  const splashStyle = useAnimatedStyle(() => ({ opacity: opacity.value }));
  const glowStyle = useAnimatedStyle(() => ({ opacity: glow.value }));

  return (
    <Animated.View
      testID="drawn-splash"
      style={[s.splash, splashStyle]}
      onLayout={onLayout}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Animated.View testID="splash-glow" style={[s.fill, glowStyle]} pointerEvents="none">
        <Glow />
      </Animated.View>
    </Animated.View>
  );
}

function Glow() {
  // Per instance, as `YesGround`'s is: React's own uniqueness, not a name that could collide.
  const id = `${useId()}-splash-glow`;

  return (
    <Svg width="100%" height="100%">
      <Defs>
        <RadialGradient id={id} cx={GLOW.cx} cy={GLOW.cy} r={GLOW.r}>
          <Stop offset={0} stopColor={theme.color.splashGroundCentre} />
          <Stop offset={GLOW.edgeFrom} stopColor={theme.color.splashGroundEdge} />
        </RadialGradient>
      </Defs>
      <Rect x={0} y={0} width="100%" height="100%" fill={`url(#${id})`} />
    </Svg>
  );
}

const s = StyleSheet.create({
  // Above everything the root draws, because it is drawn after all of it; the edge colour is its
  // own fill, so the first frame is the launch window's field before the glow has begun.
  splash: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.splashGroundEdge },
  fill: StyleSheet.absoluteFillObject,
});

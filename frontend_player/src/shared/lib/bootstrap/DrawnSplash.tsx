/**
 * **The drawn splash** — the first thing a player sees, drawn rather than played from a file, so it
 * begins on the first frame the app paints
 * ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md),
 * `docs/specs/splash-screen/`).
 *
 * **The ground**: a flat `splashGroundEdge` field, the launch window's own colour, with a radial
 * glow that comes on over the first 0.39 s, so the launch window lightens into it rather than
 * jumping. Under reduced motion the glow is simply there.
 *
 * **The lockup** (#855): *Rakieta* in white and its `volt` dot, centred together on the whole
 * screen. Seven letters, each placed by the splash's geometry (`domain/splashGeometry.ts`) from
 * Archivo 800's own advances and kerning — never laid out as a run of text, so where every letter
 * stands is known before the first frame. They keep their size whatever the phone's text size: a
 * logo is a logo. The splash loads their face itself, as it starts, and sets no letter before the
 * face is there — nor in a face that could not be read; then the lockup comes in over 0.15 s. The
 * ball that becomes the dot flies in with #856.
 *
 * **Everything is placed on the full screen**, not on the app's view: where the view does not cover
 * a system bar — Android's opaque status bar, a three-button navigation bar — the geometry offsets
 * the lockup, and the ground's glow is laid out in the whole screen's box, starting above the view,
 * so its centre and the lockup share one set of coordinates. What falls under an opaque bar is
 * never painted — the bar is the phone's, painted the field's edge by the gate (#857) — and only
 * where the glow's centre lies depends on it.
 *
 * **The fade is the whole splash's opacity**, glow, word and dot together, linear over 0.5 s. The
 * launch gate holds that value and moves it, because when the fade begins is the gate's to say;
 * this only draws it. Motion runs on the UI thread and moves only opacity.
 *
 * Nothing speaks it (ADR-0198): the ground and the word are a picture, and the splash adds no
 * announcement.
 */

import { useCallback, useContext, useEffect, useId, useMemo, useRef, useState } from 'react';
import { Dimensions, StyleSheet, Text, View } from 'react-native';
import Animated, {
  Easing,
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { SafeAreaFrameContext } from 'react-native-safe-area-context';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

import { theme } from '@/shared/ui/theme';

import {
  splashGeometry,
  WORDMARK_FACE,
  type Box,
  type WordmarkSetting,
} from './domain/splashGeometry';
import type { SplashFace } from './fonts';
import { LAUNCH_CLOCK } from './launchClock';

/**
 * **The glow, in the full screen's box** (`objectBoundingBox`): centred horizontally and 42 % down,
 * its ring reaching half the box each way, and `splashGroundEdge` from three quarters of the way out
 * — the brief's *"to the night colour at three quarters of the way to the edges and beyond"*. In
 * the box rather than in points, so the ellipse is the screen's own shape on every phone, as the
 * mock draws it.
 */
const GLOW = { cx: 0.5, cy: 0.42, r: 0.5, edgeFrom: 0.75 } as const;

/** The `splashWord` role, as the geometry sets it: the face's numbers at the role's size. */
const WORDMARK: WordmarkSetting = {
  face: WORDMARK_FACE,
  fontSize: theme.type.splashWord.fontSize,
  letterSpacing: theme.type.splashWord.letterSpacing,
};

export interface DrawnSplashProps {
  /** Reduced motion, as the launch gate decided it once, before the first frame. */
  readonly reduced: boolean;
  /** The whole splash's opacity: 1 until the launch gate fades it. */
  readonly opacity: SharedValue<number>;
  /** The wordmark's face, which the splash asks for itself as it starts. */
  readonly face: SplashFace;
  /** The splash's first layout: the launch window may go, and the launch's clock starts. Once. */
  readonly onFirstLayout: () => void;
}

export function DrawnSplash({ reduced, opacity, face, onFirstLayout }: DrawnSplashProps) {
  const glow = useSharedValue(reduced ? 1 : 0);
  const lockup = useSharedValue(0);

  // The face handed over first, asked for once.
  const firstFace = useRef(face);
  const [faceReady, setFaceReady] = useState(face.loaded);
  /**
   * What the lockup's coming in waits for: the splash laid out, and the face's answer — loaded, or
   * not to be had. Once.
   */
  const due = useRef({ laidOut: false, answered: faceReady, begun: false });

  // The view's place on the screen, as the root's safe-area provider knows it: below an opaque
  // status bar it starts that bar's height down. The screen is the whole phone, bars and all.
  // **Read from the context, never through the hook that throws without a provider**: the splash is
  // the launch's first frame, and a tree without one — a suite's — takes the view to cover the
  // screen, as an iPhone's does, rather than starting on an error.
  const frame = useContext(SafeAreaFrameContext);
  const placed = useMemo(() => {
    const screen = Dimensions.get('screen');
    const view = frame ?? { x: 0, y: 0, ...screen };
    return splashGeometry({ screen, view }, WORDMARK);
  }, [frame]);

  const bringInTheLockupIfDue = useCallback(() => {
    const now = due.current;
    if (now.begun || !now.laidOut || !now.answered) return;
    now.begun = true;
    // Never the OS's reduced motion, which would make it a cut: the variant is the gate's, and
    // under both, for now, the lockup comes in over the same short fade.
    lockup.value = withTiming(1, {
      duration: LAUNCH_CLOCK.lockupIn,
      easing: Easing.linear,
      reduceMotion: ReduceMotion.Never,
    });
  }, [lockup]);

  // **The face is asked for as the splash starts**, never behind the sequence's session check.
  // A face that cannot be read sets no letter — a family the phone never registered would draw the
  // word in the system's font at Archivo's places, misspaced, and iOS objects to it out loud in
  // development — so the lockup comes in as its dot alone. Reporting the failure is the sequence's,
  // whose own font step meets the same file.
  useEffect(() => {
    if (due.current.answered) return;
    let live = true;
    const answered = (loaded: boolean) => () => {
      if (!live) return;
      due.current.answered = true;
      if (loaded) setFaceReady(true);
      bringInTheLockupIfDue();
    };
    firstFace.current.load().then(answered(true), answered(false));
    return () => {
      live = false;
    };
  }, [bringInTheLockupIfDue]);

  const onLayout = () => {
    if (due.current.laidOut) return;
    due.current.laidOut = true;
    // The variant is the gate's, decided once: under it the glow is already lit, and otherwise it
    // comes on whatever Reanimated later hears from the OS.
    if (!reduced) {
      glow.value = withTiming(1, {
        duration: LAUNCH_CLOCK.glowIn,
        easing: Easing.linear,
        reduceMotion: ReduceMotion.Never,
      });
    }
    bringInTheLockupIfDue();
    onFirstLayout();
  };

  const splashStyle = useAnimatedStyle(() => ({ opacity: opacity.value }));
  const glowStyle = useAnimatedStyle(() => ({ opacity: glow.value }));
  const lockupStyle = useAnimatedStyle(() => ({ opacity: lockup.value }));

  const { dot } = placed;

  return (
    <Animated.View
      testID="drawn-splash"
      style={[s.splash, splashStyle]}
      onLayout={onLayout}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <View testID="splash-ground" style={[s.placed, boxOf(placed.screen)]} pointerEvents="none">
        <Animated.View testID="splash-glow" style={[s.fill, glowStyle]}>
          <Glow />
        </Animated.View>
      </View>
      <Animated.View testID="splash-lockup" style={[s.fill, lockupStyle]} pointerEvents="none">
        {faceReady
          ? placed.letters.map(({ letter, x, y }, i) => (
              // Keyed by its place in the word, which has two a's.
              <Text key={i} allowFontScaling={false} style={[s.letter, { left: x, top: y }]}>
                {letter}
              </Text>
            ))
          : null}
        <View
          testID="splash-dot"
          style={[
            s.dot,
            {
              left: dot.x - dot.size / 2,
              top: dot.y - dot.size / 2,
              width: dot.size,
              height: dot.size,
              borderRadius: dot.size / 2,
            },
          ]}
        />
      </Animated.View>
    </Animated.View>
  );
}

/** A box as a placed view's style. */
function boxOf({ x, y, width, height }: Box) {
  return { left: x, top: y, width, height };
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
  placed: { position: 'absolute' },
  // The role's face and size, never its tracking or a line height: the tracking is in where each
  // letter stands, and a lone letter in the face's own line box — `includeFontPadding` off, so
  // Android's is the face's too — has its midline where the geometry put it.
  letter: {
    position: 'absolute',
    fontFamily: theme.type.splashWord.fontFamily,
    fontSize: theme.type.splashWord.fontSize,
    color: theme.color.surface,
    includeFontPadding: false,
  },
  dot: { position: 'absolute', backgroundColor: theme.color.volt },
});

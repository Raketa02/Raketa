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
 * face is there — nor in a face that could not be read.
 *
 * **The ball bounces it into place** (#856). The dot is the ball: one volt circle, drawn above the
 * letters, that drops in from just above the top edge, lands three times along the floor and comes
 * to rest as the full stop at 1.68 s, while *Rak*, *ie* and *ta* rise with its three landings. **One
 * clock moves all of it**, on the UI thread, for 1.78 s, when the word is still; the ball's pose and
 * each letter's are pure functions of that clock (`domain/splashMotion.ts`), so the landings and the
 * letters they shake up can never drift apart, and the clock's end is exactly #855's still lockup.
 *
 * **The clock starts on the splash's first layout when the face is there, and otherwise waits for
 * it** — at most `faceWait`, 0.6 s — and starts a frame after the letters it brings are set. Setting
 * seven letters is the phone creating seven views and laying out their text on the thread that
 * moves the ball, and a face that answered mid-flight — a debug build fetches it from the dev
 * server, about 0.45 s on the A32 — set them on *Rak*'s cue, the ball stuttering as the word came in.
 * A release build reads the face from its bundle in milliseconds, so the ball starts on the first
 * layout as before. A face that has still not answered at `faceWait` lets the ball go without it,
 * and its letters come in where the clock has them by then, faded in over 0.15 s rather than all at
 * once. **When the clock is at its end the splash says so** (`onStill`), and the gate mounts the
 * tree underneath, whose views would otherwise be created while the ball is in the air (`LaunchGate`).
 *
 * **Under reduced motion nothing flies**: the clock stands at its end from the first frame, so the
 * ball is the dot and every letter is in place, and the lockup comes in over 0.15 s once the splash
 * has laid out and the face has answered.
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
 * this only draws it. Motion runs on the UI thread and moves only `transform` and `opacity`, never a
 * layout prop (CLAUDE.md, *Mobile gotchas*).
 *
 * Nothing speaks it (ADR-0198): the ground and the word are a picture, and the splash adds no
 * announcement.
 */

import { memo, useCallback, useContext, useEffect, useId, useMemo, useRef, useState } from 'react';
import { Dimensions, StyleSheet, View } from 'react-native';
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
  type PlacedLetter,
  type WordmarkSetting,
} from './domain/splashGeometry';
import { ballAt, letterAt, splashStillAt } from './domain/splashMotion';
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
  /**
   * **The motion is over**, and the lockup still: the tree underneath may mount (`LaunchGate`).
   * Once — at the first layout under reduced motion, where nothing flies.
   */
  readonly onStill: () => void;
}

/**
 * The splash, drawn again only when what the gate hands it changes — which is never, once it has
 * started: every prop the gate passes is stable. A re-render of the gate (the sequence settling,
 * the motion going still) would otherwise commit the whole splash on the thread that moves the ball.
 */
export const DrawnSplash = memo(SplashDrawing);

function SplashDrawing({
  reduced: handedOver,
  opacity,
  face,
  onFirstLayout,
  onStill,
}: DrawnSplashProps) {
  // The variant as the gate handed it over first: decided once, and never switched mid-play — nor
  // asking for the face a second time, as an effect that followed it would.
  const [reduced] = useState(handedOver);
  // The face handed over first, asked for once.
  const firstFace = useRef(face);
  const [faceReady, setFaceReady] = useState(face.loaded);
  /**
   * What the lockup's coming in waits for: the splash laid out, and the face's answer — loaded, or
   * not to be had. Once.
   */
  const due = useRef({ laidOut: false, answered: faceReady, begun: false, moving: false });
  /** The face's answer, as a render can see it: what the motion's start waits for (below). */
  const [answered, setAnswered] = useState(faceReady);
  /** The motion's own timers — its wait for the face, and its end. */
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach(clearTimeout);
  }, []);
  // `onStill` as handed over now, for a timer set at the motion's start.
  const stillNow = useRef(onStill);
  stillNow.current = onStill;

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

  const glow = useSharedValue(reduced ? 1 : 0);
  /**
   * **The motion's clock**, in milliseconds from the splash's first layout, which the ball and every
   * letter read their pose from. Under reduced motion it stands at its end — the still lockup — from
   * the first frame; otherwise it runs there once, from the first layout.
   */
  const motion = useSharedValue(reduced ? splashStillAt(placed) : 0);
  // Under full motion the lockup is there from the start, and the motion brings it in: the ball out
  // of sight above the top edge, each letter unseen below its place until its cue.
  const lockup = useSharedValue(reduced ? 0 : 1);
  // The letters, as one: there with the lockup, unless their face was not there as the splash mounted
  // under full motion. Then they come in over the lockup's short fade when it arrives — unseen before
  // the first cue, as it normally is, and otherwise rather than all at once, where the clock already
  // has them. Under reduced motion the lockup's own fade brings them in.
  const lettersIn = useSharedValue(reduced || faceReady ? 1 : 0);

  const bringInTheLateLetters = useCallback(() => {
    if (reduced) return;
    // Before the motion has begun its letters stand unseen below their places, and are simply there.
    if (!due.current.moving) {
      lettersIn.value = 1;
      return;
    }
    lettersIn.value = withTiming(1, {
      duration: LAUNCH_CLOCK.lockupIn,
      easing: Easing.linear,
      reduceMotion: ReduceMotion.Never,
    });
  }, [reduced, lettersIn]);

  const bringInTheLockupIfDue = useCallback(() => {
    const now = due.current;
    if (!reduced || now.begun || !now.laidOut || !now.answered) return;
    now.begun = true;
    // Never the OS's reduced motion, which would make it a cut: the variant is the gate's, and
    // under it the lockup comes in over a short fade, the brief's "almost instantly".
    lockup.value = withTiming(1, {
      duration: LAUNCH_CLOCK.lockupIn,
      easing: Easing.linear,
      reduceMotion: ReduceMotion.Never,
    });
  }, [reduced, lockup]);

  /**
   * **The motion, once**: the glow coming on with the ball's 0.39 s fall, the clock run to the still
   * lockup, and the tree told when it is still. Under reduced motion the glow is already lit and the
   * clock already at its end, and nothing is started.
   */
  const startTheMotion = useCallback(() => {
    const now = due.current;
    if (reduced || now.moving) return;
    now.moving = true;
    glow.value = withTiming(1, {
      duration: LAUNCH_CLOCK.glowIn,
      easing: Easing.linear,
      reduceMotion: ReduceMotion.Never,
    });
    const still = splashStillAt(placed);
    motion.value = withTiming(still, {
      duration: still,
      easing: Easing.linear,
      reduceMotion: ReduceMotion.Never,
    });
    timers.current.push(setTimeout(() => stillNow.current(), still));
  }, [reduced, glow, motion, placed]);

  // **A face that answers late starts the motion a frame after its letters are set** — set in the
  // commit its answer brings, and drawn before the ball moves, so no letter is ever set while the
  // ball is in the air (see the module note).
  useEffect(() => {
    if (reduced || !answered || !due.current.laidOut || due.current.moving) return;
    const frame = requestAnimationFrame(startTheMotion);
    return () => cancelAnimationFrame(frame);
  }, [reduced, answered, startTheMotion]);

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
      setAnswered(true);
      if (loaded) {
        setFaceReady(true);
        bringInTheLateLetters();
      }
      bringInTheLockupIfDue();
    };
    firstFace.current.load().then(answered(true), answered(false));
    return () => {
      live = false;
    };
  }, [bringInTheLockupIfDue, bringInTheLateLetters]);

  const onLayout = () => {
    if (due.current.laidOut) return;
    due.current.laidOut = true;
    // The variant is the gate's, decided once: under it the glow is already lit and the motion
    // already over — the lockup is still from the first frame. Otherwise the motion starts here, with
    // the gate's clock, when the face is already there; a face still on its way is waited for, a
    // frame past its answer (above), and for no longer than `faceWait`.
    if (reduced) onStill();
    else if (due.current.answered) startTheMotion();
    else timers.current.push(setTimeout(startTheMotion, LAUNCH_CLOCK.faceWait));
    bringInTheLockupIfDue();
    onFirstLayout();
  };

  const { ball, dot } = placed;

  const splashStyle = useAnimatedStyle(() => ({ opacity: opacity.value }));
  const glowStyle = useAnimatedStyle(() => ({ opacity: glow.value }));
  const lockupStyle = useAnimatedStyle(() => ({ opacity: lockup.value }));
  const lettersStyle = useAnimatedStyle(() => ({ opacity: lettersIn.value }));
  // The ball, drawn as the dot moved and squashed: at rest the transform is nothing at all, so the
  // last frame is the dot exactly where #855 stands it.
  const ballStyle = useAnimatedStyle(() => {
    const pose = ballAt(ball, motion.value);
    return {
      transform: [
        { translateX: pose.x - dot.x },
        { translateY: pose.y - dot.y },
        { scaleX: pose.scaleX },
        { scaleY: pose.scaleY },
      ],
    };
  });

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
        <Animated.View testID="splash-letters" style={[s.fill, lettersStyle]}>
          {faceReady
            ? placed.letters.map((placedLetter, i) => (
                // Keyed by its place in the word, which has two a's.
                <SplashLetter key={i} placed={placedLetter} motion={motion} />
              ))
            : null}
        </Animated.View>
        {/* The ball, which is the dot: last, so it is drawn above the letters it lands among. */}
        <Animated.View
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
            ballStyle,
          ]}
        />
      </Animated.View>
    </Animated.View>
  );
}

/**
 * One letter of the wordmark, at its place, rising into it on the motion's clock from its cue: 10 pt
 * from below, fading in, a touch past and back. Its place is a layout prop and never moves; the rise
 * is a transform.
 */
function SplashLetter({
  placed: { letter, x, y, cue },
  motion,
}: {
  readonly placed: PlacedLetter;
  readonly motion: SharedValue<number>;
}) {
  const style = useAnimatedStyle(() => {
    const pose = letterAt(cue, motion.value);
    return { opacity: pose.opacity, transform: [{ translateY: pose.below }] };
  });

  return (
    <Animated.Text allowFontScaling={false} style={[s.letter, { left: x, top: y }, style]}>
      {letter}
    </Animated.Text>
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

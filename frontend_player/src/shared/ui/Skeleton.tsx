/**
 * **The skeleton** (design system 5.6; PRD #867, [#870](https://github.com/Raketa02/Raketa/issues/870);
 * Part 16, 2026-11-24) — grey shapes standing where a screen's content will be while its first read
 * is out, and **one band of light sweeping across all of them at once**.
 *
 * - **The shapes**: a block, a line (a text bar) and a circle, rounded, in `color.skeleton`. A screen
 *   composes its own loading layout from them, at its content's real sizes; a container that is
 *   always there (a white list card) is drawn as itself, by the screen, around them. The layouts are
 *   the features', the shapes are this file's.
 * - **The band**: a `react-native-svg` linear gradient, `skeleton` → `skeletonSheen` → `skeleton`,
 *   leaning `motion.skeleton.tilt` degrees, sweeping left to right across the ground — the screen's width — once
 *   every `motion.skeleton.sweep` milliseconds, at constant speed, with no pause, forever. Its
 *   arithmetic is `skeletonSweep.ts`'s.
 * - **One band, one clock.** Every shape is drawn on a **`SkeletonGround`** — a plain view the
 *   screen puts round the area its shapes stand in, real content beside them included. The ground
 *   holds the one clock and is what each shape measures itself against, so each shows the band at
 *   its own place on the screen. Measured against the ground rather than the window, because a
 *   screen sliding in on a push would measure every shape mid-flight.
 * - **It moves by `transform` only, on the UI thread** (the player app's Reanimated rule): **one
 *   animated style on the ground**, a `translateX` that every shape's band shares, so a frame runs one
 *   mapper however many shapes stand. Each shape's own part of the move is a still `translateX` under
 *   it, set once from its layout. Nothing is laid out per frame.
 * - **It sweeps under reduced motion** (`ReduceMotion.Never`, without which Reanimated cuts a timing
 *   under the OS setting): Part 13's third exception, beside the calculating screen's indicator and
 *   the busy spinner — progress, not decoration.
 * - **Hidden from a listener, and it announces nothing** (ADR-0198: the name is the whole job, and a
 *   shape has none). What a screen says while it loads is the screen's.
 * - **The clock runs only while a shape stands, laid out.** The ground counts its shapes once each has
 *   been placed — a shape draws no band before its layout says where it stands, so it has nothing to
 *   move until then (#871) — starts the sweep with the first and stops it with the last: a ground
 *   round a whole page costs nothing once the page has revealed. Under jest nothing is laid out unless
 *   a suite says so, so a router suite runs no sweep under the harness, which runs minutes of frames
 *   on every navigation. It starts at the sweep's place in the wall clock's time, so shapes that go and
 *   come back in one drawing (one skeleton handing over to the next) keep the band where it was.
 *
 * **It passes on where it stands on its page** (`SectionOnPage`, #871): put round sections on a page
 * that watches what is on screen — Home's — a row inside it is still measured on the page, through it.
 *
 * How a screen's content takes the skeleton's place is `Reveal`'s.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from 'react';
import {
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
  type DimensionValue,
  type LayoutChangeEvent,
  type StyleProp,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
import Animated, {
  Easing,
  ReduceMotion,
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import { SectionOnPage, useTopOnPage } from './onScreen';
import {
  bandSheet,
  shapeOffset,
  sweepGeometry,
  sweepShift,
  type SweepGeometry,
} from './skeletonSweep';
import { theme } from './theme';

interface Ground {
  /** The view every shape measures itself against. */
  readonly node: RefObject<View>;
  /** **The one moving part**, every shape's band moved by it: the clock's share of the shift. */
  readonly sweep: ReturnType<typeof useAnimatedStyle>;
  readonly geometry: SweepGeometry;
  /** A shape has come; the function it hands back is its going. */
  readonly enter: () => () => void;
}

const GroundContext = createContext<Ground | undefined>(undefined);

/** Constant speed, and never cut: the sweep is progress, not decoration (Part 13). */
const SWEEPING = { easing: Easing.linear, reduceMotion: ReduceMotion.Never } as const;

/**
 * Start the clock at the sweep's place in the wall clock's time, and run it a sweep at a time
 * forever. It counts upwards from there — a repeat starts again from where it began — and a shape
 * reads only the fraction.
 */
function sweepOn(clock: SharedValue<number>) {
  const { sweep } = theme.motion.skeleton;
  const phase = (performance.now() % sweep) / sweep;
  clock.value = phase;
  clock.value = withRepeat(
    withTiming(phase + 1, { ...SWEEPING, duration: sweep }),
    -1,
    false,
    undefined,
    ReduceMotion.Never,
  );
}

export interface SkeletonGroundProps {
  /** The area the screen's shapes stand in — real content beside them is no matter. */
  readonly children: ReactNode;
  readonly style?: StyleProp<ViewStyle>;
  readonly testID?: string;
}

/**
 * **The ground a screen's shapes are drawn on**: one clock for all of them, and the frame each
 * measures its place in. Put it round everything that shimmers on a screen, so one band crosses it
 * all; it draws nothing of its own.
 */
export function SkeletonGround({ children, style, testID }: SkeletonGroundProps) {
  const node = useRef<View>(null);
  const page = useTopOnPage();
  const clock = useSharedValue(0);
  const shapes = useRef(0);
  // The band crosses the ground itself — its own size once laid out, the window's until then — so
  // it leaves the ground's last corner as the next sweep enters its first, and never runs on past it.
  const window = useWindowDimensions();
  const [laidOut, setLaidOut] = useState<Size>();
  const width = laidOut?.width ?? window.width;
  const height = laidOut?.height ?? window.height;
  const geometry = useMemo(() => sweepGeometry({ width, height }), [width, height]);
  // Its size is drawn from only while a shape stands: a ground round a page that has revealed — Home's,
  // for the session — draws nothing again as a line folds or a rail grows under it.
  const latest = useRef<Size>();
  const measure = useCallback(() => {
    const size = latest.current;
    if (size === undefined) return;
    setLaidOut((was) => (was?.width === size.width && was.height === size.height ? was : size));
  }, []);
  const onLayout = (event: LayoutChangeEvent) => {
    const { y, width: across, height: down } = event.nativeEvent.layout;
    page.laidOut(y);
    latest.current = { width: across, height: down };
    if (shapes.current > 0) measure();
  };

  const enter = useCallback(() => {
    shapes.current += 1;
    if (shapes.current === 1) {
      measure();
      sweepOn(clock);
    }
    return () => {
      shapes.current -= 1;
      if (shapes.current === 0) cancelAnimation(clock);
    };
  }, [clock, measure]);

  // One style for every shape on the ground, so a frame runs one mapper however many shapes stand —
  // each shape's own part of the move is a still offset under it.
  const sweep = useAnimatedStyle(() => {
    const progress = clock.value - Math.floor(clock.value);
    return { transform: [{ translateX: sweepShift(progress, geometry) }] };
  }, [geometry]);

  const ground = useMemo(() => ({ node, sweep, geometry, enter }), [sweep, geometry, enter]);

  return (
    <GroundContext.Provider value={ground}>
      <View ref={node} style={style} testID={testID} onLayout={onLayout}>
        <SectionOnPage.Provider value={page.top}>{children}</SectionOnPage.Provider>
      </View>
    </GroundContext.Provider>
  );
}

/** The ground's own size, as laid out. */
interface Size {
  readonly width: number;
  readonly height: number;
}

/** Where a shape stands on its ground, and how tall it is — read from its layout. */
interface Placed {
  readonly x: number;
  readonly y: number;
  readonly height: number;
}

interface ShapeProps {
  readonly style: StyleProp<ViewStyle>;
  readonly testID?: string;
}

/** **One shape**: the tone, rounded, and its piece of the band once its place is known. */
function Shape({ style, testID }: ShapeProps) {
  const ground = useContext(GroundContext);
  if (ground === undefined) {
    throw new Error(
      'A skeleton shape is drawn on a SkeletonGround — it holds the clock the band moves on, and ' +
        'the frame each shape measures its place in.',
    );
  }
  const { node, sweep, geometry, enter } = ground;
  const self = useRef<View>(null);
  const [placed, setPlaced] = useState<Placed>();
  const gradient = useId();

  // On the clock once placed: until its layout says where it stands it draws no band to move.
  const isPlaced = placed !== undefined;
  useEffect(() => (isPlaced ? enter() : undefined), [isPlaced, enter]);

  const onLayout = (event: LayoutChangeEvent) => {
    const { x, y, height } = event.nativeEvent.layout;
    // Its place in its parent first — exact when the ground holds it directly — then on the ground.
    setPlaced({ x, y, height });
    const on = node.current;
    if (on === null || self.current === null) return;
    self.current.measureLayout(
      on,
      (left, top) => setPlaced({ x: left, y: top, height }),
      () => {},
    );
  };

  const sheet = placed === undefined ? undefined : bandSheet(placed.height, geometry);

  return (
    <View
      ref={self}
      testID={testID}
      style={[s.shape, style]}
      onLayout={onLayout}
      accessible={false}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {placed === undefined || sheet === undefined ? null : (
        // The shape's own part of the move, still: where its sheet stands at a sweep's start.
        <View
          testID="skeleton-sheet"
          style={[
            s.sheet,
            { width: sheet.width, height: placed.height },
            { transform: [{ translateX: shapeOffset(placed, placed.height, geometry) }] },
          ]}
        >
          <Animated.View testID="skeleton-band" style={[s.band, sweep]}>
            <Svg width={sheet.width} height={placed.height}>
              <Defs>
                <LinearGradient
                  id={gradient}
                  gradientUnits="userSpaceOnUse"
                  x1={sheet.from.x}
                  y1={sheet.from.y}
                  x2={sheet.to.x}
                  y2={sheet.to.y}
                >
                  <Stop offset={0} stopColor={theme.color.skeleton} />
                  <Stop offset={0.5} stopColor={theme.color.skeletonSheen} />
                  <Stop offset={1} stopColor={theme.color.skeleton} />
                </LinearGradient>
              </Defs>
              <Rect width={sheet.width} height={placed.height} fill={`url(#${gradient})`} />
            </Svg>
          </Animated.View>
        </View>
      )}
    </View>
  );
}

export interface SkeletonBlockProps {
  /** Its size and place — a card's, a tile's, a step's — and its corner, a card's unless said. */
  readonly style: StyleProp<ViewStyle>;
  readonly testID?: string;
}

/** **A block** — where a card, a tile or a step will stand. */
export function SkeletonBlock({ style, testID }: SkeletonBlockProps) {
  return <Shape style={style} {...(testID === undefined ? {} : { testID })} />;
}

export interface SkeletonLineProps {
  /** The role the text will be set in: the bar is its size tall, in a box its line tall. */
  readonly role: { readonly fontSize: number; readonly lineHeight?: number };
  /**
   * How wide the bar is — points, or a share of its box (all of it unless said). **A share needs a box
   * with a width**: in a column the box stretches, but in a row it is as wide as its content, so a
   * line there takes points, or a `flex` through `style`, or draws nothing.
   */
  readonly width?: DimensionValue;
  /** The line's box in its parent — a flex, a margin. */
  readonly style?: StyleProp<ViewStyle>;
  readonly testID?: string;
}

/** **A line** — a bar where a line of text will stand, its ends rounded. */
export function SkeletonLine({ role, width = '100%', style, testID }: SkeletonLineProps) {
  return (
    <View style={[s.line, { height: role.lineHeight ?? role.fontSize }, style]}>
      <Shape
        style={{ width, height: role.fontSize, borderRadius: role.fontSize / 2 }}
        {...(testID === undefined ? {} : { testID })}
      />
    </View>
  );
}

export interface SkeletonWordsProps {
  /** The role the words will be set in — the heading's own, its case included. */
  readonly role: TextStyle & { readonly fontSize: number; readonly lineHeight?: number };
  /** The words that will stand there: a heading that is always there, so its words are known. */
  readonly words: string;
  /** The bar's box in its parent — a margin. */
  readonly style?: StyleProp<ViewStyle>;
  readonly testID?: string;
}

/**
 * **A line as wide as its words** (#871) — where a heading that is always there will stand, such as
 * Home's *YOUR GAMES*: the words are set unseen in their role, so the bar spans exactly what the font
 * would draw, at any text size, with no width to guess. A bar the role's size tall, as `SkeletonLine`'s.
 */
export function SkeletonWords({ role, words, style, testID }: SkeletonWordsProps) {
  return (
    <View
      style={[s.words, { height: role.lineHeight ?? role.fontSize }, style]}
      accessible={false}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Text style={[role, s.unseen]} numberOfLines={1}>
        {words}
      </Text>
      <View style={s.wordsBar}>
        <Shape
          style={{ height: role.fontSize, borderRadius: role.fontSize / 2 }}
          {...(testID === undefined ? {} : { testID })}
        />
      </View>
    </View>
  );
}

export interface SkeletonCircleProps {
  /** Its diameter — a face's, a mark's. */
  readonly size: number;
  readonly style?: StyleProp<ViewStyle>;
  readonly testID?: string;
}

/** **A circle** — where a face or a round mark will stand. */
export function SkeletonCircle({ size, style, testID }: SkeletonCircleProps) {
  return (
    <Shape
      style={[{ width: size, height: size, borderRadius: size / 2 }, style]}
      {...(testID === undefined ? {} : { testID })}
    />
  );
}

const s = StyleSheet.create({
  shape: {
    backgroundColor: theme.color.skeleton,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
  },
  sheet: { position: 'absolute', top: 0, left: 0 },
  band: { ...StyleSheet.absoluteFillObject },
  line: { justifyContent: 'center' },
  // As wide as the words inside it, whatever its column; hidden from a listener whole.
  words: { alignSelf: 'flex-start', justifyContent: 'center' },
  // Laid out, so the box takes their width — and never drawn.
  unseen: { opacity: 0 },
  wordsBar: { ...StyleSheet.absoluteFillObject, justifyContent: 'center' },
});

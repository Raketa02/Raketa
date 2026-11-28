/**
 * **The skeleton at its own seam** (design system 5.6; PRD #867,
 * [#870](https://github.com/Rakieta02/Rakieta/issues/870)) — the shapes a screen composes its loading
 * layout from, and the one band of light that sweeps across them.
 *
 * Reanimated is real here, as it is in the router harness (ADR-0176 §2): every worklet runs on the
 * JavaScript thread and `withTiming` on the fake clock, a frame every 16 ms. Nothing lays anything
 * out under jest, so a shape's place and size are handed to it as a layout event — which is where its
 * piece of the band is drawn from. Its moving part is read with `getAnimatedStyle`, never
 * `props.style`, where a Reanimated style never shows.
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { Profiler } from 'react';
import { AccessibilityInfo, Dimensions, StyleSheet, View, type ViewStyle } from 'react-native';
import { getAnimatedStyle, ReducedMotionConfig, ReduceMotion } from 'react-native-reanimated';

import { useTopOnPage, type Followed } from './onScreen';
import { ReducedMotionProvider } from './overlay';
import {
  SkeletonBlock,
  SkeletonCircle,
  SkeletonGround,
  SkeletonLine,
  SkeletonWords,
} from './Skeleton';
import { bandSheet, sweepGeometry } from './skeletonSweep';
import { theme } from './theme';

/** The shapes are hidden from a listener: a test finds them by id, hidden ones included. */
const HIDDEN = { includeHiddenElements: true } as const;
const FRAME = 16;
const SWEEP = theme.motion.skeleton.sweep;

function drawShapes({ reduced = false }: { readonly reduced?: boolean } = {}) {
  render(
    <ReducedMotionProvider value={reduced}>
      {reduced ? <ReducedMotionConfig mode={ReduceMotion.Always} /> : null}
      <SkeletonGround>
        <SkeletonBlock testID="block" style={{ height: theme.size.btn }} />
        <SkeletonLine testID="line" role={theme.type.cardTitle} />
        <SkeletonCircle testID="circle" size={theme.size.seg} />
      </SkeletonGround>
    </ReducedMotionProvider>,
  );
}

interface Box {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

/** The layout's report of where a shape stands on its ground, and how big it is. */
function layOut(testID: string, box: Box) {
  fireEvent(screen.getByTestId(testID, HIDDEN), 'layout', { nativeEvent: { layout: box } });
}

const BLOCK: Box = { x: 15, y: 0, width: 300, height: theme.size.btn };
const CIRCLE: Box = { x: 30, y: 120, width: theme.size.seg, height: theme.size.seg };

/** The moving part inside a shape — the sheet its piece of the band is drawn on. */
const bandOf = (testID: string) =>
  within(screen.getByTestId(testID, HIDDEN)).getByTestId('skeleton-band', HIDDEN);

/** How far a shape's sheet stands sideways, this frame. */
function shiftOf(testID: string): number {
  const style = getAnimatedStyle(bandOf(testID)) as {
    readonly transform?: readonly { readonly translateX?: number }[];
  };
  return style.transform?.[0]?.translateX ?? Number.NaN;
}

function frames(count: number) {
  act(() => jest.advanceTimersByTime(count * FRAME));
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => {
  jest.useRealTimers();
  // A spy a failed assertion left behind would mute or count the next test.
  jest.restoreAllMocks();
});

describe('a skeleton shape', () => {
  it('is hidden from a listener, and announces nothing', () => {
    const announce = jest.spyOn(AccessibilityInfo, 'announceForAccessibility');
    drawShapes();
    layOut('block', BLOCK);
    frames(10);

    for (const shape of ['block', 'line', 'circle']) {
      expect(screen.queryByTestId(shape)).toBeNull();
      expect(screen.getByTestId(shape, HIDDEN)).toBeTruthy();
    }
    expect(announce).not.toHaveBeenCalled();
  });

  it('is drawn in the skeleton’s tone, rounded', () => {
    drawShapes();

    const drawn = (testID: string) =>
      StyleSheet.flatten(screen.getByTestId(testID, HIDDEN).props.style) as ViewStyle;
    expect(drawn('block')).toMatchObject({
      backgroundColor: theme.color.skeleton,
      borderRadius: theme.radius.card,
      overflow: 'hidden',
    });
    expect(drawn('circle')).toMatchObject({
      backgroundColor: theme.color.skeleton,
      width: theme.size.seg,
      height: theme.size.seg,
      borderRadius: theme.size.seg / 2,
    });
    // A text bar: the role's size tall, its ends rounded.
    expect(drawn('line')).toMatchObject({
      backgroundColor: theme.color.skeleton,
      height: theme.type.cardTitle.fontSize,
      borderRadius: theme.type.cardTitle.fontSize / 2,
    });
  });

  it('draws no band until the layout has said where it stands', () => {
    drawShapes();

    expect(
      within(screen.getByTestId('block', HIDDEN)).queryByTestId('skeleton-band', HIDDEN),
    ).toBeNull();

    layOut('block', BLOCK);

    expect(bandOf('block')).toBeTruthy();
  });

  /**
   * #871: nothing moves before a shape is placed — and nothing runs. The router harness runs minutes
   * of frames on every navigation and lays nothing out, so a skeleton there must cost no frame.
   */
  it('sets the clock going only once a shape has been laid out', () => {
    drawShapes();
    frames(10);
    expect(jest.getTimerCount()).toBe(0);

    layOut('block', BLOCK);
    frames(1);

    expect(jest.getTimerCount()).toBeGreaterThan(0);
  });
});

describe('the band', () => {
  it('sweeps left to right at one speed, once a sweep, forever', () => {
    drawShapes();
    layOut('block', BLOCK);
    frames(1);

    // Frame by frame through a sweep: every frame moves it as far right as the one before, but the one
    // frame where a sweep ends and the next begins at the left.
    const at = [shiftOf('block')];
    for (let frame = 0; frame < SWEEP / FRAME; frame += 1) {
      frames(1);
      at.push(shiftOf('block'));
    }
    const moves = at.slice(1).map((shift, index) => shift - at[index]!);
    const rightwards = moves.filter((move) => move > 0);
    expect(moves.length - rightwards.length).toBeLessThanOrEqual(1);
    for (const move of rightwards) expect(move).toBeCloseTo(rightwards[0]!, 6);

    // Two whole sweeps later it stands where it stood, give or take a frame — each new sweep starts
    // on the frame the last one ended in: one cycle a sweep, with no pause.
    const now = shiftOf('block');
    frames((2 * SWEEP) / FRAME);
    expect(Math.abs(shiftOf('block') - now)).toBeLessThanOrEqual(rightwards[0]! + 1e-6);

    // And it is still moving ten sweeps on.
    frames((10 * SWEEP) / FRAME);
    const later = shiftOf('block');
    frames(3);
    expect(shiftOf('block')).not.toBeCloseTo(later, 3);
  });

  it('still sweeps under reduced motion — progress, not decoration (Part 13’s third exception)', () => {
    drawShapes({ reduced: true });
    layOut('block', BLOCK);
    frames(1);

    const before = shiftOf('block');
    frames(5);

    expect(shiftOf('block')).not.toBeCloseTo(before, 3);
  });

  it('moves nothing but a transform, from frame to frame', () => {
    drawShapes();
    layOut('block', BLOCK);
    frames(1);
    const first = { ...(getAnimatedStyle(bandOf('block')) as Record<string, unknown>) };

    const moved = new Set<string>();
    for (let at = 0; at < SWEEP / FRAME + 2; at += 1) {
      frames(1);
      const style = getAnimatedStyle(bandOf('block')) as Record<string, unknown>;
      for (const [prop, value] of Object.entries(style)) {
        if (JSON.stringify(value) !== JSON.stringify(first[prop])) moved.add(prop);
      }
    }

    expect([...moved]).toEqual(['transform']);
  });

  it('is one band across every shape: each shows it where the screen-wide band stands', () => {
    drawShapes();
    layOut('block', BLOCK);
    layOut('circle', CIRCLE);
    frames(7);

    // The moving part is the ground's one style, the same for every shape (and under jest only the
    // last shape to take it reads it, which is why it is not read here). What is each shape's own is
    // its still offset: with it, the band's centre where it crosses the shape's top — moved up the
    // lean to the ground's top edge — is one place for both.
    const g = sweepGeometry(Dimensions.get('window'));
    const stillOffset = (testID: string) => {
      const sheet = within(screen.getByTestId(testID, HIDDEN)).getByTestId(
        'skeleton-sheet',
        HIDDEN,
      );
      const style = StyleSheet.flatten(sheet.props.style) as {
        readonly transform: readonly { readonly translateX: number }[];
      };
      return style.transform[0]!.translateX;
    };
    const atTheTop = (testID: string, box: Box) =>
      box.x + stillOffset(testID) + bandSheet(box.height, g).centreTop + box.y * g.tan;

    expect(atTheTop('circle', CIRCLE)).toBeCloseTo(atTheTop('block', BLOCK), 6);
    // And the two are drawn at different places on their sheets: the offset is each shape's own.
    expect(stillOffset('circle')).not.toBeCloseTo(stillOffset('block'), 3);
  });
});

describe('a bar as wide as its words', () => {
  /** A section heading's bar — Home's *YOUR GAMES*, set in the heading's own role (#871). */
  const HEADING = { ...theme.type.eyebrow, textTransform: 'uppercase' } as const;

  it('sets the words in their role, unseen and unheard, so the bar takes exactly their width', () => {
    render(
      <SkeletonGround>
        <SkeletonWords testID="heading" role={HEADING} words="Your games" />
      </SkeletonGround>,
    );

    // A listener hears nothing of it, and nobody sees the words.
    expect(screen.queryByText('Your games')).toBeNull();
    const words = screen.getByText('Your games', HIDDEN);
    expect(StyleSheet.flatten(words.props.style)).toMatchObject({ ...HEADING, opacity: 0 });
    // The bar: the role's size tall, its ends rounded, across the words' box.
    expect(
      StyleSheet.flatten(screen.getByTestId('heading', HIDDEN).props.style) as ViewStyle,
    ).toMatchObject({
      backgroundColor: theme.color.skeleton,
      height: theme.type.eyebrow.fontSize,
      borderRadius: theme.type.eyebrow.fontSize / 2,
    });
  });
});

/**
 * **A row standing in a wrapper on a watched page** — where it reads its own top on the page, as
 * `HomeRow` does: its `y` in its parent, added to where the section around it stands.
 */
let probed: Followed<number> | undefined;
function Row() {
  const { top, laidOut } = useTopOnPage();
  probed = top;
  return <View testID="row" onLayout={(event) => laidOut(event.nativeEvent.layout.y)} />;
}
const at = (y: number) => ({ nativeEvent: { layout: { x: 0, y, width: 360, height: 100 } } });

describe('the ground', () => {
  it('passes on where it stands on its page, so a row inside it is measured on the page through it', () => {
    render(
      <SkeletonGround testID="ground">
        <Row />
      </SkeletonGround>,
    );

    act(() => {
      fireEvent(screen.getByTestId('ground'), 'layout', at(120));
      fireEvent(screen.getByTestId('row'), 'layout', at(45));
    });

    expect(probed?.get()).toBe(165);
  });

  it('draws nothing again as it is laid out anew once no shape stands — a page that has revealed', () => {
    let commits = 0;
    const page = (shimmering: boolean) => (
      <Profiler id="ground" onRender={() => (commits += 1)}>
        <SkeletonGround testID="ground">
          {shimmering ? <SkeletonBlock style={{ height: theme.size.btn }} /> : null}
        </SkeletonGround>
      </Profiler>
    );
    const { rerender } = render(page(true));
    const size = (height: number) => ({
      nativeEvent: { layout: { x: 0, y: 0, width: 360, height } },
    });
    act(() => fireEvent(screen.getByTestId('ground'), 'layout', size(600)));
    rerender(page(false));
    const before = commits;

    // A line folds open on the page under it, and the page grows.
    act(() => fireEvent(screen.getByTestId('ground'), 'layout', size(900)));
    act(() => fireEvent(screen.getByTestId('ground'), 'layout', size(1200)));

    expect(commits).toBe(before);
  });

  it('is where every shape is drawn: a shape outside one says so', () => {
    jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<SkeletonBlock style={{ height: theme.size.btn }} />)).toThrow(
      'SkeletonGround',
    );
  });
});

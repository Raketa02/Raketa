/**
 * **The sport pill's unfold, at its own seam** — the bar growing leftwards from the pill on the
 * UI thread, or rightwards from Top 10's (#821), and simply open under reduced motion (play 41–42,
 * #513; shared since #774). The router
 * suites walk what a tap does; this holds what the bar is drawn at while it does it.
 *
 * Reanimated is real here, as it is in the router harness (ADR-0176 §2): every worklet runs on the
 * JavaScript thread and `withTiming` on the fake clock. Nothing lays anything out under jest, so the
 * two widths the bar needs — its own, the closed pill's, and the other sports' row — are handed to it
 * as layout events. **The bar is never resized**: how wide it stands open is the closed width and how
 * far its sliding half's round end has travelled (`sport-bar-end`).
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import type { Sport } from '@/shared/vocabulary/sport';

import { ReducedMotionProvider } from './overlay';
import {
  SportBar,
  SportPill,
  type AnotherSport,
  type BarCover,
  type SportPillOpening,
  type SportPillWords,
} from './SportPill';
import { theme } from './theme';

/** A page's words — the bar says only what it is handed. */
const WORDS: SportPillWords = {
  sportName: (sport) =>
    ({ padel: 'Padel', tennis: 'Tennis', squash: 'Squash', badminton: 'Badminton' })[sport],
  pillLabel: (sport) => `Sport: ${sport}`,
  pillHint: 'Shows the page for another sport',
};

const ANOTHER: Omit<AnotherSport, 'onPress'> = {
  label: 'Another sport',
  drawn: '+ Another sport',
  hint: 'Opens the sports',
  pillHint: 'Offers another sport to rate',
};

const ANOTHER_SPORT = ANOTHER.label;

const PAD = theme.size.groupPage.filterPad;
const ROW = 300;
const PILL = 80;

function drawBar({
  reduced = false,
  cover,
  onAnother,
  sports = ['padel', 'tennis', 'squash', 'badminton'],
  opens,
}: {
  readonly reduced?: boolean;
  readonly cover?: BarCover;
  readonly onAnother?: () => void;
  readonly sports?: readonly Sport[];
  readonly opens?: SportPillOpening;
} = {}) {
  const onChoose = jest.fn();
  render(
    <ReducedMotionProvider value={reduced}>
      <SportBar
        sports={sports}
        sport="padel"
        words={WORDS}
        onChoose={onChoose}
        {...(cover === undefined ? {} : { cover })}
        {...(onAnother === undefined ? {} : { another: { ...ANOTHER, onPress: onAnother } })}
        {...(opens === undefined ? {} : { opens })}
      />
    </ReducedMotionProvider>,
  );
  return { onChoose };
}

/**
 * A sliding pill's opacity, and where its slide stands it **on the page** — its wrapper's own
 * translation, a few host nodes up from the button, plus the clip it rides in, which slides with the
 * bar's moving end.
 */
function slideOf(name: string): { readonly opacity?: number; readonly translateX?: number } {
  let node = within(bar()).getByRole('button', { name }).parent;
  while (node !== null) {
    if (node.props.jestAnimatedStyle !== undefined) {
      const style = getAnimatedStyle(node) as {
        readonly opacity?: number;
        readonly transform?: readonly { readonly translateX?: number }[];
      };
      return {
        ...(style.opacity === undefined ? {} : { opacity: style.opacity }),
        ...(style.transform?.[0]?.translateX === undefined
          ? {}
          : { translateX: style.transform[0].translateX + travelled() }),
      };
    }
    node = node.parent;
  }
  return {};
}

const bar = () => screen.getByTestId('sport-bar');

/** The closed pill's width: the current sport and the bar's inset either side of it. */
const CLOSED = PILL + 2 * PAD;

/**
 * The two widths the layout would report — the bar's own, which is the closed pill's, and the other
 * sports' row — for a row of `ROW` with the current sport in it, as the open bar draws it.
 */
function layOut() {
  fireEvent(bar(), 'layout', {
    nativeEvent: { layout: { width: CLOSED, height: 45, x: 0, y: 0 } },
  });
  fireEvent(screen.getByTestId('sport-bar-row'), 'layout', {
    nativeEvent: { layout: { width: ROW - PILL, height: 27, x: 0, y: 0 } },
  });
}

/** How far the bar's sliding half has travelled from the pill's end — signed, as it is drawn. */
function travelled(): number {
  const style = getAnimatedStyle(screen.getByTestId('sport-bar-end')) as {
    readonly transform?: readonly { readonly translateX?: number }[];
  };
  return style.transform?.[0]?.translateX ?? 0;
}

/** What the bar is drawn at: whether it shows, and how wide it stands open. */
function barStyle(): { readonly width: number; readonly opacity?: number } {
  const { opacity } = getAnimatedStyle(bar()) as { readonly opacity?: number };
  return { width: CLOSED + Math.abs(travelled()), ...(opacity === undefined ? {} : { opacity }) };
}

/** Every animated view in the bar, with the style it is drawn at now. */
function animatedStyles(): Record<string, unknown>[] {
  return [bar(), ...within(bar()).UNSAFE_queryAllByType(View)]
    .filter((node) => node.props.jestAnimatedStyle !== undefined)
    .map((node) => ({ ...(getAnimatedStyle(node) as Record<string, unknown>) }));
}

/** One frame: an animated style is applied on the next frame, and the frames run on the fake clock. */
const FRAME = 16;

function nextFrame() {
  act(() => jest.advanceTimersByTime(FRAME));
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe('the sport pill’s bar', () => {
  it('is drawn at nothing until the layout has said how wide it grows', () => {
    drawBar();

    expect(barStyle().opacity).toBe(0);
  });

  it('grows leftwards from the pill to the whole row over the unfold', () => {
    drawBar();
    layOut();

    nextFrame();
    const first = barStyle();
    expect(first.opacity).toBe(1);
    expect(first.width).toBeGreaterThanOrEqual(CLOSED);
    expect(first.width).toBeLessThan(ROW + 2 * PAD);
    // Leftwards: the moving end travels to the left of the pill's.
    expect(travelled()).toBeLessThan(0);

    act(() => jest.advanceTimersByTime(theme.motion.unfold / 2));
    const halfway = barStyle().width;
    expect(halfway).toBeGreaterThan(first.width);
    expect(halfway).toBeLessThan(ROW + 2 * PAD);

    act(() => jest.advanceTimersByTime(theme.motion.unfold));
    expect(barStyle().width).toBe(ROW + 2 * PAD);
  });

  // 2026-11-24: the bar grew by its width, so every frame went through Reanimated 3.16's shadow-tree
  // commit — laid out again, every label measured again — and held still while React committed.
  it('moves nothing but transforms and opacity, from the first frame to the last', () => {
    drawBar({ onAnother: jest.fn() });
    layOut();
    nextFrame();
    const first = animatedStyles();

    const moved = new Set<string>();
    for (let at = 0; at <= theme.motion.unfold + FRAME; at += FRAME) {
      nextFrame();
      animatedStyles().forEach((style, view) => {
        for (const [prop, value] of Object.entries(style)) {
          if (JSON.stringify(value) !== JSON.stringify(first[view]?.[prop])) moved.add(prop);
        }
      });
    }

    // It did move — and only by those two.
    expect([...moved].sort()).toEqual(['opacity', 'transform']);
  });

  // #529 E2: open with every sport in it, the bar ended a few points into the group's tile, and
  // the tile's edge showed past its end.
  it('opens over the tile whole when the sports would end across it', () => {
    drawBar({ cover: { reaches: ROW + 2 * PAD - 10, whole: ROW + 2 * PAD + 20 } });
    layOut();

    act(() => jest.advanceTimersByTime(theme.motion.unfold + FRAME));

    expect(barStyle().width).toBe(ROW + 2 * PAD + 20);
  });

  it('ends where the sports end when they stop short of the tile', () => {
    drawBar({ cover: { reaches: ROW + 2 * PAD + 5, whole: ROW + 2 * PAD + 40 } });
    layOut();

    act(() => jest.advanceTimersByTime(theme.motion.unfold + FRAME));

    expect(barStyle().width).toBe(ROW + 2 * PAD);
  });

  it('is simply open under reduced motion', () => {
    drawBar({ reduced: true });
    layOut();

    nextFrame();

    expect(barStyle()).toMatchObject({ opacity: 1, width: ROW + 2 * PAD });
  });

  it('lists the other sports first and the current one last, chosen', () => {
    const { onChoose } = drawBar();

    const names = within(bar())
      .getAllByRole('button')
      .map((option) => [option.props.accessibilityLabel, option.props.accessibilityState.selected]);
    expect(names).toEqual([
      ['Tennis', false],
      ['Squash', false],
      ['Badminton', false],
      ['Padel', true],
    ]);

    fireEvent.press(within(bar()).getByRole('button', { name: 'Squash' }));
    expect(onChoose).toHaveBeenCalledWith('squash');
  });

  // #731, ADR-0200 §4: the row ends with + Another sport while a sport is left to offer.
  it('ends with + Another sport, the last out from under the current one, where it is offered', () => {
    const onAnother = jest.fn();
    const { onChoose } = drawBar({ sports: ['padel', 'tennis'], onAnother });
    layOut();
    act(() => jest.advanceTimersByTime(FRAME));

    const another = within(bar()).getByRole('button', { name: ANOTHER_SPORT });
    expect(within(another).getByText(ANOTHER.drawn)).toBeTruthy();
    expect(
      within(bar())
        .getAllByRole('button')
        .map((option) => option.props.accessibilityLabel),
    ).toEqual([ANOTHER_SPORT, 'Tennis', 'Padel']);
    // One frame in, the sport beside the current one has begun to slide out and it has not.
    // The slide is the pill's animated wrapper, a few host nodes up from the button.
    const opacityOf = (name: string): number | undefined => {
      let node = within(bar()).getByRole('button', { name }).parent;
      while (node !== null) {
        if (node.props.jestAnimatedStyle !== undefined) {
          return (getAnimatedStyle(node) as { readonly opacity?: number }).opacity;
        }
        node = node.parent;
      }
      return undefined;
    };
    expect(opacityOf('Tennis')).toBeGreaterThan(0);
    expect(opacityOf(ANOTHER_SPORT)).toBe(0);

    fireEvent.press(another);
    expect(onAnother).toHaveBeenCalledTimes(1);
    expect(onChoose).not.toHaveBeenCalled();
  });

  it('draws no + Another sport where nothing is offered', () => {
    drawBar();

    expect(within(bar()).queryByRole('button', { name: ANOTHER_SPORT })).toBeNull();
  });
});

/**
 * **Opening rightwards** — Top 10's switcher, at the left of its line's footer (#821; ADR-0205 §5,
 * Q19, Q37; home refactor 12, 13, note 4): the pill reads *Padel ›*, and the bar grows to the right
 * from where it stood, the current sport at its left end and the others sliding out after it.
 */
describe('the sport pill opening rightwards', () => {
  it('points its chevron the way it opens — Padel ›', () => {
    render(
      <SportPill
        sports={['padel', 'tennis']}
        sport="padel"
        words={WORDS}
        onUnfold={jest.fn()}
        opens="right"
      />,
    );

    expect(screen.getByText('›', { includeHiddenElements: true })).toBeTruthy();
    expect(screen.queryByText('‹', { includeHiddenElements: true })).toBeNull();
  });

  it('keeps ‹ on a page’s pill, which opens leftwards', () => {
    render(
      <SportPill sports={['padel', 'tennis']} sport="padel" words={WORDS} onUnfold={jest.fn()} />,
    );

    expect(screen.getByText('‹', { includeHiddenElements: true })).toBeTruthy();
  });

  it('lists the current sport first, chosen, then the others in the page’s order', () => {
    const { onChoose } = drawBar({ opens: 'right' });

    const names = within(bar())
      .getAllByRole('button')
      .map((option) => [option.props.accessibilityLabel, option.props.accessibilityState.selected]);
    expect(names).toEqual([
      ['Padel', true],
      ['Tennis', false],
      ['Squash', false],
      ['Badminton', false],
    ]);

    fireEvent.press(within(bar()).getByRole('button', { name: 'Tennis' }));
    expect(onChoose).toHaveBeenCalledWith('tennis');
  });

  it('turns the current sport’s chevron back — ‹, the way it folds', () => {
    drawBar({ opens: 'right' });

    const current = within(bar()).getByRole('button', { name: 'Padel' });
    expect(within(current).getByText('‹', { includeHiddenElements: true })).toBeTruthy();
    expect(within(current).queryByText('›', { includeHiddenElements: true })).toBeNull();
  });

  it('keeps the current sport in the bar’s own flow, so it stays where the pill stood', () => {
    drawBar({ opens: 'right' });
    layOut();
    act(() => jest.advanceTimersByTime(theme.motion.unfold / 2));

    // Nothing between the current sport and the bar moves: no animated style on the way up.
    let node = within(bar()).getByRole('button', { name: 'Padel' }).parent;
    while (node !== null && node.props.testID !== 'sport-bar') {
      expect(node.props.jestAnimatedStyle).toBeUndefined();
      node = node.parent;
    }
    expect(StyleSheet.flatten(bar().props.style as ViewStyle).width).toBeUndefined();
  });

  it('grows from the pill to the whole row over the unfold, as leftwards', () => {
    drawBar({ opens: 'right' });
    layOut();

    nextFrame();
    expect(barStyle().width).toBeGreaterThanOrEqual(CLOSED);
    expect(barStyle().width).toBeLessThan(ROW + 2 * PAD);
    // Rightwards: the moving end travels to the right of the pill's.
    expect(travelled()).toBeGreaterThan(0);

    act(() => jest.advanceTimersByTime(theme.motion.unfold + FRAME));
    expect(barStyle().width).toBe(ROW + 2 * PAD);
  });

  it('slides each sport out rightwards from under the current one, the nearest first', () => {
    drawBar({ opens: 'right' });
    layOut();

    act(() => jest.advanceTimersByTime(FRAME * 2));

    const nearest = slideOf('Tennis');
    expect(nearest.opacity).toBeGreaterThan(0);
    // Still under the current sport, to its left, on its way out to the right.
    expect(nearest.translateX).toBeLessThan(0);
    expect(slideOf('Badminton').opacity).toBe(0);

    act(() => jest.advanceTimersByTime(theme.motion.unfold));
    expect(slideOf('Badminton')).toEqual({ opacity: 1, translateX: 0 });
  });

  it('ends with + Another sport, the farthest right, where it is offered', () => {
    drawBar({ opens: 'right', sports: ['padel', 'tennis'], onAnother: jest.fn() });

    expect(
      within(bar())
        .getAllByRole('button')
        .map((option) => option.props.accessibilityLabel),
    ).toEqual(['Padel', 'Tennis', ANOTHER_SPORT]);
  });
});

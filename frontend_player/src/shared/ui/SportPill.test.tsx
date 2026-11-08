/**
 * **The sport pill's unfold, at its own seam** — the bar growing leftwards from the pill on the
 * UI thread, and simply open under reduced motion (play 41–42, #513; shared since #774). The router
 * suites walk what a tap does; this holds what the bar is drawn at while it does it.
 *
 * Reanimated is real here, as it is in the router harness (ADR-0176 §2): every worklet runs on the
 * JavaScript thread and `withTiming` on the fake clock. Nothing lays anything out under jest, so the
 * two widths the bar grows between are handed to it as layout events.
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import type { Sport } from '@/shared/vocabulary/sport';

import { ReducedMotionProvider } from './overlay';
import { SportBar, type AnotherSport, type BarCover, type SportPillWords } from './SportPill';
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
}: {
  readonly reduced?: boolean;
  readonly cover?: BarCover;
  readonly onAnother?: () => void;
  readonly sports?: readonly Sport[];
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
      />
    </ReducedMotionProvider>,
  );
  return { onChoose };
}

const bar = () => screen.getByTestId('sport-bar');

/** The two widths the layout would report: the whole row, and the current sport's pill. */
function layOut() {
  const current = within(bar()).getByRole('button', { name: 'Padel' });
  fireEvent(current, 'layout', {
    nativeEvent: { layout: { width: PILL, height: 27, x: 0, y: 0 } },
  });
  fireEvent(screen.getByTestId('sport-bar-row'), 'layout', {
    nativeEvent: { layout: { width: ROW, height: 27, x: 0, y: 0 } },
  });
}

function barStyle(): { readonly width?: number; readonly opacity?: number } {
  return getAnimatedStyle(bar()) as { readonly width?: number; readonly opacity?: number };
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
    expect(first.width).toBeGreaterThanOrEqual(PILL + 2 * PAD);
    expect(first.width).toBeLessThan(ROW + 2 * PAD);

    act(() => jest.advanceTimersByTime(theme.motion.unfold / 2));
    const halfway = barStyle().width ?? 0;
    expect(halfway).toBeGreaterThan(first.width ?? 0);
    expect(halfway).toBeLessThan(ROW + 2 * PAD);

    act(() => jest.advanceTimersByTime(theme.motion.unfold));
    expect(barStyle().width).toBe(ROW + 2 * PAD);
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

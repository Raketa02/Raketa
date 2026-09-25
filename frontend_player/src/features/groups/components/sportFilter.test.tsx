/**
 * **The fast filter's unfold, at its own seam** — the bar growing leftwards from the pill on the
 * UI thread, and simply open under reduced motion (play 41–42, #513). The router suite walks what
 * a tap does; this holds what the bar is drawn at while it does it.
 *
 * Reanimated is real here, as it is in the router harness (ADR-0176 §2): every worklet runs on the
 * JavaScript thread and `withTiming` on the fake clock. Nothing lays anything out under jest, so the
 * two widths the bar grows between are handed to it as layout events.
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import { ReducedMotionProvider, theme } from '@/shared/ui';

import { SportBar } from './SportFilter';

const PAD = theme.size.groupPage.filterPad;
const ROW = 300;
const PILL = 80;

function drawBar({ reduced = false }: { readonly reduced?: boolean } = {}) {
  const onChoose = jest.fn();
  render(
    <ReducedMotionProvider value={reduced}>
      <SportBar
        sports={['padel', 'tennis', 'squash', 'badminton']}
        sport="padel"
        onChoose={onChoose}
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

describe('the fast filter’s bar', () => {
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
});

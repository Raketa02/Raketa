/**
 * The three things about this control that are unobservable from the screen it sits on.
 *
 * **Asserted against the drawing, which is the declared exception to "assert what the
 * player can observe"** — the same exception `AvailabilityGrid.test.tsx` and
 * `ConfidenceRing.test.tsx` make, for the same reason. A fill has no role, no name and no
 * text, so a suite that only went through a screen could not tell a slider that draws a
 * zero-length fill at the minimum from one that draws a stub of `night` there and calls it
 * a control at rest. 6.10 says outright which of those is correct.
 *
 * The reading being hidden from assistive technology is the second: the control announces
 * the figure and the words as **one** value, and a figure that were readable a second time
 * on the way past would say the control has two. That is an absence, and absences are only
 * visible from here.
 *
 * The third is the reserved figure box, which is a `Text` nobody can see.
 *
 * Everything else — what the figure says, what the words say, what an increment does — was
 * asserted where a player met it, on the radius step. That step left with the Search radius
 * ([#582](https://github.com/Raketa02/Raketa/issues/582)), and this primitive has no caller
 * until the design system decides whether it stays.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { RadiusSlider, type RadiusSliderProps } from './RadiusSlider';
import { theme } from './theme';

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

const LABEL = 'How far to look';

function draw(overrides: Partial<RadiusSliderProps> = {}) {
  const props: RadiusSliderProps = {
    value: 10,
    minimum: 1,
    maximum: 50,
    fraction: 0.5,
    onSlideTo: () => undefined,
    onIncrement: () => undefined,
    onDecrement: () => undefined,
    figure: '10 km',
    widestFigure: '50 km',
    words: 'Across your town',
    accessibilityLabel: LABEL,
    accessibilityValueText: '10 kilometres, across your town',
    ...overrides,
  };
  return render(<RadiusSlider {...props} />);
}

/**
 * The filled portion of the track: the one `night` box that takes the track's full height.
 *
 * Found by its drawing because that is all it is — a fill has no role, no name and no text,
 * which is the whole reason these two assertions live here rather than on the step.
 */
function fillWidth(): ViewStyle['width'] {
  const fill = screen.UNSAFE_getAllByType(View).find((node) => {
    const style = flatten(node.props.style);
    return style?.backgroundColor === theme.color.night && style?.height === '100%';
  });
  return flatten(fill?.props.style).width;
}

describe('the row', () => {
  /**
   * The row is the control, not the thumb: a press anywhere on it moves the value to that
   * point. That is what gets the slider to the touch minimum with no `hitSlop` entry —
   * `profileControlGeometry.test.ts` owns the arithmetic; this is the component obeying it.
   */
  it('is the touch surface, at the touch minimum', () => {
    draw();
    expect(flatten(screen.getByLabelText(LABEL).props.style).height).toBe(theme.size.minTouch);
  });

  it('tells assistive technology it is adjustable, and how to adjust it', () => {
    draw();
    const row = screen.getByLabelText(LABEL);

    expect(row.props.accessibilityRole).toBe('adjustable');
    expect(row.props.accessibilityActions).toEqual([
      { name: 'increment', label: 'Further out' },
      { name: 'decrement', label: 'Closer in' },
    ]);
  });

  it('routes each action to its own callback and neither to the other', () => {
    const moves: string[] = [];
    draw({
      onIncrement: () => moves.push('up'),
      onDecrement: () => moves.push('down'),
    });

    const row = screen.getByLabelText(LABEL);
    fireEvent(row, 'accessibilityAction', { nativeEvent: { actionName: 'increment' } });
    fireEvent(row, 'accessibilityAction', { nativeEvent: { actionName: 'decrement' } });

    expect(moves).toEqual(['up', 'down']);
  });

  /** An action nobody declared must do nothing, rather than nudge the value either way. */
  it('ignores an action it did not offer', () => {
    const moves: string[] = [];
    draw({ onIncrement: () => moves.push('up'), onDecrement: () => moves.push('down') });

    fireEvent(screen.getByLabelText(LABEL), 'accessibilityAction', {
      nativeEvent: { actionName: 'activate' },
    });

    expect(moves).toEqual([]);
  });
});

/**
 * One finger, at a page position.
 *
 * `touchHistory` is what `PanResponder` builds its gesture state from, so it has to be
 * here; the two numbers that matter are `locationX` — where in the **row** the press
 * landed — and `pageX`, which every later move is reported against.
 */
function touchAt(x: number, pageX = x) {
  return {
    nativeEvent: { locationX: x, pageX, touches: [{ pageX, pageY: 0 }], changedTouches: [] },
    touchHistory: {
      touchBank: [
        {
          touchActive: true,
          currentPageX: pageX,
          currentPageY: 0,
          currentTimeStamp: 1,
          previousPageX: pageX,
          previousPageY: 0,
          previousTimeStamp: 0,
          startPageX: pageX,
          startPageY: 0,
          startTimeStamp: 0,
        },
      ],
      numberActiveTouches: 1,
      indexOfSingleActiveTouch: 0,
      mostRecentTimeStamp: 1,
    },
  };
}

/** A row 326pt wide — the content width of a 356pt phone, and 300pt of track inside it. */
const ROW_WIDTH = 326;
const TRAVEL = ROW_WIDTH - 26;

function laidOut() {
  const row = screen.getByLabelText(LABEL);
  fireEvent(row, 'layout', { nativeEvent: { layout: { width: ROW_WIDTH, height: 44 } } });
  return row;
}

describe('a press on the row', () => {
  /**
   * 6.10's load-bearing sentence: *"A press anywhere on the row moves the value to that
   * point and the pan continues from there."* It is what gets the control to 44pt without a
   * `hitSlop`, and it is the behaviour a thumb-only slider gets wrong — the player who taps
   * the far end of the track expects the far end of the range, not nothing.
   */
  it('moves the value to where the finger landed, wherever on the row that was', () => {
    const slid: number[] = [];
    draw({ onSlideTo: (fraction) => slid.push(fraction) });
    const row = laidOut();

    fireEvent(row, 'responderGrant', touchAt(13 + TRAVEL / 2));
    expect(slid).toEqual([0.5]);
  });

  it('reaches both ends of the track', () => {
    const slid: number[] = [];
    draw({ onSlideTo: (fraction) => slid.push(fraction) });
    const row = laidOut();

    fireEvent(row, 'responderGrant', touchAt(13));
    fireEvent(row, 'responderGrant', touchAt(13 + TRAVEL));
    expect(slid).toEqual([0, 1]);
  });

  /**
   * The row is 44pt tall and the track is 4 of them, so most presses land above or below
   * the track — and half a thumb at each end is outside it horizontally. Those are presses
   * on the control, and they report a position past the end rather than nothing.
   */
  it('reports a press past either end of the track as being past it', () => {
    const slid: number[] = [];
    draw({ onSlideTo: (fraction) => slid.push(fraction) });
    const row = laidOut();

    fireEvent(row, 'responderGrant', touchAt(0));
    fireEvent(row, 'responderGrant', touchAt(ROW_WIDTH));
    expect(slid[0]).toBeLessThan(0);
    expect(slid[1]).toBeGreaterThan(1);
  });

  /** The pan continues from the press, so the value tracks the finger rather than jumping. */
  it('keeps reporting as the finger moves, measured from where it started', () => {
    const slid: number[] = [];
    draw({ onSlideTo: (fraction) => slid.push(fraction) });
    const row = laidOut();

    // Down at a quarter along, then dragged 150pt further right — half the track.
    fireEvent(row, 'responderGrant', touchAt(13 + TRAVEL / 4, 500));
    fireEvent(row, 'responderMove', touchAt(0, 650));

    expect(slid).toEqual([0.25, 0.75]);
  });

  /**
   * Before layout there is no track to have pressed. Reporting a position out of a width of
   * zero would put a `NaN` — or an arbitrary end of the range — into the draft.
   */
  it('reports nothing at all before the row has been laid out', () => {
    const slid: number[] = [];
    draw({ onSlideTo: (fraction) => slid.push(fraction) });

    fireEvent(screen.getByLabelText(LABEL), 'responderGrant', touchAt(120));
    expect(slid).toEqual([]);
  });

  /**
   * The fix for the coordinate space, declared rather than exercised: `locationX` is
   * measured against the touch's **target**, so a track or a thumb that could be a target
   * would report in its own coordinates — low by the track's inset, or near zero anywhere
   * on the thumb. Jest does no hit testing, so the declaration is the only place this is
   * observable; on a device it is the difference between a working slider and one that
   * snaps to the minimum whenever the thumb itself is grabbed.
   */
  it('takes the touch itself, so no child of it can be the target', () => {
    draw();
    expect(screen.getByLabelText(LABEL).props.pointerEvents).toBe('box-only');
  });
});

describe('the filled portion of the track', () => {
  /**
   * 6.10, in as many words: *at the minimum there is no fill at all — a zero-length fill is
   * correct, because the smallest radius is the smallest radius and not an error.* A stub
   * of `night` sitting under the thumb there would read as a control at rest.
   */
  it('is not drawn at all at the smallest radius', () => {
    draw({ fraction: 0 });
    expect(fillWidth()).toBe('0%');
  });

  it('reaches the end of the track at the largest', () => {
    draw({ fraction: 1 });
    expect(fillWidth()).toBe('100%');
  });

  /**
   * A radius recorded under bounds that have since been narrowed is still a fact about the
   * player, and it arrives here as a fraction outside the track. The fill stays on it.
   */
  it('stays on the track for a fraction from outside it', () => {
    draw({ fraction: 1.6 });
    expect(fillWidth()).toBe('100%');
  });
});

describe('the reading above the track', () => {
  /**
   * One announcement, not three. The figure and the words are the same fact drawn twice for
   * whoever is looking; the control below carries both of them as its value.
   */
  it('is hidden from assistive technology, because the control announces it', () => {
    draw();

    expect(screen.queryByText('10 km')).toBeNull();
    expect(screen.queryByText('Across your town')).toBeNull();
    expect(screen.getByText('10 km', { includeHiddenElements: true })).toBeTruthy();
    expect(screen.getByText('Across your town', { includeHiddenElements: true })).toBeTruthy();
  });

  /**
   * The widest figure the bounds can produce, drawn invisibly, is what gives the box its
   * width — so dragging from 9 to 10 does not move the text under the finger moving it.
   */
  it('reserves the widest figure behind the one it is showing', () => {
    draw({ figure: '9 km', widestFigure: '50 km' });

    const reserved = screen.getByText('50 km', { includeHiddenElements: true });
    expect(flatten(reserved.props.style).opacity).toBe(0);
    expect(screen.getByText('9 km', { includeHiddenElements: true })).toBeTruthy();
  });
});

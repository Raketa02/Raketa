/**
 * The meter — 7.3's first row, and the one drawn object whose whole accessibility contract
 * is *nothing*.
 *
 * `the-words.md` §20.8: the why-fit row prints `×{weight} → {value}` two words before the
 * meter, so a bar visualising that number is 6.8's double announcement read on a second
 * surface. The test that matters is therefore an **absence**, and an absence is exactly what
 * stops being true by accident — somebody adds `accessibilityRole="progressbar"` to be
 * helpful, and every row is announced twice.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { METER_TONE_FILL, Meter } from './Meter';
import { theme } from './theme';

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

const parts = () => {
  const views = screen.UNSAFE_getAllByType(View);
  return { track: views[0], fill: views[1] };
};

describe('the meter', () => {
  it('is hidden from assistive technology, on both platforms', () => {
    render(<Meter share={0.4} />);
    const { track } = parts();

    // Both, because `accessibilityElementsHidden` is iOS and `importantForAccessibility` is
    // Android — one of them alone leaves the meter readable on the other platform.
    expect(track?.props.accessibilityElementsHidden).toBe(true);
    expect(track?.props.importantForAccessibility).toBe('no-hide-descendants');
  });

  it('announces no value, because `progressbar` appears nowhere in this contract', () => {
    render(<Meter share={0.4} />);
    const { track } = parts();

    expect(track?.props.accessibilityRole).toBeUndefined();
    expect(track?.props.accessibilityValue).toBeUndefined();
    expect(track?.props.accessibilityLabel).toBeUndefined();
  });

  /**
   * A meter whose caller grades nothing is drawn exactly as every meter was before there was a
   * tone at all — which is what makes the why-fit sheet's rows a caller that passes none.
   */
  it("draws 7.3's geometry — 5 tall, radius 3, a line2 track and a night fill", () => {
    render(<Meter share={0.4} />);
    const { track, fill } = parts();

    expect(flatten(track?.props.style)).toMatchObject({
      height: theme.size.meter,
      borderRadius: theme.radius.meter,
      backgroundColor: theme.color.line2,
    });
    expect(flatten(fill?.props.style)).toMatchObject({
      width: '40%',
      backgroundColor: theme.color.night,
    });
  });

  /**
   * The tone is a **step in an existing fill** and never a ladder of the meter's own: what is
   * asserted is that each step draws its own colour, and *where* a figure falls on the ladder
   * is the caller's rule, tested where that rule lives.
   */
  it.each(['good', 'neutral', 'poor'] as const)('draws the %s tone in its own fill', (tone) => {
    render(<Meter share={0.4} tone={tone} />);

    expect(flatten(parts().fill?.props.style)).toMatchObject({
      backgroundColor: METER_TONE_FILL[tone],
    });
  });

  it('clamps a share the caller did not clamp, in both directions', () => {
    render(<Meter share={1.4} />);
    expect(flatten(parts().fill?.props.style)).toMatchObject({ width: '100%' });

    screen.rerender(<Meter share={-0.2} />);
    expect(flatten(parts().fill?.props.style)).toMatchObject({ width: '0%' });
  });
});

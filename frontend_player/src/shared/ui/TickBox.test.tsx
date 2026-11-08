/**
 * The tick box, asserted through what a player and a screen reader can observe — plus the
 * three rules 6.11 is most likely to lose silently.
 *
 * The visual is a 22pt square against a 44pt minimum, touch has no hover to fall back on,
 * and the refused border is drawn conditionally. None of the three is reachable by a query,
 * which is the same declared exception `Chip.test.tsx` makes for the same reasons.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { Pressable, StyleSheet, View, type ViewStyle } from 'react-native';

import { theme } from './theme';
import { TickBox } from './TickBox';

const LABEL = 'I am 18 or over';

/** The row as React Native would draw it, at rest or under a finger. */
function row(pressed: boolean): ViewStyle {
  return StyleSheet.flatten(screen.UNSAFE_getByType(Pressable).props.style({ pressed }));
}

/**
 * The box itself, found by the one property only it has.
 *
 * By shape rather than by index: the field wrapper, the row and the box are all `View`s,
 * and a positional lookup silently starts measuring a different one the moment the tree
 * gains a wrapper.
 */
function box(): ViewStyle {
  const styles = screen
    .UNSAFE_getAllByType(View)
    .map((node) => StyleSheet.flatten(node.props.style as ViewStyle));
  const found = styles.find((style) => style?.width === theme.size.tickBox.box);
  if (found === undefined) throw new Error('no tick box in the tree');
  return found;
}

describe('what a tick box reports', () => {
  it('announces the claim, its role and its state', () => {
    render(<TickBox label={LABEL} checked={false} onChange={jest.fn()} />);

    const control = screen.getByRole('checkbox', { name: LABEL });
    // Never omitted when false: *not ticked* and *not a choice* are different things to
    // be told.
    expect(control.props.accessibilityState?.checked).toBe(false);
  });

  it('hands back the answer the press produces, in both directions', () => {
    const onChange = jest.fn();
    const { rerender } = render(<TickBox label={LABEL} checked={false} onChange={onChange} />);

    fireEvent.press(screen.getByRole('checkbox', { name: LABEL }));
    expect(onChange).toHaveBeenLastCalledWith(true);

    rerender(<TickBox label={LABEL} checked onChange={onChange} />);
    fireEvent.press(screen.getByRole('checkbox', { name: LABEL }));
    // A tick box unticks. Nothing here is one-way — the player may withdraw the claim
    // right up until the form is sent.
    expect(onChange).toHaveBeenLastCalledWith(false);
  });

  it('reports nothing while disabled', () => {
    const onChange = jest.fn();
    render(<TickBox label={LABEL} checked={false} onChange={onChange} disabled />);

    fireEvent.press(screen.getByRole('checkbox', { name: LABEL }));

    expect(onChange).not.toHaveBeenCalled();
  });

  it('announces a refusal as an alert, with the words beside the box', () => {
    render(
      <TickBox label={LABEL} checked={false} onChange={jest.fn()} error="Confirm that you are." />,
    );

    expect(screen.getByRole('alert').props.children).toBe('Confirm that you are.');
  });
});

describe('what only a finger meets', () => {
  it('reaches 44pt through the row, so the words are part of the target', () => {
    render(<TickBox label={LABEL} checked={false} onChange={jest.fn()} />);

    // The box is 22pt; the row is what the finger meets, and it carries the minimum
    // without a hitSlop entry — a slop around the square would stop where the sentence
    // starts.
    expect(row(false).minHeight).toBe(theme.size.minTouch);
    expect(box().width).toBe(theme.size.tickBox.box);
  });

  /**
   * **The mocks' rounded square** (#785, mocks 4 and 6): 22pt with the availability cell's corner,
   * measured off mock 6 at 2,1 pixels to the point — 47 pixels across, a corner of 12. A corner of
   * half the side would be a circle, which is the friends picker's round box and not this one.
   */
  it('is the mocks’ rounded square, larger than the 20pt it was', () => {
    render(<TickBox label={LABEL} checked={false} onChange={jest.fn()} />);

    const drawn = box();
    expect([drawn.width, drawn.height]).toEqual([22, 22]);
    expect(drawn.borderRadius).toBe(theme.radius.availabilityCell);
    expect(drawn.borderRadius).toBeLessThan(22 / 2);
  });

  it('declares a pressed appearance, because there is no hover', () => {
    render(<TickBox label={LABEL} checked={false} onChange={jest.fn()} />);

    expect(row(true).opacity).toBe(0.7);
    expect(row(false).opacity).toBeUndefined();
  });

  it('inverts the fill when ticked rather than tinting it', () => {
    render(<TickBox label={LABEL} checked onChange={jest.fn()} />);

    expect(box().backgroundColor).toBe(theme.color.ink);
    expect(box().borderColor).toBe(theme.color.ink);
  });

  it('draws the refused border only while the box is unticked', () => {
    const { rerender } = render(
      <TickBox label={LABEL} checked={false} onChange={jest.fn()} error="Confirm that you are." />,
    );
    expect(box().borderColor).toBe(theme.color.red);

    rerender(<TickBox label={LABEL} checked onChange={jest.fn()} error="Confirm that you are." />);
    // Once it is ticked there is nothing left to fix, and a red outline around a satisfied
    // control contradicts the answer inside it.
    expect(box().borderColor).toBe(theme.color.ink);
  });
});

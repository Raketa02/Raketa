/**
 * The Undo toast — the words it is handed, one action named for what it undoes, and a ring that
 * says nothing: the count is the words', and the caller announces the toast once.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';

import { UndoToast } from './UndoToast';

const WINDOW = 10_000;

function draw(onAction = jest.fn()) {
  render(
    <UndoToast
      message="Booking in 7 s"
      actionLabel="Undo"
      actionAccessibilityLabel="Undo the booking"
      onAction={onAction}
      endsAt={Date.now() + 7_000}
      windowMs={WINDOW}
    />,
  );
  return onAction;
}

describe('UndoToast', () => {
  it('draws the caller’s words and one action, named for what it undoes', () => {
    draw();

    expect(screen.getByText('Booking in 7 s')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Undo the booking' })).toBeTruthy();
    expect(screen.getByText('Undo')).toBeTruthy();
  });

  it('undoes on the press', () => {
    const onAction = draw();

    fireEvent.press(screen.getByRole('button', { name: 'Undo the booking' }));

    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('is not a live region — a count that moves every second would talk over everything', () => {
    draw();

    expect(screen.getByText('Booking in 7 s').props.accessibilityLiveRegion).toBeUndefined();
    expect(screen.getByTestId('undo-toast').props.accessibilityLiveRegion).toBeUndefined();
  });
});

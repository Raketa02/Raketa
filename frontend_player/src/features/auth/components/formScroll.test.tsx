/**
 * **The form's scroll, after Android's keyboard has gone** — why *Sign in* took several taps on an
 * Android phone and one on an iPhone.
 *
 * On Android the window resizes for the keyboard, so with the keyboard up the form can scroll; a
 * drag scrolls it and puts the keyboard away, the window grows back, and Android puts the offset
 * back to the top itself. Under the New Architecture (React Native 0.76) the shadow tree keeps the
 * offset the drag left, so every control in the form is *measured* that far above where it is
 * drawn — and a press is measured: a finger that trembles while it is down reads as sliding off the
 * button, and the press is cancelled. Measured on a Galaxy A32: the button drawn at 599 and measured
 * at 523, after a drag that reached 76.
 *
 * That half is native and no suite can see it; a device look is its check. What a suite can hold is
 * the answer: a scroll event while the form fits is that putting-back — nothing fitting can be
 * scrolled — and the scroll is mounted afresh, from a true offset of nought.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { Platform, Text } from 'react-native';

import { FormScroll } from './AuthFrame';

/** A scroll event as the native side sends it — the content, the viewport, where it stands. */
function scrollEvent(content: number, viewport: number, at = 0) {
  return {
    nativeEvent: {
      contentOffset: { x: 0, y: at },
      contentSize: { width: 360, height: content },
      layoutMeasurement: { width: 360, height: viewport },
    },
  };
}

function drawForm() {
  render(
    <FormScroll>
      <Text>The form</Text>
    </FormScroll>,
  );
  return screen.getByTestId('auth-frame');
}

describe('the form scroll after the keyboard has gone', () => {
  it('on Android, is mounted afresh when a scroll comes while the form fits — the offset put back', () => {
    jest.replaceProperty(Platform, 'OS', 'android');
    const scroll = drawForm();

    fireEvent.scroll(scroll, scrollEvent(784, 805));

    expect(screen.getByTestId('auth-frame')).not.toBe(scroll);
    expect(screen.queryByText('The form')).not.toBeNull();
  });

  it('on Android, is kept when the form is taller than the screen — a scroll a person made', () => {
    jest.replaceProperty(Platform, 'OS', 'android');
    const scroll = drawForm();

    fireEvent.scroll(scroll, scrollEvent(784, 495, 76));

    expect(screen.getByTestId('auth-frame')).toBe(scroll);
  });

  it('on iOS, is kept — the keyboard is an inset there and the window never resizes', () => {
    jest.replaceProperty(Platform, 'OS', 'ios');
    const scroll = drawForm();

    fireEvent.scroll(scroll, scrollEvent(784, 805));

    expect(screen.getByTestId('auth-frame')).toBe(scroll);
  });
});

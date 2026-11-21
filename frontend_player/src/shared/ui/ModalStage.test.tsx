/**
 * **The Android stage and its host** — imported by file, because the harness runs as iOS and
 * would otherwise resolve `ModalStage` to the native window.
 *
 * What a screen-level suite cannot see: that the layer is drawn by the host and not where
 * the overlay was rendered, that the app beneath is hidden from a screen reader while it is
 * up and shown again when it is down, that the hardware back is answered and swallowed, and
 * that an overlay rendered with no host at all still draws — in place — so a unit test of a
 * sheet needs no host to find its controls. The reason there is a stage at all is on
 * `overlay.tsx`'s `OverlayHost`: on a Galaxy A55 with the radar mounted, the native window's
 * content was a sliver and no press inside it could complete (2026-09-17).
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { useState } from 'react';
import { Animated, Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';

import { ModalStage, type ModalStageProps } from './ModalStage.android';
import { OverlayHost } from './overlay';
import { theme } from './theme';

/** The app beneath a layer is hidden from a listener on purpose; a walk still looks. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

beforeEach(() => {
  watchHardwareBack();
});

afterEach(() => {
  stopWatchingHardwareBack();
});

/** An app with one sheet, opened and closed by a control of its own. */
function App({
  onRequestClose,
  animationType = 'none',
}: {
  readonly onRequestClose?: () => void;
  readonly animationType?: ModalStageProps['animationType'];
} = {}) {
  const [open, setOpen] = useState(false);
  return (
    <OverlayHost>
      <View testID="screen">
        <Pressable onPress={() => setOpen(true)} accessibilityLabel="Open" />
        <ModalStage
          visible={open}
          onRequestClose={onRequestClose ?? (() => setOpen(false))}
          animationType={animationType}
          layer="sheet"
        >
          <View testID="sheet">
            <Text>The sheet</Text>
            <Pressable onPress={() => setOpen(false)} accessibilityLabel="Close" />
          </View>
        </ModalStage>
      </View>
    </OverlayHost>
  );
}

describe('a stage under the host', () => {
  it('draws its layer at the root, above the app, and takes it down on close', () => {
    render(<App />);
    expect(screen.queryByTestId('modal-stage')).toBeNull();

    fireEvent.press(screen.getByLabelText('Open'));

    expect(screen.getByTestId('modal-stage')).toBeTruthy();
    expect(screen.getByText('The sheet')).toBeTruthy();
    // A sibling of the app, not a descendant of the screen that opened it — the app beneath
    // is hidden from a listener while the layer is up, so the walk looks past that.
    const beneath = screen.getByTestId('overlay-host-beneath', HIDDEN_TOO);
    expect(within(beneath).getByTestId('screen', HIDDEN_TOO)).toBeTruthy();
    expect(within(beneath).queryByTestId('modal-stage', HIDDEN_TOO)).toBeNull();
    expect(within(beneath).queryByText('The sheet', HIDDEN_TOO)).toBeNull();

    fireEvent.press(screen.getByLabelText('Close'));
    expect(screen.queryByTestId('modal-stage')).toBeNull();
    expect(screen.queryByText('The sheet')).toBeNull();
    // ...and the app is a listener's again.
    expect(screen.getByTestId('screen')).toBeTruthy();
  });

  it('hides the whole app beneath from a screen reader while a layer is up', () => {
    render(<App />);
    const beneath = () => screen.getByTestId('overlay-host-beneath', HIDDEN_TOO).props;
    expect(beneath().importantForAccessibility).toBe('auto');
    expect(beneath().accessibilityElementsHidden).toBe(false);

    fireEvent.press(screen.getByLabelText('Open'));
    expect(beneath().importantForAccessibility).toBe('no-hide-descendants');
    expect(beneath().accessibilityElementsHidden).toBe(true);

    fireEvent.press(screen.getByLabelText('Close'));
    expect(beneath().importantForAccessibility).toBe('auto');
  });

  it('orders its layer by design-system 9.3, beside the toast host', () => {
    render(<App />);
    fireEvent.press(screen.getByLabelText('Open'));
    const style = StyleSheet.flatten(screen.getByTestId('modal-stage').props.style as ViewStyle);
    expect(style.zIndex).toBe(theme.layer.sheet);
    expect(theme.layer.sheet).toBeLessThan(theme.layer.toast);
    expect(theme.layer.popover).toBeGreaterThan(theme.layer.toast);
  });

  it('hides a layer from a screen reader while a newer one is up over it', () => {
    // A sheet that opens a second sheet from inside itself — the record's Block (#587).
    function Stacked() {
      const [first, setFirst] = useState(true);
      const [second, setSecond] = useState(false);
      return (
        <OverlayHost>
          <ModalStage
            visible={first}
            onRequestClose={() => setFirst(false)}
            animationType="none"
            layer="sheet"
          >
            <View testID="first">
              <Pressable onPress={() => setSecond(true)} accessibilityLabel="Ask" />
              <ModalStage
                visible={second}
                onRequestClose={() => setSecond(false)}
                animationType="none"
                layer="sheet"
              >
                <View testID="second">
                  <Pressable onPress={() => setSecond(false)} accessibilityLabel="Cancel" />
                </View>
              </ModalStage>
            </View>
          </ModalStage>
        </OverlayHost>
      );
    }
    render(<Stacked />);
    const layerOf = (testID: string) =>
      screen
        .getAllByTestId('modal-stage', HIDDEN_TOO)
        .find((layer) => within(layer).queryByTestId(testID, HIDDEN_TOO) !== null)!;
    // One layer up, and a listener is in it.
    expect(layerOf('first').props.importantForAccessibility).toBe('auto');

    fireEvent.press(screen.getByLabelText('Ask'));
    expect(screen.getAllByTestId('modal-stage', HIDDEN_TOO)).toHaveLength(2);
    // The newer layer is the listener's; the one under it is hidden, as the app beneath is.
    expect(layerOf('first').props.importantForAccessibility).toBe('no-hide-descendants');
    expect(layerOf('first').props.accessibilityElementsHidden).toBe(true);
    expect(layerOf('second').props.importantForAccessibility).toBe('auto');
    expect(screen.queryByLabelText('Ask')).toBeNull();

    // The back answers the newer one alone.
    act(() => {
      pressHardwareBack();
    });
    expect(screen.getAllByTestId('modal-stage', HIDDEN_TOO)).toHaveLength(1);
    expect(layerOf('first').props.importantForAccessibility).toBe('auto');
    expect(screen.getByLabelText('Ask')).toBeTruthy();
  });

  it('answers the hardware back with the overlay’s own request, and swallows it', () => {
    const onRequestClose = jest.fn();
    render(<App onRequestClose={onRequestClose} />);
    // Nothing up: nothing answers, and the gesture falls through.
    expect(pressHardwareBack()).toBe(false);

    fireEvent.press(screen.getByLabelText('Open'));
    let swallowed = false;
    act(() => {
      swallowed = pressHardwareBack();
    });
    expect(swallowed).toBe(true);
    expect(onRequestClose).toHaveBeenCalledTimes(1);
  });
});

/**
 * **The arrival runs once the layer is on screen** (2026-11-21). It used to start in the effect
 * that hands the layer to the host — a commit *before* the host draws it — so on a Galaxy A32 the
 * player record's layer was first laid out 235 ms into a 260 ms slide, and the sheet simply
 * appeared. Under the native driver a test sees no frames, so what it can see is when the slide is
 * started: never before the layer is laid out, and once per arrival.
 */
describe('the arrival', () => {
  const LAID_OUT = { nativeEvent: { layout: { x: 0, y: 0, width: 390, height: 844 } } };

  function watchSlides(): { readonly started: () => number; readonly restore: () => void } {
    let count = 0;
    const timing = jest.spyOn(Animated, 'timing').mockImplementation(
      () =>
        ({
          start: () => {
            count += 1;
          },
          stop: () => undefined,
          reset: () => undefined,
        }) as Animated.CompositeAnimation,
    );
    return { started: () => count, restore: () => timing.mockRestore() };
  }

  it('slides only once its layer is laid out, never on a clock that ran before it was drawn', () => {
    const slides = watchSlides();
    render(<App animationType="slide" />);

    fireEvent.press(screen.getByLabelText('Open'));
    // In the tree, and not yet on screen: nothing may move yet.
    expect(screen.getByTestId('modal-stage')).toBeTruthy();
    expect(slides.started()).toBe(0);

    fireEvent(screen.getByTestId('modal-stage'), 'layout', LAID_OUT);
    expect(slides.started()).toBe(1);
    // A later layout — a rotation, the keyboard — is not a second arrival.
    fireEvent(screen.getByTestId('modal-stage'), 'layout', LAID_OUT);
    expect(slides.started()).toBe(1);
    slides.restore();
  });

  it('slides again on the next arrival', () => {
    const slides = watchSlides();
    render(<App animationType="slide" />);
    fireEvent.press(screen.getByLabelText('Open'));
    fireEvent(screen.getByTestId('modal-stage'), 'layout', LAID_OUT);
    fireEvent.press(screen.getByLabelText('Close'));

    fireEvent.press(screen.getByLabelText('Open'));
    expect(slides.started()).toBe(1);
    fireEvent(screen.getByTestId('modal-stage'), 'layout', LAID_OUT);
    expect(slides.started()).toBe(2);
    slides.restore();
  });
});

describe('a stage with no host', () => {
  it('draws in place, so an overlay rendered alone is still found by its controls', () => {
    const onRequestClose = jest.fn();
    render(
      <View testID="alone">
        <ModalStage visible onRequestClose={onRequestClose} animationType="slide" layer="popover">
          <Text>In place</Text>
        </ModalStage>
      </View>,
    );
    expect(within(screen.getByTestId('alone')).getByTestId('modal-stage')).toBeTruthy();
    expect(within(screen.getByTestId('alone')).getByText('In place')).toBeTruthy();
  });
});

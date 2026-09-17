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
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';

import { ModalStage } from './ModalStage.android';
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
function App({ onRequestClose }: { readonly onRequestClose?: () => void } = {}) {
  const [open, setOpen] = useState(false);
  return (
    <OverlayHost>
      <View testID="screen">
        <Pressable onPress={() => setOpen(true)} accessibilityLabel="Open" />
        <ModalStage
          visible={open}
          onRequestClose={onRequestClose ?? (() => setOpen(false))}
          animationType="none"
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

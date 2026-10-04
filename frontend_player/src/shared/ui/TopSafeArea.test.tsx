/**
 * **The inset is there on the first frame.** A tab root arrives with no transition, so whatever
 * its first frame draws is what the person sees — and a frame drawn without the inset, corrected
 * on the next, was the header blinking on every tab press on Android (#529).
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, type Metrics } from 'react-native-safe-area-context';

import { TopSafeArea } from './TopSafeArea';

/** A notched phone: both insets exist, so taking the wrong one is visible. */
const NOTCHED: Metrics = {
  frame: { x: 0, y: 0, width: 390, height: 844 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

function frameStyle() {
  return StyleSheet.flatten(screen.UNSAFE_getByType(TopSafeArea).findByType(View).props.style);
}

describe('the top safe area', () => {
  it('is padded by the top inset on its first render, and by nothing at the bottom', () => {
    render(
      <SafeAreaProvider initialMetrics={NOTCHED}>
        <TopSafeArea>
          <Text>the page</Text>
        </TopSafeArea>
      </SafeAreaProvider>,
    );

    expect(frameStyle().paddingTop).toBe(47);
    expect(frameStyle().paddingBottom).toBeUndefined();
    expect(screen.getByText('the page')).toBeTruthy();
  });

  it('keeps the screen’s own style under the inset', () => {
    render(
      <SafeAreaProvider initialMetrics={NOTCHED}>
        <TopSafeArea style={{ flex: 1, paddingTop: 3 }}>
          <Text>the page</Text>
        </TopSafeArea>
      </SafeAreaProvider>,
    );

    // The inset is the frame's and wins: a screen that padded its own top would be drawn under
    // the status bar again.
    expect(frameStyle()).toMatchObject({ flex: 1, paddingTop: 47 });
  });
});

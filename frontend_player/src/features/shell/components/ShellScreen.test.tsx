/**
 * The arrangement, asserted structurally — because every claim 10.1 makes about it is a claim
 * about *what contains what*, and all three fail invisibly.
 *
 * A header inside the scroller still renders, still reads, and only misbehaves once the page
 * is long enough to scroll — which the ranked pool is and no screen in this app is today. A
 * CTA inside the scroller is a CTA that leaves the screen. And a bottom inset taken here as
 * well as by the tab bar is 34pt of nothing above the home indicator, which reads as padding
 * rather than as a bug.
 */

import { render, screen, within } from '@testing-library/react-native';
import { Children, type ReactNode } from 'react';
import { ScrollView, Text } from 'react-native';
import { SafeAreaProvider, SafeAreaView, type Metrics } from 'react-native-safe-area-context';

import { ShellScreen } from './ShellScreen';

/** A notched phone: both insets exist, so taking the wrong one is visible. */
const METRICS: Metrics = {
  frame: { x: 0, y: 0, width: 390, height: 844 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

function renderScreen(action?: ReactNode) {
  return render(
    <SafeAreaProvider initialMetrics={METRICS}>
      <ShellScreen title="Find a game" action={action}>
        <Text>the page</Text>
      </ShellScreen>
    </SafeAreaProvider>,
  );
}

function scroller() {
  return screen.UNSAFE_getByType(ScrollView);
}

/** Header, scroller, and the pinned block when there is one. */
function siblings(): readonly ReactNode[] {
  return Children.toArray(screen.UNSAFE_getByType(SafeAreaView).props.children);
}

describe('what the scroller contains', () => {
  it('does not contain the header — it is pinned above it', () => {
    renderScreen();

    expect(screen.getByRole('header')).toBeTruthy();
    expect(within(scroller()).queryByRole('header')).toBeNull();
    expect(within(scroller()).getByText('the page')).toBeTruthy();
  });

  it('does not contain the call to action either', () => {
    renderScreen(<Text>Search</Text>);

    expect(screen.getByText('Search')).toBeTruthy();
    expect(within(scroller()).queryByText('Search')).toBeNull();
  });
});

describe('the call to action', () => {
  it('is a pinned block only when the screen has something to press', () => {
    // Not an empty strip standing in for one: the court screen populates the CTA on one of
    // its three branches, and the two that do not give the height back.
    renderScreen();
    expect(siblings()).toHaveLength(2);

    screen.unmount();
    renderScreen(<Text>Search</Text>);
    expect(siblings()).toHaveLength(3);
  });
});

describe('the safe area', () => {
  it('takes the top edge and leaves the bottom to the tab bar', () => {
    renderScreen();

    // `edges` and not a measured padding, because the padding is the library's arithmetic
    // and this is the app's decision: the screen asks for the top inset and asks for no
    // other. The bottom one is the bar's, and `TabBar` has its own suite proving it takes it.
    expect(screen.UNSAFE_getByType(SafeAreaView).props.edges).toEqual(['top']);
  });
});

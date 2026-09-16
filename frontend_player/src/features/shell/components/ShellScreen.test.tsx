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

import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { Children, type ReactNode } from 'react';
import { RefreshControl, ScrollView, Text } from 'react-native';
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

describe('a screen with no title', () => {
  /**
   * The game screen's plan lead is the first ([#414](https://github.com/Raketa02/Raketa/issues/414)):
   * an eyebrow, no h1. The header is still pinned and still a heading — the eyebrow is what it
   * says — and the page under it is untouched.
   */
  it('pins the eyebrow as its heading and draws nothing under it', () => {
    render(
      <SafeAreaProvider initialMetrics={METRICS}>
        <ShellScreen eyebrow="Doubles · Counted">
          <Text>the page</Text>
        </ShellScreen>
      </SafeAreaProvider>,
    );

    const heading = screen.getByRole('header', { name: 'Doubles · Counted' });

    expect(within(scroller()).queryByRole('header')).toBeNull();
    expect(within(heading).getAllByText(/./)).toHaveLength(1);
    expect(within(scroller()).getByText('the page')).toBeTruthy();
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

/**
 * **Pull to refresh is forwarded, not designed**: a screen that says what a pull re-reads gets
 * the platform's control over its page, spinning from the pull until what it asked for has
 * settled; a screen that says nothing gets no control at all, so the gesture means something
 * where it is offered. The spinner is the pull's own — never a background refetch's.
 */
describe('pull to refresh', () => {
  function renderRefreshing(onRefresh?: () => Promise<unknown>) {
    return render(
      <SafeAreaProvider initialMetrics={METRICS}>
        <ShellScreen title="Chats" onRefresh={onRefresh}>
          <Text>the page</Text>
        </ShellScreen>
      </SafeAreaProvider>,
    );
  }

  const control = () => screen.UNSAFE_getByType(RefreshControl);

  it('draws no control on a screen that re-reads nothing', () => {
    renderRefreshing();

    expect(scroller().props.refreshControl).toBeUndefined();
  });

  it('spins from the pull until what it asked for has settled, refused or not', async () => {
    let settle: () => void = () => {};
    const onRefresh = jest.fn(
      () =>
        new Promise<void>((resolve) => {
          settle = resolve;
        }),
    );
    renderRefreshing(onRefresh);
    expect(control().props.refreshing).toBe(false);

    await act(async () => {
      fireEvent(control(), 'refresh');
    });

    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(control().props.refreshing).toBe(true);

    await act(async () => {
      settle();
    });
    expect(control().props.refreshing).toBe(false);

    // A refusal settles it too — a spinner that never stopped would be a lie about the read.
    const refused = jest.fn(() => Promise.reject(new Error('refused')));
    screen.unmount();
    renderRefreshing(refused);
    await act(async () => {
      fireEvent(control(), 'refresh');
    });
    expect(control().props.refreshing).toBe(false);
  });

  it('asks once for one pull, however many times the gesture fires while it is in flight', async () => {
    let settle: () => void = () => {};
    const onRefresh = jest.fn(
      () =>
        new Promise<void>((resolve) => {
          settle = resolve;
        }),
    );
    renderRefreshing(onRefresh);

    await act(async () => {
      fireEvent(control(), 'refresh');
      fireEvent(control(), 'refresh');
    });
    expect(onRefresh).toHaveBeenCalledTimes(1);

    await act(async () => {
      settle();
    });
    await act(async () => {
      fireEvent(control(), 'refresh');
    });
    expect(onRefresh).toHaveBeenCalledTimes(2);
  });
});

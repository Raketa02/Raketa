/**
 * The arrangement, asserted structurally — because every claim 10.1 makes about it is a claim
 * about *what contains what*, and all three fail invisibly.
 *
 * A header inside the scroller still renders, still reads, and only misbehaves once the page
 * is long enough to scroll — which the ranked pool is and no screen in this app is today. A
 * CTA inside the scroller is a CTA that leaves the screen. And a bottom inset taken here as
 * well as by the tab bar is 34pt of nothing above the home indicator, which reads as padding
 * rather than as a bug.
 *
 * **Where the screen ends is the bar's reach** (ADR-0210 §3, #881): the bar floats over the
 * screen's foot, so a page that forgot it would leave its last row under the bar, and a CTA that
 * forgot it would sit under the bar. Neither throws.
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { Children, useState, type ReactNode } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView, type Metrics } from 'react-native-safe-area-context';

import { theme, TopSafeArea, useSaysTabBarReach } from '@/shared/ui';

import { ShellScreen } from './ShellScreen';

/** A notched phone: both insets exist, so taking the wrong one is visible. */
const METRICS: Metrics = {
  frame: { x: 0, y: 0, width: 390, height: 844 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

/**
 * The reach on this phone while the bar is drawn (10.2) — worked out from the theme, never read back
 * from the bar: the dock's lift, which is the bottom inset where that is larger than 12, and its 54.
 */
const REACH = Math.max(theme.size.tabBar.lift, METRICS.insets.bottom) + theme.size.tabBar.height;

/** The tab shell around the screen: its bar drawn, or standing down as in the chat. */
function Shell({ drawn, children }: { readonly drawn: boolean; readonly children: ReactNode }) {
  useSaysTabBarReach(drawn);
  return <>{children}</>;
}

function renderScreen(action?: ReactNode, bar: 'drawn' | 'standing down' | 'none' = 'none') {
  const page = (
    <ShellScreen title="Find a game" action={action}>
      <Text>the page</Text>
    </ShellScreen>
  );
  return render(
    <SafeAreaProvider initialMetrics={METRICS}>
      {bar === 'none' ? page : <Shell drawn={bar === 'drawn'}>{page}</Shell>}
    </SafeAreaProvider>,
  );
}

/** The screen's own frame — what `TopSafeArea` pads. */
const frame = () =>
  StyleSheet.flatten(screen.UNSAFE_getByType(TopSafeArea).findByType(View).props.style);

/** Where the page's content ends: the padding under its last row. */
const pageEnd = () => StyleSheet.flatten(scroller().props.contentContainerStyle).paddingBottom;

function scroller() {
  return screen.UNSAFE_getByType(ScrollView);
}

/** Header, scroller, and the pinned block when there is one. */
function siblings(): readonly ReactNode[] {
  return Children.toArray(screen.UNSAFE_getByType(TopSafeArea).props.children);
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
   * The game screen's plan lead is the first ([#414](https://github.com/Rakieta02/Rakieta/issues/414)):
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
  it('takes the top edge on its first frame and leaves the bottom to the tab bar', () => {
    renderScreen(undefined, 'drawn');

    // The top inset and no other: the bottom one is in the bar's reach, and `TabBar` has its own
    // suite proving it pads itself with it. Padded from the provider on the first render, never by
    // a native `SafeAreaView`, which measures itself a frame late — a tab root arrives with no
    // transition, so that frame was the whole tab press on Android: the header blinked (#529).
    expect(frame().paddingTop).toBe(METRICS.insets.top);
    expect(frame().paddingBottom).toBeUndefined();
    expect(screen.UNSAFE_queryAllByType(SafeAreaView)).toHaveLength(0);
  });
});

/**
 * **The screen draws to the bottom of the phone and ends at the bar's reach** (10.1, ADR-0210 §3):
 * the bar floats over its foot, so the page runs under it and ends 15 clear of it — today's gap above
 * the bar — and a screen with a CTA ends its layout at the reach instead, the CTA above the bar in
 * flow. Standing down, as in the chat, the reach is nothing and the page ends at its own 15.
 */
describe('where the screen ends', () => {
  it('runs the page under the bar, ending it with padding of the reach and 15', () => {
    renderScreen(undefined, 'drawn');

    expect(frame().paddingBottom).toBeUndefined();
    expect(pageEnd()).toBe(REACH + theme.space.lg);
  });

  it('ends the layout at the reach for a CTA, and the page at the CTA', () => {
    renderScreen(<Text>Save</Text>, 'drawn');

    expect(frame().paddingBottom).toBe(REACH);
    expect(pageEnd()).toBe(theme.space.lg);
    // In flow, under the page — a sibling, never inside the scroller or floating over it.
    expect(siblings()).toHaveLength(3);
    expect(within(scroller()).queryByText('Save')).toBeNull();
  });

  it.each([
    ['standing down, as in the chat', 'standing down'],
    ['absent, outside every shell', 'none'],
  ] as const)('ends the page at its own 15 with the bar %s', (_, bar) => {
    renderScreen(undefined, bar);

    expect(pageEnd()).toBe(theme.space.lg);
    expect(frame().paddingBottom).toBeUndefined();
  });

  it('moves with the bar: back to the reach when the bar is drawn again', () => {
    function Toggled() {
      const [drawn, setDrawn] = useState(false);
      return (
        <Shell drawn={drawn}>
          <Pressable accessibilityLabel="leave the chat" onPress={() => setDrawn(true)} />
          <ShellScreen title="Find a game">
            <Text>the page</Text>
          </ShellScreen>
        </Shell>
      );
    }
    render(
      <SafeAreaProvider initialMetrics={METRICS}>
        <Toggled />
      </SafeAreaProvider>,
    );
    expect(pageEnd()).toBe(theme.space.lg);

    fireEvent.press(screen.getByLabelText('leave the chat'));

    expect(pageEnd()).toBe(REACH + theme.space.lg);
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

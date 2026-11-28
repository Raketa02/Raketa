/**
 * **The tab's menu** (design-system 9.5, [#861](https://github.com/Rakieta02/Rakieta/issues/861); PRD
 * #859) — a picker hanging from the tab that opens it, drawn in the page's own tree over the page.
 * What it draws, what a press on it reports, and every way it closes but the page's own. Where it
 * stands is `tabMenuGeometry.test.ts`'s; the group page's router suites walk it on a real page.
 *
 * The navigator is real — `expo-router/testing-library` over a two-route stack — because leaving the
 * page is one of the things that closes it, and a blur is the navigator's to send.
 */

import { router, Stack } from 'expo-router';
import { act, fireEvent, renderRouter, screen, within } from 'expo-router/testing-library';
import { Pressable, StyleSheet, Text, type TextStyle } from 'react-native';
import { useState } from 'react';

import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';

import { ReducedMotionProvider } from './overlay';
import { TabMenu, type TabMenuLine } from './TabMenu';
import { theme } from './theme';

type Kind = 'competitive' | 'forFun';

const LINES: readonly TabMenuLine<Kind>[] = [
  { key: 'competitive', label: 'Competitive' },
  { key: 'forFun', label: 'For fun' },
];

const onPick = jest.fn();
const onClose = jest.fn();

/** What the page under test hands the menu — set before each render. */
let held: { readonly lines: readonly TabMenuLine<Kind>[]; readonly selected: Kind } = {
  lines: LINES,
  selected: 'competitive',
};

/** A page with a button that opens the menu; the menu's close is the page's, as a page holds it. */
function Page() {
  const [open, setOpen] = useState(false);
  // The page taking the menu away, as a page does when its tab goes.
  const [kept, setKept] = useState(true);
  return (
    <>
      <Pressable accessibilityRole="button" accessibilityLabel="Open" onPress={() => setOpen(true)}>
        <Text>the page</Text>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Take it away"
        onPress={() => setKept(false)}
      >
        <Text>another tab</Text>
      </Pressable>
      {kept ? (
        <TabMenu
          open={open}
          lines={held.lines}
          selected={held.selected}
          trigger={{ x: 252, y: 65, width: 114, height: 25 }}
          bar={{ x: 15, y: 62, width: 354, height: 31 }}
          align="end"
          onPick={onPick}
          onClose={() => {
            onClose();
            setOpen(false);
          }}
        />
      ) : null}
    </>
  );
}

function Elsewhere() {
  return <Text>elsewhere</Text>;
}

function renderPage({ reduced = false }: { readonly reduced?: boolean } = {}) {
  renderRouter(
    {
      _layout: () => (
        <ReducedMotionProvider value={reduced}>
          <Stack />
        </ReducedMotionProvider>
      ),
      index: Page,
      elsewhere: Elsewhere,
    },
    { initialUrl: '/' },
  );
}

function openMenu() {
  fireEvent.press(screen.getByRole('button', { name: 'Open' }));
  return screen.getByTestId('tab-menu');
}

const line = (name: string) => within(screen.getByTestId('tab-menu')).getByRole('button', { name });

beforeEach(() => {
  jest.useFakeTimers();
  onPick.mockReset();
  onClose.mockReset();
  held = { lines: LINES, selected: 'competitive' };
});

afterEach(() => {
  stopWatchingHardwareBack();
  jest.useRealTimers();
});

describe('what it draws', () => {
  it('draws nothing while shut', () => {
    renderPage();

    expect(screen.queryByTestId('tab-menu', { includeHiddenElements: true })).toBeNull();
  });

  it('lists its lines in order, each a button saying whether it is the one selected', () => {
    renderPage();
    const menu = openMenu();

    expect(
      within(menu)
        .getAllByRole('button')
        .map((one) => one.props.accessibilityLabel),
    ).toEqual(['Competitive', 'For fun']);
    expect(line('Competitive').props.accessibilityState).toEqual({ selected: true });
    expect(line('For fun').props.accessibilityState).toEqual({ selected: false });
  });

  /** A coralInk circle with the drawn tick, and the same space left empty on the other line. */
  it('ticks the selected line, and keeps the tick’s space on the other', () => {
    renderPage();
    openMenu();

    const tick = within(line('Competitive')).getByTestId('tab-menu-tick', {
      includeHiddenElements: true,
    });
    expect(StyleSheet.flatten(tick.props.style)).toMatchObject({
      width: theme.size.tabMenu.tick,
      height: theme.size.tabMenu.tick,
      backgroundColor: theme.color.coralInk,
    });
    expect(within(line('For fun')).queryByTestId('tab-menu-tick')).toBeNull();
    const space = within(line('For fun')).getByTestId('tab-menu-tick-space', {
      includeHiddenElements: true,
    });
    expect(StyleSheet.flatten(space.props.style)).toMatchObject({
      width: theme.size.tabMenu.tick,
      height: theme.size.tabMenu.tick,
    });
  });

  it('is a white card, every line at least the touch minimum tall', () => {
    renderPage();
    const menu = openMenu();

    expect(StyleSheet.flatten(menu.props.style)).toMatchObject({
      backgroundColor: theme.color.surface,
      borderRadius: theme.radius.tabMenu,
      ...theme.shadow.popover,
    });
    expect(StyleSheet.flatten(line('For fun').props.style)).toMatchObject({
      minHeight: theme.size.minTouch,
    });
  });

  it('draws a line’s count after its words, in muted mono', () => {
    held = {
      lines: [
        {
          key: 'competitive',
          label: 'Competitive',
          count: '5',
          accessibilityLabel: 'Competitive, 5',
        },
        { key: 'forFun', label: 'For fun', count: '1', accessibilityLabel: 'For fun, 1' },
      ],
      selected: 'competitive',
    };
    renderPage();
    openMenu();

    const count = within(line('Competitive, 5')).getByText('5', { includeHiddenElements: true });
    expect(StyleSheet.flatten(count.props.style as TextStyle)).toMatchObject({
      ...theme.num.tiny,
      color: theme.color.muted,
    });
  });

  /** A door, as the segment's (6.3): dimmed, never disabled, and its press reported. */
  it('dims a door line, never disables it, and reports its press', () => {
    held = {
      lines: [
        { key: 'competitive', label: 'Competitive' },
        { key: 'forFun', label: 'For fun', door: true },
      ],
      selected: 'competitive',
    };
    renderPage();
    openMenu();

    const door = line('For fun');
    expect(door.props.accessibilityState).toEqual({ selected: false });
    const words = within(door).getByText('For fun');
    expect(StyleSheet.flatten(words.props.style as TextStyle)).toMatchObject({
      color: theme.color.muted,
      opacity: theme.size.segDoorOpacity,
    });

    fireEvent.press(door);
    expect(onPick).toHaveBeenCalledWith('forFun');
  });
});

describe('a press on a line', () => {
  it('closes the menu, then reports the line', () => {
    renderPage();
    openMenu();

    fireEvent.press(line('For fun'));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onPick).toHaveBeenCalledWith('forFun');
    expect(onClose.mock.invocationCallOrder[0]).toBeLessThan(onPick.mock.invocationCallOrder[0]!);
  });

  it('reports the line already selected too — the page decides it is nothing', () => {
    renderPage();
    openMenu();

    fireEvent.press(line('Competitive'));

    expect(onPick).toHaveBeenCalledWith('competitive');
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe('what closes it', () => {
  it.each(['above', 'below', 'start', 'end'])(
    'a press on the page — the catcher %s the tab bar — and nothing else',
    (side) => {
      renderPage();
      openMenu();

      fireEvent.press(screen.getByTestId(`tab-menu-catcher-${side}`));

      expect(onClose).toHaveBeenCalledTimes(1);
      expect(onPick).not.toHaveBeenCalled();
    },
  );

  it('Android back, which it claims while open — and gives back once shut', () => {
    watchHardwareBack();
    renderPage();
    openMenu();

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });
    expect(claimed).toBe(true);
    expect(onClose).toHaveBeenCalledTimes(1);

    expect(pressHardwareBack()).toBe(false);
  });

  /** Taken away while open — its tab gone — the page that took it knows: no close is reported. */
  it('reports no close when its page takes it away while open', () => {
    watchHardwareBack();
    renderPage();
    openMenu();

    fireEvent.press(screen.getByRole('button', { name: 'Take it away' }));

    expect(screen.queryByTestId('tab-menu', { includeHiddenElements: true })).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
    // And Android back is the navigator's again.
    expect(pressHardwareBack()).toBe(false);
  });

  it('the page leaving view — a screen pushed over it', () => {
    renderPage();
    openMenu();

    act(() => router.push('/elsewhere'));

    expect(onClose).toHaveBeenCalled();
  });

  it('folds away out of reach: nothing in it is pressed or heard as it goes', () => {
    renderPage();
    openMenu();

    fireEvent.press(screen.getByTestId('tab-menu-catcher-below'));

    // Still drawn as it fades, and already out of a listener's and a finger's reach.
    const going = screen.getByTestId('tab-menu', { includeHiddenElements: true });
    expect(going.props.pointerEvents).toBe('none');
    expect(screen.queryByTestId('tab-menu')).toBeNull();
    expect(screen.queryByTestId('tab-menu-catcher-below')).toBeNull();

    act(() => jest.advanceTimersByTime(theme.motion.tabMenu));
    expect(screen.queryByTestId('tab-menu', { includeHiddenElements: true })).toBeNull();
  });

  it('goes at once under reduced motion', () => {
    renderPage({ reduced: true });
    openMenu();

    fireEvent.press(screen.getByTestId('tab-menu-catcher-below'));

    expect(screen.queryByTestId('tab-menu', { includeHiddenElements: true })).toBeNull();
  });
});

/**
 * **The tab bar's reach** — the room the bar takes at the bottom of the phone, now that it floats
 * over the screen rather than ending it (ADR-0210 §3, #881).
 *
 * The shell drawing a bar says how far it reaches, and everything placed against the bottom reads
 * it: a scroller's end, the deck's buttons, Post a game, a pinned button, the Undo toast. The toast
 * alone is placed by the **full** reach, from the insets, whether a bar is drawn or not — so in the
 * chat, where the bar stands down, it still clears the composer.
 *
 * Every number here is worked out from the theme, never read back from the module: the bar's height
 * at the default text size is its hairline, its two paddings, the tallest thing in a column and the
 * label (10.2). A reach that drifted from the bar it describes would leave a list's last row under it.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { useState, type ReactNode } from 'react';
import { Pressable, Text } from 'react-native';
import { SafeAreaProvider, type Metrics } from 'react-native-safe-area-context';

import {
  useFullTabBarReach,
  useRoomAtTheBottom,
  useSaysTabBarReach,
  useTabBarReach,
} from './tabBarReach';
import { theme } from './theme';

/** A notched phone: a bottom inset exists, so leaving it out is visible. */
const METRICS: Metrics = {
  frame: { x: 0, y: 0, width: 390, height: 844 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

const { space, size, type } = theme;

/** The player's bar: the hairline, the top padding, the ⚡Play disc, the gap, the label, the foot. */
const PLAYERS_BAR = 1 + space.xs + size.fab + space.xxs + type.tag.lineHeight + space.md;
/** The administrator's: the same, with the 16pt icon box for the disc it does not have. */
const ADMINISTRATORS_BAR = 1 + space.xs + size.tabIcon + space.xxs + type.tag.lineHeight + space.md;

const INSET = METRICS.insets.bottom;

/** What each reading says, as text a query can find. */
function Readings() {
  return (
    <>
      <Text testID="reach">{useTabBarReach()}</Text>
      <Text testID="full">{useFullTabBarReach()}</Text>
      <Text testID="room">{useRoomAtTheBottom()}</Text>
    </>
  );
}

const read = (id: 'reach' | 'full' | 'room') => Number(screen.getByTestId(id).props.children);

/** A shell drawing `bar` — and a press that stands it down and back, as the chat does. */
function Shell({
  bar,
  children,
}: {
  readonly bar: 'player' | 'administrator';
  readonly children: ReactNode;
}) {
  const [drawn, setDrawn] = useState(true);
  useSaysTabBarReach(bar, drawn);
  return (
    <>
      <Pressable accessibilityLabel="stand down" onPress={() => setDrawn((now) => !now)} />
      {children}
    </>
  );
}

/** The bar stands down, or comes back. */
const standDown = () => fireEvent.press(screen.getByLabelText('stand down'));

const onAPhone = (tree: ReactNode) =>
  render(<SafeAreaProvider initialMetrics={METRICS}>{tree}</SafeAreaProvider>);

describe('the reach a shell says', () => {
  it('is the player’s bar and the bottom inset under it while the bar is drawn', () => {
    onAPhone(
      <Shell bar="player">
        <Readings />
      </Shell>,
    );

    expect(read('reach')).toBe(PLAYERS_BAR + INSET);
  });

  it('is today’s bar height at the default text size — 64 — over no inset', () => {
    // The number the PRD and ADR-0210 compare the dock's 66 and 88 against.
    expect(PLAYERS_BAR).toBe(64);
  });

  it('is the administrator’s shorter bar in the administrator’s area', () => {
    onAPhone(
      <Shell bar="administrator">
        <Readings />
      </Shell>,
    );

    expect(read('reach')).toBe(ADMINISTRATORS_BAR + INSET);
  });

  it('is nothing while the bar stands down, and the bar’s again when it comes back', () => {
    onAPhone(
      <Shell bar="player">
        <Readings />
      </Shell>,
    );
    standDown();
    expect(read('reach')).toBe(0);

    standDown();
    expect(read('reach')).toBe(PLAYERS_BAR + INSET);
  });

  it('is nothing with no shell at all, and nothing again once a shell has gone', () => {
    onAPhone(<Readings />);
    expect(read('reach')).toBe(0);

    screen.unmount();
    onAPhone(
      <Shell bar="player">
        <Readings />
      </Shell>,
    );
    expect(read('reach')).toBe(PLAYERS_BAR + INSET);

    screen.unmount();
    onAPhone(<Readings />);
    expect(read('reach')).toBe(0);
  });

  /**
   * A screen mounted with its shell reads the reach **on its first render**, not one frame later:
   * the administrator's *New group* floats at the reach, and a first frame at the phone's foot would
   * be the button jumping as the area opens.
   */
  it('is read on a screen’s first render, as the shell opens', () => {
    const firstReadings: number[] = [];
    function FirstReading() {
      const reach = useTabBarReach();
      const [first] = useState(reach);
      firstReadings.push(first);
      return null;
    }

    onAPhone(
      <Shell bar="player">
        <FirstReading />
      </Shell>,
    );

    expect(firstReadings[0]).toBe(PLAYERS_BAR + INSET);
  });

  /**
   * **A profile switch replaces one shell with the other in one commit** (the root is a `Slot`), so
   * the new area's screens render while the old shell's reach still stands. They read the new
   * shell's all the same — the code review's catch: *New group* drawn 14pt high for a frame.
   */
  it('is read on a screen’s first render when one shell replaces another', () => {
    const firstReadings: number[] = [];
    function FirstReading() {
      const reach = useTabBarReach();
      const [first] = useState(reach);
      firstReadings.push(first);
      return null;
    }
    function Switcher() {
      const [bar, setBar] = useState<'player' | 'administrator'>('player');
      return (
        <>
          <Pressable accessibilityLabel="switch profile" onPress={() => setBar('administrator')} />
          <Shell key={bar} bar={bar}>
            <FirstReading />
          </Shell>
        </>
      );
    }
    onAPhone(<Switcher />);
    firstReadings.length = 0;

    fireEvent.press(screen.getByLabelText('switch profile'));

    expect(firstReadings[0]).toBe(ADMINISTRATORS_BAR + INSET);
  });
});

describe('the full reach — the toast’s', () => {
  it('is the player’s bar and the inset, whether a bar is drawn, stood down or absent', () => {
    onAPhone(
      <Shell bar="player">
        <Readings />
      </Shell>,
    );
    expect(read('full')).toBe(PLAYERS_BAR + INSET);

    standDown();
    expect(read('full')).toBe(PLAYERS_BAR + INSET);

    screen.unmount();
    onAPhone(<Readings />);
    expect(read('full')).toBe(PLAYERS_BAR + INSET);
  });

  it('is the player’s bar in the administrator’s area too, which it clears as well (9.2)', () => {
    onAPhone(
      <Shell bar="administrator">
        <Readings />
      </Shell>,
    );

    expect(read('full')).toBe(PLAYERS_BAR + INSET);
  });
});

describe('the room at the bottom — the Undo toast’s', () => {
  it('is the reach while a bar is drawn, and the bottom inset while it stands down', () => {
    onAPhone(
      <Shell bar="player">
        <Readings />
      </Shell>,
    );
    expect(read('room')).toBe(PLAYERS_BAR + INSET);

    standDown();
    expect(read('room')).toBe(INSET);
  });

  it('is the bottom inset outside every shell', () => {
    onAPhone(<Readings />);

    expect(read('room')).toBe(INSET);
  });
});

/**
 * **The tab bar's reach** — the room the bar takes at the bottom of the phone, now that it floats
 * over the screen rather than ending it (ADR-0210 §3, #881).
 *
 * The shell drawing a bar says how far it reaches, and everything placed against the bottom reads
 * it: a scroller's end, the deck's buttons, Post a game, a pinned button, the Undo toast. The toast
 * alone is placed by the **full** reach, from the insets, whether a bar is drawn or not — so in the
 * chat, where the bar stands down, it still clears the composer.
 *
 * Every number here is worked out from the theme, never read back from the module: the bar is the
 * dock, 54 tall and lifted the larger of 12 and the bottom inset (10.2, #883), and the
 * administrator's is the same dock with two columns. A reach that drifted from the dock it describes
 * would leave a list's last row under it.
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

/** A notched phone: a bottom inset exists, larger than the dock's least lift, so it leads. */
const METRICS: Metrics = {
  frame: { x: 0, y: 0, width: 390, height: 844 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

/** An Android phone on SDK 52, which draws no edge to edge: no bottom inset. */
const NO_INSET: Metrics = {
  frame: { x: 0, y: 0, width: 360, height: 800 },
  insets: { top: 24, left: 0, right: 0, bottom: 0 },
};

const { height: DOCK, lift: LEAST_LIFT } = theme.size.tabBar;

const INSET = METRICS.insets.bottom;

/** The dock's reach on the notched phone: it rests on the safe-area line, 54 tall. */
const REACH = Math.max(LEAST_LIFT, INSET) + DOCK;

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

/** A shell drawing its bar — and a press that stands it down and back, as the chat does. */
function Shell({
  startsDrawn = true,
  children,
}: {
  readonly startsDrawn?: boolean;
  readonly children: ReactNode;
}) {
  const [drawn, setDrawn] = useState(startsDrawn);
  useSaysTabBarReach(drawn);
  return (
    <>
      <Pressable accessibilityLabel="stand down" onPress={() => setDrawn((now) => !now)} />
      {children}
    </>
  );
}

/** The bar stands down, or comes back. */
const standDown = () => fireEvent.press(screen.getByLabelText('stand down'));

const onAPhone = (tree: ReactNode, metrics: Metrics = METRICS) =>
  render(<SafeAreaProvider initialMetrics={metrics}>{tree}</SafeAreaProvider>);

describe('the reach a shell says', () => {
  it('is the dock’s lift and its 54 while the bar is drawn — 88 on a notched phone', () => {
    onAPhone(
      <Shell>
        <Readings />
      </Shell>,
    );

    expect(read('reach')).toBe(REACH);
    expect(REACH).toBe(88);
  });

  it('is the least lift and the 54 on a phone with no inset — 66, the A32’s', () => {
    // The number the PRD and ADR-0210 compare against the old bar's 64.
    onAPhone(
      <Shell>
        <Readings />
      </Shell>,
      NO_INSET,
    );

    expect(read('reach')).toBe(LEAST_LIFT + DOCK);
    expect(read('reach')).toBe(66);
  });

  it('is nothing while the bar stands down, and the dock’s again when it comes back', () => {
    onAPhone(
      <Shell>
        <Readings />
      </Shell>,
    );
    standDown();
    expect(read('reach')).toBe(0);

    standDown();
    expect(read('reach')).toBe(REACH);
  });

  it('is nothing with no shell at all, and nothing again once a shell has gone', () => {
    onAPhone(<Readings />);
    expect(read('reach')).toBe(0);

    screen.unmount();
    onAPhone(
      <Shell>
        <Readings />
      </Shell>,
    );
    expect(read('reach')).toBe(REACH);

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
      <Shell>
        <FirstReading />
      </Shell>,
    );

    expect(firstReadings[0]).toBe(REACH);
  });

  /**
   * **A profile switch replaces one shell with the other in one commit** (the root is a `Slot`), so
   * the new area's screens render while the old shell's reach still stands. They read the new
   * shell's all the same — the code review's catch: *New group* drawn 14pt high for a frame, when the
   * two bars were two heights. The two shells now say one dock's reach, so the old one here is
   * standing down, and says nothing.
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
      const [area, setArea] = useState<'player' | 'administrator'>('player');
      return (
        <>
          <Pressable accessibilityLabel="switch profile" onPress={() => setArea('administrator')} />
          <Shell key={area} startsDrawn={area === 'administrator'}>
            <FirstReading />
          </Shell>
        </>
      );
    }
    onAPhone(<Switcher />);
    expect(firstReadings[0]).toBe(0);
    firstReadings.length = 0;

    fireEvent.press(screen.getByLabelText('switch profile'));

    expect(firstReadings[0]).toBe(REACH);
  });
});

describe('the full reach — the toast’s', () => {
  it('is the dock’s, from the inset, whether a bar is drawn, stood down or absent', () => {
    onAPhone(
      <Shell>
        <Readings />
      </Shell>,
    );
    expect(read('full')).toBe(REACH);

    standDown();
    expect(read('full')).toBe(REACH);

    screen.unmount();
    onAPhone(<Readings />);
    expect(read('full')).toBe(REACH);
  });

  it('is the least lift and the 54 on a phone with no inset', () => {
    onAPhone(<Readings />, NO_INSET);

    expect(read('full')).toBe(LEAST_LIFT + DOCK);
  });
});

describe('the room at the bottom — the Undo toast’s', () => {
  it('is the reach while a bar is drawn, and the bottom inset while it stands down', () => {
    onAPhone(
      <Shell>
        <Readings />
      </Shell>,
    );
    expect(read('room')).toBe(REACH);

    standDown();
    expect(read('room')).toBe(INSET);
  });

  it('is the bottom inset outside every shell', () => {
    onAPhone(<Readings />);

    expect(read('room')).toBe(INSET);
  });
});

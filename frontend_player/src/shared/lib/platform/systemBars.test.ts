/**
 * **The system bars port's own decisions** (#857): what each adapter paints, and that a restore gives
 * back exactly the look the bars had.
 *
 * The far sides are stood in for. The navigation bar is a window this file holds, behind a stand-in
 * for `expo-navigation-bar`: a read answers what the window shows and a write changes it, as the
 * module does on Android. The status bar is React Native's own stack, observed through its public
 * push and pop. So what is proved is what the port decides, never what the phone draws: that needs
 * a look on the A32 and an iPhone.
 *
 * Jest loads the iPhone adapter as `./systemBars`, so the Android one is loaded by its full name.
 * Each case takes a fresh one, because the device's adapter keeps its state for the process.
 */

import { StatusBar } from 'react-native';

import { theme } from '@/shared/ui/theme';

import { androidSystemBars } from './systemBars.android';
import { deviceSystemBars as iphoneSystemBars } from './systemBars';

/** The phone's window, as the stand-in for `expo-navigation-bar` reads and writes it. */
interface NavigationWindow {
  colour: string;
  buttons: 'light' | 'dark';
  /** Whether a read is answered. `false` is a phone whose module refuses one. */
  readable: boolean;
  /** Every write the window received, oldest first. */
  readonly writes: string[];
}

jest.mock('expo-navigation-bar', () => {
  const shown = {
    colour: '',
    buttons: 'dark',
    readable: true,
    writes: [] as string[],
  };
  const read = <T>(value: () => T) =>
    shown.readable ? Promise.resolve(value()) : Promise.reject(new Error('Unavailable'));
  return {
    __window: shown,
    getBackgroundColorAsync: () => read(() => shown.colour),
    getButtonStyleAsync: () => read(() => shown.buttons),
    setBackgroundColorAsync: (colour: string) => {
      shown.colour = colour;
      shown.writes.push(`colour ${colour}`);
      return Promise.resolve();
    },
    setButtonStyleAsync: (buttons: 'light' | 'dark') => {
      shown.buttons = buttons;
      shown.writes.push(`buttons ${buttons}`);
      return Promise.resolve();
    },
  };
});

const navigation = jest.requireMock<{ __window: NavigationWindow }>('expo-navigation-bar').__window;

const GROUND = theme.color.splashGroundEdge;

/**
 * The navigation bar the system draws before anything paints it: a light system theme's, white with
 * dark buttons, as the module reads it back. Any colour that is not the ground would do; this one
 * comes from the theme because no suite spells a colour.
 */
const SYSTEM_COLOUR = theme.color.paper;

/** Lets every change the port has asked for land. */
async function settled() {
  await new Promise((done) => setImmediate(done));
}

let push: jest.SpyInstance;
let pop: jest.SpyInstance;

beforeEach(() => {
  navigation.colour = SYSTEM_COLOUR;
  navigation.buttons = 'dark';
  navigation.readable = true;
  navigation.writes.length = 0;
  push = jest.spyOn(StatusBar, 'pushStackEntry');
  pop = jest.spyOn(StatusBar, 'popStackEntry');
});

afterEach(() => {
  // Whatever a case painted on React Native's stack is lifted again by its own restore, so no case
  // leaves an entry behind; the spies go back to being the stack's own functions.
  push.mockRestore();
  pop.mockRestore();
});

describe('on Android', () => {
  it('paints the status bar light over the ground, and a restore lifts that very entry', () => {
    const bars = androidSystemBars();

    bars.paint(GROUND);
    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith({ barStyle: 'light-content', backgroundColor: GROUND });

    bars.restore();
    expect(pop).toHaveBeenCalledTimes(1);
    expect(pop).toHaveBeenCalledWith(push.mock.results[0]?.value);
  });

  it('never changes how the status bar is laid out: the paint leaves its translucency alone', async () => {
    const bars = androidSystemBars();
    bars.paint(GROUND);

    expect(push.mock.calls[0]?.[0]).not.toHaveProperty('translucent');

    bars.restore();
    await settled();
  });

  it('paints the navigation bar the ground with light buttons, and restores the system’s own', async () => {
    const bars = androidSystemBars();

    bars.paint(GROUND);
    await settled();
    expect(navigation.colour).toBe(GROUND);
    expect(navigation.buttons).toBe('light');

    bars.restore();
    await settled();
    expect(navigation.colour).toBe(SYSTEM_COLOUR);
    expect(navigation.buttons).toBe('dark');
  });

  it('restores what the system drew before any paint, however quickly the acts follow each other', async () => {
    const bars = androidSystemBars();

    bars.paint(GROUND);
    bars.restore();
    bars.paint(GROUND);
    bars.restore();
    await settled();

    expect(navigation.colour).toBe(SYSTEM_COLOUR);
    expect(navigation.buttons).toBe('dark');
    // In the order they were asked for, each write landing after the one before.
    expect(navigation.writes).toEqual([
      `colour ${GROUND}`,
      'buttons light',
      `colour ${SYSTEM_COLOUR}`,
      'buttons dark',
      `colour ${GROUND}`,
      'buttons light',
      `colour ${SYSTEM_COLOUR}`,
      'buttons dark',
    ]);
  });

  it('reads the system’s look after a restore has landed, never the night it is undoing', async () => {
    const bars = androidSystemBars();

    bars.paint(GROUND);
    await settled();
    // Painted again while the restore's writes are still on their way: the bar still shows night.
    bars.restore();
    bars.paint(GROUND);
    bars.restore();
    await settled();

    expect(navigation.colour).toBe(SYSTEM_COLOUR);
    expect(navigation.buttons).toBe('dark');
  });

  it('gives back the look the bar had at this paint, which a new window may have changed', async () => {
    const bars = androidSystemBars();
    bars.paint(GROUND);
    bars.restore();
    await settled();

    // Android recreated the window under the same JavaScript, and its bar is the dark theme's now.
    navigation.colour = theme.color.ink;
    navigation.buttons = 'light';
    bars.paint(GROUND);
    await settled();
    expect(navigation.colour).toBe(GROUND);

    bars.restore();
    await settled();
    expect(navigation.colour).toBe(theme.color.ink);
    expect(navigation.buttons).toBe('light');
  });

  it('a second paint before a restore changes nothing, and nor does a restore with nothing painted', async () => {
    const bars = androidSystemBars();

    bars.restore();
    bars.paint(GROUND);
    bars.paint(GROUND);
    await settled();

    expect(push).toHaveBeenCalledTimes(1);
    expect(pop).not.toHaveBeenCalled();
    expect(navigation.writes).toEqual([`colour ${GROUND}`, 'buttons light']);

    bars.restore();
    bars.restore();
    await settled();
    expect(pop).toHaveBeenCalledTimes(1);
    expect(navigation.colour).toBe(SYSTEM_COLOUR);
  });

  it('leaves the navigation bar alone when the phone will not say what it shows', async () => {
    navigation.readable = false;
    const bars = androidSystemBars();

    bars.paint(GROUND);
    await settled();
    bars.restore();
    await settled();

    // Nothing it could not give back: the status bar is painted and lifted all the same.
    expect(navigation.writes).toEqual([]);
    expect(push).toHaveBeenCalledTimes(1);
    expect(pop).toHaveBeenCalledTimes(1);
  });
});

describe('on an iPhone', () => {
  it('shows light content while painted, and a restore lifts that very entry', () => {
    iphoneSystemBars.paint(GROUND);
    iphoneSystemBars.paint(GROUND);
    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith({ barStyle: 'light-content' });

    iphoneSystemBars.restore();
    iphoneSystemBars.restore();
    expect(pop).toHaveBeenCalledTimes(1);
    expect(pop).toHaveBeenCalledWith(push.mock.results[0]?.value);
  });

  it('has no navigation bar to paint', () => {
    iphoneSystemBars.paint(GROUND);
    iphoneSystemBars.restore();

    expect(navigation.writes).toEqual([]);
  });
});

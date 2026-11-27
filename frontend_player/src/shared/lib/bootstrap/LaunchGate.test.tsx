/**
 * **The launch gate, on a fake clock** — the drawn splash, the launch window's release, the
 * fade and the hold ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §1–§3).
 *
 * The gate is handed a fake sequence (a deferred promise the test resolves), a fake launch window
 * that counts its releases, the system bars' fake (#857), and reduced motion through the provider's
 * `value`, never the OS. Every assertion is something a player or the next screen could observe:
 * whether the splash is drawn, how much of it shows, whether the app is underneath, whether a press
 * lands, what the phone's bars show.
 *
 * **The times are the brief's, spelled here** rather than read from the gate's own constants: a
 * clock that drifted from 2.6 s should turn this red, not move it along.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import type { ReactNode } from 'react';
import {
  Dimensions,
  Pressable,
  StyleSheet,
  Text,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
import { getAnimatedStyle, ReducedMotionConfig, ReduceMotion } from 'react-native-reanimated';
import { SafeAreaProvider, type Rect } from 'react-native-safe-area-context';

import type { SystemBarsPort } from '@/shared/lib/platform';
import { ReducedMotionProvider, theme, useCoveredBySplash } from '@/shared/ui';
import { fakeSystemBars } from '@/test-support/platform';

import { splashGeometry, WORDMARK_FACE } from './domain/splashGeometry';
import type { SplashFace } from './fonts';
import { LaunchGate } from './LaunchGate';
import type { LaunchWindow } from './launchWindow';
import { useSplashHold } from './splashHold';

/** The brief's clock (ADR-0209 §3), in milliseconds from the splash's first layout. */
const FADE_AT = 2600;
const FADE_AT_REDUCED = 900;
const FADE = 500;
const GLOW_IN = 390;
/** The lockup's short fade-in under reduced motion, where nothing flies (#855, #856). */
const LOCKUP_IN = 150;
/** The longest the motion waits for its face, from the splash's first layout. */
const FACE_WAIT = 600;

/** A few frames of a 60 Hz screen: long enough for an animation started on a tick to show. */
const A_FEW_FRAMES = 50;

/**
 * The splash says nothing to a screen reader, and the tree under it is hidden from one until it is
 * gone, so every query that reaches either while it is up includes hidden elements.
 */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

const SPLASH = 'drawn-splash';
const GLOW = 'splash-glow';
const GROUND = 'splash-ground';
const LOCKUP = 'splash-lockup';
const DOT = 'splash-dot';
const LETTERS = 'splash-letters';
const APP = 'app-root';

/** The phone's full screen, as React Native's own test setup reports it. */
const SCREEN = Dimensions.get('screen');

/** A view that covers the whole screen, as an iPhone's does. */
const WHOLE_SCREEN: Rect = { x: 0, y: 0, width: SCREEN.width, height: SCREEN.height };

const LAYOUT = { nativeEvent: { layout: { x: 0, y: 0, width: 390, height: 844 } } };

function deferred() {
  let resolve!: () => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

/** The launch window's port, counting how often it was let go. */
function fakeLaunchWindow(): LaunchWindow & { readonly released: number } {
  let released = 0;
  return {
    release: () => {
      released += 1;
    },
    get released() {
      return released;
    },
  };
}

const pressed = jest.fn();

/** The first screen: one control, so a press either lands or it does not. */
function TheApp() {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel="Open" onPress={pressed}>
      <Text>the app</Text>
    </Pressable>
  );
}

/** A first screen that draws nothing until it has an answer, and says so. */
function BlankUntil({ answered }: { readonly answered: boolean }) {
  useSplashHold(!answered);
  return answered ? <Text>the answer</Text> : null;
}

interface Launch {
  readonly run?: () => Promise<void>;
  readonly reduced?: boolean;
  readonly app?: ReactNode;
  /**
   * Where the app's view stands on the screen, as the root's safe-area provider reports it —
   * `null` for a tree with no provider above the gate at all.
   */
  readonly view?: Rect | null;
  /** The wordmark's face. The device's — already loaded, as jest's font registry says — if unsaid. */
  readonly face?: SplashFace;
}

/** A face the phone does not have yet: it loads when the test says so, or fails to. */
function faceStillLoading(): SplashFace & {
  readonly arrive: () => Promise<void>;
  readonly fail: () => Promise<void>;
} {
  const loading = deferred();
  return {
    loaded: () => false,
    load: () => loading.promise,
    arrive: () => act(async () => loading.resolve()),
    fail: () => act(async () => loading.reject(new Error('the face could not be read'))),
  };
}

/** Says, in words, whether the splash still covers the tree it is drawn in. */
function Covered() {
  return <Text>{useCoveredBySplash() ? 'covered' : 'uncovered'}</Text>;
}

/**
 * The tree the root renders. **Under reduced motion the OS has said so to Reanimated too**, which
 * every animation consults unless told otherwise — so a fade that took the OS's word would jump
 * to its end on a phone, and this is where it would show. The safe-area provider is the root's,
 * above the gate, with the view's place on the screen as its frame.
 */
function tree(
  { run, reduced = false, app = <TheApp />, view = WHOLE_SCREEN, face }: Launch,
  launchWindow: LaunchWindow,
  systemBars: SystemBarsPort,
) {
  const gate = (
    <ReducedMotionProvider value={reduced}>
      {reduced ? <ReducedMotionConfig mode={ReduceMotion.Always} /> : null}
      <LaunchGate
        run={run ?? (() => Promise.resolve())}
        launchWindow={launchWindow}
        systemBars={systemBars}
        splashFace={face}
      >
        {app}
      </LaunchGate>
    </ReducedMotionProvider>
  );
  if (view === null) return gate;
  return (
    <SafeAreaProvider
      initialMetrics={{ frame: view, insets: { top: 0, left: 0, right: 0, bottom: 0 } }}
    >
      {gate}
    </SafeAreaProvider>
  );
}

/** The process starts: the root renders the gate, and nothing has laid out yet. */
function launch(options: Launch = {}) {
  const launchWindow = fakeLaunchWindow();
  const systemBars = fakeSystemBars();
  const view = render(tree(options, launchWindow, systemBars));
  return {
    launchWindow,
    systemBars,
    unmount: view.unmount,
    /** The same gate, re-rendered with a different tree or setting — never remounted. */
    rerender: (next: Launch) =>
      view.rerender(tree({ ...options, ...next }, launchWindow, systemBars)),
  };
}

/** When the splash first laid out: the moment every time in this suite is measured from. */
let splashLaidOutAt = 0;

function layOutTheSplash() {
  splashLaidOutAt = Date.now();
  fireEvent(screen.getByTestId(SPLASH, HIDDEN_TOO), 'layout', LAYOUT);
}

/**
 * Whether the first screen lays out once it is mounted — it mounts underneath the splash only once
 * the motion is still, so a launch says *when it is there, lay it out* rather than doing it now.
 */
let appLaysOut = false;
let appLaidOut: ReturnType<typeof screen.getByTestId> | null = null;

function layOutTheApp() {
  appLaysOut = true;
  layOutTheAppIfMounted();
}

function layOutTheAppIfMounted() {
  if (!appLaysOut) return;
  const app = screen.queryByTestId(APP, HIDDEN_TOO);
  if (app === null || app === appLaidOut) return;
  appLaidOut = app;
  fireEvent(app, 'layout', LAYOUT);
}

/** When the motion is still, and the tree may mount: 1.78 s after the splash's first layout. */
const STILL = 1780;

/**
 * Moves the clock to `ms` after the splash's first layout, **a frame at a time** — as a phone's
 * clock moves, so what one frame sets off runs in the next rather than when a long advance ends —
 * laying out a first screen the moment it has mounted.
 */
function clockTo(ms: number) {
  const target = splashLaidOutAt + ms;
  while (Date.now() < target) {
    const step = Math.min(16, target - Date.now());
    act(() => jest.advanceTimersByTime(step));
    layOutTheAppIfMounted();
  }
}

/** Lets a settled sequence's promise land. */
async function settle() {
  await act(async () => {});
}

/**
 * How much of a layer shows. Read through Reanimated's own test reader: an animated style is applied
 * frame by frame outside React's render, so the host's `style` prop never sees it move.
 */
function opacityOf(testID: string): number {
  const style = getAnimatedStyle(screen.getByTestId(testID, HIDDEN_TOO)) as ViewStyle;
  return Number(style.opacity ?? 1);
}

function splashIsUp(): boolean {
  return screen.queryByTestId(SPLASH, HIDDEN_TOO) !== null;
}

/** The ordinary launch: the splash lays out, the sequence lands, the first screen lays out. */
async function launchReady(options: Launch = {}) {
  const launched = launch(options);
  layOutTheSplash();
  await settle();
  layOutTheApp();
  return launched;
}

beforeEach(() => {
  jest.useFakeTimers();
  pressed.mockClear();
  appLaysOut = false;
  appLaidOut = null;
});

afterEach(() => {
  jest.useRealTimers();
});

describe('the launch', () => {
  it('draws the splash on its first render, before the sequence has resolved', () => {
    const startup = deferred();

    launch({ run: () => startup.promise });

    expect(splashIsUp()).toBe(true);
    expect(opacityOf(SPLASH)).toBe(1);
    expect(screen.queryByText('the app')).toBeNull();
  });

  it('lets the launch window go on the splash’s first layout — not before, and only once', () => {
    const startup = deferred();
    const { launchWindow } = launch({ run: () => startup.promise });

    expect(launchWindow.released).toBe(0);

    layOutTheSplash();
    expect(launchWindow.released).toBe(1);

    layOutTheSplash();
    expect(launchWindow.released).toBe(1);
  });

  it('no longer lets the launch window go on the tree’s layout', async () => {
    const { launchWindow } = launch();
    await settle();

    layOutTheApp();

    expect(launchWindow.released).toBe(0);
  });

  it('runs the sequence once, however often the root re-renders it', async () => {
    let runs = 0;
    // A fresh function each time, as a root that forgot to memoise it would hand over.
    const aFreshRun = () => () => {
      runs += 1;
      return Promise.resolve();
    };
    const { rerender } = launch({ run: aFreshRun() });
    await settle();

    rerender({ run: aFreshRun() });
    rerender({ run: aFreshRun() });
    await settle();

    expect(runs).toBe(1);
  });

  it('mounts the tree underneath the splash once the sequence resolves and the motion is still', async () => {
    const startup = deferred();
    launch({ run: () => startup.promise });
    layOutTheSplash();

    expect(screen.queryByText('the app', HIDDEN_TOO)).toBeNull();

    clockTo(STILL);
    expect(screen.queryByText('the app', HIDDEN_TOO)).toBeNull();

    await act(async () => startup.resolve());

    expect(screen.getByText('the app', HIDDEN_TOO)).toBeTruthy();
    expect(splashIsUp()).toBe(true);
    expect(opacityOf(SPLASH)).toBe(1);
  });

  /**
   * A first screen is hundreds of views, and the phone creating them on the thread that moves the
   * ball froze it mid-bounce — kept out of layout they are created all the same. So however early
   * the sequence resolves, the tree mounts once the motion is still.
   */
  it('mounts no tree while the ball is in the air, however early the sequence resolved', async () => {
    await launchReady();
    expect(screen.queryByText('the app', HIDDEN_TOO)).toBeNull();

    clockTo(STILL - 1);
    expect(screen.queryByText('the app', HIDDEN_TOO)).toBeNull();

    clockTo(STILL);
    expect(screen.getByText('the app', HIDDEN_TOO)).toBeTruthy();
  });

  it('mounts it from the first layout under reduced motion, where nothing flies', async () => {
    await launchReady({ reduced: true });

    expect(screen.getByText('the app', HIDDEN_TOO)).toBeTruthy();
  });

  it('keeps the tree from a screen reader until the splash is gone', async () => {
    await launchReady();
    clockTo(STILL);

    expect(screen.queryByText('the app')).toBeNull();
    expect(screen.getByText('the app', HIDDEN_TOO)).toBeTruthy();

    clockTo(FADE_AT + FADE);
    expect(screen.getByText('the app')).toBeTruthy();
  });

  /**
   * What the tree reads to know it is covered — for what the splash cannot cover by being drawn
   * last: iOS's modal stage, a native window above the whole app, and a toast's hold.
   */
  it('tells the tree it is covered until the splash is gone, not just until the fade begins', async () => {
    await launchReady({ app: <Covered /> });
    clockTo(STILL);

    expect(screen.getByText('covered', HIDDEN_TOO)).toBeTruthy();

    clockTo(FADE_AT + FADE - 1);
    expect(screen.getByText('covered', HIDDEN_TOO)).toBeTruthy();

    clockTo(FADE_AT + FADE);
    expect(screen.getByText('uncovered')).toBeTruthy();
  });

  it('comes on with its glow over the first 0.39 s', async () => {
    await launchReady();

    expect(opacityOf(GLOW)).toBe(0);

    clockTo(GLOW_IN / 2);
    expect(opacityOf(GLOW)).toBeGreaterThan(0);
    expect(opacityOf(GLOW)).toBeLessThan(1);

    clockTo(GLOW_IN + A_FEW_FRAMES);
    expect(opacityOf(GLOW)).toBe(1);
  });
});

describe('the fade', () => {
  it('starts at 2.6 s when the first screen is ready, and the splash is gone 0.5 s later', async () => {
    await launchReady();

    clockTo(FADE_AT - 1);
    expect(opacityOf(SPLASH)).toBe(1);

    clockTo(FADE_AT + A_FEW_FRAMES);
    expect(opacityOf(SPLASH)).toBeLessThan(1);

    clockTo(FADE_AT + FADE - 1);
    expect(splashIsUp()).toBe(true);

    clockTo(FADE_AT + FADE);
    expect(splashIsUp()).toBe(false);
    expect(screen.getByText('the app')).toBeTruthy();
  });

  it('counts its 2.6 s from the splash’s first layout, not from the mount', async () => {
    launch();
    await settle();
    act(() => jest.advanceTimersByTime(300));
    layOutTheSplash();
    layOutTheApp();

    clockTo(FADE_AT + FADE - 1);
    expect(splashIsUp()).toBe(true);

    clockTo(FADE_AT + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('holds the still splash while the sequence is late, and fades as soon as it lands', async () => {
    const startup = deferred();
    launch({ run: () => startup.promise });
    layOutTheSplash();

    clockTo(4000);
    expect(splashIsUp()).toBe(true);
    expect(opacityOf(SPLASH)).toBe(1);

    await act(async () => startup.resolve());
    layOutTheApp();

    clockTo(4000 + A_FEW_FRAMES);
    expect(opacityOf(SPLASH)).toBeLessThan(1);

    clockTo(4000 + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('holds while the first screen has not laid out', async () => {
    launch();
    layOutTheSplash();
    await settle();

    clockTo(FADE_AT + FADE + 1000);
    expect(splashIsUp()).toBe(true);
    expect(opacityOf(SPLASH)).toBe(1);

    layOutTheApp();
    clockTo(FADE_AT + FADE + 1000 + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('holds while a screen underneath says it is blank, and fades once it answers', async () => {
    const { rerender } = await launchReady({ app: <BlankUntil answered={false} /> });

    clockTo(5000);
    expect(splashIsUp()).toBe(true);
    expect(opacityOf(SPLASH)).toBe(1);

    rerender({ app: <BlankUntil answered /> });

    clockTo(5000 + A_FEW_FRAMES);
    expect(opacityOf(SPLASH)).toBeLessThan(1);
    expect(screen.getByText('the answer', HIDDEN_TOO)).toBeTruthy();

    clockTo(5000 + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('is not held by a screen that answered before 2.6 s', async () => {
    const { rerender } = await launchReady({ app: <BlankUntil answered={false} /> });

    clockTo(1000);
    rerender({ app: <BlankUntil answered /> });

    clockTo(FADE_AT + FADE - 1);
    expect(splashIsUp()).toBe(true);
    clockTo(FADE_AT + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('is never stopped once it has begun, whatever the screen underneath does', async () => {
    const { rerender } = await launchReady({ app: <BlankUntil answered /> });

    clockTo(FADE_AT + 100);
    rerender({ app: <BlankUntil answered={false} /> });

    clockTo(FADE_AT + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('swallows every touch until the splash is gone, not just until the fade begins', async () => {
    await launchReady();
    clockTo(STILL);

    // By its words while it is covered: a control under a hidden tree is no role a query can name.
    fireEvent.press(screen.getByText('the app', HIDDEN_TOO));
    clockTo(FADE_AT + FADE - 1);
    fireEvent.press(screen.getByText('the app', HIDDEN_TOO));
    expect(pressed).not.toHaveBeenCalled();

    clockTo(FADE_AT + FADE);
    fireEvent.press(screen.getByRole('button', { name: 'Open' }));
    expect(pressed).toHaveBeenCalledTimes(1);
  });

  it('reveals a failed launch with the same fade, the failure drawn underneath', async () => {
    launch({
      run: () =>
        Promise.reject(new Error('Invalid app configuration — EXPO_PUBLIC_API_URL: Required')),
    });
    layOutTheSplash();
    await settle();
    clockTo(STILL);

    expect(screen.getByText('Raketa could not start', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText(/EXPO_PUBLIC_API_URL/, HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByText('the app', HIDDEN_TOO)).toBeNull();
    expect(splashIsUp()).toBe(true);

    layOutTheApp();

    clockTo(FADE_AT + FADE - 1);
    expect(splashIsUp()).toBe(true);

    clockTo(FADE_AT + FADE);
    expect(splashIsUp()).toBe(false);
    expect(screen.getByText('Raketa could not start')).toBeTruthy();
  });

  it('plays once: nothing the tree does afterwards brings it back', async () => {
    const { rerender } = await launchReady();

    clockTo(FADE_AT + FADE);
    expect(splashIsUp()).toBe(false);

    rerender({ app: <BlankUntil answered={false} /> });
    rerender({ app: <TheApp /> });
    clockTo(FADE_AT * 3);

    expect(splashIsUp()).toBe(false);
  });
});

/**
 * **While the splash is up, the phone's bars belong to it** (#857): painted the field's edge with
 * light icons, so it reads edge to edge, and given back as the fade starts — under the fading
 * splash, not after it has gone. What each phone does with a paint is the port's; this suite holds
 * the gate to *when*.
 */
describe('the system bars', () => {
  const EDGE = theme.color.splashGroundEdge;

  it('are painted the splash’s edge as it starts, before its first layout', () => {
    const startup = deferred();
    const { systemBars, launchWindow } = launch({ run: () => startup.promise });

    expect(launchWindow.released).toBe(0);
    expect(systemBars.painted).toBe(EDGE);
    expect(systemBars.changes).toEqual(['painted']);
  });

  it('stay painted until the fade starts at 2.6 s, and are restored as it starts', async () => {
    const { systemBars } = await launchReady();

    clockTo(FADE_AT - 1);
    expect(systemBars.painted).toBe(EDGE);

    clockTo(FADE_AT);
    expect(systemBars.painted).toBeNull();
    expect(systemBars.changes).toEqual(['painted', 'restored']);
    // As the fade starts: the splash is still up, fading over the app.
    expect(splashIsUp()).toBe(true);
  });

  it('are restored as the fade starts at 0.9 s under reduced motion', async () => {
    const { systemBars } = await launchReady({ reduced: true });

    clockTo(FADE_AT_REDUCED - 1);
    expect(systemBars.painted).toBe(EDGE);

    clockTo(FADE_AT_REDUCED);
    expect(systemBars.painted).toBeNull();
    expect(splashIsUp()).toBe(true);
  });

  it('stay painted while the still lockup holds, and are restored when the fade starts', async () => {
    const startup = deferred();
    const { systemBars } = launch({ run: () => startup.promise });
    layOutTheSplash();

    clockTo(4000);
    expect(systemBars.painted).toBe(EDGE);

    await act(async () => startup.resolve());
    expect(systemBars.painted).toBe(EDGE);

    layOutTheApp();
    expect(systemBars.painted).toBeNull();
  });

  it('are restored when a failed launch is revealed, as for any first screen', async () => {
    const { systemBars } = launch({ run: () => Promise.reject(new Error('Invalid config')) });
    layOutTheSplash();
    await settle();
    layOutTheApp();

    clockTo(FADE_AT - 1);
    expect(systemBars.painted).toBe(EDGE);

    clockTo(FADE_AT);
    expect(systemBars.painted).toBeNull();
  });

  it('are restored by a gate that goes before its fade, leaving them as it found them', async () => {
    const { systemBars, unmount } = await launchReady();

    clockTo(1000);
    unmount();

    expect(systemBars.painted).toBeNull();
    expect(systemBars.changes).toEqual(['painted', 'restored']);
  });

  it('are painted once and restored once, whatever the root and the tree do afterwards', async () => {
    const { systemBars, rerender } = await launchReady();

    rerender({ app: <TheApp /> });
    clockTo(FADE_AT + FADE);
    rerender({ app: <BlankUntil answered={false} /> });
    rerender({ reduced: true });
    clockTo(FADE_AT * 3);

    expect(systemBars.changes).toEqual(['painted', 'restored']);
  });
});

describe('under reduced motion', () => {
  it('fades at 0.9 s — a fade, not a cut — and is gone at 1.4 s', async () => {
    await launchReady({ reduced: true });

    clockTo(FADE_AT_REDUCED - 1);
    expect(opacityOf(SPLASH)).toBe(1);

    clockTo(FADE_AT_REDUCED + A_FEW_FRAMES);
    expect(opacityOf(SPLASH)).toBeLessThan(1);
    expect(opacityOf(SPLASH)).toBeGreaterThan(0);

    clockTo(FADE_AT_REDUCED + FADE / 2);
    expect(opacityOf(SPLASH)).toBeGreaterThan(0.3);
    expect(opacityOf(SPLASH)).toBeLessThan(0.7);

    clockTo(FADE_AT_REDUCED + FADE - 1);
    expect(splashIsUp()).toBe(true);

    clockTo(FADE_AT_REDUCED + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('keeps the same hold', async () => {
    const startup = deferred();
    launch({ run: () => startup.promise, reduced: true });
    layOutTheSplash();

    clockTo(3000);
    expect(splashIsUp()).toBe(true);
    expect(opacityOf(SPLASH)).toBe(1);

    await act(async () => startup.resolve());
    layOutTheApp();

    clockTo(3000 + FADE);
    expect(splashIsUp()).toBe(false);
  });

  it('draws the glow from the start', async () => {
    await launchReady({ reduced: true });

    expect(opacityOf(GLOW)).toBe(1);
  });

  it('is decided once, before the first frame, and never switched mid-play', async () => {
    const calm = await launchReady({ reduced: false });

    clockTo(500);
    calm.rerender({ reduced: true });

    clockTo(FADE_AT_REDUCED + FADE);
    expect(splashIsUp()).toBe(true);

    // And the switch reaching Reanimated mid-play does not cut the fade it decided on either.
    clockTo(FADE_AT + A_FEW_FRAMES);
    expect(opacityOf(SPLASH)).toBeLessThan(1);
    expect(opacityOf(SPLASH)).toBeGreaterThan(0);

    clockTo(FADE_AT + FADE);
    expect(splashIsUp()).toBe(false);
  });
});

/**
 * **The lockup** (#855): *Rakieta* and its volt dot, centred together on the whole screen. Where each
 * letter stands is the geometry's, tested on its own (`domain/splashGeometry.test.ts`) and pinned to
 * the font (`splashWordmark.test.ts`); what this suite holds is that the splash draws what it says,
 * on the phone it finds — the screen, and where the app's view starts on it.
 */
describe('the lockup', () => {
  /** The letters the splash sets, in the order it draws them. */
  function letters() {
    return screen.queryAllByText(/^[A-Za-z]$/, HIDDEN_TOO);
  }

  function styleOf(testIDOrElement: string | ReturnType<typeof screen.getByTestId>): TextStyle {
    const element =
      typeof testIDOrElement === 'string'
        ? screen.getByTestId(testIDOrElement, HIDDEN_TOO)
        : testIDOrElement;
    return StyleSheet.flatten(element.props.style) as TextStyle;
  }

  /** Where the geometry puts everything, for this suite's screen and a view at `view`. */
  function placedFor(view: Rect) {
    return splashGeometry(
      { screen: SCREEN, view },
      {
        face: WORDMARK_FACE,
        fontSize: theme.type.splashWord.fontSize,
        letterSpacing: theme.type.splashWord.letterSpacing,
      },
    );
  }

  it('sets Rakieta as seven letters in pure white, the volt dot after them', async () => {
    await launchReady();

    expect(letters().map((letter) => letter.props.children)).toEqual([
      'R',
      'a',
      'k',
      'i',
      'e',
      't',
      'a',
    ]);
    letters().forEach((letter) => {
      expect(styleOf(letter).color).toBe(theme.color.surface);
      expect(styleOf(letter).fontFamily).toBe(theme.type.splashWord.fontFamily);
      expect(styleOf(letter).fontSize).toBe(42);
    });
    expect(styleOf(DOT).backgroundColor).toBe(theme.color.volt);
    expect(styleOf(DOT).width).toBe(12);
    expect(styleOf(DOT).height).toBe(12);
  });

  it('keeps its size whatever the phone’s text size, and tracks its letters itself', async () => {
    await launchReady();

    letters().forEach((letter) => {
      expect(letter.props.allowFontScaling).toBe(false);
      // The tracking is in where each letter stands; on a lone letter it would only move it.
      expect(styleOf(letter).letterSpacing).toBeUndefined();
      expect(styleOf(letter).lineHeight).toBeUndefined();
    });
  });

  it('is in place within 0,15 s of the splash’s first layout under reduced motion — a fade, not a cut', async () => {
    launch({ reduced: true });
    expect(opacityOf(LOCKUP)).toBe(0);

    layOutTheSplash();
    await settle();

    clockTo(LOCKUP_IN / 2);
    expect(opacityOf(LOCKUP)).toBeGreaterThan(0);
    expect(opacityOf(LOCKUP)).toBeLessThan(1);

    clockTo(LOCKUP_IN + A_FEW_FRAMES);
    expect(opacityOf(LOCKUP)).toBe(1);
  });

  it('stands each letter and the dot where the geometry puts them on this screen', async () => {
    await launchReady();
    const placed = placedFor(WHOLE_SCREEN);

    letters().forEach((letter, i) => {
      expect(styleOf(letter).left).toBe(placed.letters[i]!.x);
      expect(styleOf(letter).top).toBe(placed.letters[i]!.y);
    });
    expect(styleOf(DOT).left).toBe(placed.dot.x - 6);
    expect(styleOf(DOT).top).toBe(placed.dot.y - 6);
  });

  it('is centred on the screen, not on a view that starts below an opaque status bar', async () => {
    const STATUS_BAR = 24;
    const NAVIGATION_BAR = 48;
    const view = {
      x: 0,
      y: STATUS_BAR,
      width: SCREEN.width,
      height: SCREEN.height - STATUS_BAR - NAVIGATION_BAR,
    };
    await launchReady({ view });

    // The dot's centre, back on the screen: the floor, 14 pt under the screen's own midline.
    const dot = styleOf(DOT);
    expect(Number(dot.top) + 6 + STATUS_BAR).toBeCloseTo(SCREEN.height / 2 + 14, 9);
    expect(dot.left).toBe(placedFor(view).dot.x - 6);
    expect(styleOf(letters()[0]!).top).toBe(placedFor(view).letters[0]!.y);
  });

  it('takes the view to cover the screen where no safe-area provider says otherwise', async () => {
    await launchReady({ view: null });
    const placed = placedFor(WHOLE_SCREEN);

    expect(letters()).toHaveLength(7);
    expect(styleOf(DOT).left).toBe(placed.dot.x - 6);
    expect(styleOf(DOT).top).toBe(placed.dot.y - 6);
  });

  it('lays the ground and its glow out in the whole screen’s box, from above such a view', async () => {
    const view = { x: 0, y: 24, width: SCREEN.width, height: SCREEN.height - 24 };
    await launchReady({ view });

    expect(styleOf(GROUND)).toMatchObject({
      left: 0,
      top: -24,
      width: SCREEN.width,
      height: SCREEN.height,
    });
  });

  it('sets no letter before its face has loaded, and comes in once it has, under reduced motion', async () => {
    const face = faceStillLoading();
    launch({ face, reduced: true });
    layOutTheSplash();
    await settle();

    clockTo(LOCKUP_IN + A_FEW_FRAMES);
    expect(letters()).toHaveLength(0);
    expect(opacityOf(LOCKUP)).toBe(0);

    await face.arrive();
    const arrivedAt = Date.now() - splashLaidOutAt;
    expect(letters()).toHaveLength(7);
    // The layer's own fade brings them in: the letters are not faded a second time.
    expect(opacityOf(LETTERS)).toBe(1);

    clockTo(arrivedAt + LOCKUP_IN + A_FEW_FRAMES);
    expect(opacityOf(LOCKUP)).toBe(1);
  });

  it('sets no letter in a face that could not be read, and comes in as its dot alone, under reduced motion', async () => {
    const face = faceStillLoading();
    launch({ face, reduced: true });
    layOutTheSplash();

    await face.fail();
    const failedAt = Date.now() - splashLaidOutAt;

    clockTo(failedAt + LOCKUP_IN + A_FEW_FRAMES);
    expect(letters()).toHaveLength(0);
    expect(screen.getByTestId(DOT, HIDDEN_TOO)).toBeTruthy();
    expect(opacityOf(LOCKUP)).toBe(1);
  });

  it('fades with the rest of the splash, and goes with it', async () => {
    await launchReady();

    clockTo(FADE_AT + FADE);
    expect(screen.queryByTestId(LOCKUP, HIDDEN_TOO)).toBeNull();
    expect(letters()).toHaveLength(0);
  });

  /**
   * **The ball bounces Rakieta into place** (#856). Its path and its curves are pure and tested on
   * their own (`domain/splashGeometry.test.ts`, `domain/splashMotion.test.ts`); what this holds is
   * that the splash draws them on the launch's clock: where the ball is, how much of each letter
   * shows, and that the motion ends in #855's still lockup. The motion is read a frame at a time, so
   * every time here is a frame clear of the moment it is about.
   */
  describe('the motion', () => {
    type Drawn = ReturnType<typeof screen.getByTestId>;

    const FRAME = 16;
    const SETTLES_AT = 1680;
    const STILL_AT = 1780;

    /** A transform as Reanimated last drew it, every part it does not say at rest. */
    function transformOf(element: ReturnType<typeof screen.getByTestId>) {
      const { transform = [] } = getAnimatedStyle(element) as ViewStyle;
      return Object.assign(
        { translateX: 0, translateY: 0, scaleX: 1, scaleY: 1 },
        ...(transform as object[]),
      ) as { translateX: number; translateY: number; scaleX: number; scaleY: number };
    }

    /** Where the ball is drawn: the dot's own box, moved and squashed by the motion. */
    function theBall() {
      const element = screen.getByTestId(DOT, HIDDEN_TOO);
      const box = styleOf(DOT);
      const moved = transformOf(element);
      const size = Number(box.width);
      return {
        x: Number(box.left) + size / 2 + moved.translateX,
        y: Number(box.top) + size / 2 + moved.translateY,
        scaleX: moved.scaleX,
        scaleY: moved.scaleY,
      };
    }

    /** How much of each letter shows, in the word's order. */
    function shown(): number[] {
      return letters().map((letter) =>
        Number((getAnimatedStyle(letter) as TextStyle).opacity ?? 1),
      );
    }

    /** How far below its place each letter is, in the word's order. */
    function below(): number[] {
      return letters().map((letter) => transformOf(letter).translateY);
    }

    /**
     * The ball at rest on the dot: the dot's own box, exactly where #855 stands it, and no transform
     * at all — so it is drawn as #855's dot was, not near it.
     */
    function expectTheBallOnTheDot() {
      const { dot } = placedFor(WHOLE_SCREEN);
      expect(transformOf(screen.getByTestId(DOT, HIDDEN_TOO))).toEqual({
        translateX: 0,
        translateY: 0,
        scaleX: 1,
        scaleY: 1,
      });
      expect(styleOf(DOT)).toMatchObject({
        left: dot.x - 6,
        top: dot.y - 6,
        width: 12,
        height: 12,
      });
    }

    /** #855’s lockup, still: the ball on the dot, unsquashed, and every letter in its place. */
    function expectTheStillLockup() {
      const placed = placedFor(WHOLE_SCREEN);
      expectTheBallOnTheDot();
      expect(shown()).toEqual([1, 1, 1, 1, 1, 1, 1]);
      expect(below()).toEqual([0, 0, 0, 0, 0, 0, 0]);
      letters().forEach((letter, i) => {
        expect(styleOf(letter).left).toBe(placed.letters[i]!.x);
        expect(styleOf(letter).top).toBe(placed.letters[i]!.y);
      });
      expect(opacityOf(LOCKUP)).toBe(1);
    }

    it('starts with the ball out of sight above the top edge, the lockup showing nothing else', async () => {
      launch();
      await settle();

      const ball = theBall();
      expect(ball.y + 6 * ball.scaleY).toBeLessThanOrEqual(0);
      expect(ball.x).toBeCloseTo(0.1 * SCREEN.width, 6);
      expect(opacityOf(LOCKUP)).toBe(1);
      expect(opacityOf(LETTERS)).toBe(1);
      expect(shown()).toEqual([0, 0, 0, 0, 0, 0, 0]);
    });

    it('drops the ball straight down onto the floor, where it squashes, and bounces it up', async () => {
      await launchReady();
      const { floor } = placedFor(WHOLE_SCREEN);
      const start = theBall();

      clockTo(200);
      expect(theBall().x).toBe(start.x);
      expect(theBall().y).toBeGreaterThan(start.y);
      expect(theBall().y).toBeLessThan(floor);

      // The first landing, at 0,39 s: wider and flatter, its bottom pressed into the floor.
      clockTo(390 + FRAME + 8);
      expect(theBall().scaleX).toBeGreaterThan(1);
      expect(theBall().scaleY).toBeLessThan(1);

      // Near the first bounce's peak, at 0,72 s: 150 pt above the floor, and round.
      clockTo(720 + 8);
      expect(floor - theBall().y).toBeGreaterThan(145);
      expect([theBall().scaleX, theBall().scaleY]).toEqual([1, 1]);
    });

    it('comes to rest on the dot at 1,68 s and stops dead', async () => {
      await launchReady();

      clockTo(SETTLES_AT - 4 * FRAME);
      expect(transformOf(screen.getByTestId(DOT, HIDDEN_TOO)).translateY).toBeLessThan(0);

      clockTo(SETTLES_AT + FRAME);
      expectTheBallOnTheDot();

      clockTo(FADE_AT - 1);
      expectTheBallOnTheDot();
    });

    it('raises Rak with the first landing, ie with the second and ta with the third', async () => {
      await launchReady();

      clockTo(400);
      expect(shown()).toEqual([0, 0, 0, 0, 0, 0, 0]);

      clockTo(900);
      expect(shown()).toEqual([1, 1, 1, 0, 0, 0, 0]);

      clockTo(1390);
      expect(shown()).toEqual([1, 1, 1, 1, 1, 0, 0]);

      clockTo(STILL_AT + FRAME);
      expect(shown()).toEqual([1, 1, 1, 1, 1, 1, 1]);
      expect(below()).toEqual([0, 0, 0, 0, 0, 0, 0]);
    });

    it('rises each letter from below its place while it fades in', async () => {
      await launchReady();

      // R's rise is cued at 0,42 s and takes 0,32 s.
      clockTo(420 + 2 * FRAME);
      expect(shown()[0]).toBeGreaterThan(0);
      expect(shown()[0]).toBeLessThan(1);
      expect(below()[0]).toBeGreaterThan(0);
      expect(below()[0]).toBeLessThan(10);
    });

    it('ends in #855’s lockup, pixel for pixel, the last frame before the fade', async () => {
      await launchReady();

      clockTo(FADE_AT - 1);
      expectTheStillLockup();
    });

    it('still fades at 2,6 s, the motion long over', async () => {
      await launchReady();

      clockTo(FADE_AT - 1);
      expect(opacityOf(SPLASH)).toBe(1);

      clockTo(FADE_AT + A_FEW_FRAMES);
      expect(opacityOf(SPLASH)).toBeLessThan(1);

      clockTo(FADE_AT + FADE);
      expect(splashIsUp()).toBe(false);
    });

    it('draws one ball, above the letters, with nothing trailing it', async () => {
      await launchReady();
      clockTo(720);

      const drawn = screen
        .getByTestId(LOCKUP, HIDDEN_TOO)
        .findAll((node: Drawn) => typeof node.type === 'string');
      const ballAt = drawn.findIndex((node: Drawn) => node.props.testID === DOT);
      const lastLetterAt = Math.max(...letters().map((letter) => drawn.indexOf(letter)));

      expect(screen.getAllByTestId(DOT, HIDDEN_TOO)).toHaveLength(1);
      expect(ballAt).toBeGreaterThan(lastLetterAt);
      const ball = styleOf(DOT);
      expect(ball.shadowOpacity).toBeUndefined();
      expect(ball.elevation).toBeUndefined();
    });

    /**
     * Setting seven letters is the phone creating seven views and laying out their text on the
     * thread that moves the ball: a face that answered mid-flight stuttered the ball as the word came
     * in. So a face still on its way is waited for, and the ball starts a frame after its letters are
     * set — where the clock's start has them, unseen below their places.
     */
    it('waits for a face still on its way, and starts a frame after its letters are set', async () => {
      const face = faceStillLoading();
      launch({ face });
      layOutTheSplash();
      await settle();

      clockTo(400);
      const start = theBall();
      expect(start.y + 6 * start.scaleY).toBeLessThanOrEqual(0);
      expect(letters()).toHaveLength(0);

      await face.arrive();
      const startsAt = Date.now() - splashLaidOutAt + FRAME;
      expect(letters()).toHaveLength(7);
      expect(shown()).toEqual([0, 0, 0, 0, 0, 0, 0]);
      // There before the motion, so nothing about them is late: no fade of their own.
      expect(opacityOf(LETTERS)).toBe(1);

      clockTo(startsAt + 900);
      expect(shown()).toEqual([1, 1, 1, 0, 0, 0, 0]);

      clockTo(startsAt + STILL_AT + FRAME);
      expect(shown()).toEqual([1, 1, 1, 1, 1, 1, 1]);
      expectTheBallOnTheDot();
    });

    it('lets the ball go without its face after 0,6 s, and fades the letters in as the clock has them', async () => {
      const face = faceStillLoading();
      launch({ face });
      layOutTheSplash();
      await settle();

      // Falling from its first bounce, between the first two landings.
      clockTo(FACE_WAIT + 860);
      expect(letters()).toHaveLength(0);
      expect(theBall().y).toBeLessThan(placedFor(WHOLE_SCREEN).floor);

      await face.arrive();
      const arrivedAt = Date.now() - splashLaidOutAt;
      expect(shown()).toEqual([1, 1, 1, 0, 0, 0, 0]);
      // Late, so they come in over the lockup's short fade rather than all at once, already risen.
      expect(opacityOf(LETTERS)).toBe(0);
      clockTo(arrivedAt + LOCKUP_IN / 2);
      expect(opacityOf(LETTERS)).toBeGreaterThan(0);
      expect(opacityOf(LETTERS)).toBeLessThan(1);
      clockTo(arrivedAt + LOCKUP_IN + A_FEW_FRAMES);
      expect(opacityOf(LETTERS)).toBe(1);

      clockTo(FACE_WAIT + STILL_AT + FRAME);
      expect(shown()).toEqual([1, 1, 1, 1, 1, 1, 1]);
    });

    it('still fades at 2,6 s when its face kept it waiting the longest it waits', async () => {
      const face = faceStillLoading();
      launch({ face });
      layOutTheSplash();
      await settle();
      layOutTheApp();

      clockTo(FACE_WAIT + STILL_AT);
      layOutTheApp();
      clockTo(FADE_AT - 1);
      expect(opacityOf(SPLASH)).toBe(1);
      clockTo(FADE_AT + A_FEW_FRAMES);
      expect(opacityOf(SPLASH)).toBeLessThan(1);
    });

    it('lands the ball as the dot alone when the face could not be read', async () => {
      const face = faceStillLoading();
      launch({ face });
      layOutTheSplash();
      await face.fail();

      clockTo(SETTLES_AT + FRAME);
      expect(letters()).toHaveLength(0);
      expectTheBallOnTheDot();
      expect(opacityOf(LOCKUP)).toBe(1);
    });

    describe('under reduced motion', () => {
      it('flies nothing and bounces nothing: the ball is the dot, every letter in place, from the start', async () => {
        launch({ reduced: true });
        layOutTheSplash();
        await settle();

        [0, 100, 400, 800].forEach((t) => {
          clockTo(t);
          expectTheBallOnTheDot();
          expect(shown()).toEqual([1, 1, 1, 1, 1, 1, 1]);
          expect(below()).toEqual([0, 0, 0, 0, 0, 0, 0]);
        });
      });

      it('ends in the same lockup, pixel for pixel, the last frame before its fade at 0,9 s', async () => {
        await launchReady({ reduced: true });

        clockTo(FADE_AT_REDUCED - 1);
        expectTheStillLockup();
      });
    });
  });
});

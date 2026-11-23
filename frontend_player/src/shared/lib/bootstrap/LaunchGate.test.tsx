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
/** The lockup's short fade-in, under both variants until the ball flies (#855, #856). */
const LOCKUP_IN = 150;

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

function layOutTheApp() {
  fireEvent(screen.getByTestId(APP, HIDDEN_TOO), 'layout', LAYOUT);
}

/** Moves the clock to `ms` after the splash's first layout. */
function clockTo(ms: number) {
  act(() => jest.advanceTimersByTime(splashLaidOutAt + ms - Date.now()));
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

  it('mounts the tree underneath the splash once the sequence resolves', async () => {
    const startup = deferred();
    launch({ run: () => startup.promise });
    layOutTheSplash();

    expect(screen.queryByText('the app')).toBeNull();

    await act(async () => startup.resolve());

    expect(screen.getByText('the app', HIDDEN_TOO)).toBeTruthy();
    expect(splashIsUp()).toBe(true);
    expect(opacityOf(SPLASH)).toBe(1);
  });

  it('keeps the tree from a screen reader until the splash is gone', async () => {
    await launchReady();

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

  it('is in place within 0,15 s of the splash’s first layout', async () => {
    launch();
    expect(opacityOf(LOCKUP)).toBe(0);

    layOutTheSplash();
    await settle();

    clockTo(LOCKUP_IN / 2);
    expect(opacityOf(LOCKUP)).toBeGreaterThan(0);
    expect(opacityOf(LOCKUP)).toBeLessThan(1);

    clockTo(LOCKUP_IN + A_FEW_FRAMES);
    expect(opacityOf(LOCKUP)).toBe(1);
  });

  it('comes in the same way under reduced motion — a fade, not a cut', async () => {
    launch({ reduced: true });
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

  it('sets no letter before its face has loaded, and comes in once it has', async () => {
    const face = faceStillLoading();
    launch({ face });
    layOutTheSplash();
    await settle();

    clockTo(LOCKUP_IN + A_FEW_FRAMES);
    expect(letters()).toHaveLength(0);
    expect(opacityOf(LOCKUP)).toBe(0);

    await face.arrive();
    const arrivedAt = Date.now() - splashLaidOutAt;
    expect(letters()).toHaveLength(7);

    clockTo(arrivedAt + LOCKUP_IN + A_FEW_FRAMES);
    expect(opacityOf(LOCKUP)).toBe(1);
  });

  it('sets no letter in a face that could not be read, and comes in as its dot alone', async () => {
    const face = faceStillLoading();
    launch({ face });
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
});

/**
 * **The launch gate** — the one owner of the launch: the drawn splash, the launch window's release,
 * the startup sequence behind them, the fade and the hold
 * ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §1–§3). It was the bootstrap gate, which held the native splash until the sequence resolved; now
 * **startup is never held**. On its first render it:
 *
 * 1. draws the splash (`DrawnSplash`);
 * 2. starts the sequence it is handed;
 * 3. lets the launch window go on the splash's first layout, and starts its clock there.
 *
 * When the sequence resolves, **the tree mounts underneath the splash** — or the startup failure
 * does, if it rejected — and the first screen starts its own requests under the motion.
 *
 * **The fade starts at the later of** 2.6 s (0.9 s under reduced motion) and the first screen being
 * ready: the sequence settled, the tree laid out, and no hold standing (`splashHold.tsx`). It is a
 * linear 0.5 s fade of the whole splash, after which the splash unmounts. Until then **it swallows
 * every touch**: it is drawn over everything the root draws, and the tree beneath takes none.
 *
 * **It plays once per start of the JavaScript process**, a dev reload included: the gate is mounted
 * once, at the root, and the splash never comes back once it has gone — not on a fast refresh, a
 * return from the background, or a sign-out.
 *
 * Bootstrap is still a **state**, never `user === undefined` (docs/architecture.md Part 3): nothing
 * renders a route tree before the sequence resolves. A failed launch is shown rather than swallowed
 * — config that is missing or malformed has no in-app recovery — and the same fade reveals it.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Easing, ReduceMotion, useSharedValue, withTiming } from 'react-native-reanimated';

import { SplashCoverProvider, useReducedMotion } from '@/shared/ui/overlay';
import { theme } from '@/shared/ui/theme';

import { DrawnSplash } from './DrawnSplash';
import { firstScreenReady, LAUNCH_CLOCK } from './launchClock';
import { LAUNCH_COPY } from './launchCopy';
import { deviceLaunchWindow, pinLaunchWindow, type LaunchWindow } from './launchWindow';
import { SplashHoldsProvider, type SplashHolds } from './splashHold';

// Module scope, so the launch window is pinned before React renders anything at all: it is let go
// on the drawn splash's first layout and not before.
pinLaunchWindow();

type Sequence =
  | { readonly status: 'running' }
  | { readonly status: 'ready' }
  | { readonly status: 'failed'; readonly reason: string };

/**
 * What the fade waits for, as it stands. **Kept outside React's state on purpose**: the moment the
 * last condition is met is the moment the fade and its 0.5 s begin — in that same callback, a timer
 * or a layout or a withdrawn hold — rather than a render and an effect later.
 */
interface Clock {
  earliestPassed: boolean;
  settled: boolean;
  laidOut: boolean;
  holds: number;
  fadeBegun: boolean;
}

function reasonOf(error: unknown): string {
  return error instanceof Error ? error.message : LAUNCH_COPY.failure.unknownReason;
}

export interface LaunchGateProps {
  readonly children: ReactNode;
  /**
   * The sequence to run.
   *
   * Required, and deliberately not defaulted to `bootstrapApp`: one of its steps —
   * restoring the session — belongs to a feature, and `shared/` may never import one.
   * The root layout composes the steps and passes the result in.
   */
  readonly run: () => Promise<void>;
  /** The OS launch window. The device's, unless a test hands the gate a fake. */
  readonly launchWindow?: LaunchWindow;
}

export function LaunchGate({ children, run, launchWindow = deviceLaunchWindow }: LaunchGateProps) {
  // **Decided once, before the first frame**, and never switched mid-play. The provider's first
  // answer is already the OS's — read synchronously as the process started — so this is never the
  // provisional `false` an asynchronous read would give (ADR-0209 §2).
  const reducedAtLaunch = useReducedMotion();
  const [reduced] = useState(reducedAtLaunch);

  const [sequence, setSequence] = useState<Sequence>({ status: 'running' });
  const [splashGone, setSplashGone] = useState(false);

  // The whole splash's opacity, which the fade takes to nothing.
  const shown = useSharedValue(1);
  const clock = useRef<Clock>({
    earliestPassed: false,
    settled: false,
    laidOut: false,
    holds: 0,
    fadeBegun: false,
  });
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach(clearTimeout);
  }, []);

  /** Begins the fade if both its conditions now hold, and never twice. */
  const fadeIfDue = useCallback(() => {
    const now = clock.current;
    if (now.fadeBegun || !now.earliestPassed || !firstScreenReady(now)) return;

    now.fadeBegun = true;
    // **Never** the OS's reduced motion here, which Reanimated would otherwise honour by jumping to
    // the end: the variant was decided once, and under reduced motion the fade is still a 0.5 s
    // fade (decision log Q9) — a cut would leave an invisible splash swallowing taps until 1.4 s.
    shown.value = withTiming(0, {
      duration: LAUNCH_CLOCK.fade,
      easing: Easing.linear,
      reduceMotion: ReduceMotion.Never,
    });
    timers.current.push(setTimeout(() => setSplashGone(true), LAUNCH_CLOCK.fade));
  }, [shown]);

  // **The sequence runs once per mount**, which is once per process: the one handed over first. A
  // root that re-rendered with a fresh function would otherwise run the whole launch again — the
  // keychain, the session check, the referrer — behind a splash that has already decided it.
  const firstRun = useRef(run);

  useEffect(() => {
    let live = true;

    const settle = (next: Sequence) => {
      if (!live) return;
      clock.current.settled = true;
      setSequence(next);
    };

    firstRun.current().then(
      () => settle({ status: 'ready' }),
      (error: unknown) => settle({ status: 'failed', reason: reasonOf(error) }),
    );

    return () => {
      live = false;
    };
  }, []);

  // The splash's first layout, which `DrawnSplash` reports once: the moment it is ready to paint
  // its first frame, so the launch window goes with no blank frame between the two — and the
  // moment every time on the launch's clock is measured from.
  const onSplashLayout = useCallback(() => {
    launchWindow.release();
    const earliest = reduced ? LAUNCH_CLOCK.fadeAtReduced : LAUNCH_CLOCK.fadeAt;
    timers.current.push(
      setTimeout(() => {
        clock.current.earliestPassed = true;
        fadeIfDue();
      }, earliest),
    );
  }, [launchWindow, reduced, fadeIfDue]);

  const onTreeLayout = useCallback(() => {
    clock.current.laidOut = true;
    fadeIfDue();
  }, [fadeIfDue]);

  // A hold counts only while the fade could still wait for it: once the fade has begun, a screen
  // that goes blank changes nothing, and costs the gate no render.
  const splashHolds = useMemo<SplashHolds>(
    () => ({
      place: () => {
        if (clock.current.fadeBegun) return () => {};
        clock.current.holds += 1;
        let withdrawn = false;
        return () => {
          if (withdrawn) return;
          withdrawn = true;
          clock.current.holds -= 1;
          fadeIfDue();
        };
      },
    }),
    [fadeIfDue],
  );

  return (
    <View style={s.root}>
      {sequence.status === 'running' ? null : (
        <View
          style={s.tree}
          onLayout={onTreeLayout}
          // The tree takes no touch while the splash is up — through the fade too, until it is gone
          // — and no screen reader's either: a double-tap is a touch too.
          pointerEvents={splashGone ? 'auto' : 'none'}
          accessibilityElementsHidden={!splashGone}
          importantForAccessibility={splashGone ? 'auto' : 'no-hide-descendants'}
          testID="app-root"
        >
          <SplashCoverProvider covered={!splashGone}>
            <SplashHoldsProvider holds={splashHolds}>
              {sequence.status === 'failed' ? (
                <StartupFailure reason={sequence.reason} />
              ) : (
                children
              )}
            </SplashHoldsProvider>
          </SplashCoverProvider>
        </View>
      )}
      {/* Last, so it is drawn over everything the root draws: the overlay host, the toast host and
          the environment badge are all inside the tree above. */}
      {splashGone ? null : (
        <DrawnSplash reduced={reduced} opacity={shown} onFirstLayout={onSplashLayout} />
      )}
    </View>
  );
}

function StartupFailure({ reason }: { readonly reason: string }) {
  return (
    <View style={s.failure} accessibilityRole="alert">
      <Text style={s.eyebrow}>{LAUNCH_COPY.failure.eyebrow}</Text>
      <Text style={s.title}>{LAUNCH_COPY.failure.title}</Text>
      <View style={s.note}>
        <Text style={s.noteText}>{reason}</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  root: {
    flex: 1,
  },
  tree: {
    flex: 1,
    backgroundColor: theme.color.paper,
  },
  failure: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.sm,
  },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  title: {
    ...theme.type.h1,
    color: theme.color.ink,
  },
  note: {
    backgroundColor: theme.color.redSoft,
    borderRadius: theme.radius.note,
    padding: theme.space.md,
  },
  noteText: {
    ...theme.type.tiny,
    color: theme.color.red,
  },
});

/**
 * `focusManager`, wired to the thing "focus" actually means on a phone.
 *
 * TanStack Query's defaults assume a browser: it listens for `visibilitychange` and
 * window focus, neither of which a React Native app ever fires. Left unwired, "refetch
 * on focus" silently never happens — the app returns from the background showing
 * whatever was on screen when the player left, which on a court-availability screen is
 * data that is minutes stale and looks authoritative.
 *
 * Wiring it once here also makes it **the** answer to *are we at the front*, which is why
 * `useOnForeground` at the bottom is built on it rather than on a second `AppState`
 * listener: app lifecycle is centralised (docs/architecture.md Part 13), and a screen that
 * subscribed on its own would be free to disagree about what `inactive` means.
 */

import { focusManager } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { AppState, type AppStateStatus } from 'react-native';

/**
 * Only `active` counts as focused.
 *
 * `inactive` is the iOS state during the app switcher, an incoming call, or Face ID —
 * transient moments the player is still in the app. Treating them as blur would refetch
 * every time someone half-swiped the app switcher.
 */
function onAppStateChange(state: AppStateStatus): void {
  focusManager.setFocused(state === 'active');
}

/** Called once, by the bootstrap sequence. Returns the unsubscribe for tests. */
export function wireFocusManager(): () => void {
  const subscription = AppState.addEventListener('change', onAppStateChange);
  focusManager.setFocused(AppState.currentState === 'active');
  return () => subscription.remove();
}

/**
 * Run something each time the app comes back to the front.
 *
 * **`focusManager` is where this app already keeps the answer**, fed from `AppState` by
 * `wireFocusManager` above — one listener, wired once by the bootstrap sequence, rather
 * than a screen adding its own. That is Part 13's rule about app lifecycle being
 * centralised, and it is why this hook is here rather than in the feature that wanted it:
 * the second `AppState` listener in an app is the one that disagrees with the first about
 * what `inactive` means.
 *
 * **A mount is not a return.** Nothing runs on the way in — a screen that wants something
 * to happen when it opens can simply do it. What this is for is the case a screen cannot
 * see: the player left, did something else, and came back, and what is drawn is now older
 * than they think.
 *
 * The callback is read through a ref, so a subscription made once still calls what the
 * screen means now rather than the closure it mounted with.
 */
export function useOnForeground(run: () => void): void {
  const latest = useRef(run);

  useEffect(() => {
    latest.current = run;
  }, [run]);

  useEffect(
    () =>
      // `isFocused()` rather than the argument the listener is handed: the two agree, and
      // reading the manager keeps this from depending on which of them a version passes.
      focusManager.subscribe(() => {
        if (focusManager.isFocused()) latest.current();
      }),
    [],
  );
}

/**
 * **Whether the app has gone to the background** — `AppState`'s `background`, and only that — for
 * a screen that keeps something running only while it can be seen: sign-in's hero loop (#787) stops
 * when the app goes away and starts again from its first beat on return.
 *
 * **Not `focusManager`'s answer, on purpose.** That one counts iOS's `inactive` as away, which is
 * right for a refetch; but `inactive` is also the app switcher half-swiped, Control Centre, a call
 * banner — and **Face ID behind the keychain's autofill**, which is how most people fill the very
 * form this loop sits beside. A picture that reset itself every time somebody autofilled their
 * password would be the hero moving with the form. So a screen asking *can I still be seen* reads
 * the background alone. It is still this module's, as every reading of the app's lifecycle is
 * (Part 13): one place says what each state means.
 *
 * Read at the first render, so a screen mounted while the app is away does not start for a frame.
 */
export function useAppInBackground(): boolean {
  const [away, setAway] = useState(() => AppState.currentState === 'background');

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      setAway(state === 'background');
    });
    return () => subscription.remove();
  }, []);

  return away;
}

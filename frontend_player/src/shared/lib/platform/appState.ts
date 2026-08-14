/**
 * `focusManager`, wired to the thing "focus" actually means on a phone.
 *
 * TanStack Query's defaults assume a browser: it listens for `visibilitychange` and
 * window focus, neither of which a React Native app ever fires. Left unwired, "refetch
 * on focus" silently never happens — the app returns from the background showing
 * whatever was on screen when the player left, which on a court-availability screen is
 * data that is minutes stale and looks authoritative.
 */

import { focusManager } from "@tanstack/react-query";
import { AppState, type AppStateStatus } from "react-native";

/**
 * Only `active` counts as focused.
 *
 * `inactive` is the iOS state during the app switcher, an incoming call, or Face ID —
 * transient moments the player is still in the app. Treating them as blur would refetch
 * every time someone half-swiped the app switcher.
 */
function onAppStateChange(state: AppStateStatus): void {
  focusManager.setFocused(state === "active");
}

/** Called once, by the bootstrap sequence. Returns the unsubscribe for tests. */
export function wireFocusManager(): () => void {
  const subscription = AppState.addEventListener("change", onAppStateChange);
  focusManager.setFocused(AppState.currentState === "active");
  return () => subscription.remove();
}

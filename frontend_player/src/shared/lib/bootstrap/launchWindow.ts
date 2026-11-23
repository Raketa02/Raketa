/**
 * **The OS launch window** — the native splash the phone draws before the first JavaScript frame,
 * and the one port to `expo-splash-screen`
 * ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §1).
 *
 * It cannot be removed: iOS requires a launch screen, and Android 12+ always draws a system
 * splash. So it is a plain `#0B2B33` field with no icon (`app.config.ts`), the drawn splash's own
 * edge colour, and the package keeps **two jobs**: that colour, and **one release**. The window is
 * pinned the moment the launch gate's module loads, and let go on the drawn splash's first layout —
 * the moment the splash is ready to paint its first frame, so the two read as one field with no
 * blank frame between them. **Startup no longer holds it**: the sequence runs behind the drawn
 * splash, never behind this.
 *
 * Both calls are wrapped because neither failure is worth crashing a launch over: the window can
 * already be gone after a fast refresh or a warm start.
 */

import * as SplashScreen from 'expo-splash-screen';

/** What the launch gate needs of the window: to let it go, once. */
export interface LaunchWindow {
  /** The drawn splash has laid out and paints the next frame: the native window may go. */
  readonly release: () => void;
}

/** Keeps the launch window up past the first JavaScript frame, until it is released. */
export function pinLaunchWindow(): void {
  void SplashScreen.preventAutoHideAsync().catch(() => {});
}

/** The device's launch window, which the launch gate releases unless a test hands it a fake. */
export const deviceLaunchWindow: LaunchWindow = {
  release: () => {
    void SplashScreen.hideAsync().catch(() => {});
  },
};

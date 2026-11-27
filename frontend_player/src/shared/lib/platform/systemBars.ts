/**
 * **The phone's system bars**, behind a port: the status bar and, on Android, the navigation bar
 * ([#857](https://github.com/Raketa02/Raketa/issues/857), ADR-0209). **The tenth port.**
 *
 * While the drawn splash is up, the bars belong to it. On Android both are painted the field's edge
 * colour with light icons, so the splash reads edge to edge. On an iPhone the status bar shows light
 * content, and there is no navigation bar to paint: the home indicator follows what is drawn under
 * it. When the fade starts, both go back to exactly the look they had.
 *
 * **Two acts and nothing else**, because there is one caller: the launch gate paints the bars as the
 * splash starts and restores them when its fade starts. A port grows a verb when a surface needs one.
 * A screen that wants its own status bar still draws `expo-status-bar`'s element, as sign-in's stage
 * and *It's a game!* do.
 *
 * **The platforms differ, so the adapters are two files**: this one, for an iPhone (and for any
 * platform but Android), and `systemBars.android.ts`, the only importer of `expo-navigation-bar`.
 * The gate checks no platform. A suite drives `fakeSystemBars()` from `src/test-support/platform.ts`.
 *
 * ## The status bar is painted on React Native's own stack
 *
 * Every mounted `<StatusBar>` pushes an entry onto one stack, and the bar shows the entries merged,
 * the latest on top. The root layout's dark bar is the bottom entry. **The splash's paint is one
 * more entry**, pushed as the splash starts, after the root's; restoring pops it. What is left is
 * whatever the app's screens ask for, so a restore is exactly today's look on any first screen:
 * the root's dark icons on paper, or sign-in's light ones over its hero.
 *
 * **A screen mounted under the splash pushes after it, and so wins.** Today only sign-in's stage
 * does that. Its bar is light, so the icons stay light. On Android its ground is transparent, so the
 * splash's own edge shows through, the colour this would have painted.
 *
 * **Neither act ever throws.** A bar that could not be painted is the phone's look, and nothing the
 * launch does next depends on it.
 */

import { StatusBar, type StatusBarProps } from 'react-native';

/**
 * What the launch gate may ask of the system bars.
 *
 * The gate depends on this interface; `deviceSystemBars` is the implementation that talks to the
 * OS, one per platform, and a test substitutes `fakeSystemBars()` from
 * `src/test-support/platform.ts`.
 */
export interface SystemBarsPort {
  /**
   * The bars become the edges of a dark field: `ground` behind them, light icons over it. On an
   * iPhone, light status-bar content alone. **Once**: a second paint before a restore changes
   * nothing.
   */
  readonly paint: (ground: string) => void;
  /**
   * The bars go back to exactly the look they had: the app's own status bar, and the system's own
   * navigation bar. Nothing happens if nothing was painted.
   */
  readonly restore: () => void;
}

/** The splash's entry on the status bar's stack, while it is painted. */
let painted: StatusBarProps | null = null;

/** An iPhone's bars: the status bar's content, light while painted. */
export const deviceSystemBars: SystemBarsPort = {
  paint() {
    if (painted !== null) return;
    painted = StatusBar.pushStackEntry({ barStyle: 'light-content' });
  },
  restore() {
    if (painted === null) return;
    StatusBar.popStackEntry(painted);
    painted = null;
  },
};

/**
 * The one way out of a permanently refused permission: the app's own page in Settings.
 *
 * Here rather than in the screen that needed it, for Part 13's reason — what the app knows
 * about the device it is running on lives in one directory, so the next screen that has to
 * offer this finds it instead of writing a second one. It is a *wiring* rather than a port:
 * there is nothing to decide, nothing to answer, and nothing a test would want to drive.
 *
 * `Linking.openSettings()` opens the app's settings page on both platforms. It is the only
 * thing an app may do about a `blocked` permission — the OS resolves that one itself,
 * instantly and negatively, without showing the player anything.
 */

import { Linking } from 'react-native';

/** Opens Settings on the app's own page. Failures are the OS's, and there is no fallback. */
export function openAppSettings(): void {
  void Linking.openSettings();
}

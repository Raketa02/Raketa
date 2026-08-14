/**
 * The splash screen is the gate: it stays up until the bootstrap sequence resolves, so
 * the player never sees a tree render against unloaded fonts or unvalidated config.
 *
 * Both calls are wrapped because neither failure is worth crashing a launch over — the
 * splash can already be gone after a fast refresh or a warm start, and a splash that
 * refuses to hide is handled by hiding it again on the next layout, not by an exception
 * thrown out of an effect.
 */

import * as SplashScreen from 'expo-splash-screen';

export function preventSplashAutoHide(): void {
  void SplashScreen.preventAutoHideAsync().catch(() => {});
}

export function hideSplash(): void {
  void SplashScreen.hideAsync().catch(() => {});
}

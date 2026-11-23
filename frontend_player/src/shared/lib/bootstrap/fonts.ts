/**
 * The app's typefaces, and the startup sequence's last step.
 *
 * The keys are the **family names** the design system selects weight by
 * (`theme.font.sans[700]`), because `fontWeight` is ignored on Android when a custom
 * `fontFamily` is set. A key here that does not match `theme.font` is not a styling
 * slip — that text silently renders in the system font on device, and `fonts.test.ts`
 * exists to catch it.
 *
 * These are awaited *before* the tree mounts underneath the drawn splash: a font that arrives
 * late reflows every number on screen, and this app puts monospaced figures in front of the
 * player constantly. See docs/architecture.md Part 3.
 */

// Imported file by file, not from the package index. Each index `require`s every weight
// and italic the family ships — 32 files and 4.2 MB where this app needs 8 and 1.1 MB —
// and Metro does not tree-shake, so importing one name ships all of them.
import Archivo_400Regular from '@expo-google-fonts/archivo/Archivo_400Regular.ttf';
import Archivo_500Medium from '@expo-google-fonts/archivo/Archivo_500Medium.ttf';
import Archivo_600SemiBold from '@expo-google-fonts/archivo/Archivo_600SemiBold.ttf';
import Archivo_700Bold from '@expo-google-fonts/archivo/Archivo_700Bold.ttf';
import Archivo_800ExtraBold from '@expo-google-fonts/archivo/Archivo_800ExtraBold.ttf';
import IBMPlexMono_400Regular from '@expo-google-fonts/ibm-plex-mono/IBMPlexMono_400Regular.ttf';
import IBMPlexMono_500Medium from '@expo-google-fonts/ibm-plex-mono/IBMPlexMono_500Medium.ttf';
import IBMPlexMono_600SemiBold from '@expo-google-fonts/ibm-plex-mono/IBMPlexMono_600SemiBold.ttf';
import * as Font from 'expo-font';

import { theme } from '@/shared/ui/theme';

export const appFonts = {
  Archivo_400Regular,
  Archivo_500Medium,
  Archivo_600SemiBold,
  Archivo_700Bold,
  Archivo_800ExtraBold,
  IBMPlexMono_400Regular,
  IBMPlexMono_500Medium,
  IBMPlexMono_600SemiBold,
} as const;

export async function loadFonts(): Promise<void> {
  await Font.loadAsync(appFonts);
}

/**
 * **The splash's one face** — the wordmark's, which the splash loads itself as it starts
 * ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §2). The sequence loads every face last, behind the session check, and on a slow check that would
 * be seconds after the letters are due; so the splash asks for this one at once. It is the same
 * file from the bundle, and loading a face twice costs nothing. The sequence's order is unchanged.
 *
 * A port rather than a call, as the launch window and the bars are, so the launch gate's suite can
 * hold a face back and see the letters wait for it.
 */
export interface SplashFace {
  /** Whether the phone has the face already — once loaded, or after a dev reload. */
  readonly loaded: () => boolean;
  /** Loads it from the bundle: milliseconds, long before the first letter is due. */
  readonly load: () => Promise<void>;
}

const SPLASH_FAMILY = theme.type.splashWord.fontFamily;

export const deviceSplashFace: SplashFace = {
  loaded: () => Font.isLoaded(SPLASH_FAMILY),
  load: () => Font.loadAsync({ [SPLASH_FAMILY]: appFonts[SPLASH_FAMILY] }),
};

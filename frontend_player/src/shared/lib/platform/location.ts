/**
 * The device's position, behind a port. **The only module that imports `expo-location`.**
 *
 * Two reasons, and the second is the one that decided the shape. A native module cannot
 * be driven from a test — there is no JS implementation underneath it — so a feature that
 * imports one is a feature whose screens cannot be exercised. And a capability the app
 * reaches through exactly one file is a capability whose behaviour can be read in one
 * sitting, the way `shared/lib/auth` owning the keychain is what makes token lifetime
 * auditable (ADR-0008). The linter enforces the boundary.
 *
 * **Foreground only, permanently.** Nothing here asks for, checks, or starts a background
 * location. A position the player hands over once to say where they play is a different
 * thing from a stream of positions collected while they are elsewhere, and the second is
 * not what anybody agreed to. `location.test.ts` asserts the absence.
 */

import * as Location from 'expo-location';

import { permissionStateOf, type PermissionState } from './permission';

/** One position, as this app names it. */
export interface LocationFix {
  readonly latitude: number;
  readonly longitude: number;
  /**
   * How wide the device thinks its own answer is, in metres — `null` where the platform
   * does not say. Never substituted with a number: an invented radius is a claim about
   * confidence the device never made.
   */
  readonly accuracyMetres: number | null;
}

/**
 * What the app may ask the device about where it is.
 *
 * Three operations, because there are three questions: what are we allowed to do, ask the
 * player, and where are we. Screens depend on this interface; `deviceLocation` is the one
 * implementation that talks to the OS, and a test substitutes `fakeLocation()` from
 * `src/test-support/platform.ts`.
 */
export interface LocationPort {
  /** The current permission, without prompting anybody. */
  readonly getPermission: () => Promise<PermissionState>;
  /**
   * Ask the player. Shows the OS prompt when there is one to show; a `blocked` permission
   * resolves straight back to `blocked`, because the OS answers that one itself.
   */
  readonly requestPermission: () => Promise<PermissionState>;
  /**
   * One fix, now. `null` when the device could not produce one — a refused permission,
   * location services switched off, or simply no signal. All three mean the same thing to
   * a screen, which is *offer the manual path*, so they arrive as one answer rather than
   * as three native error classes every caller would have to know.
   */
  readonly readFix: () => Promise<LocationFix | null>;
}

/**
 * `Balanced` is roughly a city block, reached without spinning up GPS.
 *
 * The product question is which area someone plays in and how far out they will travel —
 * both answered in kilometres. `High` would cost battery and seconds to sharpen a number
 * nothing reads at that precision.
 */
const ACCURACY = Location.Accuracy.Balanced;

export const deviceLocation: LocationPort = {
  async getPermission() {
    return permissionStateOf(await Location.getForegroundPermissionsAsync());
  },

  async requestPermission() {
    return permissionStateOf(await Location.requestForegroundPermissionsAsync());
  },

  async readFix() {
    try {
      const position = await Location.getCurrentPositionAsync({ accuracy: ACCURACY });
      return {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracyMetres: position.coords.accuracy,
      };
    } catch {
      return null;
    }
  },
};

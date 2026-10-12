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
 * location. A position the player hands over to say where they play is a different thing
 * from a stream of positions collected while they are elsewhere, and the second is not what
 * anybody agreed to. `location.test.ts` asserts the absence.
 *
 * **Two uses, and the permission text names both** (ADR-0195 §3): the area a player plays in,
 * read at a city block and coarsened the moment it is read; and, when they say who's at a game,
 * one precise fix read at that tap and sent with it, so the backend can tell whether they are at
 * the club. Neither is a subscription, and neither is kept on the phone.
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
   * a screen, which is *there is no area, say what that costs and let the player continue*,
   * so they arrive as one answer rather than as three native error classes every caller
   * would have to know.
   */
  readonly readFix: () => Promise<LocationFix | null>;
  /**
   * **One precise fix, now — for an attendance tap alone** (#658). The same answer as
   * {@link readFix}, asked at the accuracy the club's 300 m needs. Read in the foreground at the
   * moment of the tap and handed to the request; the caller keeps nothing.
   */
  readonly readPreciseFix: () => Promise<LocationFix | null>;
}

/**
 * `Balanced` is roughly a city block, reached without spinning up GPS.
 *
 * The product question is which area someone plays in and how far it is to a club — both
 * answered in kilometres. `High` would cost battery and seconds to sharpen a number
 * nothing reads at that precision.
 */
const ACCURACY = Location.Accuracy.Balanced;

/**
 * `High` is the GPS fix, about ten metres outdoors: *at the club* is within 300 m of its point, and
 * a city block's answer could put a player in the car park on the wrong side of that line. Asked
 * once per tap, which is the only battery it costs.
 */
const PRECISE = Location.Accuracy.High;

/**
 * **How long a tap waits for its fix** — fifteen seconds, then no fix. A tap is a moment: the
 * backend dates an arrival when it lands, so a GPS that never settles indoors must not hold the
 * press, and *try again in a moment* is the honest answer.
 */
export const PRECISE_FIX_WITHIN_MS = 15_000;

/** `reading`, or `null` once `ms` have passed without it. */
function within(ms: number, reading: Promise<LocationFix | null>): Promise<LocationFix | null> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), ms);
    void reading.then((fix) => {
      clearTimeout(timer);
      resolve(fix);
    });
  });
}

/** One fix at `accuracy`, or `null` for every way the device could fail to produce one. */
async function oneFix(accuracy: Location.Accuracy): Promise<LocationFix | null> {
  try {
    const position = await Location.getCurrentPositionAsync({ accuracy });
    return {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracyMetres: position.coords.accuracy,
    };
  } catch {
    return null;
  }
}

export const deviceLocation: LocationPort = {
  async getPermission() {
    return permissionStateOf(await Location.getForegroundPermissionsAsync());
  },

  async requestPermission() {
    return permissionStateOf(await Location.requestForegroundPermissionsAsync());
  },

  readFix: () => oneFix(ACCURACY),

  readPreciseFix: () => within(PRECISE_FIX_WITHIN_MS, oneFix(PRECISE)),
};

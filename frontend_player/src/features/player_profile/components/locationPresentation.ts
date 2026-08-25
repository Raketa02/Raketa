/**
 * The words on the location step.
 *
 * **This step asks for a permission, so most of what is here is the explanation that goes
 * before one.** A prompt a player did not expect is refused by people who would have said
 * yes, and iOS shows it once — so the sentence that earns the yes has to be on screen
 * before the OS dialog is, not underneath it.
 *
 * The copy is honest in both directions, which is the harder half:
 *
 * - **What is kept is said plainly**, because *about a kilometre* is a fact a player can
 *   check against the figure on screen. A screen that said "we respect your privacy" and
 *   showed six decimal places would be a screen nobody should believe.
 * - **What a refusal costs is named, not implied.** Location is what discovery is built
 *   on: a player without an area cannot search and cannot be matched. Saying so is not a
 *   dark pattern — hiding it until the app is empty would be.
 *
 * The refused / blocked split is the photos step's, for the same reason: pressing the
 * control again is the whole answer to one of them and achieves nothing on the other.
 */

import type { LocationArea } from '../domain/ProfileDraft';
import { LOCATION_AREA_DECIMALS } from '../domain/locationArea';

import type { LocationAccess } from '../hooks/useLocationStep';

/** The one control that reaches the device — named twice below, so it is named once here. */
export const USE_MY_LOCATION = 'Use my location';

/** Swapped in while the device is being read. A busy button is not a disabled one. */
export const READING_WORD = 'Reading your area…';

export const WHY_TITLE = 'Why Raketa asks';

export const WHY_BODY =
  'Raketa puts you in front of players near you, and finds them near you — your area is ' +
  'what both of those are worked out from. We read your position once, round it to about ' +
  'a kilometre, and keep only the rounded area. Never your exact position, and never while ' +
  'you are doing something else.';

/** The heading over the area itself, and the word the row is announced with. */
export const AREA_LABEL = 'Your area';

export const AREA_PRECISION_LINE =
  'About a kilometre across. Your exact position is not kept — not on this phone, and not ' +
  'by the platform.';

/** Said under the control before anything has been read, so the ask is not a surprise. */
export const AREA_UNSET_LINE =
  'Nothing is read until you press it, and the first press is where your phone asks you.';

export const ACCESS_TITLE: Readonly<
  Record<Exclude<LocationAccess, 'unasked' | 'granted'>, string>
> = {
  refused: 'Raketa cannot see where you play',
  blocked: 'Location is turned off for Raketa',
};

/**
 * What a refusal costs, and what to do about it.
 *
 * Both sentences end the same way on purpose: the consequence is the same whichever refusal
 * it was, and the player should not have to work out that the two screens they might be
 * looking at mean one thing.
 */
export const ACCESS_BODY: Readonly<Record<Exclude<LocationAccess, 'unasked' | 'granted'>, string>> =
  {
    refused: `Press ${USE_MY_LOCATION} again to allow it. You can finish setting up without an area — but until you set one, you cannot search for players and no game can be suggested to you.`,
    blocked: `Turn it on for Raketa in Settings, then press ${USE_MY_LOCATION} again. You can finish setting up without an area — but until you set one, you cannot search for players and no game can be suggested to you.`,
  };

/** The control that goes where pressing again cannot: the app's own settings page. */
export const OPEN_SETTINGS = 'Open Settings';

/** Permission granted and still no fix — indoors, underground, or a device with no signal. */
export const NO_FIX_TITLE = 'Your phone could not place you';

export const NO_FIX_BODY =
  `It happens indoors and underground. Press ${USE_MY_LOCATION} again in a moment, or ` +
  'continue and set your area later from your profile.';

export const WITH_AN_AREA_LABEL = 'Continue';

/**
 * The label a player leaving with no area presses.
 *
 * It says the consequence rather than leaving it in a note beside it: this is the last
 * moment the choice is in front of them, and *Continue* alone would let a refusal that
 * costs discovery read as an ordinary step passed.
 */
export const WITHOUT_AN_AREA_LABEL = 'Continue without matching';

export function continueLabel(area: LocationArea | undefined): string {
  return area === undefined ? WITHOUT_AN_AREA_LABEL : WITH_AN_AREA_LABEL;
}

/** The area as it is drawn: two decimals, comma-separated, and the hemisphere as a letter. */
export function areaLine(area: LocationArea): string {
  return `${degrees(area.latitude)}° ${area.latitude < 0 ? 'S' : 'N'} · ${degrees(area.longitude)}° ${
    area.longitude < 0 ? 'W' : 'E'
  }`;
}

/** The same fact with the symbols spelled out, for whoever is listening rather than looking. */
export function spokenArea(area: LocationArea): string {
  const latitude = `${degrees(area.latitude)} degrees ${area.latitude < 0 ? 'south' : 'north'}`;
  const longitude = `${degrees(area.longitude)} degrees ${area.longitude < 0 ? 'west' : 'east'}`;
  return `${AREA_LABEL}: ${latitude}, ${longitude}`;
}

/**
 * A magnitude, in this app's decimal convention — the hemisphere carries the sign.
 *
 * `toFixed` and a substitution rather than `toLocaleString`, for the reason `ratingFormat`
 * gives: Hermes ships without full ICU data, so a locale-aware formatter puts a comma on
 * one device and a point on another for the same place.
 */
function degrees(value: number): string {
  return Math.abs(value).toFixed(LOCATION_AREA_DECIMALS).replace('.', ',');
}

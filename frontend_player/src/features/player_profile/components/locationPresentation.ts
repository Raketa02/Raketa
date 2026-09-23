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
 * - **What is kept is said plainly.** *Rounded to about 1 km, and only that approximate
 *   area* is the whole promise, and it is stated before the prompt rather than after it. A
 *   screen that said "we respect your privacy" and left the reader to guess what that meant
 *   would be a screen nobody should believe. The title asks the player's own question back at
 *   them — *why we ask your location* — because that is what somebody looking at a permission
 *   control wants answered, rather than a heading about Raketa.
 * - **What a refusal costs is named, not implied.** Location is what discovery is built
 *   on: a player without an area cannot search and cannot be matched. Saying so is not a
 *   dark pattern — hiding it until the app is empty would be.
 *
 * The refused / blocked split is the photos step's, for the same reason: pressing the
 * control again is the whole answer to one of them and achieves nothing on the other.
 *
 * ## The coordinates are not words on this screen, and there are none here to write
 *
 * The area used to be printed back as a degree pair. It no longer is: a player has no use
 * for their own latitude, cannot check it, and a screen full of figures reads as *this is
 * what we took* rather than *this is what we rounded away*. What replaced it is a control
 * that says it is done — `LOCATION_SAVED` — so the whole of what this file writes about the
 * area is now the promise and the confirmation. **The formatters that drew the pair are
 * gone rather than left unused**, which is what makes *the precise fix never reaches a
 * screen* true of one fewer file.
 */

import type { LocationArea } from '../domain/ProfileDraft';

import type { LocationAccess } from '../hooks/useLocationCapture';

/** The one control that reaches the device — named several times below, so once here. */
export const USE_MY_LOCATION = 'Use my location';

/** Swapped in while the device is being read. A busy button is not a disabled one. */
export const READING_WORD = 'Reading your area…';

/**
 * What the same control says once there is an area.
 *
 * **The words, not only the green**, and this is the half the design system insists on: a
 * control that carried *done* in a fill alone would carry it for nobody who cannot see the
 * fill. Pressing it again re-reads, which is why it stays a control rather than becoming a
 * label.
 */
export const LOCATION_SAVED = 'Location saved';

/** What pressing the settled control would do — it is not the same act as the first press. */
export const READ_AGAIN_HINT = 'Reads your area again';

export const WHY_TITLE = 'Why we ask your location';

export const WHY_BODY =
  'To show you nearby players and show you to them, Raketa needs a rough idea of where you ' +
  'play. We take one location reading, round it to about 1 km, and only keep that ' +
  'approximate area. We never store your exact location or track you in the background.';

export const ACCESS_TITLE: Readonly<
  Record<Exclude<LocationAccess, 'unasked' | 'granted'>, string>
> = {
  refused: 'Raketa cannot see where you play',
  blocked: 'Location is turned off for Raketa',
};

/**
 * What to do about a refusal — the half of each sentence that is true on every screen.
 *
 * The You tab's *Where you play* cites the step's permission states (ADR-0179 §2), and this
 * is the part it cites: how to undo the refusal. What it does **not** cite is the cost clause
 * below, which is about finishing setting up — a player on the tab finished long ago and holds
 * an area already, so that clause would be a sentence about somebody else.
 */
export const ACCESS_HOW_TO: Readonly<
  Record<Exclude<LocationAccess, 'unasked' | 'granted'>, string>
> = {
  refused: `Press ${USE_MY_LOCATION} again to allow it.`,
  blocked: `Turn it on for Raketa in Settings, then press ${USE_MY_LOCATION} again.`,
};

/**
 * What a refusal costs **on the step**: the same clause after either refusal, because the
 * consequence is the same whichever it was and the player should not have to work out that
 * the two screens they might be looking at mean one thing.
 */
const WITHOUT_AN_AREA_COST =
  'You can finish setting up without an area — but until you set one, you cannot search for ' +
  'players and no game can be suggested to you.';

/** What a refusal costs, and what to do about it — the step's whole note. */
export const ACCESS_BODY: Readonly<Record<Exclude<LocationAccess, 'unasked' | 'granted'>, string>> =
  {
    refused: `${ACCESS_HOW_TO.refused} ${WITHOUT_AN_AREA_COST}`,
    blocked: `${ACCESS_HOW_TO.blocked} ${WITHOUT_AN_AREA_COST}`,
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

/** What the control that reads the device says, given whether there is already an area. */
export function captureLabel(area: LocationArea | undefined): string {
  return area === undefined ? USE_MY_LOCATION : LOCATION_SAVED;
}

/**
 * **The one written trace of the cold-start refresh** — You's sentence, `the-words.md` §26.
 *
 * The area moves silently: on every launch and after a day in the background, the app reads
 * the phone again and puts the cell, with no prompt and no toast
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6). Silent motion with no written trace is the one thing that would surprise a careful
 * player, so the tab says it once, statically — and it says the coarseness in the same
 * breath, because *updates each time you open* on its own reads as tracking, and the
 * kilometre is what makes it not.
 */
export const AREA_UPDATES_LINE =
  'Your area updates each time you open Raketa; it is never finer than about a kilometre.';

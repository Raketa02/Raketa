/**
 * The words on the location step, and on You's *Where you play*.
 *
 * **This step asks for a permission, so most of what is here is the explanation that goes
 * before one.** A prompt a player did not expect is refused by people who would have said
 * yes, and iOS shows it once — so the sentence that earns the yes has to be on screen
 * before the OS dialog is, not underneath it.
 *
 * **The copy tells the truth about what the area is for** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §10). The area measures how far each club is and orders every club search, and that is all it
 * does: the step used to say it was *to show you nearby players and show you to them*, and that
 * a player could *finish setting up without an area* — the first named a players search that no
 * longer exists, the second a finish that never allowed it. Both went, with *Continue without
 * matching* and the commit's *Finding players near you*. What is kept is said plainly — rounded
 * to about a kilometre, never shown to another player — before the prompt rather than after it.
 *
 * **A refusal is answered with another way, not with a cost.** *Pick a club near where you play*
 * is the alternative Apple's 5.1.1(iv) asks for: the club's point becomes the area. The refused
 * / blocked split is the photos step's, for the same reason — pressing the control again is the
 * whole answer to one of them and achieves nothing on the other — and **each sentence names the
 * club as the other way**, so the step and the tab, which both offer it, say one thing.
 *
 * ## The coordinates are not words on this screen, and there are none here to write
 *
 * The area used to be printed back as a degree pair. It no longer is: a player has no use
 * for their own latitude, cannot check it, and a screen full of figures reads as *this is
 * what we took* rather than *this is what we rounded away*. What replaced it is a control
 * that says it is done — `LOCATION_SAVED` — or the club she picked, by name.
 */

import type { LocationSource, PickedClub } from '../domain/ProfileDraft';

import type { LocationAccess } from '../hooks/useLocationCapture';

/** The one control that reaches the device — named several times below, so once here. */
export const USE_MY_LOCATION = 'Use my location';

/** What pressing it does, before there is an area from the phone. */
export const USE_MY_LOCATION_HINT = 'Asks your phone for your position, once';

/** Swapped in while the device is being read. A busy button is not a disabled one. */
export const READING_WORD = 'Reading your area…';

/**
 * What the same control says once the phone's reading is the area.
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

/** ADR-0200 §10's sentence, verbatim: what the area is for, and what is kept of it. */
export const WHY_BODY =
  'Raketa shows how far each club is and lists the nearest first. Your area is rounded to ' +
  'about a kilometre and never shown to other players.';

/** The other way to an area, offered after a refusal on the step and always on the tab. */
export const PICK_A_CLUB = 'Pick a club near where you play';

/** The same offer at the end of a sentence about a refusal — said once, named three times below. */
const OR_PICK_A_CLUB = 'or pick a club near where you play';

type Refusal = Exclude<LocationAccess, 'unasked' | 'granted'>;

export const ACCESS_TITLE: Readonly<Record<Refusal, string>> = {
  refused: 'Raketa cannot see where you play',
  blocked: 'Location is turned off for Raketa',
};

/**
 * What to do about a refusal: undo it, or pick a club. True on the step and on the tab alike,
 * because both offer the club — the step's old cost clause, about finishing without an area,
 * was true of neither.
 */
export const ACCESS_HOW_TO: Readonly<Record<Refusal, string>> = {
  refused: `Press ${USE_MY_LOCATION} again to allow it, ${OR_PICK_A_CLUB}.`,
  blocked: `Turn it on for Raketa in Settings and press ${USE_MY_LOCATION} again, ${OR_PICK_A_CLUB}.`,
};

/** The control that goes where pressing again cannot: the app's own settings page. */
export const OPEN_SETTINGS = 'Open Settings';

/** Permission granted and still no fix — indoors, underground, or a device with no signal. */
export const NO_FIX_TITLE = 'Your phone could not place you';

export const NO_FIX_BODY = `It happens indoors and underground. Press ${USE_MY_LOCATION} again in a moment, ${OR_PICK_A_CLUB}.`;

/** The step's way on — drawn only once there is an area (ADR-0200 §10). */
export const CONTINUE = 'Continue';

/**
 * What the control that reads the device says: *Location saved* only while the phone's reading
 * is the area. A picked club is an area too, but not one this control produced, so the control
 * still offers what it does.
 */
export function captureLabel(location: LocationSource | undefined): string {
  return location?.kind === 'reading' ? LOCATION_SAVED : USE_MY_LOCATION;
}

// ---------------------------------------------------------------------------
// Pick a club near where you play
// ---------------------------------------------------------------------------

/** In the field before anything is typed: what the search reads. */
export const CLUB_SEARCH_PLACEHOLDER = 'Club name or district';

/** The pill beside each club the search answers — the whole head is the tap. */
export const PICK_WORD = 'Pick';

/** Under *No club called "…"*: what can be picked, so the empty answer is not a dead end. */
export const NO_CLUB_NOTE = 'Only clubs in Raketa can be picked — try a district.';

/** More of the answer than the first twenty — the search asks a page at a time. */
export const MORE_CLUBS = 'More clubs';

/** The chosen club's one control: back to the search. */
export const CHANGE_CLUB = 'Change';
export const CHANGE_CLUB_LABEL = 'Change the club';

/** While a pick is being written, on the tab — the step holds it in the draft and writes nothing. */
export const SAVING_WORD = 'Saving…';

/**
 * **The tab's write refusals, by `code`**, read over `recoveryMessage` with `codeMessage`. One entry:
 * a picked club the server no longer knows (`location_club_unknown`, #726). The generic
 * *check the details above* would point at a club the screen has already let go of; this says
 * what happened and what to do, and the search is back under it.
 */
export const AREA_WRITE_REFUSAL: Readonly<Record<string, string>> = {
  location_club_unknown: 'That club is no longer in Raketa — pick another.',
};

/** A club's card, spoken — the head is the tap, and its line rides with the name. */
export function pickClubLabel(name: string, line: string): string {
  return `${PICK_WORD} ${name}, ${line}`;
}

/** The chosen club, spoken whole: what the area now is. */
export function pickedClubLabel(club: PickedClub): string {
  return `Your area: ${club.name}, ${club.district}`;
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

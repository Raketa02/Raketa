/**
 * The words on the photos step.
 *
 * **The copy states the on-court rule, and the check is only ever mentioned to the player it
 * has something to say about.** There *is* a review running now — every upload is scored
 * server-side against the rule and the answer comes back on the response
 * ([ADR-0129](../../../../../docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md))
 * — so the sentence this file used to be careful not to write is no longer untrue. It is
 * still not written. Announcing *we check every photo* up front is small print for the
 * majority whose photo is fine, and it reads as a threat to the rest; it is the same
 * argument that took the third line off this step. The check earns a sentence at the one
 * moment it has a claim to make, and that sentence is `FLAGGED_TITLE` and `FLAGGED_BODY`.
 *
 * `Three is the ceiling` deliberately mirrors the tags step's ceiling refusal: a fact,
 * stated without apology and without *you can only*. **The two are one decision** — do not
 * reword either independently of the other.
 *
 * **The step no longer promises in advance that no photo is fine.** The eyebrow already says
 * *up to three*, the continue control is never disabled, and the two permission notes say
 * what carrying on without any gets you at the one moment a player is actually deciding it.
 * A third line saying the same thing to somebody who had not asked was small print.
 *
 * Every accessible name here exists because the tile it names carries its fact in a
 * drawing: the border says which photo leads and the foot strip says what an upload is
 * doing, and neither is legible to a screen reader (design-system 6.9).
 */

import type { AppError } from '@/shared/errors';
import { codeMessage } from '@/shared/errors';

import type { ProfilePhoto } from '../domain/photoCollection';
import type { PhotoAccess } from '../hooks/useProfilePhotos';

import { stepEyebrow } from './socialStepPresentation';

/** The rule the eyebrow carries — cited alone under the You tab's group title (ADR-0179 §2). */
export const PHOTOS_RULE = 'On-court only — up to three';

/** The eyebrow, carrying the rule beside the position — the tags step's shape. */
export function photosEyebrow(): string {
  return `${stepEyebrow('photos')} · ${PHOTOS_RULE}`;
}

/**
 * The one thing this screen asks a player to understand.
 *
 * It says what a photo is **for** rather than listing what is banned, and it is the words
 * a flagged photo's warning is measured against: the check is the same rule, applied by a
 * machine, so a player who read this and was warned anyway must not have to work out which
 * rule they are being told about.
 */
export const PHOTO_RULE_TITLE = 'Rackets mandatory, faces optional';

export const PHOTO_RULE_BODY =
  'Photos on Rakieta follow one simple rule: keep it about the racket sports. Show yourself ' +
  'on court or in a racket-sport setting — no casual selfies, party photos, or gym mirrors. ' +
  "Showing your face is optional. The sport context isn't.";

/**
 * The words on the sheet a held tile opens, and the one sentence that says the sheet exists.
 *
 * **Three acts, and the order is what they do to the row**: swap this picture, add another
 * beside it, re-frame this one. Remove is deliberately not among them — it is the square on
 * the tile and has been since the row was drawn, and moving it into a menu would put the one
 * destructive act behind a gesture nobody can see.
 *
 * ## Two of the three open the same picker, and the copy is what keeps them apart
 *
 * *Replace* and *Edit* are the same request to the platform, because there is only one crop
 * frame and it is attached to choosing a picture: nothing in this app can re-crop a file it
 * already holds (`ImagePickingPort`). So the two are told apart by what a player means by
 * them, and each hint says the whole truth about what will happen — *choose a different
 * photo* against *choose this one again and re-frame it*. **The second sentence is the one
 * that must not be softened.** A player who taps *Edit* expecting their photograph to appear
 * in a crop frame will instead be looking at their library, and the hint is the only place
 * they can be told that before it happens.
 */
export const PHOTO_SHEET_TITLE = 'This photo';

export const PHOTO_SHEET_CLOSE = 'Close photo options';

/** One act on the sheet: what it is called, and what it will actually do. */
export interface PhotoAction {
  readonly label: string;
  readonly hint: string;
}

export const REPLACE_ACTION: PhotoAction = {
  label: 'Replace this photo',
  hint: 'Choose a different photo for this spot, and crop it',
};

export const ADD_ANOTHER_ACTION: PhotoAction = {
  label: 'Add new photo',
  hint: 'Keeps this one and adds another beside it',
};

export const EDIT_ACTION: PhotoAction = {
  label: 'Edit',
  // The whole truth, and the sentence the sheet exists to be honest about: the crop frame
  // only ever comes attached to choosing a picture, so re-framing means picking again.
  hint: 'Opens your photos so you can choose this one again and re-crop it',
};

/** Names the hold on one tile, and says which photo it is about — `removeControlLabel`'s rule. */
export function optionsControlLabel(at: number, held: number): string {
  return `Options for photo ${at + 1} of ${held}`;
}

/**
 * That the tile has a third act at all, said once under the row.
 *
 * It is one line beside the promote line rather than a mark on every tile, for exactly the
 * reason `PROMOTE_LINE` is: a per-tile affordance would be this sentence printed three times
 * over the photographs it describes, and a glyph small enough to fit would be the third 44pt
 * square the tile has no room for (6.9).
 */
export const PHOTO_OPTIONS_LINE = 'Press and hold a photo to replace, add or edit.';

/**
 * The promote affordance, as a sentence under the row.
 *
 * Nothing is drawn on a tile to advertise it: a per-tile label would be this sentence
 * printed up to three times over the photographs it describes, and a glyph small enough to
 * fit would be a third 44pt square in a tile with room for two (6.9).
 */
export const PROMOTE_LINE = 'Tap a photo to make it the profile photo.';

/** The hint every non-profile tile carries — the same sentence, for whoever cannot see it. */
export const PROMOTE_HINT = 'Make this the profile photo';

/** The word the add control wears, and the refusal that replaces it at the ceiling. */
export const ADD_CONTROL_WORD = 'Add a photo';

export const CEILING_TITLE = 'Three is the ceiling';

export const CEILING_BODY =
  'Nothing changed. Remove one you have already added to make room for another.';

/** The strip's two words. Short because the strip is 18pt tall and one line of `tag`. */
export const PROFILE_WORD = 'Profile';
export const FAILED_WORD = 'Failed';

/**
 * What one photo the check did not read as on-court is told, and it is a warning.
 *
 * **The reader of this sentence may be somebody the check is wrong about**, and that is the
 * whole of the design problem — the flag rate is a fact about a corpus nobody has measured
 * yet, so some share of the people who see it are on a court in the photograph they just
 * picked. Four things follow, and every clause here is one of them.
 *
 * It is written as **our** failure to see rather than the player's failure to comply. *We
 * could not see a court* is the honest report of what happened; *this is not an on-court
 * photo* is a verdict about a picture the machine may simply have got wrong.
 *
 * It says **nobody has looked**, because nobody has. Nothing reviews a flagged photo a
 * second time — there is no queue and no human at the end of one — and a warning that let a
 * player believe otherwise would be inventing a process to reassure them with.
 *
 * It says **nothing is blocked**, because nothing is: the photo is stored, it keeps its id,
 * it is committed with the profile, and `Continue` was never disabled by this. A false
 * positive has to cost a sentence, not a signup.
 *
 * And it ends by naming the **choice**, in that order: keep it if the check is wrong, swap
 * it if it is not. A player who is on a court is told first, because they are the one the
 * sentence risks insulting.
 */
export function flaggedNoticeTitle(at: number, held: number): string {
  return `${photoPosition(at, held)} — we could not see a court`;
}

export const FLAGGED_BODY =
  'The check is automatic, nobody has looked at your photo, and it gets it wrong ' +
  'sometimes. Nothing is blocked — keep it if you are on a court in it, and swap it if ' +
  'you are not.';

/** How many slots remain, said out loud — the row's arithmetic is invisible otherwise. */
export function addControlLabel(slots: number): string {
  return slots === 1
    ? `${ADD_CONTROL_WORD}, 1 slot left`
    : `${ADD_CONTROL_WORD}, ${slots} slots left`;
}

/**
 * What one tile is called: its position, whether it leads, and what its strip says.
 *
 * *Of how many* is the number of photos the player actually has, not the ceiling: "Photo 1
 * of 3" on a row holding one would be counting the empty space beside it.
 */
function photoPosition(at: number, held: number): string {
  return `Photo ${at + 1} of ${held}`;
}

export function photoTileLabel(photo: ProfilePhoto, at: number, held: number): string {
  const position = photoPosition(at, held);

  if (photo.upload.kind === 'uploading') return `${position}, uploading`;
  if (photo.upload.kind === 'failed') return `${position}, upload failed`;
  return at === 0 ? `${position}, profile photo` : position;
}

/**
 * What pressing the tile would do — which is not the same act on a failed tile.
 *
 * A photo still uploading is promoted like any other: the press does the same thing, so it
 * has to be announced the same way. Only the one already leading has nothing to say, and
 * that is because there is nothing pressing it would do.
 */
export function photoTileHint(photo: ProfilePhoto, at: number): string | undefined {
  if (photo.upload.kind === 'failed') return 'Try this upload again';
  return at === 0 ? undefined : PROMOTE_HINT;
}

export function removeControlLabel(at: number, held: number): string {
  return `Remove photo ${at + 1} of ${held}`;
}

/** Says the picture is generated, so nobody has to see it to know it is not the player. */
export const POSTER_LABEL =
  'A generated court poster, not a photograph — what other players see until you add one.';

export const ACCESS_TITLE: Readonly<Record<Exclude<PhotoAccess, 'granted'>, string>> = {
  refused: 'Rakieta has no access to your photos',
  blocked: 'Photo access is turned off',
};

export const ACCESS_BODY: Readonly<Record<Exclude<PhotoAccess, 'granted'>, string>> = {
  refused: `Press ${ADD_CONTROL_WORD} again to allow it. Or carry on without any — you get a court poster of your own either way.`,
  blocked: `Turn it on for Rakieta in Settings, then press ${ADD_CONTROL_WORD} again. Or carry on without any — you get a court poster of your own either way.`,
};

/**
 * Why one upload failed, in words the player can act on.
 *
 * A **code** table, never the backend's `message`: that is a diagnostic written for a log,
 * and rendering it ships English into every locale. The two codes here are the ones a
 * player's own choice produces — a picture the platform will not take, and one too large —
 * and both mean *this photo will not work however many times you press retry*, which is
 * exactly what the generic recovery sentence would fail to say.
 */
const FAILURE_BY_CODE: Readonly<Record<string, string>> = {
  unsupported_image_format: 'That format is not one we can take. Try a JPEG, PNG or HEIC photo.',
  image_too_large: 'That photo is too large. Try one taken at a smaller size.',
  unreadable_image: 'That file could not be read as a photo. Try another one.',
};

export function photoFailureMessage(error: AppError): string {
  return codeMessage(FAILURE_BY_CODE, error);
}

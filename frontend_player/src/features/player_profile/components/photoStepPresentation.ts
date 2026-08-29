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
import { recoveryMessage } from '@/shared/errors';

import type { ProfilePhoto } from '../domain/photoCollection';
import type { PhotoAccess } from '../hooks/useProfilePhotos';

import { stepEyebrow } from './socialStepPresentation';

/** The eyebrow, carrying the rule beside the position — the tags step's shape. */
export function photosEyebrow(): string {
  return `${stepEyebrow('photos')} · On-court only — up to three`;
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
  'Show yourself on a court — mid-rally, or catching your breath afterwards. Not a selfie, ' +
  'not the beach, not the gym mirror. Your face is up to you; the sport is not.';

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
  refused: 'Raketa has no access to your photos',
  blocked: 'Photo access is turned off',
};

export const ACCESS_BODY: Readonly<Record<Exclude<PhotoAccess, 'granted'>, string>> = {
  refused: `Press ${ADD_CONTROL_WORD} again to allow it. Or carry on without any — you get a court poster of your own either way.`,
  blocked: `Turn it on for Raketa in Settings, then press ${ADD_CONTROL_WORD} again. Or carry on without any — you get a court poster of your own either way.`,
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
  return (
    (error.code === undefined ? undefined : FAILURE_BY_CODE[error.code]) ?? recoveryMessage(error)
  );
}

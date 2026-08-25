/**
 * The words on the photos step.
 *
 * **The copy states the on-court rule and claims no check is performed.** There is no
 * content review running in this build, and a screen that said *we check* would be telling
 * a player something untrue about how the product works — the one kind of copy defect that
 * survives a redesign, because nobody re-reads a sentence they believe.
 *
 * `Three is the ceiling` deliberately mirrors the tags step's ceiling refusal: a fact,
 * stated without apology and without *you can only*. **The two are one decision** — do not
 * reword either independently of the other.
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
 * The one thing this screen asks a player to understand, and the one it must not claim.
 *
 * *A photo here answers exactly one question, and it is not how you look.* That is the
 * whole argument for the rule, and it is why the note says what a photo is **for** rather
 * than listing what is banned.
 */
export const PHOTO_RULE_TITLE = 'Rackets mandatory, faces optional';

export const PHOTO_RULE_BODY =
  'Photos show you on a court — playing, or just after. Not a selfie, not the beach, not the ' +
  'gym mirror. Faces are optional; the sport is not. A photo here answers exactly one ' +
  'question, and it is not how you look — it is do I want to play this person?';

/** Said before a player has to find out by leaving the step with nothing. */
export const NO_PHOTO_IS_FINE =
  'No photo is fine — you get a court poster of your own, and you can add photos any time ' +
  'from your profile.';

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
export function photoTileLabel(photo: ProfilePhoto, at: number, held: number): string {
  const position = `Photo ${at + 1} of ${held}`;

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
  refused: `Press ${ADD_CONTROL_WORD} again to allow it. Or continue without any — no photo is fine.`,
  blocked: `Turn it on for Raketa in Settings, then press ${ADD_CONTROL_WORD} again. Or continue without any — no photo is fine.`,
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

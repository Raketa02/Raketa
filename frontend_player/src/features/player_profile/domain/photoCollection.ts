/**
 * The photos a Player profile may hold, and every rule about them that is not a drawing.
 *
 * **Photos are optional and the ceiling is three** — an empty collection is a complete
 * answer, and a player who adds none gets a generated court poster rather than an empty
 * box (`courtPosterFraming`). Both facts are the product's, not the layout's, which is why
 * they are here rather than in the screen that happens to draw three tiles.
 *
 * ## The first photo is the profile photo, and that is the whole of it
 *
 * There is no `isProfile` flag anywhere. The profile photo is **position one**, promotion
 * is a move to the front, and removal is a removal — which is what makes *removing the
 * profile photo promotes another* a consequence rather than a second rule that could
 * disagree with the first. Two rules for one fact is how a collection ends up with two
 * photos claiming to lead, or none.
 *
 * ## Order is the player's and is never re-sorted
 *
 * Photos stay in the order they were added, minus whatever promotion moved. The order is
 * an answer — it is what `photo_ids` carries to the commit — so nothing here sorts by
 * upload state, by whether an id has arrived, or by anything else.
 *
 * ## Uploading is per photo, and a failure costs one photo
 *
 * Each photo carries its own `PhotoUpload`, so one failing leaves the other two exactly
 * where they were and gives the player one thing to retry. That is the reason uploads are
 * one request per photo rather than one request carrying three.
 *
 * No renderer, no store, no wire type: the profile editor will hold the same three photos
 * under the same rules from a screen that looks nothing like the step that collects them.
 */

import type { AppError } from '@/shared/errors';

/**
 * The most a Player profile may hold.
 *
 * A constant rather than a served bound, unlike the tag floor and ceiling: `POST
 * /players/me/profile` fixes it at three in the contract itself, and the design system's
 * row is three tiles wide because of it — so a number arriving from the server would be a
 * number two other things could not act on. The commit re-validates either way.
 */
export const PHOTO_CEILING = 3;

/** Where one photo has got to on its way into the profile. */
export type PhotoUpload =
  /** In flight. `progress` is a fraction of the stages `httpUpload` can observe. */
  | { readonly kind: 'uploading'; readonly progress: number }
  /** It did not arrive. The error is kept so the tile can say why and offer the retry. */
  | { readonly kind: 'failed'; readonly error: AppError }
  /** Stored. `photoId` is the permanent id the commit carries; the URL is not. */
  | { readonly kind: 'uploaded'; readonly photoId: string };

/**
 * One photo, from the moment it is picked until the part ends.
 *
 * `uri` is both what the tile draws and the photo's identity here. **The device's copy is
 * what is shown throughout**, including after the upload succeeds: the server hands back a
 * short-lived signed URL, and fetching one to redraw a picture already on the phone would
 * be a round trip to see something the player is looking at.
 */
export interface ProfilePhoto {
  /**
   * The local `file://` URI the picker gave.
   *
   * It is the key as well as the source. A picker copies the chosen picture into the app's
   * own storage, so two picks produce two URIs even for one photograph — and in the case
   * where a picker does hand back the same URI twice, the second copy of one picture is
   * dropped, which is the outcome that screen wanted anyway.
   */
  readonly uri: string;
  /** What the platform said the bytes are, or `null` where it said nothing. */
  readonly mimeType: string | null;
  readonly upload: PhotoUpload;
}

/**
 * What a photo is sent as when the platform did not say what it is.
 *
 * The upload route reads `Content-Type` **and nothing else** to decide whether it will
 * accept the format, then decodes the bytes themselves — so a type has to be named, and
 * naming none is not an option.
 *
 * `image/jpeg` rather than a guess from the file extension, which the picking port refuses
 * to make and is right to: an extension is a string somebody typed. This is a different
 * claim — *the platform said nothing, and what a phone hands over when it says nothing is
 * a JPEG.* An iPhone's HEIC is reported as HEIC, so the case this covers is the residue.
 * The alternative is refusing a picture the player chose because a picker was silent, and
 * a photo whose format the server genuinely will not take is refused by the server, with a
 * code the tile can say out loud.
 */
export const ASSUMED_MEDIA_TYPE = 'image/jpeg';

/** What to put in `Content-Type` for one picked image. */
export function mediaTypeOf(mimeType: string | null): string {
  return mimeType ?? ASSUMED_MEDIA_TYPE;
}

/** How many more this collection has room for. */
export function slotsLeft(photos: readonly ProfilePhoto[]): number {
  return Math.max(PHOTO_CEILING - photos.length, 0);
}

/** What one trip to the picker did. */
export interface PhotoArrival {
  readonly uri: string;
  readonly mimeType: string | null;
}

/**
 * What adding a batch of picked photos produced.
 *
 * `refused` is a **count**, in the shape `socialTagSelection` uses: the words belong to the
 * screen, and what the rule owes it is the number that makes a refusal say what happened.
 */
export interface PhotoAddition {
  readonly photos: readonly ProfilePhoto[];
  /** How many arrivals the ceiling had no room for. Zero on the ordinary path. */
  readonly refused: number;
}

/**
 * Add what the picker handed back, up to the ceiling, refusing the rest.
 *
 * The picker is opened with `slotsLeft` as its limit, so the ordinary path refuses nothing.
 * This still counts, because **a multi-select picker can hand back more than it was asked
 * for** — an iOS limited library and a picker already holding a selection both do — and a
 * row of three tiles cannot say so on its own (design-system 6.9).
 *
 * Arrivals begin `uploading` at zero. Nothing here starts an upload: a rule that reached
 * the network would not be one.
 */
export function addPhotos(
  photos: readonly ProfilePhoto[],
  arrivals: readonly PhotoArrival[],
): PhotoAddition {
  const held = new Set(photos.map((photo) => photo.uri));
  const fresh = arrivals.filter((arrival) => !held.has(arrival.uri));

  const room = slotsLeft(photos);
  const admitted = fresh.slice(0, room);

  return {
    photos: [
      ...photos,
      ...admitted.map((arrival) => ({
        uri: arrival.uri,
        mimeType: arrival.mimeType,
        upload: { kind: 'uploading', progress: 0 } as const,
      })),
    ],
    refused: fresh.length - admitted.length,
  };
}

/**
 * Make one photo the profile photo, by moving it to the front.
 *
 * Every other photo keeps its position relative to the others: promoting the third of
 * three is not a reshuffle, it is one photo stepping to the front of a queue. A photo that
 * is not held, or is already leading, leaves the collection untouched.
 */
export function promoteToProfile(
  photos: readonly ProfilePhoto[],
  uri: string,
): readonly ProfilePhoto[] {
  const promoted = photos.find((photo) => photo.uri === uri);
  if (promoted === undefined) return photos;

  return [promoted, ...photos.filter((photo) => photo !== promoted)];
}

/**
 * Drop one photo.
 *
 * Nothing promotes anything: whatever is left at position one is the profile photo, which
 * is the same sentence before and after.
 */
export function removePhoto(photos: readonly ProfilePhoto[], uri: string): readonly ProfilePhoto[] {
  return photos.filter((photo) => photo.uri !== uri);
}

/** Record where one photo's upload has got to, leaving the others alone. */
export function recordUpload(
  photos: readonly ProfilePhoto[],
  uri: string,
  upload: PhotoUpload,
): readonly ProfilePhoto[] {
  return photos.map((photo) => (photo.uri === uri ? { ...photo, upload } : photo));
}

/**
 * The ids the profile commit would carry, in the player's order.
 *
 * **Only the photos that arrived.** One still uploading has no id and one that failed has
 * nothing to name, so neither is in the draft — and a player who continues while a photo
 * is in flight commits the photos that made it rather than a placeholder that cannot be
 * resolved.
 */
export function uploadedPhotoIds(photos: readonly ProfilePhoto[]): readonly string[] {
  return photos.flatMap((photo) =>
    photo.upload.kind === 'uploaded' ? [photo.upload.photoId] : [],
  );
}

/**
 * How many are still on their way up.
 *
 * The step is free to leave while one is — an upload outlives the screen it was started
 * from, deliberately, so that pressing continue does not cancel it. **The commit is not**:
 * a photo with no id yet is a photo the one write at the end of the part cannot name, so
 * committing while one is in flight would drop a picture the player watched arrive.
 *
 * A failed one is not counted. That one is not on its way anywhere — the tile says `Failed`
 * and offers the retry — and holding the whole part shut on a photo the player has decided
 * to leave behind would make one failure cost the setup rather than the picture.
 */
export function uploadsInFlight(photos: readonly ProfilePhoto[]): number {
  return photos.filter((photo) => photo.upload.kind === 'uploading').length;
}

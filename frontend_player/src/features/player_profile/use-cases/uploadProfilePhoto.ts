/**
 * Send one picked photo, and answer with the id a profile commit will carry — and the
 * verdict the platform's on-court check reached on it.
 *
 * **The verdict is carried, never acted on here.** It changes no id, cancels no upload and
 * removes no photo: the check soft-warns, and what a warning looks like is a sentence the
 * step writes. All this does is stop the answer being thrown away between the wire and the
 * workbench, which is what it was doing.
 *
 * **One call, one photo.** Nothing here batches, queues or retries: the step owns which
 * photo is being sent and what happens when one fails, because those are decisions about a
 * row of three tiles rather than about a request.
 *
 * The upload is **not** a TanStack Query mutation, and that is deliberate. Query owns
 * server state a screen reads; this is a write whose result is one id going into a
 * client-held draft, and there is no cache entry it belongs in. Wrapping it would buy a
 * loading flag the tile already holds and a retry policy the app forbids for a
 * non-idempotent write.
 */

import { uploadPhoto } from '../api/playerProfileApi';
import { mediaTypeOf, type UploadedPhoto } from '../domain/photoCollection';
import { toUploadedPhoto } from '../mappers/playerProfileMappers';

export interface UploadProfilePhotoInput {
  /** The local `file://` URI the picking port handed over. */
  readonly uri: string;
  /** What the platform said the bytes are, or `null` where it said nothing. */
  readonly mimeType: string | null;
  /** How far along, as a fraction. Called at least once before anything is sent. */
  readonly onProgress?: (fraction: number) => void;
  readonly signal?: AbortSignal;
}

export function uploadProfilePhoto({
  uri,
  mimeType,
  onProgress,
  signal,
}: UploadProfilePhotoInput): Promise<UploadedPhoto> {
  return uploadPhoto({
    uri,
    contentType: mediaTypeOf(mimeType),
    onProgress,
    signal,
  }).then(toUploadedPhoto);
}

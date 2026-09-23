/**
 * Make these the player's photographs, in this order — the You tab's write on every change
 * to the row (ADR-0179 §2, §8).
 *
 * It takes the pairs the workbench holds — id and verdict — and sends the ids; **it answers
 * with the pairs as the profile now holds them**: the route's ids, in the route's order, each
 * carrying the verdict the workbench held for it. The route answers ids only, because the
 * verdict is the profile read's to serve, and a cache written from ids alone would lose what
 * the check said about each photo until the next read. An id the route answered that the
 * workbench never held — none, by the route's contract — carries no verdict, which is the
 * honest reading of a verdict nobody has.
 *
 * Nothing here checks the ceiling or ownership: the row did the first and the server does
 * both, under the commit's codes.
 */

import { changePhotos as putPhotos } from '../api/playerProfileApi';
import { photoIds, type UploadedPhoto } from '../domain/photoCollection';

export function changePhotos(photos: readonly UploadedPhoto[]): Promise<readonly UploadedPhoto[]> {
  return putPhotos({ photoIds: photoIds(photos) }).then((response) =>
    response.photo_ids.map((photoId) => {
      const held = photos.find((photo) => photo.photoId === photoId);
      return held?.review === undefined ? { photoId } : { photoId, review: held.review };
    }),
  );
}

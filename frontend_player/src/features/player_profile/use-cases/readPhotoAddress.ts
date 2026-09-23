/**
 * Read where one of the player's own photographs can be drawn from — the signed address
 * `GET /photos/{id}` answers — for a tile restoring a photo the profile already holds.
 *
 * A pass-through over one request and one mapper, the uniform-strict shape: the decision
 * this read makes — the address and nothing else out of the answer, never stored past the
 * screen — is the mapper's and is stated there.
 */

import { getPhoto } from '../api/playerProfileApi';
import { toPhotoAddress } from '../mappers/playerProfileMappers';

export interface ReadPhotoAddressOptions {
  readonly photoId: string;
  readonly signal?: AbortSignal;
}

export function readPhotoAddress({ photoId, signal }: ReadPhotoAddressOptions): Promise<string> {
  return getPhoto({ photoId, signal }).then(toPhotoAddress);
}

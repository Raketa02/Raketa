/**
 * The wire adapter for the Player profile. One of the two layers allowed to read generated
 * types, and the only place these paths are written down.
 *
 * Nothing here decides anything: which tags a player may hold and how many of them are
 * rules, and they live above.
 */

import type { components } from '@/generated/schema';
import { httpRequest, httpUpload, type UploadProgress } from '@/shared/lib/http';

type PlayerProfileOptionsResponse = components['schemas']['PlayerProfileOptionsResponse'];
type PhotoResponse = components['schemas']['PhotoResponse'];

export interface PlayerProfileApiOptions {
  readonly signal?: AbortSignal;
}

/**
 * The Social tag vocabulary, how many of them a profile must hold, and the Search radius
 * bounds — in one round trip, because they are the same kind of thing and the same part of
 * onboarding needs them at the same moment.
 *
 * **Unauthenticated**, as the route is: it is closed reference data about the platform and
 * carries nothing about the player. `authenticated` is stated rather than inferred here for
 * the reason the client gives — "the endpoints that take no token" is a different set from
 * "the endpoints that happen to have none right now".
 */
export function getProfileOptions({
  signal,
}: PlayerProfileApiOptions = {}): Promise<PlayerProfileOptionsResponse> {
  return httpRequest<PlayerProfileOptionsResponse>({
    method: 'GET',
    path: '/api/v1/player-profile/options',
    authenticated: false,
    signal,
  });
}

export interface UploadPhotoOptions extends PlayerProfileApiOptions {
  /** The device's own copy of the picture, as `ImagePickingPort` handed it over. */
  readonly uri: string;
  /** Sent as `Content-Type`; the route reads it and nothing else to decide the format. */
  readonly contentType: string;
  readonly onProgress?: UploadProgress;
}

/**
 * Send one photo, and get back the id a profile commit will carry.
 *
 * **One photo per request**, which is the route's shape and also the product's: a request
 * carrying three would make one failure cost all three, and the step gives a player one
 * thing to retry rather than a part to start again.
 *
 * What comes back also carries a short-lived signed URL, and this deliberately does not
 * hand it on. The picture is already on the phone — the tile is drawing it — so a URL is
 * a round trip to see what is on screen, and one that stops working besides.
 */
export function uploadPhoto({
  uri,
  contentType,
  onProgress,
  signal,
}: UploadPhotoOptions): Promise<PhotoResponse> {
  return httpUpload<PhotoResponse>({
    path: '/api/v1/photos',
    uri,
    contentType,
    authenticated: true,
    onProgress,
    signal,
  });
}

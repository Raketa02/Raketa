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
type CommitPlayerProfileRequest = components['schemas']['CommitPlayerProfileRequest'];
type PlayerProfileResponse = components['schemas']['PlayerProfileResponse'];

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

export interface CommitPlayerProfileOptions {
  readonly body: CommitPlayerProfileRequest;
  /**
   * What the client calls this commit, sent as `Idempotency-Key`.
   *
   * **Required here, not optional.** The route requires the header, and a commit sent
   * without one is the request that turns a flaky connection into a second profile — so
   * this is a parameter a caller has to have thought about rather than a default it can
   * forget.
   */
  readonly idempotencyKey: string;
}

/**
 * Every answer from onboarding's second part, in one request.
 *
 * **One write, not six.** A partial commit — the tags saved and the consent lost — is the
 * worst outcome this part has available to it, so the whole of it is one body and one
 * transaction ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 *
 * **Idempotent per key.** The same key twice creates one profile and answers 200 with the
 * body the first call produced; a *different* key against an existing profile is a second
 * commit rather than a retry and is refused. That is what makes this the one mutation in
 * the app a retry is allowed to repeat, and why the key is not this function's to invent:
 * it belongs to the part, so that a retry and the request it retries are the same request.
 *
 * The 201 and the 200 carry the same body, so nothing here branches on which arrived.
 *
 * **No `signal`**, unlike the two reads above. A cancelled write leaves the client unable to
 * say whether it landed, and this is the write the player must never be guessed at about.
 */
export function commitPlayerProfile({
  body,
  idempotencyKey,
}: CommitPlayerProfileOptions): Promise<PlayerProfileResponse> {
  return httpRequest<PlayerProfileResponse>({
    method: 'POST',
    path: '/api/v1/players/me/profile',
    body,
    authenticated: true,
    idempotencyKey,
  });
}

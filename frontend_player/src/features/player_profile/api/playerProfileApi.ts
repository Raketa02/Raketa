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
type PlayerProfileReadResponse = components['schemas']['PlayerProfileReadResponse'];
type ChangeAvailabilityRequest = components['schemas']['ChangeAvailabilityRequest'];
type AvailabilityResponse = components['schemas']['AvailabilityResponse'];
type AvailabilitySlotResource = components['schemas']['AvailabilitySlotResource'];
type ChangeSearchRadiusRequest = components['schemas']['ChangeSearchRadiusRequest'];
type SearchRadiusResponse = components['schemas']['SearchRadiusResponse'];
type WirePlayIntent = components['schemas']['PlayIntent'];
type WireSport = components['schemas']['Sport'];
/**
 * Which screen a declaration was made on — the wire's four values, re-exported.
 *
 * Aliased out of `generated/` rather than restated: it is a closed vocabulary **nothing
 * branches on**, recorded beside the fact and never read by a decision, so there is nothing
 * for a domain table to be about. A second spelling would be a table that buys documentation
 * nothing was missing and can still drift.
 */
export type PlayIntentSurface = components['schemas']['PlayIntentSurface'];
type PlayIntentDeclarationResponse = components['schemas']['PlayIntentDeclarationResponse'];

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

/**
 * The week, the radius and the per-sport Play intent — the three facts the Play screens read.
 *
 * **One round trip across two aggregates**, which is the cheaper half of a precedent ADR-0090
 * already set on `GET /users/me`: two round trips are two things that can fail on a bad
 * connection. The fourth fact a search screen needs — *which sports am I rated in* — is
 * `GET /ratings` and is deliberately not re-served here.
 *
 * It carries no `player_id`: the resource is `/players/me`, so the caller is the bearer token.
 */
export function readPlayerProfile({
  signal,
}: PlayerProfileApiOptions = {}): Promise<PlayerProfileReadResponse> {
  return httpRequest<PlayerProfileReadResponse>({
    method: 'GET',
    path: '/api/v1/players/me/profile',
    authenticated: true,
    signal,
  });
}

export interface ChangeAvailabilityOptions {
  /** Every cell still ticked, in the app's own order. The list **is** the week. */
  readonly availability: readonly AvailabilitySlotResource[];
}

/**
 * Replace this player's week. **The whole grid, every time**, and an empty list clears it.
 *
 * The list *is* the week and what is absent from it is unticked, so there is no per-cell
 * request and nothing to merge: a client that sent a delta would be describing a transition
 * the aggregate does not have.
 *
 * **A cleared week is a legal value here and a refusal at the commit**, and the asymmetry is
 * the route's rather than this app's to preserve: the floor of one ticked cell binds the
 * answer a player is *asked for* at the end of onboarding, not every later edit of it. So
 * nothing here checks the length.
 *
 * **This is where a `KEEP_THESE_TIMES` prompt is answered.** The engine notices that a search
 * ran on a week the profile does not hold and asks; nothing in the matcher writes a profile,
 * so a *yes* is this request and a *not now* is a different one entirely
 * ([#275](https://github.com/Raketa02/Raketa/issues/275)).
 *
 * **Unkeyed, and no `signal`** — the radius write's two reasons, unchanged: a `PUT` that lands
 * the same state twice has nothing to deduplicate, and a cancelled write leaves the client
 * unable to say whether it landed.
 */
export function changeAvailability({
  availability,
}: ChangeAvailabilityOptions): Promise<AvailabilityResponse> {
  const body: ChangeAvailabilityRequest = { availability: [...availability] };
  return httpRequest<AvailabilityResponse>({
    method: 'PUT',
    path: '/api/v1/players/me/availability',
    body,
    authenticated: true,
  });
}

export interface ChangeSearchRadiusOptions {
  readonly radiusKm: number;
}

/**
 * Replace this player's Search radius. **Whole kilometres, unkeyed, and idempotent.**
 *
 * A `PUT` rather than a `PATCH`, which is the shape ADR-0094 fixed for the third changeable
 * fact in this context and the shape the week beside it takes for a sharper reason: a blank
 * grid is a legal value, so `null` there would mean both *leave it alone* and *clear it*. Two
 * write shapes in one context is the thing worth avoiding, so the radius takes the same one.
 *
 * **No idempotency key**, unlike the commit: that request *creates* an aggregate out of six
 * answers and a duplicate would be a second profile, where a `PUT` that lands the same state
 * twice has nothing to deduplicate.
 *
 * **No `signal`**, for the reason the commit has none: a cancelled write leaves the client
 * unable to say whether it landed, and a search runs against whatever the profile now holds.
 */
export function changeSearchRadius({
  radiusKm,
}: ChangeSearchRadiusOptions): Promise<SearchRadiusResponse> {
  const body: ChangeSearchRadiusRequest = { search_radius_km: radiusKm };
  return httpRequest<SearchRadiusResponse>({
    method: 'PUT',
    path: '/api/v1/players/me/search-radius',
    body,
    authenticated: true,
  });
}

export interface DeclarePlayIntentOptions {
  /** The path, because the sport is half the resource's identity (ADR-0094). */
  readonly wireSport: WireSport;
  readonly intent: WirePlayIntent;
  /**
   * Which screen said so. Required, because the client is the only party that knows — and
   * safe to take its word for, because nothing branches on it.
   */
  readonly surface: PlayIntentSurface;
}

/**
 * Declare what kind of game this player wants, in one sport. **Unkeyed and idempotent.**
 *
 * `NO_PREFERENCE` is an explicit answer and there is no null: the matcher must be able to
 * tell *either kind of evening suits me* from *I never opened that screen*, and nobody is
 * ever backfilled to it (ADR-0094).
 *
 * **A declaration is not a search mode.** Mode is which tab the player is on right now and
 * has two values; this has three and is what *make this my intent* means — so the mode toggle
 * on Find a game reaches this route through nothing at all.
 */
export function declarePlayIntent({
  wireSport,
  intent,
  surface,
}: DeclarePlayIntentOptions): Promise<PlayIntentDeclarationResponse> {
  return httpRequest<PlayIntentDeclarationResponse>({
    method: 'PUT',
    path: `/api/v1/play-intents/${wireSport}`,
    body: { intent, surface },
    authenticated: true,
  });
}

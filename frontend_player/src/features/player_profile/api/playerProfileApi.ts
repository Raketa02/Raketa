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
type SetWeeklyHoursRequest = components['schemas']['SetWeeklyHoursRequest'];
type WeeklyHoursResponse = components['schemas']['WeeklyHoursResponse'];
type WeeklyHourResource = components['schemas']['WeeklyHourResource'];
type ChangeLocationRequest = components['schemas']['ChangeLocationRequest'];
type ChangeSocialTagsRequest = components['schemas']['ChangeSocialTagsRequest'];
type SocialTagsResponse = components['schemas']['SocialTagsResponse'];
type ChangePhotosRequest = components['schemas']['ChangePhotosRequest'];
type PhotosResponse = components['schemas']['PhotosResponse'];
type ChangeIntroRequest = components['schemas']['ChangeIntroRequest'];
type ChangeGenderRequest = components['schemas']['ChangeGenderRequest'];
type ChangeGenderPreferenceRequest = components['schemas']['ChangeGenderPreferenceRequest'];
type WireGender = components['schemas']['Gender'];
type WireGenderPreference = components['schemas']['GenderPreference'];
type WirePlayIntent = components['schemas']['PlayIntent'];
type WireSport = components['schemas']['Sport'];
/**
 * Which screen a declaration was made on — the wire's five values, re-exported.
 *
 * Aliased out of `generated/` rather than restated: it is a closed vocabulary **nothing
 * branches on**, recorded beside the fact and never read by a decision, so there is nothing
 * for a domain table to be about. A second spelling would be a table that buys documentation
 * nothing was missing and can still drift — and it would have had to be widened by hand when
 * `DECK` landed ([#280](https://github.com/Raketa02/Raketa/issues/280)), which is the drift
 * this alias exists to make impossible.
 */
export type PlayIntentSurface = components['schemas']['PlayIntentSurface'];
type PlayIntentDeclarationResponse = components['schemas']['PlayIntentDeclarationResponse'];

export interface PlayerProfileApiOptions {
  readonly signal?: AbortSignal;
}

/**
 * The Social tag vocabulary and how many of them a profile must hold — in one round trip,
 * because they are the same kind of thing and the same step of onboarding needs them at the
 * same moment.
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

export interface GetPhotoOptions extends PlayerProfileApiOptions {
  readonly photoId: string;
}

/**
 * A signed address for one of the caller's own photographs — what a tile on the You tab
 * draws a photo the profile already holds from, because a restored photo has no device copy.
 *
 * Short-lived and signed for one player: not an identifier, never stored past the screen.
 * `review` is always `null` on this route by design — the verdict crosses on the upload and
 * on the profile read, never here.
 */
export function getPhoto({ photoId, signal }: GetPhotoOptions): Promise<PhotoResponse> {
  return httpRequest<PhotoResponse>({
    method: 'GET',
    path: `/api/v1/photos/${photoId}`,
    authenticated: true,
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
 * **One write, not six.** A partial commit — the tags saved and the week lost — is the
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
 * The player's own profile — the week, the per-sport Play intent and every fact You draws.
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

export interface ChangeWeeklyHoursOptions {
  /** Every hour still ticked, in the app's own order. The list **is** the week. */
  readonly weeklyHours: readonly WeeklyHourResource[];
}

/**
 * Replace this player's weekly hours — *Save your week*. **The whole week, every time**, and an
 * empty list clears it.
 *
 * The list *is* the week and what is absent from it is unticked, so there is no per-cell
 * request and nothing to merge: a client that sent a delta would be describing a transition
 * the aggregate does not have.
 *
 * **A cleared week is a legal value here and a refusal at the commit**, and the asymmetry is
 * the route's rather than this app's to preserve: the floor of one ticked hour binds the
 * answer a player is *asked for* at the end of onboarding, not every later edit of it. So
 * nothing here checks the length.
 *
 * **This is where a `KEEP_THESE_TIMES` prompt is answered.** The engine notices that a search
 * ran on a week the profile does not hold and asks; nothing in the matcher writes a profile,
 * so a *yes* is this request and a *not now* is a different one entirely
 * ([#275](https://github.com/Raketa02/Raketa/issues/275)).
 *
 * **Unkeyed**, unlike the commit: that request *creates* an aggregate and a duplicate would be
 * a second profile, where a `PUT` that lands the same state twice has nothing to deduplicate.
 * **No `signal`**, as the commit has none: a cancelled write leaves the client unable to say
 * whether it landed. Every write below takes this one's two reasons.
 */
export function changeWeeklyHours({
  weeklyHours,
}: ChangeWeeklyHoursOptions): Promise<WeeklyHoursResponse> {
  const body: SetWeeklyHoursRequest = { weekly_hours: [...weeklyHours] };
  return httpRequest<WeeklyHoursResponse>({
    method: 'PUT',
    path: '/api/v1/players/me/weekly-hours',
    body,
    authenticated: true,
  });
}

export interface ChangeLocationOptions {
  readonly latitude: number;
  readonly longitude: number;
}

/**
 * Move this player's Location area to where the phone is. **The cold start's write, and no
 * screen's** ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6).
 *
 * A `204` and no body: the route rounds what it is sent to the cell about a kilometre across
 * before anything is recorded, a fix that rounds to the cell already stored records nothing
 * and still answers `204`, and no route on this surface serves the area back. What this app
 * sends is already that cell — `areaAround` is applied the moment the fix is read, as it is
 * for the commit — so the precise fix does not cross the wire either.
 *
 * **Unkeyed, and no `signal`**, for the week write's two reasons: a `PUT` that lands the
 * same state twice has nothing to deduplicate — which is what makes a write on every launch
 * free — and a cancelled write leaves the client unable to say whether it landed.
 */
export function changeLocation({ latitude, longitude }: ChangeLocationOptions): Promise<void> {
  const body: ChangeLocationRequest = { latitude, longitude };
  return httpRequest<void>({
    method: 'PUT',
    path: '/api/v1/players/me/location',
    body,
    authenticated: true,
  });
}

export interface ChangeSocialTagsOptions {
  /** Every tag the player now holds. **The list is the selection** — what is absent is dropped. */
  readonly socialTagIds: readonly string[];
}

/**
 * Replace this player's Social tags, whole
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §8). Re-checked against the served vocabulary and bounds exactly as the commit re-checks
 * them, under the commit's codes.
 *
 * It answers with the tags **in the vocabulary's order**, whatever order was sent, and that
 * is what a caller may draw — the week's rule, on the fact beside it: a client that kept what
 * it sent would hold a selection in an order the profile does not.
 *
 * **Unkeyed, and no `signal`**, for the week write's two reasons.
 */
export function changeSocialTags({
  socialTagIds,
}: ChangeSocialTagsOptions): Promise<SocialTagsResponse> {
  const body: ChangeSocialTagsRequest = { social_tags: [...socialTagIds] };
  return httpRequest<SocialTagsResponse>({
    method: 'PUT',
    path: '/api/v1/players/me/social-tags',
    body,
    authenticated: true,
  });
}

export interface ChangePhotosOptions {
  /** Ids from `POST /photos`, in the player's order — the first leads. **Empty clears.** */
  readonly photoIds: readonly string[];
}

/**
 * Replace this player's photographs, whole and **in order** (ADR-0179 §8) — the write the
 * You tab sends on **every change to the row**: a promotion, a removal, an upload that landed.
 *
 * Every id is checked to exist and to belong to the caller, exactly as the commit checks
 * them; an empty list is legal and brings the poster back. It answers with the ids as the
 * profile now holds them — ids only, because the verdict beside each is the profile read's
 * to serve, paid for once there rather than on every rearrangement here.
 *
 * **Unkeyed, and no `signal`**: a `PUT` that lands the same state twice has nothing to
 * deduplicate — which is what makes writing on every change free — and a cancelled write
 * leaves the client unable to say whether it landed.
 */
export function changePhotos({ photoIds }: ChangePhotosOptions): Promise<PhotosResponse> {
  const body: ChangePhotosRequest = { photo_ids: [...photoIds] };
  return httpRequest<PhotosResponse>({
    method: 'PUT',
    path: '/api/v1/players/me/photos',
    body,
    authenticated: true,
  });
}

export interface ChangeIntroOptions {
  /** The new line, or `null` to withdraw it. Trimmed and fenced on the far side, as the commit is. */
  readonly intro: string | null;
}

/**
 * Replace this player's intro — or withdraw it (ADR-0179 §6, the `IntroChanged` ADR-0170 §5
 * deferred to the day all three of tags, photos and intro were editable).
 *
 * **The field is required and nullable**, which is the shape of a value whose absence is a
 * real act: `null` withdraws the line, and `{}` is a 422 so that a client which forgot the
 * field cannot be clearing lines. The fence is the commit's exactly — `intro_not_admitted`
 * with `too_long`, `multiline` or `contains_contact` — and the two shape reasons are
 * pre-empted on the screen before a send, as the step pre-empts them.
 *
 * **Nothing comes back** — a `204`. The intro reaches the card, the record and its author's
 * own profile read and nowhere else, and a response that echoed the line would be a fourth
 * shape. The author reads it back from the profile read.
 *
 * **Unkeyed, and no `signal`**, for the week write's two reasons.
 */
export function changeIntro({ intro }: ChangeIntroOptions): Promise<void> {
  const body: ChangeIntroRequest = { intro };
  return httpRequest<void>({
    method: 'PUT',
    path: '/api/v1/players/me/intro',
    body,
    authenticated: true,
  });
}

export interface ChangeGenderOptions {
  readonly gender: WireGender;
}

/**
 * Correct this player's answer to the gender question — the You tab's *Save* under *About
 * you* (ADR-0179 §8). A no-op on an unchanged value, on the far side.
 *
 * **`204` and no body, deliberately.** The owner's own profile read is the one response shape
 * that carries a gender value out (ADR-0179 §4), and the contract walk holds it to being the
 * only one; the write answers nothing rather than becoming a second. The screen reads the
 * answer back from the read — which its cache already holds, so the use case says why the
 * value sent is the value held.
 *
 * **Unkeyed, and no `signal`**, for the week write's two reasons.
 */
export function changeGender({ gender }: ChangeGenderOptions): Promise<void> {
  const body: ChangeGenderRequest = { gender };
  return httpRequest<void>({
    method: 'PUT',
    path: '/api/v1/players/me/gender',
    body,
    authenticated: true,
  });
}

export interface ChangeGenderPreferenceOptions {
  readonly genderPreference: WireGenderPreference;
}

/**
 * Change who this player is willing to be matched with — the You tab's *Save* under *Who we
 * should match you with* (ADR-0179 §8). **Mutual and durable**: narrowing it hides this player
 * from the excluded side entirely, and the screen has said so at the moment of the press.
 *
 * **`204` and no body**, for the gender write's reason: the setting is served on the owner's
 * profile read and on no other shape. It gates the next search in both directions.
 *
 * **Unkeyed, and no `signal`**, for the week write's two reasons.
 */
export function changeGenderPreference({
  genderPreference,
}: ChangeGenderPreferenceOptions): Promise<void> {
  const body: ChangeGenderPreferenceRequest = { gender_preference: genderPreference };
  return httpRequest<void>({
    method: 'PUT',
    path: '/api/v1/players/me/gender-preference',
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

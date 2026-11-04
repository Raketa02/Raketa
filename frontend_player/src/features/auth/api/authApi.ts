/**
 * The wire adapter for the auth endpoints. One of the two layers allowed to read
 * generated types, and the only place these paths are written down.
 *
 * Every function is named for the operation, not for the screen that calls it, and none
 * of them decides anything: persisting tokens, opening a session and clearing a cache all
 * belong to the use-cases above.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type TokenResponse = components['schemas']['TokenResponse'];
type UserResponse = components['schemas']['UserResponse'];
type MeResponse = components['schemas']['MeResponse'];
type UserCreateRequest = components['schemas']['UserCreateRequest'];
type NameRequest = components['schemas']['NameRequest'];
type AdultAttestationRequest = components['schemas']['AdultAttestationRequest'];
type NamingResponse = components['schemas']['NamingResponse'];
type LoginRequest = components['schemas']['LoginRequest'];
type LogoutResponse = components['schemas']['LogoutResponse'];
type RefreshRequest = components['schemas']['RefreshRequest'];
type ForgotPasswordRequest = components['schemas']['ForgotPasswordRequest'];
type ClaimCodeRequest = components['schemas']['ClaimCodeRequest'];
type ClaimTicketResponse = components['schemas']['ClaimTicketResponse'];
type NewPasswordRequest = components['schemas']['NewPasswordRequest'];
type ClaimInvitationRequest = components['schemas']['ClaimInvitationRequest'];
type InvitationPasswordRequest = components['schemas']['InvitationPasswordRequest'];
type InvitationByTokenResponse = components['schemas']['InvitationByTokenResponse'];
type AccountProfilesSchema = components['schemas']['AccountProfilesSchema'];
type PushDeviceRequest = components['schemas']['PushDeviceRequest'];

export interface AuthApiOptions {
  readonly signal?: AbortSignal;
}

/** Exchange credentials for a token pair. Unauthenticated by definition. */
export function login(body: LoginRequest, { signal }: AuthApiOptions = {}): Promise<TokenResponse> {
  return httpRequest<TokenResponse>({
    method: 'POST',
    path: '/api/v1/auth/login',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * Create an account. Returns the user, **not** a token pair — signing the new player in
 * is a second call, which is why registration is a use-case rather than one request.
 */
export function register(
  body: UserCreateRequest,
  { signal }: AuthApiOptions = {},
): Promise<UserResponse> {
  return httpRequest<UserResponse>({
    method: 'POST',
    path: '/api/v1/users',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * Trade a refresh token for a fresh pair.
 *
 * `authenticated: false` is doing real work here, not just describing the endpoint: it is
 * what stops the refresh call from being refreshed. A rotation whose own 401 triggered
 * another rotation would recurse until the app fell over.
 */
export function refresh(
  body: RefreshRequest,
  { signal }: AuthApiOptions = {},
): Promise<TokenResponse> {
  return httpRequest<TokenResponse>({
    method: 'POST',
    path: '/api/v1/auth/refresh',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * The current player, per the access token.
 *
 * This doubles as session validation at launch: it is the cheapest authenticated read on
 * the player surface, and the server's answer is the only thing that can tell a live
 * session from a keychain entry that outlived a reinstall.
 */
export function me({ signal }: AuthApiOptions = {}): Promise<MeResponse> {
  return httpRequest<MeResponse>({
    method: 'GET',
    path: '/api/v1/users/me',
    authenticated: true,
    signal,
  });
}

/**
 * Name yourself — *How should people see you?* — the one act that names a player: a nickname,
 * and nothing else, repeatable at any time
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). The path
 * keeps the word *name*: what a player is called, which is the nickname.
 *
 * It answers with the nickname **as recorded** rather than with a `UserResponse`, and the refusal
 * it carries is the users context's own `nickname_already_taken`, on `details.field`, for the
 * screen to put under the box.
 */
export function nameMe(
  body: NameRequest,
  { signal }: AuthApiOptions = {},
): Promise<NamingResponse> {
  return httpRequest<NamingResponse>({
    method: 'PUT',
    path: '/api/v1/users/me/name',
    body,
    authenticated: true,
    signal,
  });
}

/**
 * **The Adult attestation, given by an account that already exists** — *Start playing*'s first
 * step ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §5). `204`, and giving it twice records nothing, so an account that attested at sign-up is
 * answered the same. Anything but `true` is refused `adult_attestation_required` on
 * `details.field` — a body this app never sends.
 */
export function postAdultAttestation(body: AdultAttestationRequest): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: '/api/v1/users/me/adult-attestation',
    body,
    authenticated: true,
  });
}

/**
 * **This phone is pushed nothing more for the signed-in player** (#559, #549's route) — the
 * sign-out's first step, because it needs the session the revoke ends. The token travels in the
 * body, never the path, so it is in no access log. `204`, also for a phone that was not registered.
 */
export function removePushDevice(
  body: PushDeviceRequest,
  { signal }: AuthApiOptions = {},
): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: '/api/v1/players/me/devices/removal',
    body,
    authenticated: true,
    signal,
  });
}

/**
 * Revoke a refresh token server-side. Documented as idempotent, which is what makes it
 * safe for sign-out to call and safe for sign-out to ignore the result.
 */
export function revokeRefreshToken(
  refreshToken: string,
  { signal }: AuthApiOptions = {},
): Promise<LogoutResponse> {
  return httpRequest<LogoutResponse>({
    method: 'POST',
    path: '/api/v1/auth/logout',
    body: { refresh_token: refreshToken },
    authenticated: false,
    signal,
  });
}

/**
 * *Forgot password?* — ask for an email with a link and an 8-character code
 * ([ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §5). Answered `202` with no body **whoever asks**: for an address with an account, without one,
 * and past the per-address throttle, which sends nothing and says so to nobody.
 */
export function forgotPassword(
  body: ForgotPasswordRequest,
  { signal }: AuthApiOptions = {},
): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: '/api/v1/auth/forgot-password',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * The email and the code, exchanged for a short-lived **ticket** the new password is set with. A
 * claim is not a use: until a password is set, the same code buys another ticket. A wrong code is
 * `code_incorrect` whatever else is true; only a right one learns it is expired, used or locked.
 */
export function claimForgotPasswordCode(
  body: ClaimCodeRequest,
  { signal }: AuthApiOptions = {},
): Promise<ClaimTicketResponse> {
  return httpRequest<ClaimTicketResponse>({
    method: 'POST',
    path: '/api/v1/auth/forgot-password/claim',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * Set the new password with **exactly one** of the link's `token` or a claimed code's `ticket`.
 * It signs out everywhere — every token issued before this moment is refused from here on — and
 * answers this session's own new pair, signed in.
 */
export function setForgottenPassword(
  body: NewPasswordRequest,
  { signal }: AuthApiOptions = {},
): Promise<TokenResponse> {
  return httpRequest<TokenResponse>({
    method: 'POST',
    path: '/api/v1/auth/forgot-password/new-password',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * ***Have an invitation code?*** — the email the club invited and the 8-character code, exchanged
 * for a short-lived **ticket** *Set your password* is sent with
 * ([ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §2, §4). The same machinery as *Forgot password?*'s claim, on the invitation's own route: a wrong
 * code is `code_incorrect` whatever else is true, and only a right one learns it is expired, used or
 * locked — or that the email has an account now, `sign_in_to_accept`.
 */
export function claimInvitationCode(
  body: ClaimInvitationRequest,
  { signal }: AuthApiOptions = {},
): Promise<ClaimTicketResponse> {
  return httpRequest<ClaimTicketResponse>({
    method: 'POST',
    path: '/api/v1/invitations/claim',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * ***Set your password*** with **exactly one** of the link's `token` or a claimed code's `ticket`.
 * A new person's account is created — no player name (the one the club typed is the
 * Administrator's), no nickname, no Adult attestation —
 * or an account the club reset gets its password back; either way it answers a signed-in session.
 */
export function setInvitationPassword(
  body: InvitationPasswordRequest,
  { signal }: AuthApiOptions = {},
): Promise<TokenResponse> {
  return httpRequest<TokenResponse>({
    method: 'POST',
    path: '/api/v1/invitations/password',
    body,
    authenticated: false,
    signal,
  });
}

/**
 * **What an invitation's link opens**, read before anything is set: the email *Set your password*
 * locks its field to, and whether the link still works. Changes nothing. The token travels in the
 * body so that it is in no access log.
 */
export function readInvitationByToken(
  token: string,
  { signal }: AuthApiOptions = {},
): Promise<InvitationByTokenResponse> {
  return httpRequest<InvitationByTokenResponse>({
    method: 'POST',
    path: '/api/v1/invitations/by-token',
    body: { token },
    authenticated: false,
    signal,
  });
}

/**
 * **Accept a pending invitation** — for the signed-in account whose email it names, with no password
 * step. Answers the account's profiles as `/users/me` would, so the switcher is drawn at once;
 * accepting again is the same answer.
 */
export function acceptInvitation(administratorId: string): Promise<AccountProfilesSchema> {
  return httpRequest<AccountProfilesSchema>({
    method: 'POST',
    path: `/api/v1/invitations/${encodeURIComponent(administratorId)}/acceptance`,
    authenticated: true,
  });
}

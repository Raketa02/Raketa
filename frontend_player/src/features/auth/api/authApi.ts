/**
 * The wire adapter for the auth endpoints. One of the two layers allowed to read
 * generated types, and the only place these paths are written down.
 *
 * Every function is named for the operation, not for the screen that calls it, and none
 * of them decides anything: persisting tokens, opening a session and clearing a cache all
 * belong to the use-cases above.
 */

import type { components } from "@/generated/schema";
import { httpRequest } from "@/shared/lib/http";

type TokenResponse = components["schemas"]["TokenResponse"];
type UserResponse = components["schemas"]["UserResponse"];
type UserCreateRequest = components["schemas"]["UserCreateRequest"];
type LoginRequest = components["schemas"]["LoginRequest"];
type LogoutResponse = components["schemas"]["LogoutResponse"];
type RefreshRequest = components["schemas"]["RefreshRequest"];

export interface AuthApiOptions {
  readonly signal?: AbortSignal;
}

/** Exchange credentials for a token pair. Unauthenticated by definition. */
export function login(
  body: LoginRequest,
  { signal }: AuthApiOptions = {},
): Promise<TokenResponse> {
  return httpRequest<TokenResponse>({
    method: "POST",
    path: "/api/v1/auth/login",
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
    method: "POST",
    path: "/api/v1/users",
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
    method: "POST",
    path: "/api/v1/auth/refresh",
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
export function me({ signal }: AuthApiOptions = {}): Promise<UserResponse> {
  return httpRequest<UserResponse>({
    method: "GET",
    path: "/api/v1/users/me",
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
    method: "POST",
    path: "/api/v1/auth/logout",
    body: { refresh_token: refreshToken },
    authenticated: false,
    signal,
  });
}

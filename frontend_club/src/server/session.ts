import 'server-only';

import { cookies } from 'next/headers';

import type { components } from '@/generated/schema';

import { seal, cookieOptions, unseal } from './seal';

/**
 * **The club's session: its token pair, sealed into one cookie** (ADR-0187 §3).
 *
 * **No token ever reaches the browser any other way**: pages get view models, and the forms get
 * refusal codes.
 *
 * Reading works anywhere on the server. Writing works only where Next allows a response to set
 * a cookie: a server action, a route handler, or the proxy (`src/proxy.ts`), which is why the
 * proxy seals and unseals through the same two functions.
 */

export const SESSION_COOKIE = 'rakieta_club_session';

/**
 * The cookie outlives any refresh token, so **the backend decides when a session ends**, not the
 * browser: a pair it will no longer rotate is refused, and the refusal clears the cookie.
 */
const TTL_SECONDS = 30 * 24 * 60 * 60;

export interface ClubSession {
  readonly accessToken: string;
  readonly refreshToken: string;
  /** Epoch milliseconds at which the access token lapses, from the pair's `expires_in`. */
  readonly expiresAt: number;
  /** Epoch milliseconds at which the pair was issued: a pair refused this young is not renewed again. */
  readonly issuedAt: number;
}

type TokenResponse = components['schemas']['TokenResponse'];

export function sessionFromPair(pair: TokenResponse, now: number = Date.now()): ClubSession {
  return {
    accessToken: pair.access_token,
    refreshToken: pair.refresh_token,
    expiresAt: now + pair.expires_in * 1000,
    issuedAt: now,
  };
}

export function sessionCookieOptions() {
  return cookieOptions(TTL_SECONDS);
}

export function sealSession(session: ClubSession): Promise<string> {
  return seal(session, TTL_SECONDS);
}

/** `null` for anything that is not a session this server sealed. */
export async function unsealSession(sealed: string): Promise<ClubSession | null> {
  const data = await unseal(sealed, TTL_SECONDS);
  if (data === null) return null;
  const { accessToken, refreshToken, expiresAt, issuedAt } = data;
  if (typeof accessToken !== 'string' || typeof refreshToken !== 'string') return null;
  if (typeof expiresAt !== 'number' || typeof issuedAt !== 'number') return null;
  return { accessToken, refreshToken, expiresAt, issuedAt };
}

export async function readSession(): Promise<ClubSession | null> {
  const sealed = (await cookies()).get(SESSION_COOKIE)?.value;
  return sealed === undefined ? null : unsealSession(sealed);
}

/** Server actions and route handlers only. */
export async function saveSession(session: ClubSession): Promise<void> {
  (await cookies()).set(SESSION_COOKIE, await sealSession(session), sessionCookieOptions());
}

/** Server actions and route handlers only. */
export async function endSession(): Promise<void> {
  (await cookies()).delete({ name: SESSION_COOKIE, path: '/' });
}

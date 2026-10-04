import 'server-only';

import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

import type { components } from '@/generated/schema';

import { bearer, clubApi, type ClubApi } from './backend';
import { settle, type FetchResult, type Outcome } from './outcome';
import { refreshOnce } from './refresh';
import { endSession, readSession, saveSession, sessionFromPair } from './session';

/**
 * **The three ways a feature reaches the backend**, and the only ones: a call nobody is signed in
 * for, a read while a page renders, and a write from a server action.
 *
 * - **{@link anonymously}**: signing up, signing in, *Forgot password?*.
 * - **{@link readAsClub}**: a server component's read. A render cannot set a cookie, so on a 401
 *   it hands the page to **`/session/renew`**, a route handler that can: it renews the pair
 *   through the single flight and comes straight back ({@link renewSession}). The proxy renews a
 *   lapsing pair before the render, so the hop is for a 401 the clock did not see coming.
 * - **{@link writeAsClub}**: a server action's write, which can set a cookie, and so does
 *   **401 → refresh → retry** in place, once.
 *
 * A pair refused while under {@link FRESH_MS} old is not renewed again: it was just issued, so
 * renewing it would only go round. Every signed-in call without a session goes to sign-in, and so
 * does every one the backend has stopped accepting, with the note that says so.
 */

type AuthInit = ReturnType<typeof bearer>;

export const SIGN_IN_PATH = '/sign-in';
/** Where a session the backend stopped accepting lands: sign-in, saying so. */
export const SESSION_ENDED_PATH = '/sign-in?session=ended';
/** Where a renewal nobody answered lands: sign-in, saying so, with the cookie kept. */
export const SESSION_UNREACHABLE_PATH = '/sign-in?session=unreachable';
/** The route handlers a render hands a refused pair to (src/app/session/). */
export const RENEW_PATH = '/session/renew';
export const END_PATH = '/session/end';
/** The request's own path and query, stamped by the proxy on the way in. */
export const PATH_HEADER = 'x-club-path';
const HOME_PATH = '/overview';

/**
 * Longer than a renewal's round trip back to the page, so a refused renewed pair ends the session
 * instead of renewing again. A browser also stops any redirect loop after about twenty hops.
 */
const FRESH_MS = 5_000;

/**
 * A path to go back to after a renewal: this site's own, or Overview. `/session/renew?to=` is
 * a link anybody can write, so `//elsewhere` and `/\elsewhere` are refused.
 */
export function returnPath(raw: string | null | undefined): string {
  if (raw === null || raw === undefined || !raw.startsWith('/')) return HOME_PATH;
  if (raw.startsWith('//') || raw.startsWith('/\\')) return HOME_PATH;
  if (raw.startsWith('/session/')) return HOME_PATH;
  return raw;
}

export function anonymously<T>(
  call: (api: ClubApi) => Promise<FetchResult<T>>,
): Promise<Outcome<T>> {
  return settle(() => call(clubApi()));
}

export async function readAsClub<T>(
  call: (api: ClubApi, auth: AuthInit) => Promise<FetchResult<T>>,
): Promise<Outcome<T>> {
  const session = await readSession();
  if (session === null) redirect(SIGN_IN_PATH);

  const outcome = await settle(() => call(clubApi(), bearer(session.accessToken)));
  if (!outcome.ok && outcome.error.status === 401) {
    if (Date.now() - session.issuedAt < FRESH_MS) redirect(END_PATH);
    const here = returnPath((await headers()).get(PATH_HEADER));
    redirect(`${RENEW_PATH}?to=${encodeURIComponent(here)}`);
  }
  return outcome;
}

export async function writeAsClub<T>(
  call: (api: ClubApi, auth: AuthInit) => Promise<FetchResult<T>>,
): Promise<Outcome<T>> {
  const session = await readSession();
  if (session === null) redirect(SIGN_IN_PATH);

  const first = await settle(() => call(clubApi(), bearer(session.accessToken)));
  if (first.ok || first.error.status !== 401) return first;

  const refreshed = await refreshOnce(session.refreshToken);
  if (refreshed.kind === 'unreachable') return { ok: false, error: refreshed.error };
  if (refreshed.kind === 'refused') {
    await endSession();
    redirect(SESSION_ENDED_PATH);
  }

  await saveSession(refreshed.session);
  const retried = await settle(() => call(clubApi(), bearer(refreshed.session.accessToken)));
  if (!retried.ok && retried.error.status === 401) {
    await endSession();
    redirect(SESSION_ENDED_PATH);
  }
  return retried;
}

/**
 * **Renew the session for a render that was refused**, from `/session/renew`: where to go next.
 * Renewed, back where the render was. Refused, the session is over and the cookie goes. Nobody
 * answered, sign-in says so and the cookie stays, since nothing is concluded from silence.
 */
export async function renewSession(to: string): Promise<string> {
  const session = await readSession();
  if (session === null) return SIGN_IN_PATH;
  const refreshed = await refreshOnce(session.refreshToken);
  switch (refreshed.kind) {
    case 'renewed':
      await saveSession(refreshed.session);
      return returnPath(to);
    case 'refused':
      await endSession();
      return SESSION_ENDED_PATH;
    case 'unreachable':
      return SESSION_UNREACHABLE_PATH;
  }
}

/** End a session the backend refused though it was just issued, from `/session/end`. */
export async function endRefusedSession(): Promise<string> {
  await endSession();
  return SESSION_ENDED_PATH;
}

/** Begin a session with a pair the backend just issued: signing in, or setting a password. */
export async function beginSession(pair: components['schemas']['TokenResponse']): Promise<void> {
  await saveSession(sessionFromPair(pair));
}

/**
 * **Sign out**: revoke the refresh token, then forget the cookie. The backend's answer is not
 * waited on for anything; its sign-out is idempotent, and a club asking to leave leaves.
 */
export async function signOutClub(): Promise<void> {
  const session = await readSession();
  if (session !== null) {
    await anonymously((api) =>
      api.POST('/api/v1/club/auth/logout', { body: { refresh_token: session.refreshToken } }),
    );
  }
  await endSession();
}

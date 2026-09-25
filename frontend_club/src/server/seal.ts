import 'server-only';

import { sealData, unsealData } from 'iron-session';

import { loadConfig } from './config';

/**
 * **The seal both of the site's cookies use**: iron-session's, keyed by `SESSION_SECRET`, and the
 * attributes they share. `httpOnly`, so the browser carries them without reading them;
 * `SameSite=Lax`; `Secure` everywhere but `local` (ADR-0187 §6).
 */

export function sealedCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: 'lax' as const,
    secure: loadConfig().environment !== 'local',
    path: '/',
    maxAge,
  };
}

export function seal(data: object, ttlSeconds: number): Promise<string> {
  return sealData(data, { password: loadConfig().sessionSecret, ttl: ttlSeconds });
}

/** What was sealed, field by field as `unknown`, or `null` for anything this server did not seal. */
export async function unseal(
  sealed: string,
  ttlSeconds: number,
): Promise<Readonly<Record<string, unknown>> | null> {
  try {
    return await unsealData<Record<string, unknown>>(sealed, {
      password: loadConfig().sessionSecret,
      ttl: ttlSeconds,
    });
  } catch {
    return null;
  }
}

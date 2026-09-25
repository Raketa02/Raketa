import 'server-only';

import { cookies } from 'next/headers';

import { seal, sealedCookieOptions, unseal } from './seal';

/**
 * **Forgot password?'s own cookie**: what one recovery carries between its pages.
 *
 * The email asked with, so the code page can offer it back, and, once a right code is claimed,
 * the **ticket** the new password is set with. The ticket is a credential, so it is sealed like
 * the session and never reaches the browser; the cookie lasts only as long as the backend said
 * the ticket would. Nothing here is a session: a recovery signs nobody in until the password is
 * set.
 */

export const RECOVERY_COOKIE = 'raketa_club_recovery';

/** A code lasts an hour (ADR-0184 §3), so a recovery has no reason to outlive one. */
const RECOVERY_SECONDS = 60 * 60;

export interface Recovery {
  readonly email: string;
  readonly ticket?: string;
}

export async function readRecovery(): Promise<Recovery | null> {
  const sealed = (await cookies()).get(RECOVERY_COOKIE)?.value;
  const data = sealed === undefined ? null : await unseal(sealed, RECOVERY_SECONDS);
  if (data === null || typeof data.email !== 'string') return null;
  return typeof data.ticket === 'string'
    ? { email: data.email, ticket: data.ticket }
    : { email: data.email };
}

/** `seconds` bounds the cookie: the ticket's own `expires_in` once there is one. */
export async function saveRecovery(
  recovery: Recovery,
  seconds: number = RECOVERY_SECONDS,
): Promise<void> {
  const maxAge = Math.max(1, Math.min(seconds, RECOVERY_SECONDS));
  const sealed = await seal(recovery, RECOVERY_SECONDS);
  (await cookies()).set(RECOVERY_COOKIE, sealed, sealedCookieOptions(maxAge));
}

export async function endRecovery(): Promise<void> {
  (await cookies()).delete({ name: RECOVERY_COOKIE, path: '/' });
}

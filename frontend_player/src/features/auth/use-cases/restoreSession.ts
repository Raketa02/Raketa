/**
 * Launch: decide whether the credentials on this device are a session.
 *
 * **A token existing is not proof a session exists.** iOS Keychain data survives an
 * uninstall and reinstall, so a fresh install can start life holding a credential the
 * backend retired months ago. The only authority on whether it still works is the
 * backend, so this asks — with the cheapest authenticated read on the player surface.
 */

import {
  endSession,
  readStoredTokens,
  setSessionStatus,
  type SessionStatus,
} from '@/shared/lib/auth';
import { AppError } from '@/shared/errors';

import { me } from '../api/authApi';
import type { AuthenticatedUser } from '../domain/AuthenticatedUser';
import { toAuthenticatedUser } from '../mappers/authMappers';

export interface RestoredSession {
  readonly status: Extract<SessionStatus, 'authenticated' | 'unauthenticated'>;
  /**
   * The validated player, when the server answered. Handed back so bootstrap can seed
   * the Query cache with it — the profile is backend data and Query owns it, so this is
   * a response-driven cache write, never a second copy held by the session.
   */
  readonly user?: AuthenticatedUser;
}

/**
 * Three outcomes, and the third is the one that is easy to get wrong.
 *
 * | What happened                        | What it means                          |
 * |--------------------------------------|----------------------------------------|
 * | No stored credentials                | Nobody is signed in.                    |
 * | The server rejected the token        | The session is genuinely over.          |
 * | The server never answered            | We learned nothing. Keep the session.   |
 *
 * That third row is the lift, the train, the tunnel. Signing a player out because a
 * request timed out destroys a perfectly valid session and costs them their password —
 * and the architecture is explicit that unreachable is not the same as rejected.
 *
 * So an unanswered validation keeps the credentials and opens the session optimistically.
 * That is not the check being skipped: it is the check being *answered later*. The first
 * real request of the session re-asks the same question, and #22's rotation turns a
 * genuine rejection into a single clean sign-out. The failure mode of guessing wrong here
 * is one screen showing a retry; the failure mode of guessing wrong the other way is a
 * signed-in player thrown back to a login form every time a tunnel swallows a request.
 */
export async function restoreSession(): Promise<RestoredSession> {
  const tokens = await readStoredTokens();

  if (tokens === undefined) {
    setSessionStatus('unauthenticated');
    return { status: 'unauthenticated' };
  }

  try {
    const user = toAuthenticatedUser(await me());
    setSessionStatus('authenticated');
    return { status: 'authenticated', user };
  } catch (error) {
    if (error instanceof AppError && error.invalidatesSession) {
      // Rejected. The credentials are dead — destroy them rather than carry them into a
      // session that will fail on its first request.
      await endSession('session-invalidated');
      return { status: 'unauthenticated' };
    }

    // Unreachable, timed out, or the server itself failed. None of those say anything
    // about whether this session is valid.
    setSessionStatus('authenticated');
    return { status: 'authenticated' };
  }
}

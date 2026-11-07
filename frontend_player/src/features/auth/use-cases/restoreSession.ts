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
  getSessionStatus,
  readStoredTokens,
  setSessionStatus,
  type SessionStatus,
} from '@/shared/lib/auth';
import { AppError } from '@/shared/errors';

import type { AuthenticatedUser } from '../domain/AuthenticatedUser';

export interface RestoredSession {
  readonly status: Extract<SessionStatus, 'authenticated' | 'unauthenticated'>;
  /**
   * The validated player, when the server answered. The read handed in has already left
   * it in the Query cache — the profile is backend data and Query owns it — so this is the
   * answer as the caller learnt it, never a second copy held by the session.
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
 *
 * **The read is handed in**, and it is `/users/me` through the Query cache
 * (`fetchCurrentUserAtLaunch`): this is pure session logic and may not know a data-fetching
 * library, while the read's two answers both belong in the cache the entry gate reads — the
 * player, so the first screen asks nothing, and the failure, so the gate opens on it instead
 * of asking again behind an empty screen.
 */
export async function restoreSession(
  readThePlayer: () => Promise<AuthenticatedUser>,
): Promise<RestoredSession> {
  const tokens = await readStoredTokens();

  if (tokens === undefined) {
    setSessionStatus('unauthenticated');
    return { status: 'unauthenticated' };
  }

  try {
    const user = await readThePlayer();
    setSessionStatus('authenticated');
    return { status: 'authenticated', user };
  } catch (error) {
    if (error instanceof AppError && error.invalidatesSession) {
      // Rejected. The credentials are dead — destroy them rather than carry them into a
      // session that will fail on its first request.
      await endSession('session-invalidated');
      return { status: 'unauthenticated' };
    }

    // **Ended under the read.** A rejected refresh ends the session where it is learnt, and
    // that teardown cancels every query in flight — this read among them — so what arrives
    // here is the cancellation rather than the 401 behind it. The session machine already
    // holds the verdict; opening the session again would hand the gate a status with no
    // credentials behind it.
    if (getSessionStatus() === 'unauthenticated') return { status: 'unauthenticated' };

    // Unreachable, timed out, or the server itself failed. None of those say anything
    // about whether this session is valid.
    setSessionStatus('authenticated');
    return { status: 'authenticated' };
  }
}

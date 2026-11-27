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
import type { Reachability } from '@/shared/lib/platform';

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
 * Three outcomes, and a fourth that is the third learnt early — and the third is the one that is
 * easy to get wrong.
 *
 * | What happened                        | What it means                          |
 * |--------------------------------------|----------------------------------------|
 * | No stored credentials                | Nobody is signed in.                    |
 * | The server rejected the token        | The session is genuinely over.          |
 * | The server never answered            | We learned nothing. Keep the session.   |
 * | The phone already knows it's offline | Nothing to learn. Keep it, don't ask.   |
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
 *
 * **The fourth row is the third, asked of the phone first** (ADR-0209 §4). On a captive portal or
 * a *connected, no internet* network the phone already knows the check cannot succeed, and sending
 * it only waits out the `launch` budget to learn so. So **reachability is handed in too**, read once
 * before the check — the online manager's belief, from the network-state module, which a use-case
 * may not import — and on `unreachable` the check is not sent and the session is kept. **Nothing
 * is written**: no synthesised failure in the cache, so the gate's own read pauses on the online
 * manager, which already agrees, and the gate says *Waiting for a connection* and moves on by
 * itself when the connection returns. `undecided` and a read that fails are no reason to skip:
 * the check goes exactly as it did before.
 */
export async function restoreSession(
  readThePlayer: () => Promise<AuthenticatedUser>,
  readReachability: () => Promise<Reachability>,
): Promise<RestoredSession> {
  const tokens = await readStoredTokens();

  if (tokens === undefined) {
    setSessionStatus('unauthenticated');
    return { status: 'unauthenticated' };
  }

  if (await phoneKnowsItIsOffline(readReachability)) {
    setSessionStatus('authenticated');
    return { status: 'authenticated' };
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

/**
 * Only a known `unreachable` skips the check; a read that fails says nothing about the network.
 * **The launch's one offline rule** (ADR-0209 §4): Home's warm-up, which starts once this has
 * resolved, skips its reads on it too (#874), so the two never disagree about the phone.
 */
export async function phoneKnowsItIsOffline(
  readReachability: () => Promise<Reachability>,
): Promise<boolean> {
  try {
    return (await readReachability()) === 'unreachable';
  } catch {
    return false;
  }
}

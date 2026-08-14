/**
 * Sign out — a system operation, not a redirect.
 *
 * The revoke is here rather than in `endSession` because it speaks the wire, and it runs
 * *first* because it needs the refresh token that `endSession` is about to destroy.
 */

import { endSession, getRefreshToken } from "@/shared/lib/auth";

import { revokeRefreshToken } from "../api/authApi";

/**
 * Revoke server-side, then tear the local session down.
 *
 * **The revoke is best-effort and its failure is swallowed.** A player who taps sign out
 * on a train has decided to leave; refusing because the server is unreachable would
 * strand them inside an account they asked to exit — and would leave a device holding
 * live credentials, which is the outcome the revoke exists to prevent. The refresh token
 * is destroyed locally either way, and it expires server-side on its own.
 *
 * This is the "defined product policy" the architecture insists on rather than leaving
 * accidental: local credentials always go, whatever the server said.
 */
export async function signOut(): Promise<void> {
  const refreshToken = getRefreshToken();

  if (refreshToken !== undefined) {
    try {
      await revokeRefreshToken(refreshToken);
    } catch {
      // Deliberately ignored — see above. Never log the token or the failure's payload.
    }
  }

  await endSession("requested");
}

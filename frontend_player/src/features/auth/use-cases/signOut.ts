/**
 * Sign out — a system operation, not a redirect.
 *
 * Two acts speak the wire before the local teardown, and both run *first* because each needs
 * something `endSession` is about to destroy: **this phone is let go** (#559) — the signed-in
 * player's notices stop being pushed to it, which needs the access token — and **the refresh token
 * is revoked**, which needs the refresh token.
 */

import { endSession, getRefreshToken } from '@/shared/lib/auth';
import type { PushPort } from '@/shared/lib/platform';

import { removePushDevice, revokeRefreshToken } from '../api/authApi';

/**
 * Let the phone go and revoke server-side — side by side, so an offline sign-out waits for one
 * timeout rather than two — then tear the local session down.
 *
 * **Both server acts are best-effort and their failures are swallowed.** A player who taps sign out
 * on a train has decided to leave; refusing because the server is unreachable would strand them
 * inside an account they asked to exit — and would leave a device holding live credentials, which
 * is the outcome the revoke exists to prevent. The refresh token is destroyed locally either way,
 * and it expires server-side on its own.
 *
 * This is the "defined product policy" the architecture insists on rather than leaving
 * accidental: local credentials always go, whatever the server said.
 *
 * **The phone is let go whatever its permission says now**: one registered while it allowed
 * notifications and switched off in Settings since would, switched on again with nobody signed in,
 * show the last player's notices. A phone with no token to give was never registered. **A phone that
 * could not be let go is still pushed the last player's notices** — until somebody signs in on it,
 * when the backend moves it to them, or until Expo reports it gone.
 *
 * @param phone the push port — the sign-out reads which token this phone is pushed by.
 */
export async function signOut(phone: PushPort): Promise<void> {
  await Promise.all([letThePhoneGo(phone), revoke()]);
  await endSession('requested');
}

async function letThePhoneGo(phone: PushPort): Promise<void> {
  try {
    const token = await phone.readToken();
    if (token !== null) await removePushDevice({ token });
  } catch {
    // Deliberately ignored — see above. Never log the token.
  }
}

async function revoke(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (refreshToken === undefined) return;
  try {
    await revokeRefreshToken(refreshToken);
  } catch {
    // Deliberately ignored — see above. Never log the token or the failure's payload.
  }
}

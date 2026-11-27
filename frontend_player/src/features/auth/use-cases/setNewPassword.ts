/**
 * *Set a new password* — by the email's link or by a claimed code — **and be signed in**.
 *
 * The server signs out everywhere and answers this session's own pair
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §7), so the rest is `signIn`'s: `beginSession` persists the pair *before* flipping the status,
 * and the `(auth)` guard sees an authenticated session and hands it to the entry gate. Another
 * phone still holding the old pair finds out on its next request — its access token is refused as
 * `access_token_revoked`, its refresh token as revoked, and the http client's rotation ends that
 * session there.
 *
 * `readAccount` runs before the status opens, as `signIn`'s does: the form's button turns while
 * the gate's first read is out, rather than the gate drawing nothing while it asks
 * (`docs/specs/busy-indicator/decisions.md` §3.1).
 */

import { beginSession } from '@/shared/lib/auth';

import { setForgottenPassword } from '../api/authApi';
import type { NewPassword } from '../domain/passwordReset';
import { toTokens } from '../mappers/authMappers';

export async function setNewPassword(
  { key, password }: NewPassword,
  readAccount: () => Promise<unknown>,
): Promise<void> {
  const wire = await setForgottenPassword(
    key.via === 'link' ? { token: key.token, password } : { ticket: key.ticket, password },
  );

  await beginSession(toTokens(wire), readAccount);
}

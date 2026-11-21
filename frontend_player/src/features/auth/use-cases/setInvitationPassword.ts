/**
 * ***Set your password*** — by the invitation's link or by a claimed code — **and be signed in**.
 *
 * `setNewPassword`'s shape: the server answers this session's own pair, `beginSession` persists it
 * *before* flipping the status, and the `(auth)` guard hands the session to the entry gate — which
 * sends an account that only administers to its area (ADR-0185 §3). Nothing here navigates.
 *
 * `readAccount` runs before the status opens, as `signIn`'s does: the form's button turns while
 * the gate's first read is out, rather than the gate drawing nothing while it asks
 * (`docs/specs/busy-indicator/decisions.md` §3.1).
 */

import { beginSession } from '@/shared/lib/auth';

import { setInvitationPassword as setOnTheWire } from '../api/authApi';
import type { InvitationPassword } from '../domain/invitation';
import { toTokens } from '../mappers/authMappers';

export async function setInvitationPassword(
  { key, password }: InvitationPassword,
  readAccount: () => Promise<unknown>,
): Promise<void> {
  const wire = await setOnTheWire(
    key.via === 'link' ? { token: key.token, password } : { ticket: key.ticket, password },
  );

  await beginSession(toTokens(wire), readAccount);
}

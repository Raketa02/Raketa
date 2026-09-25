/**
 * The email and the 8-character code, exchanged for the ticket *Set a new password* is sent with.
 */

import { claimForgotPasswordCode } from '../api/authApi';
import type { ResetCodeClaim } from '../domain/passwordReset';
import { toResetTicket } from '../mappers/authMappers';

export async function claimResetCode(claim: ResetCodeClaim): Promise<string> {
  const wire = await claimForgotPasswordCode({ email: claim.email, code: claim.code });
  return toResetTicket(wire);
}

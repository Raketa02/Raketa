/**
 * ***Have an invitation code?*** — the email the club invited and the code from its email,
 * exchanged for the ticket *Set your password* is sent with.
 */

import { claimInvitationCode as claimOnTheWire } from '../api/authApi';
import type { InvitationCodeClaim } from '../domain/invitation';
import { toClaimTicket } from '../mappers/authMappers';

export async function claimInvitationCode(claim: InvitationCodeClaim): Promise<string> {
  const wire = await claimOnTheWire({ email: claim.email, code: claim.code });
  return toClaimTicket(wire);
}

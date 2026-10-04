import 'server-only';

import { appRoute } from '@/features/get-the-app/mappers';
import { isAToken } from '@/features/set-password/schemas';
import { fromBackend } from '@/server/backend';

import { toInvitation, type Invitation } from './mappers';

/**
 * **What an invitation's link opens**, or `null` when it leads nowhere: a link never issued as an
 * invitation (`credential_not_found`), or a token that could be nobody's. Reading it changes
 * nothing, whatever its state. The token travels in a body, so it is in no backend access log.
 * Any other answer is a failure the error page reports.
 */
export async function readInvitation(linkToken: string): Promise<Invitation | null> {
  if (!isAToken(linkToken)) return null;
  const outcome = await fromBackend((api) =>
    api.POST('/api/v1/public/invitations/by-token', { body: { token: linkToken } }),
  );
  if (outcome.ok) return toInvitation(outcome.data);
  if (outcome.error.code === 'credential_not_found') return null;
  throw new Error(`An invitation's link could not be read: ${outcome.error.code}`);
}

/**
 * The app's route for the page: `invite/<token>` while the link can still be used in the app, and
 * the app's own start once it can't, where the person signs in. Only for a token
 * {@link readInvitation} found an invitation for, which is URL-safe letters.
 */
export function invitationRoute(linkToken: string, invitation: Invitation): string {
  return invitation.state === 'valid' ? appRoute('invitation', linkToken) : '';
}

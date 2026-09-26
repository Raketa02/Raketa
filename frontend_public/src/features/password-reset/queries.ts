import 'server-only';

import { appRoute } from '@/features/get-the-app/mappers';
import { isAToken } from '@/features/set-password/schemas';
import { fromBackend } from '@/server/backend';

import { toResetLink, type ResetLink } from './mappers';

/**
 * **What a reset's link opens**, or `null` when it leads nowhere: a link never issued as a
 * player's or an administrator's reset (`credential_not_found`; a club's lives on the club
 * website), or a token that could be nobody's. Reading it changes nothing. The token travels in a
 * body, so it is in no backend access log. Any other answer is a failure the error page reports.
 */
export async function readResetLink(linkToken: string): Promise<ResetLink | null> {
  if (!isAToken(linkToken)) return null;
  const outcome = await fromBackend((api) =>
    api.POST('/api/v1/public/password-resets/by-token', { body: { token: linkToken } }),
  );
  if (outcome.ok) return toResetLink(outcome.data);
  if (outcome.error.code === 'credential_not_found') return null;
  throw new Error(`A reset's link could not be read: ${outcome.error.code}`);
}

/**
 * The app's route for the page: `reset/<token>` while the link can still be used in the app, and
 * the app's own start once it can't. Only for a token {@link readResetLink} found a reset for.
 */
export function resetRoute(linkToken: string, link: ResetLink): string {
  return link.state === 'valid' ? appRoute('reset', linkToken) : '';
}

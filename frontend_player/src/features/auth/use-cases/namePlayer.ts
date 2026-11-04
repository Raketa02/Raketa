/**
 * The naming — *How should people see you?* — as one workflow.
 *
 * One request, and still a use-case rather than a bare `api/` call, because what comes back is
 * the server's: the nickname **as recorded**, and the caller is handed that rather than what was
 * typed. Nothing here normalises on its own: the value object is the server's, and a copy of its
 * rule on this side would be the second authority the auth feature refuses to be.
 *
 * The refusal for a taken handle arrives as `nickname_already_taken` on `details.field`, and it
 * is left to surface exactly as the sign-up conflicts always did — under the box it names.
 */

import { nameMe } from '../api/authApi';
import type { Naming } from '../domain/AuthenticatedUser';
import { toNaming } from '../mappers/authMappers';

export async function namePlayer(naming: Naming): Promise<Naming> {
  return toNaming(await nameMe({ nickname: naming.nickname }));
}

/** **What an invitation's link opens**, before anything is set — the address and whether it works. */

import { readInvitationByToken } from '../api/authApi';
import type { InvitationLink } from '../domain/invitation';
import { toInvitationLink } from '../mappers/authMappers';

export async function readInvitationLink(
  token: string,
  { signal }: { readonly signal?: AbortSignal } = {},
): Promise<InvitationLink> {
  return toInvitationLink(await readInvitationByToken(token, { signal }));
}

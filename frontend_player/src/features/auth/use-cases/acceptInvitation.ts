/**
 * **Accept a club's invitation** — the signed-in account whose email it names takes the
 * administrator profile, with no password step (ADR-0184 §2). The answer is the account's profiles
 * as `/users/me` would give them, so the switcher can be drawn from it at once.
 */

import { acceptInvitation as acceptOnTheWire } from '../api/authApi';
import type { AccountProfiles } from '../domain/AuthenticatedUser';
import { toAccountProfiles } from '../mappers/authMappers';

export async function acceptInvitation(administratorId: string): Promise<AccountProfiles> {
  return toAccountProfiles(await acceptOnTheWire(administratorId));
}

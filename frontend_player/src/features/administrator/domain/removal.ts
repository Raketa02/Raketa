/**
 * **Where an account goes once its club has removed it** (PRD #500 story 136, ADR-0184 §7,
 * ADR-0185 §3): *moved to my player profile, or signed out if I have none*.
 *
 * What is left is the account's profiles **without the club that removed it** — the profile read
 * may not have caught up yet, since a removal is usually first heard as a refused administrator
 * request. An account that also plays goes to its player side, which is where a launch opens an
 * account holding both; one that still runs another club's groups goes to that club's area; one
 * with nothing left is signed out.
 */

import type { HeldProfiles, ProfileChoice } from '@/features/auth/types';

/**
 * **The profile to switch to, or nothing left** — a switch like the switcher's, so the phone keeps
 * it and the next launch agrees (#518).
 */
export type AfterRemoval = ProfileChoice | { readonly kind: 'sign-out' };

export function afterRemoval(profiles: HeldProfiles, removedClubId: string): AfterRemoval {
  if (profiles.actsAsPlayer) return { kind: 'player' };
  const other = profiles.administers.find((club) => club.clubId !== removedClubId);
  return other === undefined
    ? { kind: 'sign-out' }
    : { kind: 'administrator', clubId: other.clubId };
}

/**
 * **Whether this account may be in this club's administrator area** — read off the signed-in
 * player, whose profiles name every club it administers (ADR-0185 §2).
 *
 * The server is the authority: every administrator route asks again and refuses a removed
 * Administrator (`useRemovalWatch`). This is the area's door, not its lock — it keeps a route
 * nobody should be on from drawing a screen that could only be refused, and it is where the
 * club's name every header says comes from, without a read of its own: the player read is seeded
 * at launch and the entry gate waited for it before sending anybody here.
 */

import { useCurrentUser, type AdministeredClub } from '@/features/auth/types';

export type AreaAccess =
  /** The player read has not answered. Nothing is drawn — the gate's rule. */
  | { readonly kind: 'pending' }
  /** Not this account's club, or the read could not say: the entry gate decides where to go. */
  | { readonly kind: 'elsewhere' }
  | { readonly kind: 'open'; readonly club: AdministeredClub };

export function useAreaAccess(clubId: string): AreaAccess {
  const user = useCurrentUser();

  if (user.data === undefined) {
    return user.isPending && user.fetchStatus === 'fetching'
      ? { kind: 'pending' }
      : { kind: 'elsewhere' };
  }

  const club = user.data.profiles.administers.find((held) => held.clubId === clubId);
  return club === undefined ? { kind: 'elsewhere' } : { kind: 'open', club };
}

/** The club's name, for a screen inside an area already open — `''` in the one frame it could not be. */
export function useAreaClubName(clubId: string): string {
  const access = useAreaAccess(clubId);
  return access.kind === 'open' ? access.club.clubName : '';
}

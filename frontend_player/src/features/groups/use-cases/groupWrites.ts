/**
 * **The feature's two writes** — creating a Player group, and joining one (or asking to).
 *
 * No rule is applied here that the server does not apply again: *Create the group* is only
 * pressable once the form's schema answers a group (`newGroupFrom`), and the server refuses the
 * same two fields by name. What comes back is the canonical answer, mapped, for the hook to write into the cache.
 */

import { postGroup, postMembership } from '../api/groupsApi';
import type { Group, GroupAtClub, NewGroup } from '../domain/group';
import { toGroup, toGroupAtClub } from '../mappers/groupMappers';

/** The reader becomes the group's Owner and first member; the answer is the group as its page reads it. */
export async function createGroup(group: NewGroup): Promise<Group> {
  return toGroup(
    await postGroup({
      name: group.name,
      home_club_id: group.homeClubId,
      join_policy: group.joinPolicy,
    }),
  );
}

/** Join, or ask to — the answer's relation says which happened. */
export async function joinGroup(groupId: string): Promise<GroupAtClub> {
  return toGroupAtClub(await postMembership(groupId));
}

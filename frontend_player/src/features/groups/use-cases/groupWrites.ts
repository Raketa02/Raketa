/**
 * **The feature's writes** — creating a Player group, joining one (or asking to), withdrawing a
 * request, and the Info tab's: answering a Join request, editing the group, leaving it and deleting it.
 *
 * No rule is applied here that the server does not apply again: *Create the group* is only
 * pressable once the form's schema answers a group (`newGroupFrom`), and the server refuses the
 * same two fields by name. What comes back is the canonical answer, mapped, for the hook to write into the cache.
 */

import type { GroupExit } from '../domain/groupInfo';
import {
  deleteGroup,
  deleteJoinRequest,
  deleteMembership,
  postApproval,
  postDecline,
  postGroup,
  postMembership,
  putGroupDetails,
} from '../api/groupsApi';
import type { EditedGroup, Group, GroupAtClub, GroupDetails, NewGroup } from '../domain/group';
import { toEditedGroup, toGroup, toGroupAtClub } from '../mappers/groupMappers';

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

/**
 * **Withdraw request** (#800) — the reader's Join request on the group is gone, and nobody is told.
 * Nothing is refused: a request already answered changes nothing, and still succeeds.
 */
export function withdrawJoinRequest(groupId: string): Promise<void> {
  return deleteJoinRequest(groupId);
}

/** How the Owner answers a Join request: **Approve** admits the player, **✕** declines, silently. */
export type RequestAnswer = 'approve' | 'decline';

export function answerRequest(
  groupId: string,
  playerId: string,
  answer: RequestAnswer,
): Promise<void> {
  return answer === 'approve' ? postApproval(groupId, playerId) : postDecline(groupId, playerId);
}

/** Both fields as the form holds them; the answer says who a switch to Anyone let in. */
export async function editGroup(groupId: string, details: GroupDetails): Promise<EditedGroup> {
  return toEditedGroup(
    await putGroupDetails(groupId, { name: details.name, join_policy: details.joinPolicy }),
  );
}

/** *Delete the group* removes it; *Leave the group* removes the reader from it. */
export function exitGroup(groupId: string, exit: GroupExit): Promise<void> {
  return exit === 'delete' ? deleteGroup(groupId) : deleteMembership(groupId);
}

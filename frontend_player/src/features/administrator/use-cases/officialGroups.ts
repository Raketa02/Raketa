/**
 * **The administrator area's reads and writes** — the Groups tab, one official group, creating one
 * and answering its Join requests. Pass-throughs over `api/` and `mappers/`, as the uniform-strict
 * rule allows where there is no rule to apply: the server orders, counts, checks and admits, and
 * nothing is decided here. *Create the group* is pressable only once the form's schema answers a
 * group, and the server refuses the same four fields by name.
 */

import {
  getAdministeredGroups,
  getOfficialGroup,
  postApproval,
  postDecline,
  postOfficialGroup,
  type Cancellable,
} from '../api/administratorApi';
import type { AdministeredGroups, NewOfficialGroup, OfficialGroup } from '../domain/officialGroup';
import {
  toAdministeredGroups,
  toCreateRequest,
  toOfficialGroup,
} from '../mappers/administratorMappers';

/** The club, and the official groups this Administrator runs there, newest created first. */
export async function readAdministeredGroups(
  clubId: string,
  options: Cancellable = {},
): Promise<AdministeredGroups> {
  return toAdministeredGroups(await getAdministeredGroups(clubId, options));
}

export async function readOfficialGroup(
  clubId: string,
  groupId: string,
  options: Cancellable = {},
): Promise<OfficialGroup> {
  return toOfficialGroup(await getOfficialGroup(clubId, groupId, options));
}

/** The answer is the new group as its page reads it. */
export async function createOfficialGroup(
  clubId: string,
  group: NewOfficialGroup,
): Promise<OfficialGroup> {
  return toOfficialGroup(await postOfficialGroup(clubId, toCreateRequest(group)));
}

/** How an Administrator answers a Join request: **Approve** admits the player, **✕** declines, silently. */
export type RequestAnswer = 'approve' | 'decline';

export function answerRequest(
  clubId: string,
  groupId: string,
  playerId: string,
  answer: RequestAnswer,
): Promise<void> {
  return answer === 'approve'
    ? postApproval(clubId, groupId, playerId)
    : postDecline(clubId, groupId, playerId);
}

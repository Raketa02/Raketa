/**
 * **The administrator area's reads and writes** — the Groups tab, one official group, creating one,
 * saving its settings and answering its Join requests. Pass-throughs over `api/` and `mappers/`, as the uniform-strict
 * rule allows where there is no rule to apply: the server orders, counts, checks and admits, and
 * nothing is decided here. *Create the group* and *Save* are pressable only once the form's schema
 * answers settings, and the server refuses the same four fields by name.
 */

import {
  getAdministeredGroups,
  getOfficialGroup,
  postApproval,
  postDecline,
  postHandoversSeen,
  postOfficialGroup,
  putSettings,
  type Cancellable,
} from '../api/administratorApi';
import type {
  AdministeredGroups,
  OfficialGroup,
  OfficialGroupSettings,
  SavedSettings,
} from '../domain/officialGroup';
import {
  toAdministeredGroups,
  toOfficialGroup,
  toSavedSettings,
  toSettingsRequest,
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
  group: OfficialGroupSettings,
): Promise<OfficialGroup> {
  return toOfficialGroup(await postOfficialGroup(clubId, toSettingsRequest(group)));
}

/** The group as its settings left it, and who a switch to *Anyone* let in. */
export async function saveSettings(
  clubId: string,
  groupId: string,
  settings: OfficialGroupSettings,
): Promise<SavedSettings> {
  return toSavedSettings(await putSettings(clubId, groupId, toSettingsRequest(settings)));
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

/** The handover sheet was closed or followed: these groups were told (ADR-0192 §1). */
export function noteHandoversSeen(clubId: string, groupIds: readonly string[]): Promise<void> {
  return postHandoversSeen(clubId, groupIds);
}

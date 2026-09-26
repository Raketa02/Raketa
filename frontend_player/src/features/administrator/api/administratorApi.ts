/**
 * **The administrator's official-group routes** — one of the two layers allowed to read generated
 * types, and the only place these paths are written down
 * ([#509](https://github.com/Raketa02/Raketa/issues/509)'s contract).
 *
 * Every route hangs under `/administrator/clubs/{club_id}` and **every one asks again** whether this
 * account is an active Administrator of that club: a removal takes effect on the next request, as
 * `403 not_an_administrator` (ADR-0184 §7). The administrator profile runs on the player app's own
 * token (ADR-0185 §6) — switching profile is client state, never a new credential.
 *
 * ## A `signal` on the reads and none on the writes, and no retry on either
 *
 * `groupsApi`'s rule, for its reason: an abandoned `GET` records nothing, and a write appends to the
 * group's stream. **Creating twice would make two groups** — names are never unique — so the create
 * is never retried and its button is busy while it is in flight. Approving somebody already in and
 * declining a request that is not waiting change nothing, by the routes' own word; neither is
 * retried all the same, every mutation's rule.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

/** The reads may be abandoned; a write may not. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

const groupsPath = (clubId: string) =>
  `/api/v1/administrator/clubs/${encodeURIComponent(clubId)}/groups`;

const groupPath = (clubId: string, groupId: string) =>
  `${groupsPath(clubId)}/${encodeURIComponent(groupId)}`;

/** The official groups this Administrator runs at the club, newest created first — and the club. */
export function getAdministeredGroups(
  clubId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['AdministeredGroupsResponse']> {
  return httpRequest({ method: 'GET', path: groupsPath(clubId), authenticated: true, signal });
}

/**
 * One official group this Administrator runs — `group_not_found` for every group that is not
 * theirs: a missing one, a player group, another club's, a colleague's.
 */
export function getOfficialGroup(
  clubId: string,
  groupId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['AdministeredGroupResponse']> {
  return httpRequest({
    method: 'GET',
    path: groupPath(clubId, groupId),
    authenticated: true,
    signal,
  });
}

/**
 * **Create an official group** — its Home club is the club in the path, it has no Owner and nobody
 * in it yet, and it gets its link. Answers the group as its page reads it.
 */
export function postOfficialGroup(
  clubId: string,
  body: Schemas['CreateOfficialGroupRequest'],
): Promise<Schemas['AdministeredGroupResponse']> {
  return httpRequest({ method: 'POST', path: groupsPath(clubId), body, authenticated: true });
}

/** The player is a Group member at once. */
export function postApproval(clubId: string, groupId: string, playerId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${groupPath(clubId, groupId)}/requests/${encodeURIComponent(playerId)}/approve`,
    authenticated: true,
  });
}

/** The request is gone, silently: nothing tells the player, and they may ask again. */
export function postDecline(clubId: string, groupId: string, playerId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${groupPath(clubId, groupId)}/requests/${encodeURIComponent(playerId)}/decline`,
    authenticated: true,
  });
}

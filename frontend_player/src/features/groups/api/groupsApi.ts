/**
 * **The group routes the Groups list, New group, Join a group, the group page, Members and Edit
 * group read and write** — one of the two layers allowed to read generated types, and the only
 * place these paths are written down.
 *
 * ## A `signal` on the reads and none on the writes
 *
 * The asymmetry `gamesApi` draws, for its reason: a `GET` records nothing, so an abandoned one
 * costs nobody a row — and the two searches are abandoned on **every keystroke**, because each
 * letter is a new question. A write appends an event to the group's stream, and a cancelled one
 * can leave a member or a request recorded with nobody holding the answer that says so.
 *
 * ## No `Idempotency-Key` on any write
 *
 * Joining twice changes nothing: the second `POST /membership` answers the relation the first one
 * made, *you're in* or *requested · waiting*. Creating twice **would** make two groups — names are
 * never unique — so the create is never retried, and the form's button is busy while it is in
 * flight (`useCreateGroup`).
 *
 * Info's writes (#514) are each safe to repeat by the route's own word: approving
 * somebody already in and declining a request that is not waiting change nothing, saving what the
 * group already says records nothing, and a second *Leave* or *Delete* meets `group_not_found`.
 * None is retried all the same — every mutation's rule — and each control is busy in flight.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

/** The reads may be abandoned; a write may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/** The groups the reader belongs to, **newest joined first**. */
export function getMyGroups({ signal }: Cancellable = {}): Promise<Schemas['MyGroupsResponse']> {
  return httpRequest({ method: 'GET', path: '/api/v1/groups', authenticated: true, signal });
}

/** A group, for its members. `group_not_found` for no such group and for one the reader is not in. */
export function getGroup(
  groupId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['GroupResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/groups/${encodeURIComponent(groupId)}`,
    authenticated: true,
    signal,
  });
}

/** Create a Player group — the reader becomes its Owner and first member. */
export function postGroup(
  body: Schemas['CreatePlayerGroupRequest'],
): Promise<Schemas['GroupResponse']> {
  return httpRequest({ method: 'POST', path: '/api/v1/groups', body, authenticated: true });
}

/**
 * **Join, or ask to** — one tap, and the answer's `relation` says which happened: `MEMBER` for an
 * Anyone group, `REQUESTED` for a People I approve one.
 */
export function postMembership(groupId: string): Promise<Schemas['GroupAtClubSchema']> {
  return httpRequest({
    method: 'POST',
    path: `/api/v1/groups/${encodeURIComponent(groupId)}/membership`,
    authenticated: true,
  });
}

const groupPath = (groupId: string) => `/api/v1/groups/${encodeURIComponent(groupId)}`;

/**
 * **Members, for one sport** — only the members rated in it: the reader, the Owner, then newest
 * joined first. A block hides nobody here, either way round (ADR-0193 §2).
 */
export function getGroupMembers(
  groupId: string,
  sport: Schemas['Sport'],
  { signal }: Cancellable = {},
): Promise<Schemas['GroupMembersResponse']> {
  return httpRequest({
    method: 'GET',
    path: `${groupPath(groupId)}/members?sport=${sport}`,
    authenticated: true,
    signal,
  });
}

/** *Want to join · N* — the Owner's; `not_the_group_owner` for anybody else. */
export function getJoinRequests(
  groupId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['JoinRequestsResponse']> {
  return httpRequest({
    method: 'GET',
    path: `${groupPath(groupId)}/requests`,
    authenticated: true,
    signal,
  });
}

/** The player is a Group member at once. */
export function postApproval(groupId: string, playerId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${groupPath(groupId)}/requests/${encodeURIComponent(playerId)}/approve`,
    authenticated: true,
  });
}

/** The request is gone, silently: nothing tells the player, and they may ask again. */
export function postDecline(groupId: string, playerId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${groupPath(groupId)}/requests/${encodeURIComponent(playerId)}/decline`,
    authenticated: true,
  });
}

/**
 * **Edit group** — both fields as the form holds them, recorded together or not at all. Switching
 * to `ANYONE` admits everybody waiting, and the answer's `admitted` says who.
 */
export function putGroupDetails(
  groupId: string,
  body: Schemas['EditGroupRequest'],
): Promise<Schemas['EditedGroupResponse']> {
  return httpRequest({
    method: 'PUT',
    path: `${groupPath(groupId)}/details`,
    body,
    authenticated: true,
  });
}

/**
 * **Leave** — an Owner leaving a group other people are in passes it to whoever has been in
 * longest; `lone_owner_cannot_leave` for an Owner alone, whose way out is *Delete*.
 */
export function deleteMembership(groupId: string): Promise<void> {
  return httpRequest<void>({
    method: 'DELETE',
    path: `${groupPath(groupId)}/membership`,
    authenticated: true,
  });
}

/** **Delete** — the Owner's, and only while they are its only member. */
export function deleteGroup(groupId: string): Promise<void> {
  return httpRequest<void>({ method: 'DELETE', path: groupPath(groupId), authenticated: true });
}

function pageQuery(text: string, page: number): string {
  return `q=${encodeURIComponent(text)}&page=${page}`;
}

/** Every club in Raketa whose name or district holds `text`, nearest first, twenty to a page. */
export function getHomeClubs(
  text: string,
  page: number,
  { signal }: Cancellable = {},
): Promise<Schemas['HomeClubPageResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/home-clubs?${pageQuery(text, page)}`,
    authenticated: true,
    signal,
  });
}

/** Clubs, districts, group names or a group link — answered as club cards with groups inside. */
export function getJoinSearch(
  text: string,
  page: number,
  { signal }: Cancellable = {},
): Promise<Schemas['JoinSearchResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/join-search?${pageQuery(text, page)}`,
    authenticated: true,
    signal,
  });
}

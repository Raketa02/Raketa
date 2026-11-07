/**
 * **The eleven friends routes this app sends**, and the only place their paths are written down
 * ([#753](https://github.com/Raketa02/Raketa/issues/753), [#754](https://github.com/Raketa02/Raketa/issues/754),
 * [#756](https://github.com/Raketa02/Raketa/issues/756), on the contract
 * [#745](https://github.com/Raketa02/Raketa/issues/745) and [#748](https://github.com/Raketa02/Raketa/issues/748)
 * built; ADR-0202 §1).
 *
 * One of the two layers allowed to read generated types.
 *
 * | Route | |
 * | --- | --- |
 * | `POST /friends/requests` | ask — `SENT`, or `FRIEND` when the two requests crossed |
 * | `POST /friends/requests/{id}/acceptance` | accept — `FRIEND`; also after *Not now* |
 * | `POST /friends/requests/{id}/set-aside` | *Not now* — 204; the request stays open, untold |
 * | `DELETE /friends/requests/{id}` | cancel your own — 204 always, nobody told |
 * | `DELETE /friends/{id}` | remove a friend — 204 always, nobody told, no game touched |
 * | `GET /friends` | your friends, by nickname, each with every sport they are rated in (#754) |
 * | `GET /friends/requests?direction=` | *Asked you* or *You asked*, newest first (#754) |
 * | `GET /friends/groups` | the Add friends sheet's groups, *8 members · 2 to add* (#754) |
 * | `GET /friends/link` | your friend link — made on its first read, the same until a New link (#756) |
 * | `POST /friends/link/replacement` | **New link** — a fresh code, the old one dead at once (#756) |
 * | `POST /friends/links/{code}/opening` | open somebody's link — their request on your Home (#756) |
 *
 * **The three writes that take something back are idempotent**, which is the correctness mechanism
 * under a double tap. Asking and accepting are not: a second ask is `friend_request_already_sent`,
 * a second accept `friend_request_not_found`, and the surface re-reads rather than retrying.
 * **Opening a link is idempotent too** — opened again, it makes no second request — and a New link
 * is not: each makes a fresh code.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

const REQUESTS_PATH = '/api/v1/friends/requests';
const FRIENDS_PATH = '/api/v1/friends';

const GROUPS_PATH = '/api/v1/friends/groups';
const LINK_PATH = '/api/v1/friends/link';
const linkOpeningPath = (code: string) =>
  `/api/v1/friends/links/${encodeURIComponent(code)}/opening`;

const requestPath = (playerId: string) => `${REQUESTS_PATH}/${encodeURIComponent(playerId)}`;

/** A read the caller may abandon — Query's signal, passed to the request. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/**
 * **Ask to be friends.** Refused with `cannot_befriend_yourself`, `player_not_in_your_groups`,
 * `already_friends`, `friend_request_already_sent`, `unblock_them_first` or
 * `concurrent_modification`.
 */
export function postFriendRequest(
  body: Schemas['AskToBeFriendsRequest'],
): Promise<Schemas['RelationResponse']> {
  return httpRequest<Schemas['RelationResponse']>({
    method: 'POST',
    path: REQUESTS_PATH,
    body,
    authenticated: true,
  });
}

/** **Accept their request** — `friend_request_not_found` when none from them is waiting. */
export function postAcceptance(playerId: string): Promise<Schemas['RelationResponse']> {
  return httpRequest<Schemas['RelationResponse']>({
    method: 'POST',
    path: `${requestPath(playerId)}/acceptance`,
    authenticated: true,
  });
}

/** **Not now** — `friend_request_not_found` when none from them is waiting. */
export function postSetAside(playerId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${requestPath(playerId)}/set-aside`,
    authenticated: true,
  });
}

/** **Cancel your request to them.** */
export function deleteFriendRequest(playerId: string): Promise<void> {
  return httpRequest<void>({ method: 'DELETE', path: requestPath(playerId), authenticated: true });
}

/** **Remove them as a friend.** */
export function deleteFriend(playerId: string): Promise<void> {
  return httpRequest<void>({
    method: 'DELETE',
    path: `${FRIENDS_PATH}/${encodeURIComponent(playerId)}`,
    authenticated: true,
  });
}

/**
 * **Your friends** — from every group, by nickname, each with every sport they are rated in. The
 * picker's `?sport=` narrowing is #757's.
 */
export function getFriends({ signal }: Cancellable = {}): Promise<Schemas['FriendsResponse']> {
  return httpRequest<Schemas['FriendsResponse']>({
    method: 'GET',
    path: FRIENDS_PATH,
    authenticated: true,
    signal,
  });
}

/** **Open requests one way** — `ASKED_YOU`, set aside or not; `YOU_ASKED`. Newest first. */
export function getFriendRequests(
  direction: Schemas['Direction'],
  { signal }: Cancellable = {},
): Promise<Schemas['FriendRequestsResponse']> {
  return httpRequest<Schemas['FriendRequestsResponse']>({
    method: 'GET',
    path: `${REQUESTS_PATH}?direction=${direction}`,
    authenticated: true,
    signal,
  });
}

/** **Add friends — from your groups**: each group, its size, and how many you could still ask. */
export function getGroupsToAddFrom({ signal }: Cancellable = {}): Promise<
  Schemas['GroupsToAddFromResponse']
> {
  return httpRequest<Schemas['GroupsToAddFromResponse']>({
    method: 'GET',
    path: GROUPS_PATH,
    authenticated: true,
    signal,
  });
}

/**
 * **Your friend link** — `<public site>/f/<code>`, **made on its first read** and the same on every
 * read after. Refused with `concurrent_modification` when two first reads raced: read again.
 */
export function getFriendLink({ signal }: Cancellable = {}): Promise<
  Schemas['FriendLinkResponse']
> {
  return httpRequest<Schemas['FriendLinkResponse']>({
    method: 'GET',
    path: LINK_PATH,
    authenticated: true,
    signal,
  });
}

/**
 * **New link** — a fresh code, the old one answering `friend_link_not_found` at once. Requests
 * already made through it stay. `concurrent_modification` when it raced a read or another New link.
 */
export function postFriendLinkReplacement(): Promise<Schemas['FriendLinkResponse']> {
  return httpRequest<Schemas['FriendLinkResponse']>({
    method: 'POST',
    path: `${LINK_PATH}/replacement`,
    authenticated: true,
  });
}

/**
 * **Open somebody's link** — the opener's relation to its owner once it is: `ASKED_YOU` (their
 * request is on your Home), `FRIEND`, or `NONE` (your own). Refused with `friend_link_not_found`,
 * `unblock_them_first` (you blocked them) or `concurrent_modification`.
 */
export function postFriendLinkOpening(code: string): Promise<Schemas['OpenedFriendLinkResponse']> {
  return httpRequest<Schemas['OpenedFriendLinkResponse']>({
    method: 'POST',
    path: linkOpeningPath(code),
    authenticated: true,
  });
}

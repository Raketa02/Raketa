/**
 * **The five friends routes this app sends**, and the only place their paths are written down
 * ([#753](https://github.com/Raketa02/Raketa/issues/753), on the contract
 * [#745](https://github.com/Raketa02/Raketa/issues/745) built; ADR-0202 §1).
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
 *
 * **The three writes that take something back are idempotent**, which is the correctness mechanism
 * under a double tap. Asking and accepting are not: a second ask is `friend_request_already_sent`,
 * a second accept `friend_request_not_found`, and the surface re-reads rather than retrying.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

const REQUESTS_PATH = '/api/v1/friends/requests';
const FRIENDS_PATH = '/api/v1/friends';

const requestPath = (playerId: string) => `${REQUESTS_PATH}/${encodeURIComponent(playerId)}`;

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

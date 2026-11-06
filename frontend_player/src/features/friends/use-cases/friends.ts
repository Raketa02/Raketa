/**
 * **The five acts** (#753) **and the three reads** (#754) — pass-throughs over the routes, the
 * template's uniform-strict escape hatch: every rule a request obeys is the server's aggregate's,
 * every list is in the server's order, and the relation an act answers is spelled as the wire
 * spells it.
 */

import {
  type Cancellable,
  deleteFriend,
  deleteFriendRequest,
  getFriendRequests,
  getFriends,
  getGroupsToAddFrom,
  postAcceptance,
  postFriendRequest,
  postSetAside,
} from '../api/friendsApi';
import type { Friend, FriendRequest, GroupToAddFrom } from '../domain/friendList';
import type { AskedWhere } from '../domain/friendship';
import type { FriendRelation, RequestDirection } from '../domain/vocabulary';
import {
  toAskRequest,
  toFriend,
  toFriendRequest,
  toGroupToAddFrom,
} from '../mappers/friendsMappers';

/** Ask — `SENT`, or `FRIEND` when they had asked first. */
export function askToBeFriends(playerId: string, where: AskedWhere): Promise<FriendRelation> {
  return postFriendRequest(toAskRequest(playerId, where)).then((answer) => answer.relation);
}

/** Accept — `FRIEND`. */
export function acceptFriendRequest(playerId: string): Promise<FriendRelation> {
  return postAcceptance(playerId).then((answer) => answer.relation);
}

export function setAsideFriendRequest(playerId: string): Promise<void> {
  return postSetAside(playerId);
}

export function cancelFriendRequest(playerId: string): Promise<void> {
  return deleteFriendRequest(playerId);
}

export function removeFriend(playerId: string): Promise<void> {
  return deleteFriend(playerId);
}

/** Your friends, by nickname. */
export function readFriends(options: Cancellable = {}): Promise<readonly Friend[]> {
  return getFriends(options).then((answer) => answer.friends.map(toFriend));
}

/** The open requests one way, newest first. */
export function readFriendRequests(
  direction: RequestDirection,
  options: Cancellable = {},
): Promise<readonly FriendRequest[]> {
  return getFriendRequests(direction, options).then((answer) =>
    answer.requests.map(toFriendRequest),
  );
}

/** Your groups, newest joined first, with how many in each you could still ask. */
export function readGroupsToAddFrom(options: Cancellable = {}): Promise<readonly GroupToAddFrom[]> {
  return getGroupsToAddFrom(options).then((answer) => answer.groups.map(toGroupToAddFrom));
}

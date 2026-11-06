/**
 * **The five acts** (#753) — pass-throughs over the routes, the template's uniform-strict escape
 * hatch: every rule a request obeys is the server's aggregate's, and the relation it answers is
 * spelled as the wire spells it.
 */

import {
  deleteFriend,
  deleteFriendRequest,
  postAcceptance,
  postFriendRequest,
  postSetAside,
} from '../api/friendsApi';
import type { AskedWhere } from '../domain/friendship';
import type { FriendRelation } from '../domain/vocabulary';
import { toAskRequest } from '../mappers/friendsMappers';

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

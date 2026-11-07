/**
 * **The five acts** (#753), **the three reads** (#754), **the link's three** (#756) — your link
 * read, a New link, and somebody's link opened — **an ask for a Level** (#758), **and Not now on
 * the asks waiting on you** (#765): pass-throughs
 * over the routes, the
 * template's uniform-strict escape hatch: every rule a request obeys is the server's aggregate's,
 * every list is in the server's order, and the relation an act answers is spelled as the wire
 * spells it.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  type Cancellable,
  deleteFriend,
  deleteFriendRequest,
  getFriendRequests,
  getFriends,
  getFriendLink,
  getGroupsToAddFrom,
  postAcceptance,
  postFriendLinkOpening,
  postFriendLinkReplacement,
  postFriendRequest,
  postLevelAsk,
  postLevelAsksSetAside,
  postSetAside,
} from '../api/friendsApi';
import type { Friend, FriendRequest, GroupToAddFrom } from '../domain/friendList';
import type { FriendLink } from '../domain/friendLink';
import type { AskedWhere } from '../domain/friendship';
import type { FriendRelation, RequestDirection } from '../domain/vocabulary';
import {
  toAskRequest,
  toFriend,
  toFriendLink,
  toFriendRequest,
  toGroupToAddFrom,
  toLevelAskRequest,
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
  return getFriends(undefined, options).then((answer) => answer.friends.map(toFriend));
}

/**
 * **Your friends in one sport** — a group's picker (#757): each with that sport's Level alone, or
 * none, highest first and the unrated last, in the server's order.
 */
export function readFriendsIn(sport: Sport, options: Cancellable = {}): Promise<readonly Friend[]> {
  return getFriends(toWireSport(sport), options).then((answer) => answer.friends.map(toFriend));
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

/** Your friend link — made on its first read. */
export function readFriendLink(options: Cancellable = {}): Promise<FriendLink> {
  return getFriendLink(options).then(toFriendLink);
}

/** **New link** — the fresh one; the old is dead. */
export function replaceFriendLink(): Promise<FriendLink> {
  return postFriendLinkReplacement().then(toFriendLink);
}

/** **Open somebody's link** — where the opener stands with its owner once it is. */
export function openFriendLink(code: string): Promise<FriendRelation> {
  return postFriendLinkOpening(code).then((answer) => answer.relation);
}

/** **Ask a friend to get a Level in the picker's sport**, from this group's Friends tab (#758). */
export function askForALevel(playerId: string, sport: Sport, groupId: string): Promise<void> {
  return postLevelAsk(playerId, toLevelAskRequest(sport, groupId));
}

/** **Not now** on Home's ASKED FOR A LEVEL card — every ask in the sport it names, set aside. */
export function setAsideLevelAsks(sport: Sport): Promise<void> {
  return postLevelAsksSetAside(toWireSport(sport));
}

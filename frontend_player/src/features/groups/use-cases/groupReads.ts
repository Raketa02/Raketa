/**
 * **The feature's reads** — the Groups list, one group, its Members for a sport, the Join
 * requests waiting on it, and the two searches. Pass-throughs over
 * `api/` and `mappers/`, as the uniform-strict rule allows where there is no rule to apply: the
 * backend orders, filters and folds everything these return, and nothing is decided here.
 *
 * The one thing a search use-case adds is **the text it answered**, carried on the answer, so an
 * empty result quotes what was searched for rather than what has been typed since.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  getGroup,
  getGroupMembers,
  getHomeClubs,
  getHottestGroups,
  getJoinRequests,
  getJoinSearch,
  getMyGroups,
  type Cancellable,
} from '../api/groupsApi';
import type {
  ClubSearch,
  Group,
  GroupMember,
  HottestGroup,
  JoinRequest,
  MyGroup,
} from '../domain/group';
import {
  toGroup,
  toGroupMembers,
  toHomeClubSearch,
  toHottestGroups,
  toJoinRequests,
  toJoinSearch,
  toMyGroups,
} from '../mappers/groupMappers';

export async function readMyGroups(options: Cancellable = {}): Promise<readonly MyGroup[]> {
  return toMyGroups(await getMyGroups(options));
}

export async function readGroup(groupId: string, options: Cancellable = {}): Promise<Group> {
  return toGroup(await getGroup(groupId, options));
}

/** Members rated in `sport`: the reader, the Owner, then newest joined first. */
export async function readGroupMembers(
  groupId: string,
  sport: Sport,
  options: Cancellable = {},
): Promise<readonly GroupMember[]> {
  return toGroupMembers(await getGroupMembers(groupId, toWireSport(sport), options));
}

/** *Want to join · N* — the Owner's read, in the order they asked. */
export async function readJoinRequests(
  groupId: string,
  options: Cancellable = {},
): Promise<readonly JoinRequest[]> {
  return toJoinRequests(await getJoinRequests(groupId, options));
}

/** **Home's Hottest groups** (#800) — up to six, in the row's order; none hides the row. */
export async function readHottestGroups(
  options: Cancellable = {},
): Promise<readonly HottestGroup[]> {
  return toHottestGroups(await getHottestGroups(options));
}

export async function searchHomeClubs(
  text: string,
  page: number,
  options: Cancellable = {},
): Promise<ClubSearch> {
  return toHomeClubSearch(text, await getHomeClubs(text, page, options));
}

export async function searchToJoin(
  text: string,
  page: number,
  options: Cancellable = {},
): Promise<ClubSearch> {
  return toJoinSearch(text, await getJoinSearch(text, page, options));
}

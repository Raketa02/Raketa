/**
 * **The feature's reads** — the Groups list, one group, and the two searches. Pass-throughs over
 * `api/` and `mappers/`, as the uniform-strict rule allows where there is no rule to apply: the
 * backend orders, filters and folds everything these return, and nothing is decided here.
 *
 * The one thing a search use-case adds is **the text it answered**, carried on the answer, so an
 * empty result quotes what was searched for rather than what has been typed since.
 */

import {
  getGroup,
  getHomeClubs,
  getJoinSearch,
  getMyGroups,
  type Cancellable,
} from '../api/groupsApi';
import type { ClubSearch, Group, MyGroup } from '../domain/group';
import { toGroup, toHomeClubSearch, toJoinSearch, toMyGroups } from '../mappers/groupMappers';

export async function readMyGroups(options: Cancellable = {}): Promise<readonly MyGroup[]> {
  return toMyGroups(await getMyGroups(options));
}

export async function readGroup(groupId: string, options: Cancellable = {}): Promise<Group> {
  return toGroup(await getGroup(groupId, options));
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

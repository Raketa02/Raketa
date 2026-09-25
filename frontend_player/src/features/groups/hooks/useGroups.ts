/**
 * **The Groups list, one group, its Members and its requests** — four reads, on the app's defaults.
 *
 * | | |
 * | --- | --- |
 * | `useMyGroups` | `GET /groups` — the reader's groups, newest joined first |
 * | `useGroup` | `GET /groups/{id}` — one group, as its page reads it |
 * | `useGroupMembers` | `GET /groups/{id}/members?sport=` — Members, for the filter's sport |
 * | `useJoinRequests` | `GET /groups/{id}/requests` — *Want to join*, asked **only by the Owner** |
 *
 * Neither overrides anything: a group changes when somebody joins it, and the thirty-second
 * `staleTime` with a refetch on focus is what makes a count that moved while the app was away
 * current when the player comes back. The two writes that change them say so in their own cache
 * effects (`useGroupWrites.ts`).
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Sport } from '@/shared/vocabulary/sport';

import type { Group, GroupMember, JoinRequest, MyGroup } from '../domain/group';
import {
  readGroup,
  readGroupMembers,
  readJoinRequests,
  readMyGroups,
} from '../use-cases/groupReads';

import { groupKeys } from './groupKeys';

export function useMyGroups() {
  return useQuery<readonly MyGroup[], AppError>({
    queryKey: groupKeys.mine(),
    queryFn: ({ signal }) => readMyGroups({ signal }),
  });
}

export function useGroup(groupId: string) {
  return useQuery<Group, AppError>({
    queryKey: groupKeys.detail(groupId),
    queryFn: ({ signal }) => readGroup(groupId, { signal }),
  });
}

/**
 * For the sport the filter is on — mounted only once the phone has said which, so nothing is
 * drawn for one sport and then another.
 */
export function useGroupMembers(groupId: string, sport: Sport) {
  return useQuery<readonly GroupMember[], AppError>({
    queryKey: groupKeys.members(groupId, sport),
    queryFn: ({ signal }) => readGroupMembers(groupId, sport, { signal }),
  });
}

/**
 * **The Owner's read** — anybody else is refused (`not_the_group_owner`), so only a surface drawn
 * for the Owner mounts it, and a read that can only be refused is never asked.
 */
export function useJoinRequests(groupId: string) {
  return useQuery<readonly JoinRequest[], AppError>({
    queryKey: groupKeys.requests(groupId),
    queryFn: ({ signal }) => readJoinRequests(groupId, { signal }),
  });
}

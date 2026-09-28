/**
 * **The Groups list, one group, its Members and its requests** — four reads, on the app's defaults.
 *
 * | | |
 * | --- | --- |
 * | `useMyGroups` | `GET /groups` — the reader's groups, newest joined first; `useGroupsList` re-reads it on a return |
 * | `useGroup` | `GET /groups/{id}` — one group, as its page reads it |
 * | `useGroupMembers` | `GET /groups/{id}/members?sport=` — Members, for the filter's sport |
 * | `useJoinRequests` | `GET /groups/{id}/requests` — *Want to join*, asked **only by the Owner** |
 *
 * Neither overrides anything: a group changes when somebody joins it, and the thirty-second
 * `staleTime` with a refetch on focus is what makes a count that moved while the app was away
 * current when the player comes back. The two writes that change them say so in their own cache
 * effects (`useGroupWrites.ts`).
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';

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

/**
 * **The Groups list as Play › Groups draws it — re-read each time the player comes back to it.**
 *
 * New group, Join a group and every group's page are pushed over the list, and a stack keeps the
 * list mounted under them, so *back* is neither a mount nor a foreground (`useOnReturn`'s note).
 * An Owner can let the reader in while they are still on Join a group — nothing on this phone
 * hears it — and back on Groups the list was the one read before they left, without the group,
 * until a switch to Explore and back remounted it (#529). The return is the moment the list is
 * looked at again, so it is the moment it is marked stale, as the Chats list is.
 */
export function useGroupsList() {
  const client = useQueryClient();

  useOnReturn(() => {
    void client.invalidateQueries({ queryKey: groupKeys.mine() });
  });

  return useMyGroups();
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
 * **The Owner's read** — anybody else is refused (`not_the_group_owner`), so it is asked only
 * `enabled` for the Owner, and a read that can only be refused is never asked. Two surfaces read
 * it under one key: *Want to join* on Info, and the Info tab's count on every tab (#529) — so an
 * answer that takes a row takes it off the count in the same frame.
 */
export function useJoinRequests(groupId: string, enabled = true) {
  return useQuery<readonly JoinRequest[], AppError>({
    queryKey: groupKeys.requests(groupId),
    queryFn: ({ signal }) => readJoinRequests(groupId, { signal }),
    enabled,
  });
}

/**
 * **Info's pull** — the group, and everything read under it that is on screen: who is waiting,
 * and so the tab's count. What is not on screen is marked stale and read when it is next looked
 * at. Resolves once the re-reads have landed, refused or not — a refusal is the read's own to say.
 */
export function useGroupReread(groupId: string): () => Promise<void> {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: groupKeys.detail(groupId) });
}

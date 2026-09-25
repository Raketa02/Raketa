/**
 * **The Groups list and one group** — two reads, on the app's defaults.
 *
 * | | |
 * | --- | --- |
 * | `useMyGroups` | `GET /groups` — the reader's groups, newest joined first |
 * | `useGroup` | `GET /groups/{id}` — one group, as its page reads it |
 *
 * Neither overrides anything: a group changes when somebody joins it, and the thirty-second
 * `staleTime` with a refetch on focus is what makes a count that moved while the app was away
 * current when the player comes back. The two writes that change them say so in their own cache
 * effects (`useGroupWrites.ts`).
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Group, MyGroup } from '../domain/group';
import { readGroup, readMyGroups } from '../use-cases/groupReads';

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

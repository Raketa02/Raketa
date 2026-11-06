/**
 * **The Friends page's reads** ([#754](https://github.com/Raketa02/Raketa/issues/754)) — your
 * friends, the requests each way, and the Add friends sheet's groups. One key each, so the You
 * tab's row and the page behind it are one read and agree, and every friends write re-reads them
 * (`friendKeys`). The global defaults suit them: lists only the players' own acts move.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Friend, FriendRequest, GroupToAddFrom } from '../domain/friendList';
import type { RequestDirection } from '../domain/vocabulary';
import { readFriendRequests, readFriends, readGroupsToAddFrom } from '../use-cases/friends';

import { friendKeys } from './friendKeys';

export function useFriends() {
  return useQuery<readonly Friend[], AppError>({
    queryKey: friendKeys.list(),
    queryFn: ({ signal }) => readFriends({ signal }),
  });
}

export function useFriendRequests(direction: RequestDirection) {
  return useQuery<readonly FriendRequest[], AppError>({
    queryKey: friendKeys.requests(direction),
    queryFn: ({ signal }) => readFriendRequests(direction, { signal }),
  });
}

/** `enabled` false asks nothing — the sheet reads its groups only once it is opened. */
export function useGroupsToAddFrom({ enabled = true }: { readonly enabled?: boolean } = {}) {
  return useQuery<readonly GroupToAddFrom[], AppError>({
    queryKey: friendKeys.groups(),
    queryFn: ({ signal }) => readGroupsToAddFrom({ signal }),
    enabled,
  });
}

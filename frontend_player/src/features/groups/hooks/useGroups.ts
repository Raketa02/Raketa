/**
 * **The Groups list, one group, its Members and its requests** — four reads, on the app's defaults,
 * and one answer off the first.
 *
 * | | |
 * | --- | --- |
 * | `useMyGroups` | `GET /groups` — the reader's groups, newest joined first; `useGroupsList` re-reads it on a return, and on a pull; Home's card asks it of a player rated in nothing |
 * | `useGroup` | `GET /groups/{id}` — one group, as its page reads it |
 * | `useGroupMembers` | `GET /groups/{id}/members?sport=` — Members, for the filter's sport |
 * | `useJoinRequests` | `GET /groups/{id}/requests` — *Want to join*, asked **only by the Owner** |
 * | `useInNoGroup` | the Groups list's answer to whether *Your games* says the groupless line (#800) |
 *
 * Neither overrides anything: a group changes when somebody joins it, and the thirty-second
 * `staleTime` with a refetch on focus is what makes a count that moved while the app was away
 * current when the player comes back. The two writes that change them say so in their own cache
 * effects (`useGroupWrites.ts`).
 */

import { queryOptions, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect } from 'react';

import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';
import { useReadFinished } from '@/shared/lib/query-client';

import type { Sport } from '@/shared/vocabulary/sport';

import type { Group, GroupMember, JoinRequest, MyGroup } from '../domain/group';
import {
  readGroup,
  readGroupMembers,
  readJoinRequests,
  readMyGroups,
} from '../use-cases/groupReads';

import { groupKeys } from './groupKeys';

/** The Groups list's read, as one definition — every hook over it, and Home's warm-up (#874). */
export const myGroupsRead = queryOptions<readonly MyGroup[], AppError>({
  queryKey: groupKeys.mine(),
  queryFn: ({ signal }) => readMyGroups({ signal }),
});

/** `enabled` is Home's card's (#731): it asks which groups only of a player rated in nothing. */
export function useMyGroups({ enabled = true }: { readonly enabled?: boolean } = {}) {
  return useQuery({ ...myGroupsRead, enabled });
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

/** One group's read — the page's, and the name *Your rating* says on the way back to it. */
function groupRead(groupId: string) {
  return {
    queryKey: groupKeys.detail(groupId),
    queryFn: ({ signal }: { readonly signal: AbortSignal }) => readGroup(groupId, { signal }),
  };
}

export function useGroup(groupId: string) {
  return useQuery<Group, AppError>(groupRead(groupId));
}

/**
 * **A group's name, by its id** — for *Your rating*'s *Back to {group name}* (#729), on a screen
 * that is not this feature's. The page's own read, under its key, so a pass begun on the page finds
 * the name already in hand; asked for nothing while there is no group to name.
 */
export function useGroupName(groupId: string | undefined): string | undefined {
  return useQuery<Group, AppError, string>({
    ...groupRead(groupId ?? ''),
    enabled: groupId !== undefined,
    select: (group) => group.name,
  }).data;
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
 * it under one key: *Want to join* on Info, and the count on the group's tile (#529, Q125) — so an
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
 * **The Groups list's pull** (#529) — the reader's groups, read again now rather than marked stale,
 * so a group joined or left on another phone is on the list when the spinner stops.
 */
export function useMyGroupsReread(): () => Promise<void> {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: groupKeys.mine() });
}

/**
 * **The group's re-read** — the group, and everything read under it that is on screen: who is
 * waiting, and so the tile's count. What is not on screen is marked stale and read when it is next
 * looked at. Resolves once the re-reads have landed, refused or not — a refusal is the read's own
 * to say. Info's pull and the page's (with its games) hand it to `usePull`. One function for as long
 * as the group is the same, so an effect may depend on it.
 */
export function useGroupReread(groupId: string): () => Promise<void> {
  const client = useQueryClient();
  return useCallback(
    () => client.invalidateQueries({ queryKey: groupKeys.detail(groupId) }),
    [client, groupId],
  );
}

/**
 * **Info's read** (Q125) — the group, read again **when Info opens** and **each time it is come back
 * to** from Members or Edit group, so what another phone changed meanwhile is on it without a pull
 * (#529 F2). Opening it re-reads what the page asked for as it opened: one more read of the group
 * and the requests, paid on a tap. Hands back the re-read for Info's pull.
 */
export function useGroupInfo(groupId: string) {
  const read = useGroup(groupId);
  const reread = useGroupReread(groupId);
  useEffect(() => {
    void reread();
  }, [reread]);
  useOnReturn(() => void reread());
  return { read, reread };
}

/**
 * **Whether the reader is in no group** — then *Your games* reads *Join a group to get games — the
 * hottest ones are just below.* in place of *Play finds you one.* (the Home rows mechanics §3;
 * `GROUPS_COPY.hottest.groupless`). `false` for a member of any group, and while the list is unread
 * or refused: the line it stands in for is true of everybody, so nothing is claimed about groups the
 * phone has not been told of.
 */
export function useInNoGroup(): boolean {
  return useMyGroups().data?.length === 0;
}

/**
 * **Whether the read `useInNoGroup` answers from has finished** (#871) — your groups, landed, refused,
 * held for a connection, or failed once and retrying: *YOUR GAMES*' line waits on it before Home
 * reveals it. Read off the cache, so it draws again only as it turns.
 */
export function useInNoGroupFinished(): boolean {
  return useReadFinished(groupKeys.mine());
}

/**
 * **The five friends writes, and what each re-reads**
 * ([#753](https://github.com/Raketa02/Raketa/issues/753); ADR-0202 §1–§2).
 *
 * | Hook | Route | Re-reads |
 * | --- | --- | --- |
 * | `useAskToBeFriends` | `POST /friends/requests` | the surface's own read; every face too, when the requests crossed |
 * | `useAcceptFriendRequest` | `POST …/{id}/acceptance` | the surface's own read, every face, and Home |
 * | `useSetAsideFriendRequest` | `POST …/{id}/set-aside` | Home, where the card was, and the surface's own read |
 * | `useCancelFriendRequest` | `DELETE /friends/requests/{id}` | the surface's own read |
 * | `useRemoveFriend` | `DELETE /friends/{id}` | the surface's own read, and every face |
 *
 * **And every one re-reads this feature's own lists** (#754, `friendKeys`): You › Friends' three
 * tabs, the Add friends sheet's *to add*, and the You tab's row — so a request asked on Members
 * opened from the sheet is on *You asked* when the player comes back, and an accept on Home is off
 * *Asked you*.
 *
 * ## The surface hands its own read in
 *
 * **Members and the record each re-read themselves** — they hand `reread` down, because the reads
 * are `groups`' and `player_record`'s, and this feature naming their keys while they draw its pill
 * and its buttons would be a dependency both ways (architecture Part 1; `blocks`' `rereadRecord`, the
 * same seam). **Each write settles once that read has**, so the pill stays busy until the row under
 * it already says *request sent* — the row is the server's answer, never a guess.
 *
 * ## What a friendship moves
 *
 * **Every face carries the *friend* tag** (Q12, Q68): the deck's tiles, a game's details, a booked
 * game and Fill in. So an act that turns a friendship on or off — an accept, a crossed request, a
 * removal (`movesTheFaces`) — re-reads every group's deck (and with it Fill in and posting, under
 * each group's root), every game in detail and Home, as a block does. Asking and cancelling move no
 * face, and re-read none of them.
 *
 * ## A refusal that is the state moving is a re-read
 *
 * `already_friends`, `friend_request_already_sent` and `friend_request_not_found` say the surface
 * was drawn from a state that has since moved — accepted on another phone, cancelled by them — and
 * `concurrent_modification` that two acts on the pair raced. **None of them is retried**: asking and
 * accepting are not idempotent, and the global rule retries no mutation. The surface re-reads
 * instead, and the pill or the button it draws next is the answer. Any other refusal is said where
 * it was pressed.
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { proposalKeys } from '@/features/proposals/types';
import type { AppError } from '@/shared/errors';

import { movesTheFaces, type AskedWhere } from '../domain/friendship';
import type { FriendRelation } from '../domain/vocabulary';
import {
  acceptFriendRequest,
  askToBeFriends,
  cancelFriendRequest,
  removeFriend,
  setAsideFriendRequest,
} from '../use-cases/friends';

import { friendKeys } from './friendKeys';

/** The surface's own re-read, handed in by the screen that holds it — see the module note. */
export type Reread = () => Promise<unknown>;

/** The refusals that mean the surface was drawn from a state that has moved. */
const MOVED: ReadonlySet<string> = new Set([
  'already_friends',
  'friend_request_already_sent',
  'friend_request_not_found',
  'concurrent_modification',
]);

/** Whether a refusal is the state moving — re-read, and say nothing. */
export function stateMoved(error: AppError | null | undefined): boolean {
  return error?.code !== undefined && MOVED.has(error.code);
}

export function useAskToBeFriends(playerId: string, where: AskedWhere, reread: Reread) {
  const client = useQueryClient();
  return useMutation<FriendRelation, AppError, void>({
    mutationFn: () => askToBeFriends(playerId, where),
    onSuccess: (relation) => settle(client, reread, movesTheFaces('NONE', relation)),
    onError: (error) => rereadIfMoved(client, error, reread),
  });
}

export function useAcceptFriendRequest(playerId: string, reread?: Reread) {
  const client = useQueryClient();
  return useMutation<FriendRelation, AppError, void>({
    mutationFn: () => acceptFriendRequest(playerId),
    // Home is among the faces, always: the card asking for this answer leaves it.
    onSuccess: () => settle(client, reread, true),
    onError: (error) => (stateMoved(error) ? rereadHomeToo(client, reread) : undefined),
  });
}

/** *Not now* — Home, where the card was, and the surface's own read (the bell, from Home). */
export function useSetAsideFriendRequest(playerId: string, reread?: Reread) {
  const client = useQueryClient();
  return useMutation<void, AppError, void>({
    mutationFn: () => setAsideFriendRequest(playerId),
    onSettled: () => rereadHomeToo(client, reread),
  });
}

export function useCancelFriendRequest(playerId: string, reread: Reread) {
  const client = useQueryClient();
  return useMutation<void, AppError, void>({
    mutationFn: () => cancelFriendRequest(playerId),
    onSuccess: () => settle(client, reread, false),
  });
}

export function useRemoveFriend(playerId: string, reread: Reread) {
  const client = useQueryClient();
  return useMutation<void, AppError, void>({
    mutationFn: () => removeFriend(playerId),
    onSuccess: () => settle(client, reread, true),
  });
}

function rereadIfMoved(client: QueryClient, error: AppError, reread: Reread) {
  return stateMoved(error) ? Promise.all([reread(), rereadTheLists(client)]) : undefined;
}

/** The surface's own read, this feature's lists, and every face where the friendship turned. */
function settle(client: QueryClient, reread: Reread | undefined, faces: boolean) {
  return Promise.all([
    reread?.(),
    rereadTheLists(client),
    ...(faces ? rereadEveryFace(client) : []),
  ]);
}

/** The surface's own read, this feature's lists, and Home — where a request's card stood. */
function rereadHomeToo(client: QueryClient, reread: Reread | undefined) {
  return Promise.all([
    reread?.(),
    rereadTheLists(client),
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
  ]);
}

/** **This feature's own lists** — the page's tabs, the sheet's groups, the You tab's row. */
function rereadTheLists(client: QueryClient) {
  return client.invalidateQueries({ queryKey: friendKeys.all });
}

/**
 * **Every read that draws a face** — the decks (and Fill in and posting under each group's root),
 * every game still filling and every booked game in detail, and Home.
 */
function rereadEveryFace(client: QueryClient) {
  return [
    client.invalidateQueries({ queryKey: proposalKeys.decks() }),
    client.invalidateQueries({ queryKey: proposalKeys.proposals() }),
    client.invalidateQueries({ queryKey: proposalKeys.bookings() }),
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
  ];
}

/**
 * **The eight friends writes, and what each re-reads**
 * ([#753](https://github.com/Raketa02/Raketa/issues/753), [#756](https://github.com/Raketa02/Raketa/issues/756),
 * [#758](https://github.com/Raketa02/Raketa/issues/758), [#765](https://github.com/Raketa02/Raketa/issues/765);
 * ADR-0202 §1–§2, §4).
 *
 * | Hook | Route | Re-reads |
 * | --- | --- | --- |
 * | `useOpenFriendLink` | `POST /friends/links/{code}/opening` | Home and the bell for `ASKED_YOU`; every face for `FRIEND` |
 * | `useAskToBeFriends` | `POST /friends/requests` | the surface's own read; every face too, when the requests crossed |
 * | `useAcceptFriendRequest` | `POST …/{id}/acceptance` | the surface's own read, every face, and Home |
 * | `useSetAsideFriendRequest` | `POST …/{id}/set-aside` | Home, where the card was, and the surface's own read |
 * | `useCancelFriendRequest` | `DELETE /friends/requests/{id}` | the surface's own read |
 * | `useRemoveFriend` | `DELETE /friends/{id}` | the surface's own read, and every face |
 * | `useAskForALevel` | `POST /friends/{id}/level-asks` | this feature's lists — the picker's among them |
 * | `useSetAsideLevelAsks` | `POST /friends/level-asks/{sport}/set-aside` | Home, where the card was, and the bell |
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
 * ## Opening somebody's link (#756)
 *
 * **Opening a link puts its owner's request on the opener's Home** (the mechanics §4.2), so an
 * `ASKED_YOU` re-reads Home, the bell (its notice; the caller hands that re-read in) and this
 * feature's lists; a `FRIEND` may be the opener's own request crossing the owner's, so it re-reads
 * every face as an accept does; the opener's own link (`NONE`) moves nothing. **It is idempotent**
 * — opened again, it makes no second request — so it is retried as a read is: a lost race
 * (`concurrent_modification`) once, and the network's own failures by the app's rule for reads.
 * **And it is answered now or not at all** (`networkMode: 'always'`): a link the phone opened
 * offline is not landed on Home on a reconnect the player never saw; it fails, and the links
 * feature says why.
 *
 * ## Asking a friend to get a Level (#758)
 *
 * **The picker's row reads *Asked* on the server's answer**: the ask settles once this feature's
 * lists have re-read — the picker's `GET /friends?sport=` among them, whose `level_asked_in` says it
 * — so the button stays busy until the row under it already says so. It moves no face: a Level
 * asked for is not a Level got.
 *
 * ## Not now on a friend's ask for a level (#765)
 *
 * **It tells the reader where the level still is, then re-reads Home and the bell**: the card's
 * toast (`onSetAside`, handed in with its words) and the two reads the server took the asks off. It names
 * no friend's list — an ask set aside changes nothing any of them draws. It settles once both have
 * re-read, so Not now stays busy until Home no longer holds the card. It is idempotent, and
 * `concurrent_modification` is the state moving: re-read, and say nothing.
 *
 * ## A refusal that is the state moving is a re-read
 *
 * `already_friends`, `friend_request_already_sent` and `friend_request_not_found` say the surface
 * was drawn from a state that has since moved — accepted on another phone, cancelled by them — and
 * `concurrent_modification` that two acts on the pair raced. **So does `player_unavailable`** (#799,
 * ADR-0204 §2): they turned *Show me to new people* off since the surface was read, and share no
 * group, game or friendship with the asker. It names nothing, so nothing is said: the record read
 * again is refused with its own one line, which is the answer. So do an ask's three (#758):
 * `level_already_asked` (asked from another phone), `already_has_a_level` (they got one since the
 * picker was read — the row turns pickable) and `friend_not_found` (no longer friends — the row
 * goes). **None of them is retried**: asking and
 * accepting are not idempotent, and the global rule retries no mutation. The surface re-reads
 * instead, and the pill or the button it draws next is the answer. Any other refusal is said where
 * it was pressed.
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { proposalKeys } from '@/features/proposals/types';
import type { AppError } from '@/shared/errors';
import { shouldRetryQuery } from '@/shared/lib/query-client';
import type { Sport } from '@/shared/vocabulary/sport';

import { movesTheFaces, type AskedWhere } from '../domain/friendship';
import type { FriendRelation } from '../domain/vocabulary';
import {
  acceptFriendRequest,
  askForALevel,
  askToBeFriends,
  cancelFriendRequest,
  openFriendLink,
  removeFriend,
  setAsideFriendRequest,
  setAsideLevelAsks,
} from '../use-cases/friends';

import { friendKeys } from './friendKeys';

/** The surface's own re-read, handed in by the screen that holds it — see the module note. */
export type Reread = () => Promise<unknown>;

/** Two acts on the same thing raced, and this one lost — the one refusal an idempotent act retries. */
export const RACED = 'concurrent_modification';

/** The refusals that mean the surface was drawn from a state that has moved. */
const MOVED: ReadonlySet<string> = new Set([
  'already_friends',
  'friend_request_already_sent',
  'friend_request_not_found',
  'level_already_asked',
  'already_has_a_level',
  'friend_not_found',
  // Not askable any more — the record read again says so, with its one refusal (#799).
  'player_unavailable',
  RACED,
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

/**
 * **Ask a friend to get a Level in the picker's sport** (#758), from this group's Friends tab — see
 * the module note. Not retried, as no write here is: a second ask is `level_already_asked`.
 */
export function useAskForALevel(playerId: string, sport: Sport, groupId: string) {
  const client = useQueryClient();
  return useMutation<void, AppError, void>({
    mutationFn: () => askForALevel(playerId, sport, groupId),
    onSuccess: () => settle(client, undefined, false),
    onError: (error) => rereadIfMoved(client, error),
  });
}

/**
 * **Not now on Home's ASKED FOR A LEVEL card** (#765) — every ask in the sport set aside. See the
 * module note.
 *
 * @param rereadBell the bell's re-read, handed in: the server takes the asks' rows off it.
 * @param onSetAside what the card says once it is done — its toast, whose words are the card's.
 */
export function useSetAsideLevelAsks(sport: Sport, rereadBell: Reread, onSetAside: () => void) {
  const client = useQueryClient();
  return useMutation<void, AppError, void>({
    mutationFn: () => setAsideLevelAsks(sport),
    onSuccess: () => {
      onSetAside();
      return rereadHomeAndBell(client, rereadBell);
    },
    onError: (error) => (stateMoved(error) ? rereadHomeAndBell(client, rereadBell) : undefined),
  });
}

/**
 * **Home and the bell, read again** — after Not now on a level ask, and after its start was refused
 * because the level is already got (`useGetAskedLevel`): either way the card has gone on the server,
 * and the bell's *level asked* row with it (#765).
 */
export function rereadHomeAndBell(client: QueryClient, rereadBell: Reread) {
  return Promise.all([rereadBell(), client.invalidateQueries({ queryKey: proposalKeys.home() })]);
}

/**
 * **Open somebody's link** — the code, checked as the link was read; answers where the opener stands
 * with its owner once it is. See the module note.
 *
 * @param rereadBell the bell's re-read, handed in — `notifications` draws this feature's controls
 *   through the record, so naming its keys here would be a dependency both ways.
 */
export function useOpenFriendLink(rereadBell: Reread) {
  const client = useQueryClient();
  return useMutation<FriendRelation, AppError, string>({
    mutationFn: (code) => openFriendLink(code),
    // Idempotent, so retried as a read is — the network's failures twice, and a lost race once.
    retry: (failures, error) =>
      (error.code === RACED && failures < 1) || shouldRetryQuery(failures, error),
    networkMode: 'always',
    onSuccess: (relation) => {
      if (relation === 'ASKED_YOU') return rereadHomeToo(client, rereadBell);
      if (relation === 'FRIEND') return settle(client, undefined, true);
      return undefined;
    },
  });
}

function rereadIfMoved(client: QueryClient, error: AppError, reread?: Reread) {
  return stateMoved(error) ? Promise.all([reread?.(), rereadTheLists(client)]) : undefined;
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
function rereadHomeToo(client: QueryClient, reread?: Reread) {
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

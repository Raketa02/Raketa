/**
 * The rooms list, and the one join a booked game reads it through.
 *
 * | | |
 * | --- | --- |
 * | `useConversations` | `GET /conversations` — every room you are a member of |
 * | `useGameRoom` | the room a booked game's chat is, found by its game |
 * | `useGameRooms` | every booked game's room, by its game, for Home's cards |
 *
 * **Nothing is re-sorted and nothing is filtered.** Every room on the list is one the reader is a
 * member of, because membership is enforced on the route. A client filter here would be this app
 * holding a second opinion about who is in a room.
 *
 * It was also the Chats tab's inbox and the old loop's chat doors — a challenge joining its way
 * into its room — until that loop was removed ([#576](https://github.com/Raketa02/Raketa/issues/576)).
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Conversation } from '../domain/conversation';
import { readConversations } from '../use-cases/readConversations';

import { conversationKeys } from './conversationKeys';

/**
 * **The app-wide defaults, chosen rather than inherited** — thirty seconds stale, and the focus
 * refetch already wired from `AppState`.
 *
 * Nothing on this list is a number and nothing drawn from it is a clock: it is a set of rooms, so a
 * list served from cache is internally consistent rather than merely recent, and foregrounding is
 * what makes it current. That is `gameKeys`' reasoning on the same class of read. `retry` is the
 * app-wide default too — a conversation is append-ordered; see `conversationKeys.ts`.
 */
export function useConversations() {
  return useQuery<readonly Conversation[], AppError>({
    queryKey: conversationKeys.list(),
    queryFn: ({ signal }) => readConversations({ signal }),
  });
}

/**
 * **A booked game's room, found by its game** ([#556](https://github.com/Raketa02/Raketa/issues/556)).
 *
 * A booked game's room opens with the booking and is about its game from its first moment (the
 * mechanics §14.3), so every row of it carries the `game_id` the booking's details name — and that
 * is the join `GET /bookings/{id}` documents: *the chat is the reader's room whose `game_id` is this
 * game's*. No read carries a conversation id, and none should (ADR-0149 §3).
 *
 * `listed` says whether the list has been heard from, because the chat screen behind the details
 * has two different things to say while it has no room: *still finding it*, and *there is none* —
 * and `paused` and `error` the two others every read has: offline, and refused.
 * It fails soft — no room is no door.
 */
export function useGameRoom(gameId: string | undefined): {
  readonly conversationId: string | undefined;
  readonly listed: boolean;
  /** The list is held while offline, to resume on reconnect. */
  readonly paused: boolean;
  /** The list's read was refused, and nothing was listed before it. */
  readonly error: AppError | null;
  readonly retry: () => void;
} {
  const { data, error, fetchStatus, refetch } = useConversations();
  const room =
    gameId === undefined ? undefined : data?.find((conversation) => conversation.gameId === gameId);
  return {
    conversationId: room?.conversationId,
    listed: data !== undefined,
    paused: fetchStatus === 'paused',
    error: data === undefined ? error : null,
    retry: () => void refetch(),
  };
}

/**
 * **Every booked game's room, by its game** — the list form of {@link useGameRoom}, for Home's rail,
 * whose cards each say whether their game's chat is open: the join runs once at the surface, and
 * each card is handed its own answer.
 */
export function useGameRooms(): ReadonlyMap<string, string> {
  const { data } = useConversations();
  return new Map(
    (data ?? []).flatMap((room) =>
      room.gameId === undefined ? [] : [[room.gameId, room.conversationId] as const],
    ),
  );
}

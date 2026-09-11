/**
 * The one read this feature has today, and the one reading of it the Chats tab wants.
 *
 * | | |
 * | --- | --- |
 * | `useConversations` | `GET /conversations` — every room you are a member of |
 * | `useConversationRows` | the same list, with the reader known, for the `CONVERSATIONS` section |
 *
 * **Nothing is re-sorted and nothing is filtered.** The order is the server's — *by the last
 * entry, newest first* — and every room on the list is one the reader is a member of, because
 * membership is enforced on the route. A client filter here would be this app holding a second
 * opinion about who is in a room.
 *
 * Who the reader is comes from `useCurrentUser`, exactly as the challenge inbox and the games
 * list take it: no route serves a player their own id, and a row draws **the others** in the room.
 */

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { useCurrentUser } from '@/features/auth/types';
import type { AppError } from '@/shared/errors';

import type { Conversation } from '../domain/conversation';
import { ROOM_OPENING_BOUND_MS, ROOM_OPENING_POLL_MS } from '../domain/roomOpening';
import { readConversations } from '../use-cases/readConversations';

import { conversationKeys } from './conversationKeys';

/**
 * **The app-wide defaults, chosen rather than inherited** — thirty seconds stale, and the focus
 * refetch already wired from `AppState`.
 *
 * It is the deliberate opposite of `useChallengeList` one section up, which zeroes `staleTime`,
 * and the difference is what each read is **for**. That one feeds a **count on permanent chrome**,
 * where thirty seconds of staleness is a number claiming something is waiting when it is not.
 * Nothing on this list is a number and no row on it draws a clock: it is a set of rooms the player
 * is reading, so a list served from cache is internally consistent rather than merely recent, and
 * foregrounding is what makes it current. That is `gameKeys`' reasoning on the same class of read.
 *
 * `retry` is the app-wide default too, and stays there: Play's *nothing retries without the player
 * asking* is about a ranked list moving under a finger, and a conversation is append-ordered — see
 * `conversationKeys.ts`.
 */
export function useConversations() {
  return useQuery<readonly Conversation[], AppError>({
    queryKey: conversationKeys.list(),
    queryFn: ({ signal }) => readConversations({ signal }),
  });
}

/**
 * The `CONVERSATIONS` section's query, with the reader beside it.
 *
 * `rows` is empty until there is both a list and a reader — the same shape `useChallengeInbox`
 * has, and for the same reason: a row is drawn *about the other people in it*, so drawing one
 * before the reader is known would put the reader's own face in their own row for a frame.
 */
export function useConversationRows() {
  const conversations = useConversations();
  const playerId = useCurrentUser().data?.id;

  return {
    ...conversations,
    playerId,
    rows: playerId === undefined ? [] : (conversations.data ?? []),
  };
}

/**
 * **The way into the room a challenge opened**, or nothing.
 *
 * A **client join over `GET /conversations`**, which is
 * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §3's answer to the same question one context over: *the chat door is a fact no route provides
 * and the surface genuinely needs.* No route serves a challenge its conversation, and ADR-0146
 * forbids `challenges` knowing that this context exists — so what crosses the seam is the address
 * of a room rather than a field on a challenge.
 *
 * **It fails soft, and the absence is ordinary rather than an error.** A room opens on the *first
 * acceptance*, so a challenge nobody has answered has none; a room is **destroyed** when the
 * episode it was opened for ends, so a challenge that is over has none either. Both draw **no
 * door**, which is what keeps a dead control off the screen.
 *
 * It costs nothing new on a warm cache — the Chats tab reads this list anyway — and on a cold one
 * it costs a list the player was about to need. Stated plainly, as ADR-0149 states its own
 * version: **a challenge screen reads a list belonging to a context it is forbidden to know
 * about, and gets away with it because it reads that list as *the player's rooms*.**
 *
 * **An absent challenge is the same nothing as an unmatched one**, which is what the second caller
 * needs: the game screen's plan block joins on the challenge its *game* names, and a games list
 * that has not landed yet holds no challenge to join on. A hook cannot be called conditionally, so
 * the alternative is a call site inventing an id that matches nothing — the same answer, spelled
 * where it can go wrong.
 */
export function useChatDoor(challengeId: string | undefined): string | undefined {
  const { data } = useConversations();
  return doorIn(data, challengeId);
}

/**
 * **What the screen that just said *I'm in* is waiting for** — and the reply is what decides it.
 *
 * A reply of `AWAITING_ANSWERS` or `LINE_UP_INCOMPLETE` opened or grew a room and nothing else, so
 * the room is the whole of the wait. A reply of `ON` says a **game exists** — it is opened inline
 * with the accept that filled the last seat — while the room learns *which* off the outbox a
 * moment later (`GameNoted`, `tell_the_room.py`); a push that waited only for the room would land
 * in one that draws no plan card yet, and nothing nudges when a game is noted. So the wait is for
 * the row to say so, which is what the reply already knew.
 */
export type RoomExpectation = 'the-room' | 'the-room-and-its-game';

/**
 * **The same door, waited for** — the join above, with the list re-read while what is expected is
 * on its way ([`domain/roomOpening`](../domain/roomOpening.ts)).
 *
 * While `awaiting` names an expectation the list does not yet meet, the list is re-read on
 * `ROOM_OPENING_POLL_MS` and stops the moment it does, or at `ROOM_OPENING_BOUND_MS`, whichever is
 * first. It is a second observer over the **same** query, so nothing is fetched twice and the
 * Chats tab reads whatever this found; `refetchInterval` is the mechanism because it is Query's
 * own and stops itself, where a hand-rolled loop would be a request outliving the screen.
 *
 * Two answers, because they are two facts. `door` is the join as it stands — a room the list
 * holds, whatever else it knows — and is what a button is drawn from. `arrived` is whether the
 * expectation is met, and is what a push waits for: a room listed without its game is a door
 * and not yet an arrival.
 *
 * The bound is held here rather than by the caller because it is a fact about the wait and not
 * about the screen: a caller says what it expects, and this says when to stop asking. `awaiting`
 * going false resets it, so a second press waits its own full bound.
 */
export function useAwaitedChatDoor(
  challengeId: string,
  awaiting: RoomExpectation | false,
): { readonly door: string | undefined; readonly arrived: boolean } {
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    setExpired(false);
    if (awaiting === false) return undefined;
    const bound = setTimeout(() => setExpired(true), ROOM_OPENING_BOUND_MS);
    return () => clearTimeout(bound);
  }, [awaiting]);

  const { data } = useQuery<readonly Conversation[], AppError>({
    queryKey: conversationKeys.list(),
    queryFn: ({ signal }) => readConversations({ signal }),
    refetchInterval: (query) =>
      awaiting !== false && !expired && !met(query.state.data, challengeId, awaiting)
        ? ROOM_OPENING_POLL_MS
        : false,
  });

  return {
    door: doorIn(data, challengeId),
    arrived: awaiting !== false && met(data, challengeId, awaiting),
  };
}

/** Whether the list already holds what is expected of this challenge's room. */
function met(
  rooms: readonly Conversation[] | undefined,
  challengeId: string,
  expectation: RoomExpectation,
): boolean {
  const room = rooms?.find((one) => one.challengeId === challengeId);
  if (room === undefined) return false;
  return expectation === 'the-room' || room.gameId !== undefined;
}

/** The join itself: the room this challenge opened, in the player's own rooms, or nothing. */
function doorIn(
  rooms: readonly Conversation[] | undefined,
  challengeId: string | undefined,
): string | undefined {
  if (challengeId === undefined) return undefined;
  return rooms?.find((room) => room.challengeId === challengeId)?.conversationId;
}

/**
 * **The same join, over a list** — every room this player holds, keyed by the challenge that
 * opened it.
 *
 * A rail of games needs a door per card and a hook cannot be called in a loop, so the join runs
 * **once at the surface** and each card is handed the answer for its own challenge. That is also
 * what keeps [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md)
 * §3.4's rule true of the card: it is handed the game, the plan beside it and the address of the
 * room, and reaches for nothing itself.
 *
 * It fails soft exactly as {@link useChatDoor} does, and for the same two reasons — a room opens
 * on the first acceptance and is destroyed when the episode ends, so a missing entry is the
 * ordinary state and never an error.
 */
export function useChatDoors(): ReadonlyMap<string, string> {
  const { data } = useConversations();

  return new Map((data ?? []).map((room) => [room.challengeId, room.conversationId]));
}

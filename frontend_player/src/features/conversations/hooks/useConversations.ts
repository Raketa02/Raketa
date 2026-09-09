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

import { useQuery } from '@tanstack/react-query';

import { useCurrentUser } from '@/features/auth/types';
import type { AppError } from '@/shared/errors';

import type { Conversation } from '../domain/conversation';
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
 */
export function useChatDoor(challengeId: string): string | undefined {
  const { data } = useConversations();

  return data?.find((room) => room.challengeId === challengeId)?.conversationId;
}

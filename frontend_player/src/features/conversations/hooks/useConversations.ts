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

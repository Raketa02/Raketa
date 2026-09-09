/**
 * **One stream per open room, and the nudge invalidates.**
 *
 * The whole of the client half of
 * [ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md):
 * a frame says *this room moved* and the answer is to ask the ordinary read path again. It is four
 * lines because the record spent its design budget making it four lines.
 *
 * ## There is no second store, and no cursor arithmetic
 *
 * **The Query cache stays the single copy** (ADR-0147 §10, and the posture `docs/architecture.md`
 * Part 7 already takes for mutations). Nothing here appends an entry, reconciles a sequence or
 * holds a high-water mark: `useConversation`'s pages **are** the mark, so re-reading them is
 * fetching from the client's own cursor by construction. That is what makes a dropped frame free —
 * the next nudge repairs it, because what is asked for was never the frame's number.
 *
 * **And the number is not here to be misused.** `LiveNudge` carries the room and nothing else; the
 * port reads `last_seq` to know a frame is a nudge and drops it. The one field this hook reads is
 * `conversationId`, and it reads it to **check**, never to fetch.
 *
 * ## What the invalidation costs, and what it deliberately does not touch
 *
 * The room is an **infinite** query, so invalidating it re-reads every page the client is holding
 * rather than only the newest. On a room somebody has paged back through three times that is four
 * requests for one message. It is the honest price of the cache being the single copy — the
 * alternative is a client assembling the newest page itself, which is the second store this whole
 * design refuses — and at two-to-four members it is nothing.
 *
 * **The Chats list is not invalidated, and the cost of that is stated rather than glossed.** A
 * send does invalidate it, because the reply says nothing about the row's order and the player is
 * the one who moved it. A nudge is not an act: the list sits **mounted** under this screen in the
 * stack, so invalidating it would refetch every room's row on every inbound message, for a line
 * nobody is looking at — and it is the same shape of cost ADR-0147 already prices per message.
 *
 * What that leaves is real and small: **a row's last line can be one message behind when a player
 * comes back to the list**, because popping the stack is not a focus event and an active query
 * does not refetch on staleness alone. It is the state #363 shipped with — a message from somebody
 * else has never moved a row without a refetch — so this ticket does not make it worse, and it is
 * one line to reverse here the day the trade looks wrong.
 *
 * ## Play's posture is not in question here
 *
 * *Nothing in Play background-refetches* is a **scope clarification rather than an exception**
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §2.4):
 * that rule is written about a ranked list reordering under a finger, and a conversation is
 * append-ordered — there is no ordering to lose, and the two rules never touch.
 */

import { useEffect, useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { useLiveStream, type LiveStreamStatus } from '@/shared/lib/platform';

import { conversationKeys } from './conversationKeys';

/**
 * Follow one room for as long as it is on screen, and report what the channel is doing.
 *
 * The status is folded into what the room **draws** by `domain/liveState.ts`, and never read as a
 * socket by a component: this hook hands up a value, and the two conditions on the *not live* line
 * are that fold's.
 */
export function useLiveConversation(conversationId: string): LiveStreamStatus {
  const channel = useLiveStream();
  const client = useQueryClient();
  const [status, setStatus] = useState<LiveStreamStatus>('connecting');

  useEffect(
    () =>
      channel.follow({
        conversationId,
        onNudge: (nudge) => {
          // A stream carries one room, so this can only fail in a build where something has
          // gone wrong — and the failure it would otherwise be is a room re-read on news about
          // another one, which nothing on screen would show.
          if (nudge.conversationId !== conversationId) return;

          void client.invalidateQueries({ queryKey: conversationKeys.room(conversationId) });
        },
        onStatus: setStatus,
      }),
    [channel, client, conversationId],
  );

  return status;
}

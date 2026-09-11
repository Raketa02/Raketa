/**
 * **One stream per open room: the nudge invalidates, and the typing frame draws.**
 *
 * The whole of the client half of
 * [ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md):
 * a frame says *this room moved* and the answer is to ask the ordinary read path again. It is four
 * lines because the record spent its design budget making it four lines. Since
 * [ADR-0156](../../../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)
 * the same stream carries **who is typing**, and that frame gets the opposite answer: it is held
 * as state and drawn, and it invalidates nothing — see below.
 *
 * ## Typing is not query cache state
 *
 * It is ephemeral, it moves no `seq`, and it must never touch the stream's data. So it is the one
 * thing this hook keeps in React state: the **roster** the last frame carried, replaced whole by
 * the next one — an empty list is the clear — and folded against the channel by
 * `domain/typing.ts`, which is what makes a roster vanish the moment the channel is not live.
 * **Nothing here re-reads on a typing frame**, and nothing may: the fact is in the frame and there
 * is no read path for it to defer to.
 *
 * **Both come off one `follow`**, which is why they are one hook and not two: the port opens one
 * stream per call, and a second hook following the same room would be the second stream this
 * feature asserts it never opens.
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
 * ## A nudge re-reads what the room draws — the stream and the plan
 *
 * The plan card pinned under the header is read off `GET /plans`, a list beside the room and never
 * inside it (ADR-0148 §7), and a slot another member set reaches this phone as a system line on
 * this very frame. A nudge that re-read the stream alone left the card saying `Where` under
 * *tomek.p set the place* until the app was next foregrounded
 * ([#405](https://github.com/Raketa02/Raketa/issues/405)) — which is the state ADR-0147 §12 had
 * written down as *free*, true of the line and not yet of the card. So the nudge invalidates
 * `planKeys.list()` beside the room, and the card, the quick chips and the header's state word all
 * follow the line, because all three are readers of that one list.
 *
 * **On every nudge, and not on sighting a plan line.** The alternative — read the re-fetched
 * stream for a new `PLACE_RECORDED | DAY_RECORDED | HOUR_RECORDED | PLAN_LOCKED` above the last
 * `seq` held, and invalidate the plan only then — was considered and is refused. A nudge carries
 * no content by construction and the port drops the number; a trigger derived from the stream's
 * codes would couple the card's liveness to the line vocabulary, so a fifth plan line this build
 * cannot read — the one case an old phone most needs a re-read for — would leave the card stale
 * precisely there. *A build too old to read a code says so*; it must not also go quietly stale.
 * And the stream's opening frame is a nudge too (ADR-0147 §4), so every connect and every
 * fifteen-minute reconnect re-reads the plan for free, which is the catch-up after a stretch out
 * of the room.
 *
 * ## What the invalidation costs, and what it deliberately does not touch
 *
 * The room is an **infinite** query, so invalidating it re-reads every page the client is holding
 * rather than only the newest. On a room somebody has paged back through three times that is four
 * requests for one message. It is the honest price of the cache being the single copy — the
 * alternative is a client assembling the newest page itself, which is the second store this whole
 * design refuses — and at two-to-four members it is nothing. The plan list is one short request
 * more, on every nudge including the ones that were a message: ADR-0147 priced *one extra round
 * trip per delivered message*, and inside a room it is two, both to lists the room draws.
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

import { planKeys } from '@/features/plans/types';
import { useLiveStream, type LiveStreamStatus } from '@/shared/lib/platform';

import { shownTypists } from '../domain/typing';

import { conversationKeys } from './conversationKeys';

/** What the channel is doing, and who it says is typing — an empty list on any channel not live. */
export interface LiveConversation {
  readonly status: LiveStreamStatus;
  /** As the server reported it: ids, not names, and never filtered here — that is the fold's. */
  readonly typing: readonly string[];
}

/**
 * Follow one room for as long as it is on screen, and report what the channel is doing.
 *
 * The status is folded into what the room **draws** by `domain/liveState.ts`, and never read as a
 * socket by a component: this hook hands up a value, and the two conditions on the *not live* line
 * are that fold's. The roster is folded against the same status before it leaves here, so no
 * component can draw a typist off a channel that could not deliver the clear.
 */
export function useLiveConversation(conversationId: string): LiveConversation {
  const channel = useLiveStream();
  const client = useQueryClient();
  const [status, setStatus] = useState<LiveStreamStatus>('connecting');
  const [roster, setRoster] = useState<readonly string[]>([]);

  useEffect(
    () =>
      channel.follow({
        conversationId,
        onNudge: (nudge) => {
          // A stream carries one room, so this can only fail in a build where something has
          // gone wrong — and the failure it would otherwise be is a room re-read on news about
          // another one, which nothing on screen would show.
          if (nudge.conversationId !== conversationId) return;

          // What the room draws: the stream, and the plan pinned over it. Never the Chats list.
          void client.invalidateQueries({ queryKey: conversationKeys.room(conversationId) });
          void client.invalidateQueries({ queryKey: planKeys.list() });
        },
        onTyping: (typing) => {
          if (typing.conversationId !== conversationId) return;

          // Replaced whole, never merged: the frame is the roster, and an empty one is the clear.
          setRoster(typing.playerIds);
        },
        onStatus: (next) => {
          setStatus(next);
          // **Dropped, not hidden**: a channel that is not live cannot deliver the clear, and a
          // roster remembered across a reconnect would come back as a guess — the server
          // re-announces anybody still typing on its first check, which is the only honest source.
          if (next !== 'live') setRoster([]);
        },
      }),
    [channel, client, conversationId],
  );

  return { status, typing: shownTypists(status, roster) };
}

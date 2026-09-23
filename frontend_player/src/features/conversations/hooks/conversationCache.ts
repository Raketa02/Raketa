/**
 * **The one write another feature may make to this list** — dropping the room a court opened, on
 * the reply that took the reader off that court
 * ([#427](https://github.com/Raketa02/Raketa/issues/427)).
 *
 * `types.ts` exports this list's **key** to `features/challenges` so that an accept, a withdraw and
 * a departure can mark it stale — *invalidate rather than patch*, because none of those replies
 * carries a conversation and *"a client that removed a row itself would be asserting a deletion it
 * was not told about."* The departure is the one act where that argument turns over: its reply
 * says the reader's own seat is `LEFT`, and **membership is the accepted seats** (ADR-0146 §7), so
 * the reply *has* told the client they are out of the room. The row goes on the reply, and the
 * re-read that follows confirms it rather than causes it — which is what *gone without a refetch*
 * asks for, and why the leaver never sees their own row linger for a round trip.
 *
 * It is a function over the client rather than a filter over the rows, so what crosses the seam
 * is still an act on a list and never the shape of one: `features/challenges` says *the court
 * with this id is no longer mine*, and which rows that touches is decided here, where the rows'
 * shape is known. Keyed by the **challenge**, because that is the one id the departure has and
 * the one id both contexts already share.
 */

import type { QueryClient } from '@tanstack/react-query';

import type { Conversation } from '../domain/conversation';

import { conversationKeys } from './conversationKeys';

export function dropRoomOfChallenge(client: QueryClient, challengeId: string): void {
  client.setQueryData<readonly Conversation[] | undefined>(conversationKeys.list(), (held) =>
    held?.filter((room) => room.challengeId !== challengeId),
  );
}

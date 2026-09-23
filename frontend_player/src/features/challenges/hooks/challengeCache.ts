/**
 * **The one write another feature may make to this list** — dropping the row of a called-off
 * court, on the reply that cleared that court's card
 * ([ADR-0173](../../../../../docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md)).
 *
 * `types.ts` exports this list's **key** to `features/games` so the dismissal can mark it stale —
 * and this, so the row goes on the reply rather than a round trip later. The argument is the
 * departure's, one feature over (`conversationCache.ts`): a client removing a row itself asserts
 * a deletion it was told about, and the dismissal's reply *has* told it — `GET /challenges`
 * subtracts its reader off the set the reply just wrote to, so a list without this court is
 * exactly the next read's answer, arriving early. The re-read that follows confirms it rather than
 * causes it.
 *
 * A function over the client rather than a filter over the rows, for `dropRoomOfChallenge`'s
 * reason: what crosses the seam is an act on a list and never the shape of one. `features/games`
 * says *the court that became this game is cleared for me*, and which rows that touches is
 * decided here, where the rows' shape is known. Keyed by the **game**, because that is the one
 * id the dismissal has and the one the row carries for exactly this join (ADR-0172 §4).
 */

import type { QueryClient } from '@tanstack/react-query';

import type { Challenge } from '../domain/challenge';

import { challengeKeys } from './challengeKeys';

export function dropCourtOfGame(client: QueryClient, gameId: string): void {
  client.setQueryData<readonly Challenge[] | undefined>(challengeKeys.list(), (held) =>
    held?.filter((challenge) => challenge.gameId !== gameId),
  );
}

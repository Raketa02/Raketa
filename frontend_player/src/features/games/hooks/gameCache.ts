/**
 * **The one write another feature may make to this list** — dropping the card of a called-off
 * court, on the reply that cleared that court's row
 * ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §5). `dropCourtOfGame`'s mirror, one feature over, for its reason: a called-off court is one
 * fact on two of the reader's lists, and the dismissal — met from the Chats row's own door since
 * ADR-0175 — clears both, so the card goes on the reply through this rather than a round trip
 * later. A function over the client rather than a filter over the rows, so what crosses the seam
 * is an act on a list and never the shape of one.
 */

import type { QueryClient } from '@tanstack/react-query';

import type { Game } from '../domain/game';

import { gameKeys } from './gameKeys';

export function dropCardOfGame(client: QueryClient, gameId: string): void {
  client.setQueryData<readonly Game[] | undefined>(gameKeys.list(), (held) =>
    held?.filter((game) => game.gameId !== gameId),
  );
}

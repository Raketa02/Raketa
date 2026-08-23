/**
 * The second write another feature may make to this screen.
 *
 * `ADR-0054`'s third ask is *an action*, and until an action existed the whole of
 * it was invalidating `nowKeys`. It is a **cache write** now, because `ADR-0074`
 * has the action's own response carry Now's update: the server has just
 * recomposed this card at the instant the write happened, and asking for the
 * whole screen again would pay the full funnel for an answer already in hand.
 *
 * **Every sport's screen, not the selected one.** The sport is part of the key —
 * one request per chip, never a filter over a payload holding every sport — so a
 * match the player left is stale on `all` *and* on its own sport's screen, and
 * correcting only whichever chip she happened to be on would leave the other to
 * be discovered later as a card offering an act that is gone. `setQueriesData`
 * over `nowKeys.all` is what makes that one call rather than a loop over the five
 * chips this build happens to have.
 *
 * **Nothing is invalidated.** A departure changes more than one card — the
 * counting moves for everybody in the match, and a shelf could reorder — and none
 * of that is in the update, deliberately (`ADR-0070`). The next of the four asks
 * is what collects it. Marking the screen stale here would turn every action into
 * a refetch on the next focus, which is the cost `ADR-0074` refused by name.
 *
 * It lives in `hooks/` because a query client is Query's, and `use-cases/` is
 * pure — the pure half is `applyNowUpdate`, which is where the rule about *where
 * a card goes* is written and tested.
 */

import type { QueryClient } from '@tanstack/react-query';

import type { ComposedScreen, NowUpdate } from '../domain/ComposedScreen';
import { applyNowUpdate } from '../use-cases/applyNowUpdate';

import { nowKeys } from './nowKeys';

export function writeNowUpdate(client: QueryClient, update: NowUpdate): void {
  client.setQueriesData<ComposedScreen>({ queryKey: nowKeys.all }, (screen) =>
    screen === undefined ? screen : applyNowUpdate(screen, update),
  );
}

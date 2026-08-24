/**
 * What a taken seat writes into the cache, and the one place the two halves of an
 * answer go to two different keys.
 *
 * `ADR-0074`: the act's own response carries what Now needs, so nothing is
 * invalidated and nothing is fetched. What is new here is that a seat answer has
 * **two** halves with two different scopes, and sending either to the other's key
 * would be wrong in a way nobody would see for a while:
 *
 * - **The card goes to every sport's screen.** A card is a card whatever chip is
 *   held; a match she has just claimed is stale on `all` *and* on its own sport's
 *   screen, and correcting only the one she happens to be looking at leaves the
 *   other to be discovered later as a card offering an act that is gone. That is
 *   `writeNowUpdate`, unchanged.
 * - **The two regions go to the chip that was tapped, and only there.** They were
 *   **composed under it** — that is what the request's `sport` parameter is for —
 *   so writing `all`'s regions onto the padel screen would replace her filtered
 *   screen with somebody else's. Every other sport's screen keeps its own regions
 *   and takes the corrected card in place: the match sits in the region it was in
 *   until the next of `ADR-0054`'s four asks, saying exactly what it is doing.
 *   That is a card in the wrong *region* and never a card saying the wrong thing,
 *   which is the direction this should fail in.
 *
 * It lives in `hooks/` because a query client is Query's, beside the write it
 * extends; the pure halves are `applyNowUpdate` and `applySeatRegions`, which is
 * where the two rules are written and tested.
 */

import type { QueryClient } from '@tanstack/react-query';

import type { ComposedScreen, SeatAnswer } from '../domain/ComposedScreen';
import type { SportFilter } from '../mappers/codes';
import { applySeatRegions } from '../use-cases/applySeatRegions';

import { nowKeys } from './nowKeys';
import { writeNowUpdate } from './writeNowUpdate';

export function writeSeatAnswer(client: QueryClient, answer: SeatAnswer, sport: SportFilter): void {
  writeNowUpdate(client, answer.update);

  const regions = answer.regions;
  if (regions === undefined) return;

  client.setQueryData<ComposedScreen>(nowKeys.screen(sport), (screen) =>
    screen === undefined ? screen : applySeatRegions(screen, regions),
  );
}

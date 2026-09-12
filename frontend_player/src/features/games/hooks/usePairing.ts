/**
 * The court's pairing, read beside the game — **and only while there is one to read.**
 *
 * `GET /games/{game_id}/pairing` answers while the game is `AWAITING_ENTRY` and refuses by name
 * after it ([ADR-0161](../../../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)
 * §1), so the query is **enabled on that standing and on nothing else**: a result arm never asks,
 * and a game whose standing this build cannot read never asks either, because the one answer the
 * route could give it is the refusal. The surface that mounts this is the plan lead's court slot,
 * which the screen draws on the two plan-lead rungs and nowhere else — so the standing here is the
 * belt over the layout's braces, and neither is the other's reason.
 *
 * ## `null` is an answer, `undefined` is not yet
 *
 * The use case folds the route's three named refusals to `null` — *no pairing* — and the block
 * draws nothing for it, exactly as it draws nothing while the read is in flight or after it
 * failed. What the three states buy is not a different drawing but a different **posture**: an
 * answer is cached and re-asked on the usual clock, a failure is retried by the app's own rule,
 * and neither is reported as the other.
 *
 * ## It takes the app-wide defaults whole
 *
 * The same argument `gameKeys` makes for the list: this is a value read beside a record, not a
 * ranked list under a finger, and a refetch on focus is what keeps the figures current — the
 * pairing is *computed when you asked*, and a screen left open across a Level's movement should
 * show the new figures the next time it is looked at.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Game } from '../domain/game';
import type { Pairing } from '../domain/pairing';
import { readPairing } from '../use-cases/readPairing';

import { gameKeys } from './gameKeys';

export function usePairing(game: Game) {
  return useQuery<Pairing | null, AppError>({
    queryKey: gameKeys.pairing(game.gameId),
    queryFn: ({ signal }) => readPairing(game.gameId, { signal }),
    enabled: game.standing === 'AWAITING_ENTRY',
  });
}

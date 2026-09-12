/**
 * The fourth route: the court's pairing, **read beside the game and never on it**
 * ([ADR-0161](../../../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
 *
 * One of the two layers allowed to read generated types, and the only place this path is written
 * down. It is a file of its own rather than a fourth function in `gamesApi.ts` because that file
 * is *the three routes the result argument is*, and this is not one of them: nothing here is an
 * act, and the answer means what a card means for exactly as long as the game has not happened.
 *
 * ## A `signal`, because it is a read
 *
 * `gamesApi`'s asymmetry, on the same argument: a `GET` records nothing, so an abandoned one costs
 * nobody a row — and this one costs the whole Fit stack over the court, so a screen left before
 * the answer landed should not have it computed for nobody.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

import type { Cancellable } from './gamesApi';

type GamePairingResponse = components['schemas']['GamePairingResponse'];

/**
 * What this platform makes of your court, computed when you asked.
 *
 * `404 game_not_found` for a game that is not yours — one code for two cases, so an id cannot be
 * probed; `409 pairing_is_history` once the game has happened or its entry window closed on
 * silence. Both are answers rather than failures, and `use-cases/readPairing.ts` reads them so.
 */
export function getPairing(
  gameId: string,
  { signal }: Cancellable = {},
): Promise<GamePairingResponse> {
  return httpRequest<GamePairingResponse>({
    method: 'GET',
    path: `/api/v1/games/${gameId}/pairing`,
    authenticated: true,
    signal,
  });
}

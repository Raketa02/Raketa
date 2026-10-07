/**
 * **The three blocks routes**, and the only place their paths are written down
 * ([#587](https://github.com/Raketa02/Raketa/issues/587);
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
 *
 * One of the two layers allowed to read generated types.
 *
 * | Route | |
 * | --- | --- |
 * | `POST /blocks` | block — the other player and nothing else; 204, idempotent |
 * | `DELETE /blocks/{player_id}` | unblock — lifts the caller's own block; 204, never 404 |
 * | `GET /blocks` | *Blocked players* — the caller's own blocks, newest first |
 *
 * **Both writes are idempotent**, which is the correctness mechanism under a double tap: a second
 * block records nothing, and an unblock of somebody never blocked answers the same 204 — a
 * different answer would be the API reporting on somebody else's state.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type BlockPlayerRequest = components['schemas']['BlockPlayerRequest'];
type BlockedPlayersResponse = components['schemas']['BlockedPlayersResponse'];

const BLOCKS_PATH = '/api/v1/blocks';

/** The read may be abandoned: a `GET` records nothing, so a screen left mid-read costs nobody. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/**
 * **Block this player.** `cannot_block_yourself` for the caller's own id — never sent, since no row
 * is drawn on your own record — and `concurrent_modification` when two blocks of the same player
 * raced, whose retry is the idempotent no-op.
 */
export function postBlock(playerId: string): Promise<void> {
  const body: BlockPlayerRequest = { player_id: playerId };
  return httpRequest<void>({ method: 'POST', path: BLOCKS_PATH, body, authenticated: true });
}

/** **Unblock this player** — the caller's own block, and nobody else's. */
export function deleteBlock(playerId: string): Promise<void> {
  return httpRequest<void>({
    method: 'DELETE',
    path: `${BLOCKS_PATH}/${encodeURIComponent(playerId)}`,
    authenticated: true,
  });
}

/**
 * **Blocked players.** `block_state_unavailable` (503) when the blocks could not be read — a
 * failure, never an empty list.
 */
export function getBlockedPlayers({ signal }: Cancellable = {}): Promise<BlockedPlayersResponse> {
  return httpRequest<BlockedPlayersResponse>({
    method: 'GET',
    path: BLOCKS_PATH,
    authenticated: true,
    signal,
  });
}

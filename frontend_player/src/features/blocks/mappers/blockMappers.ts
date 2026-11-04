/**
 * *Blocked players*, from the wire's spelling into this app's — the wire boundary.
 *
 * The list is carried whole and in the server's order, newest first: nothing is re-sorted, and an
 * empty list is a real answer (*You haven't blocked anyone.*), never a failure. When each block was
 * made crosses on the wire and is not carried — nothing draws it.
 */

import type { components } from '@/generated/schema';

import type { BlockedPlayer } from '../domain/blockedPlayer';

type BlockedPlayersResponse = components['schemas']['BlockedPlayersResponse'];
type BlockedPlayerSchema = components['schemas']['BlockedPlayerSchema'];

export function toBlockedPlayers(response: BlockedPlayersResponse): readonly BlockedPlayer[] {
  return response.players.map(toBlockedPlayer);
}

function toBlockedPlayer(served: BlockedPlayerSchema): BlockedPlayer {
  return {
    playerId: served.player_id,
    name: served.nickname,
    ...(served.photo_url === undefined ? {} : { photoUrl: served.photo_url }),
  };
}

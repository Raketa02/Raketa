/**
 * **Block, unblock, and read your blocks** — pass-throughs with a mapping, which is what ADR-0009's
 * uniform-strict escape hatch is for: there is no rule a client applies to a block. Who may be put
 * on a court together is the server's pair rule, and the one fact a record carries about a block is
 * the server's answer.
 */

import { deleteBlock, getBlockedPlayers, postBlock, type Cancellable } from '../api/blocksApi';
import type { BlockedPlayer } from '../domain/blockedPlayer';
import { toBlockedPlayers } from '../mappers/blockMappers';

export function block(playerId: string): Promise<void> {
  return postBlock(playerId);
}

export function unblock(playerId: string): Promise<void> {
  return deleteBlock(playerId);
}

export function readBlockedPlayers(ask: Cancellable = {}): Promise<readonly BlockedPlayer[]> {
  return getBlockedPlayers(ask).then(toBlockedPlayers);
}

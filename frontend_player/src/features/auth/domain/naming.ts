/**
 * **Named** — holding a nickname
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3, amending
 * ADR-0185 §4).
 *
 * The one rule about the naming the client applies, and it applies it in two places: the entry
 * gate, whose first destination for anybody who plays is *no nickname*, and the naming step,
 * which says one sentence more to an account an Invitation opened. Neither kind of account holds
 * a nickname until the naming, and neither holds a player name at all: the name a club types for
 * its Administrator stays the Administrator's (§4).
 */

import type { AuthenticatedUser } from './AuthenticatedUser';

/** Whether the player holds a nickname — past the gate's first destination. */
export function named(player: Pick<AuthenticatedUser, 'nickname'>): boolean {
  return player.nickname !== undefined;
}

/**
 * **An account an Invitation opened** — one that runs a club's groups, reaching the naming through
 * *Start playing* (ADR-0185 §4). The step tells it what the nickname is for: it has been known to
 * its club by the name the club typed, and to players it will be known by this.
 */
export function openedByInvitation(player: {
  readonly profiles: Pick<AuthenticatedUser['profiles'], 'administers'>;
}): boolean {
  return player.profiles.administers.length > 0;
}

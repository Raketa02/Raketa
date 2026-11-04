/**
 * **Named** — holding a nickname
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3, amending
 * ADR-0185 §4).
 *
 * The one rule about the naming the client applies, and it applies it in two places: the entry
 * gate, whose first destination for anybody who plays is *no nickname*, and the naming step,
 * which says one sentence more to an account that runs a club's groups. Neither kind of account holds
 * a nickname until the naming, and neither holds a player name at all: the name a club types for
 * its Administrator stays the Administrator's (§4).
 */

import type { AuthenticatedUser } from './AuthenticatedUser';

/** Whether the player holds a nickname — past the gate's first destination. */
export function named(player: Pick<AuthenticatedUser, 'nickname'>): boolean {
  return player.nickname !== undefined;
}

/**
 * **Whether the account runs a club's groups** — the phone's one sign of an account an Invitation
 * opened, reaching the naming through *Start playing* (ADR-0185 §4): `/users/me` says which clubs an
 * account administers and not how it was opened. The step tells such an account what the nickname
 * is for: its club has known it by the name the club typed, and players will know it by this. An
 * account that signed up and accepted an invitation before naming itself reads the same line,
 * which is as true for it.
 */
export function runsAClub(player: {
  readonly profiles: Pick<AuthenticatedUser['profiles'], 'administers'>;
}): boolean {
  return player.profiles.administers.length > 0;
}

/**
 * **Named in full** — a name *and* a nickname
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §4, amending ADR-0171 §3).
 *
 * The one rule about the naming the client applies, and it applies it in two places: the entry
 * gate, whose first destination for anybody who plays is *not named in full*, and the naming step,
 * which asks only for what is missing. An account sign-up creates holds neither until the naming;
 * an account an Invitation opened holds the **Name its club typed and no Nickname**, which is the one
 * shape with half — so the step shows the nickname's box alone and sends that name beside it, and
 * the naming stays one act carrying both.
 */

import type { AuthenticatedUser } from './AuthenticatedUser';

type Named = Pick<AuthenticatedUser, 'name' | 'nickname'>;

/** Whether the player holds both a name and a nickname — past the gate's first destination. */
export function namedInFull(player: Named): boolean {
  return player.name !== undefined && player.nickname !== undefined;
}

/**
 * **The name an account holds without a nickname** — the club's — which the naming keeps, asking
 * only for the nickname; nothing for an account holding neither, or both.
 */
export function heldNameWithoutNickname(player: Named): string | undefined {
  return player.nickname === undefined ? player.name : undefined;
}

/**
 * **What the account panel says** — the identity as one spoken answer, and the wait.
 *
 * The You tab is one of the two screens that draw a player's handle
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §4): the name, `@nickname` under it, and the email under that. The mark is `atNickname`'s,
 * spelled once in `shared/formatting` so this tab and the record cannot disagree about it.
 */

import { atNickname } from '@/shared/formatting/playerName';

export const ACCOUNT_LOADING = 'Loading your profile…';

/** The one way back to the beginning, and what it says while it is happening. */
export const SIGN_OUT = { label: 'Sign out', busyLabel: 'Signing out…' } as const;

/**
 * The identity as a listener meets it — **one element**, so *who am I signed in as* is one
 * answer rather than three stops, in the order the lines are drawn.
 *
 * The name and the handle are absent on an account that has not named itself yet. That
 * account is held at the naming step and never reaches this tab, so the clauses are dropped
 * rather than spoken as nothing.
 */
export interface AccountIdentity {
  readonly name?: string;
  readonly nickname?: string;
  readonly email: string;
}

export function identityLabel(identity: AccountIdentity): string {
  return [
    ...(identity.name === undefined ? [] : [identity.name]),
    ...(identity.nickname === undefined ? [] : [atNickname(identity.nickname)]),
    identity.email,
  ].join(', ');
}

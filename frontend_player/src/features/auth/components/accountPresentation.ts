/**
 * **What the account panel says** — the way out, and what it says while it is happening.
 *
 * The identity it used to speak — the name, `@nickname` under it, the email under that, as one
 * element — left with the panel's identity block when the You tab was built
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1): the header card and the *Nickname* row say the nickname now, and the email has no row
 * because it has no route (§9).
 */

/** The one way back to the beginning, and what it says while it is happening. */
export const SIGN_OUT = { label: 'Sign out', busyLabel: 'Signing out…' } as const;

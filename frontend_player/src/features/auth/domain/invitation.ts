/**
 * **An invitation, as the invited person meets it** — the code they type, what opens *Set your
 * password*, and what a link says about itself before anything is set
 * ([ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §2–§5, [#518](https://github.com/Raketa02/Raketa/issues/518)).
 *
 * Types and nothing else, for `passwordReset`'s reason — it is the same machinery: whether a code
 * is right, whether a link still works and whether an email already has an account are all the
 * server's answers.
 */

import type { InvitationLinkState } from './vocabulary';

export type { InvitationLinkState };

/** The email the club invited, and the 8-character code its email carries. */
export interface InvitationCodeClaim {
  readonly email: string;
  readonly code: string;
}

/**
 * **What opens *Set your password*** — exactly one of the two, as the server requires: the `token`
 * in the email's link, or the `ticket` a right code was exchanged for.
 */
export type InvitationKey =
  | { readonly via: 'link'; readonly token: string }
  | { readonly via: 'code'; readonly ticket: string };

/** How the person got to *Set your password*. The refusals and the way out are worded by it. */
export type InvitationVia = InvitationKey['via'];

export interface InvitationPassword {
  readonly key: InvitationKey;
  readonly password: string;
}

/** **What a link opens**, read before anything is set: the address *Set your password* locks to. */
export interface InvitationLink {
  readonly email: string;
  readonly state: InvitationLinkState;
}

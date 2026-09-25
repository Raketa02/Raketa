/**
 * **Recovering a forgotten password**, as the app talks about it
 * ([ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §3, §5).
 *
 * Types and nothing else, for `AuthenticatedUser`'s reason: whether a code is right, whether a
 * link has expired, whether a password is strong enough are all the server's answers, and the
 * form's copies of the last one are a courtesy.
 */

/** The email a person asked with, and the 8-character code the server sent to it. */
export interface ResetCodeClaim {
  readonly email: string;
  readonly code: string;
}

/**
 * **What opens the way to a new password** — exactly one of the two, as the server requires:
 * the `token` in the email's link, or the `ticket` a right code was exchanged for. A shape with
 * both, or neither, is a request the server refuses as malformed, so it is not representable.
 */
export type ResetKey =
  | { readonly via: 'link'; readonly token: string }
  | { readonly via: 'code'; readonly ticket: string };

/** How the person got to *Set a new password*. The refusals are worded by it. */
export type ResetVia = ResetKey['via'];

export interface NewPassword {
  readonly key: ResetKey;
  readonly password: string;
}

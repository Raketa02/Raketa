/**
 * **Every sentence a link says when it is opened on a phone somebody is signed in on**
 * ([#520](https://github.com/Raketa02/Raketa/issues/520)) — the two sheets that ask first, because
 * the link may not be the signed-in person's: an invitation for another address, and a password
 * reset for an account nobody can tell from its link.
 *
 * The rest of what a link says is said by the screens it opens, in their own words: Join a group,
 * *Set your password*, *Set a new password*, the invitation sheet — and a spent invitation in the
 * sentence *Set your password* would have said it in (`auth`'s `LINK_STATE_MESSAGE`).
 */

export const LINKS_COPY = {
  /** The second button — nothing changes, and the link is let go. *Sign out* is `auth`'s. */
  stay: 'Stay signed in',
  /** The sheet's close does the same, under its own name: two controls never share one. */
  close: 'Not now',
} as const;

/** **An invitation for another address** — the address it is for is the title (#520). */
export function someoneElsesInvitationTitle(invited: string): string {
  return `This invitation is for ${invited}`;
}

/** Who is signed in, and what signing out leads to: that address's own way in. */
export function someoneElsesInvitationBody(signedInAs: string, invited: string): string {
  return `You’re signed in as ${signedInAs}. Sign out to set a password for ${invited}, or to sign in with it and accept.`;
}

/**
 * **A reset link on a phone that is signed in.** Its link names no account, so the sheet cannot
 * say whose it is — only that it is used signed out.
 */
export const RESET_WHILE_SIGNED_IN = {
  title: 'Set a new password?',
  body: (signedInAs: string) =>
    `You’re signed in as ${signedInAs}. This link sets a new password for the account it was sent to — sign out first to use it.`,
} as const;

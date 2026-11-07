/**
 * **A link into the app** — one of the four the public site serves an in-app twin of
 * ([#520](https://github.com/Raketa02/Raketa/issues/520), PRD #500 stories 46–48, 111–113, 117;
 * [ADR-0187](../../../../../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
 * §4, §7): a **Group link** out of WhatsApp, an **Invitation**'s button, a password reset's link, a
 * **Friend link** ([#756](https://github.com/Raketa02/Raketa/issues/756)) — and the app's own bare
 * address, which the club's email to an existing account opens.
 *
 * What the app does with one depends on who is signed in on the phone when it arrives, and on
 * whether that account is in the app yet — so a link is **held** from the moment it arrives until
 * the place it opens is reached: through sign-in, sign-up, the naming, the questionnaire and the
 * social steps if it has to be. The values were checked when the link was read.
 */

export type IncomingLink =
  | { readonly kind: 'join'; readonly code: string }
  | { readonly kind: 'invite'; readonly token: string }
  | { readonly kind: 'reset'; readonly token: string }
  /**
   * **`f/<code>`** — somebody's friend link (#756). Opened as the account, it puts the owner's
   * request on the opener's Home (the friends mechanics §4.2).
   */
  | { readonly kind: 'friend'; readonly code: string }
  /**
   * **`raketa://` and nothing after it** — the button of the club's email to an account that
   * already exists, which carries no token (ADR-0184 §2): *open Raketa, signed in as you, and
   * accept*. Opened while the app runs, it offers the invitations set aside this launch again.
   */
  | { readonly kind: 'open' };

/** The two links that carry a credential, and open a screen of their own with nobody signed in. */
export type CredentialLink = Extract<IncomingLink, { readonly kind: 'invite' | 'reset' }>;

/** Whether two links are the same link — the same page with the same value. */
export function sameLink(a: IncomingLink, b: IncomingLink): boolean {
  return a.kind === b.kind && valueOf(a) === valueOf(b);
}

function valueOf(link: IncomingLink): string {
  switch (link.kind) {
    case 'join':
    case 'friend':
      return link.code;
    case 'invite':
    case 'reset':
      return link.token;
    case 'open':
      return '';
  }
}

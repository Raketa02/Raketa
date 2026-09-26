/**
 * **The links feature's only public surface** — links into the app: a **Group link**, an
 * **Invitation**'s button — a token's, or the app's bare address for an existing account — and a
 * password reset's link
 * ([#520](https://github.com/Raketa02/Raketa/issues/520), PRD #500 stories 46–48, 111–113, 117;
 * ADR-0187 §4, §7).
 *
 * Three callers, all route files: `+native-intent` hands this feature every address the operating
 * system opens the app with; the player's app and the administrator area mount the place a held
 * link is answered; and the reset link's screen says it has been answered there.
 */

export { redirectSystemPath } from './components/redirectSystemPath';
export { IncomingLinks, type IncomingLinksProps } from './components/IncomingLinks';
export { useResetLinkOpened } from './hooks/heldLink';

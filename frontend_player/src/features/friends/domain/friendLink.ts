/**
 * **Your friend link** ([#756](https://github.com/Rakieta02/Rakieta/issues/756), the friends mechanics
 * §4.1) — the Add friends sheet's *Not on Rakieta yet?* card.
 *
 * Each player has one, `<public site>/f/<code>`: made the first time its owner reads it, the same on
 * every read after, and replaced at once by **New link**, after which the old code is nobody's.
 * **Opening it never makes friends by itself** (§4.2): it puts the owner's request on the opener's
 * Home, answered like any other.
 */

export interface FriendLink {
  /** What follows `/f/`: eight letters and digits. */
  readonly code: string;
  /** The whole address, as the server prints it — what **Copy** puts on the clipboard. */
  readonly link: string;
}

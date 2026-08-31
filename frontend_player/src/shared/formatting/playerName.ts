/**
 * How this platform names a person — **the whole handle, or nobody**.
 *
 * `users` holds an Email and a Nickname and no name at all, and `Nickname` is 2 to 64
 * characters. ADR-0107 is explicit about what follows: *"every sentence naming somebody uses
 * the whole handle or names nobody — the prototype's `split(' ')[0]` has nothing behind it
 * here, and inventing a first name is the product addressing a person by a name they never
 * gave it."*
 *
 * So there is **one** of these, and it is the only thing that turns a player into words:
 * the head-to-head row, the court's side names, the pre-send sheet and all eight of the
 * toasts that name somebody
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §15). It is in
 * `shared/` rather than in Play because the challenge a send opens names the same people on
 * screens Play does not own.
 *
 * **A seat label may truncate visually; a sentence may not, and a spoken name never does.**
 * ADR-0107's rule is against *inventing* a familiar form — a visual truncation invents
 * nothing, and it belongs to the component whose box is doing the truncating rather than
 * here.
 */

/**
 * Somebody a sentence can name: you, another player, or nobody yet.
 *
 * `unknown` is the empty seat. It is a case rather than an `undefined` handle because an
 * empty seat is a **state the court states**, and a formatter that took an optional string
 * would let a missing nickname read as an empty seat.
 */
export type NamedPlayer =
  | { readonly kind: 'you' }
  | { readonly kind: 'player'; readonly nickname: string }
  | { readonly kind: 'unknown' };

/** The unknown player stays a question mark — §15, and it is not a word. */
const UNKNOWN = '?';

/** You, to yourself. Never the handle: a player reading their own name in a row about them. */
const YOURSELF = 'You';

export function playerName(player: NamedPlayer): string {
  switch (player.kind) {
    case 'you':
      return YOURSELF;
    case 'player':
      return player.nickname;
    case 'unknown':
      return UNKNOWN;
  }
}

/**
 * The names on one side of a court — **one entry per seat, never one joined phrase**.
 *
 * This is §B16's side-name formatter *redrawn*. What it used to return was `"You + Marek"`,
 * and that is a layout that assumed short words: at 64 characters the join produces a string
 * no side label can hold, and the 46pt seat is the binding constraint on what a court can
 * print ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §5). A formatter that returns one string has decided the layout, and this one must not.
 *
 * So the caller gets the names and decides how to draw them — one per line, each truncated
 * to its own box, with the whole handle read off the lines the screen already prints in full.
 * A side with one seat is a list of one, which is what makes singles and doubles the same
 * call.
 */
export function sideNames(seats: readonly NamedPlayer[]): readonly string[] {
  return seats.map(playerName);
}

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
 *
 * **`sideNames` is gone, and the rule it carried is not.** §B16's `"You + Marek"` was redrawn
 * as a *list* — *"a formatter that returns one string has decided the layout, and this one
 * must not"*, because at 64 characters a join produces a phrase no side label can hold — and
 * it had one caller, the builder's forecast card. That row is now a list of **controls** and
 * not of names ([#285](https://github.com/Raketa02/Raketa/issues/285)): each seated handle
 * with a breakdown behind it opens `SH.whyfit`, so the entry carries a place and a candidate
 * row beside its word. `handlesOn` composes those entries from this file's one formatter, and
 * a `map` over a shape it does not own could not have been the thing doing it.
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

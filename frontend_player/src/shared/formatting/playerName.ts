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
 * nothing. *Whether* a box truncates is that box's business; **where a handle can be cut** is
 * a property of handles, and that is `handleStem` below.
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

/**
 * The handle **up to its first word break** — `Sergio.Sabater` drawn as `Sergio`.
 *
 * **This is not a first name, and the distinction is the whole of why it is allowed.**
 * ADR-0107 forbids *inventing* a familiar form: the prototype's `split(' ')[0]` over a real
 * name produced a word the person never gave the platform. This produces no word at all — it
 * takes a **prefix of the handle they chose**, cut at a character they typed, and it is used
 * only where a box is drawing rather than where a sentence is naming. Every sentence, every
 * accessible name and every toast still carries all sixty-four characters, and the two rows
 * that draw this stem sit directly under one that speaks the whole thing.
 *
 * **A dot or a space, and deliberately not a dash or an underscore.** Those two are the
 * characters a handle puts *between words* — `Sergio.Sabater`, `Hugo Ferrer` — where `-` and
 * `_` are as often inside one: `bea_k` and `dorota_w` are single words with punctuation in
 * them, and cutting at the underscore would draw `bea` for a handle whose owner wrote four
 * characters. Cutting at a separator rather than at a character count is what keeps the
 * result a word: it is the same rule the seat's three-character caption breaks on purpose,
 * because a 46pt face has no room to respect it.
 *
 * **A handle that opens with a break keeps all of itself.** An empty stem is not a shorter
 * name, it is no name, and there is nothing to draw in its place.
 */
export function handleStem(name: string): string {
  const [stem] = name.split(WORD_BREAK);
  return stem === undefined || stem === '' ? name : stem;
}

/** The two characters a handle separates words with. See `handleStem`. */
const WORD_BREAK = /[.\s]/;

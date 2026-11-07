/**
 * How this platform names a person — **the whole nickname, or nobody**, and never with an @.
 *
 * `users` holds an Email and a **Nickname**
 * ([ADR-0199](../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md)). The nickname is
 * a handle — 2 to 64 characters of letters, digits and `. _ -`, unique across the platform — and
 * **it is what every screen says**: every sentence, row, card, sheet, toast, notice, seat label
 * and spoken name. It is never written with an @ (*ania.k put a score up*): the @ is a chat app's
 * mention mark, and inside a sentence it reads as markup (ADR-0199 §1). The Name is retired.
 *
 * ADR-0107 §4's rule reads on the nickname again, and its argument is untouched: *"every sentence
 * naming somebody uses the whole handle or names nobody — the prototype's `split(' ')[0]` has
 * nothing behind it here, and inventing a first name is the product addressing a person by a
 * name they never gave it."*
 *
 * So there is **one** of these, and it is the only thing that turns a player into words:
 * the head-to-head row, the court's side names, the pre-send sheet and all eight of the
 * toasts that name somebody
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §15). It is in
 * `shared/` because every feature that draws a person names them through it. **The function
 * keeps the word *name***, as ADR-0199's *Neutral* says: *name* there means *what a player is
 * called*, which is the nickname — and so does the `name` a read model carries for a person.
 *
 * **A seat label may truncate visually; a sentence may not, and a spoken name never does.**
 * ADR-0107's rule is against *inventing* a familiar form — a visual truncation invents
 * nothing. *Whether* a box truncates is that box's business; **where a nickname can be cut** is
 * a property of nicknames, and that is `handleStem` below.
 *
 * **`sideNames` is gone, and the rule it carried is not.** §B16's `"You + Marek"` was redrawn
 * as a *list* — *"a formatter that returns one string has decided the layout, and this one
 * must not"*, because at 64 characters a join produces a phrase no side label can hold — and
 * it had one caller, the builder's forecast card. That row is now a list of **controls** and
 * not of names ([#285](https://github.com/Raketa02/Raketa/issues/285)): each seated name
 * with a breakdown behind it opens `SH.whyfit`, so the entry carries a place and a candidate
 * row beside its word. `handlesOn` composes those entries from this file's one formatter, and
 * a `map` over a shape it does not own could not have been the thing doing it.
 */

/**
 * Somebody a sentence can name: you, another player, or nobody this side can name.
 *
 * `unknown` is **two things that draw the same way and are not the same fact**: a seat nobody
 * has landed in yet, and a seat somebody holds whose name the record cannot answer for — a
 * Play row the read-back no longer carries, or a games seat whose account `users` has lost.
 * They share the `?` because there is no word to draw in either, and they stay one case rather
 * than an optional name because the *caller* is what knows which: a formatter taking
 * `string | undefined` would let one read as the other at the call site instead of at the seat.
 * **Never a player with no nickname yet**: the entry gate holds such an account at the naming
 * step, so a read that names somebody has necessarily been handed a nickname (ADR-0199 §3).
 */
export type NamedPlayer =
  | { readonly kind: 'you' }
  | { readonly kind: 'player'; readonly name: string }
  | { readonly kind: 'unknown' };

/** The unknown player stays a question mark — §15, and it is not a word. */
const UNKNOWN = '?';

/** You, to yourself. Never the nickname: a player reading their own handle in a row about them. */
const YOURSELF = 'You';

export function playerName(player: NamedPlayer): string {
  switch (player.kind) {
    case 'you':
      return YOURSELF;
    case 'player':
      return player.name;
    case 'unknown':
      return UNKNOWN;
  }
}

/**
 * The nickname **up to its first dot** — `sergio.sabater` drawn as `sergio`.
 *
 * **This is not an invented name, and the distinction is the whole of why it is allowed.**
 * ADR-0107 forbids *inventing* a familiar form: the prototype's `split(' ')[0]` over a real
 * name produced a word the person never gave the platform. This produces no word at all — it
 * takes a **prefix of the nickname they typed**, cut at a character they typed, and it is used
 * only where a box is drawing rather than where a sentence is naming. Every sentence, every
 * accessible name and every toast still carries all sixty-four characters: the two rows that
 * draw this stem sit directly under one that speaks the whole thing, and the conversation's
 * header, the third drawer, is called by the nicknames whole in its own accessible name
 * ([#401](https://github.com/Raketa02/Raketa/issues/401)).
 *
 * **The first dot, and deliberately not a dash or an underscore** — ADR-0157's cut, as it stood
 * before ADR-0171 (ADR-0199, *Leaves standing*). `-` and `_` are as often inside one word as
 * between two — `anne-marie` and `dorota_w` are what their owners chose — and cutting at a
 * separator rather than at a character count is what keeps the result a word: it is the same
 * rule the seat's three-character caption breaks on purpose, because a 60pt face has no room to
 * respect it. **The poster's initials now break at all three** (`handleInitials`), so
 * `dorota_w` draws `DW` on a poster and `dorota_w` whole in a box; ADR-0199 names the split, and
 * whoever next touches either rule decides whether they meet again.
 *
 * **A nickname that opens with a dot keeps all of itself.** An empty stem is not a shorter
 * nickname, it is none, and there is nothing to draw in its place.
 */
export function handleStem(nickname: string): string {
  const [stem] = nickname.split(STEM_BREAK);
  return stem === undefined || stem === '' ? nickname : stem;
}

/** Where a box may cut a nickname. See `handleStem`. */
const STEM_BREAK = '.';

/**
 * **Two initials, for a poster** — `ania.k` drawn as `AK`, `kuba` as `KU`, `x` as `X`.
 *
 * **This one *is* an exception to ADR-0107 §4, and it is argued as one rather than smuggled
 * under the rule** —
 * [ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §3, cut from the **nickname** since
 * [ADR-0199](../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §2. `handleStem`
 * above is a prefix somebody typed; two initials are a derived form, which is what
 * [#338](https://github.com/Raketa02/Raketa/issues/338) §5 refused on the Chats rows. What §4
 * protects is a **sentence** — *addressing a person by a name they never gave it* — and this
 * is a **drawing**: it goes over the generated poster on the yes screen's tile, where the
 * gradient alone cannot say who at tile size, and over nothing else. **The fence has four
 * sides**: never spoken, never in copy or a toast, never over a photograph, never on any other
 * surface. The tile's spoken name is the whole nickname, and the screen's sentence is built from
 * whole nicknames — so nobody is ever addressed as `AK`.
 *
 * **The cut** (ADR-0199 §2): the nickname's first character, then **the first character after
 * its first `.`, `_` or `-`**, else its second character. With no name, a handle's three
 * separators are the only breaks a player types, and `dorota_w` → `DO` would draw half of what
 * she chose. A separator with nothing after it gives nothing, and the second character stands in.
 * Upper-cased **here**, for the drawing, and the nickname itself is never touched.
 */
export function handleInitials(nickname: string): string {
  const first = nickname.slice(0, 1);
  const separator = nickname.search(INITIAL_BREAK);
  const afterSeparator = separator === -1 ? '' : nickname.slice(separator + 1, separator + 2);
  const second = afterSeparator === '' ? nickname.slice(1, 2) : afterSeparator;
  return `${first}${second}`.toUpperCase();
}

/** The three characters a nickname may separate its parts with — `[A-Za-z0-9_.-]` has no other. */
const INITIAL_BREAK = /[._-]/;

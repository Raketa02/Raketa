# ADR-0149 — A game is composed at the surface, and the chat door is a join

- **Status:** Accepted
- **Date:** 2026-09-07

Decided on [Now, and the one state-detail surface both tabs open](https://github.com/Raketa02/Raketa/issues/336),
on the map [Closing the core loop](https://github.com/Raketa02/Raketa/issues/321), against the
prototype `prototype/now-and-game-screen`.

Extends [ADR-0148](0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md) §8,
which put the plan on its own list *"beside `GET /games`, joined by game id"* and handed **where
that join lives** to this ticket. Upholds
[ADR-0143](0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md) §8 and
[ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) rather than narrowing
either.

## Context

Now draws **fourteen cards** ([#324](https://github.com/Raketa02/Raketa/issues/324)), and four
of them are keyed on how many of the plan's three slots are filled. The plan is not on
`GameSchema` and never will be: ADR-0145 §4 made *"`games` importing the Plan"* the **checkable**
statement of ADR-0137's scoping, and ADR-0148 §8 answered the resulting N+1 with a second list —
`GET /plans` — rather than by breaking it. So every card on Now is a **join of two lists**, and
nothing had said where a feature-first client performs it.

Three constraints met on that question at once, and they point in different directions.

**The dependency direction is already fixed on the server and unstated on the client.** ADR-0148
names *"`plans` imports `games`"* among its costs. The mirror — `games` importing `plans` — is
the exact inversion of the clause ADR-0145 §4 made checkable, and a client written that way
would read as permission to write the server that way.

**The card needs both halves to decide anything.** #324's ladder as amended by ADR-0145 §3 is a
pure function of `(standing, plan, now)`: *the agreed point has passed* → **Needs result**, *the
agreed day is today* → **Today**, *all three slots* → **Game on**, otherwise **Planning**. A
component holding only a `Game` cannot draw a card, and a component holding only a `Plan` cannot
either.

**And the chat door has no id anywhere on the wire.** ADR-0146 forbids `games` knowing a
conversation exists, and ADR-0148 §2 gave the conversation **its own** `conversation_id` with
`game_id` as a nullable field on *it* — *"a UUID costs one column and keeps the door open"* for
Around's plan chats. The arrow therefore points conversation → game and never back. But #324
requires **Open the chat** on the game surface, drawn *"always … whichever door you came in by"*,
and a card in Now has a game id and nothing else. Arriving from Chats the id is in hand;
arriving from Now it is not.

Three ways out were considered for the door and two are worse than the cost they avoid. A
`GET /conversations?game_id=` is a second read shape ADR-0148 §3 did not write, for a list the
Chats tab already fetches whole. Putting `conversation_id` on the plan moves ADR-0146's
coupling one context along rather than removing it. Putting it on `GameSchema` is the thing
ADR-0146 exists to refuse.

[#335](https://github.com/Raketa02/Raketa/issues/335) looks like a precedent against a client
join and is not. It refused a conversation row's state pill because that pill would have been
**a second spelling of a fact the row already had** — ADR-0148 §6's *the last line is what a
pill would have said*. A chat door is a fact **no route provides** and the surface genuinely
needs.

## Decision

**We will compose a game and its plan at the surface, and neither feature will import the
other.**

1. **The ladder and the Now card belong to `features/plans`, which may import
   `features/games`.** That is the direction ADR-0148 already pays for on the server, and it
   keeps the client half of ADR-0145 §4's clause true for free: **`features/games` never learns
   a plan exists.** The rule is one-way and stated as such, so a future reader cannot read the
   existing edge as symmetry.

2. **The game screen stays `features/games`' and receives the plan as a child.** It is
   `ResultScreen` grown its plan arms and renamed **`GameScreen`** (#324 §2): `games` owns the
   frame, the court and the result arms, and `plans` renders the three slots into it. Neither
   type crosses. This is `Court`'s own shape, one folder over — *"read-only faces and pressable
   seats are different children"* — applied to two features instead of two variants.

3. **The chat door is a client join over `GET /conversations`, and it fails soft.** The surface
   finds the row whose `game_id` matches and draws a door to it; finding none draws **no door**,
   which is not an error state but the ordinary one — a conversation is **destroyed 24 h after
   the moment it was arranging** ([#325](https://github.com/Raketa02/Raketa/issues/325)) while
   the entry window runs **eight days**. No route is added and no context learns about another.

4. **The plan is read-only wherever it is drawn outside the chat**, so the slots are `Tag`s and
   never `Chip`s — *"a control that cannot be operated must not offer the affordance of one"* —
   and the way to change one is the chat door above.

5. **The same screen is reachable from two tabs as two routes**: `/games/[gameId]` under Now and
   `/chats/[conversationId]/details` under Chats, over one screen component both import.
   `tabForPathname` is pure on the **first path segment**, so each route lights its own column
   and *back* is correct in both directions by construction; `INSIDE_A_TAB` is untouched. Two
   addresses for one screen is not two spellings of a fact — it is two places you can be.

6. **ADR-0143 §8 is upheld on the game screen and not extended to it.** *"`ON` draws neither.
   … a card here would be a second, worse copy of the game screen."* A game exists only after
   `ON`, so no pairing, Fit, level, band, confidence or `at_stake` is drawn on `GameScreen` or
   on a Now card. What survives of the design's forecast block is the one sentence this build
   already owns: `worthLine`'s *"This one counts, so an agreed score becomes part of your
   record."*

## Consequences

**A card is one component with one anatomy, and the ladder is derived rather than stored.** Four
of the fourteen cards read the plan and the other ten ignore it, through one function over one
pair of values. Nothing keys a card on a field somebody has to remember to write.

**The client half of ADR-0145 §4 becomes checkable the same way the server half is.** *If
`features/games` ever imports `features/plans`, the clause is broken* — a grep, not a judgement,
and the existing import-boundary ESLint rules are where it would be enforced if it is worth
enforcing.

**Now pays two reads and a join, and the game screen pays three.** ADR-0148 named the first two;
the third is `GET /conversations`, which the Chats tab fetches anyway, so on a warm cache the
door costs nothing and on a cold one it costs one list the player was about to need. Stated
plainly: **the game screen reads a list belonging to a context it is forbidden to know about,
and gets away with it because it reads that list as *the player's rooms* rather than as *this
game's conversation*.** That is a real seam and the next person to widen it should say so.

**The chat door disappears before the loop closes, and this record does not fix it.** A game
sits at *Needs result* for up to eight days with **no conversation at all** — the door is gone
at exactly the moment two people most want to ask *did we play?*. That does not contradict #324,
whose *always drawn* is scoped to the two planning states, which are always before the agreed
point. It is a hole in the product, it is filed as its own question, and the card and the screen
both fail soft into it rather than drawing a door to a room that is gone.

**A screen renamed is a rename with a blast radius.** `ResultScreen` becomes `GameScreen`, and
`GAME_ROUTE`'s docblock stops calling it *"the result conversation for one game"*. Everything
`features/games` already owns — `resultConversation`, the eight arms, the pad and the grid —
keeps its name, because the result argument is still what most of that screen is.

**Two route files over one component is a shape this repo has not used.** The cost is that a
screen now has two addresses and a reader has to notice that both point at one component; the
benefit is that the shell keeps knowing nothing, and neither the router nor `shellTabs` grows a
`from` parameter that would make a pure function impure.

**Refusing the forecast costs the game screen its most visual block**, and the design drew it.
What is bought is that no port from `games` into `matchmaking` has to exist, ADR-0143's
recompute-rather-than-replay apparatus is not built a second time, and the screen makes no
as-of-now claim about a person on a record that will be read for as long as the game exists. If
that refusal is ever reversed it is a fresh decision extending ADR-0143 a second time, with its
own argument — not a detail of a screen spec.

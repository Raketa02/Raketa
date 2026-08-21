# ADR-0085 — *Recently viewed* ships dark, and the wire keeps its code

- **Status:** Accepted
- **Date:** 2026-08-22

## Context

[ADR-0050](0050-now-below-the-strip-is-shelves.md) gave Now five shelves, and defined the third as
*matches **tapped** in the last 48 h, still joinable*. [ADR-0051](0051-now-is-ordered-not-drawn.md)
gave it the only shelf on the screen with **no floor at all**, on the argument that it makes no
claim: *"it says you looked at this, and a 41 with its badge printed is exactly what reminds the
player why they backed out."*

[Fifty cards where six were budgeted](https://github.com/Raketa02/Raketa/issues/40) went looking
for what that shelf costs and found that **nothing in `backend/` records a card tap** — no table,
no event, no field — and filed the storage question as its own ticket: what counts as a view,
where the log lives, whether the write is fire-and-forget on *"a write on every tap on the busiest
screen in the app."*

**That framing was overtaken.** [ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md)
closed the act enumeration at six and killed the `Open match` fallback:

> There is no fallback. `Open match` dies with its destination. A card with no act has **no primary
> button**, and its body is **not a tap target** either — ADR-0060 fixed that the card and its
> button resolve to the same place, and that survives here as *both resolve to nothing*.

So **v1 has no gesture that opens a match to look at it.** Of the six surviving acts, only
`takeSeat` points at a match this shelf could ever hold — one that is `NotAlreadyMine` and still
joinable — and tapping it does not open the match. It starts a five-minute **seat claim**
([ADR-0081](0081-a-seat-is-never-taken-until-it-is-paid.md)), which is a purchase, not a look.

Three things follow before any storage question is reached:

- **The hot-path write does not exist.** Twenty-seven of thirty-three situations have no tap at
  all, and the taps that remain already write a record. The cost that motivated the ticket is not
  there to be paid.
- **This was never a cache tier.** [ADR-0068](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md)
  fixed that *"a tier must be justified by a **shared** key, not merely by a different clock"* — a
  view log is per viewer and would hold the only copy of what it stores, so the Redis-with-a-48h-TTL
  recommendation carried in from #40 was answering a question this screen does not ask.
- **The title is not protected.** Neither UI authority names *Recently viewed*; it is ADR-0050's,
  so a rename was available.

The alternatives considered:

- **Redefine a view as an abandoned seat claim** — *matches you started to take and didn't finish*.
  Internally consistent, and it is precisely ADR-0051's *"why they backed out"*. It needs no new
  store, because the claim record already exists.
- **Reintroduce a tap target**, honouring ADR-0050 as written and reopening ADR-0083.
- **Ship the shelf dark.**

## Decision

**We will compose four shelves on Now, and leave *Recently viewed* dark until the surface that
gives it a gesture exists.**

### The shelf is dark because its gesture is, not because it was dropped

ADR-0083's rule is *a card names an act when the viewer can take it now and a v1 surface can
receive it*. **"Look at this match" fails both halves**, and this shelf is the only thing on Now
that reads it. Nothing about the shelf's definition is wrong; the screen it was defined against is
out of scope, and ADR-0083 already killed the tap on that ground. This ADR follows the same fact to
the same conclusion one shelf further down.

**Refused: redefining a view as an abandoned seat claim.** It is the tempting option and it is
nearly right, which is why it is refused explicitly rather than passed over. Three things sink it.
It **renames the shelf to describe a promise nobody made** — *you nearly bought this* is an
accusation where *you looked at this* is a courtesy. It would be **empty for almost every player**:
ADR-0081 allows **one live claim at a time** at five minutes each, so a 48-hour window holds two or
three abandonments for a very indecisive player and zero for everybody else — and ADR-0050's
absence rule would then hide the shelf for nearly everyone anyway, which is the dark shelf with
extra machinery in front of it. And it **spends the good idea on a thin imitation**: the shelf that
returns with the match-detail screen would have to argue with this one.

**Refused: reintroducing a tap target.** ADR-0083 is nine days old and closed its enumeration
deliberately, fixing that *a seventh act arrives with the surface that receives it, never ahead of
it*. Building a browsing gesture so that a shelf can observe it inverts that rule for the one case
that would most reward inverting it.

### The wire keeps the code

`recentlyViewed` **stays in ADR-0070's shelf enum** — `bestFit | sameLevel | recentlyViewed |
newPlayers | newClubs` — and is simply never composed.

[ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md) put shelf **presence** and shelf
**order** on the server for exactly this reason: *"the words were never the part that needed to move
without a client release; shelf presence and shelf order were, and both stay server-owned."* Keeping
the code means the shelf's return is a **server** change. Removing it would make presence a
client-release concern, which is the one thing that rule exists to prevent.

**The client is not asked to build its render path in v1**, and that is stated rather than left to
inference. A shelf code the phone never receives needs no branch, and a branch nobody can exercise
is a branch that has rotted by the time it is wanted. What the contract guarantees is that the
**value is reserved** — not that anything draws it.

### The budgets restate their condition, and hold their numbers

[ADR-0069](0069-the-budget-is-two-budgets-and-both-fail-the-build.md) is measured against
**29 cards across five retrieval lanes**. The caps become **6 · 3 · — · 8 · 6**, so the screen is
**23 cards across four lanes**.

- **The latency gate is unchanged: p99 ≤ 150 ms, cold ceiling 250 ms** — now *"measured at 500 live
  city matches on a **23-card** screen with a warm context cache"*. The table's retrieval row drops
  a lane. The gates were never tight against a modelled ~92 ms cold, and a gate that loosens every
  time the screen shrinks is a gate that never fails.
- **The payload ceiling is unchanged: 150 KB uncompressed, and it fails the build** — now measured
  on a 23-card screen. This is the number that could have moved, since 150 KB was *derived* as
  29 × ~5 KB, and holding it at 23 cards allows ~6.5 KB a card.

  It holds anyway, because **the per-card figure was a derivation and never the rule**. ADR-0069
  puts the gate on the total *"because that is what a player feels"* and keeps the per-stage rows as
  *"diagnosis, not as gates"*; the same reasoning applies one level up. The discipline the ~5 KB
  bought has already been spent — [What a card carries](https://github.com/Raketa02/Raketa/issues/42)
  is closed and the card's contents are fixed — so re-deriving the ceiling downward now would fail
  builds for a screen that is about to grow back by six cards.
- **The degrade table loses its *Recently viewed* row.** Degrade narrows to the shelves that have a
  scorer and can appear; two of three match shelves remain.

**Restating the condition is the load-bearing half**, on ADR-0069's own terms: *"a p99 measured
against a cold cache is measuring the cache, not the funnel."* A 150 KB ceiling measured on a
23-card screen and a 150 KB ceiling measured on a 29-card screen are different gates wearing one
number, and only the stated condition tells them apart.

### What is deliberately not decided

**No store is built and none is specified.** No view log, no Redis key, no Alembic migration, no
retention sweep, no write on any path. Every question #53 was opened to answer —
what counts as a view, whether a scroll-past counts, one row or two for a repeat visit, Redis
against Postgres, fire-and-forget against awaited, whether erasure deletes or expires, and shelf 3's
own eligibility predicates, which no ADR ever wrote — **goes with the shelf** to the effort that
builds the surface it reads. Deciding them now would be authoring a store for a gesture, in advance
of the gesture, which is what ADR-0083 refused for acts.

## Consequences

**Easier**

- **Now ships with nothing unbuilt behind it.** The one retrieval path that needed infrastructure
  rather than a query is gone, and with it the last reason for `backend/` to acquire a Redis client
  before the caches ADR-0068 actually specified.
- **A hot-path write leaves the budget.** ADR-0069's numbers were modelled, not measured, and the
  first implementation is also the first measurement; it now takes that measurement without a write
  of unknown cost on the most-used interaction in the product.
- **The shelf returns as a server change.** Presence stays server-owned, the enum value is reserved,
  and the effort that builds the match-detail screen inherits the shelf's definition — 48 hours,
  still joinable, no floor, cap 6, scored — intact and unargued-with.
- **[Seeding the demo week](https://github.com/Raketa02/Raketa/issues/52) loses its last blocker.**
  There is nothing to seed a view into, because there is nothing that records one.

**Harder**

- **Now is four shelves, and one of its five questions goes unasked.** A player who scrolled past
  something on Saturday has no way back to it on Sunday but to find it again. That is a real loss
  and it is not mitigated; it is deferred.
- **A reserved enum value with no producer and no consumer is a thing that can be forgotten.** The
  next session to read ADR-0070's enum will find five codes and a server that emits four, and the
  only thing pointing at why is this ADR.
- **The payload ceiling is looser per card than the number that justified it.** At 23 cards, 150 KB
  is ~30 % more room a card than #42 was held to. If the shelf's return is delayed indefinitely, the
  slack is permanent and the next card-contents question inherits a budget nobody sized for it.
- **This is the third thing this map has bounded without owning**, after the club console's
  counter-mark surface and account deletion. The view log now sits with the match-detail screen in
  the map's out-of-scope section, and neither has an owner.

**Neutral**

- **No glossary change.** `CONTEXT.md` holds no shelf vocabulary; shelves are ranking policy, which
  [ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md) placed outside the engines
  and ADR-0051 confirmed. Nothing in the domain language moves.
- **ADR-0050's five-shelf ceiling stands.** It bounds the number of *questions* Now may ask, not the
  number it does ask, and its own rule — *a shelf that has nothing to show is absent* — already
  describes what a player sees. What is new here is that shelf 3 has nothing to show **by
  construction** rather than by a thin week.
- **ADR-0051's no-floor rule for the shelf is untouched** and unexercised. When the shelf returns, a
  41 still prints with its badge.

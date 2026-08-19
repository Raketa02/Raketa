# ADR-0034 — The Matches context is a record and keeps no history

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

[ADR-0002](0002-event-sourced-user-aggregate.md) made event sourcing a **per-context
choice rather than a house style**, and named the four contexts that would each have to
make it deliberately: *"Clubs, Courts, Bookings and Matches."* Every racket-sport context
built since has gone the same way — [ADR-0017](0017-rating-context-event-sourced.md) for
`Assessment` and `SkillRating` — so the pattern in the tree points one direction and the
rule in [`CONTEXT.md`](../../CONTEXT.md) insists the direction be argued rather than
inherited. [ADR-0018](0018-aggregate-repositories-over-the-event-store.md) then refused a
generic `EventSourcedRepository[A]` for exactly this reason: shipping one *"would quietly
answer that question for four contexts nobody has asked it of."* This record is the asking.

Matches is also the context [ADR-0026](0026-matchmaking-engines-snapshot-input-contract.md)
was written to feed — *"the snapshot becomes the specification for the Matches aggregate"* —
and `backend/app/engines/matchmaking.py` says so in the docstring above `SeatState`: *"This
engine reads them; Matches will define them."*

**Almost nothing about a match is stored.** `3.1-enrolled_match_states_and_transitions.md`
§1.1 is blunt about it: *"There is no `status` column. Nothing writes `state = 'CONFIRMED'`.
The state is recomputed from scratch every time anybody looks at the match, from the record
plus the current instant."* The stored facts are roughly two dozen scalars, and the whole
33-context state model is a pure function of them and the clock. There is little history to
source, because there is little state to have a history of.

**The argument on the other side was that the match is the aggregate whose past a player
will dispute** — most concurrent writers, most money attached. That argument does not
survive contact with the product. Nothing about a match is genuinely disputable except the
score, and the score is entered on court while both sides are still standing there, inside a
thirty-minute window, with a two-party confirmation flow. Everything else a player might
argue about is answered somewhere that is not the match:

| What is argued about | Where the answer already lives |
| --- | --- |
| What was I charged, what came back | the money ledger — event-sourced, every movement referenced `PAY-…` / `REF-…` / `REV-…` |
| I left in time, why only half | the **departure** record and its settlement ([ADR-0033](0033-settlement-and-occupancy-are-independent.md)) |
| That is not the score we played | the on-court confirmation flow, settled in thirty minutes |
| Why did this match cancel | **the record itself** |

That last row is quietly decisive. The model does not carry one cancelled flag — it carries
**four**, because *"they are four different stories and the player deserves to know which one
happened."* The reason a player is owed the distinction is the same reason no history is
needed to reconstruct it: the record *is* the explanation.

`now-section-domain-spec.md` — the document `§A.0` makes the tie-breaker — had already
reached the same split from the money side: *"the ledger is **event-sourced** even though the
match is 'a record with an outbox'."*

**Doc 5's finding C3 is the second half of this decision, and it does not reach.** It names
three kinds of stored fact — allocations, irreversible crossings, side-effect receipts — over
`FactDelta`'s **seven write verbs**. §1.2's table lists **twenty** facts, and
[ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md) and
[ADR-0033](0033-settlement-and-occupancy-are-independent.md) have since added `heldSince`,
`created` and `vacancies[]`. Three kinds over seven verbs cannot classify twenty-three nouns,
and the classification is load-bearing: C2's defect is that a downed timekeeper makes four
transitions read *wrong in the reassuring direction*, and the fix depends on knowing which
facts a reader may derive and which only a writer can produce.

C3 also mis-files one. It groups `clubCancelled` with `formCancelled` and
`checkpointCancelled` as receipts. The latter two genuinely are — the clock plus the record
derives them, and the flag exists only so the refund runs once. `clubCancelled` is nothing of
the kind: **no reader can derive that a manager cancelled.**

The alternatives considered:

- **Event-source the match, like every other aggregate here.** Consistent with the tree, and
  it is the pattern [ADR-0017](0017-rating-context-event-sourced.md) set. But that record
  warned in its own Consequences that *"the pattern is being set for contexts where [volumes]
  will not be [trivial]"* — and this is that context. The home screen reads several matches on
  every open; rebuilding each from its stream is the cost that warning was about. Critically,
  **it buys nothing for concurrency**: optimistic concurrency comes from a version, and a
  version on a row gives the identical guarantee.
- **A row plus a separate audit log.** The dual write [ADR-0017](0017-rating-context-event-sourced.md)
  refused in its Context — *"the day the rating row and the replayed log disagree there is
  nothing to say which one lied."*
- **A row with a version and a transactional outbox.**

## Decision

We will model **Matches as records with a version and an outbox**, and **no aggregate in the
Matches context will keep event history.**

### One aggregate

There is **one `Match`**. "Enrolled" is a *relationship*, not an object: `3.1` §0.1 says the
state is a property of the match and *"the wording is a property of your relationship to
it."* A second aggregate for the enrolled view would be a third instance of the mistake
[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) named — encoding a fact about a
player's relationship as a fact about the match.

### Five kinds of stored fact

§1.2's table is classified by the question C2 actually asks — **may a reader derive this, or
may only a writer produce it?**

| Kind | Facts | May a reader derive it? |
| --- | --- | --- |
| **Constitutive** — chosen at creation, never recomputed | `share`, `sport`, `counted`, `created`, the court category | no — chosen, not computed |
| **Occupancy** — current state, freely reversible | `seats[].p`, `.paid`, `.at`, `transferring` | no — but nothing derives *from* absence |
| **Allocation** — a claim on contended inventory, and its failure | `courtId`, `heldSince`, `holdKind`, `protectedAt`, `releasedAt`, `inventoryLost` | no — a court is a scarce resource, not a computation |
| **Crossing** — a threshold irreversibly passed | `committedAt`, `rescueTaken`, a departure's settlement | derivable **once**, then frozen, because the inputs stop supporting it |
| **Declaration** — an outside actor's decision | `clubCancelled`, `courtLocked`, `score`, `confirmed`, `noShow` | **no, by construction** |

`start` is deliberately **not** constitutive:
[ADR-0032](0032-order-is-a-property-of-the-composed-screen.md) keeps it mutable, and *"a
moved match is the same match."*

**Receipts are an annotation, not a sixth kind.** `formCancelled` and `checkpointCancelled`
are receipts on *derivable* conclusions: the state derives without them
(`cancelledIncomplete` is `now ≥ check ∧ committedAt = null ∧ ¬isFull`), and the flag records
only that the refund, the court release and the notification completed. That is C2's fix
stated as a rule rather than a patch — **a downed timekeeper delays the money and never the
truth.** `clubCancelled` is a Declaration and carries no such property, which is precisely why
grouping the three together would have made the fix look like it covered a case it does not.

### The shape

- **One row per match, one row per seat, updated in place**, carrying a **version**. Two
  concurrent writers cannot interleave: one wins, one retries. This is the guarantee
  [ADR-0002](0002-event-sourced-user-aggregate.md) got from `expected_version` on the stream,
  and it does not require the stream. `RefreshToken` is the precedent — the one thing in the
  tree already built this way, and named by ADR-0002 as the deliberate counter-example.
- **The money ledger is the only event-sourced thing in this picture, and it is not part of
  Matches.** Its shape is a separate decision and is not settled here.
- **A departure is a row too.** Its outcome is monotonic upward and may improve after
  settling ([ADR-0033](0033-settlement-and-occupancy-are-independent.md)), but that trail
  already exists where a player would look for it: the ledger writes a referenced line for the
  original refund and another for the top-up. A second copy inside the departure is the dual
  write again.
- **The score is four facts, never a list**: the score currently on the table, who put it
  there, whether it has been agreed, and **how many times it has been proposed**. A count, not
  a sequence — see [Consequences](#consequences) and the ticket it hands off to.

### Every change announces itself, specifically

Each change to a match publishes a **named** domain event through the transactional outbox
([ADR-0003](0003-transactional-outbox-for-event-delivery.md)). This is the ordinary pattern,
with one obligation added that is not ordinary and that has to be honoured from the first
commit:

> **Every change a support agent would one day need to explain to a player is announced as
> its own named event — never as a generic "match updated".**

The planned **playerEventsTracker** — a player's timeline across every match, read by the club
console for player support — is to be **built from these announcements and never written
alongside them.** Two writes recording one event is the failure
[ADR-0017](0017-rating-context-event-sourced.md) refused; put it under player support and the
record a support agent reads while a player is on the phone is the one that lied.

**A player's timeline belongs to the tracker, not to the match.** The support question is
*what happened to this player*, spanning every match they hold — the tracker's natural shape
and the match's worst one.

## Consequences

**Easier**

- The state model is what the documents say it is. `3.1` §1.1's list — no stale state, no
  scheduled job to fail, correct offline, scrubbable backwards, no two clients can disagree —
  falls out of *"a handful of integer comparisons"* over a row, with no rehydration between a
  read and an answer.
- **The busiest object in the product is the cheapest to read.** The home screen reads several
  matches per open; each is one row-set, not a replay.
- The five kinds make C2's fix mechanical rather than clever. A reviewer asking *"can a reader
  derive this?"* has a table to answer from, and a new fact has to declare its kind before it
  can be added.
- The concurrency guard is unchanged. `EvaluateAt`'s deterministic idempotency key and the
  version together make at-least-once scheduling safe, exactly as `3-enrolled_match_engine_architecture.md`
  §2.2 designs it.
- The Matches context needs no aggregate repository over the event store, so
  [ADR-0018](0018-aggregate-repositories-over-the-event-store.md)'s deferred question — whether
  a generic `EventSourcedRepository[A]` is owed — stays deferred on the evidence rather than
  being forced by a fourth event-sourced aggregate.

**Harder**

- **"Who changed this, and when" is only as good as the announcements.** For anything the
  ledger does not touch — a manager locking a court by hand, a court released and reacquired —
  the answer exists only in the outbox trail and whatever consumes it. Until
  playerEventsTracker exists, that trail is transient. **This is the real cost of the decision
  and it should not be discovered later**; if club-side accountability needs it sooner, the fix
  is a small audit trail on club actions, not history on the match.
- **The announcement obligation costs event types now to buy a feature later.** A longer,
  more specific event list is more to name, more to version, and more to keep faithful — and
  nothing mechanical catches an event that is published too coarsely. The first flow to prove
  it earns its keep is the score's propose-and-agree round trip, where the match keeps a count
  and the tracker keeps the conversation.
- **The tree is no longer uniform.** Three aggregates are event-sourced and the fourth
  context is not, so an agent pattern-matching on `backend/app/modules/` will find the wrong
  template first. The same hazard [ADR-0018](0018-aggregate-repositories-over-the-event-store.md)
  flagged for two things called "repository".
- **Events are still a published contract.** Not sourcing state from them does not make them
  private; the event catalog rules apply unchanged.
- If the score flow ever grows a genuine negotiation that must be reconstructable, the count
  will not be enough and the tracker will have to be load-bearing rather than convenient.
  That is a real dependency of a product rule on a feature that does not exist yet.

**Neutral**

- `SeatState`'s three words — **paid**, **held**, **empty** — are adopted verbatim, as
  [ADR-0026](0026-matchmaking-engines-snapshot-input-contract.md) requires. **Held** means a
  name and no money, and *"holding a seat never holds a court."* A short post-join grace period
  in which money is not taken was considered and **rejected**: joining means paying, and the
  existing pre-commitment reversal already returns everything.
- Nothing changes for `User`, `Assessment` or `SkillRating`.
  [ADR-0002](0002-event-sourced-user-aggregate.md)'s per-context rule is being followed, not
  overturned — this is the first time it has come out the other way for a racket-sport context,
  which is what a genuinely per-context rule looks like when it is real.

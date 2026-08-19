# ADR-0035 — A reservation is the only claim on a court, and it claims an interval

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

Doc 5's finding **C1** is blocking, and it is the reason its build order puts Courts *before*
the match lifecycle: *"the reservation has to exist before the ladder can assign anything."*

> Optimistic concurrency on match `m1` says nothing about match `m2`. Two matches at the same
> club, same category and same hour, both crossing their ladder threshold in the same second,
> both load the free-court list and both take the same court.

`3.1-enrolled_match_states_and_transitions.md` §9.2 lists precisely this case as handled —
*"Two open matches, same club, category and hour: each gets a genuinely different court.
`pickCourt` returns the first available one"* — with no mechanism behind it. And
`inventoryLost` is **terminal**: it cancels the match and refunds everybody, including anybody
who had already left. Getting it wrong is not a display bug.

**C1's proposed fix names the wrong scarce thing.** It asks for *"a uniqueness constraint on
`(court, slot)`."* Two problems.

First, `3.1` is emphatic that the court is not what was bought:

> **The exact court is assigned, never chosen — and the price cannot change.** The category
> was bought, not the court, which is what lets a seat price be quoted before a court exists
> and stay fixed when one is assigned.

`courtAssigned`, fifteen minutes before play, is *"the only state that names a specific
court"* — everywhere else the card says the category, *"because the court is assigned and may
be reassigned."* `inventoryLost` fires when *"the category sells out"*, not when one court is
taken.

Second, a constraint on a **slot** is the dead repo's issue `#127` restated: reservations
unique on the slot's *start* let 14:00–15:30 and 14:30–16:00 both land on one court. The same
defect seen from the schema side — see the triage on
[#4](https://github.com/Raketa02/Raketa/issues/4).

Root [`CONTEXT.md`](../../CONTEXT.md) flags four questions that *"must be answered before
Bookings exists"*: whether a Booking is owned by the Court, the Club, or stands alone; whether
availability is a projection or a stored concept; what the tenancy spine is; and which side
owns cancellation windows and pricing. The first three are this decision's.

The alternatives considered:

- **A category allotment counter** — a count against `(club, category, interval)`, no court
  named until T−15min. The most literal reading of *"the category was bought"*. Rejected:
  counters over **overlapping** intervals are `#127` wearing a different hat, the club's own
  private bookings have to decrement it too, and a counter kept beside the reservations it
  summarises is a second thing to keep true.
- **The Court aggregate owns its reservations**, so exclusion is an aggregate invariant.
  Correct-by-construction and unbounded: court 3 accumulates every booking it will ever have,
  and every availability check loads all of it.
- **Reservations belong to a Booking**, and matches go through bookings. Rejected because a
  match's speculative hold is not a booking — nobody bought anything, and the ladder grants and
  withdraws it as seats fill and empty.
- **A reservation standing alone, excluding by interval.**

## Decision

We will make a **reservation the only thing that can claim a court**, and it will claim a
**time range**, not a slot.

### The primitive

A **reservation** is one court, one time range, claimed. It is its own record — not part of the
Court, which stays a catalogue entry (surface, indoor/outdoor, sport, category), and not part
of a Booking.

**Exclusion is by overlapping interval on one court,** enforced by the database, never by read
ordering. Two matches crossing their ladder threshold in the same second cannot both take
court 3, because the second write is refused. This also fixes `#127`: overlap, not equality of
start.

### A booking holds a reservation; it is not one

Two different things can hold a reservation, and conflating them is the naming trap under
`CONTEXT.md`'s open question:

- A **Booking** — a player buying a court outright. Deliberate, paid, and on the private
  split-share path it exists *before any share is paid*.
- A **Court hold** — a match's speculative reservation, granted by the hold ladder and
  withdrawn when the ladder is no longer satisfied ([ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)).

So `CONTEXT.md`'s question — *is a Booking owned by the Court, the Club, or standing alone* —
is answered with **none of the three**: a Booking *holds* a reservation. The tenancy spine is
`Club → Court`, and a reservation references a court and is held by exactly one holder.

**This is also the crispest statement of the two match kinds:** the **private path starts with
a reservation and looks for players; the open path starts with players and looks for a
reservation.** That single sentence is why the private path has no commitment deadline —
[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) reached the same conclusion from the
money side, because *"the court is bought at booking, so the moment has passed before the first
share is paid."*

### The court is named internally and published late

A reservation names a real court from the moment it is granted, because that is what makes the
exclusion real. **That name is not published.** The card shows the *category* until
`courtAssigned`, and reassignment — swapping which court a live reservation names — is an
ordinary operation, legal wherever exclusion still holds. Every property `3.1` needs survives:
the seat price is quotable before a court exists, it does not change when one is assigned, and
the court may move until shortly before play.

### Availability is a query, and so is losing it

**Availability is a projection over reservations, never a stored number.** *"Is a court of this
category free for this window"* is a question asked of reservations, which is what stops it
drifting from the thing it summarises.

That settles the sub-question C1 leaves open — whether `inventoryLost` is a *query result*
(nothing was free) or a *race outcome* (something was free and somebody else took it). **It is
a query result, always.** The constraint makes the race impossible rather than detectable, so
there is exactly one story to tell the player.

### The match asks; the claim commits with the payment

The match does **not** reach into court inventory. It asks for *a court of this category, for
this window*, and is given a reservation or refused. It never learns how courts are organised.

**The claim commits in the same transaction as the payment that earned it.** The alternative
leaves a hole with no owner: the payment has landed, the ladder says a court is owed, and
nothing holds one — a state the model has no card for, and one a crashed process would make
permanent. So a seat payment that satisfies the ladder writes, in one transaction, the seat, the
reservation **or** `inventoryLost`, and the outbox rows for both.

This is not a new pattern here. [ADR-0018](0018-aggregate-repositories-over-the-event-store.md)
already chose it, for the same reason and in the same words: *"`save` appends and publishes. It
never commits. The transaction boundary stays with the use case, because completing an
assessment spans two aggregates in one transaction and ADR-0017 states that as a domain rule,
not a persistence detail."* Here the domain rule is: **a seat payment that earns a court, and
the court it earns, are one event or they are a bug.**

Whether the reservation record itself is event-sourced is answered by
[ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)'s rule applied one context over:
it is a row with a version and an outbox. A court's booking history is a query over
reservations.

## Consequences

**Easier**

- **The double-booking defect becomes structurally impossible**, not merely unlikely. C1's
  failure mode — expensive, silent, terminal — is removed by a constraint rather than by
  ordering discipline nobody can review.
- `inventoryLost` has one meaning and one story. The player is told *"the last court of this
  category was sold"* and that is what happened.
- **`#127` is fixed by construction**, in a context that did not exist when it was filed.
- Availability cannot drift, because there is nothing beside the reservations to drift from.
- The match layer shrinks. It asks a question and records an answer; it holds no opinion about
  surfaces, categories or club layout.
- The private and open paths get one sentence that explains their entire divergence, which is
  worth more than either path's rules listed separately.

**Harder**

- **Interval exclusion is a real database feature, not a unique index.** PostgreSQL has it
  (`EXCLUDE USING gist` over a range), SQLite does not — and the test suite runs on SQLite
  (`tests/api/`). The guarantee will therefore hold in production and **not** in the fastest
  tests, so the exclusion needs a test that runs against Postgres or it is being asserted by
  hope. This is the sharpest cost of the decision.
- **Reassignment is now something that can be got wrong.** Swapping a live reservation's court
  must re-check exclusion, and a swap that silently fails leaves the match pointing at a court
  somebody else holds — the original defect, moved downstream.
- **The one-transaction rule couples two contexts at the write boundary.** A payment webhook
  can now fail for a reason that has nothing to do with payment. The failure is correct — the
  match really is dead — but the operator reading the log is looking at a payment handler.
- Turnaround time between reservations is not modelled. Two matches back to back on one court
  with no gap will be accepted, and whether a club needs a buffer is unasked.
- **Nobody has said who authors a category**, or whether a category is a club's word or the
  platform's. The reservation does not need to know, but the ladder's *"a court of this
  category"* question does.

**Neutral**

- `ClubPolicy` is untouched. Which fields exist, who authors them, and what `maxHoldAge`
  defaults to remain open ([ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)).
- `MatchSnapshot` carries `CourtHold` and a `ClubSnapshot` and never a court identity, so
  [ADR-0026](0026-matchmaking-engines-snapshot-input-contract.md)'s input contract needs no
  change: the engines never wanted the court's name, only whether one is held and how firmly.
- The fourth of `CONTEXT.md`'s pre-Bookings questions — which side owns cancellation windows
  and pricing — is **not** answered here and stays open.

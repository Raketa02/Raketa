# ADR-0077 — A club is a record, and history is a property of three facts rather than of the aggregate

- **Status:** Accepted
- **Date:** 2026-08-21
- **Closes:** [ADR-0002](0002-event-sourced-user-aggregate.md)'s per-context obligation for the last of the five contexts. Matches and Courts are records ([ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)), Money is event-sourced ([ADR-0055](0055-the-ledger-is-event-sourced-one-stream-per-player.md)), Players was answered by 0002 itself. **Clubs was the one still open.**
- **Narrows [ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)** for the Courts context — see [The one amendment](#the-one-amendment-a-courts-existence-carries-history-its-state-does-not).

## Context

[ADR-0002](0002-event-sourced-user-aggregate.md) made event sourcing a **per-context choice
rather than a house style**, and named the contexts that would each have to make it
deliberately. This is the last one. It is also the context with the strongest audit argument of
the group, because a club's policy governs money and inventory that **other people** depend on —
where a match's history was disputable only in ways ADR-0034 showed already live on the ledger.

**Clubs is greenfield.** There is no aggregate, no module and no seed:
`backend/app/api/v1/club.py` is an empty router that says so, and `backend/app/seeds/catalog.py`
states it outright — *"Players, onboarding assessments and Skill ratings have aggregates; Clubs,
Courts, Bookings and Matches do not."* There is also **no role or staff concept on `User`**;
nothing in `modules/auth` or `modules/users` mentions one. So this decision precedes its code
entirely, which is what [`CONTEXT.md`](../../CONTEXT.md) and the `write-adr` skill both require.

### The ledger already answers more of this than the question assumed

The argument that defeated history for Matches was *"the answer already lives on the ledger."*
Traced against Clubs, that turns out to be **literally true for the club's money and its
cancellations**, and it narrows the open question sharply:

| A club act | Where it is already recorded |
| --- | --- |
| Being paid for a court | the ledger — `club` is a party ([ADR-0056](0056-a-movement-has-two-parties-and-custody-follows-what-was-sold.md)), event-sourced |
| Marking a share paid at the counter | the ledger — a `player → club` movement, cause `shareAtCounter`, **on the club's word** ([ADR-0059](0059-the-clubs-cash-is-on-the-ledger-and-a-late-mark-is-refused.md)) |
| Cancelling a match | the match record — `clubCancelled` is a **Declaration** with its own named outbox event ([ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)) |
| **Changing policy** | **nothing** |
| **Retiring a court, or moving it out of a category** | **nothing** |
| **Changing where the club is paid** | **nothing** |

So the audit argument does not fail — it **shrinks to three classes**, and none of the three is
money, which is why the ledger cannot reach them.

### The scenario the ledger cannot answer

A club sets `maxHoldAge` to 48 h. Four matches are holding courts under it. On Friday at 16:00
the club tightens it to 6 h. [ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)
evaluates staleness on **current facts and never latches**, so those holds lapse immediately and
retroactively, and four groups lose their Saturday. **No money necessarily moved** — the
unpaid seats never charged anyone — so nothing about this reaches the ledger, and nothing
anywhere records that the cap was ever 48 h.

This is the one place ADR-0034's *"the record is the explanation"* fails. The record is the
explanation **only when the record still holds what caused the outcome**, and a policy field
updated in place does not.

### Who is asking

The audience test [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) set applies here
and narrows the requirement. In v1 there is no club console
([ADR-0040](0040-one-ladder-resolves-a-situation.md) leaves it unstarted, and
`frontend_club/src/features` holds nothing but `_template`) and no club-staff identity, so:

- the **club** cannot be the audience — there is no second manager to dispute with;
- the **player** cannot be — no policy field is ever shown to one;
- **Raketa ops**, reconstructing why a match died, is the only real audience in v1.

That sets the bar at **reconstructable**, not at *event-sourced*. It also means every entry in
any trail built now reads *"changed by: system"* — a Raketa engineer running a script. That
was weighed as an argument for deferring the machinery and **rejected**: *what it was before,
and when it changed* is the whole of the scenario's need, and *who* is the part that can be
added later without invalidating anything already written.

### The alternatives considered

- **Event-source Clubs**, like `User`, `SkillRating` and the ledger. It is the tree's pattern
  and would carry *who* on the event naturally. Rejected on two counts.
  [ADR-0018](0018-aggregate-repositories-over-the-event-store.md) refused a generic
  `EventSourcedRepository[A]` precisely so a fourth stream would be a **decision rather than a
  default**; and the read profile is wrong for it in exactly the way ADR-0034 described — the
  hold ladder reads policy on **every** evaluation and every card on Now needs its club, so
  rehydration sits on the busiest path in the product. It also does not reach the court
  catalogue without dragging the Courts context into event sourcing behind it.
- **A record plus an append-only audit table.** This is the dual write
  [ADR-0017](0017-rating-context-event-sourced.md) refused in its own Context — *"the day the
  rating row and the replayed log disagree there is nothing to say which one lied"* — and the
  thing ADR-0002 warned about by name: *"bolting on an audit table afterwards tends to drift
  from the real transitions."*
- **A record plus named outbox events, and nothing else** — ADR-0034's pattern. Rejected
  because 0034 itself calls that trail **transient** until a consumer exists, and
  playerEventsTracker is out of scope. It answers the scenario with nothing durable.
- **A record whose history-bearing facts are effective-dated.**

## Decision

**We will model Clubs as a record with a version and an outbox — and give history to three
named facts rather than to the aggregate.**

### One aggregate

There is **one `Club`**: identity, name, location, opening hours, its policy, and the
destination it is paid at. `ClubPolicy` is a value the club holds, **not** a second aggregate.
The hold ladder wanting to ask a policy question without loading a club is an **interface**
concern answered by a port — ADR-0035's own words for the analogous case are *"the match asks
for a court of this category and is given a reservation; it never learns how courts are
organised."* A separate `ClubPolicy` aggregate would have exactly one invariant, *"belongs to a
club"*, which is not an invariant.

The tenancy spine is unchanged: `Club → Court`
([ADR-0035](0035-a-reservation-claims-a-court-over-an-interval.md)). Courts remains its own
context.

### Three facts carry history, and they carry it by not being overwritten

A change to one of these does **not** update in place. It **closes the current row and opens a
new one**, carrying a validity interval:

| Series | Why it earns history |
| --- | --- |
| **The club's policy**, versioned **whole** | the `maxHoldAge` scenario: a change is retroactive, terminal for a match, and invisible to the ledger |
| **The payout destination** | the one field where a change is fraud-relevant and *"who changed this, and when"* is not a nice-to-have |
| **A court's existence and its category** *(Courts context)* | a retirement shrinks availability, and `inventoryLost` is terminal — it cancels the match and refunds everybody |

**Everything else on a club is a mutable column.** A club renaming itself is not a dispute, and
history on every field is how an audit trail becomes noise nobody reads.

**Policy is versioned as a whole row, not per field**, so *"what was this club's policy on
Friday at 16:00"* is one query rather than one per field. **The payout destination is its own
series**, not folded into the policy row: they have different authors and different audiences —
ops tunes a hold cap, finance changes a bank account — and folding them means every routine
tweak re-asserts the bank details, which is how a fraud-relevant field ends up buried in noise.

This is **not** event sourcing and it is **not** the dual write. The drift objection that kills
an audit table is an objection to **two representations of one fact**, and there is one here:
the current policy is not a copy kept beside the history, it **is** the row in force. That is
event sourcing's non-drift property obtained without event sourcing's machinery — the fold is
*the row whose interval contains now*, not a replay. It also reuses a primitive this repo
already chose: ADR-0035 made a reservation *"claim a time range, not a slot"*, and this is that
idea one context over.

### The domain never reads the past

**A policy value is always read as of now.** ADR-0031 already fixed this for `maxHoldAge` —
*"evaluated on current facts and never latched"* — and it is now the rule for the whole record.
History exists for a human reconstructing an outcome, and **nothing in the domain queries it**.

Where a value must be honoured **as booked** — a cancellation window in force when a player
committed — the fix is to **copy it onto the match record at booking**, where ADR-0034's five
kinds already has the slot: a **Constitutive** fact, *"chosen at creation, never recomputed"*,
beside `share` and `counted`. Making Clubs temporally queryable by the domain instead would put
a second aggregate's fold inside the derivation kernel — the precise thing ADR-0055 refused for
Money, because *"every state on the screen would inherit the ledger's consistency lag"*, and
what [ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md) and
[ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) keep the kernel a pure function
of the record and the clock for.

### `changedBy` exists from the first migration

Every row in every series carries an actor, written as a **system sentinel** until a club-staff
identity exists. Adding the column later would leave every pre-existing row claiming an actor it
never had; a nullable column added afterwards cannot distinguish *"we didn't know"* from
*"nobody did it"*. A sentinel that says *"system, no human identity existed"* is a true
statement.

### Two guards, answering two different questions

- **A version on the club**, as ADR-0034 gives Matches and Courts, so two concurrent writers
  cannot interleave.
- **A partial unique index per series** — `(club_id) WHERE valid_to IS NULL` — so a bug can
  never leave two rows open.

They are not redundant. The version stops a race; the index stops an invariant violation from
ever reaching disk. Discipline alone would mean the invariant is asserted by code review, which
is what ADR-0035 refused when it said exclusion is *"enforced by the database, never by read
ordering."*

**This is the cheap case of ADR-0035's pattern and does not inherit its cost.** 0035 called
interval exclusion *"the sharpest cost of the decision"* because reservations are
many-per-court and genuinely overlapping, needing `EXCLUDE USING gist`, which PostgreSQL has and
SQLite — where `tests/api/` runs — does not. A club has exactly **one open row per series**, so
the constraint is *at most one row with a null `valid_to`*: a **partial unique index**, which
both engines support. The guarantee therefore holds in the fast tests as well as in production.
Recorded explicitly so a later reader does not assume Clubs carries 0035's Postgres-only gap.

### No outbox on Clubs

Clubs does **not** inherit ADR-0034's announcement obligation. Nothing has to *react* to a
policy change: the ladder is evaluated on current facts and never latches, so a tightened cap
takes effect the next time anyone looks, and availability is a **query** over reservations
(ADR-0035), so a retired court is already accounted for. There is no cache to bust and no
consumer to notify.

ADR-0034's obligation was justified by a **named** future reader, playerEventsTracker.
[ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md) has since narrowed
exactly this pattern to *a named future reader*, and Clubs has none. Announcing anyway would be
the audit table wearing a different hat — a second representation, with the same question about
which one lied. If a consumer appears, the effective-dated rows **can be projected into events
after the fact**; that is not true in the other direction, which is why the asymmetry favours
waiting.

### The one amendment: a court's existence carries history, its state does not

ADR-0034 says *"no aggregate in [Matches or Courts] will keep event history."* The court-retirement
case above needs the catalogue **as it stood**, so this record narrows that sentence for Courts.

The narrowing is deliberately small, and ADR-0034 is **not** wrong: it argued about a court's
**reservations and state**, and never about whether a court **exists**. A court's current state
remains a record with a version and no history, exactly as 0034 decided. What gains a validity
interval is the catalogue row — *this court existed, in this category, between these instants*.

ADRs are immutable once accepted, so 0034 is not edited; it gains a **scope note** pointing
here, the same route [#38](https://github.com/Raketa02/Raketa/issues/38) took with ADR-0062.

## Consequences

**Easier**

- **The scenario that motivated this is answerable.** *"What was this club's hold cap on Friday
  at 16:00, and when did it change"* is one query against one table, and it cannot be wrong,
  because the row that answers it is the same row the ladder read.
- **`inventoryLost` becomes explicable.** ADR-0035 makes it *"a query result, always"* — nothing
  was free — and the catalogue history is the second half of that answer: whether nothing was
  free because everything was booked, or because the club retired the court.
- **The last of ADR-0002's five contexts is closed**, and closed the way a genuinely per-context
  rule looks when it is real: two records, one event-sourced ledger, and one record with
  history on three named facts. None of the three answers was inherited.
- **Nothing new is invented.** The mechanism is ADR-0035's interval, the concurrency guard is
  ADR-0034's version, and the read path is an ordinary row.
- **The kernel stays pure.** The domain reads current policy and never a fold, so no state on
  Now inherits another aggregate's consistency lag.

**Harder**

- **Every write to a history-bearing fact is now two statements, and getting it wrong is
  silent.** Closing the old row and opening the new one must happen in one transaction; a
  partial failure leaves either no open row (the ladder reads nothing) or — caught by the index
  — a refused write in a code path that looks like an ordinary update. The index makes the
  second case loud and does nothing about the first.
- **The trail's actor column is a constant, and will be for as long as there is no club
  console.** It answers *what* and *when* and never *who*. Anyone reading it in v1 should know
  that up front rather than infer a fleet of system-initiated changes.
- **Three history-bearing facts is a judgement, and the boundary will be tested.** The next
  field somebody wants history on — opening hours, when a club's hours change under a booked
  match — will arrive as a request to widen the list, and there is no mechanical test for
  whether it belongs. The criterion is the one this record used: *does a change to it
  retroactively alter an outcome that no other record explains?*
- **A fourth persistence idiom is now in the tree.** Event-sourced aggregates, records with
  outboxes, interval-excluded reservations, and now effective-dated series — an agent
  pattern-matching on `backend/app/modules/` will find three wrong templates before the right
  one. This is the same hazard ADR-0034 flagged for itself, one further along.
- **Reading current policy costs a predicate, not a lookup.** Every read carries
  `WHERE valid_to IS NULL`, and forgetting it returns every version a club has ever had. That
  is a bug that passes a unit test on a club with one policy version and fails in production on
  the first club that ever changed one.

**Neutral**

- **Money is untouched.** The club is still only ever a payee ([ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)), the
  counter-mark is still a ledger movement on the club's word (ADR-0059), and the Raketa→club
  payout run is still outside the Money context (ADR-0055). What this record adds is only that
  the **destination** of that run carries history.
- **`ClubPolicy`'s contents remain open.** Which fields exist, who authors them, what each
  defaults to, whether the platform floors `maxHoldAge`, and who authors a court `category` are
  [#47](https://github.com/Raketa02/Raketa/issues/47)'s and are deliberately not answered here.
  This record decides only that policy is a **whole-row versioned value**; #47 fills the row.
- **The club console remains out of scope**, and gains one obligation it did not have: the
  screen that authors policy is authoring a **new version**, not editing a field, and its
  affordances should say so.
- The fourth of `CONTEXT.md`'s pre-Bookings questions — which side owns cancellation windows and
  pricing — is still not answered. This record fixes only *where a window that must be honoured
  as-booked is stored*: on the match, as a Constitutive fact.

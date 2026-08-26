# ADR-0104 — The search record is the answer, and it never expires

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[`docs/specs/matchmaking/matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md)
writes the same numbers down twice, in two stores, for two reasons, and never notices.

**§8.3** holds the stronger of the two convictions and this record keeps it whole: when a player
taps *Why 78?*, **the breakdown reads the stored result and never recomputes**. Recomputing
scores against an index that has moved — a rating updated, a grid edited, somebody who went
active — so the number in the sheet disagrees with the number on the card, *"in a product whose
one promise is that its numbers are checkable."* §8.3 satisfies this with a Redis key,
`search:{id}`, at a **30-minute TTL**, listed among §14.1's mutable ledgers and §15.3's stores.

**§19.2** then requires an append-only `search_candidate` table holding — field for field — the
same thing: the Fit, every term with its contribution, the liveness reasons, the inclusion
reason. Its argument is different and also correct: *"a search that was not recorded is evidence
that no longer exists,"* with no backfill and no reconstruction, so every day it is not shipped
is a day of permanently missing denominator.

Two stores for one set of numbers was defensible in the architecture that proposed it — a
separate Go service with its own Postgres, a p99 hostage to a connection pool, and a cache in
front. [ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) removed that
architecture. The write §19.2 requires is already happening, in the same process, in the same
transaction, one primary-key lookup away from the tap that asks *Why 78?*

What remains of the two-store design is its cost: **two representations of one number, free to
disagree, in the one place §8.3 says disagreement is fatal.** The 30-minute TTL is the
disagreement, scheduled.

Three further facts decided the shape:

- **Nothing in this repository has ever opened a Redis connection.** `redis` is pinned in
  `backend/pyproject.toml` and a `redis:7.2` container runs in `docker-compose-local.yml`, and
  that is the whole of it — no client, no port, no adapter, no test double. ADR-0093's *"redis is
  already a backend dependency"* is true of the Compose file and not of the code.
- **The event store is the wrong home**, though "append-only" is the shared word. `event_store`
  exists to rebuild an aggregate's state by replay ([ADR-0089](0089-player-profile-context-event-sourced.md),
  [ADR-0097](0097-event-store-append-order-is-a-sequence-column.md)). A search has no state, no
  invariants and no life story; replaying one rebuilds nothing, and putting the platform's
  highest-volume rows in the store taxes every rebuild that has to scan past them. ADR-0093
  already ruled that nothing in the matcher is event-sourced.
- **There is no erasure.** §21 promises a player's rows are deleted *"on the backend's erasure
  event."* No such event exists; nor does account deletion, nor any code path in `app/` that
  removes a player.

## Decision

**We will keep one durable record of a search, in the backend's own database, and read the
product's own explanation out of it.**

### 1. One store, and it is not Redis

Two append-only tables owned by `app/modules/matchmaking/` — `search` and `search_candidate` —
written with plain SQL through the existing `UnitOfWork`. **Not the event store, and not the
outbox:** the event store is for things with invariants, and the outbox delivers facts to
consumers, of which this has none. The reader is a query.

**`search:{id}` is deleted from the design.** *Why 78?* is a lookup by primary key on the row the
request has just written. §14.1's other ledgers are untouched by this record; **this one needs no
Redis at all**, which is worth knowing before something else assumes a client exists.

### 2. A returned search is a recorded search

The recording is **durable before the response returns**, in the request's own transaction. If
the insert fails, **the search fails** — no shortlist is returned.

The instinct against this is *never fail a player's search because analytics broke*, and it is
answered by observing that this is not analytics: the `search_id` **is the response's own
identity**. Without it the next tap has nothing to cite — no *Why 78?*, no origin key, no way to
send interest. Degrading returns a shortlist the player cannot act on and calls it success. The
gate-shaped choice matches [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md):
fail closed, and keep the invariant that makes every later rate computable without a case
analysis.

### 3. Nothing expires

**No retention window ships.** The 30-minute TTL is gone and nothing replaces it. A search
breakdown stamped with its `ruleset_version`, `snapshot_version` and `at` is a claim about a
moment — *this is what we saw at 19:04 on Thursday* — and it does not become false with age.

Deleting later is a migration; recovering later is impossible. The revisit trigger, in ADR-0093's
shape, is **observed table size, never a calendar**: when `search_candidate` passes 100 million
rows, tier it. §17 puts peak at 1–20 searches a second and a launch city nowhere near it.

### 4. Erasure is therefore the only deletion path, and it is recorded as a demand

Choosing to keep rows forever is what creates the obligation, so this record cannot both keep
everything and leave erasure to somebody's memory. In the shape
[ADR-0098](0098-matcher-demands-as-executable-contracts.md) used for the contexts that do not
exist: **erasure of a player deletes their `search` rows and their `search_candidate` rows in
both roles — as searcher and as recorded candidate — and the denominator loses them.** The
mechanism belongs to whoever builds erasure; the demand is written down in
[`search-telemetry.md`](../specs/matchmaking/search-telemetry.md) so it is satisfiable on purpose
rather than by accident.

Rejected: **pseudonymising at write time** so erasure is one row in a mapping table. It buys a
mapping table that is itself the personal data, a lookup on every write, and broken joins to
every other context — real engineering for a problem this system does not have at this size.

### 5. What the searcher may read, and what nobody may

The searcher may read **their own returned candidates**, and nothing else, asserted by a test
rather than by a convention: a `search_id` that is unknown or belongs to somebody else is
refused.

The record also holds a **near-miss band** — the best scored candidates that did not clear the
quality floor, which
[`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md) §7 requires and calls *"the
entire falsifier."* **No route ever returns it, to anyone.** A player may ask why somebody was
shown; nobody may ask who was withheld. That is the line §21 already draws around passes and
declines, and it is asserted on the response shapes, not left to review.

## Consequences

- ***Why 78?* is answerable forever, and answerable at all.** The breakdown outliving thirty
  minutes is the point: the claim is checkable the next day, which is when a player who felt
  badly matched actually goes looking.
- **One number, one row.** The failure mode this record exists to prevent — two stores of one
  Fit, drifting — is gone by construction rather than by discipline.
- **Redis is not required by the matcher's first build.** Three of §14.1's ledgers still want it
  and will bring their own adapter; this decision does not.
- **A search now writes.** A read-shaped request performs one insert of ~20 rows plus one, inside
  the p99 budget of 60 ms (§17), and a search cannot succeed while the database refuses writes.
  That is a new coupling and it is deliberate.
- **`search_candidate` will be the largest table in the system**, and it is kept forever. The
  trigger in §3 is the answer to that, and it is a size, so somebody has to be watching it —
  §19.3's operational metrics are where it belongs.
- **A durable record of who was offered whom, indefinitely.** Ids only, never exposed beyond the
  searcher's own returned rows, and — by
  [ADR-0101](0101-partition-derived-never-a-matching-criterion.md) and §7.2 — carrying no name,
  photo, email, date of birth or precise location, because those fields do not exist. It is
  still a social graph, and §4's demand is what keeps it honest.
- **§8.3's mechanism is discarded and its conviction is kept.** §14.1 loses a row, §15.3 loses a
  reason for Redis, and §19.2's three tables become two — the third is settled by the **Origin
  key** the glossary already carries, on the record that expresses interest.

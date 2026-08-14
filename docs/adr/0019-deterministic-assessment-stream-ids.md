# ADR-0019 — Assessment stream ids are derived from (player, sport, attempt)

- **Status:** Accepted
- **Date:** 2026-08-14

## Context

`POST /api/v1/assessments` is idempotent per player and sport: `CreateAssessment` asks
whether an unfinished run exists before opening one. That guard is a **read before a
write**, and it closes every case where the first start has already committed — a retry
after a lost response, a second device, a double tap slower than a round trip.

It cannot close two starts that both read *before either has appended*. Each minted its own
`assessment_id` with `new_uuid()`, so the two appends landed on different streams: there was
no `expected_version` for them to collide on and both succeeded. The result was a second run
for one sport — and because the in-progress lookup answers with a single run, the loser was
**stranded**: not resumable, not abandonable, invisible to every client path, so nothing
surfaced it and nothing cleaned it up.

The window is small — both requests must be in flight before either commits, and the client
blocks its confirm while a start is in flight — but the failure is silent and permanent.

**The blocker was never the design, it was testability.** `tests/api/` drives one in-memory
SQLite connection through HTTPX ASGI, so it cannot express two genuinely concurrent starts.
Landing an unverifiable concurrency fix is worse than a documented known gap, so the issue
was deliberately left open until a seam existed.

Two things changed that. The aggregate repositories ([ADR-0018](0018-aggregate-repositories-over-the-event-store.md))
put a `DomainEventStore` behind a port, so a store that *makes* the interleaving happen is a
test double rather than an infrastructure project. And a re-reading of the schema found that
the uniqueness this needs **already exists**: `uq_event_store_stream_version` on
`(aggregate_type, aggregate_id, version)` has been on `event_store` since it was created,
and `SqlAlchemyEventStore.append` already translates the resulting `IntegrityError` into
`EventStreamVersionConflict`.

## Decision

An Assessment's event-stream id is **derived**, not minted:

```python
assessment_stream_id(player_id, sport, attempt) = uuid5(namespace, f"{player}:{sport}:{attempt}")
```

- **The attempt counts every stream the pair has ever opened**, not the open ones. An
  abandoned run still happened and still holds its attempt number; counting only open runs
  would hand the next run an id that is already taken, and the sport would be unstartable
  for good.
- **The read that derives it is not load-bearing for correctness.** Two starts that both
  read first compute the *same* attempt, therefore the same id, therefore collide on version
  1 of one stream. The count only picks a candidate; the constraint does the enforcing.
- **The loser rolls back and re-reads.** If the winner has committed, its run is handed back
  with `created=False`, exactly as the ordinary retry returns it — the player cannot tell
  the two apart and should not be able to. If it has not committed, the conflict is
  re-raised and surfaces as a **409 `concurrent_modification`**, which the client retries
  into the same answer. Either way no second stream is opened.
- **`SkillRating` already worked this way.** `skill_rating_id(player, sport)` is `uuid5`-
  derived, with a docstring arguing for it. This is the same rule where a *run* can legitimately
  happen more than once for a pair, which is what the attempt adds.

### The alternative declined

**A projection table** carrying one row per (player, sport, open run) with a unique
constraint. It has a real second prize — it would give the in-progress lookup an index
instead of today's stream scan — but it costs a migration, a read model, and a rule for who
maintains it. The stream scan is not a measured problem yet, and ADR-0018 already names a
projection as the answer *when it stops being tens of streams*. Choosing it now would be
paying a schema cost for a concurrency guarantee the schema already provides.

### What this does not change

**Ids become derivable by anyone who knows a player id, and that leaks nothing.** Reading an
assessment requires saying whose it is (`load(id, *, for_player)`), and another player's
assessment is reported exactly as an absent one — so a guessed id answers not-found either
way. The property PRD #42 story 8 asks for is preserved.

**Existing runs keep their random ids.** The derivation applies to streams opened from now
on, and the attempt count includes the old ones, so a pair holding one legacy stream gets
attempt 1 and cannot collide with it.

## Consequences

**Easier**

- The race is closed with **no migration, no new table and nothing to maintain**.
- `EventStreamVersionConflict` now has an HTTP mapping (409, `concurrent_modification`), so
  a genuine concurrent write stops telling the client the server broke — a gap ADR-0018
  predicted when it made the exception reproducible in a unit test for the first time.
- Concurrency is testable at all. `RacingEventStore` holds every candidate scan at a barrier
  until all racers have read, which is precisely the window the guard cannot close, and the
  seam is worth having beyond this issue.

**Harder**

- **The identity of an Assessment is now a fact about the store, not a fresh value.**
  Deriving it costs one scan of the pair's streams on every start that opens a run. That
  scan was already being made by the in-progress guard; this makes it two.
- The attempt number has to come from somewhere, and that somewhere is a count of streams.
  A projection would answer it more cheaply, which is the argument that will eventually
  bring one.
- **The seam is a fake, not the database.** `test_concurrent_starts` proves the use case
  serialises; `test_event_store_concurrency` proves the constraint is real and that the
  adapter reports its rejection as a domain conflict. Neither is a two-connection test
  against Postgres, and adding one would make `make check` require Docker.

**Neutral**

- Deduplicating runs already stranded in an environment is not in scope. This prevents new
  ones.

# ADR-0110 — The candidate index tails the ordered log; the outbox delivers side effects

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) made the candidate
index "a rebuildable projection — drop it and replay the event store". It did not say what
does the replaying, and the design document's answer no longer applies.

§7.3 ranks three transports and picks (a): the `EventWorker` POSTs batches to the matcher's
`/ingest` endpoint. It rejects (c) — *the matcher polls the outbox directly* — on the ground
that this "makes the matcher a reader of the backend's private tables and breaks the
only-HTTP rule". **ADR-0093 deleted that premise.** The matcher is a module inside the
backend; there are no private tables to cross into, and there is no POST. What remains is a
genuine fork between subscribing to the outbox and reading the log, and three facts in the
shipped code decide it.

**The outbox cannot carry a watermark.** `event_delivery_queue` orders by
`(created_at, id)` — both of the non-orders [ADR-0097](0097-event-store-append-order-is-a-sequence-column.md)
rejected by name — and `fetch_pending` drains it `FOR UPDATE SKIP LOCKED`, so delivery order
is *deliberately* not append order. Worse, `EventPublisher.publish_many` mints a fresh
`new_uuid()` for the outbox row, unrelated to the `id` the event store wrote for the same
event: **there is no join key from an outbox row back to its `event_store` row.** An outbox
subscriber cannot name a `sequence_no`, and
[`search-telemetry.md`](../specs/matchmaking/search-telemetry.md) §6 requires that
`snapshot_version` do exactly that — *everything up to and including this is applied* —
because [ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) makes the
search record reproducible forever.

**The outbox is leased, once per platform.** That is right for a side effect and wrong for a
projection: a leased delivery is a thing that happens once *somewhere*, and a projection is a
function of a log that anybody may recompute.

**Nothing in `app/` projects anything today.** The candidate index is the platform's first
read model; the only event handlers registered are `LogPlayerProfileEvent`-shaped loggers.
There is no existing projection idiom to be consistent with, so this ADR is setting one.

Two further constraints bind the answer.

**[ADR-0092](0092-periodic-jobs-as-embedded-loops.md)'s concurrency rule.** With N API
processes a job runs N times per interval with no lock, and *"a job that cannot tolerate that
may not be registered here; it needs a different mechanism, and that mechanism needs its own
ADR."* Applying a row is safe beside itself when guarded by the sequence it was last moved
at. **A shared cursor is not.** Two writers racing on one cursor row each advance it past
events the other applied — harmless for the rows, fatal for the watermark, which would then
claim coverage no single reader ever established.

**Identity is assigned at `INSERT`, not at `COMMIT`.** A transaction holding `sequence_no`
100 can commit *after* one holding 101, so a reader that consumes to `max(sequence_no)` skips
the late one and its watermark becomes a lie about what it has seen. This is the caveat
`search-telemetry.md` §6 handed forward, and it bites the *reader*: it is not fixed by
serialising ticks.

### Ruled out

- **A dispatcher handler on the outbox.** Free — retries, dead-lettering and at-least-once
  are already built — and it cannot produce the one number the design has already promised to
  record forever. A projection whose watermark is unnameable is one whose rebuild cannot be
  proved equal to its tail.
- **`pg_advisory_lock` around the tail read.** The leader election ADR-0092 was written to
  avoid, arriving anyway, with its own held-lock-behind-a-dead-process failure mode — bought
  to protect work that a serialising read already protects.
- **No shared cursor at all, deriving the watermark as a `min` over per-row stamps.** Correct
  and unaffordable: it makes reading the watermark a full scan of the table whose freshness it
  describes.
- **A safety lag — consume only rows older than `statement_timeout`.** Provably past any live
  transaction, needs no `xmin`, and spends the entire timeout out of §17's 2 s freshness
  target for a race whose real duration is milliseconds.
- **A second, commit-ordered column on `event_store`.** Correct, and a second write on every
  append to the platform's hottest table, for a property `xmin` already exposes.
- **Deferring the out-of-order commit problem** on the ground that one API process makes it
  nearly unobservable. This is precisely the argument ADR-0097 refused: cheap now against a
  near-empty store, a table rewrite and an uninventable backfill later.

## Decision

**We will build the candidate index as a tail reader over `event_store` ordered by
`sequence_no`, advancing a single cursor row taken `FOR UPDATE`, and consuming only a
contiguous prefix. The outbox keeps delivering side effects and is not the projection's
feed.**

- **Two subscriptions, two guarantees, said out loud.** The same domain event drives the
  outbox (delivered once, eventually, out of append order) and the projection (replayed, in
  append order, by anybody). They are not the same subscription and neither is a fallback for
  the other. The outbox is for *things that happen because* an event happened; the projection
  is for *a function of the log*.

- **The cursor row is taken `FOR UPDATE` for the tick.** This keeps ADR-0092's rule literally
  true rather than by exemption: a concurrent run does not race, it **blocks, then reads the
  advanced cursor and finds nothing to do**. The lock is the transaction, so there is nothing
  to leak behind a dead process and nothing to expire mid-run — which is the exact property
  that let ADR-0092 refuse leader election. It inherits the cost ADR-0092 already accepted for
  the photo sweep: one session held for the length of a bounded batch. No new mechanism, so no
  amendment to ADR-0092.

- **The watermark is contiguous, and a gap is stepped over only under an `xmin` horizon.**
  The tick applies rows up to the last *contiguous* `sequence_no`. A hole is either a
  transaction still in flight or one that aborted, and the two are indistinguishable from the
  reader's side — so `pg_snapshot_xmin(pg_current_snapshot())` decides: once no transaction
  old enough to fill the hole is still running, the hole is permanent and the cursor steps
  over it. Without this the projection stalls forever on one aborted append. **Contiguity is
  the literal reading of the sentence `search-telemetry.md` demanded**, so `snapshot_version`
  means what it says by construction rather than by argument.

- **The batch and the cursor advance in one transaction, and the cursor is the
  idempotency.** §7.3's four-field `(event_type, schema_version, occurred_at, event_id)` row
  stamp was designed against at-least-once HTTP delivery, which this design does not have. It
  collapses to **one column, `applied_through_sequence_no`**, kept for a different job: it is
  what the snapshot's delta refresh reads to know which rows moved
  ([ADR-0112](0112-the-snapshot-is-a-per-partition-container-bound-once.md)), and what makes an
  out-of-order repair provably safe. **§7.3's `occurred_at` comparison is struck**: dropping
  "an event older than what a field already reflects" by comparing domain moments is ADR-0097's
  mistake wearing a different hat, and ADR-0089 guarantees the ties exist.

- **A fact the index holds must arrive as an event, or it is not in the index.** This is what
  makes §7.4's rebuild true rather than aspirational, and it is what forbids the tempting
  shortcut of a plain column touched on each authenticated request — see
  [ADR-0111](0111-the-index-holds-only-what-a-player-changes-about-themselves.md).

- **CI asserts the equality, not the clock.** §7.4 commits to a rebuild exercised on a
  production-sized fixture with wall-clock as a tracked metric. The assertion is: **tail a
  fixture incrementally, rebuild the same fixture from zero, and require the two tables to be
  identical.** That one property proves the projection is a pure function of the log, that
  ADR-0097's total order does the job it was written for, and that
  [ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md)'s determinism has a
  stable input — and it is what would actually be false if a projection had a bug. A
  wall-clock bound on a shared runner is a flaky test that gets muted; the five-minute figure
  stays a metric the rebuild logs. Measured, the projection is not the constraint: 959 000
  events/s on one core, **1.0 s of CPU for a 50 000-player city**.

- **Rebuild is a `make` target built from `app/bootstrap/composition.py`, never an admin
  route.** A button that drops and rebuilds the index is a button that is eventually pressed
  in the wrong place. ADR-0092's register is for loops; this is a one-shot operation and does
  not belong there.

## Consequences

**Easier**

- `snapshot_version` becomes a real number with a defensible meaning, so ADR-0104's
  unexpiring search record is reproducible in principle and not only in intent, and the replay
  harness (§20.3) has the input it was missing.
- Rebuild-equals-tail is one assertion rather than an operational hope, and it fails loudly
  the day a projection stops being a pure function of the log.
- Nothing about the outbox changes. Its ordering, its lease and its unrelated row id are all
  fine for what it does, and this ADR stops asking it to be something else.

**Harder**

- **The same event now has two consumers with different delivery guarantees**, and a reader
  of `app/` has to hold both in their head. Mitigated only by saying so — in this ADR, in the
  projection's module docstring, and in the spec.
- **The projection lags by the longest in-flight append transaction.** Today that is
  milliseconds, comfortably inside §17's 2 s p50, but it is a real coupling between an
  unrelated slow write and the matcher's freshness, and it has no alarm of its own yet.
- **`xmin` is Postgres-specific.** The test suite runs on in-memory SQLite, where there is no
  snapshot horizon and no concurrent appender — so the gap-stepping path is exercised against
  Postgres or not at all, and the SQLite run asserts contiguity only. This is a place where the
  suite is weaker than production, and it is worth knowing rather than discovering.
- **The tail reader is a second thing that must keep up.** The outbox worker already has this
  property; now there are two, and a stalled projection is silent where a stalled outbox is
  eventually visible as a missing side effect.

# ADR-0039 — The card projection rebuilds from the record, so its consumer needs no partition

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

`3-enrolled_match_engine_architecture.md` §2.4 specifies a materialized per-player card list —
one row per player holding their ordered cards and a monotonic `version` — and states one
requirement in bold:

> **Partition the projection consumer by `playerId`, not by `matchId`** — that is the one
> non-obvious choice, and it is what keeps a player's list version monotonic when two of their
> matches change at once.

Doc 5 reviews the same architecture and reaches the opposite conclusion about cost, saying the
fan-out is *"wiring, not infrastructure"* on the existing outbox and `EventWorker`. Both cannot
be true: a partitioned consumer is not wiring.

The existing machinery is [ADR-0003](0003-transactional-outbox-for-event-delivery.md)'s
transactional outbox. `SqlAlchemyEventDeliveryQueue.fetch_pending` orders by
`(created_at, id)` with `FOR UPDATE SKIP LOCKED`, and `EventBatch.execute` dispatches a batch
sequentially. One worker therefore preserves order globally and offers no per-key partitioning
at all; several workers preserve nothing. Building §2.4's requirement means building a second,
differently-shaped consumer beside the one that exists.

### Why the requirement dissolves

§2.4's own build step is *rebuild that one card* — `evaluate + render` against the current match
record. It does not apply a delta to a previous card. Two events for the same match, processed
in either order, both read the same current record and both produce the same card; the second
recomputes what the first already wrote. The build is idempotent under reordering by
construction, which is the same property
[ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md) relies on when it says the record
is the fixed point and the projection is a cache.

That leaves exactly one thing needing care, and it is not ordering: two workers incrementing one
player's `version` concurrently could lose an update. `UPDATE … SET version = version + 1` is
atomic on a row. A read-modify-write in Python is not, and that — not the event order — is the
defect §2.4 was reaching for.

The wire side is already safe without help. §2.5's monotonic acceptance has the client ignore
any frame whose `listVersion` is not greater than what it holds, so an out-of-order frame is
dropped rather than misapplied. Under [ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md)
there are no frames in v1 at all, and a poll reads whatever the row currently holds — which is
the newest card either way.

## Decision

**We will build the card projection as one more handler on the existing `EventWorker`, with no
partitioning.**

- **The consumer rebuilds each affected player's card from the current match record.** It never
  applies a delta and never reads a previous card to compute a new one. This is what makes
  reordering harmless, and it is a rule, not an implementation detail — a consumer that starts
  diffing has silently reintroduced the ordering requirement.
- **`version` is incremented in the database**, atomically on the row, never read-modify-written
  in application code.
- **The same code path builds a card for the projection and for a rebuild.** Invariant 13 — *the
  projection is rebuildable from match records alone* — is exercised by a drill asserting the
  rebuild is byte-identical, which is only meaningful if there is one builder.
- **§2.4's partitioning requirement does not carry**, and the reason is recorded here rather
  than left as an absence. It is amended by spec delta, not edited.

## Consequences

**Easier**

- No second consumer, no partition assignment, no rebalancing, no per-key worker pool. The
  projection is a subscription in `event_subscriptions.py` like every other side effect, which
  is exactly what ADR-0003's shape is for.
- `SKIP LOCKED` keeps working as designed: multiple workers drain the queue without
  coordination, which was its stated benefit and which §2.4's requirement would have removed.
- Delivery being deferred (ADR-0038) costs the projection nothing. It exists for `GET /now`'s
  single indexed read on its own merits.
- Disaster recovery is ordinary: replay or rebuild in any order and converge on the same rows.

**Harder**

- **An absent requirement is easy to reintroduce.** A future reader of §2.4 will find a bold
  instruction this codebase ignores. That is the specific risk this ADR exists to cover, and it
  is why the rebuild-not-diff rule is stated as a rule — a reviewer's question is *"does this
  handler read the previous card?"*, and if the answer is yes, the partition is back on the
  table.
- **A frame can carry a card newer than the event that triggered it**, because the rebuild reads
  the record at processing time rather than the record as of the event. This is correct — late
  corrected early — but it means `listVersion` order on the wire does not track event order, and
  anyone debugging by lining the two up will be confused.
- **The projection is written by a handler that is at-least-once** (ADR-0003), so it must be
  idempotent. It is, by the same rebuild property — but that is now load-bearing in two places
  for two reasons, and only one of them is obvious.

**Neutral**

- This overturns a specific claim in a document doc 5 verdicted *Keep*. The verdict stands; one
  requirement inside it does not, and §2.4's three reasons for materializing at all are
  untouched.

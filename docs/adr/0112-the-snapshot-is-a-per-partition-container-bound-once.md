# ADR-0112 — The snapshot is a per-partition immutable container, bound once per search

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

§13's determinism rule says *the index cannot move underneath a running search*, and §15.3
implements it with the design's "one clever moment": the indexer builds a fresh immutable
snapshot and the matcher swaps an `atomic.Pointer` to it every few seconds, so a search holds
one pointer for its whole life and readers never lock.

**The mechanism does not transfer, but the property has to.**
[ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) put the matcher inside
a Python API served by gunicorn workers, where "one immutable copy per process, swapped
atomically" means something different from what it means in one Go binary.

[The scale posture](https://github.com/Raketa02/Raketa/issues/165) settled the surrounding
numbers and handed three things here. `CandidateSource` is taken **at container granularity**
— `snapshot()` returning the container costs **54 ns**, while a port answering per-row
questions costs **+0.58 ms** and doubles the walk — so the granularity is not a free choice,
but *what it returns and how it is refreshed* are open. `gc.freeze()` is required after every
load and refresh, and the reason is a number: one automatic gen-2 collection over a live index
cost **57.9 ms stop-the-world**, roughly thirty times the search it interrupted, cut to 0.4 ms
by freezing. And the refresh peak was budgeted at **2× the index**, a figure
[ADR-0101](0101-partition-derived-never-a-matching-criterion.md) then wrote into trigger 4 as
`bytes_per_row × rows × workers × 2`.

That last figure is a cold-build number, and this ticket found that the steady state does not
have it.

### Ruled out

- **A whole-index container per worker.** Simplest, and it does not survive trigger 4:
  ADR-0101 makes the partition `(sport)` today and `(sport, cell)` when the index outgrows the
  API, so a whole-index swap is a shape that has to be rewritten on the day there is least time
  to rewrite it.
- **Querying the database per search.** §15.3 rejected it as "a p99 hostage to connection
  pools for no benefit at this data size", and nothing since has changed that; the measured
  in-memory search is 2.79 ms for a 50 000-player city.
- **Shared memory across workers.** `--preload` with `gc.freeze()` buys **zero** copy-on-write
  sharing for Python objects, because refcounting dirties the pages anyway; `array`-packed
  columns do share (5 MB per worker instead of 108) and cost **23% on the walk**. They are the
  answer to trigger 4, which is a memory problem, and not to this one.
- **Rebuilding the container from scratch on every refresh.** The 0.9 s figure that made the
  2× budget look necessary. It decodes 50 000 rows to change the handful that moved.

## Decision

**We will hold one immutable container per partition per worker, refresh it by copying
references and decoding only the rows that moved, and publish it by rebinding a single
attribute. A search binds the reference once, at entry.**

- **Rebinding is the `atomic.Pointer`.** Build the replacement off the event loop, then
  rebind one attribute — atomic under the GIL. A search takes the reference **once**, into its
  `SearchContext`, and every read goes through that binding. A refresh mid-search rebinds while
  the running search keeps its container alive by reference; the outgoing container is freed
  when the last search holding it finishes. That is the whole mechanism, it costs nothing, and
  it gives §13 its meaning in this process model.

- **The container is per partition, not per index.** ADR-0101 makes the partition `(sport)`
  today and `(sport, cell)` at trigger 4, so a per-partition swap is the shape that survives
  that day without a rewrite. Generation is `sport ∧ box ∧ gates` and a search never spans two
  sports, so there is no cost to pay for the split.

- **The refresh is a delta, and it shares row references with the container it replaces.**
  `applied_through_sequence_no` (ADR-0110) says which rows moved since the outgoing container
  was built; the new container copies references to the rest. There is no derived spatial
  structure to rebuild — [the scale research](../specs/matchmaking/scale-posture.md) established
  that the bounding box is **not** the cost (18.5 ns/row rejection against 1.00 µs per surviving
  candidate), which is what killed §9.2's geo-cell bucket map — so the container is a list, and
  the refresh is a pointer copy plus a few decodes.

- **Therefore trigger 4 loses its `× 2`, and ADR-0093 and ADR-0101 are amended in place.**
  The trigger becomes `bytes_per_row × rows × workers` > half the container limit, which
  **doubles the player count it fires at** — *~32 000 to roughly 64 000* at four workers on a
  1 GB container as this was written, and *~12 500 to roughly 25 000* since
  [#276](https://github.com/Raketa02/Raketa/issues/276) remeasured `bytes_per_row` against the
  shipping row rather than §7.2's. The doubling is what this ADR bought and it is unaffected.
  The `× 2`
  was budgeting a duplicate of every row during a refresh that no longer duplicates any of them.
  Amended rather than restated, in ADR-0101's own idiom — a trigger nobody can compute is a
  trigger that fires late, and one computed against a peak that does not occur fires early.

- **The intervals are 1 s and 2 s.** The tail reader runs at **1 s**, the cadence
  `EventWorker` already runs at, so no new number is invented. The snapshot refresh runs at
  **2 s**, matching §17's p50 target directly. Both are `PeriodicJob`s
  ([ADR-0092](0092-periodic-jobs-as-embedded-loops.md)); the refresh is per worker by design,
  which is the one place ADR-0092's *N processes, N runs* is the behaviour wanted rather than
  the cost paid.

- **`gc.freeze()` after every load and refresh, and it is safe here for a stated reason.**
  Freezing moves the live index into a permanent generation exempt from collection, which is
  only safe if the frozen objects cannot become unreachable garbage. **A `CandidateRow` has no
  reference cycles** — `__slots__`, primitive fields, no back-pointer to its container — so
  refcounting frees an outgoing row the moment the last container drops it, and the permanent
  generation does not accumulate. That is a property, not a hope, and it is asserted beside the
  schema test that already asserts §7.2's forbidden PII field names are absent.

- **§15.3's slogan narrows to the sentence that was load-bearing: *the pure scorer never
  touches a database.*** The *search* does — [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)'s
  live block set and [ADR-0098](0098-matcher-demands-as-executable-contracts.md)'s history are
  both database reads, taken before `matchfit` is called and carried in the `SearchContext`, and
  the Redis ledgers are read there too. "A search never touches a database" was never true after
  those decisions, and leaving it standing would make the one claim that *is* true — that
  `app/engines/matchfit/` is pure — read as rhetoric.

## Consequences

**Easier**

- §13's guarantee is one binding rather than a mechanism: a search cannot see a moving index
  because it holds the object, and there is no lock, no copy and no coordination anywhere.
- The refresh stops being a memory event. Trigger 4 gets a truer number and the platform gets
  roughly twice the runway before the index has to leave the API process.
- Trigger 4's eventual answer — packed columns, shared across forked workers — remains
  available, because the container is behind `CandidateSource` and its representation was
  always meant to be swappable.

**Harder**

- **Every worker holds its own copy and refreshes it independently**, so N workers do N delta
  reads every 2 s and may briefly disagree about a row. That disagreement is bounded by the
  refresh interval and is exactly the kind ADR-0111 says the index is allowed to have; it would
  not be tolerable for anything the index is now forbidden to hold.
- **`gc.freeze()`'s safety rests on a property of a type**, and the assertion that protects it
  is a test somebody can delete. It is the same class of guardrail as the PII schema test, with
  the same weakness.
- **The cycle-free rule constrains `CandidateRow` forever.** A future field that wants to be a
  rich object rather than a primitive has to justify itself against a 57.9 ms pause.
- **Amending trigger 4 twice makes ADR-0093's original numbers hard to read in place.** Both
  amendments are recorded in the ADRs that made them, but the reader of 0093 alone now gets a
  figure superseded in two directions.

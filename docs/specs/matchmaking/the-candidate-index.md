# The candidate index — what builds it, what a search reads, and how stale it may be

> Resolves [#173](https://github.com/Raketa02/Raketa/issues/173). Decisions are in
> [ADR-0110](../../adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md),
> [ADR-0111](../../adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)
> and [ADR-0112](../../adr/0112-the-snapshot-is-a-per-partition-container-bound-once.md).
> This file holds the commitments that are not decisions: the event list, the row, the
> cursor mechanics, the refresh, and what CI asserts.

---

## 1. The shape, in one picture

```
event_store (ordered by sequence_no — ADR-0097)
      │
      │  tail reader, PeriodicJob @ 1 s, cursor row FOR UPDATE
      │  contiguous prefix only; gaps stepped over under an xmin horizon
      ▼
candidate_row  (player_id, sport)  +  applied_through_sequence_no
      │
      │  delta refresh, PeriodicJob @ 2 s, per worker, per partition
      │  references copied; only moved rows decoded; gc.freeze() after
      ▼
CandidateSource.snapshot(partition) ──▶ one immutable container
      │
      │  bound ONCE into SearchContext at entry
      ▼
app/engines/matchfit/   ── pure. never reads anything. ──
```

The outbox (`event_delivery_queue`) is **not** in this picture. It keeps delivering side
effects, out of append order, leased once per platform. Two subscriptions, two guarantees
(ADR-0110).

---

## 2. What feeds it

### 2.1 Live contracts, consumed today

Every one of these is registered in `app/modules/*/application/event_subscriptions.py` and
exists in the store now.

| Event | Moves |
|---|---|
| `player_profile.created` / v1 | Creates the rows: tags, grid, area, radius, opt-in — **and, once #182 lands, gender and gender preference** |
| `player_profile.social_tags_changed` / v1 | `tags`, `tags_updated_at` |
| `player_profile.availability_changed` / v1 | `grid`, `grid_updated_at` |
| `player_profile.location_changed` / v1 | `area`, centroid |
| `player_profile.search_radius_changed` / v1 | `search_radius_km` |
| `player_profile.proposals_opt_in_answered` / v1 | `proposals_opt_in` |
| `rating.rating_initialised` / v1 | μ, σ, `confidence`, band and its edges, **the likely range**, `status`, `calibration_priority` |
| `auth.refresh_token_issued` / v1 · `auth.refresh_token_rotated` / v1 | `last_active_at` — see §2.3 |

`player_profile.photos_changed` is **not** consumed: ADR-0107 assembles the player card
outside the engine, so no photo fact reaches the index.

**`users` is not consumed either, and that is deliberate rather than an omission.**
`UserDisabled` never reaches this index: an *active* column that could be stale would make
staleness cost **safety**, which is the one thing §3's invariant exists to prevent — and account
state is not a fact a player changes *about themselves*, since an administrator may change it.
Gate 8 reads it **live**, as a set, beside the block set
([ADR-0124](../../adr/0124-the-matcher-gates-account-state-never-age.md)). Until that gate is
built, **a disabled account keeps its row and remains a candidate** — the gap this file's source
list made invisible for as long as nobody asked what *eligibility* meant.

`RatingInitialised` carries everything the row needs except `counted_games`, which belongs to
`matches` and is `0` today.

### 2.2 Contracts this map's decisions required — **all four have landed**

Four demands on `player_profile`, filed as a build ticket outside this map
([#182](https://github.com/Raketa02/Raketa/issues/182)) in the pattern #176 and #181
established. Every one is now registered in
`backend/app/modules/player_profile/application/event_subscriptions.py` and consumed by the
projection:

| Needed | Because |
|---|---|
| `gender` and `gender_preference` on `player_profile.created` | ADR-0096 makes both required at profile creation |
| `player_profile.play_intent_declared` / v1 | ADR-0094 |
| `player_profile.gender_changed` / v1 | ADR-0096: gender is *"self-declared, freely changed"* |
| `player_profile.gender_preference_changed` / v1 | ADR-0096: the preference is durable and a player may narrow it |

**The rule, which outlives the list:** *a fact the index holds must arrive as an event, or it
is not in the index.* It is what makes §7.4's rebuild true rather than aspirational.

### 2.3 `last_active_at`, and what it actually means

Nothing in `backend/app` records when a player was last active — not a column, not an event.
`last_active_at` is projected from `auth.refresh_token_issued|rotated` against
`REFRESH_TOKEN_EXPIRE_SECONDS = 86400`, so **it resolves days, not hours, and it means *last
session refresh***.

§9.5's *Recent activity* row is therefore read as ***this week* … *dormant***, not *Active
now* vs *3 days ago*. The −5 … +4 bounds are unchanged (that is the discrimination they were
buying), the *Active now* end is unreachable, and ADR-0106 §5 had already refused to print
*"active 2 hours ago"* to a player under any name. Full argument in ADR-0111.

### 2.4 What is deliberately absent

`player_score` and the strands are **not columns**, and since
[ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)
that is a **permanent rule rather than a wait**. ADR-0098 made them ports and the provider has
now landed as `PublishedPlayerScores`; what decides the question is ADR-0111, which this document
is otherwise about: **the index holds only what a player changes about themselves**, and a Player
Score is the platform's observation *of* them. It reaches a card through a port at assembly time,
on the seam `CardIdentity` already rides, and it reaches the engine through `PlayerScoreQuery`
bounded by the box.

So the sentence this section used to carry — *when the provider lands they arrive as
denormalised columns fed by this same tail reader* — is **withdrawn**. The scale research's
**+0.58 ms** for a per-row port call still stands as the cost of the alternative that was
rejected on other grounds; the read is a **set read over the box**, once per search, which is
neither of the two shapes that paragraph was choosing between. `opponent_variety` is not a
column either, and no longer a demand at all: it was withdrawn with its consumers (#164, #175).

Blocks, holds, history and the open-challenge set are not columns either, and never will be —
they are the facts ADR-0111 forbids the index to hold. §7.5's advisory-copy sentence is
superseded by ADR-0095 and ADR-0098.

---

## 3. The row

Identity is `(player_id, sport)` — ADR-0101, and never `(player, sport, area)`. The row holds
a *set* of area references (size one today) so a row reachable from two cells costs a pointer,
not a duplicate row.

Three assertions guard it, all build-failing:

1. **No `shard_key` field** (ADR-0101) — no field exists for a future conjunct to attach to.
2. **No name, photo, email, date of birth, nationality or precise location** (§7.2's rule).
   Gender is present and fenced: it reaches generation and gating and is **absent from the type
   handed to `app/engines/matchfit/`** (ADR-0096).
3. **No reference cycles** — `__slots__`, primitive fields, no back-pointer to the container.
   This is what makes `gc.freeze()` safe (ADR-0112, §5 below).

The Level columns are what `rating.rating_initialised` published, **copied and never
recomputed** — μ, σ, `confidence`, the band and its edges, and the **likely range**
(`range_low` / `range_high`), which is what a player card prints beside the Level so that a
reader can see how sure the platform is and not only what it thinks
([`the-play-screens.md`](the-play-screens.md) §1). `likely_range()` returns *unrounded*
values and the rounding lives in the engine, so a consumer deriving μ ± σ for itself would
own a rounding rule for a number `rating` publishes — the same argument that put the band's
edges here rather than in a table of four somewhere downstream.

Measured at **1 991 bytes a row** as `__slots__` objects, held once per gunicorn worker —
[`candidate_row_bench.py`](../../research/bench/matcher-scale/candidate_row_bench.py), which
imports this type rather than copying it. The **782** this said until
[#276](https://github.com/Raketa02/Raketa/issues/276) was measured against
`matchmaking-engine.md` §7.2's row — two `int` bitmasks, scalar area columns, epoch ints — and
never against this one. **Half the row** is vocabulary strings the projection copies per
row instead of sharing: sharing them would give back **996 bytes of the 1 991**, and that is a
change to the projection rather than to this figure.

---

## 4. The tail reader

A `PeriodicJob` at **1 s**, the cadence `EventWorker` already runs at.

1. Take the single cursor row **`FOR UPDATE`**. A concurrent run blocks, then reads the
   advanced cursor and finds nothing to do — which is how ADR-0092's *idempotent and safe
   beside itself* stays literally true with no leader election and no lease to leak.
2. Read `event_store WHERE sequence_no > cursor ORDER BY sequence_no`, bounded batch.
3. Apply the **contiguous prefix only**. `sequence_no` is assigned at `INSERT`, not at
   `COMMIT`, so a transaction holding 100 may commit after one holding 101 — a reader that
   consumes to `max(sequence_no)` records a watermark that is a lie about what it has seen.
4. A hole is either an in-flight transaction or an aborted one, and the two look identical
   from here. `pg_snapshot_xmin(pg_current_snapshot())` decides: once no transaction old enough
   to fill the hole is still running, the hole is permanent and the cursor **steps over it**.
   Without this, one aborted append stalls the projection forever.
5. Apply the batch and advance the cursor **in one transaction**. The cursor *is* the
   idempotency; there is no at-least-once delivery here to defend against.
6. Stamp each moved row with `applied_through_sequence_no`.

**§7.3's four-field row stamp is struck.** `(event_type, schema_version, occurred_at,
event_id)` was designed against at-least-once HTTP delivery this design does not have, and its
`occurred_at` comparison is ADR-0097's rejected non-order wearing a different hat — ADR-0089
guarantees those ties exist.

**On SQLite** (the test suite) there is no snapshot horizon and no concurrent appender: the
run asserts contiguity and the gap-stepping path is exercised against Postgres or not at all.
Recorded in ADR-0110 as a place the suite is weaker than production.

### The watermark

`snapshot_version` = the cursor's value, and it means **everything up to and including this is
applied** — the literal sentence
[`search-telemetry.md`](search-telemetry.md) §6 demanded, true by construction rather than by
argument. It is what makes ADR-0104's unexpiring search record reproducible, and it is the
input the replay harness was missing.

---

## 5. What a search reads

`CandidateSource.snapshot(partition)` returns **one immutable container**, at container
granularity (54 ns; per-row is +0.58 ms).

- **Per partition, not per index.** `(sport)` today, `(sport, cell)` at trigger 4 (ADR-0101),
  so the shape survives that day without a rewrite. Generation is `sport ∧ box ∧ gates` and a
  search never spans two sports.
- **Bound once, at entry**, into the `SearchContext`. A refresh mid-search rebinds an
  attribute — atomic under the GIL — while the running search keeps its container alive by
  reference. That is `atomic.Pointer` in Python, and it is the whole of §13's *the index cannot
  move underneath a running search*.
- **Refreshed by delta at 2 s**, per worker (§17's p50 target). The new container copies
  references from the outgoing one and decodes only rows whose `applied_through_sequence_no`
  moved. There is no derived spatial structure to rebuild: the bounding box is 18.5 ns/row
  against 1.00 µs per surviving candidate, which is what killed §9.2's cell map.
- **`gc.freeze()` after every load and refresh.** One automatic gen-2 collection over a live
  index cost **57.9 ms stop-the-world**, ~30× the search it interrupted; frozen, four
  collections totalling 1.1 ms, max 0.4 ms. Safe because a `CandidateRow` has no reference
  cycles, so refcounting frees an outgoing row the moment the last container drops it.

**§15.3's slogan narrows: the *pure scorer* never touches a database.** The search does —
ADR-0095's live block set, ADR-0098's history and the Redis ledgers are all read before
`matchfit` is called, and carried in the `SearchContext`.

### The `× 2` that is no longer there

A delta refresh shares row references, so the steady state never holds two copies of a row.
**Trigger 4 loses its `× 2`** and becomes `bytes_per_row × rows × workers` > half the
container limit. That was *~64 000 players* at four workers on a 1 GB container while
`BYTES_PER_ROW` was 782; at the measured 1 991 it is roughly **25 000 players** — the `× 2`
argument is untouched and the row underneath it was remeasured (#276).
ADR-0093 and ADR-0101 are amended in place (ADR-0112).

---

## 6. How stale it may be

Two budgets, not one, and neither is what §18 said it was.

| | Value | What it is |
|---|---|---|
| §17 index staleness | p50 **2 s**, p99 **15 s** | A **target on the refresh loop**. Missing it raises an alert. No behaviour changes |
| §18 lag < 15 min | serve normally | — |
| §18 lag 15 min – 24 h | serve, record `index_stale`, alarm | **Internal.** On ADR-0104's search record and in the structured logs, never on ADR-0106's envelope |
| §18 lag > 24 h | **refuse** — the honest empty state | A **quality** ladder, not a safety stop |

**§18's stated reason for the refusal is false and is replaced.** It refuses because *"a
day-old index can put a held or blocked player in front of somebody"* — but ADR-0095, ADR-0098
and ADR-0109 between them took every live-truth fact out of the index and put it in the
`SearchContext` with a backend re-verify. The refusal survives on quality: a day-old index
means stale μ, grids and intent, and a shortlist built from those is §18's own worst outcome —
a confident bad list.

**The invariant that replaces it, and that a future column is tested against:**

> **The index holds only facts a player changes about themselves. Every fact that must be live
> is never in it.**

*What happens to a search that reads a row the backend has already changed:* nothing, by
design. The index is allowed to be wrong about slow facts; it cannot be wrong about live ones,
because it does not hold any. The backend re-verifies the returned rows (ADR-0095, ADR-0098),
and a stored search read back later re-verifies again and states its withholdings (ADR-0109).

---

## 7. Rebuild

**A `make` target built from `app/bootstrap/composition.py`** — never an admin route. A button
that drops and rebuilds the index is a button eventually pressed in the wrong place, and
ADR-0092's register is for loops, not one-shot operations.

**CI asserts the equality, not the clock:** tail a fixture incrementally, rebuild the same
fixture from zero, require the two tables to be **identical**. That one property proves the
projection is a pure function of the log, that ADR-0097's total order does the job it was
written for, and that ADR-0105's determinism has a stable input.

A wall-clock bound on a shared runner is a flaky test that gets muted. The five-minute figure
stays a metric the rebuild command logs. Measured, projection is not the constraint: **959 000
events/s on one core — 1.0 s of CPU for a 50 000-player city.** The read and the write batching
set the wall clock.

---

## 8. The geo cell — the rule, not the integer

ADR-0101 makes the partition `(sport)` today and `(sport, cell)` at trigger 4. The cell **size
is not chosen here**, and that is deliberate: it is calibrated against a real population's
clustering, and trigger 4 is ~25 000 players away. Choosing it now would repeat
[#167](https://github.com/Raketa02/Raketa/issues/167)'s `QUALITY_FLOOR` mistake — a number that
cannot be calibrated is not an answer, it is a placeholder that later reads as a decision.

What *is* fixed, because it is forced by geometry:

- A 50 km `SearchRadius` at ADR-0099's ×2.0 rung makes a box up to **200 km across**.
- **A cell edge is at least the largest possible box edge**, so a box touches at most four
  cells and the number a search must union is bounded by geometry rather than by population.
- The partition key **derives from the area centroid** (ADR-0101 — there is no field for it to
  attach to).
- The row holds a **set** of area references, so a row reachable from two cells costs a
  pointer, never a duplicate row. Row identity stays `(player, sport)`.

---

## 9. What this hands onward

- **To the replay harness** ([#183](https://github.com/Raketa02/Raketa/issues/183)):
  `snapshot_version` now identifies a reconstructible index state, which is the input
  ADR-0105 said a *past*-search replay was still missing. Determinism already ships as a
  two-subprocess property test; replaying a past search is now expressible.
- **To `player_profile`** ([#182](https://github.com/Raketa02/Raketa/issues/182)): the four
  event contracts in §2.2.
- **To whoever owns `player_score`:** the strands land as denormalised columns on this row,
  fed by this tail reader, not as a per-row port call. ADR-0098's contract suite already fixes
  the shape.
- **To the operational surface, still fog:** `index_stale` and the two trigger instruments emit
  structured log records, and there is still nowhere to read them.

---

## 10. Constants introduced

| Constant | Value | What would falsify it |
|---|---|---|
| Tail reader interval | **1 s** | The contiguous prefix routinely falling behind by more than one tick's worth of appends — i.e. batches consistently hitting their bound |
| Snapshot refresh interval | **2 s** | §17's p50 target moving, or a delta refresh whose cost stops being dominated by the pointer copy |
| Trigger 4 (amended) | `bytes_per_row × rows × workers` > 50% of the container limit | A refresh implementation that stops sharing row references, which would put the `× 2` back |

---

## 11. Where this lives, now that it is built

Resolved by [#202](https://github.com/Raketa02/Raketa/issues/202). Every commitment above has
a file and a test; this table is the map between them, so that changing one of them is
obviously a change to the other.

| Commitment | Code | What fails if it breaks |
|---|---|---|
| §2 The fold, pure and per-event | `matchmaking/domain/candidate_projection.py` | `test_candidate_projection.py` — including that the register and the dispatch are exhaustive over each other |
| §3 The row, and its three fences | `matchmaking/domain/candidate_index.py` | `test_candidate_row_fence.py` (source walk + a cycle walk over a real row), `test_candidate_index_schema.py` (the tables) |
| §4 Contiguity and the horizon | `matchmaking/domain/candidate_tail.py`, `…/infrastructure/snapshot_horizon.py` | `test_candidate_index_tail_plan.py` — every ordering, with no database in the way |
| §4 The tick, the cursor, the stamps | `matchmaking/infrastructure/candidate_index_tail.py` | `test_candidate_index_tail.py` |
| §5 The container, bound once, delta-refreshed | `matchmaking/domain/candidate_snapshot.py`, `…/infrastructure/candidate_snapshot_source.py` | `test_candidate_snapshot_source.py` — reference **identity**, not equality |
| §6 Two budgets | `matchmaking/domain/index_staleness.py` | `test_candidate_index_staleness.py` |
| §7 Rebuild | `matchmaking/infrastructure/rebuild_candidate_index.py`, `…/rebuild_cli.py`, `make rebuild-candidate-index` | `test_candidate_index_rebuild_equals_tail.py` |

**Four things the build settled that this document had left open, and each is a decision
rather than a detail.**

1. **The index is two tables, not one.** A search reads `(player, sport)`; a player edits
   their profile once. `candidate_player_facts` holds what a person says about themselves and
   `candidate_row` holds what is true of them in one sport, because the fold may not look
   anything up — and a profile edit that had to know which sports its author is rated in
   would be exactly that lookup. **A row enters a snapshot only when both halves exist**,
   which is said with a join rather than with columns full of nulls a term would eventually
   read as a measured zero.
2. **`applied_through_sequence_no` carries the moving event's own number, never the batch's
   end.** §7.4 asks for the two tables to be *identical*, and a batch-end stamp differs on
   every row between a tail at 1 s and a rebuild that swallows the log whole — while the
   projection is perfectly correct. Per-event stamping costs the delta refresh nothing: a row
   moved after a container's version still stamps past that version, which is the only
   question the refresh asks.
3. **The row's area has no `area_code`, and its absence is deliberate.** The coarse centroid
   is the only spatial truth the index has and is what the bounding box reads; the
   human-readable area a player card prints is assembled outside the engine (ADR-0107) and has
   **no producer in this repository**. Deriving one here would be inventing a naming scheme
   nobody has calibrated — §8's own argument about the geo cell, one field over. It is handed
   onward with the rest of §9.
4. **`gc.freeze()` runs after every load and after every refresh *that decoded a row*.** The
   freeze promotes **everything currently tracked** into the permanent generation, not only the
   rows just built — so freezing on a refresh with nothing new would permanently promote
   whatever requests happened to be in flight, every two seconds, for ever. That is a slow leak
   bought for nothing: with no newly decoded row there is no collection for the freeze to
   avoid. The 57.9 ms it *is* buying is paid wherever there is something to buy. **This narrows
   ADR-0112's "after every load and refresh" and is the one place this build did not take that
   ADR literally** — worth an amendment if anybody disagrees.

---

**What this build did not close, stated rather than implied.**

- **The degradation ladder has no caller.** `freshness_of` is written and tested, and nothing
  in `app/` refuses on it — because the thing that would is a *search*, and there is no search
  yet. The same goes for §5's *bound once into the `SearchContext` at entry*: the container
  half is built and immutable, and there is no `SearchContext` to bind it into. Both are the
  next ticket's, not this one's, and neither is a gap that a later reader should mistake for an
  oversight.
- **The instruments emit and there is still nowhere to read them.** `snapshot_version` goes on
  every tail tick, and the refresh loop logs the lag, the rung (`index_freshness` — which is
  `index_stale` by another name, internal exactly as §6 requires) and whether §17's p99 was
  missed, at `WARNING` when it was. Structured log records, and no operational surface behind
  them, exactly as §9 said.
- **The tail reader logs a line every tick, including the ticks that did nothing.** *The reader
  ran and found nothing* and *the reader did not run* are the two states a stalled projection
  has to be distinguishable by, and a stalled projection is otherwise silent where a stalled
  outbox is eventually visible as a missing side effect.
- **A rebuild that stops short says so and exits non-zero.** On PostgreSQL a tick applies
  nothing both at the end of the log and while waiting on an unsettled hole; a run that exited
  quietly on the second would have rebuilt a *prefix* while reporting success, which is
  `rebuild == tail` failing where nobody would look.

# The search-side telemetry: what is recorded from the very first search

Settles [#169](https://github.com/Raketa02/Raketa/issues/169) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
The decisions are in [ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md)
and [ADR-0105](../../adr/0105-determinism-is-a-set-iteration-problem-in-python.md); this is the
field list they imply and the checklist a build agent ticks off.

**Every fact here is search-time and cannot be reconstructed afterwards.** There is no backfill.
A day without it is a day of permanently missing denominator, for every rate the engine is
judged by, forever.

---

## 1. Three layers, and why there are three

§19.2 records the shortlist. [`the-five-numbers.md`](the-five-numbers.md) §7 then demands two
facts *per scored candidate* — the evidence basis behind each Fit, and whether the reliability
penalty was what put somebody below the floor. Scored candidates run to ~500 a search; returned
run to ~20. Recording all of them is 25× the volume and a durable record of who was excluded for
whom.

Both demands are about **interpreting a Fit that was kept** or **explaining a candidate who just
missed** — neither is about the four hundred that were nowhere near. And one demand names the
population exactly: *the Fit of the best candidate that did not clear the floor*, which §7 calls
*"the entire falsifier."* So:

| Layer | Population | Rows per search |
|---|---|---|
| **1 · Counters** | Everything, aggregated by reason | on the `search` row |
| **2 · Returned** | What the response carried | ≤ 20 |
| **3 · Near miss** | The best scored candidates that did **not** clear | ≤ `NEAR_MISS_RECORDED` |

`NEAR_MISS_RECORDED = 10`, a named ruleset constant, revisitable. Layer 3 contains the
best-withheld candidate by construction; the per-candidate evidence basis exists for exactly the
candidates whose Fit was kept, and for the rest there is no stored Fit to interpret.

**Layer 3 is engine-internal. No route ever returns it, to anyone** (ADR-0104 §5). A player may
ask why somebody was shown; nobody may ask who was withheld.

---

## 2. `search` — one row per engine invocation

Written in the request's own transaction, committed before the response returns. If it fails, the
search fails (ADR-0104 §2).

### Identity and stamps

| Column | Notes |
|---|---|
| `id` | `uuid4` from `app/shared/ids.py`. Minted server-side, never by the client |
| `searcher_id` | |
| `sport` | **Fixes the seat count** (`kernel/sports.py`). There is no `format` column and there never will be — `CONTEXT.md` lists *Game format* under the terms this context refuses |
| `mode` | `COMPETITIVE` \| `FOR_FUN`. **`NULL` exactly when `surface = DECK`** — §9.11's deck has no mode and scores against declared Play intent instead. A check constraint, not a convention |
| `intent_read` | `COMPETITIVE` \| `FOR_FUN` \| `NO_PREFERENCE`. **Non-null exactly when `surface = DECK`** — the mirror of `mode`'s constraint, and added by [#170](https://github.com/Raketa02/Raketa/issues/170), which found that `mode` being `NULL` left the deck's own weight vector unrecorded on the row ADR-0104 makes the reproducible answer. Recoverable from `search_candidate.terms` only by reading a *candidate* row to learn a fact about the *search*, and not at all when the deal was empty. It records the **declaration as it stood**, never the vector it mapped to (`NO_PREFERENCE → fun`), so a later change to the mapping does not rewrite history |
| `surface` | `SHORTLIST` \| `LINEUP` \| `DECK` \| `FILL_SEATS` — §1.1's four (it is titled *"Two surfaces"* and lists four). Different terminal stages, and §8.4's last one is not even optimising for the searcher; pooling their rates makes every number meaningless |
| `initiation` | `HUMAN` \| `ENGINE`. §9.1 carries these two values on `SearchContext` under the name `surface`, which collides with §1.1's. **They are orthogonal** — an engine-pushed deck card is `DECK` + `ENGINE` — so they are two columns, and the one whose values say *initiated* is the one that gets renamed |
| `at` | The `Instant`, from the `Clock` port at the composition root (ADR-0105 §1, ADR-0024) |
| `engine_version` | How the maths works (ADR-0093) |
| `ruleset_version` | What the numbers were (ADR-0093) |
| `snapshot_version` | The `event_store.sequence_no` the index projection had consumed when the search began (ADR-0097). Demanded of [#173](https://github.com/Raketa02/Raketa/issues/173), not designed here — see §6 |
| `trace_id` | The request's `X-Request-ID` (`app/core/tracing.py`). One column, and *"it showed me somebody strange"* reaches the exact log line |

### The pool, counted at every stage

Generation is `sport ∧ box ∧ gates` — the shard conjunct is struck
([ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md)).

| Column | Notes |
|---|---|
| `n_generated` | After the box, before the gates |
| `excluded_by_gate` | JSONB histogram, one key per gate reason code — the ten gates of §9.1 plus [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s and [ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)'s. Counts only; **no candidate is named at this layer** |
| `n_scored` | Cleared every gate and was given a Fit |
| `n_cleared_floor` | |
| `n_returned` | Shortlist length. **Also the redaction detector** — compared against the count of `band = RETURNED` rows, a mismatch means erasure removed a candidate's row from a search that survived ([ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md) §6). It is load-bearing rather than redundant and is never denormalised away |
| `n_near_miss_recorded` | How many layer-3 rows were written, `0 … NEAR_MISS_RECORDED`. The same detector for the near-miss band, which `best_withheld_fit` cannot provide because it is a value and not a count. Added by [#183](https://github.com/Raketa02/Raketa/issues/183) |
| `best_withheld_fit` | The Fit of the best candidate that did not clear. Nullable — null means nothing was withheld, which is not the same as `0` |
| `pool_description` | ADR-0099's shape: `{sport, radius_km_used, players_in_range, window, post_gate: true}`. Written on **every** search, not only empty ones — a thin pool and a broken floor are indistinguishable without it. Codes, never a sentence (ADR-0022) |
| `latency_ms_by_stage` | JSONB. §19.3's operational half |

**Empty results are recorded exactly like any other search**, with `n_returned = 0`. There is no
separate table and no separate path; the absence of a row is never how emptiness is expressed.

### The rung offers, and the chain

ADR-0099 made relaxation an **offer**: the engine prints what relaxing the searcher's own asks
would add, and *the player accepts*. The acceptance arrives as a **second search**, so *"which
rung was taken"* cannot be written on the search that made the offer — a row cannot record its
own future.

| Column | Notes |
|---|---|
| `rung_offers` | JSONB: which of A/B/C were offered and each one's **real count**; `null` when `n_returned ≥ MIN_SHORTLIST` meant offers were not computed at all — which is itself the falsifier for `MIN_SHORTLIST` |
| `radius_clamp_bit` | Whether the widening ceiling clamped to the profile's own maximum. Tells you how many searchers are already at the ceiling |
| `offered_by_search_id` | Nullable self-reference: the search whose offer this one accepts |
| `rung_taken` | Nullable: `A` \| `B` \| `C`. Set on the **accepting** search, beside `offered_by_search_id` |

Take-up per rung is then a join, the table stays append-only, and the falsifier gets what it
actually wants: not a flag, but the **pair** of searches — what was offered, and what the same
person did about it.

---

## 3. `search_candidate` — layers 2 and 3

| Column | Notes |
|---|---|
| `search_id` | |
| `band` | `RETURNED` \| `NEAR_MISS` |
| `position` | Rank within the band. `1` is the top of the shortlist, or the best withheld |
| `player_id` | |
| `fit` | |
| `terms` | JSONB — every term with its value, weight, contribution and evidence codes. **Deliberately opaque**: it is stamped with `ruleset_version` and its shape is allowed to change between rulesets, which is exactly what a relational schema would fight |
| `degraded_terms` | `text[]` of the terms that returned `NoEvidence`. Lifted out of the blob so §19.3's per-term `NoEvidence` rate — *"a term quietly dying is invisible otherwise"* — is an array query with a GIN index rather than a JSONB scan. Also the **renormalisation basis**, without which a Fit is uninterpretable a year later |
| `modifiers` | JSONB, each with its code |
| `liveness_reasons` | `text[]` |
| `liveness_signals` | JSONB — the **raw input value** per liveness signal, never the offset it produced. The offset is a function of the ruleset's bounds, so storing it makes a Liveness-bounds change undiffable: a replay cannot re-derive under new bounds what it only has the old bounds' answer to. Added by [#183](https://github.com/Raketa02/Raketa/issues/183), which corrects [`ranking-weights.md`](ranking-weights.md) §12's *the offset applied* to *the inputs that produced it* |
| `inclusion_reason` | Nullable: `INTEREST_LIFT` \| `NEWCOMER_WINDOW` \| `ZERO_EXPOSURE`. **All three are kept here; only `INTEREST_LIFT` crosses the wire** ([#175](https://github.com/Raketa02/Raketa/issues/175)) — the other two reorder rather than admit, `NEWCOMER_WINDOW` ships to the client as a liveness reason, and `ZERO_EXPOSURE` is the first code that lives only in the store |
| `withheld_reason` | `NEAR_MISS` only: `BELOW_FLOOR` \| `INSUFFICIENT_EVIDENCE` |
| `missing_terms` | `text[]`, for `INSUFFICIENT_EVIDENCE`. Distinguishes *nobody was good enough* from *nobody was known enough* |
| `reliability_penalty_applied` | |
| `reliability_penalty_decisive` | Whether the penalty is what put them below the floor — **docked** versus **docked out** |

Primary key `(search_id, band, position)`; an index on `player_id` for erasure. An index on
`(searcher_id, at)` lives on `search` — time ordering comes from there, which is why `uuid4` is
enough and UUIDv7 buys nothing (Python 3.11 has no stdlib v7 anyway).

**Authorization:** the searcher may read their own `RETURNED` rows and nothing else, asserted by
a test. A `search_id` that is unknown or belongs to somebody else is refused.

---

## 4. The origin key is not a third table

§19.2's `search_outcome_link` does not exist. The **Origin key** — `(search_id, position)`, glossed
in `CONTEXT.md` as *required, never optional* — is carried by the record that expresses interest,
as two columns. The link is 1:1 with the interest; a separate table buys a join for nothing, and
when `matches` arrives the chain is `match ← interest ← search`, still foreign keys, still no
third table.

An interest declaration citing a `search_id` that is unknown, or that belongs to somebody else,
is **refused — never linked as null.** A silently-dropped link is a denominator that lies.

`position` in an origin key always resolves against `band = RETURNED`, because no route ever
returns a near-miss row for a player to act on.

---

## 5. The six demands of `the-five-numbers.md` §7, ticked off

| Demand | Satisfied by |
|---|---|
| How many were scored, how many cleared, and **the Fit of the best that did not** | `n_scored`, `n_cleared_floor`, `best_withheld_fit`, and layer 3's `position = 1` row |
| Which terms produced evidence, per scored candidate | `degraded_terms`, on every row whose Fit is kept (layers 2 and 3) |
| Whether a candidate was withheld for insufficient evidence, and which terms were missing | `withheld_reason`, `missing_terms` |
| Shortlist length, and whether the rung offers were computed | `n_returned`, `rung_offers` (null = not computed) |
| Which rungs were offered, each one's real count, which was taken, and the radius clamp | `rung_offers`, `radius_clamp_bit`, `rung_taken` + `offered_by_search_id` on the accepting search |
| Whether the reliability penalty fired, and whether it was decisive | `reliability_penalty_applied`, `reliability_penalty_decisive` |

---

## 6. What this hands onward

Two demands leave this spec unanswered on purpose, in the shape
[ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) uses.

**To [The matcher's picture of the city](https://github.com/Raketa02/Raketa/issues/173) — the
watermark.** `snapshot_version` must identify the exact index state a search read, such that
replaying the event store to that point reconstructs it. `event_store.sequence_no` is the obvious
carrier and ADR-0097 already put it there. **One caveat, because it is not obvious and it is
load-bearing:** Postgres assigns an identity value at `INSERT`, not at `COMMIT`, so a transaction
holding `sequence_no` 100 can commit *after* one holding 101. A projection that consumes up to
`max(sequence_no)` will skip the late one, and its watermark will then be a lie about what it has
seen. The consumption rule is #173's to design; this spec only requires that the number recorded
here means *everything up to and including this is applied*.

**To whoever builds erasure — the deletion.** There is no erasure event, no account deletion, and
no code path in `app/` that removes a player. When one exists: erasing a player deletes their
`search` rows **and** their `search_candidate` rows **in both roles** — as searcher and as
recorded candidate — and the denominator loses them. Nothing else in this design ever deletes a
row (ADR-0104 §3), so this is the only deletion path there is.

---

## 7. Constants introduced

| Constant | Value | What would falsify it |
|---|---|---|
| `NEAR_MISS_RECORDED` | **10** | **Two things now.** A floor investigation that needs a distribution ten rows cannot show — the top row is the load-bearing one and the other nine are the shape around it. And a **ruleset diff whose promotions saturate the band**: if every recorded near-miss crossed the floor, the diff understated the change and the window is too narrow ([ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md) §4) |
| Table-size revisit trigger | **100 M `search_candidate` rows** | Reached — at which point retention is tiered rather than reconsidered from scratch (ADR-0104 §3) |

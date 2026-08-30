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
| `excluded_by_gate` | JSONB histogram, one key per gate reason code — **ten in all**: §9.1's **eight**, plus [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s ninth and [ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)'s tenth. (This row said *"the ten gates of §9.1 plus"* those two, which counts twelve; §9.1 lists eight and the roster is enumerated once in [`the-engine.md`](the-engine.md) §3.) Counts only; **no candidate is named at this layer** |
| `n_scored` | Cleared every gate and was given a Fit |
| `n_cleared_floor` | |
| `n_returned` | Shortlist length. **Also the redaction detector** — compared against the count of `band = RETURNED` rows, a mismatch means erasure removed a candidate's row from a search that survived ([ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md) §6). It is load-bearing rather than redundant and is never denormalised away |
| `n_near_miss_recorded` | How many layer-3 rows were written, `0 … NEAR_MISS_RECORDED`. The same detector for the near-miss band, which `best_withheld_fit` cannot provide because it is a value and not a count. Added by [#183](https://github.com/Raketa02/Raketa/issues/183) |
| `best_withheld_fit` | The Fit of the best candidate that did not clear. Nullable — null means nothing was withheld, which is not the same as `0` |
| `pool_description` | ADR-0099's shape: `{sport, radius_km_used, players_in_range, window, post_gate: true}`. Written on **every** search, not only empty ones — a thin pool and a broken floor are indistinguishable without it. Codes, never a sentence (ADR-0022) |
| `searcher_slot_count` | How many of the twenty-one grid cells the searcher had ticked. The availability term's **denominator**, and per-search rather than per-candidate because the near-miss band pays per-candidate costs ten rows at a time. Added by [#184](https://github.com/Raketa02/Raketa/issues/184) — it is the input to the falsifier for [ADR-0120](../../adr/0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md)'s asymmetry, and there is no other row it could live on |
| `n_excluded_by_suppression` | **Deck deals only**, null elsewhere. How many candidates a **live** pass suppression removed from this deal. It is the only thing that distinguishes *your own passes emptied your deck* from *the pool is empty* — the failure mode that makes `PASS_SUPPRESS` five-numbers-shaped, and one nobody can see from any screen because no route returns a pass. Added by [#194](https://github.com/Raketa02/Raketa/issues/194) |
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
| `degraded_reasons` | `text[]`, **index-aligned** with `degraded_terms`: whose gap each stood-down term was, over `NOT_YET_ON_THIS_PLATFORM \| NOTHING_FROM_YOU \| NOTHING_FROM_THEM`. A read-back never recomputes, so the code a card printed has to be the code the row kept. **Not folded into the column above** — pairs in one JSONB column would spend exactly the queryability that lift bought |
| `modifiers` | JSONB, each with its code |
| `liveness_reasons` | `text[]` |
| `liveness_signals` | JSONB — the **raw input value** per liveness signal, never the offset it produced. **For the interest signal the raw input is the age of the yes in days, never the boolean** — [ADR-0127](../../adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md) makes the `+14` flat, so a boolean would be the *sufficient* input and the age would be lost to a Redis TTL within the month. It is the entire x-axis of *acceptance by age of yes*, and it is `their_slot_count`'s argument one signal over: a strike that is not recorded becomes irreversible by accident, and re-admitting a taper would be undiffable.  The offset is a function of the ruleset's bounds, so storing it makes a Liveness-bounds change undiffable: a replay cannot re-derive under new bounds what it only has the old bounds' answer to. Added by [#183](https://github.com/Raketa02/Raketa/issues/183), which corrects [`ranking-weights.md`](ranking-weights.md) §12's *the offset applied* to *the inputs that produced it* |
| `shared_count` | Grid cells both players ticked. With `search.searcher_slot_count` this **is** the availability term, so the value in `terms` is checkable against its own inputs |
| `their_slot_count` | The candidate's ticked cells. **Nothing reads it** — [ADR-0120](../../adr/0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md) struck `significance`, whose denominator it was. Recorded so that a ruleset re-admitting the factor is re-derivable over the corpus reaching back to the first search; **a strike that is not recorded becomes irreversible by accident**, which is [#183](https://github.com/Raketa02/Raketa/issues/183)'s `liveness_signals` argument one term over |
| `days_away` | Days to the next shared slot, at day resolution (`next_shared(shared, today)`). Nullable — null means nothing is shared, which is not `0`. Also unread by scoring, and recorded because it is the input to the falsifier for **striking** proximity: acceptance rate by `days_away`, held out |
| `inclusion_reason` | Nullable: `INTEREST_LIFT` \| `NEWCOMER_WINDOW` \| `ZERO_EXPOSURE`. **All three are kept here; only `INTEREST_LIFT` crosses the wire** ([#175](https://github.com/Raketa02/Raketa/issues/175)) — the other two reorder rather than admit, `NEWCOMER_WINDOW` ships to the client as a liveness reason, and `ZERO_EXPOSURE` is the first code that lives only in the store |
| `suppression_lapsed` | `boolean`, **deck deals only**, null elsewhere. Whether this pairing had a pass whose 30-day suppression had already lapsed — that is, whether this card is a **re-show**. Without it only plain pass rate is computable, never *pass rate on re-shown profiles*, which is the only falsifier `PASS_SUPPRESS` has. It reads the **durable pass record**, not Redis, for the reason in §6 |
| `withheld_reason` | `NEAR_MISS` only: `BELOW_FLOOR` \| `INSUFFICIENT_EVIDENCE` |
| `missing_terms` | `text[]`, for `INSUFFICIENT_EVIDENCE`. Distinguishes *nobody was good enough* from *nobody was known enough* |
| `reliability_penalty_applied` | |
| `reliability_penalty_decisive` | Whether the penalty is what put them below the floor — **docked** versus **docked out** |

**Two demands are satisfied without a column, and it is worth saying which.** *Whether an
interest lift admitted somebody below the floor* is derivable — `inclusion_reason =
INTEREST_LIFT` with `fit` below the floor of the stamped `ruleset_version`. And *yeses that
expired having never lifted anybody* is a join, not a flag: a durable interest row whose
`expires_at` has passed with no `search_candidate` row in its lifetime carrying
`inclusion_reason = INTEREST_LIFT` for that pair. Both were listed as demands in
[`the-five-numbers.md`](the-five-numbers.md) §7 and neither costs storage.

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

## 5. The demands of `the-five-numbers.md` §7, ticked off

| Demand | Satisfied by |
|---|---|
| How many were scored, how many cleared, and **the Fit of the best that did not** | `n_scored`, `n_cleared_floor`, `best_withheld_fit`, and layer 3's `position = 1` row |
| Which terms produced evidence, per scored candidate | `degraded_terms`, on every row whose Fit is kept (layers 2 and 3) |
| Whether a term produced nothing because **nobody** has it, or because one of these two people did not | `degraded_reasons`, index-aligned with it. `missing_terms` is the same fact from the gate's side and the two may not disagree: a test asserts `missing_terms` is exactly the non-`NOT_YET_ON_THIS_PLATFORM` subset, because two columns computing overlapping facts is how they drift |
| Whether a candidate was withheld for insufficient evidence, and which terms were missing | `withheld_reason`, `missing_terms` |
| Shortlist length, and whether the rung offers were computed | `n_returned`, `rung_offers` (null = not computed) |
| Which rungs were offered, each one's real count, which was taken, and the radius clamp | `rung_offers`, `radius_clamp_bit`, `rung_taken` + `offered_by_search_id` on the accepting search |
| Whether the reliability penalty fired, and whether it was decisive | `reliability_penalty_applied`, `reliability_penalty_decisive` |
| Age of the yes per lifted candidate, and whether the lift admitted below the floor | `liveness_signals` (age in **days**, never a boolean); the admission is **derived** from `inclusion_reason = INTEREST_LIFT` and `fit` against the stamped ruleset's floor |
| Yeses that expired having never lifted anybody | **Derived**: a lapsed durable interest row with no `INTEREST_LIFT` row for the pair in its lifetime. The one falsifier here that runs without `matches` |
| Cards a live suppression excluded, per deal; and whether a card is a **re-show** | `n_excluded_by_suppression` on `search`; `suppression_lapsed` on `search_candidate` — both reading the **durable pass record** (§6) |
| Refusals at the cap, and the distribution of outstanding counts | **Not here.** Both are facts about the interest **write**, not about a search — §6 |

---

## 6. The two ledgers this spec now depends on

[#194](https://github.com/Raketa02/Raketa/issues/194) put two facts inside this spec's reach that
were not previously here, and one of them cost a storage change.

**The pass record is durable; the suppression is not.** `PASS_SUPPRESS`'s only falsifier is *pass
rate on **re-shown** profiles*, and until now a pass lived solely as a Redis suppression with a
30-day TTL. A **lapsed** suppression leaves no trace the pair was ever passed — so at the exact
moment the re-show happens, the fact that makes it a re-show has expired. The **Origin key** on
`POST /passes` was bought for this falsifier and pays only half of it: it records where a pass
came from, never that a later card is the same person coming back.

So the pass becomes a durable row — `(passer, passed, sport, at, search_id, position)` — and the
30-day suppression stays the Redis TTL, derived from it
([`the-engine.md`](the-engine.md) §12). Suppression still **fails soft**, and the split is why
that stays true: the **gate** is the cache, the **evidence** is the row. Unlike an interest, a
pass record does not expire; nothing in this design deletes a row except erasure (ADR-0104 §3),
and this joins that rule.

**A prompt decline is a durable row, and its denominator is not a column.**
[#237](https://github.com/Raketa02/Raketa/issues/237) reaches the same split from the other side.
`prompts.py`'s two constants are falsified by *take-up rate on the prompt*
(`INTENT_DRIFT_SEARCHES`) and *acceptance rate on the offer, against rung acceptance*
(`REPEATED_WIDENINGS`) — three outcomes per raised prompt, and only one of the three is
unrecorded:

| Outcome | Where it already is |
| --- | --- |
| **Raised** | derived — the widening condition is `widenings_taken >= 3` over this store, the drift condition is five consecutive disagreeing searches over the same rows, and both are recomputable forever ([ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md)'s *explainable, not reproducible*) |
| **Accepted** | derived — `PlayIntentDeclared(surface=DRIFT_PROMPT)` by name, and an accepted radius is the next search asking at that radius on rung A |
| **Declined** | **nowhere.** It writes no value, and a Redis suppression that lapses destroys it |

So the decline earns a row and nothing else does. **There is deliberately no `prompts_raised`
column on the search record**, and adding one would break two arguments that are already
written down: `ShortlistAnswer.prompts` is beside the record rather than on it, because *"a
read-back a month later must not re-ask a question whose answer has since been given"*; and the
raise runs **after the commit**, because *how often have I taken this widening* has to count the
search that just ran. The named cost is that derived take-up is **approximate** — a player who
edits their radius in *You* the same week reads as a take-up — and that is enough for a falsifier
whose job is to say *nobody ever acts on this*.

**The cap's falsifier is not a search fact and does not live here.** Refusals at
`OUTSTANDING_INTEREST_CAP` and the distribution of outstanding counts per player are facts about
the interest **write**. The distribution needs no new storage — it is a query over the durable
interest ledger. The refusals are a **counter**, keyed by sport, on the write path; a raw count
alone cannot tell *20 is too low* from *somebody is saying yes to everybody*, which is why the
distribution is named beside it rather than instead of it.

---

## 7. What this hands onward

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
`search` rows **and** their `search_candidate` rows **in both roles** — and, from
[#194](https://github.com/Raketa02/Raketa/issues/194), their **pass records in both roles** and
their interest rows, since neither now expires out from under an erasure the way a Redis key
did — as searcher and as
recorded candidate — and the denominator loses them. Nothing else in this design ever deletes a
row (ADR-0104 §3), so this is the only deletion path there is.

---

## 8. Constants introduced

| Constant | Value | What would falsify it |
|---|---|---|
| `NEAR_MISS_RECORDED` | **10** | **Two things now.** A floor investigation that needs a distribution ten rows cannot show — the top row is the load-bearing one and the other nine are the shape around it. And a **ruleset diff whose promotions saturate the band**: if every recorded near-miss crossed the floor, the diff understated the change and the window is too narrow ([ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md) §4) |
| Table-size revisit trigger | **100 M `search_candidate` rows** | Reached — at which point retention is tiered rather than reconsidered from scratch (ADR-0104 §3) |

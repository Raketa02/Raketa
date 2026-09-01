# ADR-0101 — The matcher's partition is derived, and is never a matching criterion

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) put the matcher in
the backend and named four triggers that would reverse it, reasoning from the input
document's own figures because there were no others. Ticket
[#161](https://github.com/Raketa02/Raketa/issues/161) then went and measured them
([`docs/research/matcher-scale-in-python.md`](../research/matcher-scale-in-python.md)). Two
of the four triggers turn out to be wrong as written. And one question ADR-0093 left as a
detail — the shard — turns out to be the decision that is expensive to reverse, because
everything downstream keys on it.

This record extends ADR-0093 on both. It supersedes nothing: the matcher stays in the
backend, the split across `app/engines/matchfit/` and `app/modules/matchmaking/` stands
unchanged, and the reasons it was taken are untouched by the measurement — a 50 000-player
city search is 2.79 ms, which is comfortably inside a request.

### The document states the shard rule, then breaks it two sections later

§7.2 and §17 are emphatic that `shard_key` is *"a shard key, not a matching criterion"* —
the reference repository's `region` idea *"finally in the right job"*. §9.2's generation
predicate then reads:

```
shard_key == searcher.shard_key
  ∧ sport == searcher.sport
  ∧ within a bounding box of searcher.radius_km × relaxation_multiplier
  ∧ passes every gate
```

An equality in the generation conjunction **excludes**. A player three kilometres from the
searcher, well inside the radius they chose, is invisible because a boundary somebody drew
runs between them — and no relaxation rung reaches it, because
[ADR-0099](0099-relaxation-offers-the-searchers-own-asks.md) only relaxes what the searcher
themselves asked for, and nobody asked for a metro. That is a matching criterion by any
definition, and a silent one: the pool description would report the post-gate count inside
the shard and the searcher would never learn that the person across the river existed.

**The rule is worth keeping. The predicate is not.**

### Nothing in this backend produces a shard key

A profile holds one `LocationArea` — latitude and longitude rounded to two decimal places,
coarsened *on the way in* so the precise fix never reaches the event store at all
(`player_profile/domain/location.py`) — and one `SearchRadius` in whole kilometres, 1 to 50,
default 10. There is no city, no metro, no `area_cell`. Both of §7.2's spatial fields are
fields somebody would have to invent, and inventing one means also inventing whatever
assigns it, keeps it right when a player moves, and decides which side of a boundary a
suburb is on. A partition that needs an authority is a partition that can be wrong about a
person.

### Four ways to partition, and what each costs

- **Keep §9.2's equality.** Simple, and buys the sport-bucket win. Costs boundary blindness
  permanently, and makes the document's own rule false.
- **Drop the shard and scan the sport bucket for the whole deployment,** letting the box be
  the only spatial truth. Correct, and it does not scale: rejecting a row costs 18.5 ns, so
  ten cities is roughly 312 000 rows and 5.8 ms of pure rejection before a single term runs.
- **Shard, plus a hand-maintained adjacency list of neighbouring shards.** Boundary-correct
  where somebody remembered to make it so. The list is a fact with an owner and no test.
- **No metro at all: the partition is a coarse geo-cell derived from the area the row already
  holds, and generation scans the cells the radius box overlaps.** Boundary-correct *by
  construction*, because the partition and the box are derived from the same geometry. No
  registry, no authority, nothing for a player to declare, and nothing that can be wrong
  about a person that their own coordinates are not already wrong about.

### Two of ADR-0093's triggers were arithmetic, and the arithmetic was wrong

ADR-0093's **trigger 4** reasons from §7.2's *"~160 bytes per row … roughly 32 MB"* and
concludes that *"several cities at gigabyte scale"* would fire it. Measured, the same index
is **782 bytes a row as `__slots__` objects — 98 MB** — and it is held **once per gunicorn
worker**. `docker/api/startup.prod.sh` runs `--workers ${GUNICORN_WORKERS:-1}` with no
`--preload`, so the multiplier is 1 today and quadruples silently the day somebody sets that
variable to 4. On a 1 GB container the trigger is reached at roughly **80 000 rows — about
32 000 players** — which is one large city, not several. `--preload` does not rescue it:
refcounting dirties every page a scan touches, so four forked workers cost 108 MB of
*unique* set size each.

> **Corrected by [#276](https://github.com/Raketa02/Raketa/issues/276), and the correction
> runs the same way the paragraph above does.** The 782 is a real measurement of the row §7.2
> *specifies*, taken before `CandidateRow` existed and never retaken against it. The shipping
> row holds two tuples of strings where §7.2 holds two `int` bitmasks, a tuple of
> `IndexedArea` where §7.2 holds three scalars, and four `datetime` objects where §7.2 holds
> epoch ints — **1 991 bytes a row, 249 MB for the same city**
> ([`candidate_row_bench.py`](../research/bench/matcher-scale/candidate_row_bench.py), which
> imports the type rather than copying it). Every figure in the paragraph moves in the
> direction this ADR already argues; its row counts are also the `× 2` era's, separately
> halved by [ADR-0112](0112-the-snapshot-is-a-per-partition-container-bound-once.md). With
> both corrections the 1 GB container reaches trigger 4 at **~63 000 rows, about 25 000
> players**.

**Trigger 1** — *"request latency measurably contends with scoring"* — was prose, and prose
does not fire. The measurement supplies the numbers, and also the reason to instrument
rather than to wait: the largest latency event in the process is not the search but the
garbage collector, at **57.9 ms stop-the-world** for one automatic gen-2 collection over a
live index, roughly thirty times the search it interrupts.

## Decision

**1. There is no shard in the predicate, at any size.** Candidate generation is

```
sport == searcher.sport ∧ within the box ∧ passes every gate
```

and **the box is the only spatial truth in the engine.** Distance may weigh
(§9.3 has a term for it) and the radius may bound; nothing else geographic may exclude.

**2. The partition is derived, never declared.** Rows are bucketed by `(sport)` today, and
by `(sport, cell)` — a coarse geo-cell computed from the area already on the row — when row
count crosses trigger 4's threshold. Generation scans every cell the radius box overlaps.
Both keys are *derived from data the row already holds*, which is what stops a partition
from becoming a criterion later: there is no field for somebody to add a conjunct on.

**3. There is no `shard_key` field, and a schema test asserts its absence** — in the same
test as §7.2's forbidden name, photo, email, date of birth, nationality and precise
location. A metro label is still useful for *reporting*, and it is **derivable from the area
whenever somebody wants one**; a stored label with no producer, in a deployment with one
city, is decoration that the next reader would mistake for a partition. §7.2's `area_cell`
survives only as a bucket key, never as a stored criterion.

**4. Nothing routes on geography.** Under ADR-0093 there is one deployment; the day a load
balancer routes by city is the extracted service by another name, and that is trigger 2, not
a configuration change.

**5. Row identity is `(player, sport)` and never `(player, sport, area)`.** The interest
ledger, the exposure ledger, suppression and the newcomer window are all keyed on the
player, so a duplicated row makes four ledgers disagree with each other. The row holds a
*set* of areas, whose size is always one today because a profile has one. Whether a player
is ever offered a second is `player_profile`'s question; the matcher's whole obligation is
that answering it yes stays a **representation** change and never an identity change. The
cell index holds *references*, so a row reachable from two places costs a pointer. The one
price, named here so it is known rather than discovered: a second area forces the distance
term to a **nearest-area** rule, and the reason code has to say which one it measured from.

**6. ADR-0093's trigger 1 is restated with numbers, and ships instrumented.**

> **Trigger 1 has fired when, on one worker over fifteen minutes, either the p99 of one
> synchronous scoring call exceeds 20 ms, or the scoring duty cycle — searches per second ×
> mean scoring seconds — exceeds 0.25.**

20 ms is the measured bound on what one blocking call adds to an unrelated request's p99,
and a third of §17's 60 ms server-side budget. 0.25 sits below the measured knee: loop-lag
p99 was 3.5 ms at 33% utilisation and **50 ms at 65%**, and above full utilisation the
process is unrecoverable with no back-pressure and nothing in between to warn anybody.
Today's measured values are **11.4 ms and 0.07**.

**Both instruments ship in the first build** — a histogram around the scoring call and an
ADR-0092 `PeriodicJob` measuring its own oversleep — emitting fixed-name structured log
records, because this repository has structured logs and no metrics stack. A trigger that
requires somebody to go and measure is a trigger that fires late, which is the same disease
as a claim with no trigger at all.

**7. ADR-0093's trigger 4 is restated in rows and workers.**

> **Trigger 4 has fired when `bytes_per_row × rows × GUNICORN_WORKERS × 2` — the measured
> refresh peak — exceeds 50% of the container's memory limit.**

**Amended by [ADR-0112](0112-the-snapshot-is-a-per-partition-container-bound-once.md): the
`× 2` is struck.** It budgeted a duplicate of every row during a refresh, and the refresh
this ADR assumed was a cold rebuild. #173 made it a **delta** that copies row *references*
from the container it replaces and decodes only the rows that moved, so the steady state
never holds two copies of a row. The trigger is
`bytes_per_row × rows × GUNICORN_WORKERS` > 50% of the limit — roughly **25 000 players** on
four workers of a 1 GB container, twice what the `× 2` allowed. (That figure read *64 000*
until [#276](https://github.com/Raketa02/Raketa/issues/276) remeasured `bytes_per_row` against
the row that ships rather than the row §7.2 specifies; the doubling this paragraph argues for
is untouched.) A trigger computed against a peak that does
not occur fires early, which is the same defect in the other direction as the one this
section was written to fix.

The module computes this at every index load, from the **actual** worker count and the
cgroup limit, and **warns**. It never refuses to start: refusing would take sign-in down to
protect a feature the matcher owns. The answer to the warning is a representation change and
not a service — `array`-packed columns are **43 bytes a row**, below the figure ADR-0093
trusted, and they genuinely do share across forked workers, at a cost of 23% on the scan.
They are the answer to trigger 4 and **never** to trigger 1.

**8. Multi-country is trigger 4 plus one clock parameter, and that is the whole
commitment.** Nothing else in the matcher knows what a country is: the cell partition is
geographic and works at any latitude, the equirectangular distance already carries its
`cos(lat)` correction, and the availability grid is timezone-free by construction —
`availability.py` records that *"nothing in this module has a duration, a date or a timezone
in it"*. The one exception is [ADR-0100](0100-challenge-window-derived-never-chosen.md)'s
derived window, which is a rule with thresholds evaluated against *now*: **the zone is an
input to the derivation, never `Europe/Warsaw` baked into it.** That costs one parameter
today and is the difference between a configuration change and a rewrite. Currency, language
and legal residency are not matcher concerns and this record promises nothing about them.

The commitments that are *not* decisions — the escalation ladder, the derated cost table and
SLOs, the `K` ceiling and the list of what is deliberately not built — live in
[`docs/specs/matchmaking/scale-posture.md`](../specs/matchmaking/scale-posture.md), because
they are a set of things to check work against rather than one decision, and an ADR that
tries to be a spec stops being either.

## Consequences

**Easier**

- **The document's own rule becomes true.** *A partition, never a matching criterion* is now
  enforced by the absence of a field rather than by everyone remembering, which is the same
  move §7.2 makes for a protected characteristic and the reason that one works.
- **Nobody has to decide where a metro ends.** No registry, no boundary file, no authority,
  and no support conversation about which side of a river somebody is on.
- **The pool description means what it says.** ADR-0099's `players_in_range` is now literally
  the count inside the radius, not the count inside the radius *and* the shard.
- **Multi-city and multi-country are the same change** — more rows — and that change already
  has a trigger and a measured answer.
- **Two triggers can now fire on their own.** They were prose reasoning from a number nobody
  had measured; they are now thresholds with instruments attached and today's values on the
  record beside them.

**Harder**

- **The cheap partition is gone at the low end.** Bucketing by sport alone is a quarter of
  the rows, where sport-and-shard would have been less. This is affordable because rejection
  is 18.5 ns a row and four fifths of a search is the eight terms — but it is a real margin
  spent, and the cell partition is the thing that buys it back.
- **A geo-cell scheme has to be chosen when trigger 4 fires** — cell size against the 50 km
  maximum radius and ADR-0099's ×2.0 rung, which together can make a box 200 km across. That
  is a decision deferred, not avoided, and [#173](https://github.com/Raketa02/Raketa/issues/173)
  inherits the shape of it.
- **Instrumenting from build one is work that buys nothing today** — the duty cycle is 0.07
  and will stay there for a long time. It is taken on the argument that the alternative is
  discovering both numbers during the incident that made somebody look.
- **`--preload` is now a footgun with a warning rather than a fix.** The honest position is
  that the object representation does not share, and the packed one does; anybody reaching
  for `--preload` to solve memory should find that sentence.

**Neutral**

- **§9.2's shard conjunct is discarded; the rest of §9.2 transfers.** So does §7.2, minus
  `shard_key` and with `area_cell` demoted to a derived bucket key. §17's *"shard by
  `shard_key` and route on it at the backend"* ceiling is replaced by the two triggers.
- **ADR-0093 is extended, not superseded.** Its decision, its split and its storage table
  stand; triggers 1 and 4 carry an amendment marker pointing here, so a reader cannot take a
  stale number as current.
- The **derived-not-declared** shape is the same one
  [ADR-0100](0100-challenge-window-derived-never-chosen.md) took for the challenge window, and
  for a related reason: a value a human declares is free to contradict the thing it is
  supposed to describe.

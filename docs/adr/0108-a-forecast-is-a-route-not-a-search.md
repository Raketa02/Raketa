# ADR-0108 — A forecast is a route, not a search

- **Status:** Accepted
- **Date:** 2026-08-26

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** `POST /forecasts` is gone, with the builder and the searches it was bound to (#579), so §1, §3, §4, the per-row `would_be_forecast` and the *Evenest* sort describe nothing that runs. §2's rule stands and the engine is built to it: one function, `v1/group.py`'s `forecast`, produces both the full and the provisional figure, reading an empty seat as if it matched its partner, and the assumption travels inside `Forecast`. A Games card prints its forecast as provisional while a side is short; a booked game's pairing reads the same function.

## Context

§9.9 of `matchmaking-engine.md` ends with a
promise: the group objective and the arrangement *"both live in the matcher and neither is
reimplemented on the client"*.
`the-two-contracts.md` §5 made half of it
enforceable — all three arrangements of the four cross with a forecast each, so *Even it out*
is a **selection** and not a calculation, and there is no arithmetic left for the client to be
tempted by.

The other half has nothing behind it. **The builder lets a player compose a line-up the
engine never scored.** Tap a seat, replace whoever is in it with anybody from the shortlist,
and the four on screen is one of hundreds of combinations, none of them enumerated. The
screen's entire claim is a balance figure that moves when you move somebody — so at that
moment there is a number to produce and no route to produce it from.

The prototype produces it in the browser. `arrangedForecast` and `partialForecast` are fifty
lines of JavaScript computing team strength, the gap, the confidence band and the percentage
— which is precisely the failure [ADR-0015](0015-engines-as-a-pure-versioned-layer.md) and
[ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md) forbid, in TypeScript, on
the screen the feature is named after.

The same gap swallows the **provisional** forecast. §9.9 asks for a running figure while the
court is filling, reading a half-empty side *as if the missing player matched the one already
there*, labelled provisional everywhere it appears, and agreeing **exactly** with the arranged
figure the moment the last seat is taken. That equality is only assertable if one
implementation produces both numbers.

Three ways to close it, and the second is the trap:

- **Re-`POST /lineups`** with the composed set as `locked_seats`. Correct, and it writes a
  durable `search` row per tap. ADR-0104
  made every engine invocation a permanent record and §19's denominator *searches run*; a
  builder session of six edits would enter that denominator as six searches. This is the same
  reasoning that made `POST /searches` deliberately non-idempotent — two taps are two searches
  because they are two searches — and it cuts the other way here: six swaps are **not** six
  searches, and recording them as such would put a lie in the one table the product uses to
  judge itself.
- **The client computes it.** The forbidden one.
- **A route that is not a search.**

## Decision

**We will add a fifth public route, `POST /api/v1/forecasts`, which returns the three
arrangements of a given line-up with a forecast each, and records nothing.**

### 1. It is not a search, and that is a fact about it rather than a convenience

No candidates are generated. Nothing is ranked, scored against the floor, withheld or
explained. There is no shortlist, no `search_id`, no *Why 78?* and no Origin key. ADR-0104's
rule binds **searches**, and calling this one to avoid a fifth route would corrupt the record
it was written to protect.

### 2. It answers the provisional forecast too

Seats may be empty. A side with one player is read as if the missing seat matched the one
already there, and the result carries `provisional: true` with its `assumption` code, inside
the `Forecast` type `the-two-contracts.md` §5
already defines — *inside*, because a sibling boolean is how the number and its caveat get
separated in a refactor.

One implementation now produces both figures, so §9.9's equality is a **property test** over
one function rather than a hope about two: fill the last seat and the provisional figure and
the arranged figure are the same number.

This also rescues the ***Evenest*** sort with more than one seat open. §8.2 gives each
shortlist row a `would_be_forecast` only when `open_seats == 1`; the prototype falls back to a
client-side proxy — how close a candidate sits to the average level already seated — which is
the arithmetic this record removes. Instead the engine returns a **provisional**
`would_be_forecast` per row whenever any seat is filled on both sides. It costs one cheap
forecast per row, it keeps a control the prototype ships, and the number it sorts by is
labelled provisional exactly as the header and the seat lines already are.

### 3. It is bound to a search the caller ran

The request cites a `search_id`, and every player id in the line-up must have appeared in that
search's returned rows. Required and non-nullable, the same discipline
`the-two-contracts.md` §7 applies to interest and
for the same reason: a fact with no origin is a fact nobody can audit.

Unbounded, this route is a level-and-band lookup for any player in the city, reachable by id.
The privacy line is spent everywhere else in this design; leaving one route that answers *how
good is this stranger* for arbitrary input would be where it leaks.

### 4. It re-verifies the fail-closed gates, and it stamps its versions

A player can hold a shortlist for an hour and then ask for a forecast naming somebody who
blocked them ten minutes ago.
[ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) says the block
reaches **every surface that shows one player to another**, and a screen predicting your
evening with a named person is such a surface. Blocks and holds are re-read live; a failure
refuses the whole forecast, because a gate that cannot be evaluated excludes.

The result carries `ruleset_version` and `engine_version`. A forecast with no stamp is a
number nobody can reproduce, which is the defect ADR-0104 exists to prevent — arriving through
the one route with no record to reproduce it from.

## Consequences

**§9.9's sentence becomes true rather than aspirational.** There is now no forecast the client
could be tempted to compute, because there is a route for every one of them — full, partial,
per-candidate and per-arrangement. The client's whole job is selection and rendering, and a
reviewer can check that by looking for arithmetic rather than by reading intent.

**The builder is chattier.** Every seat change is a round trip where the prototype was
instant, and a poor connection will show it. The honest mitigations are ordinary interface
work — the previous figure stays on screen while the next is in flight, and the three
arrangements of a *complete* line-up arrive together so swapping sides needs no call at all.
What is not available is computing it locally "just for responsiveness", which is the same
decision under a nicer name.

**A route exists that produces a number and records nothing,** in a system whose central
argument is that every number is checkable. The defence is that a forecast is checkable by
**recomputation** — same inputs, same ruleset, same answer, guaranteed by
[ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md) — while a *search* is
not, because its inputs include an index that has moved. That asymmetry is the whole reason
ADR-0104 exists, and it is why this route may be exempt from it. If a forecast ever becomes
non-deterministic, it becomes a search.

**It is a small oracle even bounded.** Cite a search you ran and you may ask about any four of
its rows — which is, by construction, four people the engine already decided to show you, with
levels and bands the cards already print. It reveals nothing the shortlist did not. The bound
is doing real work only against ids that were never returned, and that is the case it refuses.

**One more route the map did not have when it started counting.** With `POST /passes` and
`GET /interest`, the four routes of `the-two-contracts.md` are seven. That file's §1 stands as
written for the four that create searches; the additions are recorded in
`the-play-screens.md`, which is where the screens
that need them are specified.

# ADR-0093 — The matcher is a backend module with a pure Match Fit engine, not a fourth deployable

- **Status:** Accepted
- **Date:** 2026-08-26

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The searches, the deck, the candidate index and the "who fits whom" ranking are gone (#579, #580), and with them everything this record put in the stateful half: the index, the exposure, suppression and interest ledgers, the sweeper and the search telemetry — so the storage table, the per-result version stamps and the four triggers describe a scoring loop that no longer runs. The split stands. `app/engines/matchfit/` is still a pure engine, now the balance forecast and group availability, fenced from RacketSkill both ways; `app/modules/matchmaking/` is its stateful neighbour, holding the level window, geography and the account gates. One ruleset is released, `2026.09.15-a`, embedded and never chosen by the environment. When the ranking went, its other sections were cut from that ruleset in place rather than released under a new name — the one exception to *immutable once released*, taken because no number the new games read moved (#580).

## Context

The matchmaking engine answers *who sits down*: given a player, a sport and a moment, it
returns a ranked shortlist, a seated line-up with a forecast, or a one-at-a-time deck. Today
the backend ends at onboarding and nothing ranks anybody. Everything about the engine is being
decided on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155);
this record settles the first question on it, because nearly every operational question waits
on the answer.

The input document (`docs/specs/matchmaking/matchmaking-engine.md` *(removed)* §4)
recommends **a separate, independently deployable service written in Go at `matcher/`**,
reachable from the backend over internal HTTP, and argues explicitly past two accepted ADRs to
get there. The document is input material, not accepted design; both arguments deserve an
answer on their merits.

**ADR-0005 — three-app monorepo, ownership boundaries.** A Go service is a fourth deployable
and a second backend language: another CI lane, another deploy pipeline, another on-call
idiom, a fourth ownership fence for the `PreToolUse` hook, and a `matcher/.claude/`. For one
developer driving agents, all of that cost lands on day one.

**ADR-0015 — engines are a pure layer, *not* a microservice.** ADR-0015 rejected an engine
microservice for a precise reason: *"A pure function behind a network call has no state to own
and no independent lifecycle, so the hop buys no isolation that an import rule does not
already give."* The document's counter is that **the matcher is not a pure function** — it
owns a candidate index, an interest ledger, an exposure ledger, a suppression ledger and
outcome telemetry, and its weights are hypotheses that change often, so it has an independent
release cadence.

**That counter is correct, and it argues for something other than what the document
concludes.** It establishes that the matcher's stateful half does not belong in the engines
layer. It does not establish that it belongs in a separate deployable. The rest of the case
was measured against the repository as it actually stands:

- **CPU.** The document itself sizes one search at **under 1 ms** and the load at **1–20
  searches per second** (§17) — roughly two percent of one core at peak. The load the
  separation is meant to isolate does not exist.
- **Release cadence — the strongest argument, and it is symmetric.** §11 dissolves it itself:
  rulesets are *versioned configuration, hot-reloaded from a config store*. There is no config
  store in this repository and none in either plan, so today a weight change is a deploy in
  both worlds; on the day one exists, a Python module re-reads a versioned ruleset exactly as
  well as a Go binary does. The cadence argument distinguishes *how numbers are stored and
  cited*, not *where the program runs*.
- **State.** Real but modest: a rebuildable read model plus TTL-shaped ledgers. `redis` is
  already a backend dependency and already runs beside the API locally; ADR-0092's
  `PeriodicJob` is already the mechanism the sweeper's loops want.
- **Persistence idiom.** The document warns that forcing the matcher into the backend's
  event-sourced idiom would be *"dressing a projection as a domain."* The warning is right and
  survives this decision — and the backend already has a module that is not event-sourced
  (`modules/auth`), so honouring it costs no new precedent.
- **The document's own fallback loses nothing:** *"Every algorithm, term, gate and constant in
  §9 transfers unchanged; only §15 and §16 are discarded."*

The alternatives considered:

- **A Go service at `matcher/`,** as §4 recommends. Buys process isolation and independent
  scaling, neither of which has a workload to justify it, at the cost of a second language a
  one-person team pays for permanently.
- **Deferring the decision to §22's Phase 1.** The document offers this and it is honest —
  the design is portable on this axis. Rejected because eleven of the map's remaining tickets
  sit behind this answer: deferring the decision defers the map.
- **A Python module in the backend with the whole matcher inside it,** scorer included.
  Rejected: it is the case ADR-0015 exists to prevent, and it would make Ania's 78
  irreproducible the first time a term read a clock.
- **A Python module in the backend, with the scorer split out into the pure engines layer.**

## Decision

We will build the matcher **inside the backend, in Python**, split across the fence that
already exists:

- **The pure scoring core is an engine:** `backend/app/engines/matchfit/`, under ADR-0015's
  rules unchanged — no clock, no randomness, no hidden state, one `Protocol`, a version is a
  directory, constants frozen and travelling with the version.
- **The stateful half is a module:** `backend/app/modules/matchmaking/` — the candidate index,
  the ledgers, the ingest projections, the sweeper and the search-side telemetry. It is a
  bounded context in the ordinary sense and consumes the engine through its `Protocol`.
- **No fourth deployable and no second backend language.** ADR-0005 is untouched; the
  ownership hook, the per-app `.claude/` directories and the CI lanes stay exactly as they
  are.

**ADR-0015 is distinguished, not amended.** Its rejection of an engine microservice stands
verbatim, because we are not building one. The document's observation that the matcher owns
state is accepted in full and answered by the split above: the state was never engine
material, and the part that *is* an engine is as pure as RacketSkill. Nothing in ADR-0015
needs a sentence added, and the next reader who reaches its microservice paragraph should find
this record rather than re-open it.

**Storage is chosen by what it costs to lose,** and no part of the matcher is event-sourced:

| What | Where | Why |
| --- | --- | --- |
| The candidate index — the matcher's picture of the city | The backend's database, as a projection rebuilt by replaying the events the owning contexts already record | **The matcher owns no truth.** If it and the backend ever disagree, the backend is right and the matcher is rebuilt |
| The exposure and suppression ledgers | Redis, TTL-native | Cheap to lose; losing a week's "who was shown to whom" costs nobody a fact |
| **Interest** — *"Ania said yes to Kuba"* | Durable storage in the module | The only thing in the matcher a human would miss. A person reached out to another person; losing it silently is a product failure, not a cache miss |

Interest is durable but **not** an aggregate with a life story: it is a small fact with an
expiry date, and it does not get an event stream.

**Every result carries two version stamps, and they mean different things:**

- **The engine version** changes when the *maths* changes — a term computed differently. A
  version is a directory that lives forever (ADR-0015).
- **The ruleset version** changes when the *numbers* change — a weight, a cap, a tolerance. A
  ruleset is a named, dated, frozen dataset (`2026.08.26-a`), **immutable once released**: a
  new set is a new name, never an edit to an old one. It ships embedded with the code today,
  so releasing one is a deploy; the runtime store of §11 is deferred until there is enough real
  traffic for an experiment to mean anything, and its arrival changes only where the file is
  read from, never what the stamp guarantees.

**A ruleset is never selected by the environment.** `local`, `development`, `staging` and
`production` run the same numbers unless somebody deliberately releases a different named
ruleset. A weight is not a setting — it is the product's opinion about who a player should
meet, which is behaviour a domain test can observe, and ADR-0028's rule applies to it without
exception. A malformed ruleset refuses to load and the previous one keeps serving (§11); it
never falls back to defaults, because a matcher that silently falls back is one that quietly
A/B tests against itself.

**Purity is enforced mechanically, exactly as it is today.** `backend/.importlinter`'s
`engines-are-pure` contract covers `app.engines` as a whole, so `matchfit` inherits the fence —
no module, no framework, no I/O library, no ambience, no `datetime` — with the AST purity
tests of ADR-0022 beside it. Match Fit is also **the second engine**, which is the case
`.importlinter`'s own comment says to write the engine-to-engine fence for: two `forbidden`
contracts and not one, so RacketSkill and Match Fit cannot import each other and develop two
opinions about a level.

**The name *Match Fit* is taken back.** An engine of that name was removed in the 2026-08-25
reset; its code is gone, the number gap records it, and inventing a synonym to avoid a ghost
would cost the correct domain term permanently.

**The trigger that makes the other choice right.** Any one of these, *observed and not
predicted*, is grounds to revisit — and this decision is deliberately cheap to reverse,
because ADR-0015 already notes that a pure function behind a `Protocol` is the easiest thing
in a codebase to lift into a service:

1. **Request latency measurably contends with scoring** — sign-in or profile requests degrade
   when a city is busy, traced to the scoring loop sharing the process.
   *(Amended by ADR-0101: stated as
   p99 of one scoring call > 20 ms, or duty cycle > 0.25, on one worker over fifteen
   minutes — measured, and instrumented from the first build.)*
2. **Scoring capacity and request capacity visibly diverge** — one needs scaling and the other
   does not.
3. **The deploy becomes the bottleneck on learning** — the runtime ruleset store exists, real
   outcome data exists, and weight releases are frequent enough that shipping them beside
   authentication code is costing experiments.
4. **The index no longer fits comfortably in memory beside the API** — §7.2 sizes a
   50 000-player city at 32 MB; several cities at gigabyte scale expires the "it is just a
   function call" argument.
   *(Amended by ADR-0101: §7.2's
   32 MB is wrong by an order of magnitude — measured, 782 bytes a row, held once per
   worker. Restated as `bytes_per_row × rows × workers × 2` exceeding half the container's
   memory limit, which a 1 GB container reaches at ~32 000 players on four workers, not at
   "several cities".)*
   *(Amended again by ADR-0112:
   the `× 2` was budgeting a duplicate of every row during a refresh that no longer
   duplicates any of them — a delta refresh copies row **references** from the container it
   replaces. The trigger is `bytes_per_row × rows × workers`, which the same 1 GB container
   reaches at roughly **64 000 players** on four workers.)*
   *(Corrected by [#276](https://github.com/Raketa02/Raketa/issues/276): the 782 both
   amendments divide by was measured against the row §7.2 **specified** — two `int` bitmasks,
   scalar area columns, epoch ints — and never against `CandidateRow`, which holds tuples of
   strings, a tuple of `IndexedArea` and four `datetime` objects. Measured against the type
   that ships, a row is **1 991 bytes**, and the same 1 GB container reaches the trigger at
   roughly **25 000 players** on four workers. The order-of-magnitude point stands and gets
   larger; what changed is that the figure is now a measurement of the thing it is quoted
   about.)*

None of the four can fire this year, which is the point of naming them.

## Consequences

**Easier**

- One language, one CI lane, one deploy path, one set of ownership fences. Every cost the Go
  plan would have started paying on day one is not paid at all.
- The matcher reaches the same Redis, the same database session and the same `PeriodicJob`
  register the backend already runs, rather than provisioning a second opinion about where
  each lives.
- No network hop between the backend and the matcher, so the failure mode §18 exists for does
  not exist, and a search is a function call with no second contract to version.
- The scoring core is testable with no database, no fixtures and no HTTP, and reproducible
  from its stored inputs plus two version stamps — which is what makes the replay harness and
  the falsification programme possible at all.

**Harder**

- **A runaway scoring loop shares a process with sign-in.** In-process isolation is weaker
  than a network boundary, and trigger 1 above exists precisely because this is the failure
  we are accepting.
- **Scaling scoring means scaling whole API instances.** Fine at 1–20 searches per second;
  the day it is not, that is trigger 2.
- **A weight release is a deploy** until the runtime ruleset store is built. That is a real
  cost to the experiment loop, taken knowingly because there is no traffic to experiment on
  yet.
- **Two version stamps on every result** is more ceremony than one, and both have to be
  threaded through the response contract and the telemetry or the explainability promise is
  decorative.
- **Python is the wrong shape for a tight numeric loop.** The margin is enormous today; it is
  not infinite, and the profile that closes it is trigger 1.
- **A second engine means the engine-to-engine fence must actually be written**, and a
  wildcard contract matching nothing is reported `KEPT` — so it needs a probe driven through
  it, per `scripts/test-purity-gates.sh`.

**Neutral**

- §15 (the service) and §16 (the internal contract) of the input document are **discarded**.
  Every algorithm, term, gate and constant in §9 transfers unchanged, as the document says.
- The matcher's transport question does not disappear, it moves: the backend still needs an
  internal boundary between `modules/matchmaking/` and the rest, and that boundary is an
  import rule rather than mTLS.
- `matcher/` is not created, so no fourth entry is added to the ownership hook. The hook's
  existing `frontend_club/` arm remains the template for the day a genuinely new app lands.

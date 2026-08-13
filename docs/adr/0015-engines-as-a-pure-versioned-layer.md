# ADR-0015 — Engines are a pure, versioned layer, not bounded contexts

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Most of what makes Rakieta a product rather than a booking form is computation, not CRUD.
The player app is specified around a skill-rating engine, a Match Fit score, a balance
forecast and a replacement cascade; the club console around an availability oracle, a hold
ladder, a fill-probability model and a twelve-stage eligibility pipeline. The first of
these — RacketSkill Fusion v3 — is being built now, and the shape chosen for it is the
shape the others will inherit.

Three properties make these different from ordinary domain services:

- **Several are read by more than one context.** Match Fit is consumed by matches, by
  the club's formation engine, and by the player app's Find ranking. An availability
  answer is consumed by the grid, by the booking flow, and by the Intent Pool.
- **Their constants are admitted hypotheses.** Every launch constant ships with the
  measurement that would falsify it, so ratings must be attributable to the exact engine
  build that produced them, forever.
- **They must be reproducible.** A scenario replayed at a fixed clock must produce the
  same world; a demo is not a slot machine.

The failure this is guarding against is named in both source documents, and one of them
records having lived through it: an early build recomputed a club's fill model on the
player side, and the cross-application test suite caught the two apps disagreeing about
whether the same court was held. Two implementations of one question is stated as *"the
failure from which no amount of good design recovers."*

The alternatives considered:

- **Engine math inside the owning module's `domain/`,** as ordinary DDD domain logic.
  Correct for exactly one engine. It breaks on the second engine that two contexts need:
  either one module imports another module's `domain/` — the coupling vertical slices
  exist to prevent — or the formula is written twice.
- **An engine microservice.** A pure function behind a network call has no state to own
  and no independent lifecycle, so the hop buys no isolation that an import rule does not
  already give, while adding latency, a second contract to version, and a new failure
  mode. See [ADR-0016](0016-modular-monolith-two-api-surfaces.md).
- **A dedicated pure layer** beside `modules/`, with mechanically enforced import rules.

## Decision

We will keep engines in a top-level `backend/app/engines/` layer that is **not** a bounded
context and owns no state.

- **Import rules, enforced by `import-linter` in CI.** `engines/` may import `shared/` and
  nothing else — never `modules/`, never FastAPI, SQLAlchemy or any I/O library.
  `modules/` may import `engines/` freely.
- **One `Protocol` per engine** in `engines/contracts.py`. `modules/` depends on the
  Protocol, never on a concrete engine, so swapping a version or an implementation is a
  wiring change at the FastAPI boundary like any other port.
- **A version is a directory.** `engines/racketskill/v3/` is the v3 engine, permanently.
  Shipped versions are never deleted, which is also what makes a historical assessment
  interpretable: the question definitions *are* the code that asked them.
- **Constants travel with the version** as a frozen dataclass, and every engine output
  carries the engine version that produced it.
- **`core/` holds what outlives a version.** The scale, the bands, `SIGMA_MAX`, the
  confidence transform and the σ-combination rule live in `engines/racketskill/core/`, so
  onboarding and later match updates cannot develop two ideas of what σ means.

Three purity rules bind every engine, from the first one:

1. **No clock.** `now` is an explicit field on the input.
2. **No randomness.** Where an engine genuinely needs it, it is a PRNG seeded from stable
   identifiers passed in — never `random`, never `uuid4`.
3. **No hidden state.** An engine is a function of its input; conversational engines take
   the whole accumulated transcript rather than holding a session.

Tests are split by what a constant retune should do to them: invariants that must survive
one, golden personas that are meant to break on one, and property tests holding the bounds.

## Consequences

**Easier**

- One implementation of each question, enforced by a linter rather than by vigilance.
- A rating is reproducible from its stored inputs and its engine version, which is what
  makes the falsification programme possible at all.
- Engines are testable with no database, no fixtures and no HTTP — the cheapest and
  fastest tests in the codebase.
- Extraction stays open. A pure function behind a Protocol is the easiest thing in a
  codebase to lift into a service, and the likely first case — ML inference on different
  hardware — is a second implementation of an existing Protocol, not a refactor.

**Harder**

- **A layer that is not a bounded context is unusual,** and a reader who knows DDD will
  reasonably ask why the fusion is not in `rating/domain/`. That is what this record is for.
- Engines cannot read configuration, feature flags or the database. Anything an engine
  needs must be assembled by the calling module and passed in, which makes some call sites
  wordier than a direct lookup would be.
- Never deleting a shipped engine version means the tree accumulates code nothing runs.
  That is the price of interpreting old assessments, and it is paid on purpose.
- `import-linter` is one more CI gate to keep green, and a boundary nothing checks is a
  boundary that is already broken — so it must not be allowed to rot.

**Neutral**

- The registry every engine reads — sports, ids, clock types — sits in `shared/` as a
  shared kernel. That is a deliberate exception to context autonomy, justified by the
  registry being tiny, closed and required to be identical everywhere.
- Engines emit no events and perform no side effects. The calling module decides what a
  result means and what to record about it.

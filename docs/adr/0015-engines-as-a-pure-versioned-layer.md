# ADR-0015 — Engines as a pure, versioned layer

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Rakieta is specified around **engines** — the rating engine first, then Match Fit, the
balance forecast, fill probability, the hold ladder, the Intent Pool's eligibility
pipeline. These are pure computation over domain inputs. The shape chosen for the first one
is the shape the rest inherit, and getting it wrong is invisible until two screens quote
different numbers for the same thing.

Two forces pull on where this computation lives:

- It must not become a bounded context. An engine owns no aggregate and no stream; it is a
  function from a transcript (or match, or line-up) to a result. Modelling it as a module
  would give it a database it must not have.
- It must be **reproducible and falsifiable**. Every constant in the rating engine is a
  hypothesis with a documented measurement that would refute it. That is only possible if a
  result can be recomputed from stored inputs against a named engine version — which forbids
  a clock, randomness or hidden state inside the engine.

We ruled out putting the engine inside the rating module (couples the arithmetic to
SQLAlchemy and makes it untestable without I/O) and behind an interface with no enforced
purity (nothing stops the next engine reaching for `datetime.now()` and silently becoming
irreproducible).

## Decision

We will add a **new top-level layer** `backend/app/engines/`, and a dependency-free
**shared kernel** `backend/app/kernel/`, with the boundary enforced by `import-linter` in CI
rather than by discipline.

- **Engines import only the shared kernel** (and the standard library). They never import a
  module (`app.modules.*`), FastAPI, SQLAlchemy, Pydantic or any I/O library. Modules import
  engines freely — the fence is one-directional.
- **One `Protocol` per engine.** A module depends on the abstraction (e.g. an
  `AssessmentEngine`), never on a concrete implementation, so a version swap — or a future
  ML-inference implementation behind HTTP — is a wiring change at the FastAPI boundary.
- **A version is a directory**, and a shipped version is never deleted. A version's question
  definitions *are* the code that asked them, which is what keeps historical assessments
  interpretable without a `question_definition` table.
- **Three purity rules bind every engine:** no clock (`now` is an input), no randomness (a
  PRNG seeded from stable identifiers if ever needed), no hidden state (a conversational
  engine takes the whole accumulated transcript).
- **What outlives a version lives in the shared kernel** — the scale, the bands, the σ
  ceiling, the confidence transform and the σ-combination rule — so onboarding and the later
  match-update engine cannot develop two definitions of uncertainty.

The `.importlinter` config carries two `forbidden` contracts: engines may not import a
module, framework or I/O library; the kernel may not import anything in the app or any
framework or I/O library. CI runs `lint-imports`; a broken contract fails the build.

## Consequences

**Easier**
- Engines are pure functions: their tests are fast, need no database, and reproduce exactly.
- A constant can be falsified against the ratings it generated, because results carry their
  engine version and inputs are stored rather than derived.
- The boundary holds in six months because a linter checks it, not a reviewer's memory.

**Harder**
- A value shared between an engine and a module has exactly one correct home — the kernel —
  and putting it anywhere else is now a CI failure, not a judgement call. That is the point,
  but it removes the easy shortcut of importing across the fence.
- `import-linter` is another gate to keep green, and its `include_external_packages` mode
  makes it sensitive to how third-party imports are written.

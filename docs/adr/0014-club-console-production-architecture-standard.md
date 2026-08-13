# ADR-0014 — The club console follows its production architecture standard; ADR-0009 narrows to the player app

- **Status:** Accepted
- **Date:** 2026-08-12

## Context

[ADR-0009](0009-feature-first-clean-architecture-frontends.md) mandated one uniform layer
set (`domain/ use-cases/ mappers/ …`) on **both** frontends, applied to every feature. Its
strongest argument was transfer: a rule learned in one client would hold in the other,
halving the instruction surface across two stacks.

Since then the club app acquired a canonical architecture standard —
[`frontend_club/docs/architecture/production-architecture.md`](../../frontend_club/docs/architecture/production-architecture.md),
55 sections covering runtime model, BFF, auth, tenancy, Query, state, errors, testing,
security and operations. That standard **explicitly rejects** the uniform layer set for a
frontend:

- §3.8 — "do not introduce repositories, use-case classes … merely to imitate backend
  Clean Architecture"
- §44 — "avoid empty layers that only forward arguments one-to-one"

The club app is a Next.js App Router application with a server-only BFF. Its real
architectural boundaries are *server vs browser* and *route handler vs feature*, not
`domain/` vs `use-cases/`. ADR-0009's escape hatch anticipated hollow layers and asked for
honesty about them; in this app they are hollow by construction, not occasionally.

This contradiction has been live and undeclared: `frontend_club/CLAUDE.md` announced the
standard had superseded ADR-0009 while ADR-0009, the root `CLAUDE.md` and `CONTEXT-MAP.md`
still asserted the uniform shape. Three instruction files disagreed, and an agent reading
them picks one arbitrarily.

The player app is a different case. It is React Native talking to FastAPI directly, with
no server tier, and its `domain/` + `use-cases/` layers carry real booking and session
rules. ADR-0009 fits it.

## Decision

- The **club app follows its production architecture standard.** Where the standard and
  ADR-0009 disagree, the standard wins for `frontend_club/`.
- **ADR-0009 is narrowed to `frontend_player/`.** It remains Accepted and in force there.
- The club app's layer set is: `model/` (query keys, options, hooks, feature types),
  `server/` (server-only operations and the FastAPI adapter), `api/` (browser → BFF calls
  and the BFF-facing contract), `schemas/`, `state/`, `ui/`, `test/`, `index.ts`.
  `domain/`, `use-cases/` and `mappers/` do not exist there.
- **We drop the claim that the two clients share a shape.** Root `CLAUDE.md` and
  `CONTEXT-MAP.md` are corrected accordingly.

ADRs that remain in force for the club app and agree with the standard:
[0005](0005-three-app-monorepo-ownership-boundaries.md),
[0006](0006-backend-owns-api-contract.md),
[0007](0007-club-web-bff-httponly-cookie-session.md),
[0011](0011-club-console-design-system.md).

## Consequences

**Easier**
- One authority per client. An agent in `frontend_club/` reads the standard; an agent in
  `frontend_player/` reads ADR-0009. Neither has to reconcile a contradiction at runtime.
- The club app stops creating layers that forward arguments unchanged, which were the
  layers most likely to be filled with invented invariants.
- The standard already answers questions ADR-0009 never addressed for a server-rendered
  app: BFF boundaries, request-local Query clients, tenant-scoped cache keys.

**Harder**
- **The transfer argument is gone.** This is the real cost: two clients now need two sets
  of instructions, and a convention learned in one is no longer evidence about the other.
  Every rule must state which app it governs.
- `frontend_club/eslint.config.mjs` still enforces the ADR-0009 layers — it exempts `api/`
  and `mappers/` for generated imports and treats `domain/`/`use-cases/` as pure. Those
  folders no longer exist, so **the club app's import boundaries are currently
  documentation, not enforcement.** Rewriting that config is the immediate follow-up.
- Reviewers must hold two mental models.

**Neutral**
- The backend's module layering ([ADR-0001](0001-clean-hexagonal-architecture.md)) is
  unaffected. The repo now answers "where does this code go?" in three ways rather than
  two, which is honest about three genuinely different runtimes.

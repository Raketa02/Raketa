# ADR-0001 — Clean / hexagonal architecture on the backend

- **Status:** Accepted
- **Date:** 2026-08-09 *(captured retroactively from the existing implementation)*

## Context

The backend is expected to grow a large number of features (clubs, courts, bookings,
matches, payments, notifications) over a long lifetime, developed substantially by AI
agents working from a fresh context each session. Two failure modes dominate at that
scale:

1. **Framework leakage** — business rules written inside FastAPI route handlers or
   SQLAlchemy models. The rules become untestable without HTTP and a database, and
   unmovable when the framework changes.
2. **Horizontal layering** — organising by technical type (`models/`, `services/`,
   `routers/`) so that one feature is smeared across the whole tree. An agent then has
   to hold the entire codebase in context to change one behavior.

## Decision

We will structure the backend as **vertical slices with inward-pointing dependencies**.

- Each bounded context is a module at `app/modules/<context>/`, split into four layers:
  `domain/`, `application/`, `infrastructure/`, `presentation/`.
- `domain/` is **pure Python** — no FastAPI, SQLAlchemy, Pydantic, or external SDK.
- `application/` holds use cases that depend on **`Protocol` ports**, injected by
  constructor, never on concrete adapters.
- `infrastructure/` implements those ports.
- Adapters are bound to ports **only** at the FastAPI boundary, in
  `app/api/dependencies.py`, via `Annotated[Port, Depends(factory)]`.
- Feature-specific ports live in the module's `domain/ports.py`; cross-cutting ports
  (unit of work, event store, publisher) live in `app/application/ports/`.

## Consequences

**Easier**
- Domain rules are testable with no HTTP server and no database — the fastest and most
  numerous tests exercise the part most likely to be wrong.
- A feature change is localised to one module, so an agent needs a small context window
  to work correctly.
- Swapping an adapter (a repository, a hasher, a third-party client) touches one file
  and no business logic.

**Harder**
- More indirection and more files than putting the query in the route handler. For a
  genuinely trivial CRUD endpoint this is real overhead.
- Requires discipline about which layer a piece of code belongs to; the boundary between
  "domain rule" and "application orchestration" needs judgment.
- Value objects must validate themselves, which means the same concept is expressed once
  in the domain and once in a Pydantic schema at the boundary.

**Neutral**
- The frontends adopt the *same shape* for the same reasons
  ([ADR-0009](0009-feature-first-clean-architecture-frontends.md)), so the rule transfers
  across the repo even though no code does.

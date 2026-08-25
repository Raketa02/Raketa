# ADR-0009 — Feature-first Clean Architecture on both frontends

- **Status:** Accepted, **narrowed to `frontend_player/` by
  **ADR-0014** *(removed)***
- **Date:** 2026-08-09

> **Scope note.** This ADR governs **`frontend_player/` only.** The club app follows its
> own production architecture standard, which rejects the uniform layer set for a
> frontend. Read every "both frontends" below as "the player app". In particular, the
> claim under *Consequences → Easier* that a rule transfers between the two clients no
> longer holds.

> **Note — the 2026-08-25 reset.** It cites **ADR-0014** (the club console's architecture standard), removed in the 2026-08-25 reset. This ADR now governs the only client there is, `frontend_player/`. See the [ADR index](README.md#the-2026-08-25-reset--why-the-sequence-has-gaps). This ADR's body is left as written: an accepted ADR is immutable, and the reason a past decision looked right is itself information.

## Context

Both frontends are expected to grow a large, evolving feature set, developed largely by
AI agents from a fresh context. The default layouts the ecosystem hands you do not
survive that:

- `create-next-app` and `create-expo-app` produce a flat route tree with components and
  fetching wherever they land. That is fine for ten screens and unnavigable at a hundred.
- Grouping by technical type (`components/`, `hooks/`, `services/`) smears one feature
  across the whole tree, so changing one behavior requires holding the whole app in
  context.
- Letting business rules live in components makes them untestable without a renderer,
  which is exactly where they stop being tested.

There is also a specific hazard for generated code: raw wire types are convenient and
spread fast. Once a `components/` file imports a generated response type, the backend's
serialization shape has reached the UI, and the two are welded together.

## Decision

Both frontends will use **feature-first Clean Architecture**, with the **same layer set**
in both, applied **uniformly** to every feature.

Each feature is a vertical slice under `src/features/<name>/`:

```
domain/       entities, value objects, rules. Pure TS — no React/RN/Next/fetch.
use-cases/    one function per workflow; orchestrates domain + ports.
api/          talks to the network (BFF in club, FastAPI in player). Wire types.
mappers/      pure wire DTO <-> domain object. THE wire boundary.
schemas/      Zod schemas for forms and any external input.
components/   rendering and interaction only.
hooks/        thin adapters over use-cases; TanStack Query lives here.
types.ts      the feature's public surface.
```

- **Dependencies point inward:** `app/ → hooks/ → use-cases/ → domain/`.
- **Generated wire types may only be imported in `api/` and `mappers/`.** ESLint's
  `no-restricted-imports` enforces this in both apps, with those two layers exempted.
- **`domain/` and `use-cases/` are pure** — ESLint blocks React, Next, React Native and
  Expo imports there.
- **Every feature carries the full layer set**, so an agent applies one rule rather than
  judging per feature. `src/features/_template/` is the canonical copy-me folder.
- **Uniform-strict escape hatch:** where a feature genuinely has no business rule, its
  `use-cases/` may be thin pass-throughs and `domain/` may be just types. Keep the
  folders for predictability — but **do not invent fake invariants to fill them**.
- The two apps share this **shape**, not code ([ADR-0005](0005-three-app-monorepo-ownership-boundaries.md)).

## Consequences

**Easier**
- A feature is one directory. An agent can change it correctly with a small context.
- The most valuable tests — `domain/`, `use-cases/`, `mappers/` — are pure and need no
  DOM or renderer, so they are fast and get written.
- A backend response shape change breaks in exactly one layer per feature.
- A rule learned in the club app transfers to the player app, halving the instruction
  surface across two stacks.

**Harder**
- More ceremony than the framework defaults, and noticeably more for a simple screen:
  seven folders to render a list.
- The escape hatch requires honesty. The failure mode is an agent inventing a hollow
  `domain/` object to make a folder look inhabited, which is worse than an empty one.
- Neither generator can be used as intended; both apps start from the structure instead,
  which is more upfront work.
- ESLint boundary rules must be maintained as layers move.

**Neutral**
- The structure mirrors the backend's module layering
  ([ADR-0001](0001-clean-hexagonal-architecture.md)), so the whole repo answers "where
  does this code go?" the same way in three stacks.

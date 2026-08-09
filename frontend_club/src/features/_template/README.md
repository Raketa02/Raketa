# `_template` — the shape every feature must have

Copy this folder to `src/features/<feature>/` when you start a feature. **Every**
feature carries the full layer set, so an agent applies one rule instead of judgment
(see [ADR-0009](../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md)).

| Layer | Holds | May import | Must never import |
| --- | --- | --- | --- |
| `domain/` | Entities, value objects, invariants. Pure TypeScript. | nothing outside `domain/` | React, Next, `fetch`, `@/generated` |
| `use-cases/` | One function per workflow. Orchestrates `domain/` + the `api/` port. | `domain/`, `api/` types | React, Next, `@/generated` |
| `api/` | Calls the **BFF** (`/api/*`). Speaks wire types. | `@/generated`, `@/shared/lib/http` | `components/`, `hooks/` |
| `mappers/` | Pure `wire DTO ⇄ domain object` functions. **The wire boundary.** | `@/generated`, `domain/` | React, Next |
| `schemas/` | Zod schemas for forms and any external input. | `zod`, `domain/` | React, Next |
| `components/` | Rendering and interaction only. | `hooks/`, `@/shared/ui`, `domain/` types | `api/`, `@/generated` |
| `hooks/` | Thin adapters over use-cases. TanStack Query lives here. | `use-cases/`, `@tanstack/react-query` | `@/generated` |
| `types.ts` | The feature's public surface. | — | — |

## Non-negotiables

- **Dependencies point inward.** `app/ → hooks/ → use-cases/ → domain/`. Nothing in
  `domain/` knows the app exists.
- **`@/generated` may only be read in `api/` and `mappers/`.** The ESLint config
  enforces this; the hooks do too. Raw wire types never reach a component.
- **Never hand-write a type that mirrors a backend response.** Run `pnpm gen:api`.
- **Business rules live in `domain/` + `use-cases/`,** never in a component or hook.

## The honest escape hatch

If a feature genuinely has no business rule, its `use-cases/` may be thin
pass-throughs and `domain/` may be just types. Keep the folders — but **do not invent
fake invariants to fill them**.

## Tests

Colocate as `*.test.ts(x)` next to the file under test. `domain/`, `use-cases/` and
`mappers/` need no DOM. End-to-end specs go in `../../../e2e/`.

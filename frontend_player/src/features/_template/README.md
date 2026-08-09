# `_template` — the shape every feature must have

Copy this folder to `src/features/<feature>/` when you start a feature. **Every**
feature carries the full layer set, so an agent applies one rule instead of judgment
(see [ADR-0009](../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md)).

This mirrors `frontend_club`'s structure on purpose: the two client apps are separate
deployables that share no code, but they share a *shape*, so a rule you learn in one
transfers to the other.

| Layer | Holds | May import | Must never import |
| --- | --- | --- | --- |
| `domain/` | Entities, value objects, invariants. Pure TypeScript. | nothing outside `domain/` | React, React Native, Expo, `fetch`, `@/generated` |
| `use-cases/` | One function per workflow. Orchestrates `domain/` + the `api/` port. | `domain/`, `api/` types | React Native, Expo, `@/generated` |
| `api/` | Calls **FastAPI directly** over HTTPS. Speaks wire types. | `@/generated`, `@/shared/lib/http` | `components/`, `hooks/` |
| `mappers/` | Pure `wire DTO ⇄ domain object` functions. **The wire boundary.** | `@/generated`, `domain/` | React Native |
| `schemas/` | Zod schemas for forms and any external input. | `zod`, `domain/` | React Native |
| `components/` | Rendering and interaction only. | `hooks/`, `@/shared/ui`, `domain/` types | `api/`, `@/generated` |
| `hooks/` | Thin adapters over use-cases. TanStack Query lives here. | `use-cases/`, `@tanstack/react-query` | `@/generated` |
| `types.ts` | The feature's public surface. | — | — |

## Non-negotiables

- **Dependencies point inward.** `app/ → hooks/ → use-cases/ → domain/`.
- **`@/generated` may only be read in `api/` and `mappers/`.** ESLint enforces it.
- **Never hand-write a type that mirrors a backend response.** Run `pnpm gen:api`.
- **Business rules live in `domain/` + `use-cases/`,** never in a screen or hook.
- **Tokens live only in `expo-secure-store`,** accessed through `@/shared/lib/auth`.
  A feature never touches the keychain directly.

## Where this differs from the club app

There is **no BFF**. A native app has no cookie jar, so `api/` calls FastAPI directly
and attaches `Authorization: Bearer` from the OS keychain
([ADR-0008](../../../../docs/adr/0008-player-mobile-securestore-direct-api.md)).
Everything above the `api/` layer is identical in shape to the club app.

## Tests

Colocate as `*.test.ts(x)` next to the file under test. `domain/`, `use-cases/` and
`mappers/` are pure and need no renderer — test those first and hardest.

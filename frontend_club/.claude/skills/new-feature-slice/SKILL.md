---
name: new-feature-slice
description: Build a new feature in the club app as a vertical slice from UI down to FastAPI. Use when adding a feature, screen or major capability under src/features/ in frontend_club.
---

# A new feature slice

The standard's §47 Phase 7: build **vertically**, not layer by layer. Each feature walks the
whole path once. That is what stops every new feature inventing its own architecture.

```
page/UI → query → browser client → BFF route handler → feature server adapter → FastAPI
          → tests → telemetry
```

## The folders

```
src/features/<feature>/
  api/       browser → BFF calls + the BFF-facing contract
  model/     query keys, query options, hooks, feature types
  schemas/   Zod — forms, search params, inputs
  state/     feature-local Zustand — only if justified
  ui/        rendering and interaction
  server/    server-only operations + the FastAPI adapter
  test/
  index.ts   the explicit public API — the ONLY import surface
```

Do **not** create `domain/`, `use-cases/` or `mappers/`. Those belong to the player app
([ADR-0014](../../../../docs/adr/0014-club-console-production-architecture-standard.md)).
Do not create a folder you have nothing to put in — §44 rejects layers that forward
arguments one-to-one.

## Order of work

1. **Name it in the glossary's vocabulary** ([`../CONTEXT.md`](../../../../CONTEXT.md)). If
   the concept isn't there, that is a signal — resolve it before the name hardens.
2. **Decide who owns each value** before writing code. Walk the state-ownership table in
   `CLAUDE.md`. Two owners for one value is the bug you are trying not to write.
3. **`schemas/`** — the Zod schema for the feature's inputs and search params.
4. **`server/`** — the server-only FastAPI adapter. Generated wire types stop here.
5. **`app/api/…/route.ts`** — the BFF endpoint. Follow the handler sequence in the `bff`
   rule; it loads when you open that file.
6. **`api/` + `model/`** — the browser client and the typed query-key factory. Every input
   that changes the response goes in the key, **including `clubId`**.
7. **`ui/`** — composed from `shared/ui/` primitives. No literal values.
8. **`index.ts`** — export the smallest surface that works. No root mega-barrel.
9. **Tests** at the cheapest layer that gives confidence, plus the BFF integration
   assertions for anything authenticated or tenant-scoped.

## Before you call it done

Walk §46 Definition of Done — not just the happy path. Every server-driven surface models
loading, empty, error and permission-denied states. Run `pnpm check`.

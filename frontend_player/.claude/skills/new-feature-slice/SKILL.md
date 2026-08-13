---
name: new-feature-slice
description: Build a new feature in the player app as a full Clean Architecture slice. Use when adding a feature, screen or major capability under src/features/ in frontend_player.
---

# A new feature slice

Copy [`src/features/_template/`](../../../src/features/_template/README.md). Every feature
carries the full layer set, so an agent applies one rule rather than judging per feature
([ADR-0009](../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md)).

```
domain/       entities, value objects, rules. Pure TS — no RN, Expo, fetch or generated/.
use-cases/    one function per workflow; orchestrates domain + ports.
api/          calls FastAPI; speaks wire types.
mappers/      pure wire DTO <-> domain object. THE wire boundary.
schemas/      Zod — forms, deep links, push payloads, any external input.
components/   rendering and interaction only.
hooks/        thin adapters over use-cases; TanStack Query + the key factory.
store/        OPTIONAL — a small feature-scoped Zustand store, only with a reason.
types.ts      the feature's public surface.
```

## Order of work

1. **Name it in the glossary's vocabulary** ([`../CONTEXT.md`](../../../../CONTEXT.md)). If
   the concept isn't there, that is a signal — resolve it before the name hardens. A `Court`
   is a `Court`, not a Venue.
2. **`domain/` first**, and test it first. These are the tests that stay valuable: pure, fast,
   no renderer.
3. **`mappers/`** — the wire boundary. Generated types stop here and in `api/`.
4. **`use-cases/`** — one function per workflow. If the feature genuinely has no business
   rule, thin pass-throughs are honest; **do not invent fake invariants to fill the folder.**
5. **`hooks/`** — the query-key factory and semantic hooks (`useMatch(id)`), not query options
   assembled per screen.
6. **`components/`** — read the design system's Appendix B before writing one. Every value
   comes from `theme.ts`.
7. **`types.ts`** — the only surface another feature may import.

## Before you call it done

- Every server-driven screen models initial loading · loaded · empty · refreshing ·
  recoverable error · terminal error · offline.
- Critical mutations have decided their duplicate-submit behaviour.
- Walk the Definition of Done in
  [`docs/architecture.md` Part 20](../../../docs/architecture.md#part-20--definition-of-done-and-the-pr-checklist).
- Run `pnpm check`. If the change is visual, say so and ask for a look — you cannot see the
  screen.

# `_template` — the shape every feature must have

Copy this folder to `src/features/<feature>/` when you start a feature. **Every**
feature carries the full layer set, so an agent applies one rule instead of judgment
(see [ADR-0009](../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md)).

This mirrors the structure the club console used before the 2026-08-25 reset removed it —
kept on purpose, because client apps in this repo are separate
deployables that share no code, but they share a _shape_, so a rule you learn in one
transfers to the other.

| Layer                 | Holds                                                                                         | May import                                      | Must never import                                                    |
| --------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------- |
| `domain/`             | Entities, value objects, invariants. Pure TypeScript.                                         | nothing outside `domain/`                       | React, React Native, Expo, TanStack, Zustand, `fetch`, `@/generated` |
| `use-cases/`          | One function per workflow. Orchestrates `domain/` + the `api/` port.                          | `domain/`, `api/` types                         | React Native, Expo, `@/generated`                                    |
| `api/`                | Calls **FastAPI directly** through `@/shared/lib/http`. Speaks wire types.                    | `@/generated`, `@/shared/lib/http`              | `components/`, `hooks/`, `fetch`                                     |
| `mappers/`            | Pure `wire DTO ⇄ domain object` functions. **The wire boundary.**                             | `@/generated`, `domain/`                        | React Native                                                         |
| `schemas/`            | Zod schemas for forms, route params, deep links, any external input.                          | `zod`, `domain/`                                | React Native                                                         |
| `components/`         | Rendering and interaction only.                                                               | `hooks/`, `@/shared/ui`, `domain/` types        | `api/`, `@/generated`                                                |
| `hooks/`              | Thin adapters over use-cases. TanStack Query + the **query-key factory**.                     | `use-cases/`, `store/`, `@tanstack/react-query` | `@/generated`                                                        |
| `store/` _(optional)_ | A small feature-scoped Zustand store, when the feature needs one.                             | `zod`, plain types                              | server data, tokens, `api/`                                          |
| `types.ts`            | **The feature's only public surface.** Re-exports what other features and `src/app/` may use. | —                                               | —                                                                    |

`store/` is the one **optional** layer — present when the feature has UI state that
outlives a component, absent otherwise. Everything else is always there, even when thin.

## Non-negotiables

- **Dependencies point inward.** `app/ → components/ → hooks/ → use-cases/ → domain/`.
- **`@/generated` may only be read in `api/` and `mappers/`.** ESLint enforces it.
- **Never hand-write a type that mirrors a backend response.** Run `pnpm gen:api`.
- **Business rules live in `domain/` + `use-cases/`,** never in a screen, a hook, or a
  `disabled={…}` expression. `canJoinMatch(match, player)` is testable; the JSX is not.
- **Tokens live only in `expo-secure-store`,** accessed through `@/shared/lib/auth`.
  A feature never touches the keychain directly.
- **`fetch` is never called here.** `api/` goes through `@/shared/lib/http`, which owns
  the auth header, timeouts, cancellation, error normalization and the 401 refresh.
- **Import your own layers relatively** (`../domain/Match`); import another feature only
  through its `types.ts`. ESLint blocks `@/features/<other>/<layer>/…` outright.
- **Server data never enters `store/`.** TanStack Query owns everything from the backend.

## Anything in `components/` obeys the design system

**The visual language is locked and predates the app.** A feature does not get to invent
one. Before writing the first component, read — in this order:

1. **[`docs/design-system.md` Appendix B](../../../docs/design-system.md#appendix-b--quick-reference-card)**
   — the quick-reference card. ~20 lines, and it is the minimum. Read it every time.
2. **[`docs/design-system.md` Part 0](../../../docs/design-system.md#part-0--reading-a-web-prototype-as-a-native-app)**
   — why the prototype's phone frame, dark stage and scenario rail are **harness that does
   not ship**, and how a web stylesheet translates to React Native. Read it once.
3. **[`@/shared/ui/README.md`](../../shared/ui/README.md)** — how to consume the theme, and
   the four React Native traps (Android ignores `fontWeight`; tracking and line height are
   points; 44 × 44pt targets; there is no hover).
4. The Part covering the surface you are building — Part 5 primitives, 6 controls,
   7 data display, 9 overlays, 12 screens.

Then:

- **Every value comes from [`@/shared/ui/theme.ts`](../../shared/ui/theme.ts).** A literal
  `'#E8482B'`, `fontSize: 12` or `padding: 10` in a component is a bug, not a shortcut.
  ESLint rejects hex and `rgb()`/`rgba()` literals and the `fontWeight` property outright.
- **Colour is chosen by meaning, not appearance** — coral is the one accent, mint is
  settled, amber is reversible, red is ended badly, info explains rather than states.
- **A value that genuinely does not exist** is a change to `theme.ts` **and** to
  `docs/design-system.md`, in the same commit — not a literal, and not a near-miss token.
- **Reuse before you build.** The match card, state card, level bar and popover are shared
  primitives from the start; the prototype kept second copies and they drifted.

## Two things a feature must define, not inherit

**A query-key factory,** in `hooks/`, listing every key the feature uses — with _every_
parameter that changes the response, including the cursor:

```ts
export const matchKeys = {
  all: ['matches'] as const,
  lists: () => [...matchKeys.all, 'list'] as const,
  list: (f: MatchFilters) => [...matchKeys.lists(), f] as const,
  detail: (id: string) => [...matchKeys.all, 'detail', id] as const,
};
```

**A cache effect per mutation** — prefer writing the canonical response with
`setQueryData`, then invalidating the broader lists. And a retry/idempotency decision:
a mutation is only retried when the endpoint is idempotent, accepts an idempotency key,
or is explicitly safe to repeat.

## Where this differs from a web client

There is **no BFF**. A native app has no cookie jar, so `api/` calls FastAPI directly
and attaches `Authorization: Bearer` from the OS keychain
([ADR-0008](../../../../docs/adr/0008-player-mobile-securestore-direct-api.md)).
Everything above the `api/` layer is shape a web client would share.

## Tests

Colocate as `*.test.ts(x)` next to the file under test. `domain/`, `use-cases/`,
`mappers/`, `schemas/` and the key factory are pure and need no renderer — test those
first and hardest. Component tests assert what the user can observe, never internal
state. Router tests live **outside** `src/app/`.

## Before calling the feature done

Walk the Definition of Done in
[`docs/architecture.md` Part 20](../../../docs/architecture.md#part-20--definition-of-done-and-the-pr-checklist).
The short version: states designed (loading / empty / error / offline), errors mapped to
codes, invalidations defined, deep-link params validated, duplicate-submit decided,
accessible, tested on both platforms.

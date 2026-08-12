# `_template` — the shape every feature has

Copy this folder to `src/features/<feature>/` when you start a feature. A feature is the
**unit of change and ownership**: it should be understandable, and removable, mostly
within this one boundary.

The contract is [`docs/architecture/production-architecture.md`](../../../docs/architecture/production-architecture.md)
§5 and Appendix B; section refs below point there.

> **This replaced the ADR-0009 layer set.** `domain/`, `use-cases/` and `mappers/` are
> gone — the standard rejects imitating backend Clean Architecture on a frontend (§3.8)
> and forbids layers that forward arguments one-to-one (§44). `frontend_player/` still
> uses the old set; do not copy its shape here. See [`../../../CLAUDE.md`](../../../CLAUDE.md).

| Layer | Holds | May import | Must never import |
| --- | --- | --- | --- |
| `api/` | Browser → BFF calls, and the BFF-facing request/response + error contract. | `@/platform/api`, `schemas/` | `@/generated`, `ui/`, anything server-only |
| `model/` | Query key factory, query option factories, hooks, feature types. TanStack Query lives here. | `api/`, `schemas/`, `@tanstack/react-query` | `@/generated`, `server/` |
| `schemas/` | Zod schemas — forms, search params, any input crossing a trust boundary. | `zod` | React, Next |
| `state/` | Feature-local Zustand. **Only if a real need exists** — see below. | `zustand` | `api/`, `model/`, route components |
| `ui/` | Rendering and interaction. Feature composites built from `@/shared/ui` primitives. **[Read `ui/README.md`](ui/README.md) — the design system is locked.** | `model/`, `state/`, `schemas/`, `@/shared/ui` | `api/`, `server/`, `@/generated` |
| `server/` | Server-only operations + this feature's FastAPI adapter. **`server-only`.** | `@/generated`, `@/platform/server` | anything under `ui/`, `model/`, `state/` |
| `test/` | Feature tests that do not colocate. | — | — |
| `index.ts` | The feature's **public API** — the only surface other modules may import. | — | — |

## Non-negotiables

- **Other modules import only `index.ts`.** A deep import (`features/bookings/model/foo`)
  is forbidden, and so is a circular dependency between features. Keep the surface small
  and intentional — no root mega-barrel. *(§5.2, §6.1)*
- **`server/` cannot reach the client bundle.** Anything that can read a token, a secret
  or the FastAPI base URL is `server-only`. *(§5.1, §19.1)*
- **`@/generated` stays at the transport boundary** — `server/`, and the contract adapter
  in `api/`. Generated `paths` and response types never reach `ui/`. *(§16.2)*
- **Never hand-write a type that mirrors a backend response.** Run `pnpm gen:api`.
- **The BFF contract is yours, not FastAPI's.** `api/` may drop fields, reduce payloads
  and normalize errors. Re-exposing every backend DTO unchanged erases the point of the
  BFF. *(§16.3)*
- **Tenant identity is part of every tenant-scoped query key** —
  `['clubs', clubId, 'bookings', filters]`, never `['bookings']`. *(§11.2)*
- **Business rules are FastAPI's.** Mirror one in the frontend only for UX, and only while
  it is clearly non-authoritative. *(§3.2)*

## The design system is locked — and it applies to this feature

Anything you render conforms to the club console's visual contract. It was designed and
audited before the app existed, and **you are assembling from it, not designing**:

| Artefact | Is |
| --- | --- |
| [`docs/design-system.md`](../../../docs/design-system.md) | The rules — 14 parts, ~1150 lines. Read it in one pass. |
| [`src/shared/ui/tokens.css`](../../shared/ui/tokens.css) | Every value. Components use `var(--…)`; **a literal is a bug.** |
| [`ui/README.md`](ui/README.md) | The short version, colocated with your components. |

Before building a container, check the **five that already exist** — card, stat tile,
note, row list, action row. Before picking a colour, ask **which state it is** — coral =
live, mint = settled, amber = provisional, red = failed — never which looks best.
Styling is **CSS Modules colocated with the component**. *(ADR-0011, §39)*

## Two layers that are conditional, not mandatory

This is the standard's biggest departure from the old template: **empty layers are not
kept for symmetry.**

- **`state/` only if the state is genuinely transient, client-only and shared by distant
  components.** If it came from FastAPI it belongs to Query; if refresh or a shared link
  should preserve it, it belongs in the URL; if one screen owns it, it is React state.
  *(§13.1, §13.2, §49)*
- **A server-only *operation* only when orchestration is real** — combining endpoints,
  permission-dependent adaptation, multi-step commands, response composition. A trivial
  read goes `route.ts → api adapter → platform client` with nothing in between. *(§44)*

Delete a folder you do not need. Do **not** invent work to fill one.

## Tests *(§29)*

Colocate as `*.test.ts(x)` beside the file, or put them in `test/`. E2E specs go in
`../../../e2e/`.

Highest value here: the **query key factory**, Zod schemas and normalization, search-param
parsing, error normalization, and DTO→UI mapping — all pure, all fast, none needing a DOM.
Component tests assert user-observable behavior, not that a component calls a hook.

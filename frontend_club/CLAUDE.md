# Raketa Club Web App

Next.js 15 (App Router) + React 19 + TypeScript. The web app clubs use to manage courts,
availability, pricing and bookings. A feature-oriented modular frontend with a thin App
Router composition layer and a **server-only BFF**: the browser calls same-origin `/api/*`
route handlers, and those call FastAPI. pnpm.

> The `frontend_club/` app of a three-app monorepo — see the root
> [`CLAUDE.md`](../CLAUDE.md). Run every command from this directory. Never import from
> `../backend/` or `../frontend_player/`; a hook blocks writes there. Shared docs:
> [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

## The architecture standard is the law

[`docs/architecture/production-architecture.md`](docs/architecture/production-architecture.md)
is the **canonical architecture for this app** — 55 sections covering runtime model, BFF,
auth, tenancy, Query, state, Zod, OpenAPI, errors, testing, security, observability and
operations.

**This file is the operational digest.** When the two disagree, the standard wins. When
you need detail this file omits — retry policy, cache-invalidation contracts, refresh
concurrency, Playwright fixtures — open the standard at the cited section (`§8.5`, `§27.4`,
`§9.5`, `§29.7`) rather than inventing an answer.

Its §2 normative language: **MUST** is an invariant that needs an ADR to break. **SHOULD**
is the default; deviate only with a concrete reason. **MAY** is optional.

The standard governs this app, not the player app
([ADR-0014](../docs/adr/0014-club-console-production-architecture-standard.md)).
ADR-0009's uniform layer set does **not** apply here — `domain/`, `use-cases/` and
`mappers/` do not exist. A rule learned in `frontend_player/` does not transfer.

## Not scaffolded yet

This directory holds architecture, config and rules — not a running app. `pnpm install`
has not been run and there is no `src/app/layout.tsx`. If you are the first session here,
read [`README.md`](README.md) and build in the standard's **§47 order**. Do not reach for
`create-next-app`; its flat layout contradicts the structure below. The design system is
already locked — the first `app/layout.tsx` must `import '@/shared/ui/tokens.css'` and load
Archivo + IBM Plex Mono through `next/font/google` as `--font-sans` / `--font-mono`.

Outstanding gaps you must not assume are already handled — including the ESLint config
still enforcing the old layer set — are in [`docs/known-gaps.md`](docs/known-gaps.md).

## Commands

```bash
pnpm dev          # Next dev server
pnpm build        # production build
pnpm lint         # ESLint — also enforces the import boundaries below
pnpm typecheck    # tsc --noEmit (strict)
pnpm test         # Vitest (unit + component)     pnpm test:e2e → Playwright
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.club.json
pnpm check        # lint + typecheck + test — the local gate
```

Regenerate the API client whenever the backend contract changes, and **commit the result**.

## Safety — never without an explicit request

- **Let browser code call FastAPI directly.** Client Components call the BFF in
  `src/app/api/*` only. The browser must never learn the FastAPI origin. *(§4.1)*
- **Expose auth tokens to the browser.** Access/refresh JWTs live in httpOnly cookies set
  by the BFF — never in `localStorage`, Zustand, TanStack Query, React Context, a
  JS-readable cookie, or a Client Component prop. *(§9.1)*
- **Rename `BACKEND_API_URL` to `NEXT_PUBLIC_*`.** Anything `NEXT_PUBLIC_` is baked into
  the client bundle. *(§20.1)*
- **Build a catch-all proxy** — `/api/proxy?url=…`, `/api/backend/[...path]`. Generic
  forwarding is an SSRF hole. *(§8.2)*
- **Import `src/generated/` outside the transport boundary.** Generated wire types stay in
  `platform/server/`, a feature's `server/`, or a feature's `api/` contract adapter. Never
  in `ui/`. *(§16.2)*
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put a literal colour, font size, gap or radius in a component.** Every value comes from
  `src/shared/ui/tokens.css` as `var(--…)`.
- **Add a dependency that owns styling** — Tailwind, styled-components, Emotion, a
  component library. *(ADR-0011)*
- **Introduce Server Actions for domain mutations.** BFF route handlers are the declared
  mutation transport; a second one splits auth, errors, tests and observability. Needs an
  ADR. *(§7.3)*
- **Create or edit a real `.env*` file, or run a deploy (`vercel`).** *(hook-enforced)*

## Architecture

```
src/
  app/                     App Router — composition and routing ONLY (§3.5)
    (public)/ (authenticated)/
    api/                   BFF route handlers — deliberate endpoints (§8)
  features/<feature>/      the unit of change and ownership
    api/       browser → BFF calls + the BFF-facing contract
    model/     query keys, query options, hooks, feature types
    schemas/   Zod — forms, search params, inputs
    state/     feature-local Zustand — only if justified
    ui/        rendering and interaction
    server/    server-only operations + the FastAPI adapter
    test/      index.ts ← the explicit public API, the only import surface
  platform/                application-wide infrastructure
    api/ server/ query/ config/ observability/ security/
  shared/                  generic capability that knows no feature
    ui/ (tokens.css lives here)  lib/ hooks/ types/ test/
  generated/               openapi-typescript output — never hand-edited
e2e/                       Playwright specs
```

### Dependency rules *(§6)*

```
app        → features · platform · shared
features   → platform public APIs · shared · another feature ONLY via its index.ts
platform   → shared
shared     → nothing from any feature
generated  → consumed at the server/transport boundary, never by UI
```

**MUST NOT:** import `src/app` from a feature · import feature code into `shared` · import
server-only code into a Client Component · deep-import another feature's internals
(`features/x/model/foo`) · create a circular feature dependency.

Cross-feature workflows compose at the route level, in a dedicated workflow module, or as a
genuinely shared capability — never by letting features reach into each other. *(§5.3)*

### The canonical flow

```
Client Component → TanStack Query → /api BFF route handler → FastAPI
Server Component → server-only feature adapter → FastAPI      (never self-fetch /api)
```

Build every feature vertically along that path. That is what stops each new feature
inventing its own architecture. *(§47 Phase 7)*

## One owner for every piece of state *(§3.1, §49)*

Two owners for one value is the bug.

| The value | Owner |
| --- | --- |
| Came from FastAPI and can go stale | **TanStack Query** |
| Server-rendered, never independently refetched | **Server Component** |
| Should survive refresh / back / share | **URL** search params |
| Only this component's interaction | React `useState` / `useReducer` |
| Transient UI shared by distant components | **Zustand** |
| A form value | form/component state + Zod at the boundary |
| A token or credential | **httpOnly cookie, BFF only** |
| An authoritative business rule | **FastAPI** |

Never: Query data copied into Zustand · URL filters mirrored into a store · server request
state re-implemented as `isLoading/isError/data` · tokens anywhere JavaScript can read.

**FastAPI stays authoritative** for permissions, tenant membership, booking eligibility,
pricing, cancellation rules, state transitions, capacity, payment state, conflicts and
idempotency. The frontend may mirror a rule for UX only. *(§3.2)*

## Multi-tenancy is an invariant, not a UI filter *(§11)*

Every tenant-scoped query key **MUST** carry the club identity —
`['clubs', clubId, 'bookings', filters]`, never `['bookings']`. Tenant-specific Zustand
state includes tenant identity or resets when the club changes. **Key scoping is not
authorization:** FastAPI verifies the principal against the target club, and a `clubId`
from the browser is never trusted.

## Code style

- **TypeScript strict**, near-zero `any` in feature code. `unknown` at untrusted
  boundaries; `as` is not an error-suppression tool; prefer `satisfies`. *(§17.2–17.4)*
- Model state machines as **discriminated unions**, not several booleans that permit
  impossible combinations, and make critical status switches **exhaustive** so a new
  backend state fails the compile. *(§17.5, §17.6)*
- Name by domain meaning: `BookingTable`, `cancelBooking` — never `DataComponent`,
  `Helper2`. New domain concepts use the shared glossary's vocabulary
  ([`../CONTEXT.md`](../CONTEXT.md)). A `Court` is a `Court`, not a Venue.
- A helper reaches `shared/lib` only when it is genuinely domain-independent. A booking
  calculation stays in the booking feature even if two screens use it. *(§17.8)*
- `useEffect` synchronizes with external systems — not deriving values, not copying props
  to state, not routine fetching. *(§23.3)*

## Git & PRs

Conventional Commits scoped `club`: `feat(club): court availability calendar`. Run
`pnpm check` before pushing; CI runs lint, typecheck, test and build for `frontend_club/**`
changes. For a substantial PR, walk the standard's **§51 review questions** — what owns
this state, where is authorization enforced, what is the timeout, what invalidates the
cache, can this run correctly on ten instances.

Club-app technical vocabulary: [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term
locally.

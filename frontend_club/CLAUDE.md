# Rakieta Club Web App

Next.js (App Router) + React + TypeScript. The web app clubs use to manage courts,
availability, pricing and bookings. Feature-first **Clean Architecture**, fully
decoupled from the backend: it talks to FastAPI only over HTTP, generates its wire types
from `backend/openapi.json`, and maps them into its own objects. pnpm.

> **Monorepo note.** This is the `frontend_club/` app of a three-app monorepo (see the
> root [`CLAUDE.md`](../CLAUDE.md) and [`../CONTEXT-MAP.md`](../CONTEXT-MAP.md)).
> Everything here scopes to `frontend_club/` — **run all commands from this directory.**
> The FastAPI backend (`../backend/`) and the Expo player app (`../frontend_player/`)
> have their own `CLAUDE.md`; **never apply their rules here, and never import their
> source.** A `PreToolUse` hook blocks writes outside `frontend_club/` from this session.
> Shared docs live at the root: [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

## Not scaffolded yet

This directory currently holds architecture, config and rules — not a running app.
`pnpm install` has not been run and there is no `src/app/layout.tsx` yet. If you are the
first session here, read [`README.md`](README.md) for the bootstrap sequence, and build
outward from the structure rather than reaching for `create-next-app` (its flat layout
contradicts [ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)).

The **design system is already locked** — `src/shared/ui/tokens.css` exists and predates
the app. The first `app/layout.tsx` must `import '@/shared/ui/tokens.css'` and load
Archivo + IBM Plex Mono through `next/font/google` as `--font-sans` / `--font-mono`. See
[Design system](#design-system).

## Default workflow

For non-trivial changes:
1. Explore the relevant files; state current behavior and constraints.
2. Propose a minimal plan before editing. For changes touching >5 files, confirm first.
3. Write or update tests first when behavior changes (see Testing).
4. Make the smallest safe change.
5. Run the most focused relevant tests first, then `pnpm test` when practical.
6. Run `pnpm lint && pnpm typecheck` before finishing if code changed.
7. Summarize changed files, checks run, and remaining risks.

Do not claim a task is done unless the relevant tests/checks ran — or plainly state why.

## Safety — never do these without an explicit request

- **Let browser code call FastAPI directly.** Client Components call the **BFF** route
  handlers in `src/app/api/*` only; the BFF (server-side) calls FastAPI.
- **Expose auth tokens to the browser.** Access/refresh JWTs live in httpOnly + Secure +
  SameSite cookies set by the BFF. Never in `localStorage`, a JS-readable cookie, or a
  Client Component prop.
- **Rename `BACKEND_API_URL` to `NEXT_PUBLIC_*`.** Anything `NEXT_PUBLIC_` ships to the
  browser. The FastAPI origin is server-only.
- **Import from `src/generated/` outside a feature's `api/` or `mappers/` layer.**
  Generated wire types are raw transport.
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put business rules in components or hooks.** Rules live in `domain/` + `use-cases/`.
- **Write a literal colour, font size, gap or radius in a component.** Every value comes
  from `src/shared/ui/tokens.css` as `var(--…)`. See [Design system](#design-system).
- **Add a dependency that owns styling** — Tailwind, styled-components, Emotion, a
  component library. The design system is CSS custom properties + CSS Modules
  ([ADR-0011](../docs/adr/0011-club-console-design-system.md)).
- **Create or edit a real `.env*` file, or run a deploy (`vercel`).** *(hook-enforced)*

## Commands

```bash
pnpm dev          # Next dev server
pnpm build        # production build
pnpm lint         # ESLint — also enforces the import boundaries below
pnpm typecheck    # tsc --noEmit (strict)
pnpm test         # Vitest (unit + component); pnpm test:watch for the loop
pnpm test:e2e     # Playwright
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.json
pnpm check        # lint + typecheck + test — the local gate
```

Regenerate the API client whenever the backend contract changes, and **commit the
result**. `make gen-api` from the repo root regenerates both clients at once.

## Architecture

Source lives under `src/`. **Every feature carries the full layer set** — the same
discipline the backend uses — so an agent applies one rule instead of judgment:

```
src/
  app/                      Next App Router (thin). Routes compose features.
    (auth)/ (dashboard)/    route groups
    api/                    BFF route handlers (proxy FastAPI, own the httpOnly cookies)
    layout.tsx providers.tsx middleware.ts
  features/<feature>/
    domain/                 entities + value objects + rules (pure TS, no React/fetch)
    use-cases/              one fn per workflow; orchestrates domain + ports
    api/                    calls the BFF; speaks wire types
    mappers/                wire DTO  <->  domain object
    schemas/                Zod schemas (form/input validation)
    components/             rendering + interaction only
    hooks/                  thin adapters over use-cases (TanStack Query lives here)
    types.ts
  shared/
    ui/                     tokens.css (THE source of every value) + primitives
    lib/                    http/ auth/ query-client/
    config/                 env.ts (Zod-validated)
    errors/                 AppError.ts
    store/                  Zustand — cross-cutting UI state only
  generated/                openapi-typescript output — raw wire types ONLY
```

The per-layer contract is in
[`src/features/_template/README.md`](src/features/_template/README.md). Copy that folder
to start a feature.

Rules to preserve:
- **Dependencies point inward:** `app/ → hooks/ → use-cases/ → domain/`. `domain/`
  imports nothing from React, Next, `fetch`, or `generated/`.
- **The wire boundary is `api/` + `mappers/`.** Raw `generated/` types enter there and
  leave as the feature's own DTO/domain objects. Nothing above touches `generated/`.
  ESLint enforces this.
- **Reads vs writes:** Server Components do initial reads server-side (read the session
  cookie → attach `Authorization: Bearer` via `shared/lib/http`). Client interactivity
  uses **TanStack Query** in `hooks/`, hitting the **BFF**, never FastAPI directly.
- **Global state is minimal:** **Zustand** only for cross-cutting UI state (e.g. the
  active club). Server data is never mirrored into a store — TanStack owns it.
- **Auth:** the BFF in `src/app/api/auth/*` proxies login/refresh/logout and manages the
  cookies; `middleware.ts` guards routes by reading the session cookie; a 401 triggers a
  server-side rotate against the backend's `/auth/refresh`.

**Uniform-strict escape hatch:** when a feature genuinely has no business rule, its
`use-cases/` may be thin pass-throughs and `domain/` may be just types. Keep the folders
for predictability, but **do not invent fake invariants to fill them**.

## Design system

**Locked.** The club console's visual language was designed and audited before the app
existed. Full rules: [`docs/design-system.md`](docs/design-system.md). The decision and
its corrections: [ADR-0011](../docs/adr/0011-club-console-design-system.md).

Three artefacts that **change together, in the same commit**:

| File | Is |
| --- | --- |
| [`src/shared/ui/tokens.css`](src/shared/ui/tokens.css) | The source of every value. Imported once, from `app/layout.tsx`. |
| [`docs/design-system.md`](docs/design-system.md) | The rules — meanings, containers, surfaces, copy. |
| [`docs/design-system-v7-prototype-audit.md`](docs/design-system-v7-prototype-audit.md) | Archived measurement of the prototype. Not the rules. |

**Styling is CSS Modules colocated with the component** (`Card.tsx` + `Card.module.css`),
referencing `var(--…)`. No Tailwind, no CSS-in-JS, no runtime-injected CSS.

### The rules an agent gets wrong

- **`--line` bounds a thing; `--line2` separates rows within a thing.** The single most
  common visual error — a card whose internal rows use `--line` reads as five cards.
- **11 between things · 14 inside things · 13 radius on cards.** Everything else follows.
- **Colour is picked by meaning, never appearance.** coral = live · mint = settled ·
  amber = provisional · red = failed. Amber and red are not a severity gradient: amber
  means *the clock may still resolve this*, red means *this failed*.
- **Rule C — white text never sits on `--coral` or `--mint`** (3.89:1 and 4.07:1). Use
  `--coral-ink` / `--mint-ink` / `--mint-deep`. `--ink` is the only dark that may sit on
  coral (4.50:1).
- **`--volt` on dark surfaces only.** On paper it is ~1.3:1.
- **Eleven type sizes exist. A twelfth is a bug** — change the scale deliberately, in
  `tokens.css` and the doc, or use an existing step.
- **Cards cast no shadow.** Only the sheet, drawer, toast and mobile nav do.
- **Every state carries a word**, not just a colour — that is what a tag is for.
- **Every number carries a sentence.** A stat description is not optional; a tile that
  cannot justify itself in one line is a vanity metric.
- **Never remove the global `:focus-visible` outline.**
- Copy follows Part 12: *off sale*, not soft-held. *Booked*, not confirmed. *Unearned*,
  not lost revenue. Polish number formatting — `2 474,25 zł`, `1 h`, `65%`, `09:00`.

Before building a new component, check the **five containers** (card · stat · note · row
list · action row). The system's coherence comes from re-use, not new parts.

The design system covers `frontend_club/` **only**. The player app has its own.

## Testing (TDD — test first)

Mirror the backend: write the failing test first, make it pass, refactor.

- **Vitest + Testing Library** for `domain/`, `use-cases/`, `mappers/`, `hooks/` and
  components. Pure logic needs no DOM — test it without one. Mock ports with
  hand-written stubs.
- **Playwright** for end-to-end slices. The auth slice must assert that tokens are
  **not** readable from `document.cookie`.
- Colocate as `*.test.ts(x)` next to the file under test; E2E specs live in `e2e/`.

## Code style

- **TypeScript strict** (`strict`, `noUncheckedIndexedAccess`, no implicit `any`).
- **ESLint + Prettier**; run `pnpm format` before committing. Prefer named exports.
- **Zod** for all external input (forms, env, anything crossing a boundary). Validate
  and normalize inside the schema, then map to domain — mirroring the backend's
  "validate inside the value object" rule.
- New domain concepts use the **shared glossary's** vocabulary
  ([`../CONTEXT.md`](../CONTEXT.md)). A `Court` is a `Court` — not a Venue or Facility.

## Git & PRs

- Conventional Commits scoped `club`: e.g. `feat(club): court availability calendar`.
- CI runs `lint`, `typecheck`, `test` and `build` for `frontend_club/` when
  `frontend_club/**` changed; all must pass. Run `pnpm check` before pushing.

## Domain language

Shared domain terms: [`../CONTEXT.md`](../CONTEXT.md). Club-app-only technical
vocabulary: [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally.

# Rakieta — Club web app

The web application clubs use to manage their courts, availability, pricing and
bookings. Next.js 15 (App Router) + React 19 + TypeScript, talking to the FastAPI backend
**only over HTTP**, through its own BFF.

One of three independently deployable apps in this monorepo — see the root
[`CONTEXT-MAP.md`](../CONTEXT-MAP.md).

## The architecture standard

[`docs/architecture/production-architecture.md`](docs/architecture/production-architecture.md)
is the canonical architecture for this app: runtime model, project structure, dependency
rules, BFF design, authentication, multi-tenancy, TanStack Query, Zustand, URL state,
Zod, OpenAPI, errors, testing, security, observability, CI and operations.

[`CLAUDE.md`](CLAUDE.md) is the working digest — the decisions already made and the rules
that get broken. Read it first; open the standard when you need the detail behind a rule.

> **It supersedes [ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)
> for this app.** `domain/`, `use-cases/` and `mappers/` are gone; the standard rejects
> imitating backend Clean Architecture on a frontend (§3.8, §44). `frontend_player/` still
> follows ADR-0009, so **the two clients no longer share a shape** — a rule learned there
> does not transfer here. The ADR recording this is still outstanding; see
> [Known gaps](CLAUDE.md#known-gaps).

## Bootstrap (first time)

Nothing is installed yet: this directory holds the architecture, config and rules, not a
generated app. To bring it to life:

```bash
cd frontend_club
pnpm install                 # installs what package.json already declares
```

Then create the App Router entry points Next expects — `src/app/layout.tsx` and
`src/app/page.tsx` — and build the foundations in the standard's **§47 order**:

1. strict compiler, lint/import boundaries, `server-only` enforcement, CI baseline;
2. the OpenAPI contract pipeline, FastAPI client, browser client, error model;
3. auth — login/logout/refresh, cookie policy, session projection, CSRF, CSP;
4. the state platform — QueryClient, query defaults, hydration, key conventions;
5. tests — Vitest, component setup, Playwright fixtures, contract tests;
6. observability — structured logs, tracing, error reporting, Web Vitals;
7. business features, each built vertically through the established path.

`layout.tsx` must `import '@/shared/ui/tokens.css'` and load Archivo + IBM Plex Mono via
`next/font/google`, exposed as `--font-sans` / `--font-mono`. The design system is already
locked — see below.

> Deliberately **not** scaffolded with `create-next-app`: its default flat `app/` layout
> contradicts the feature-oriented structure. Starting from the structure is cheaper than
> unpicking the generator's.

## Commands

```bash
pnpm dev          # dev server on :3000
pnpm build        # production build
pnpm lint         # ESLint (also enforces the import boundaries)
pnpm typecheck    # tsc --noEmit, strict
pnpm test         # Vitest
pnpm test:e2e     # Playwright
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.json
pnpm check        # lint + typecheck + test — the local gate
```

## Environment

Copy `.env.example` → `.env.local`. Everything is read in exactly one place —
[`src/platform/config/`](src/platform/config/) — which validates it with Zod and refuses to
start the server on anything missing or malformed. A lint rule keeps `process.env` out of
the rest of the app.

`APP_ENV` is one of four names, shared with the backend and the player app:

| Environment | Scheme | State |
| --- | --- | --- |
| `local` | `http://` | the only one that runs today |
| `development` | `https://` | defined and validated, **not provisioned** |
| `staging` | `https://` | defined and validated, **not provisioned** |
| `production` | `https://` | does not exist yet |

Selecting an unprovisioned environment is a startup failure, not a silent fallback: the
scheme rule requires `https://` there, and the only reachable backend is an `http://` one.

`APP_ENV` is **not** `NODE_ENV`. That has two values and describes how the app was
*compiled* — one production build serves staging and production alike. Nothing reads it.

Two schemas, never one (§20.1):

- **`server.ts`** — the environment, `BACKEND_API_URL` and the session cookie policy. It
  carries `import "server-only"`, so a Client Component that imports it **fails to
  compile** rather than shipping and reading `undefined`. `BACKEND_API_URL` must never
  become `NEXT_PUBLIC_*`: anything so prefixed is public information baked into the client
  bundle, and the browser must never learn the FastAPI origin ([ADR-0007](../docs/adr/0007-club-web-bff-httponly-cookie-session.md)).
- **`public.ts`** — only `NEXT_PUBLIC_APP_URL`. What is *absent* is the point: no FastAPI
  origin, no environment name, no cookie policy.

The session cookie's `Secure` flag is **derived** from the environment — `false` only in
`local` — and can no longer be set by hand. A stale `SESSION_COOKIE_SECURE` in the
environment stops the server rather than being ignored.

Two things are wired but not yet mounted, because there is no `src/app/layout.tsx` to mount
them in — do this when you scaffold the app:

- `src/instrumentation.ts` already validates the server config at boot. It runs as soon as
  Next has an app to start.
- `<EnvironmentBadge />` from `@/platform/config/EnvironmentBadge` renders the amber
  environment pill. Mount it once in the root layout. It is a **Server Component** on
  purpose: it reads the server-only environment, so no public mirror of the name exists.
  Production is unbadged.

## Architecture in one paragraph

The browser only ever calls this app's own BFF route handlers under `src/app/api/*`;
those run server-side, hold the session in httpOnly cookies, and call FastAPI with an
explicit header allowlist and a finite timeout. Server Components skip the BFF and use a
server-only FastAPI adapter directly. Each business capability is a feature module under
`src/features/<name>/` (`api/ model/ schemas/ state/ ui/ server/ test/` + `index.ts`),
reachable only through its `index.ts`; application-wide infrastructure lives in
`src/platform/`, generic capability in `src/shared/`. State has exactly one owner —
Query for server data, the URL for navigable state, React for local interaction, Zustand
for transient shared UI, httpOnly cookies for tokens, and FastAPI for business truth.

Each directory has a README stating its own contract:
[`src/app/api/`](src/app/api/README.md) · [`src/platform/`](src/platform/README.md) ·
[`src/features/_template/`](src/features/_template/README.md) ·
[`src/shared/`](src/shared/README.md) · [`src/generated/`](src/generated/README.md).

## Design system

The visual language was designed and audited before the app existed, and is **locked**:

- [`docs/design-system.md`](docs/design-system.md) — the rules.
- [`src/shared/ui/tokens.css`](src/shared/ui/tokens.css) — every colour, size, space,
  radius, shadow, duration and z-index. Components reference `var(--…)`; **a literal in a
  component is a bug.**
- [`docs/design-system-v7-prototype-audit.md`](docs/design-system-v7-prototype-audit.md) —
  the archived measurement of the v7 prototype. Descriptive, superseded by the rules.

Styling is **CSS Modules colocated with the component**. No Tailwind, no CSS-in-JS —
[ADR-0011](../docs/adr/0011-club-console-design-system.md). The architecture standard's
§39 agrees with it; nothing about the design system changed.

Full rules: [`CLAUDE.md`](CLAUDE.md). Vocabulary: [`CONTEXT.md`](CONTEXT.md).

# Rakieta — Club web app

The web application clubs use to manage their courts, availability, pricing and
bookings. Next.js (App Router) + React + TypeScript, talking to the FastAPI backend
**only over HTTP**, through its own BFF.

One of three independently deployable apps in this monorepo — see the root
[`CONTEXT-MAP.md`](../CONTEXT-MAP.md).

## Bootstrap (first time)

Nothing is installed yet: this directory holds the architecture, config and rules, not
a generated app. To bring it to life:

```bash
cd frontend_club
pnpm install                 # installs what package.json already declares
```

Then create the App Router entry points that Next expects — `src/app/layout.tsx` and
`src/app/page.tsx` — and build outward from there. Keep the layer rules in
[`CLAUDE.md`](CLAUDE.md); the folder contract is in
[`src/features/_template/README.md`](src/features/_template/README.md).

> Deliberately **not** scaffolded with `create-next-app`: its default flat `app/`
> layout contradicts the feature-first structure recorded in
> [ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md). Starting
> from the structure is cheaper than unpicking the generator's.

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

Copy `.env.example` → `.env.local`. `BACKEND_API_URL` is **server-only** and must never
become `NEXT_PUBLIC_*`.

## Architecture in one paragraph

The browser only ever calls this app's own BFF route handlers under `src/app/api/*`;
those run server-side, hold the session in httpOnly cookies, and proxy FastAPI. Each
user-facing capability is a vertical slice in `src/features/<name>/` with the full
layer set (`domain/ use-cases/ api/ mappers/ schemas/ components/ hooks/`), and
dependencies point inward. Wire types are generated from the backend contract and are
confined to the `api/` and `mappers/` layers.

Full rules: [`CLAUDE.md`](CLAUDE.md). Vocabulary: [`CONTEXT.md`](CONTEXT.md).

# Rakieta Club Web App — Technical Vocabulary

This file holds **club-app-only technical vocabulary**. It does **not** define domain
language — those terms (User, Club, Court, Booking, statuses, events) live once in the
shared glossary [`../CONTEXT.md`](../CONTEXT.md), which all three apps obey. See
[`../CONTEXT-MAP.md`](../CONTEXT-MAP.md) for the topology.

> When you name a frontend architecture concept, use the term as defined here. When you
> name a *domain* concept, use the root glossary. Don't drift to synonyms either avoids.

## Glossary — club-app technical terms

- **Feature** — a vertical slice under `src/features/<name>/` owning a user-facing
  capability, split into the full layer set (`domain/ use-cases/ api/ mappers/
  schemas/ components/ hooks/ types.ts`). _Avoid_: module, page-folder.
- **Wire type** — a raw request/response shape **generated** from the backend's
  `openapi.json` into `src/generated/`. The never-hand-written description of what
  crosses the network. _Avoid_: DTO (a wire type is the *input* to building a DTO).
- **DTO** — the app's **own** transport object, built in a feature's `api/` layer from a
  wire type. Owned here; never imported from `generated/` directly.
- **Domain object** — a feature's entity/value object in `domain/`: the mapped,
  rule-bearing form a use-case and the UI work with. Pure TS, no React/Next/fetch.
- **Mapper** — pure function converting wire DTO ⇄ domain object, in `mappers/`. The
  single place the wire shape is allowed to influence domain shape.
- **Use-case** — one function per workflow in `use-cases/`, orchestrating domain +
  ports. The home of business orchestration. _Avoid_: service, controller.
- **Server Component** — the default; renders on the server, may read the session cookie
  and do initial reads server-side. **Client Component** — `"use client"`; needed for
  interactivity/hooks. Prefer Server Components; reach for Client only when needed.
- **BFF route handler** — an app-owned server endpoint under `src/app/api/*` that proxies
  FastAPI and manages the httpOnly session cookies. The **only** thing the browser calls.
  _Avoid_: proxy, gateway (it is this app's own backend-for-frontend).
- **Session cookie** — the httpOnly/Secure/SameSite cookie(s) holding the access/refresh
  JWTs, set and read only by the BFF and Server Components. Never readable by browser JS.
- **Query / Mutation** — TanStack Query primitives used in `hooks/` for client-side reads
  (including polling via `refetchInterval`) and writes, always against the BFF.
  _Avoid_: calling `fetch` to FastAPI from a component.
- **UI state** — cross-cutting client state (the active club selector, modal open/close)
  held in **Zustand**. Server data is *not* UI state — TanStack owns that.

Add club-app-only technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.

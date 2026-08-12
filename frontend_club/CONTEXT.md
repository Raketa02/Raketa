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

## Glossary — design-system terms

The rules behind these are in [`docs/design-system.md`](docs/design-system.md); the values
are in [`src/shared/ui/tokens.css`](src/shared/ui/tokens.css). Named here so a component,
a review comment and a commit message all use the same word.

- **Token** — a CSS custom property in `tokens.css`, the only legitimate source of a
  colour, type size, spacing step, radius, shadow, duration or z-index. _Avoid_: variable,
  constant (a token is a *design* decision, not just a value).
- **Paper / surface** — `--paper` is the application background; `--surface` is white, and
  everything raised off the paper (cards, nav, table heads, the calendar) sits on it.
- **Line vs line2** — `--line` **bounds a thing** (card edge, table header rule); `--line2`
  **separates rows within a thing** (hairlines, row borders, inert fills). The distinction
  is load-bearing, not stylistic.
- **Soft / ink** — a semantic accent's companions. `-soft` is the tinted background;
  `-ink` is the darkened form that carries text on that soft, and the fill used whenever
  white text sits on top (**Rule C**).
- **Rule C** — white text never sits on `--coral` or `--mint`; it needs `--coral-ink`,
  `--mint-ink` or `--mint-deep`. `--ink` is the only dark permitted on `--coral`.
- **The five containers** — **card**, **stat tile**, **note**, **row list**, **action
  row**. Nearly every screen is built from these; a new container needs justifying.
- **Tag** — a 19px uppercase state chip that always **carries a word**. Never clickable —
  a clickable pill is a **chip**.
- **Eyebrow** — the 9.5px uppercase `--muted` group label above a set. _Avoid_: overline,
  kicker.
- **Hairline** — the 1px `--line2` divider *inside* a card, with 11px margins.
- **Severity rail** — the 4px vertical bar on an action row. The only vertical colour bar
  in the system, which is why it reads as severity.
- **Sheet** — the right-hand detail overlay on a `--paper` background. **Drawer** — the
  narrower `--night-deep` operator overlay. **Toast** — the bottom-centre `--night`
  confirmation carrying one volt-emphasised phrase. Three distinct surfaces; not synonyms.
- **Block** — a booking rendered inside a calendar cell (`inset: 2px`, `pointer-events:
  none`). **Cell** — the 44px grid unit beneath it, which owns the click.
- **Past vs nosell** — *past* is elapsed time; *nosell* is time outside that court's
  opening hours. Both inert; only nosell dims, because it was never inventory.
- **Hatch** — the 45° texture marking blocked/programme time. Texture rather than colour,
  so blocked time leaves the sold/free axis entirely.
- **Hard hold / soft hold** — in the *interface*, a soft hold is drawn with a **dashed**
  edge and a hard hold with a solid fill. In *copy*, both are reported to the club as
  **off sale** — see the design system's Part 12 vocabulary table.

> The demand surfaces (heat map, demand map, match card, timeline) name *interface*
> concepts only. Their domain terms are unmodelled — Bookings, Courts and Matches are
> Part 2 of the shared glossary. Settle those there first, then rename the UI to match.

Add club-app-only technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.

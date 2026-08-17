# Rakieta Club Web App — Technical Vocabulary

This file holds **club-app-only technical vocabulary**. It does **not** define domain
language — those terms (User, Club, Court, Booking, statuses, events) live once in the
shared glossary [`../CONTEXT.md`](../CONTEXT.md), which all three apps obey. See
[`../CONTEXT-MAP.md`](../CONTEXT-MAP.md) for the topology.

> When you name a frontend architecture concept, use the term as defined here. When you
> name a *domain* concept, use the root glossary. Don't drift to synonyms either avoids.

The concepts behind these terms are specified in
[`docs/architecture/production-architecture.md`](docs/architecture/production-architecture.md);
section references point there.

> **Vocabulary change.** *Use-case*, *mapper* and *domain object* are no longer club-app
> terms. They belonged to the ADR-0009 layer set, which the architecture standard
> replaces here (§3.8, §44) — see [`CLAUDE.md`](CLAUDE.md). They are still live terms in
> `frontend_player/`. Do not reintroduce them in this app, and do not assume a sentence
> using them describes club-app code.

## Glossary — structure

- **Feature** — a business capability owning a vertical slice under
  `src/features/<name>/`, split into `api/ model/ schemas/ state/ ui/ server/ test/` plus
  `index.ts`. The unit of change and ownership; it should be understandable and removable
  within one boundary. _Avoid_: module, page-folder. *(§3.4)*
- **Public API** — a feature's `index.ts`: the small, intentional surface other modules
  import. Reaching past it into `features/x/model/foo` is a **deep import** and is
  forbidden. _Avoid_: barrel (a root mega-barrel is the anti-pattern this replaces). *(§5.2)*
- **Platform** — `src/platform/`: application-wide infrastructure owned by no single
  feature — browser client primitives, the server FastAPI client, auth, CSRF, request
  context, query client, config, observability, security. Changes here get architecture
  review because they affect every feature. _Avoid_: core, common, infra. *(§35.2)*
- **Shared** — `src/shared/`: genuinely generic capability that knows no feature — design
  system primitives, pure helpers, generic hooks, types, test utilities. A helper earns a
  place here only when it is domain-independent. *(§17.8)*
- **Model layer** — a feature's `model/`: query keys, query option factories, hooks and
  feature types. Where TanStack Query lives. _Avoid_: store, service.
- **Server layer** — a feature's `server/`: server-only operations and that feature's
  FastAPI adapter. Kept beside its feature for ownership, but mechanically excluded from
  the client bundle. *(§5.1)*
- **`server-only`** — the boundary marking a module as impossible to import into a client
  bundle. Anything that can read a token, a secret or the FastAPI base URL carries it. *(§19.1)*

## Glossary — the network path

- **BFF route handler** — an app-owned server endpoint under `src/app/api/*`. A
  **deliberate** endpoint, not a proxy: it owns origin/CSRF checks, session resolution,
  input validation, the timed FastAPI call, error normalization and response shaping.
  The **only** thing the browser calls. _Avoid_: proxy, gateway. *(§8)*
- **Catch-all proxy** — the banned shape: `/api/proxy?url=…`, `/api/backend/[...path]`.
  Named here so it can be rejected by name in review. *(§8.2)*
- **BFF contract** — the browser-facing request/response shape the BFF defines. It is
  **conceptually distinct from the FastAPI contract** even when a shape passes through
  unchanged: the BFF may combine calls, drop fields, reduce payloads and normalize errors.
  *(§16.3)*
- **Wire type** — a raw request/response shape **generated** from the backend's
  `openapi.json` into `src/generated/`. Never hand-written; confined to the server /
  transport boundary. _Avoid_: DTO. *(§16.2)*
- **FastAPI adapter** — the server-side function that calls one backend endpoint using
  wire types and returns the app's own shape. Lives in a feature's `server/`; the shared
  client primitives live in `platform/server/`. _Avoid_: repository, service. *(§19, §44)*
- **Server-only feature operation** — an orchestration step above the adapter, created
  **only** when there is real work: combining endpoints, permission-dependent adaptation,
  multi-step command preparation, response composition. A layer that forwards arguments
  one-to-one should not exist. *(§44)*
- **Self-fetch** — a Server Component making an HTTP request to this app's own `/api/*`.
  An anti-pattern: server code calls the FastAPI adapter directly. *(§4.2)*
- **Request context** — the per-request bundle carrying correlation/request ID, trace
  context and resolved session, created at the top of a handler and threaded through.
  *(§8.1, §31.1)*
- **Error envelope** — the one stable browser-facing error contract: machine `code`, safe
  `message`, optional `fieldErrors`/`details`, and `requestId`. Clients branch on stable
  codes, never on backend exception strings. *(§18.2)*
- **Error category** — the normalized class a component reasons about: unauthenticated,
  forbidden, validation, conflict, rate limited, not found, transient network, backend
  unavailable, unexpected. A **domain code** (`COURT_ALREADY_BOOKED`) sits beneath one.
  *(§12.13, §22.1)*
- **Idempotency key** — the value representing **one logical user intent**, generated
  before the first attempt and identical across retries of that intent — not per HTTP
  attempt. The only thing that makes retrying a create safe. *(§28.2)*

## Glossary — environment and configuration

- **Environment** — one of exactly four: `local`, `development`, `staging`, `production`.
  The same four names the backend (`APP_ENV`) and the player app (`EXPO_PUBLIC_ENV`) use.
  It answers *which infrastructure is in use*, never *whether a feature is on* — that is a
  feature flag, and the two are never mixed. Only `local` runs today; the other three are
  validated but unprovisioned, so selecting one fails at start rather than falling back.
  _Avoid_: `dev`, `prod`, `stage`, `test`. *(§20.1)*
- **Build mode** — `NODE_ENV`: two values, describing how the app was *compiled*. **Not
  the environment** — one production build serves staging and production alike. Nothing
  reads it to answer an environment question, and a lint rule enforces that. Named here so
  it can be rejected by name in review.
- **Scheme rule** — the contract that a **public-network URL** is `https://` in every
  deployed environment, and either in `local`. A claim about a URL *and* the environment
  together, so it is checked on the object rather than on either field alone — and it stays
  silent when the field itself already refused the value, so one typo yields one complaint.
- **Public-network URL vs server-to-server URL** — which of the two a variable is decides
  whether the scheme rule applies to it. `NEXT_PUBLIC_APP_URL` is the origin a browser
  visits, so `http://` in a deployed environment means a session cookie in the clear: the
  rule applies. `BACKEND_API_URL` is called by this app's own server tier and a browser
  never learns it, so a cluster-internal `http://backend.svc.cluster.local:8000` is
  legitimate and the rule does not apply — whether that hop is encrypted is a
  deployment-topology question this app cannot answer. Settled for all three apps in
  [`../docs/environments.md`](../docs/environments.md).
- **Server configuration** — `src/platform/config/server.ts`: the environment, the FastAPI
  origin and the session cookie policy. Carries `server-only`, so importing it from a
  Client Component is a build error rather than a runtime `undefined`. *(§19.1, §20.1)*
- **Public configuration** — `src/platform/config/public.ts`: only what is deliberately
  baked into the client bundle. What is *absent* is the point — no FastAPI origin, no
  environment, no cookie policy. **Two schemas, never one.** *(§20.1)*
- **Derived setting** — a configuration value computed from the environment rather than set
  independently, because two settable values can disagree. The session cookie's `Secure`
  flag is one: `false` only in `local`. Setting it by hand is refused, not ignored — a
  variable that looks like it controls security and does not is worse than one that is
  absent.
- **Environment badge** — the amber `warn` Tag naming the current environment, rendered by
  a **Server Component** reading the server-only value. Production is unbadged. It is a
  Server Component precisely so no public mirror of the environment name exists to drift.

## Glossary — session and tenancy

- **Session cookie** — the httpOnly/Secure/SameSite cookie(s) holding the access/refresh
  JWTs, written and read only by the BFF and server code. Never readable by browser JS.
  *(§9.1, §9.2)*
- **Session projection** — the sanitized user/session model the browser is allowed to
  see: user id, display name, roles, capabilities, memberships, expiry metadata. Never
  tokens. _Avoid_: "the session" unqualified — say which one. *(§9.7)*
- **UX gate** — a middleware or layout redirect that bounces an obviously unauthenticated
  user. Named separately from **authorization**, which only FastAPI performs, because
  conflating them is how an app ships an unprotected endpoint behind a protected route.
  *(§7.6, §9.8)*
- **Terminal 401** — the unauthenticated response the browser sees only after the BFF's
  single refresh attempt has failed. It triggers one centralized session-expiry flow, not
  a per-feature logout. *(§18.1)*
- **Tenant / club context** — the effective club a request or query is scoped to, from a
  route segment, the session, or a parameter. **It is always authorized server-side**,
  never trusted from the browser. *(§11.1)*
- **Trust boundary** — any point where untrusted data enters: browser input, URL and
  search params, cookies, headers, environment variables, third-party data, persisted
  client state. Where Zod belongs — and nowhere else. *(§3.3, §15.1)*

## Glossary — client state

- **Server Component** — the default; renders on the server, may resolve the session and
  read through a server-only adapter. **Client Component** — `"use client"`; a deliberate
  bundle boundary, not a convenience. Do not put the directive at a page or layout root.
  *(§7.1, §7.2)*
- **Query / Mutation** — TanStack Query primitives in a feature's `model/`, always
  against the BFF. Query owns **remote server state**; it is not a general state
  container. *(§12.1)*
- **Query key factory** — the feature-owned, typed, hierarchical key builder. Includes
  every input that changes the response **and the tenant**; never a token, never a display
  label. `['clubs', clubId, 'bookings', normalizedFilters]`. *(§12.2, §11.2)*
- **Query option factory** — the reusable bundle of `queryKey`, `queryFn`, `staleTime`,
  error behavior and `select` that prefetch, hydration, invalidation and tests all share,
  instead of each component repeating it. *(§12.3)*
- **Prefetch / hydration** — the server path for initial data: a **request-local**
  QueryClient prefetches through the FastAPI adapter and dehydrates into a
  `HydrationBoundary`; the client hook then owns the same key over the BFF transport.
  *(§4.3, §12.11)*
- **Server-owned vs client-owned region** — the required per-region choice. In a
  server-owned region the Server Component renders the value and no client Query
  duplicates it; in a client-owned region the server only prefetches and Query owns it
  after hydration. Two owners diverge on revalidation. *(§12.12)*
- **UI state** — cross-cutting or transient client state held in **Zustand**: sidebar,
  command palette, non-navigable selection, preferences. Server data is *not* UI state —
  Query owns that, and copying it into a store is the bug that makes caches lie. *(§13)*
- **URL state** — navigable state in route/search params: filters, date range, sort,
  page/cursor, active tab, search query. Parsed and normalized **once at the boundary**
  into a canonical typed value. *(§14)*

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
- **Primitive vs composite** — a **primitive** lives in `shared/ui/` and knows no feature
  (button, dialog, table parts). A **composite** (`BookingStatusBadge`,
  `CourtAvailabilityGrid`) belongs to its feature's `ui/`, built from primitives. *(§39.2)*
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

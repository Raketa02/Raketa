# Rakieta Club Web App

Next.js 15 (App Router) + React 19 + TypeScript. The web app clubs use to manage courts,
availability, pricing and bookings. A **feature-oriented modular frontend** with a thin
App Router composition layer and a **server-only BFF**: the browser calls same-origin
`/api/*` route handlers, and those call FastAPI. pnpm.

> **Monorepo note.** This is the `frontend_club/` app of a three-app monorepo (see the
> root [`CLAUDE.md`](../CLAUDE.md) and [`../CONTEXT-MAP.md`](../CONTEXT-MAP.md)).
> Everything here scopes to `frontend_club/` — **run all commands from this directory.**
> The FastAPI backend (`../backend/`) and the Expo player app (`../frontend_player/`)
> have their own `CLAUDE.md`; **never apply their rules here, and never import their
> source.** A `PreToolUse` hook blocks writes outside `frontend_club/` from this session.
> Shared docs live at the root: [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

## The architecture standard is the law

[`docs/architecture/production-architecture.md`](docs/architecture/production-architecture.md)
is the **canonical architecture for this app** — 55 sections plus appendices, covering
runtime model, BFF, auth, tenancy, Query, Zustand, URL state, Zod, OpenAPI, errors,
testing, security, observability, CI and operations.

**This file is the operational digest.** It carries the rules an agent gets wrong and the
decisions that are already made. When the two disagree, the standard wins. When you need
detail this file omits — retry policy, cache-invalidation contracts, refresh concurrency,
Playwright fixtures — open the standard at the cited section (`§8.5`, `§27.4`, `§9.5`,
`§29.7`) rather than inventing an answer.

Read the standard's [§2 normative language](docs/architecture/production-architecture.md):
**MUST** is an invariant that needs an ADR to break. **SHOULD** is the default; deviate
only with a concrete reason. **MAY** is optional.

### ⚠ This supersedes ADR-0009 for this app

[ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md) mandates a
uniform Clean-Architecture layer set (`domain/ use-cases/ mappers/ …`) on **both**
frontends. The standard rejects that for a frontend explicitly — §3.8 ("do not introduce
repositories, use-case classes … merely to imitate backend Clean Architecture") and §44
("avoid empty layers that only forward arguments one-to-one").

The club app now follows the standard. Consequences you must know:

- `domain/`, `use-cases/` and `mappers/` **no longer exist here.** `model/` holds query
  keys, query options, hooks and feature types; `server/` holds server-only operations;
  `ui/` replaces `components/`.
- **The two clients no longer share a shape.** `frontend_player/` still follows ADR-0009.
  A rule learned there **does not** transfer here. The root `CLAUDE.md` and
  `CONTEXT-MAP.md` still claim they share a shape — that claim is now stale for the club
  app and needs correcting in a root-scoped session.
- No ADR has been written for this yet. Per [`docs/adr/README.md`](../docs/adr/README.md),
  a contradiction gets surfaced rather than silently overridden — this section is that
  surfacing, and the ADR is outstanding. See [Known gaps](#known-gaps).

ADRs that remain **in force** and agree with the standard:
[0005](../docs/adr/0005-three-app-monorepo-ownership-boundaries.md) (separate deployables,
HTTP only), [0006](../docs/adr/0006-backend-owns-api-contract.md) (backend owns the
contract), [0007](../docs/adr/0007-club-web-bff-httponly-cookie-session.md) (BFF +
httpOnly cookies), [0011](../docs/adr/0011-club-console-design-system.md) (locked design
system).

## Not scaffolded yet

This directory holds architecture, config and rules — not a running app. `pnpm install`
has not been run and there is no `src/app/layout.tsx`. If you are the first session here,
read [`README.md`](README.md) and build the foundations in the standard's **§47 order**
(compiler/boundaries → contract → auth/security → state platform → tests → observability
→ features). Do not reach for `create-next-app`; its flat layout contradicts the
structure below.

The **design system is already locked** — `src/shared/ui/tokens.css` predates the app.
The first `app/layout.tsx` must `import '@/shared/ui/tokens.css'` and load Archivo + IBM
Plex Mono through `next/font/google` as `--font-sans` / `--font-mono`.

## Default workflow

For non-trivial changes:
1. Explore the relevant files; state current behavior and constraints.
2. Propose a minimal plan before editing. For changes touching >5 files, confirm first.
3. Write or update tests first when behavior changes (see [Testing](#testing--29)).
4. Make the smallest safe change.
5. Run the most focused relevant tests first, then `pnpm test` when practical.
6. Run `pnpm lint && pnpm typecheck` before finishing if code changed.
7. Check the change against **§46 Definition of Done** — not just the happy path.
8. Summarize changed files, checks run, and remaining risks.

Do not claim a task is done unless the relevant tests/checks ran — or plainly state why.

## Safety — never do these without an explicit request

- **Let browser code call FastAPI directly.** Client Components call the BFF in
  `src/app/api/*` only. The browser must never learn the FastAPI origin. *(§4.1)*
- **Expose auth tokens to the browser.** Access/refresh JWTs live in httpOnly cookies set
  by the BFF — never in `localStorage`, `sessionStorage`, Zustand, TanStack Query, React
  Context, a JS-readable cookie, or a Client Component prop. *(§9.1)*
- **Rename `BACKEND_API_URL` to `NEXT_PUBLIC_*`.** Anything `NEXT_PUBLIC_` is public
  information baked into the client bundle. *(§20.1)*
- **Build a catch-all proxy** — `/api/proxy?url=…`, `/api/backend/[...path]`. Route
  handlers are deliberate endpoints. Generic forwarding is an SSRF hole. *(§8.2)*
- **Call FastAPI without a timeout,** or auto-retry a POST/PATCH without an idempotency
  key. *(§8.4, §8.5)*
- **Have a Server Component fetch its own `/api/*` over the network.** Server code calls
  the server-only FastAPI gateway directly. *(§4.2)*
- **Import `src/generated/` outside the transport boundary.** Generated wire types stay
  in `platform/server/`, a feature's `server/`, or a feature's `api/` contract adapter.
  Never in `ui/`. *(§16.2)*
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put a literal colour, font size, gap or radius in a component.** Every value comes
  from `src/shared/ui/tokens.css` as `var(--…)`. See [Design system](#design-system).
- **Add a dependency that owns styling** — Tailwind, styled-components, Emotion, a
  component library. *(ADR-0011)*
- **Introduce Server Actions for domain mutations.** BFF route handlers are the declared
  mutation transport; a second one splits auth, errors, tests and observability. Needs an
  ADR. *(§7.3)*
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

```
src/
  app/                     Next App Router — composition and routing ONLY (§3.5)
    (public)/ (authenticated)/
    api/                   BFF route handlers — deliberate endpoints (§8)
    layout.tsx providers.tsx error.tsx global-error.tsx not-found.tsx
  features/<feature>/      the unit of change and ownership
    api/                   browser → BFF calls + the BFF-facing contract
    model/                 query keys, query options, hooks, feature types
    schemas/               Zod — forms, search params, inputs
    state/                 feature-local Zustand — only if justified
    ui/                    rendering and interaction
    server/                server-only operations + the FastAPI adapter
    test/
    index.ts               the explicit public API — the only import surface
  platform/                application-wide infrastructure
    api/                   browser client primitives, error normalization
    server/                fastapi-client, auth/, csrf/, request-context/,
                           errors/, observability/  — all server-only
    query/                 query-client factory, providers, global key primitives
    config/                Zod-validated env (server schema and public schema)
    observability/  security/
  shared/                  generic capability that knows no feature
    ui/                    design-system primitives (tokens.css lives here)
    lib/ hooks/ types/ test/
  generated/               openapi-typescript output — never hand-edited
e2e/                       Playwright specs
docs/architecture/         the standard
```

Two deliberate deviations from the standard's §5 sketch, both permitted by its own
"exact names can evolve" clause:

- Generated types stay at `src/generated/schema.d.ts` (not `generated/fastapi/`), because
  `pnpm gen:api` and the root `make gen-api` already target it.
- E2E specs stay in `e2e/` (not `tests/e2e/`), where `playwright.config` expects them.

### Dependency rules *(§6)*

```
app        → features · platform · shared
features   → platform public APIs · shared · another feature ONLY via its index.ts
platform   → shared
shared     → nothing from any feature
generated  → consumed at the server/transport boundary, never by UI
```

**MUST NOT:** import `src/app` from a feature · import feature code into `shared` ·
import server-only code into a Client Component · import generated `paths` into a
component · deep-import another feature's internals (`features/x/model/foo`) · create a
circular feature dependency.

A feature is reachable **only through its `index.ts`.** Keep that surface small and
intentional; no root mega-barrel. *(§5.2)*

Cross-feature workflows compose at the route level, in a dedicated workflow module, or as
a genuinely shared capability — never by letting features reach into each other. *(§5.3)*

### The canonical flow

```
Client Component → TanStack Query → /api BFF route handler → FastAPI
Server Component → server-only feature adapter → FastAPI          (never self-fetch /api)
```

Build every feature vertically along that path — page/UI → query → browser client →
route handler → feature server adapter → FastAPI → tests/telemetry. That is what stops
each new feature inventing its own architecture. *(§47 Phase 7)*

## One owner for every piece of state *(§3.1, §49)*

The single most important table in the standard. Two owners for one value is the bug.

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
idempotency. The frontend may mirror a rule for UX only, and only while it is clearly
non-authoritative. *(§3.2)*

## The BFF *(§8, §43)*

Not a proxy — a security, authentication, adaptation and observability boundary.

Every handler follows this sequence, built from small reusable primitives rather than
copied into each `route.ts`:

```
request context / trace ID → method + content-type + origin/CSRF checks
→ authentication → input validation → authorization context
→ feature server operation → FastAPI call WITH TIMEOUT
→ error normalization → minimal response DTO
→ explicit cache + security headers → structured telemetry
```

Rules that get broken:

- **Explicit header allowlist outbound.** Construct `Authorization` server-side; add
  request ID, trace context, idempotency key where relevant. Never forward the browser's
  whole header set or its cookies to FastAPI. *(§8.3)*
- **Finite timeout on every downstream call,** categorized by endpoint — not one huge
  global value. Propagate abort signals. *(§8.4)*
- **Retry is opt-in, not default.** GET/HEAD may retry transient failures inside the
  deadline; POST/PATCH never retry without a backend idempotency guarantee; auth refresh
  gets at most one attempt per request. *(§8.5)*
- **Authenticated responses are `no-store`/private.** A cache leak is a data breach, not a
  minor bug. *(§8.7, §27.3)*
- **Never proxy large media byte-for-byte.** Use presigned upload/download URLs or async
  export jobs. *(§8.6)*
- **The BFF contract is a frontend contract,** not a mirror of FastAPI. It may combine
  calls, drop sensitive fields, normalize errors and reduce payloads. Do not erase the
  BFF's purpose by re-exposing every backend DTO unchanged. *(§16.3)*
- Business workflows do not live in `route.ts`. *(§8.1)*

## Auth *(§9)*

Login: browser POSTs to the same-origin BFF → BFF validates → BFF calls FastAPI →
FastAPI returns credentials server-to-server → BFF writes httpOnly cookies → BFF returns
**only a sanitized session projection** (user id, display name, roles, capabilities,
memberships, expiry metadata). Never tokens. *(§9.3, §9.7)*

Cookie baseline: `HttpOnly`, `Secure` outside local, explicit `SameSite` (never the
browser default), `Path=/`, no broad `Domain`, `__Host-` prefix where the deployment
allows, short access lifetime, controlled refresh rotation. *(§9.2)*

**Middleware is not authorization.** A layout or middleware redirect is a UX gate. Every
BFF endpoint and every sensitive server operation must independently verify session and
permission, and FastAPI must authorize every protected operation. Hidden UI is not
security. *(§7.6, §9.8, §24.5)*

Logout: revoke server-side → clear cookies with matching attributes → clear sensitive
Query state → reset sensitive Zustand stores → redirect. *(§9.6, §37.4)*

> **Open: refresh concurrency.** §9.5 forbids solving concurrent refresh with an
> in-memory JavaScript mutex, because a horizontally scaled Next.js deployment has many
> processes. [ADR-0004](../docs/adr/0004-jwt-access-with-rotating-refresh-tokens.md)
> rotates strictly and **rejects** an already-rotated token — there is no grace window
> today, and that ADR itself names the failure ("a burst of concurrent refreshes that
> rotate each other out and log the user out"). The mechanism must be settled with the
> backend — rotation grace/reuse, an opaque session ID with a shared session store, or
> distributed synchronization — before auth is built. Do not paper over it with a
> module-global lock. See [Known gaps](#known-gaps).

## Multi-tenancy *(§11)*

Tenant isolation is an architecture invariant, not a UI filter.

- Every tenant-scoped query key **MUST** carry the club identity:
  `['clubs', clubId, 'bookings', normalizedFilters]`, never `['bookings']`. *(§11.2)*
- Tenant-specific Zustand state either includes tenant identity or resets when the club
  changes. *(§11.3)*
- **Key scoping is not authorization.** It prevents cache confusion; FastAPI must verify
  the principal against the target club. Never trust a `clubId` from the browser. *(§11.4)*

## TanStack Query *(§12)*

Owns remote server state in the browser. It is not a general state container.

- **Feature-owned typed key factory** — hierarchical, deterministic, includes every input
  that changes the response and the tenant; never a token, never a display label. *(§12.2)*
- **Query option factories,** not `queryKey`/`queryFn`/`staleTime` duplicated per
  component — that is what makes prefetch, hydration and invalidation consistent. *(§12.3)*
- **`staleTime` is a product decision per data class,** not one global number: session,
  near-real-time availability, club config, reference data, immutable history. Choose
  `gcTime` independently. Decide focus/reconnect/mount refetch deliberately — an admin
  tab stays open for hours. *(§12.4, §12.5)*
- **Propagate the abort signal** into `fetch` — type-ahead, fast-changing filters,
  reports. *(§12.6)*
- **Invalidate narrowly.** Prefer updating known entries from the mutation response over
  a broad prefix invalidation after every write. *(§12.7)*
- **Mutation retry defaults off.** Optimistic updates only when rollback is deterministic
  and conflict semantics are understood — not for payments, destructive admin actions or
  permission changes. *(§12.8, §12.9)*
- **RSC and Query must not own the same live value.** Pick one per region: server-owned
  (RSC renders, refresh via navigation) or client-owned (RSC prefetches + dehydrates, then
  Query owns it). Divergence after revalidation is the failure mode. *(§12.12)*
- Server prefetch uses a **request-local** QueryClient. Never a global one shared across
  users. *(§12.11, §42.2)*

## Zustand *(§13)*

Only client UI state that belongs to neither the server nor the URL: sidebar state,
command palette, non-navigable selection, transient wizard draft, UI preferences.

**Never** a second cache for bookings, courts, members, club settings, session tokens,
server permissions, URL filters, or single-screen form state. Prefer several small stores
with a reset policy over one global store; subscribe to the smallest slice. Never a
global mutable store on the server — that leaks one user's state into another request.
Persist only non-sensitive, versioned, migratable, tenant-scoped state. *(§13.2–13.6)*

## URL state *(§14)*

Filters, date ranges, sort, page/cursor, active tab, search query, selected club — put
them in search params so back/forward, deep links, refresh and multiple tabs all work.
Parse and normalize them **once at the boundary** into a canonical typed value; do not let
every component parse strings.

## Zod and runtime validation *(§15)*

Zod belongs at **trust boundaries**, not sprayed over already-typed internals. Static
types disappear at runtime.

Validate: form payloads, search params, BFF request bodies, environment config, persisted
state migrations. Use `safeParse` for user input so validation is a typed branch, not an
exception. Put cross-field rules in the schema, not in `onChange`. *(§15.2, §15.6, §15.7)*

**Client validation is UX; FastAPI validation is authority.** *(§15.3)*

Do not duplicate the same concept as interface + type alias + Zod schema + OpenAPI type.
Infer TS from Zod where the app owns the input model; use the generated type at the
transport boundary. Runtime-validate responses on a **risk basis** — high-risk, external
or corruption-sensitive data — not every payload. *(§15.4, §15.5)*

Business primitives: an instant is not a calendar date; a club's local opening time is not
a UTC instant; test DST. Money never in floats — integer minor units or the backend's
decimal-string contract, with an explicit currency. IDs are opaque. *(§15.8)*

## Errors *(§22, §18.2)*

One stable browser-facing envelope: machine `code`, safe user-facing `message`, optional
`fieldErrors`/`details`, and a `requestId`. Components reason about stable categories —
unauthenticated, forbidden, validation, conflict, rate limited, not found, transient
network, backend unavailable, unexpected — never raw HTTP status/body shapes. *(§12.13)*

Feature domain codes sit beneath those categories (`COURT_ALREADY_BOOKED`). BFF status
codes stay semantically meaningful — not everything a 200 with `success: false`, not
everything a 500. Internal exception text, SQL and stack traces stay server-side.

Recovery is per category: validation → field error · conflict → refresh and explain ·
401 → central session expiry · 403 → permission UI · transient → retry affordance ·
5xx → preserve input, show retry and a request ID. *(§22.5)*

## OpenAPI *(§16)*

`src/generated/schema.d.ts` is generated, never hand-edited, and committed. The pinned
contract artifact is `../backend/openapi.json`, which the backend owns
([ADR-0006](../docs/adr/0006-backend-owns-api-contract.md)) — the production build must
never depend on reaching a live backend for its schema. *(§16.1, §16.4)*

Keep generated types **at the boundary**:

```
generated types → server FastAPI adapter → feature contract/model → hooks → UI
```

No broad snake_case↔camelCase remapping for aesthetics; adapt a field only where the
frontend contract genuinely differs. Design for enum evolution — decide what the UI does
with an unknown value, because backend and frontend do not deploy atomically. *(§16.7, §40.2)*

## Design system

**Locked**, and unchanged by this standard — the standard's §39 says exactly what
[ADR-0011](../docs/adr/0011-club-console-design-system.md) already decided. Full rules:
[`docs/design-system.md`](docs/design-system.md).

Three artefacts that **change together, in the same commit**:

| File | Is |
| --- | --- |
| [`src/shared/ui/tokens.css`](src/shared/ui/tokens.css) | The source of every value. Imported once, from `app/layout.tsx`. |
| [`docs/design-system.md`](docs/design-system.md) | The rules — meanings, containers, surfaces, copy. |
| [`docs/design-system-v7-prototype-audit.md`](docs/design-system-v7-prototype-audit.md) | Archived measurement of the prototype. Not the rules. |

**Styling is CSS Modules colocated with the component** (`Card.tsx` + `Card.module.css`),
referencing `var(--…)`. No Tailwind, no CSS-in-JS, no runtime-injected CSS.

`shared/ui/` primitives must not know what a booking is. A `BookingStatusBadge` or
`CourtAvailabilityGrid` belongs to its feature's `ui/`, composed from those primitives.
Accessibility (focus management, ARIA, keyboard) is encoded **once** in the primitives so
features cannot reimplement it wrongly. *(§39.2, §39.3)*

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

## Accessibility *(§24)*

WCAG 2.2 AA is the target. Semantic HTML first; keyboard operability; visible focus;
associated labels; accessible names on icon buttons; dialog focus trap and restoration;
table semantics; status never by colour alone; live regions for async feedback;
reduced-motion respect.

Desktop does not mean mouse-only — club staff work keyboard-heavy. Prefer contextual
skeletons over blank pages. Make destructive actions proportionally resistant to
accidental clicks.

## Testing *(§29)*

Confidence at the cheapest reliable layer — not the maximum number of tests.

| Layer | Covers |
| --- | --- |
| Static | TypeScript, lint/import boundaries, generated-contract drift |
| **Vitest unit** | Zod schemas, money/date rules, search-param parsing, **query-key factories**, error normalization, state transitions, DTO→UI mapping, idempotency helpers |
| Component | user-observable behavior: validation, loading/error/success, keyboard, permission-dependent UI, dialogs, filters |
| **BFF integration** | unauthenticated rejected · wrong tenant rejected · invalid input rejected before the backend call · Authorization built server-side · browser cookies not forwarded · refresh success **and** failure · cookie flags · timeout mapping · conflict mapping · request-ID propagation · bad-Origin rejection · **no backend internals leaked** |
| Contract | OpenAPI validity, generated-type drift, breaking-change detection |
| **Playwright** | login/logout · session expiry and refresh · club switching and tenant isolation · role boundaries · booking create/edit/cancel · concurrent-change conflict · deep-link filters · double-submit · security-sensitive actions |

Security assertions are tests, not prose: cookies are HttpOnly/Secure/SameSite · tenant A
cannot read tenant B · mutations reject disallowed origins · redirect targets cannot leave
the allowlist · token strings never appear in rendered HTML or client storage · generic
BFF URL forwarding is impossible. *(§30)*

Playwright rules: isolated tests, each owning its data · `getByRole`/label/text before
CSS/XPath · **no arbitrary sleeps** · web-first assertions · traces on CI failure.
**Flaky tests are defects**, quarantined only with an owner and a deadline. Coverage is a
signal, not a goal. *(§29.7, §29.9, §29.10)*

Colocate unit/component tests as `*.test.ts(x)` beside the file, or in the feature's
`test/`. E2E specs live in `e2e/`.

## Code style

- **TypeScript strict.** `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`,
  `noFallthroughCasesInSwitch` are on today; §17.1 also wants
  `exactOptionalPropertyTypes` and `useUnknownInCatchVariables` — see
  [Known gaps](#known-gaps).
- **Near-zero `any`** in feature code. Use `unknown` at untrusted boundaries, real
  generics, Zod narrowing, generated types, discriminated unions. If a third-party
  integration forces `any`, isolate it in one adapter and document why. *(§17.2)*
- **`as` is not an error-suppression tool.** Localize a proven-boundary assertion and test
  it. Prefer `satisfies` to check conformance without losing literal inference. *(§17.3, §17.4)*
- Model state machines as **discriminated unions**, not several booleans that permit
  impossible combinations. Make critical status switches **exhaustive** so a new backend
  state fails the compile instead of silently rendering nothing. *(§17.5, §17.6)*
- Name by domain meaning: `BookingTable`, `useBookingFilters`, `cancelBooking` — never
  `DataComponent`, `CommonService`, `Helper2`. *(§17.7)*
- A helper reaches `shared/lib` only when it is genuinely domain-independent. A booking
  calculation stays in the booking feature even if two screens use it. *(§17.8)*
- `useEffect` synchronizes with external systems — not deriving values, not copying props
  to state, not copying Query data into Zustand, not routine fetching. *(§23.3)*
- Do not memoize pre-emptively; optimize what you measured. List keys are stable domain
  IDs, never array indices. *(§23.4, §23.5)*
- **Zod** for all external input. New domain concepts use the **shared glossary's**
  vocabulary ([`../CONTEXT.md`](../CONTEXT.md)). A `Court` is a `Court` — not a Venue.
- Prefer named exports. Run `pnpm format` before committing.

## Known gaps

Real and outstanding. Do not assume the guardrails below already hold.

1. **No ADR for this standard.** One is needed: adopting it, and scoping ADR-0009 to the
   player app. Root-scoped session — the ownership hook blocks it from here.
2. **Root `CLAUDE.md` and `CONTEXT-MAP.md` are stale** on "the two clients share a shape"
   and on the club layer set. Same — root-scoped session.
3. **`eslint.config.mjs` still enforces the ADR-0009 layers.** It exempts `api/` and
   `mappers/` for generated imports and treats `domain/`/`use-cases/` as pure. Those
   folders no longer exist. It needs: `server/` and the transport adapters exempted
   instead, a `server-only` boundary rule, a deep-import ban on
   `features/*/{api,model,schemas,state,ui,server}`, and a rule keeping generated `paths`
   out of `ui/`. Until then **the boundaries in this file are documentation, not
   enforcement.** *(§34)*
4. **`tsconfig.json` lacks `exactOptionalPropertyTypes` and
   `useUnknownInCatchVariables`.** *(§17.1)*
5. **Tooling from §48 is absent** from `package.json`: no Prettier config in lint, no
   TanStack Query ESLint plugin, no axe, no OpenTelemetry, no bundle budget, no
   OpenAPI breaking-change tool. Next/React are floating `^` ranges — §33.1 wants exact
   patched pins, and §33.2 makes that a security requirement, not a preference.
6. **Refresh concurrency is unsettled** with the backend — see [Auth](#auth-9).

## Git & PRs

- Conventional Commits scoped `club`: e.g. `feat(club): court availability calendar`.
- CI runs `lint`, `typecheck`, `test` and `build` for `frontend_club/` when
  `frontend_club/**` changed; all must pass. Run `pnpm check` before pushing.
- For a substantial PR, walk the standard's **§51 review questions** — what owns this
  state, where is authorization enforced, what is the timeout, what invalidates the cache,
  can this run correctly on ten instances.

## Domain language

Shared domain terms: [`../CONTEXT.md`](../CONTEXT.md). Club-app-only technical
vocabulary: [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally.

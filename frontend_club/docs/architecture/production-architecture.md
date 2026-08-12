# Frontend Club — Senior Production-Ready Architecture Standard

**Target:** Desktop web application built with Next.js App Router + React + TypeScript  
**Declared stack:** Next.js 15, React 19, TypeScript, TanStack Query, Zod, Zustand, Vitest, Playwright, openapi-typescript  
**Backend integration:** Browser → Next.js BFF Route Handlers (`src/app/api/*`) → FastAPI backend  
**Authentication:** Access/refresh authentication managed by the BFF through `httpOnly` cookies; browser JavaScript must never receive or persist the raw tokens.

---

## 1. Purpose and architectural position

This document defines the architecture and engineering rules for a production-grade, long-lived, highly scalable club web application. The goal is not merely to organize folders. The goal is to create a system that remains safe to change when:

- the number of features grows significantly;
- several developers or AI agents work in parallel;
- backend contracts evolve;
- multiple clubs/tenants, roles, permissions, locales, and workflows are introduced;
- the UI becomes increasingly interactive;
- traffic and concurrency grow;
- deployment becomes horizontally scaled;
- security requirements become stricter;
- the codebase must support years of incremental change without becoming tightly coupled.

The recommended architecture is a **feature-oriented modular monolith** inside the Next.js application, with a strict separation between:

1. **Next.js composition and routing** — `src/app`;
2. **browser-facing feature modules** — UI, query hooks, feature state, validation, feature contracts;
3. **server-only BFF infrastructure** — authentication, FastAPI client, error normalization, request context, security and observability;
4. **generated backend API types** — isolated at the FastAPI boundary;
5. **shared platform capabilities** — design system, query infrastructure, configuration, telemetry and generic utilities.

The architecture must optimize for **change isolation**, **clear ownership**, **explicit trust boundaries**, **type safety**, **runtime validation where it matters**, **testability**, and **horizontal scalability**.

---

## 2. Normative language

This document uses the following terms intentionally:

- **MUST / MUST NOT** — architectural invariant. Violating it requires an explicit architecture decision and review.
- **SHOULD / SHOULD NOT** — default senior-level practice. Deviations are acceptable only with a concrete reason.
- **MAY** — optional practice depending on feature needs.

Architecture rules that matter should eventually be enforced mechanically through TypeScript, ESLint/import-boundary rules, CI checks, test architecture and code ownership rather than relying only on team memory.

---

## 3. Core architectural principles

### 3.1 One owner for every category of state

The application MUST not allow the same state to be independently owned by multiple mechanisms.

| State category | Owner |
|---|---|
| Backend/server data | TanStack Query, or a Server Component when the region is fully server-owned |
| Authentication tokens | BFF `httpOnly` cookies only |
| Logged-in user/session projection | Server session resolution and/or a sanitized session query |
| Navigable/filter state that belongs in a URL | Next.js route params/search params |
| Local transient component state | React `useState` / `useReducer` |
| Cross-component transient UI state | Zustand |
| Form state | Component/form layer; Zod validates boundaries |
| Long-lived server business rules | FastAPI backend, not the frontend |
| Generated backend contract | FastAPI OpenAPI → `openapi-typescript` |

Duplicating query data in Zustand, copying URL filters into a store, or storing access tokens in client state creates two sources of truth and MUST be avoided.

### 3.2 Server-authoritative business behavior

The browser may provide immediate validation and optimistic UX, but authoritative rules MUST remain on the FastAPI backend. Examples include:

- permissions and tenant membership;
- booking eligibility;
- pricing;
- cancellation/funding rules;
- state transitions;
- capacity constraints;
- payment state;
- conflict detection;
- idempotency;
- transactional rules.

The frontend is allowed to mirror rules for UX only when the backend remains authoritative and the mirrored rule is clearly recognized as non-authoritative.

### 3.3 Explicit trust boundaries

Treat all of the following as untrusted until validated or normalized:

- browser input;
- URL parameters and search parameters;
- cookies;
- request headers;
- FastAPI responses at runtime when correctness/security warrants validation;
- environment variables;
- third-party data;
- persisted client-side state.

Static TypeScript types are not runtime validation.

### 3.4 Feature-first organization

The codebase SHOULD be organized primarily around business capabilities, not a top-level technical-layer structure such as one giant `components/`, `hooks/`, `services/` and `stores/` directory.

A feature should be understandable and removable mostly within one module boundary.

### 3.5 `src/app` is composition, not the business layer

`src/app` MUST remain thin. Pages, layouts and Route Handlers compose capabilities. They should not become the place where feature logic accumulates.

### 3.6 The BFF is not a generic proxy

The BFF is a security, authentication, adaptation and observability boundary. It MUST expose deliberate endpoints. It MUST NOT accept an arbitrary backend URL/path supplied by the browser and forward it blindly.

### 3.7 Stateless frontend servers

The Next.js application MUST remain safe when several instances run simultaneously. Do not depend on in-memory locks, in-memory sessions, module-global request data, or process-local caches for correctness.

### 3.8 Prefer boring, explicit architecture over abstraction density

Abstractions must reduce real duplication or enforce real invariants. Do not introduce repositories, use-case classes, factories, dependency injection containers or generic wrappers merely to imitate backend Clean Architecture. Frontend architecture should remain appropriately lightweight while preserving boundaries.

---

## 4. Target runtime model

### 4.1 Primary browser data flow

```text
Browser / Client Component
        │
        │ same-origin HTTP
        ▼
Next.js Route Handler (/api/...)
        │
        │ server-side HTTP + Authorization header
        ▼
FastAPI backend
```

The browser SHOULD know only the club application's origin. The FastAPI base URL SHOULD be server-only configuration and MUST NOT be exposed as `NEXT_PUBLIC_*` unless there is an unrelated explicit browser-direct requirement.

### 4.2 Server Component data flow

A Server Component that needs backend data SHOULD NOT make an HTTP request back into the same Next.js deployment through `/api/*`. That creates an unnecessary network hop, complicates headers/cookies, adds latency and can create deployment-specific problems.

Use:

```text
Server Component
      │
      ▼
server-only feature/gateway function
      │
      ▼
FastAPI
```

The browser still uses `/api/*`; server code may call the shared server-side FastAPI gateway directly.

### 4.3 One domain, two transports

For data that is prefetched on the server and then managed interactively with TanStack Query in the browser:

- the **query key and resulting data contract** should be shared;
- the **server prefetch transport** calls FastAPI directly through server-only infrastructure;
- the **browser query transport** calls the BFF;
- the hydrated TanStack Query cache bridges the initial data without making browser code aware of backend tokens or the FastAPI address.

This avoids self-fetching while retaining a consistent client cache.

---

## 5. Recommended project structure

The exact names can evolve, but the dependency direction and responsibilities should remain stable.

```text
frontend_club/
├─ src/
│  ├─ app/                         # Next.js routing/composition only
│  │  ├─ (public)/
│  │  ├─ (authenticated)/
│  │  │  ├─ layout.tsx
│  │  │  └─ ...
│  │  ├─ api/                     # Thin BFF Route Handlers
│  │  │  ├─ auth/
│  │  │  ├─ clubs/
│  │  │  ├─ bookings/
│  │  │  └─ ...
│  │  ├─ layout.tsx
│  │  ├─ providers.tsx
│  │  ├─ error.tsx
│  │  ├─ global-error.tsx
│  │  └─ not-found.tsx
│  │
│  ├─ features/                   # Business capability modules
│  │  ├─ auth/
│  │  │  ├─ api/                 # Browser → BFF calls
│  │  │  ├─ model/               # Query keys/options, hooks, feature types
│  │  │  ├─ schemas/             # Zod form/input schemas
│  │  │  ├─ state/               # Feature-local Zustand only if justified
│  │  │  ├─ ui/
│  │  │  ├─ server/              # Server-only feature operations
│  │  │  ├─ test/
│  │  │  └─ index.ts             # Explicit public API
│  │  ├─ bookings/
│  │  ├─ matches/
│  │  ├─ courts/
│  │  ├─ members/
│  │  └─ ...
│  │
│  ├─ platform/                   # Application-wide infrastructure
│  │  ├─ api/
│  │  │  ├─ browser-client.ts    # Same-origin /api client primitives
│  │  │  ├─ errors.ts
│  │  │  └─ request.ts
│  │  ├─ server/
│  │  │  ├─ fastapi-client.ts
│  │  │  ├─ auth/
│  │  │  ├─ csrf/
│  │  │  ├─ request-context/
│  │  │  ├─ errors/
│  │  │  └─ observability/
│  │  ├─ query/
│  │  │  ├─ query-client.ts
│  │  │  ├─ providers.tsx
│  │  │  └─ keys.ts              # only truly global key primitives
│  │  ├─ config/
│  │  ├─ observability/
│  │  └─ security/
│  │
│  ├─ shared/
│  │  ├─ ui/                     # Design-system primitives
│  │  ├─ lib/                    # Pure, generic helpers
│  │  ├─ hooks/                  # Truly generic browser hooks only
│  │  ├─ types/
│  │  └─ test/
│  │
│  └─ generated/
│     └─ fastapi/
│        └─ schema.d.ts          # Generated; never manually edited
│
├─ tests/
│  ├─ e2e/
│  ├─ fixtures/
│  └─ contract/
│
├─ docs/
│  ├─ architecture/
│  └─ adr/
│
├─ openapi/
│  └─ backend.openapi.json       # Pinned/checked contract artifact if chosen
│
└─ ...
```

### 5.1 Why feature modules include `server/`

Keeping server-specific feature behavior close to its feature preserves ownership without allowing it into the client bundle. Server files MUST be protected with `server-only` boundaries or equivalent import restrictions.

### 5.2 Public module APIs

Each feature SHOULD expose a small, intentional `index.ts` public surface. Other modules MUST NOT deep-import internal feature files.

Avoid giant root barrel files because they:

- hide dependency direction;
- create cycles;
- worsen tree-shaking/debugging;
- make feature boundaries meaningless.

### 5.3 Cross-feature workflows

If a workflow genuinely coordinates several features, compose it at one of these places:

1. the route/page orchestration level;
2. a dedicated workflow module;
3. a shared domain capability only when it is genuinely shared.

Do not solve cross-feature workflows by allowing every feature to import arbitrary internals of every other feature.

---

## 6. Dependency rules

A practical dependency model:

```text
src/app
  ├──> features
  ├──> platform
  └──> shared

features
  ├──> platform public APIs
  ├──> shared
  └──> another feature only through its declared public API when unavoidable

platform
  └──> shared

shared
  └──> no business feature

generated FastAPI types
  └──> consumed by server/API boundary code, not directly by UI
```

### 6.1 Forbidden dependencies

MUST NOT:

- import `src/app` from a feature;
- import feature-specific code into `shared`;
- import server-only code into a Client Component;
- import FastAPI generated `paths` directly into presentation components;
- import another feature's private files;
- create circular feature dependencies;
- let a generic utility import React feature code;
- let Zustand stores import route components.

These constraints SHOULD be linted in CI.

---

## 7. Next.js App Router architecture

### 7.1 Server Components are the default

Use Server Components by default for:

- page/layout composition;
- server-only configuration;
- authorization-aware shells;
- initial backend reads where server ownership makes sense;
- prefetching data for client Query hydration;
- reducing browser JavaScript.

Use Client Components only when a subtree needs browser-only capabilities such as:

- event handlers;
- local interactive state;
- Zustand;
- TanStack Query hooks;
- browser APIs;
- effects;
- client-only libraries.

Do not place `'use client'` at page/layout roots merely for convenience. The directive defines a client boundary and can unnecessarily pull substantial code into the client bundle.

### 7.2 Keep client boundaries low and deliberate

A large administrative screen can still be mostly server-composed while individual tables, filters, dialogs or editors are Client Components.

Do not obsess over making every tiny element a separate boundary. The objective is a sensible server/client split that minimizes shipped JavaScript and preserves maintainability.

### 7.3 Do not create a second mutation architecture with Server Actions by accident

This project's declared browser integration model is:

```text
Browser → BFF Route Handlers → FastAPI
```

That should remain the primary mutation contract. Introducing Server Actions for the same domain operations creates two transports with different:

- authentication behavior;
- error handling;
- test strategy;
- observability;
- caching/invalidation semantics;
- security review surfaces.

Therefore, domain mutations SHOULD use BFF Route Handlers consistently unless an explicit ADR decides otherwise.

### 7.4 Suspense and streaming

Use route-level `loading.tsx` and targeted `<Suspense>` boundaries around independently loadable regions when they improve perceived latency.

Avoid a single full-page spinner for dashboards that contain independently fetchable panels.

Parallelize independent server requests rather than introducing accidental waterfalls.

### 7.5 Error boundaries

Provide appropriate:

- `error.tsx` at meaningful route boundaries;
- `global-error.tsx` for unrecoverable shell failures;
- `not-found.tsx` for domain resources that do not exist;
- feature-level error UI for query/mutation failures.

Error boundaries should show safe, actionable user feedback and an incident/request identifier when useful. They MUST NOT expose stack traces, tokens or backend internal details.

### 7.6 Middleware/Proxy is not authorization

Next.js request interception may be used for cheap coarse checks such as redirecting an obviously unauthenticated user away from an authenticated route.

It MUST NOT be the only authorization control. Every BFF endpoint and every sensitive server operation must independently verify the current session and required permission.

### 7.7 Route groups and layouts

Use route groups to model layout/security boundaries, not business-layer boundaries. Examples:

- `(public)`
- `(authenticated)`
- `(admin)` if the product genuinely has a distinct shell/permission segment.

Do not let route group nesting become the source of feature code organization.

---

## 8. BFF architecture

The BFF is one of the most important parts of this design.

### 8.1 Route Handler responsibilities

A Route Handler SHOULD do only orchestration-level work:

1. create/obtain request context;
2. enforce method/content-type/body-size expectations;
3. verify CSRF/origin for unsafe methods;
4. resolve authentication;
5. check coarse BFF-side permissions where applicable;
6. validate browser input;
7. call a server-only feature operation/FastAPI gateway;
8. map backend errors to the BFF error contract;
9. attach tracing/security/cache headers;
10. return a minimal browser-facing response.

Do not embed large business workflows directly in `route.ts` files.

### 8.2 No catch-all proxy endpoint

Never expose designs such as:

```text
/api/proxy?url=https://backend/...
/api/backend/[...path]
```

unless the path space is tightly allowlisted and deliberately treated as an API gateway. Generic forwarding increases SSRF, authorization, header-forwarding and accidental-backend-exposure risk.

### 8.3 Explicit header forwarding

The BFF SHOULD construct outbound FastAPI requests from an allowlist of required headers.

Possible forwarded/generated headers include:

- `Authorization` — constructed server-side from the access token;
- `Content-Type` / negotiated `Accept` where needed;
- request/correlation ID;
- W3C trace context;
- idempotency key for supported mutations;
- locale/time-zone headers only if part of a deliberate backend contract.

Do not forward the browser's entire header set or all cookies to FastAPI.

### 8.4 Timeouts and cancellation

Every downstream FastAPI request MUST have a finite timeout appropriate to the endpoint. A BFF request must not be allowed to wait indefinitely.

Use abort signals so that:

- timed-out downstream calls are cancelled;
- where the runtime supports it, cancelled upstream requests can stop unnecessary work.

Timeout policy should be categorized by endpoint rather than set to one excessively large global value.

### 8.5 Retry policy

The BFF SHOULD NOT blindly retry every failed request.

Safe default:

- GET/HEAD: limited retry only for clearly transient failures and only within the overall request deadline;
- idempotent PUT/DELETE: only if the backend contract makes retry safety explicit;
- POST/PATCH mutations: no automatic retry unless backed by an idempotency key and server-side idempotency guarantee;
- authentication refresh: at most one controlled refresh attempt per original request.

Avoid multiplicative retry storms where browser, BFF, service mesh and FastAPI client all retry independently.

### 8.6 Large uploads/downloads

Do not use Route Handlers as a default byte-for-byte proxy for large media or export files. Prefer patterns such as:

- presigned object-storage upload/download URLs;
- backend streaming endpoints reached through controlled infrastructure;
- asynchronous export jobs.

This protects memory, bandwidth and execution limits.

### 8.7 Cache behavior

Authenticated BFF endpoints SHOULD explicitly return non-shared cache semantics such as private/no-store behavior unless there is a very specific safe caching design.

Never allow personalized data to enter a shared CDN cache accidentally.

In Next.js 15, Route Handlers are not cached by default, but security-sensitive cache behavior should still be explicit so future refactors or framework upgrades do not silently change assumptions.

---

## 9. Authentication and session architecture

### 9.1 Fundamental rule

Raw access and refresh tokens MUST NOT be readable by browser JavaScript.

Never store them in:

- `localStorage`;
- `sessionStorage`;
- Zustand;
- TanStack Query;
- React Context;
- non-HttpOnly cookies.

### 9.2 Cookie baseline

Authentication cookies SHOULD use:

- `HttpOnly`;
- `Secure` in all non-local environments;
- explicit `SameSite=Strict` when product flows allow it, otherwise a carefully justified `Lax`;
- `Path=/` where appropriate;
- no broad `Domain` attribute unless subdomain sharing is intentionally required;
- `__Host-` prefix when compatible with the deployment because it enforces strong browser cookie constraints;
- short access-token lifetime;
- controlled refresh-token lifetime and rotation/revocation behavior.

Never rely on browser-default SameSite behavior.

### 9.3 Login flow

Recommended sequence:

```text
1. Browser POSTs credentials/auth proof to same-origin BFF auth endpoint.
2. BFF validates input.
3. BFF calls FastAPI authentication endpoint.
4. FastAPI returns access/refresh credentials to BFF over server-to-server TLS.
5. BFF writes secure HttpOnly cookies.
6. BFF returns only sanitized session/user information needed by the UI.
```

### 9.4 Authenticated API flow

```text
1. Browser calls /api/... without handling tokens.
2. BFF reads HttpOnly access cookie.
3. BFF sends Authorization header to FastAPI.
4. FastAPI validates token and authorization.
5. BFF returns sanitized response.
```

### 9.5 Refresh flow and concurrency

Token refresh is a common production failure point.

A route may attempt one refresh when FastAPI returns an authentication-expired signal, then retry the original request once. However, multiple browser requests may arrive concurrently with the same expired access token.

**Do not solve this only with an in-memory JavaScript mutex.** A horizontally scaled Next.js deployment has multiple processes/instances, so a process-local lock cannot guarantee single-flight refresh globally.

If refresh tokens rotate, the overall auth design MUST be concurrency-safe. Viable approaches include:

1. backend refresh-token rotation with a grace/reuse strategy that safely tolerates concurrent refreshes;
2. an opaque server-side session ID in the browser with tokens maintained in a shared session store;
3. distributed synchronization keyed by the session, if the operational complexity is justified.

The chosen mechanism must be defined with the FastAPI team. Refresh correctness cannot be delegated to frontend process memory.

### 9.6 Logout

Logout SHOULD:

1. revoke/invalidate the refresh/session server-side when supported;
2. clear all auth cookies with matching cookie attributes;
3. clear sensitive TanStack Query state;
4. reset sensitive Zustand stores;
5. redirect to an unauthenticated route;
6. ensure subsequent BFF calls cannot reuse an old session.

### 9.7 Session projection

The browser may need a safe session model such as:

```text
user id
user display name
roles
permissions/capabilities
selected club or memberships
session expiry metadata when UX requires it
```

Expose that through a sanitized server-provided projection or `/api/session`. Never expose access/refresh tokens as part of it.

### 9.8 Authorization

Authentication answers “who is this?”. Authorization answers “may this identity perform this action on this resource?”.

Authorization MUST be enforced by FastAPI for every protected operation. BFF checks are useful for early rejection and UX but are not a substitute for backend authorization.

In a multi-club product, never trust `clubId` alone. The backend must verify that the authenticated principal is authorized for that specific club/resource.

---

## 10. CSRF, XSS and browser security

Cookie-based authentication changes the threat model: the browser automatically sends cookies, so CSRF protection is mandatory.

### 10.1 CSRF defense

For state-changing BFF endpoints, use defense in depth:

- explicit `SameSite` auth cookies;
- reject unsafe requests with an unexpected/missing `Origin` against a strict allowlist;
- optionally validate `Referer` as fallback where required by deployment policy;
- accept mutations only through intended HTTP methods;
- prefer JSON content types for JSON APIs and reject unexpected simple form content types;
- add an anti-CSRF token mechanism if the deployment, cross-site integration requirements or threat model make it necessary;
- never perform state changes through GET.

SameSite is useful but should not be the only conceptual defense for a high-value club administration application.

### 10.2 XSS

React escapes text output by default, but XSS is still possible.

MUST NOT:

- inject untrusted HTML with `dangerouslySetInnerHTML`;
- build script/URL HTML fragments from user data;
- use `eval`/dynamic code execution;
- trust rich text without sanitization.

If sanitized HTML is a real requirement, use a dedicated audited sanitizer and centralize the rendering component so the policy cannot be bypassed casually.

### 10.3 Content Security Policy

Deploy a CSP appropriate to the application. Prefer nonce/hash based strict policies where operationally possible. At minimum, explicitly control script, frame, object, connection and form destinations.

CSP SHOULD be rolled out with reporting/monitoring before strict enforcement if third-party integrations make immediate enforcement risky.

### 10.4 Security headers

At the edge/Next layer, define and test headers such as:

- `Content-Security-Policy`;
- `Strict-Transport-Security` in HTTPS production;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy`;
- `Permissions-Policy`;
- `frame-ancestors` in CSP, generally preventing unwanted framing;
- COOP/CORP/COEP only when compatible with integrations and intentionally required.

### 10.5 Open redirects

Any `returnTo`, `redirect`, or callback target supplied by the browser MUST be validated against an internal route allowlist or same-origin policy.

### 10.6 SSRF prevention

Because the BFF can perform server-side network calls, never allow untrusted values to control:

- request host;
- scheme;
- port;
- full backend URL.

Backend destinations should come from trusted configuration. User values may fill validated path/query parameters, not redefine the destination host.

---

## 11. Multi-tenancy and club context

A club management application is naturally multi-tenant. Treat tenant isolation as an architecture invariant, not a UI filter.

### 11.1 Tenant context

Every tenant-scoped operation should have an explicit club/tenant context. It may come from:

- route segment;
- selected club in the session;
- request parameter.

Regardless of source, FastAPI MUST authorize the current principal against the target club.

### 11.2 Query-key scoping

All TanStack Query keys for tenant-scoped data MUST include the effective club/tenant identity.

Bad:

```text
['bookings']
```

Good:

```text
['clubs', clubId, 'bookings', normalizedFilters]
```

When changing clubs, queries from the previous tenant must not be accidentally rendered in the new tenant context.

### 11.3 Client stores

Zustand state that is tenant-specific must either:

- include tenant identity as part of its state model; or
- be reset when tenant context changes.

### 11.4 Cache and authorization separation

Never rely on query-key separation as authorization. It prevents client cache confusion; it does not protect data. Authorization is server-side.


---

## 12. TanStack Query architecture

TanStack Query owns **remote/server state in the browser**. It is not a general-purpose state container.

### 12.1 Query ownership rules

Use TanStack Query for:

- lists and detail records from FastAPI through the BFF;
- server-derived permissions/session projections that must refresh;
- dashboard metrics;
- availability data;
- mutation lifecycle state;
- pagination/infinite data;
- cache invalidation/refetching;
- optimistic updates where safe.

Do NOT put the same data in Zustand after fetching it.

### 12.2 Query key factories

Every feature SHOULD own a typed query-key factory. Keys should be deterministic and hierarchical.

Conceptually:

```text
clubs.all
clubs.detail(clubId)
bookings.all(clubId)
bookings.list(clubId, normalizedFilters)
bookings.detail(clubId, bookingId)
```

Rules:

- include every input that materially changes the response;
- include tenant identity;
- normalize object filters so semantically equivalent filters produce stable keys;
- do not include access tokens;
- do not use display labels as identities;
- avoid ad-hoc string arrays scattered throughout components.

### 12.3 Query option factories

Prefer reusable feature-owned query option factories rather than duplicating `queryKey`, `queryFn`, `staleTime`, error behavior and select logic in many components.

This makes prefetching, hydration, invalidation and testing consistent.

### 12.4 `staleTime` is a product/data decision

Do not set one arbitrary global stale time for every endpoint.

Classify data by volatility and UX needs. Example categories:

- session/permissions — refreshed deliberately on auth/role transitions;
- near-real-time availability — short stale window;
- club configuration — medium/long stale window;
- reference catalogues — long stale window;
- immutable historical records — effectively infinite until explicit invalidation.

`gcTime` should be chosen independently from `staleTime`.

### 12.5 Avoid default refetch surprises

Define a deliberate policy for:

- refetch on window focus;
- refetch on reconnect;
- refetch on mount;
- polling.

Desktop administrative apps can remain open for hours, so stale data matters, but uncontrolled refetching can create significant backend load. Configure per data class rather than globally disabling freshness.

### 12.6 Cancellation

Query functions SHOULD consume TanStack Query's abort signal and propagate it to `fetch` so obsolete searches, route transitions and cancelled requests do not continue unnecessarily.

This is especially important for:

- type-ahead search;
- rapidly changing filters;
- large reports;
- availability lookup.

### 12.7 Mutation invalidation

After a successful mutation, choose deliberately between:

1. updating known cache entries directly from the mutation response;
2. invalidating a narrow related key set;
3. invalidating broader data only when required.

Avoid `invalidateQueries()` with overly broad prefixes after every mutation. Broad invalidation becomes expensive as the product grows.

### 12.8 Optimistic updates

Use optimistic UI only when:

- rollback is deterministic;
- conflict behavior is understood;
- the backend operation has a high success probability;
- showing a temporarily incorrect state is acceptable;
- concurrency semantics are clear.

For payments, destructive administrative operations, complex inventory transitions or permission changes, pessimistic confirmation is often safer.

### 12.9 Mutation retries

Automatic mutation retry SHOULD default to off unless the specific operation is idempotent and the backend supports safe retry semantics.

If retrying a create-like action, pair it with an idempotency key generated once per logical user action, not once per HTTP attempt.

### 12.10 Pagination and filtering

For large club datasets:

- paginate/filter/sort server-side;
- keep canonical filters in URL search params when users should be able to bookmark/share/refresh them;
- use Query keys derived from normalized filters;
- avoid loading an entire dataset into Zustand and filtering locally;
- preserve previous page data only where it improves UX without showing misleading tenant/filter results.

### 12.11 Prefetching and hydration

For routes where initial data materially improves first render:

1. create a request-local QueryClient on the server;
2. prefetch with a server-only FastAPI transport;
3. dehydrate into a `HydrationBoundary`;
4. let the client hook use the same query key but browser/BFF transport;
5. use a sensible non-zero `staleTime` so the browser does not immediately refetch identical data.

Do not create a global server QueryClient shared across users.

### 12.12 Do not let RSC and Query own the same live value

If a Server Component renders a value and a Client Component independently owns/refetches that same value through TanStack Query, they can diverge after client revalidation.

Choose one of two modes for a region:

**Server-owned region**
- Server Component fetches and renders the data.
- Refresh occurs through navigation/revalidation semantics.
- Do not create a second client Query owner for the same live value.

**Client-owned interactive region**
- Server Component may prefetch/dehydrate only.
- Client Query becomes the owner after hydration.
- Avoid separately rendering derived live values from the same query result in the surrounding Server Component.

### 12.13 Query errors

Normalize browser API failures into a typed application error model before they reach UI code. Components should reason about stable categories such as:

- unauthenticated;
- forbidden;
- validation;
- conflict;
- rate limited;
- not found;
- transient network;
- backend unavailable;
- unexpected.

Do not make every component inspect arbitrary HTTP status/body shapes.

---

## 13. Zustand architecture

Zustand exists for **client-only UI/application interaction state that does not belong to the server or URL**.

### 13.1 Appropriate Zustand state

Examples:

- sidebar collapsed/expanded state;
- global command palette visibility;
- multi-panel selection that is intentionally non-navigable;
- temporary cross-component wizard draft when route-local state is insufficient;
- UI preferences;
- modal coordinator when composition cannot solve it cleanly.

### 13.2 Inappropriate Zustand state

MUST NOT use Zustand as a second cache for:

- bookings;
- courts;
- members;
- club settings from FastAPI;
- session tokens;
- server permissions;
- lists already managed by TanStack Query;
- URL filters;
- form state that is local to one screen.

### 13.3 Small stores by concern

Prefer several small stores with clear ownership over one global application store.

A store should have:

- explicit state shape;
- actions that own mutations;
- selectors;
- a reset behavior when context/session changes;
- persistence only when justified.

### 13.4 Selectors and render performance

Components SHOULD subscribe to the smallest state slice they need. Avoid subscribing to an entire large store and destructuring many fields, which causes unnecessary rerenders.

### 13.5 SSR and hydration

Zustand must not use one global mutable server store shared across requests. That can leak one user's state into another request.

The simplest rule for this application is:

- keep most Zustand state client-only;
- where server-provided initial state is genuinely necessary, create/request-scope the store correctly and guarantee identical hydration output;
- do not read browser-only persisted state during server render in a way that creates hydration mismatch.

### 13.6 Persistence

If `persist` or local storage is added:

- persist only non-sensitive preferences/drafts;
- version the persisted shape;
- provide migration logic;
- handle corrupt/old storage safely;
- clear tenant/user-specific persisted state on logout when required;
- never persist tokens or privileged server data merely for convenience.

---

## 14. URL state architecture

Desktop applications frequently have filterable tables and dashboards. The URL should be considered an intentional state store for navigable state.

Use route/search parameters for values such as:

- selected date/date range;
- page number/cursor where shareable;
- filters;
- sort direction;
- active tab when deep-linking matters;
- selected club if the route model uses club identity;
- search query where users should be able to refresh/share it.

Benefits:

- browser back/forward works correctly;
- deep links work;
- refresh preserves context;
- support/debugging is easier;
- multiple tabs behave independently.

Parse search params at the boundary and normalize them into a canonical typed representation. Do not let every component parse arbitrary strings independently.

---

## 15. Zod and runtime validation

### 15.1 Static types versus runtime validation

TypeScript disappears at runtime. `openapi-typescript` gives compile-time guarantees against the known schema, but an HTTP response is still runtime data.

Zod should be used at **trust boundaries**, not sprayed over internal objects that are already type-safe.

### 15.2 Validate browser-controlled inputs

Use Zod for:

- form submission payloads;
- search params;
- route-derived values where needed;
- BFF JSON request bodies;
- imported files/CSV metadata if introduced;
- environment configuration;
- persisted client state migrations;
- complex discriminated form workflows.

### 15.3 Client validation is UX, backend validation is authority

A Zod schema in the frontend improves feedback and prevents malformed BFF requests. It does not replace FastAPI/Pydantic validation.

The server must reject invalid data even if the browser claims it validated successfully.

### 15.4 Avoid schema/type duplication

Do not manually define all of the following for the same concept unless they genuinely differ:

- interface;
- type alias;
- Zod schema;
- OpenAPI type;
- form type;
- API DTO type.

Where Zod defines an application-owned input model, infer its TypeScript type from the schema.

Where FastAPI OpenAPI defines a transport model, use the generated type at the transport boundary.

### 15.5 Response validation strategy

Validating every large internal backend response with manually duplicated Zod schemas can create maintenance burden and runtime cost. Use a risk-based strategy:

- compile-time generated OpenAPI types for all FastAPI calls;
- CI contract checks for schema drift/breaking changes;
- runtime Zod validation for high-risk data, externally sourced data, critical transformations or areas where corrupted payloads could cause harmful behavior;
- optional development/test response assertions for broader coverage.

If full runtime schema parity becomes a requirement, adopt generation from the same OpenAPI source rather than maintaining a second independent schema universe manually.

### 15.6 `safeParse` for user-facing errors

For expected invalid user input, prefer non-throwing validation flows such as `safeParse` so validation errors become explicit typed branches rather than exceptional control flow.

### 15.7 Cross-field rules

Put cross-field validation in one schema/domain validation unit rather than scattering checks across input `onChange` callbacks.

### 15.8 Time, date and money rules

Validation must account for business-sensitive primitives:

**Dates/times**
- API instants should be ISO 8601 with timezone/UTC semantics clearly defined;
- a calendar date such as `2026-08-12` is not the same type of concept as an instant;
- a local club opening time is not automatically a UTC instant;
- DST boundaries must be tested.

**Money**
- do not perform authoritative currency calculations with binary floating point;
- use integer minor units or backend-defined decimal-string contracts;
- currency code must be explicit when multiple currencies are possible.

**Identifiers**
- treat IDs as opaque values;
- do not infer meaning from string structure unless the contract guarantees it.

---

## 16. OpenAPI and generated API type architecture

The FastAPI OpenAPI specification SHOULD be the canonical backend transport contract.

### 16.1 Generated files are generated

`openapi-typescript` output MUST:

- live in a clearly generated directory;
- never be manually edited;
- be reproducible from a pinned schema artifact/version;
- be regenerated in CI or checked for drift;
- be excluded from casual feature-domain imports.

### 16.2 Keep generated backend types at the boundary

Do not allow UI components to import FastAPI's generated `paths` and response types directly everywhere.

Instead:

```text
FastAPI generated types
        ↓
server FastAPI client / feature API adapter
        ↓
frontend feature contract/model
        ↓
query hooks / UI
```

This prevents backend transport details from becoming the entire frontend domain model.

### 16.3 BFF contracts are frontend contracts

The BFF may deliberately:

- combine several backend calls;
- remove sensitive fields;
- normalize error shapes;
- reduce payloads;
- adapt backend naming/structure where the UI contract genuinely differs.

Therefore the browser-facing BFF contract is conceptually distinct from the FastAPI contract even when some endpoints initially pass through similar shapes.

Do not accidentally erase the architectural purpose of the BFF by exposing every backend DTO unchanged directly to the entire client codebase.

### 16.4 Schema generation pipeline

Recommended pipeline:

```text
FastAPI OpenAPI artifact
        ↓
OpenAPI lint/validation
        ↓
openapi-typescript generation
        ↓
TypeScript compile
        ↓
contract tests
        ↓
build
```

The production build SHOULD NOT depend on reaching a live backend to download its OpenAPI schema. Build from a versioned/pinned artifact supplied by the backend pipeline or committed according to team policy.

### 16.5 Breaking-change gate

CI SHOULD compare backend OpenAPI changes and detect incompatible changes before rollout, including:

- removed endpoints;
- removed fields;
- optional → required changes;
- incompatible enum changes;
- type changes;
- response/status shape changes.

Frontend and backend deployment strategy must support backward-compatible rolling deployments. Avoid requiring both services to switch schemas at the exact same millisecond.

### 16.6 TypeScript safety recommendation from openapi-typescript

Enable `noUncheckedIndexedAccess` so dictionary/additional-property lookups correctly force handling of missing keys.

### 16.7 Avoid cosmetic runtime remapping

Do not add broad snake_case ↔ camelCase remapping only for aesthetics. It introduces runtime transformation, duplicate type concerns and maintenance overhead. Adapt fields only where the frontend contract genuinely benefits from a different semantic model.

---

## 17. TypeScript production rules

### 17.1 Compiler strictness

At minimum:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "useUnknownInCatchVariables": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true
  }
}
```

Exact compatibility with the project's Next.js/TypeScript versions should be verified, but the direction should remain maximum practical strictness.

### 17.2 `any`

Production feature code SHOULD have a near-zero tolerance for `any`.

Use:

- `unknown` at untrusted boundaries;
- generics where type relationships are real;
- Zod narrowing;
- generated OpenAPI types;
- discriminated unions.

If `any` is unavoidable for a third-party integration, isolate it in one adapter and document the reason.

### 17.3 Type assertions

Avoid `as SomeType` as a shortcut around compiler errors. Assertions are promises to the compiler and can hide contract bugs.

When an assertion is necessary at a proven boundary, localize it and test it.

### 17.4 `satisfies`

Prefer `satisfies` when you want to verify an object conforms to a contract without losing useful literal inference.

### 17.5 Domain discriminated unions

Use discriminated unions for meaningful state machines rather than multiple booleans that permit impossible combinations.

Bad conceptual state:

```text
isLoading=true
isSuccess=true
hasError=true
```

Prefer mutually exclusive modeled states where a custom state machine is genuinely needed. For server request lifecycle, use TanStack Query's state rather than recreating it in Zustand.

### 17.6 Exhaustiveness

Critical switches over domain states/status values SHOULD be exhaustive so new backend/frontend states generate compile failures rather than silent UI gaps.

### 17.7 Naming

Name by domain meaning, not implementation mechanism.

Prefer:

- `BookingTable`
- `useBookingFilters`
- `cancelBooking`

over vague names such as:

- `DataComponent`
- `CommonService`
- `Helper2`
- `useStoreData`.

### 17.8 Utility discipline

A helper belongs in `shared/lib` only if it is truly domain-independent. A booking calculation belongs in the booking feature even if two booking screens use it.

---

## 18. Browser API client design

The browser-side API client SHOULD be intentionally small because it talks only to same-origin BFF endpoints.

Responsibilities:

- serialize typed request input;
- apply headers such as `Content-Type`;
- pass `AbortSignal`;
- parse expected response payload;
- normalize HTTP/network errors;
- carry request ID from responses when exposed;
- never handle raw tokens.

It SHOULD NOT:

- silently retry unsafe mutations;
- contain feature business logic;
- store global mutable response data;
- know the FastAPI origin;
- attach Authorization bearer tokens.

### 18.1 Centralized 401 handling

Because refresh is BFF-owned, the browser should normally see a terminal 401 only when the session cannot be recovered.

Centralize behavior for terminal unauthenticated responses so multiple features do not invent different logout flows.

Do not redirect on every arbitrary query error; preserve error semantics and user context where possible.

### 18.2 Error envelope

Define one stable browser-facing error contract, for example conceptually:

```text
{
  error: {
    code: "BOOKING_CONFLICT",
    message: "...safe user-facing/default message...",
    fieldErrors?: ...,
    details?: ...safe structured details...,
    requestId: "..."
  }
}
```

The exact shape may differ. The important rule is that clients reason about stable application error codes rather than backend exception strings.

---

## 19. FastAPI server client design

The server-only FastAPI client is infrastructure, not a global dumping ground.

It SHOULD centralize:

- base URL from validated server environment;
- TLS/network behavior supplied by deployment platform;
- timeout defaults/endpoint overrides;
- generated OpenAPI typing;
- request IDs/tracing;
- authorization header construction;
- explicit safe header forwarding;
- common response/error parsing;
- metrics.

Feature-specific endpoint calls SHOULD live in the corresponding feature's server/API adapter so the central client does not become a 5,000-line `apiService.ts`.

### 19.1 `server-only`

Any module capable of reading tokens, secrets or the FastAPI base URL MUST be impossible to import into client bundles. Use explicit server-only module boundaries and lint checks.

### 19.2 Secrets

Server secrets MUST come from deployment secret/configuration systems. Never hardcode them, commit them, print them, or mirror them to `NEXT_PUBLIC_*` variables.

---

## 20. Environment and configuration architecture

### 20.1 Separate server and public configuration

Create distinct validated schemas:

**Server-only**
- FastAPI origin;
- auth/cookie configuration;
- observability credentials;
- internal service secrets;
- feature service endpoints.

**Browser-safe public**
- only values intentionally embedded in the client bundle.

Anything named `NEXT_PUBLIC_*` should be treated as public information.

### 20.2 Validate on startup/build

Use Zod to fail fast when required configuration is missing or malformed. Do not discover a malformed API URL only when a user opens a rarely used screen.

### 20.3 Build-time versus runtime values

Understand which Next.js values are embedded at build time and which are read at server runtime. The deployment strategy should avoid rebuilding only to change a server-private endpoint when runtime configuration can support it.

Conversely, public client variables are often bundled and should not be expected to change dynamically after build without an explicit runtime-config pattern.

### 20.4 Environment parity

Keep development, test, staging and production configuration shapes identical. Differences should be values, not entirely different code paths.

---

## 21. Forms and command workflows

### 21.1 Boundary model

A form flow should look like:

```text
raw input
  ↓
Zod validation/normalization
  ↓
typed command DTO
  ↓
TanStack mutation
  ↓
BFF request validation
  ↓
FastAPI authoritative validation/business rules
```

### 21.2 Prevent duplicate submissions

Buttons disabling during submission is useful UX but not a correctness guarantee. Users can double-click, retry, open two tabs or experience network ambiguity.

For operations where duplicates matter, use backend idempotency.

### 21.3 Field errors

Define a stable mapping from backend validation/domain errors to form fields or form-level errors. Do not expose raw Pydantic/internal error objects throughout component code.

### 21.4 Unsaved changes

For complex club forms:

- track dirty state locally;
- warn on destructive navigation only when justified;
- avoid persisting sensitive drafts casually;
- if drafts must survive refresh/session, explicitly design storage/versioning and tenant scoping.

### 21.5 Multi-step forms

For multi-step wizards, choose one owner:

- route state when each step is navigable/deep-linkable;
- a feature-local form provider/store when transient;
- backend draft resource when the workflow must survive devices/sessions.

Do not choose Zustand by default for every wizard.

---

## 22. Error architecture

Errors should have a stable path from FastAPI to the final UI.

### 22.1 Error taxonomy

Create explicit application categories such as:

- `UnauthenticatedError` / session expired;
- `ForbiddenError`;
- `NotFoundError`;
- `ValidationError`;
- `ConflictError`;
- `RateLimitError`;
- `DownstreamUnavailableError`;
- `TimeoutError`;
- `UnexpectedError`.

Feature-specific domain codes sit beneath these categories, e.g. `COURT_ALREADY_BOOKED`.

### 22.2 Status mapping

BFF status codes should be semantically meaningful and consistent. Do not turn every FastAPI failure into 200 with `{ success: false }`, and do not turn every failure into generic 500.

### 22.3 Safe messages

Separate:

- stable machine code;
- safe user-facing message;
- internal diagnostic context.

Internal exception messages, SQL errors, stack traces and token details must stay server-side.

### 22.4 Request IDs

Unexpected errors shown to a user/support team SHOULD include a safe correlation/request ID so logs/traces can be located without exposing internal details.

### 22.5 Recovery behavior

Design recovery based on category:

- validation → show field/context error;
- conflict → refresh affected data and explain change;
- 401 → centralized session expiry flow;
- 403 → permission UI;
- transient network → retry affordance;
- 5xx → preserve user input where safe and show retry/support path.

---

## 23. React component design

### 23.1 Component responsibilities

Prefer three conceptual categories:

**Route/composition components**
- arrange feature regions;
- pass route/search context;
- establish Suspense/error boundaries.

**Feature components**
- understand booking/court/member concepts;
- call feature hooks;
- implement feature UX.

**Shared UI primitives**
- buttons, dialogs, table primitives, inputs, typography;
- no booking-specific imports.

### 23.2 Avoid container/presentational dogma

Do not force every component into a duplicated `Container` + `View` pair. Split when it improves testing, reuse or conceptual clarity.

### 23.3 Effects

`useEffect` SHOULD be reserved for synchronization with external systems, not for ordinary derivation.

Avoid effects that:

- copy props into state;
- copy Query data into Zustand;
- calculate values that can be derived during render;
- perform routine server fetching that belongs in TanStack Query;
- chain application workflows through many flags.

### 23.4 Memoization

Do not use `useMemo`, `useCallback` and `memo` everywhere pre-emptively. Optimize measured or structurally obvious render bottlenecks. Incorrect dependency logic creates bugs and abstraction noise.

### 23.5 Stable identity

List keys MUST be stable domain IDs, not array indices when ordering/insertion can change.

### 23.6 Controlled complexity

When a component grows to manage unrelated concerns—data orchestration, table filtering, dialogs, mutation state, export and permissions—split by responsibility before it becomes untestable.

---

## 24. Accessibility and desktop UX

Production readiness includes accessibility.

### 24.1 Baseline

The application SHOULD target WCAG 2.2 AA behavior unless product/legal requirements dictate otherwise.

Ensure:

- semantic HTML first;
- keyboard operability;
- visible focus;
- correctly associated labels;
- accessible names for icon buttons;
- dialog focus trapping/restoration;
- table semantics;
- non-color-only status communication;
- appropriate live regions for async feedback;
- sufficient contrast;
- reduced-motion respect where animation is used.

### 24.2 Desktop does not mean mouse-only

Club staff may use keyboard-heavy workflows. Tables, filters, forms and commands should be efficient without requiring precise mouse interactions.

### 24.3 Loading states

Prefer contextual skeletons/progress indicators over blank pages. Avoid layout shifts where practical.

### 24.4 Destructive operations

Use confirmation patterns proportional to the risk. Do not confirm every harmless action, but make irreversible/high-impact actions explicit and resistant to accidental clicks.

### 24.5 Permission UX

Hide or disable unavailable actions for clarity, but never treat hidden UI as security. The server remains authoritative.

---

## 25. Internationalization, locale and timezone correctness

Even if the initial market is one country, architecture SHOULD avoid hard-coding assumptions that become expensive later.

### 25.1 Locale formatting

Use locale-aware formatting for:

- dates;
- times;
- numbers;
- currency;
- pluralization.

Do not concatenate translated sentence fragments in ways that cannot be reordered by language.

### 25.2 Club timezone versus user timezone

A club resource often has a business timezone. Make the distinction explicit between:

- UTC instant;
- club-local time;
- browser/user-local time;
- date-only business value.

Booking schedules should generally be reasoned about in the club's configured timezone, while transport instants can remain UTC.

### 25.3 DST tests

Test scheduling/cancellation/time-window behavior around daylight saving transitions where relevant.

---

## 26. Performance architecture

Performance should be budgeted and measured, not guessed.

### 26.1 Server/client boundary as a bundle tool

The largest architectural performance lever in App Router is preventing unnecessary code from entering the client bundle.

- default to Server Components;
- keep `'use client'` boundaries narrow;
- keep server-only libraries out of client modules;
- dynamically import large client-only capabilities when they are not needed initially.

### 26.2 Avoid waterfalls

On the server:

- initiate independent calls early;
- use parallel requests when data is independent;
- use Suspense to stream independently resolvable regions.

On the client:

- prefetch likely-next Query data when justified;
- avoid child-after-parent sequential fetching when dependencies do not require it.

### 26.3 Tables and large datasets

Do not render tens of thousands of rows because the browser technically can.

Use:

- backend pagination;
- cursor pagination for unstable/high-volume collections when appropriate;
- server sorting/filtering;
- row virtualization when profiling shows rendering is the bottleneck;
- memoization only where measured.

### 26.4 Search

For remote type-ahead:

- debounce sensibly;
- cancel obsolete requests;
- enforce minimum query length where useful;
- cache by normalized query;
- do not send a request on every keystroke without control.

### 26.5 Asset optimization

Use Next.js-supported image/font optimization where applicable. Avoid loading large icon libraries or design-system packages wholesale when selective imports are possible.

### 26.6 Bundle budgets

CI SHOULD track client bundle growth for critical routes. Define a budget or at least a regression threshold so a small feature cannot accidentally add hundreds of kilobytes to every page.

### 26.7 Web Vitals

Measure production experience, especially:

- LCP;
- INP;
- CLS;
- route transition latency;
- application-specific interaction latency for high-frequency workflows.

### 26.8 Performance before abstraction

Do not introduce client caches, memoization or persistence solely because they sound fast. Each cache creates invalidation complexity. Measure before adding layers.

---

## 27. Caching strategy across layers

This architecture contains several possible caches:

1. FastAPI/backend/database caches;
2. CDN/Next caching;
3. Server Component/data cache behavior;
4. BFF Route Handler responses;
5. TanStack Query browser cache.

Without explicit ownership, these layers can return contradictory stale data.

### 27.1 Default rule for authenticated operational data

For mutable authenticated club data:

- backend is authoritative;
- BFF response is generally not shared-cacheable;
- TanStack Query handles browser freshness;
- mutations explicitly update/invalidate relevant Query data.

### 27.2 Public/reference data

Only cache more aggressively when data is:

- non-sensitive;
- shared across users;
- safe when stale for a known period;
- invalidated by a documented mechanism.

### 27.3 Never cache by accident

Personalized response caching must vary correctly by identity/tenant or, preferably for the BFF, be disabled. A cache leak is a data breach, not a minor bug.

### 27.4 Cache invalidation contract

For every added cache, document:

- key;
- owner;
- TTL;
- invalidation event;
- maximum tolerated staleness;
- tenant/user scope;
- failure behavior.

If those cannot be answered, do not add the cache yet.

---

## 28. Concurrency and idempotency

Web UIs create concurrent operations naturally: multiple tabs, double clicks, retries, refetches and parallel dashboard requests.

### 28.1 Frontend locks are not authoritative

Disabling a button or setting `isPending` helps UX but does not prevent duplicate backend execution.

### 28.2 Idempotency keys

For commands where duplicate execution is harmful, define an idempotency contract with FastAPI.

The key should:

- represent one logical user intent;
- remain identical across retries of that intent;
- be generated before the first attempt;
- be scoped and retained server-side for a defined period;
- return the original result or a deterministic conflict response.

### 28.3 Optimistic concurrency

For editing resources that can change concurrently, prefer backend-supported versioning/ETag/revision fields where needed. The UI can then surface a conflict instead of silently overwriting newer data.

### 28.4 Race-aware UI

Examples to test:

- court becomes unavailable after screen load;
- another staff member changes a booking;
- permissions are revoked while the tab is open;
- two tabs submit the same operation;
- refresh token rotates while many queries refetch;
- club context changes while previous tenant requests are in flight.

---

## 29. Testing strategy

A senior test strategy does not maximize test count. It maximizes confidence at the cheapest reliable layer.

### 29.1 Test layers

Recommended layers:

1. **Type/static checks** — TypeScript, lint/import boundaries, generated contract drift.
2. **Unit tests (Vitest)** — pure logic, schemas, adapters, state transitions, query-key factories.
3. **Component/integration tests** — meaningful interactive UI behavior with realistic boundaries.
4. **BFF/API integration tests** — auth, validation, error mapping, cookies, backend adapter behavior.
5. **Contract tests** — FastAPI OpenAPI compatibility.
6. **E2E (Playwright)** — critical user journeys across the deployed application.

### 29.2 What to unit test with Vitest

Strong candidates:

- Zod schemas and normalization;
- money/date utility rules;
- permission-display helpers where non-authoritative UI logic exists;
- filter/search-param parsing;
- Query key factories;
- API error normalization;
- state reducers/state machines;
- feature-local Zustand actions;
- BFF helper functions;
- mapping backend DTOs to UI models;
- retry/idempotency helper behavior.

Avoid unit tests that simply assert that a component calls a hook because its implementation currently does so.

### 29.3 Component tests

If not already present, add an appropriate React testing layer such as React Testing Library or Vitest Browser Mode depending on project preference.

Test user-observable behavior:

- form validation;
- loading/error/success states;
- keyboard behavior;
- permission-dependent UI;
- mutation feedback;
- dialog behavior;
- filter interactions.

### 29.4 BFF tests

Test route/security behavior, including:

- unauthenticated request rejected;
- forbidden tenant/resource rejected;
- invalid input rejected before backend call where intended;
- correct Authorization constructed server-side;
- browser cookies are not blindly forwarded;
- refresh success and refresh failure;
- cookie flags on login/refresh/logout;
- backend timeout mapping;
- backend conflict/error mapping;
- request ID propagation;
- unsafe Origin/CSRF rejection;
- unsupported content type rejection;
- no backend internal error leakage.

### 29.5 OpenAPI contract tests

CI should prove:

- the schema artifact is valid;
- generated types are current;
- generated output has no uncommitted drift if committed;
- incompatible backend changes are detected;
- critical fixtures still satisfy expected response contracts.

### 29.6 Playwright E2E philosophy

E2E tests should cover high-value journeys, not every visual permutation.

Core candidates:

- login/logout;
- expired session/refresh behavior;
- club switching/tenant isolation;
- role/permission boundaries;
- create/edit/cancel booking flows;
- conflict when a resource changes concurrently;
- critical member/court management flow;
- navigation/deep-link filters;
- terminal backend error/recovery;
- double-submit behavior;
- security-sensitive actions.

### 29.7 Playwright resilience

Follow these rules:

- tests are isolated;
- each test owns its data/state;
- use user-facing locators (`getByRole`, labels, text) before CSS/XPath;
- do not use arbitrary sleeps;
- rely on Playwright auto-waiting/web-first assertions;
- mock only external systems you do not control when appropriate;
- use traces/screenshots/videos on CI failure/retry;
- run critical flows against Chromium, Firefox and WebKit unless the supported browser policy is intentionally narrower.

### 29.8 Test data

Create deterministic test fixtures/factories. Avoid shared mutable staging data that makes tests order-dependent.

For E2E, preferably provision isolated users/clubs/resources per worker/test or provide backend test APIs/fixtures designed for isolation.

### 29.9 Flaky test policy

Flaky tests are defects. Quarantine only temporarily with an owner and deadline. Do not normalize rerunning tests until they pass.

### 29.10 Coverage

Use coverage as a signal, not the goal. Enforce meaningful thresholds primarily on pure business/utility modules and critical infrastructure. A 95% line-coverage target with weak assertions is less valuable than targeted high-risk coverage.

Vitest's V8 coverage is a sensible default when compatible with the test environment.

---

## 30. Security testing

Security requirements should have automated tests where practical.

Test at least:

- auth cookies are HttpOnly/Secure/SameSite as expected in production-like environments;
- logout invalidates session behavior;
- 401/403 are not confused;
- tenant A cannot read tenant B resources;
- mutation endpoints reject disallowed origins;
- redirect targets cannot leave the allowlisted origin;
- CSP/security headers exist on deployed responses;
- sensitive fields are absent from browser payloads;
- access/refresh token strings never appear in rendered HTML/client storage;
- generic BFF URL forwarding is impossible;
- unexpected FastAPI errors do not leak internals.

Run dependency/security scanning in CI and maintain a defined remediation SLA for critical vulnerabilities.

---

## 31. Observability architecture

Observability must connect the browser, Next.js BFF and FastAPI so a production failure can be diagnosed end-to-end.

### 31.1 Correlation IDs

Every request SHOULD have a correlation/request ID.

Flow:

```text
Browser request
  ↓
BFF request ID / trace context
  ↓
FastAPI
  ↓
logs + metrics + trace spans
```

If an upstream trusted ID exists, validate its format/length before using it. Otherwise generate one.

### 31.2 Distributed tracing

Prefer W3C trace context and OpenTelemetry-compatible instrumentation so BFF latency can be decomposed into:

- Next.js handling time;
- authentication/refresh time;
- FastAPI network latency;
- backend processing.

### 31.3 Server logs

Use structured logs, not free-form `console.log` as the long-term production strategy.

Useful fields:

- timestamp;
- environment/version;
- request ID/trace ID;
- route template;
- method;
- status;
- latency;
- FastAPI endpoint template;
- tenant ID when policy allows and appropriately classified;
- authenticated principal pseudonymous identifier where allowed;
- error code;
- deployment instance/revision.

Never log:

- access/refresh tokens;
- passwords;
- Authorization headers;
- full cookie headers;
- payment secrets;
- unnecessary PII;
- raw sensitive request bodies.

### 31.4 Metrics

Track at least:

**BFF**
- request rate;
- p50/p95/p99 latency;
- 4xx/5xx rate by route;
- timeout rate;
- FastAPI dependency latency;
- refresh attempt/success/failure rate;
- rate-limit events.

**Browser**
- Web Vitals;
- uncaught errors;
- failed critical API requests;
- route transition latency;
- feature-specific interaction metrics where product value justifies them.

### 31.5 Error reporting

Use an error-reporting platform or OpenTelemetry-compatible pipeline for browser and server errors. Release/version identifiers and source maps are essential for actionable stack traces.

Source maps must be managed so they support debugging without unintentionally exposing private source artifacts publicly.

### 31.6 SLOs

Define service-level objectives for critical user flows, not only infrastructure uptime. Examples:

- login success availability;
- booking-management API availability;
- p95 dashboard interaction response;
- error-free session rate.

Alert on user-impacting symptoms, not only CPU/memory.

---

## 32. Operational resilience

### 32.1 Horizontal scaling

Assume any two requests may hit different Next.js instances.

Therefore do not rely on module globals for:

- auth session correctness;
- refresh locking;
- rate-limit correctness;
- tenant state;
- workflow state;
- idempotency;
- durable cache invalidation.

### 32.2 Backend outage behavior

Define UX for FastAPI degradation:

- short timeout;
- safe retry affordance;
- preserve unsaved form input where possible;
- avoid mass auto-retry storms;
- show a request ID;
- distinguish offline/browser network failure from backend 5xx when useful.

### 32.3 Rate limiting

Rate limiting is best enforced at infrastructure/backend layers with a shared/distributed view, but the BFF may add route/identity-specific controls for expensive endpoints.

Do not rely on a process-local JavaScript counter in a horizontally scaled deployment.

### 32.4 Background work

Long-running work SHOULD NOT execute synchronously inside a Route Handler if it can exceed normal request lifecycle expectations.

Examples:

- bulk imports;
- report generation;
- large notifications;
- reconciliation.

Create a backend job and poll/subscribe to status through the BFF.

### 32.5 Graceful deployment

BFF and FastAPI should tolerate rolling deployments with temporarily mixed versions. API changes should be backward compatible over the rollout window.

---

## 33. CI/CD quality gates

A merge to the main branch SHOULD require a reproducible quality pipeline.

Recommended order:

```text
1. install with frozen lockfile
2. generated-file / OpenAPI contract check
3. TypeScript typecheck (`tsc --noEmit`)
4. lint + architecture boundary rules
5. unit/component tests
6. production Next.js build
7. dependency/security checks
8. Playwright critical tests against preview/test deployment
9. artifact/image signing/metadata as required
10. deployment + post-deploy smoke checks
```

### 33.1 Pin the toolchain

Pin/document:

- Node.js major/minor strategy;
- package manager and version;
- lockfile;
- Next.js exact patch version;
- React exact patch version;
- CI action/tool versions.

“Next.js 15” is not precise enough for production security.

### 33.2 Security patch baseline

Because React Server Components had critical security advisories in late 2025, production MUST run patched React/Next.js versions and continuously track upstream security advisories.

For the original React2Shell-related Next.js advisory, patched 15.x lines included versions such as 15.0.5, 15.1.9, 15.2.6, 15.3.6, 15.4.8 and 15.5.7. That historical list is **not a substitute for using the newest supported patched release available to the project now**. Security updates published after those versions must also be incorporated.

Treat framework patch upgrades as normal security maintenance, not optional feature work.

### 33.3 Dependency updates

Use automated dependency-update tooling and define an update policy:

- security patches fast-tracked;
- normal patches batched safely;
- minor/major upgrades tested intentionally;
- lockfile reviewed;
- changelogs/security advisories read for framework/runtime packages.

### 33.4 Preview environments

For significant UI/BFF changes, ephemeral or shared preview environments SHOULD provide:

- production-like auth cookie behavior;
- FastAPI-compatible test backend;
- Playwright execution;
- observability tags by PR/revision.

### 33.5 Build once, promote where possible

Prefer promoting the same tested build artifact across environments. Be conscious that browser-public configuration may be baked into Next.js output; design runtime configuration accordingly.

### 33.6 Rollback

Every deployment strategy needs a known rollback path. Database/backend contract changes must remain compatible with the frontend version that may be restored.

---

## 34. Architecture fitness functions

Important architectural rules SHOULD be executable.

Examples:

- lint forbids `features/*` deep imports;
- lint forbids client modules from importing `server-only` code;
- lint forbids generated FastAPI types from UI directories;
- CI fails if OpenAPI generation has drift;
- CI fails on TypeScript errors;
- CI checks for forbidden `any` patterns where practical;
- bundle-size regression budget;
- security header E2E checks;
- tenant-isolation E2E tests;
- architecture dependency-cycle check;
- no committed secrets scan.

This is how architecture survives team growth.

---

## 35. Code ownership and parallel development

For a project developed by multiple teams or AI agents, ownership boundaries are especially important.

### 35.1 Feature ownership

Each feature should have a clear owner/responsible team for:

- browser contract;
- Query hooks;
- feature UI;
- feature tests;
- associated BFF handlers/server adapters;
- coordination with backend contract changes.

### 35.2 Shared/platform ownership

Changes to:

- API client primitives;
- auth flow;
- query client defaults;
- design system;
- security middleware;
- error contract;
- generated contract pipeline;
- observability;

should receive platform/architecture review because they affect many features.

### 35.3 Avoid shared-file hotspots

Parallel agents/developers collide when every feature edits:

- one giant API service;
- one root Zustand store;
- one routes configuration file;
- one global types file;
- one global test fixture.

Feature-local files reduce merge conflicts and accidental coupling.

### 35.4 ADRs

Record significant decisions in `docs/adr/`, including:

- auth token/session strategy;
- BFF contract rules;
- Server Component/TanStack Query ownership rules;
- caching policy;
- tenant routing model;
- error envelope;
- OpenAPI versioning workflow;
- observability vendor/integration;
- form library if one is introduced;
- feature flag solution if introduced.

An ADR should explain context, decision, consequences and alternatives—not become a long implementation tutorial.

---

## 36. Recommended linting and static-quality rules

Even if not all tools are currently declared in `package.json`, production should enforce equivalent behavior.

### 36.1 Core rules

Enforce:

- Next.js recommended lint rules;
- React hooks rules;
- no floating/unhandled promises where tooling allows;
- no unused imports/variables;
- import ordering policy only if it does not create noise;
- restricted imports for architecture boundaries;
- no `console.log` in production paths except approved logger wrapper;
- no direct browser FastAPI URL use;
- no `localStorage` auth token patterns;
- no `dangerouslySetInnerHTML` outside an approved sanitizer component;
- exhaustive dependency rules for hooks;
- TanStack Query ESLint plugin rules where compatible.

### 36.2 Formatting

Formatting should be automated and non-debatable. CI should validate it or developers should apply it automatically pre-commit/editor-side.

### 36.3 Do not block delivery with stylistic trivia

Static rules should primarily prevent correctness, security, architecture and maintainability defects. Avoid a lint configuration dominated by subjective formatting rules already handled by a formatter.

---

## 37. Data privacy and sensitive-data handling

### 37.1 Data minimization

The BFF SHOULD return only fields the browser needs. Do not expose backend records wholesale “just in case”.

### 37.2 Client-side sensitivity

Anything sent to the browser must be considered visible to the user/device regardless of UI visibility. Do not send privileged data and then hide it with CSS or role checks.

### 37.3 Logging/analytics

Define a data classification policy for telemetry. User IDs, emails, payment details, free text and operational notes may have different retention/redaction requirements.

### 37.4 Query cache lifecycle

On logout or identity/tenant boundary changes, clear or correctly partition sensitive cached data so the next user/context cannot see the previous context's data.

### 37.5 Browser persistence

Persist only what is required. Local storage has no HttpOnly protection and survives sessions; treat it accordingly.

---

## 38. Feature flags and configuration changes

If the application needs staged rollouts, add a deliberate feature-flag system rather than scattering environment checks across components.

Rules:

- flag evaluation semantics must be centralized;
- security/authorization must never depend solely on a client flag;
- stale flags must be retired;
- variants should be observable for debugging;
- server/client flag values must not diverge unexpectedly during hydration;
- flags should not permanently fork architecture.

Do not introduce a flag platform until rollout needs justify it, but reserve an architectural location for it under `platform/config` or an equivalent boundary.

---

## 39. Design system and shared UI architecture

A scalable desktop app benefits from a small, intentional design system.

### 39.1 Shared UI primitives

`shared/ui` may contain:

- button;
- input;
- select;
- dialog;
- tooltip;
- table primitives;
- badge;
- typography;
- form field layout;
- loading/error primitives.

They should not know what a booking or court is.

### 39.2 Feature composites

A `BookingStatusBadge` or `CourtAvailabilityGrid` belongs to the feature, even if composed from shared primitives.

### 39.3 Accessibility built into primitives

Shared primitives should encode focus management, ARIA semantics and keyboard behavior once so feature teams do not reimplement accessibility incorrectly.

### 39.4 No uncontrolled “common” directory

Directories named `common`, `misc`, `helpers` or `utils` tend to become architecture bypasses. Prefer explicit ownership and move a helper to shared only after genuine cross-feature reuse appears.

---

## 40. API evolution and frontend compatibility

### 40.1 Additive first

Prefer backend changes that are backward compatible:

- add optional fields;
- add endpoints;
- support old and new values during rollout;
- avoid immediate renames/removals.

### 40.2 Enum evolution

Enums are a common rolling-deployment risk. If the backend can add values independently, UI behavior must define what happens to an unknown/new value instead of assuming every runtime value is known forever.

Where backend and frontend deploy atomically, strict enums may be acceptable; where deployments are decoupled, design forward compatibility deliberately.

### 40.3 Consumer-driven behavior

For critical contracts, maintain fixtures or contract tests that prove the backend still provides fields/semantics the club UI relies on.

### 40.4 Versioning

Do not version the entire API reflexively for every additive change. Introduce endpoint/API versions when semantic incompatibility genuinely requires parallel contracts.

---

## 41. Recommended architecture for authentication-aware layouts

A common robust pattern:

```text
Root layout
  ↓
public/authenticated route group
  ↓
authenticated server layout resolves safe session
  ↓
redirect if no valid session (UX gate)
  ↓
render shell with sanitized session info
  ↓
client providers for Query/UI state
```

Important: the layout redirect is not the authorization boundary. BFF/FastAPI checks remain mandatory.

### 41.1 Providers

Keep the root provider composition small. Typical client providers may include:

- TanStack Query provider;
- error/telemetry client boundary;
- design-system theming if client state is required.

Do not create a provider for every feature merely because Context exists.

---

## 42. QueryClient lifecycle

### 42.1 Browser

Create one stable browser QueryClient for the application lifecycle. Do not recreate it on each render.

### 42.2 Server

For SSR/RSC prefetching, use request-safe QueryClient creation. Never share one QueryClient across different users on the server.

### 42.3 Default options

Global defaults should be conservative and overridden by features:

- non-zero SSR hydration `staleTime`;
- mutation retries disabled unless overridden;
- query retries bounded and error-aware;
- sensible garbage collection;
- focus/reconnect policy chosen explicitly.

### 42.4 Query Devtools

Development-only Query devtools may be useful, but ensure they are not unnecessarily shipped/enabled in production.

---

## 43. Route Handler design template

Every BFF handler SHOULD conceptually follow this sequence:

```text
Request received
  ↓
request context / trace ID
  ↓
method + content-type + origin/CSRF checks
  ↓
authentication/session resolution
  ↓
input parse/validation
  ↓
authorization context
  ↓
feature server operation
  ↓
FastAPI call with timeout
  ↓
backend result/error normalization
  ↓
minimal response DTO
  ↓
explicit cache/security headers
  ↓
structured telemetry
```

This sequence should be implemented through small reusable primitives, not copied as hundreds of lines into every handler.

Be careful not to create a magical generic handler abstraction that hides endpoint behavior. Security-relevant behavior must remain inspectable.

---

## 44. Recommended server-side abstraction depth

A frontend BFF does not need full enterprise backend layering for every endpoint.

Use the lightest structure that preserves responsibilities:

```text
route.ts
   ↓
feature server operation (only when orchestration is non-trivial)
   ↓
feature FastAPI adapter
   ↓
platform FastAPI client
```

For a trivial pass-through read, `route.ts → feature API adapter → platform client` may be enough.

Create an application/use-case layer only when it has meaningful orchestration such as:

- combining backend endpoints;
- permission-dependent adaptation;
- multi-step command preparation;
- response composition;
- cross-cutting idempotency behavior.

Avoid empty layers that only forward arguments one-to-one.

---

## 45. Anti-patterns to ban

The following patterns SHOULD be explicitly rejected in review:

### Architecture
- giant `components/`, `services/`, `hooks/`, `utils/` folders with no feature ownership;
- a single `apiService.ts` for every endpoint;
- a single global Zustand store;
- feature deep imports;
- circular feature dependencies;
- business rules hidden in page components;
- arbitrary abstractions with one implementation and no invariant.

### State
- Query response copied into Zustand;
- URL filters mirrored into Zustand and React state;
- auth tokens in JavaScript-accessible storage;
- server request state implemented manually with `isLoading/isError/data` when TanStack Query owns it;
- stale server data persisted locally without an explicit offline strategy.

### Networking
- browser calling FastAPI directly when BFF is the declared security boundary;
- Server Component self-fetching `/api/*` over the network;
- generic proxy Route Handler;
- retrying POST automatically without idempotency;
- no timeout on backend calls;
- forwarding all browser headers/cookies;
- returning raw backend errors.

### Next.js/React
- `'use client'` on the entire authenticated application for convenience;
- using Middleware as authorization;
- fetching routine query data in `useEffect`;
- effects that synchronize two state stores;
- using Server Actions and Route Handlers interchangeably for the same domain commands without an architecture decision;
- indiscriminate caching of authenticated responses.

### Type safety
- manual edits to generated OpenAPI types;
- widespread `any`;
- `as` assertions used to suppress real contract mismatches;
- manually duplicated schemas/interfaces with no reason;
- trusting environment variables without validation.

### Testing
- E2E tests that depend on previous tests;
- arbitrary sleeps;
- CSS/XPath selectors when semantic locators are available;
- tests against uncontrolled third-party services;
- snapshot-heavy tests with weak behavioral assertions;
- accepting flaky tests as normal.

### Security
- `dangerouslySetInnerHTML` for untrusted content;
- wildcard CORS/cookie assumptions;
- missing CSRF/origin protection for cookie-auth mutations;
- secrets in `NEXT_PUBLIC_*`;
- logging Authorization/cookie headers;
- process-local auth refresh locks treated as globally correct;
- missing tenant authorization because the UI already hides the resource.

---

## 46. Definition of Done for every feature

A production feature is not done when the happy-path UI works.

Before merge, verify:

### Architecture
- [ ] Feature is placed in the correct module.
- [ ] No forbidden deep/circular imports.
- [ ] `src/app` remains composition-oriented.
- [ ] Server-only code cannot enter the client bundle.
- [ ] State has one clear owner.

### API/data
- [ ] BFF endpoint is deliberate and minimal.
- [ ] Input is validated at the appropriate boundary.
- [ ] FastAPI generated types are current.
- [ ] Error mapping follows the common contract.
- [ ] Request timeout is defined.
- [ ] Retry behavior is explicit.
- [ ] Mutation idempotency/concurrency behavior is understood.
- [ ] Tenant context is explicit.
- [ ] Query key includes all relevant scope/filter inputs.
- [ ] Cache invalidation is narrow and correct.

### Security
- [ ] Authentication checked server-side.
- [ ] Authorization enforced by FastAPI.
- [ ] Mutation CSRF/origin policy applies.
- [ ] Sensitive data is not returned/logged unnecessarily.
- [ ] No client-readable tokens/secrets.
- [ ] Redirects/URLs from user input are validated.

### UX/accessibility
- [ ] Loading, empty, error and success states exist.
- [ ] Keyboard interaction works.
- [ ] Labels/focus/semantics are correct.
- [ ] Destructive actions have appropriate safeguards.
- [ ] Timezone/locale behavior is correct.

### Testing
- [ ] Pure logic/schema tests added where valuable.
- [ ] Critical UI behavior covered.
- [ ] BFF error/security behavior covered where relevant.
- [ ] E2E critical flow added/updated if feature is business-critical.
- [ ] No flaky sleeps/shared test state.

### Operations
- [ ] Logs/metrics/traces provide enough context.
- [ ] User-visible unexpected errors have a request ID where appropriate.
- [ ] Feature does not create unbounded backend load.
- [ ] Bundle impact is acceptable.
- [ ] Rollout/backward compatibility considered.

---

## 47. Initial implementation sequence

For a greenfield or architecture-refactor phase, implement foundations in this order.

### Phase 1 — compiler, repository and boundaries

1. strict TypeScript configuration;
2. lint/import-boundary rules;
3. feature/platform/shared directories;
4. server-only import enforcement;
5. code formatting and CI baseline;
6. Node/package-manager version pinning.

### Phase 2 — API contract foundation

1. pin FastAPI OpenAPI artifact flow;
2. `openapi-typescript` generation;
3. generated-code drift check;
4. server FastAPI client;
5. browser BFF client;
6. normalized error model;
7. request IDs/timeouts.

### Phase 3 — authentication/security

1. login/logout/refresh BFF endpoints;
2. secure cookie policy;
3. session projection;
4. authenticated route layout;
5. BFF auth helper;
6. origin/CSRF policy;
7. security headers/CSP baseline;
8. terminal 401 browser behavior;
9. refresh concurrency design with backend.

### Phase 4 — state/data platform

1. QueryClient factory/provider;
2. query defaults;
3. hydration pattern;
4. feature query-key pattern;
5. Zustand store conventions;
6. URL-state parsing conventions.

### Phase 5 — test platform

1. Vitest config;
2. browser/component test setup if required;
3. Playwright projects/fixtures;
4. deterministic auth test setup;
5. contract tests;
6. CI traces/artifacts;
7. security header/session tests.

### Phase 6 — observability and deployment

1. structured logging;
2. request/trace propagation;
3. server/client error reporting;
4. Web Vitals;
5. SLO/metric dashboards;
6. preview deployments;
7. security/dependency scanning;
8. rollback/runbook.

### Phase 7 — business features

Build features vertically through the established path:

```text
page/UI
→ Query/mutation
→ browser BFF client
→ Route Handler
→ feature server adapter
→ FastAPI
→ tests/telemetry
```

This prevents each new feature from inventing its own architecture.

---

## 48. Supporting tooling worth adding if not already present

The declared stack is sufficient for the architectural core, but a production repository normally also needs supporting tooling. Add only after checking what is already present.

Strong candidates:

- **ESLint** with Next.js, React hooks, TypeScript and import-boundary rules;
- **Prettier** or equivalent deterministic formatter;
- **TanStack Query ESLint plugin**;
- **React Testing Library** if Vitest DOM/component testing is desired rather than browser-mode-only tests;
- **accessibility test integration** such as axe for automated high-signal checks;
- **OpenTelemetry** and/or a production error-reporting backend;
- **dependency update automation**;
- **secret/dependency/SBOM scanning** appropriate to the organization's security process;
- **OpenAPI breaking-change tooling**;
- **bundle analysis/regression tooling**.

These are not reasons to replace the declared architectural stack. They are engineering controls around it.

---

## 49. Concrete state decision matrix

When a developer asks “where should this state live?”, use this matrix.

| Question | Use |
|---|---|
| Did it come from FastAPI and can become stale? | TanStack Query |
| Is it needed only during this component's interaction? | React local state |
| Should refresh/back/share preserve it? | URL params/search params |
| Is it transient UI state shared by distant components? | Zustand |
| Is it a form value? | Form/component state + Zod |
| Is it a token/credential? | HttpOnly cookie on BFF only |
| Is it an authoritative business transition? | FastAPI/backend |
| Is it server-rendered and never independently client-refetched? | Server Component ownership |
| Is it server-prefetched but interactive/live after hydration? | TanStack Query owns it after hydration |

If two rows seem applicable, define which behavior is primary rather than storing the value twice.

---

## 50. Concrete API decision matrix

When adding a data operation:

### Browser needs mutable/queryable server data

```text
Client Component
→ TanStack Query
→ /api feature BFF endpoint
→ FastAPI
```

### Server-rendered page needs one server-owned read

```text
Server Component
→ server-only feature adapter
→ FastAPI
```

### Server-rendered page wants initial data for later client interaction

```text
Server Component
→ request-local QueryClient prefetch
→ server-only FastAPI adapter
→ dehydrate
→ Client Component Query hook
→ later browser refetches via /api BFF
```

### Long-running operation

```text
Browser mutation
→ BFF
→ FastAPI creates job
→ return job ID
→ Query polls/subscribes to job status
```

### Large file upload

```text
Browser asks BFF/backend for authorized upload intent
→ backend returns presigned/controlled upload target
→ browser uploads directly to storage
→ backend finalizes/processes
```

Do not route every byte through Next.js unless required by the threat/infrastructure model.

---

## 51. Architecture review questions for every major PR

A senior reviewer should ask:

1. What owns this state?
2. Is any data duplicated between Query, Zustand, URL and component state?
3. Is this code in the correct feature/platform boundary?
4. Can server-only data reach the client bundle?
5. Does the browser ever learn the FastAPI origin or tokens unnecessarily?
6. Is the Route Handler a deliberate endpoint or becoming a generic proxy?
7. Where is authentication checked?
8. Where is authorization enforced?
9. Is tenant scope guaranteed server-side?
10. What happens if two identical mutations occur concurrently?
11. Is retry safe?
12. What is the timeout?
13. What cache owns freshness?
14. What invalidates the cache?
15. Can RSC-rendered data diverge from Query-owned data?
16. What happens when the backend adds/removes a field/status?
17. Are runtime inputs validated?
18. Are error codes stable and safe?
19. Are logs free of tokens/PII?
20. Can this run correctly on 10 Next.js instances?
21. Can this be tested without knowing private component internals?
22. Is accessibility preserved?
23. What happens on partial backend failure?
24. Does this increase bundle size for unrelated routes?
25. Can the feature be removed without editing dozens of global files?

---

## 52. Reference production request flows

### 52.1 Read flow

```text
User opens booking dashboard
  ↓
Server route resolves session
  ↓
Server optionally prefetches booking query through FastAPI adapter
  ↓
HTML/RSC + dehydrated Query data streamed
  ↓
Client Query hydrates without immediate duplicate fetch
  ↓
User changes URL filter
  ↓
Query key changes
  ↓
Browser calls /api/clubs/{clubId}/bookings?... 
  ↓
BFF validates session + tenant request + input
  ↓
BFF adds Authorization and trace ID
  ↓
FastAPI authorizes club membership and returns data
  ↓
BFF returns minimal safe DTO
  ↓
TanStack Query caches by tenant/filter key
```

### 52.2 Mutation flow

```text
User submits booking change
  ↓
Form schema safeParse
  ↓
TanStack mutation starts
  ↓
Idempotency key generated for logical command if required
  ↓
POST /api/... with same-origin cookies
  ↓
BFF validates Origin/CSRF + session + body
  ↓
BFF calls FastAPI with bearer token + idempotency key + trace
  ↓
FastAPI validates authorization/business rules transactionally
  ↓
BFF maps result/error
  ↓
Mutation updates/invalidate precise Query keys
  ↓
UI announces success/conflict/error accessibly
```

### 52.3 Expired access token flow

```text
BFF calls FastAPI
  ↓
access token expired
  ↓
BFF performs one controlled refresh attempt
  ↓
refresh succeeds under concurrency-safe backend/session design
  ↓
BFF updates HttpOnly cookies
  ↓
BFF retries original operation once
  ↓
result returned
```

If refresh fails:

```text
BFF clears invalid session cookies
  ↓
returns terminal 401
  ↓
browser central auth handling clears sensitive caches/state
  ↓
redirect/login UX
```

---

## 53. What “senior production ready” means for this stack

For this specific technology set, a senior architecture is **not** demonstrated by adding more layers. It is demonstrated by maintaining the following invariants under growth:

1. **Next.js App Router is a composition/runtime framework, not the domain layer.**
2. **The BFF is the only normal browser path to FastAPI and owns token handling.**
3. **FastAPI remains authoritative for business rules and authorization.**
4. **TanStack Query owns browser server state.**
5. **Zustand owns only justified transient client UI state.**
6. **URL state owns navigable filters/selections.**
7. **Zod validates runtime trust boundaries; TypeScript models compile-time invariants.**
8. **OpenAPI is generated once from the backend contract and isolated at the transport boundary.**
9. **Feature modules are the unit of change and ownership.**
10. **Server-only and client code are mechanically separated.**
11. **Authenticated data is never accidentally shared-cached.**
12. **Auth refresh, idempotency and rate limiting work under horizontal concurrency.**
13. **Errors are typed, normalized, safe and observable end-to-end.**
14. **Security controls are tested, not assumed.**
15. **Architecture rules are enforced in CI.**
16. **Framework dependencies are kept on supported security-patched releases.**
17. **Every feature has loading/error/empty/accessibility/concurrency behavior, not just a happy path.**
18. **The application can scale to many teams without global files becoming coordination bottlenecks.**

---

## 54. Final recommended architecture summary

Use a **feature-oriented modular frontend** with a **thin App Router composition layer** and a **server-only BFF platform layer**.

The canonical flow is:

```text
┌──────────────────────────────────────────────────────────┐
│ Browser                                                  │
│                                                          │
│ React Client Components                                  │
│  ├─ TanStack Query = server state                        │
│  ├─ Zustand = transient shared UI state                  │
│  ├─ URL = navigable state                                │
│  ├─ React local state = local interaction                │
│  └─ Zod = runtime input validation                       │
└────────────────────────────┬─────────────────────────────┘
                             │ same-origin /api
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Next.js 15 BFF                                           │
│                                                          │
│ Route Handlers                                           │
│  ├─ Origin/CSRF checks                                   │
│  ├─ HttpOnly cookie auth                                 │
│  ├─ input validation                                     │
│  ├─ tenant/request context                               │
│  ├─ error normalization                                  │
│  ├─ timeout/tracing                                      │
│  └─ explicit safe response contracts                     │
│                                                          │
│ server-only FastAPI adapters                             │
│  └─ openapi-typescript generated transport types         │
└────────────────────────────┬─────────────────────────────┘
                             │ Authorization + trace
                             ▼
┌──────────────────────────────────────────────────────────┐
│ FastAPI backend                                          │
│                                                          │
│ Authoritative:                                           │
│  ├─ authentication/token semantics                       │
│  ├─ authorization/tenant isolation                       │
│  ├─ business rules                                       │
│  ├─ validation                                           │
│  ├─ transactions/concurrency                             │
│  └─ idempotency                                          │
└──────────────────────────────────────────────────────────┘
```

For initial server rendering, Server Components may call the server-only FastAPI adapter directly or prefetch a request-local TanStack Query cache. They should **not** loop back through the application's own `/api` endpoints.

This structure gives the project the properties required for a highly scalable and changing production application: local feature ownership, secure token isolation, backend contract discipline, clear state ownership, safe horizontal scaling, controlled rendering boundaries, resilient tests, and end-to-end observability.

---

## 55. Source basis / official guidance consulted

This architecture was cross-checked against current official/primary guidance for the declared stack, including:

- Next.js App Router, Route Handlers, Backend-for-Frontend, authentication, data security, cookies, caching and security guidance;
- React 19 Server Components / server-client boundary guidance;
- TanStack Query advanced server rendering, hydration, invalidation and mutation guidance;
- Zustand Next.js SSR/hydration guidance;
- Zod runtime parsing and strict TypeScript guidance;
- TypeScript compiler strictness documentation;
- openapi-typescript generation and advanced recommendations;
- Vitest coverage/projects/browser testing guidance;
- Playwright test isolation, locators, CI and E2E best practices;
- OWASP CSRF, session management, CSP and security-header guidance;
- Next.js and React security advisories affecting React Server Components.

Because framework security and patch versions evolve, the team MUST re-check official advisories during dependency upgrades and should not treat this document's historical version examples as a permanent patch list.

---

# Appendix A — Suggested architectural conventions

These conventions are intentionally compact and can be copied into the repository's contributor guide.

## A.1 Imports

- Import features only through their public API.
- Never import `server/` from client code.
- Never import generated FastAPI `paths` from UI.
- Never import feature code from `shared`.
- Avoid root mega-barrels.

## A.2 State

- Remote = Query.
- Navigable = URL.
- Local = React.
- Shared transient UI = Zustand.
- Tokens = HttpOnly cookies.
- Business truth = FastAPI.

## A.3 Networking

- Browser calls only same-origin BFF for application APIs.
- Server Components do not self-fetch BFF.
- Every FastAPI call has timeout + trace context.
- No unsafe automatic mutation retries.
- No generic proxy.

## A.4 Security

- Secure/HttpOnly/SameSite cookies.
- Origin/CSRF defense on mutations.
- Authorization in FastAPI for every resource/action.
- No secrets in public environment.
- No sensitive logs.
- Explicit cache behavior for authenticated data.

## A.5 Tests

- Pure logic: Vitest.
- UI behavior: component/browser integration tests.
- Critical journeys: Playwright.
- Tests isolated and deterministic.
- Contract/codegen drift checked in CI.

---

# Appendix B — Example feature boundary

```text
features/bookings/
├─ api/
│  ├─ bookings.browser.ts       # calls /api/bookings...
│  └─ bookings.contract.ts      # BFF-facing DTO/error contracts
├─ model/
│  ├─ booking-query-keys.ts
│  ├─ booking-query-options.ts
│  ├─ use-bookings.ts
│  ├─ use-cancel-booking.ts
│  └─ booking-model.ts
├─ schemas/
│  ├─ booking-filters.schema.ts
│  └─ edit-booking.schema.ts
├─ state/
│  └─ booking-workspace.store.ts # only if transient shared UI requires it
├─ ui/
│  ├─ BookingTable.tsx
│  ├─ BookingFilters.tsx
│  └─ EditBookingDialog.tsx
├─ server/
│  ├─ bookings.fastapi.ts       # generated FastAPI types used here
│  ├─ get-bookings.server.ts
│  └─ cancel-booking.server.ts
├─ test/
│  └─ ...
└─ index.ts
```

Corresponding App Router code stays small:

```text
app/(authenticated)/clubs/[clubId]/bookings/page.tsx
app/api/clubs/[clubId]/bookings/route.ts
app/api/clubs/[clubId]/bookings/[bookingId]/cancel/route.ts
```

The feature owns the capability. `app` owns how that capability is exposed through Next.js routing.

---

# Appendix C — Production readiness checklist for the platform itself

Before feature teams scale up, the platform should have all of the following:

- [ ] Strict TypeScript settings.
- [ ] Architecture import rules.
- [ ] Server-only boundary enforcement.
- [ ] FastAPI OpenAPI generation pipeline.
- [ ] Generated-code drift CI gate.
- [ ] Typed server FastAPI client.
- [ ] Typed browser BFF client.
- [ ] Standard BFF error envelope.
- [ ] Request ID/trace propagation.
- [ ] Per-request timeout strategy.
- [ ] Secure auth cookie helper.
- [ ] Login/logout/refresh implementation.
- [ ] Concurrency-safe refresh design agreed with FastAPI.
- [ ] CSRF/origin policy.
- [ ] Security headers/CSP.
- [ ] Authenticated layout/session projection.
- [ ] QueryClient provider/factory.
- [ ] Server prefetch/hydration convention.
- [ ] Query-key convention.
- [ ] Zustand convention/reset policy.
- [ ] URL-state parsing convention.
- [ ] Vitest test foundation.
- [ ] Component/browser test foundation.
- [ ] Playwright auth/data fixtures.
- [ ] Tenant-isolation tests.
- [ ] Cookie/security tests.
- [ ] Contract tests.
- [ ] Structured logs.
- [ ] Error reporting.
- [ ] Web Vitals.
- [ ] SLO/alerting baseline.
- [ ] Dependency/security scanning.
- [ ] Exact patched framework versions pinned.
- [ ] Preview environment.
- [ ] Rollback procedure.
- [ ] ADR directory and architecture ownership.

When these foundations exist, individual business features can be developed in parallel without repeatedly solving cross-cutting architecture problems.

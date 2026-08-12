# `src/app/api/` — the BFF (backend-for-frontend)

These route handlers are **the only thing the browser is allowed to call**. They run
server-side, hold the FastAPI base URL (`BACKEND_API_URL`, never `NEXT_PUBLIC_*`), and
own the httpOnly session cookies. See
[ADR-0007](../../../../docs/adr/0007-club-web-bff-httponly-cookie-session.md) and
[`docs/architecture/production-architecture.md`](../../../docs/architecture/production-architecture.md)
§8, §9, §43 — section refs below point there.

```
browser ──▶ /api/*  (this BFF, same origin)  ──▶  FastAPI
        ✗ never straight to FastAPI
        ✗ never a Server Component fetching /api/* over the network
```

**The BFF is not a generic proxy.** It is a security, authentication, adaptation and
observability boundary that exposes **deliberate** endpoints. *(§3.6)*

## The handler sequence *(§43)*

Every handler follows this, built from small reusable primitives in
[`@/platform/server`](../../platform/README.md) — not copied as hundreds of lines into
each `route.ts`, and not hidden behind a magic wrapper that makes security behavior
uninspectable.

```
request context / trace ID
  → method + content-type + body-size checks
  → origin/CSRF check for unsafe methods
  → authentication (resolve session from the cookie)
  → input validation (Zod)
  → authorization context
  → feature server operation  (@/features/<f>/server)
  → FastAPI call WITH TIMEOUT
  → backend result/error normalization
  → minimal response DTO
  → explicit cache + security headers
  → structured telemetry
```

Large business workflows do not live in `route.ts`. *(§8.1)*

## Rules

- **A Client Component never calls FastAPI directly.** It calls `/api/*`. The browser must
  never learn the FastAPI origin. *(§4.1)*
- **Never a catch-all.** `/api/proxy?url=…` and `/api/backend/[...path]` are banned —
  generic forwarding is an SSRF, authorization and header-leak hole. User values may fill
  validated path/query parameters; they never redefine the destination host, scheme or
  port. *(§8.2, §10.6)*
- **Tokens never reach the browser.** Access/refresh JWTs live in httpOnly + Secure +
  SameSite cookies set here — never in `localStorage`, `sessionStorage`, Zustand, Query,
  React Context, a JS-readable cookie, or a Client Component prop. Responses carry only a
  **sanitized session projection**. *(§9.1, §9.7)*
- **Explicit outbound header allowlist.** Construct `Authorization` server-side; add
  request/correlation ID, trace context, and an idempotency key where the contract
  supports one. Never forward the browser's whole header set or its cookies. *(§8.3)*
- **Finite timeout on every downstream call,** categorized by endpoint, with abort
  signals so timed-out work is cancelled. *(§8.4)*
- **Retry is opt-in.** GET/HEAD may retry clearly transient failures inside the deadline.
  POST/PATCH never auto-retry without a backend idempotency guarantee. Auth refresh gets
  **at most one** controlled attempt per original request. Avoid retry storms — browser,
  BFF and mesh must not all retry independently. *(§8.5)*
- **Authenticated responses are private/`no-store`.** Personalized data must never reach a
  shared CDN cache. Next 15 does not cache route handlers by default, but say so
  explicitly so a future refactor cannot silently change it. *(§8.7, §27.3)*
- **CSRF defense in depth** on state-changing endpoints: explicit `SameSite` cookies, a
  strict `Origin` allowlist, intended HTTP methods only, JSON content types enforced, and
  never a state change through GET. *(§10.1)*
- **Status codes stay semantically meaningful.** Not everything a 200 with
  `{ success: false }`; not everything a 500. Internal exception text, SQL and stack
  traces stay server-side; the browser gets a code, a safe message and a request ID.
  *(§22.2, §22.3)*
- **Validate redirect targets.** Any `returnTo`/`redirect`/callback from the browser is
  checked against an internal route allowlist. *(§10.5)*
- **Middleware is not authorization.** A middleware or layout redirect is a UX gate; every
  endpoint here re-verifies session and permission independently, and FastAPI authorizes
  every protected operation — including that the principal may act on that specific club.
  *(§7.6, §9.8, §11.1)*
- **No long-running work in a handler.** Bulk imports, report generation and reconciliation
  become backend jobs the browser polls. Large files use presigned upload/download URLs,
  not a byte-for-byte proxy. *(§8.6, §32.4)*
- **Nothing stateful across requests.** No module-global refresh lock, session store or
  rate-limit counter — any two requests may hit different instances. *(§3.7, §32.1)*

## Server Components do not come through here

A Server Component that needs backend data calls the feature's server-only adapter
directly. Routing it back through `/api/*` adds a network hop, complicates cookies and
headers, and breaks in some deployments. *(§4.2)*

For data prefetched on the server and then owned by Query in the browser: the **query key
and data contract are shared**, the server prefetch uses the FastAPI adapter, and the
browser transport uses this BFF. *(§4.3)*

## Why the mobile app differs

`frontend_player` (Expo) has no BFF: a native app has no cookie jar and no XSS surface of
the same shape, so it holds tokens in the OS keychain via `expo-secure-store` and calls
FastAPI directly. Same backend, deliberately different session model — see
[ADR-0008](../../../../docs/adr/0008-player-mobile-securestore-direct-api.md).

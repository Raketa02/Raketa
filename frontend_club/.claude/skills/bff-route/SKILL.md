---
name: bff-route
description: Add or change a BFF route handler under src/app/api in the club app. Use when creating an endpoint the browser calls, or changing auth, validation, timeouts or error mapping on one.
---

# Adding a BFF route handler

A route handler is a **deliberate endpoint**, never generic forwarding. If you are tempted
to write `[...path]`, stop — that is an SSRF hole (§8.2).

## The sequence

Build it from the shared primitives in `src/platform/server/`, not by copying a previous
`route.ts`:

```
request context / trace ID → method + content-type + origin/CSRF checks
→ authentication → input validation (Zod, safeParse)
→ authorization context → feature server operation
→ FastAPI call WITH TIMEOUT → error normalization
→ minimal response DTO → explicit cache + security headers → structured telemetry
```

## Decisions you must make explicitly, not inherit

- **The timeout**, categorized by what this endpoint does. Not one global value. (§8.4)
- **Whether it may retry.** GET/HEAD may, inside the deadline. POST/PATCH may not, without
  a backend idempotency guarantee. (§8.5)
- **The cache header.** Authenticated responses are `no-store`/private. A cache leak here
  is a data breach. (§8.7)
- **What the response omits.** The BFF contract is a frontend contract, not a mirror of the
  FastAPI DTO. Drop what the browser does not need. (§16.3)
- **Which outbound headers you construct.** An explicit allowlist. `Authorization` is built
  server-side; the browser's cookies and header set are never forwarded. (§8.3)

## Authorization

Verify session and permission **in this handler**. A middleware or layout redirect is a UX
gate, not authorization, and FastAPI must authorize the operation independently. Never trust
a `clubId` from the browser — the principal is checked against the target club server-side.

## Tests that must exist

Unauthenticated rejected · wrong tenant rejected · invalid input rejected *before* the
backend call · `Authorization` built server-side · browser cookies not forwarded · timeout
mapped · conflict mapped · request ID propagated · bad Origin rejected · **no backend
internals in the response body**.

These are security assertions, so they are tests, not prose (§30).

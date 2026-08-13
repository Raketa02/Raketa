---
paths:
  - "src/app/api/**"
  - "src/platform/server/**"
  - "src/features/*/server/**"
---

# The BFF *(§8, §43)*

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

## The rules that get broken

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
  calls, drop sensitive fields, normalize errors and reduce payloads. Re-exposing every
  backend DTO unchanged erases the BFF's purpose. *(§16.3)*
- Business workflows do not live in `route.ts`. *(§8.1)*
- **No catch-all forwarding.** `/api/proxy?url=…` and `/api/backend/[...path]` are SSRF
  holes. Route handlers are deliberate endpoints. *(§8.2)*
- **A Server Component never fetches its own `/api/*` over the network.** Server code calls
  the server-only FastAPI gateway directly. *(§4.2)*

## Generated types at the boundary *(§16)*

```
generated types → server FastAPI adapter → feature contract/model → hooks → UI
```

`src/generated/schema.d.ts` is generated from `../backend/openapi.json`, never hand-edited,
and committed. The production build must never depend on reaching a live backend for its
schema. No broad snake_case↔camelCase remapping for aesthetics — adapt a field only where
the frontend contract genuinely differs. Design for enum evolution: decide what the UI does
with an unknown value, because backend and frontend do not deploy atomically. *(§16.7, §40.2)*

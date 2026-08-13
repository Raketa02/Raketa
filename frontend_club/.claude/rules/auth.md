---
paths:
  - "src/platform/server/auth/**"
  - "src/platform/server/csrf/**"
  - "src/app/api/auth/**"
  - "src/middleware.ts"
---

# Auth *(§9)*

Login: browser POSTs to the same-origin BFF → BFF validates → BFF calls FastAPI → FastAPI
returns credentials server-to-server → BFF writes httpOnly cookies → BFF returns **only a
sanitized session projection** (user id, display name, roles, capabilities, memberships,
expiry metadata). Never tokens. *(§9.3, §9.7)*

Cookie baseline: `HttpOnly`, `Secure` outside local, explicit `SameSite` (never the browser
default), `Path=/`, no broad `Domain`, `__Host-` prefix where the deployment allows, short
access lifetime, controlled refresh rotation. *(§9.2)*

**Middleware is not authorization.** A layout or middleware redirect is a UX gate. Every
BFF endpoint and every sensitive server operation must independently verify session and
permission, and FastAPI must authorize every protected operation. Hidden UI is not
security. *(§7.6, §9.8, §24.5)*

Logout: revoke server-side → clear cookies with matching attributes → clear sensitive Query
state → reset sensitive Zustand stores → redirect. *(§9.6, §37.4)*

## Open: refresh concurrency — settle this before building auth

§9.5 forbids solving concurrent refresh with an in-memory JavaScript mutex, because a
horizontally scaled Next.js deployment has many processes.
[ADR-0004](../../../docs/adr/0004-jwt-access-with-rotating-refresh-tokens.md) rotates
strictly and **rejects** an already-rotated token — there is no grace window today, and that
ADR itself names the failure ("a burst of concurrent refreshes that rotate each other out
and log the user out").

The mechanism must be agreed with the backend — rotation grace/reuse, an opaque session ID
with a shared session store, or distributed synchronization. **Do not paper over it with a
module-global lock.** Raise it rather than picking one silently.

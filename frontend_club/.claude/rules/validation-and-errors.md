---
paths:
  - "src/features/*/schemas/**"
  - "src/platform/api/**"
  - "src/platform/config/**"
---

# Zod and the error envelope

## Zod belongs at trust boundaries *(§15)*

Not sprayed over already-typed internals. Static types disappear at runtime.

Validate: form payloads, search params, BFF request bodies, environment config, persisted
state migrations. Use `safeParse` for user input so validation is a typed branch, not an
exception. Put cross-field rules in the schema, not in `onChange`.

**Client validation is UX; FastAPI validation is authority.** *(§15.3)*

Do not duplicate one concept as interface + type alias + Zod schema + OpenAPI type. Infer TS
from Zod where the app owns the input model; use the generated type at the transport
boundary. Runtime-validate responses on a **risk basis** — high-risk, external or
corruption-sensitive data — not every payload. *(§15.4, §15.5)*

Business primitives: an instant is not a calendar date; a club's local opening time is not a
UTC instant; test DST. Money never in floats — integer minor units or the backend's
decimal-string contract, with an explicit currency. IDs are opaque. *(§15.8)*

## One stable browser-facing envelope *(§22, §18.2)*

Machine `code`, safe user-facing `message`, optional `fieldErrors`/`details`, and a
`requestId`. Components reason about stable **categories** — unauthenticated, forbidden,
validation, conflict, rate limited, not found, transient network, backend unavailable,
unexpected — never raw HTTP status or body shapes. *(§12.13)*

Feature domain codes sit beneath those categories (`COURT_ALREADY_BOOKED`). BFF status codes
stay semantically meaningful — not everything a 200 with `success: false`, not everything a
500. Internal exception text, SQL and stack traces stay server-side.

Recovery is per category: validation → field error · conflict → refresh and explain · 401 →
central session expiry · 403 → permission UI · transient → retry affordance · 5xx → preserve
input, show retry and a request ID. *(§22.5)*

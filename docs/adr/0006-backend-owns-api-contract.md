# ADR-0006 — The backend owns the API contract

- **Status:** Accepted
- **Date:** 2026-08-09

## Context

Two independent clients consume the same API, and by
[ADR-0005](0005-three-app-monorepo-ownership-boundaries.md) they share no code. That
raises an obvious question: how do three separately-developed apps agree on the shape of
a `Booking`?

The failure mode to avoid is well known. A developer (or an agent) hand-writes a
TypeScript interface that mirrors a JSON response. It is correct on the day it is
written. Then a field becomes optional, or a date becomes a string, and nothing tells
anyone — the type keeps compiling and starts lying. With two clients, the lie diverges
in two directions.

## Decision

We will treat the **backend as the single source of truth for the API contract**, and
**generate** both clients' wire types from it.

- `make openapi` (in `backend/`) dumps `backend/openapi.json` from the FastAPI app — no
  running server needed. The file is **committed**.
- Each client generates its own `src/generated/schema.d.ts` from that file with
  `openapi-typescript` (`pnpm gen:api`). `make gen-api` at the repo root does the whole
  chain for both clients.
- **Hand-writing a type that mirrors a backend response is forbidden.** If a type is
  missing, the fix is to correct the backend schema and regenerate.
- **Generated types are raw transport, confined to a feature's `api/` and `mappers/`
  layers.** They are mapped into each app's own DTO/domain objects before going further.
  ESLint enforces the confinement.
- A backend change that alters response shape must say so explicitly and regenerate the
  contract. The backend session **must not** edit the clients — the ownership hook
  blocks it, and correctly so.

## Consequences

**Easier**
- The two clients cannot drift from the backend or from each other in the one place they
  are most likely to: the wire.
- Removing or renaming a backend field surfaces as a **type error at generation time** in
  both clients, rather than as a runtime `undefined` in one of them.
- The contract is reviewable: `backend/openapi.json` appears in the diff.

**Harder**
- Regeneration is a step someone has to remember. A committed `openapi.json` that is
  stale relative to the code is worse than none, because it looks authoritative. CI
  should eventually verify it is current.
- Generated types are shaped by FastAPI/Pydantic, not by what the UI wants — hence the
  mandatory mapper layer, which is real extra code.
- Both clients must be regenerated after a contract change, in separate sessions.

**Neutral**
- Confining generated types to `api/` + `mappers/` means a backend response shape change
  breaks in exactly one layer per feature, which is the point.
- The mobile client makes this stricter in practice: old app versions stay installed on
  real phones for months, so **additive** contract changes should be the default and
  removals should be treated as breaking
  ([ADR-0008](0008-player-mobile-securestore-direct-api.md)).

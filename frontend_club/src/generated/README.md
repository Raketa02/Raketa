# `src/generated/` — do not edit by hand

`schema.d.ts` is generated from the backend's OpenAPI contract:

```bash
cd ../backend && make openapi     # writes backend/openapi.json
cd ../frontend_club && pnpm gen:api
# or, from the repo root:  make gen-api
```

The backend is the **single source of truth** for the API contract
([ADR-0006](../../../docs/adr/0006-backend-owns-api-contract.md)). Never hand-write a type
that mirrors a backend response — regenerate instead, and **commit the result**.

`../backend/openapi.json` is the **pinned artifact** the build reads. A production build
must never depend on reaching a live backend to download a schema
([`docs/architecture/production-architecture.md`](../../docs/architecture/production-architecture.md)
§16.4).

## Keep these at the boundary *(§16.2)*

These are **raw wire types** — the backend's transport shape, not this app's domain model.

```
generated types
      ↓
platform/server/fastapi-client  ·  features/<f>/server/*.fastapi.ts
      ↓
the feature's own contract/model
      ↓
model/ hooks  →  ui/
```

They may be read in a feature's `server/` layer, in `platform/server/`, and in the
contract adapter inside a feature's `api/`. **They must never reach `ui/`.** Once a
component imports a generated response type, the backend's serialization shape has been
welded to the UI.

Do not add broad snake_case↔camelCase remapping for aesthetics — it buys runtime cost and
duplicate type concerns. Adapt a field only where the frontend contract genuinely differs
(§16.7).

## Contract discipline *(§16.1, §16.5, §40)*

- Generated output is reproducible and checked for drift in CI; a diff means someone
  edited it or forgot to regenerate.
- CI should detect incompatible backend changes before rollout: removed endpoints or
  fields, optional→required, enum and type changes, response-shape changes.
- Frontend and backend deploy independently, so **design for enum evolution** — decide
  what the UI does with an unknown status rather than assuming today's values are
  permanent (§40.2).
- Prefer additive backend changes; a rolling deployment runs both versions at once.

> The standard's §5 sketch nests this as `generated/fastapi/`. This app keeps
> `src/generated/schema.d.ts`, which `pnpm gen:api` and the root `make gen-api` already
> target — the standard permits the names to differ as long as the dependency direction
> and responsibilities hold.

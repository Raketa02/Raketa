# `src/generated/` — do not edit by hand

`schema.d.ts` is generated from the backend's OpenAPI contract:

```bash
cd ../backend && make openapi     # writes backend/openapi.json
cd ../frontend_club && pnpm gen:api
# or, from the repo root:  make gen-api
```

The backend is the **single source of truth** for the API contract
([ADR-0006](../../../docs/adr/0006-backend-owns-api-contract.md)). Never hand-write a
type that mirrors a backend response — regenerate instead, and commit the result.

These are **raw wire types**. They may only be imported inside a feature's `api/` or
`mappers/` layer, which maps them into the feature's own DTO/domain objects. ESLint
enforces this. If a generated type is leaking upward, the fix is a mapper, not an
import.

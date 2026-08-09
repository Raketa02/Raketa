# `src/generated/` — do not edit by hand

`schema.d.ts` is generated from the backend's OpenAPI contract:

```bash
cd ../backend && make openapi     # writes backend/openapi.json
cd ../frontend_player && pnpm gen:api
# or, from the repo root:  make gen-api
```

The backend is the **single source of truth** for the API contract
([ADR-0006](../../../docs/adr/0006-backend-owns-api-contract.md)). Never hand-write a
type that mirrors a backend response — regenerate instead, and commit the result.

`frontend_club` generates its own copy from the same `backend/openapi.json`. The two
apps share no code by design (ADR-0005); regenerating both from one contract is what
keeps them from drifting. `make gen-api` at the repo root does both at once.

These are **raw wire types**, importable only inside a feature's `api/` or `mappers/`
layer. ESLint enforces this.

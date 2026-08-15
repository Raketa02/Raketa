# `src/generated/` — do not edit by hand

`schema.d.ts` is generated from the player half of the backend's OpenAPI contract.
From `frontend_player/`:

```bash
cd ../backend && make openapi     # writes BOTH openapi.player.json and openapi.club.json
cd ../frontend_player && pnpm gen:api
# or, from the repo root:  make gen-api
```

The backend is the **single source of truth** for the API contract
([ADR-0006](../../../docs/adr/0006-backend-owns-api-contract.md)). Never hand-write a
type that mirrors a backend response — regenerate instead, and commit the result.

The contract is **two documents**, one per client — `backend/openapi.player.json` and
`backend/openapi.club.json`. This app reads only the first; `frontend_club` generates its
own copy from the second. The two apps share no code by design (ADR-0005); regenerating
both from one emitter is what keeps them from drifting. `make gen-api` at the repo root
does both at once.

**Drift is checked in CI.** The player job regenerates with this app's own pinned
`openapi-typescript` and diffs — and it runs on a **backend-only** pull request too,
because the job's paths filter watches `backend/openapi.player.json` as well as this
directory. A red drift step means the contract moved and `schema.d.ts` did not; the fix is
`make gen-api` at the root, committed. The check is
[`.github/scripts/check-contract-drift.sh`](../../../.github/scripts/check-contract-drift.sh),
and it has its own tests (`make test-drift`).

These are **raw wire types**, importable only inside a feature's `api/` or `mappers/`
layer. ESLint enforces this.

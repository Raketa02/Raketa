# `src/generated/` — do not edit by hand

`schema.d.ts` is generated from the player half of the backend's OpenAPI contract.
From `frontend_player/`:

```bash
cd ../backend && make openapi     # writes openapi.player.json
cd ../frontend_player && pnpm gen:api
# or, from the repo root:  make gen-api
```

The backend is the **single source of truth** for the API contract
([ADR-0006](../../../docs/adr/0006-backend-owns-api-contract.md)). Never hand-write a
type that mirrors a backend response — regenerate instead, and commit the result.

The contract is **one document today** — `backend/openapi.player.json`, the player surface.
The emitter is already written per surface (`backend/app/api/contract.py` writes one
`openapi.<surface>.json` per entry in `SURFACES`), so a second client would read its own
document rather than share this one. The apps share no code by design (ADR-0005);
generating every client's types from one emitter is what keeps them from drifting.
`make gen-api` at the repo root emits the contract and regenerates this client in one step.

**Drift is checked in CI.** The player job regenerates with this app's own pinned
`openapi-typescript` and diffs — and it runs on a **backend-only** pull request too,
because the job's paths filter watches `backend/openapi.player.json` as well as this
directory. A red drift step means the contract moved and `schema.d.ts` did not; the fix is
`make gen-api` at the root, committed. The check is
[`.github/scripts/check-contract-drift.sh`](../../../.github/scripts/check-contract-drift.sh),
and it has its own tests (`make test-drift`).

These are **raw wire types**, importable only inside a feature's `api/` or `mappers/`
layer. ESLint enforces this.

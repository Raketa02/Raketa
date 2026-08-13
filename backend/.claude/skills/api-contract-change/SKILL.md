---
name: api-contract-change
description: Ship a change to the FastAPI response or request shape without breaking the two clients. Use when adding, removing or renaming a field, adding an endpoint, or changing a status code in backend/.
---

# Changing the API contract

`backend/openapi.json` is the single source of truth both clients generate from
([ADR-0006](../../../../docs/adr/0006-backend-owns-api-contract.md)). Neither client is in
your session, and the ownership hook will block you from editing them — correctly.

## Before changing the shape

Ask whether the change can be **additive**. A new optional field breaks nothing. A removed
or renamed field breaks two shipped clients, one of which is a mobile app whose old
versions stay installed on real phones for months — you cannot force an update, so a
released build is immutable from your point of view.

If a field must go, the sequence is: add the replacement → both clients migrate → remove
the old one in a later change. Not all three at once.

## The steps

1. Make the change in `app/modules/<context>/presentation/` (schemas and routes).
2. Add or update tests in `tests/api/` covering the new shape, including the error paths.
3. `make check` — lint, typecheck, tests.
4. `make openapi` — regenerate `openapi.json` so the committed contract matches the code.
5. Commit the code **and** `openapi.json` together. A contract file that lags the code is
   worse than no contract file, because both clients generate from it.

## Then hand off

You cannot regenerate the clients from here. End your summary with an explicit handoff:

> Contract changed: `POST /api/v1/bookings` response now includes `cancellation_deadline`
> (ISO-8601 string, nullable). `openapi.json` regenerated and committed.
> **Both clients need `pnpm gen:api`** — run `make gen-api` from the repo root, or a
> session in each client.

Name the endpoints and the shape change. "The contract changed" is not a handoff.

# ADR-0016 — A modular monolith with two API surfaces

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Two client applications talk to one backend: the player app (`frontend_player/`) and the
club console (`frontend_club/`). ADR-0006 established that the backend owns the API contract
and both clients generate their wire types from it. That ADR assumed a **single**
`openapi.json`.

A single document has a latent problem: it lets either client take a dependency on a path or
schema meant for the other. Once both clients have generated against one document, splitting
it later is a migration touching real, shipped wire types — including a mobile app whose old
versions stay installed on phones for months.

We also considered — and rejected — splitting the backend into microservices per client.
`Match` and the Intent Pool straddle the player/club line, so that seam would put a network
hop inside the transaction that takes a court off the market. One deployable is the right
call; the separation belongs at the **contract**, not the process.

## Decision

We will keep **one backend deployable** and give it **two route trees and two OpenAPI
documents**, one per client.

- `backend/app/api/v1/player.py` and `.../club.py` each build a surface router under the
  versioned `/api/v1` prefix. The running app (`app/api/v1/router.py`) mounts **both**; the
  deployable is single.
- `make openapi` (`python -m app.api.contract`) emits **two committed documents** —
  `backend/openapi.player.json` and `backend/openapi.club.json` — each generated from a
  throwaway app carrying only that surface's routes, so a player client never sees a club
  path and vice versa.
- Each client's `pnpm gen:api` reads **its own** document: the player app from
  `openapi.player.json`, the club app from `openapi.club.json`.
- The split is set up **now**, while it costs two one-line edits, rather than after real club
  wire types exist. The club surface currently carries no endpoints; the tree exists so club
  routes have a home the day they are written.

This amends ADR-0006's single-document mechanism; ADR-0006 has been updated to point here.

## Consequences

**Easier**
- Neither client can accidentally depend on the other's contract — the other's paths are not
  in its document to import.
- Adding the club surface later is additive: mount routes on the club router, regenerate,
  commit. No migration of existing player wire types.
- One deployable keeps cross-surface transactions (Match, the Intent Pool) in-process.

**Harder**
- Two documents to keep current instead of one, and `make gen-api` now regenerates two
  targets. A stale document still looks authoritative — CI should eventually verify both are
  current.
- A route's surface is a deliberate choice a developer must make (which router to mount it
  on), not an afterthought. A genuinely shared endpoint (auth, identity) has to be included
  on each surface that needs it.

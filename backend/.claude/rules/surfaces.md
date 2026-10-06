---
paths:
  - "app/api/**"
  - "app/modules/*/presentation/**"
  - "openapi.*.json"
---

# API surfaces and the dev console

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

> **The dev console below is replaced by the games test console of
> [ADR-0194](../../../docs/adr/0194-the-games-test-console-acts-as-seed-accounts-and-writes-history-never-time.md)**
> (#590, after #578 removes it). That console acts as seed accounts **without signing in**,
> refuses a non-seed account, is served in `local` only, and builds situations from `app/seeds/`.
> Each action runs the player's or club's own use case. What follows describes the console that
> exists until then.

- **New routes mount under `app/api/v1/router.py`;** keep the `/api/v1` prefix, and mount
  them on **the surface whose client calls them**: `app/api/v1/player.py` for the player
  app, `app/api/v1/club.py` — everything under `/api/v1/club` — for the club website, and
  `app/api/v1/public.py` — everything under `/api/v1/public`, and no route taking a session —
  for the public site
  ([ADR-0187](../../../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §5). No path is in two documents (`tests/unit/test_club_surface.py`,
  `tests/unit/test_public_surface.py`). **A route no client calls is on no surface**: the
  payment provider's webhooks mount through `app/api/v1/webhooks.py`, under
  `/api/v1/webhooks` and out of every document (ADR-0190 §4). The one
  exception to the prefix is the **dev console** (`app/api/dev/`, #256) — a second *surface*, not a
  second client: one no-build `console.html` behind a `FileResponse` at `/dev`, and one
  roster route, which is the whole of `openapi.dev.json`. It **acts as another player by
  signing in as them** through the ordinary `POST /api/v1/auth/login` with the public seed
  password the roster hands over, so there is no impersonation endpoint, no `Act-As` header
  and no authorisation path that exists for it — every write it presses is a
  player-surface write. It is gated **structurally and by data**, asymmetrically:
  `CONSOLE_SERVED` in `app/api/dev/gate.py` is a **second table** and never `SEEDABLE`
  (deriving one refusal from another is what `app/seeds/guard.py` argues against), and
  importing `routes.py` in production raises `ConsoleRefused` — while the data half is a
  *consequence*, since the roster lists only the reserved `.example` TLD and production has
  no such accounts. The refusal is at the top of `routes.py` rather than in the package's
  `__init__`, deliberately: `create_app` reads the gate in **every** environment, so a
  package that refused on import would take the production deployable down at startup. It
  **declines the `app/seeds/` import it is entitled to** — which is what keeps the console's
  own refusal the one that fires — at the cost of spelling two constants twice, pinned by
  `tests/unit/test_dev_console_surface.py`. Its contract is checked for **freshness**
  (`make contract-freshness`), not by the client drift check, which has no purchase on a
  document with no client.

**`make openapi` writes one document per surface, and there are four.** The second is the
**dev console**'s `openapi.dev.json` — one path, and no client, so nothing generates types
from it. The third is the **club website**'s `openapi.club.json`, which `frontend_club`
generates from; the fourth is the **public site**'s `openapi.public.json`, which
`frontend_public` generates from — **no route on it takes a session**, and its password
routes run the app's own rules and sign nobody in (#511). All four are committed and gated at
the repository root by `make contract-freshness`: re-emit and diff, which is a different
question from `make test-drift`'s (that one asks whether a *client's* generated types
reproduce from its document, and has no purchase on a document with no client).
`tests/unit/test_club_surface.py` and `tests/unit/test_public_surface.py` fail a stale club or
public document inside this suite too, before the root gate runs. Commit the regenerated
documents with whatever moved them, and hand the clients a `make gen-api` at the root.

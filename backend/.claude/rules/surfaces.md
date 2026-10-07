---
paths:
  - "app/api/**"
  - "app/modules/*/presentation/**"
  - "openapi.*.json"
---

# API surfaces and the dev console

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

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
  exception to the prefix is the **dev console** (`app/api/dev/`) — a second *surface*, not a
  second client: the **games test console** of
  [ADR-0194](../../../docs/adr/0194-the-games-test-console-acts-as-seed-accounts-and-writes-history-never-time.md)
  (#590). A no-build `console.html` at `/dev`, out of the contract; the roster the phone signs
  in from; and a route per thing the page presses — a person's buttons under
  `/dev/as/{player_id}/…`, a group's board under `/dev/groups`, the situations under
  `/dev/situations/…`, and *Run it now* (#592). Four rules hold it:
  - **It acts as seed accounts without signing in.** A press names its **acting account** in
    its path; `accounts.py` refuses any id not addressed on the reserved `.example` TLD
    (`not_a_seed_account`) before the use case is built. No token, session or header.
  - **A press is wiring.** It builds the player's (or club's) command and runs that route's
    own use case, through the same dependency, so its outcome and its refusals are the
    player's — `tests/api/test_games_test_console.py` holds each button to the player's
    route. Work a player route does outside its use case is a bug the console would skip:
    move it into the use case, never into a copy here.
  - **Served in `local` only.** `CONSOLE_SERVED` in `gate.py` is a **second table** and never
    `SEEDABLE` (the seed runs in three environments, the console in one), and **every module
    of the console imports `refusal.py` first** — but `gate` and the package's `__init__`,
    which `create_app` reads in every environment, so a package that refused on import would
    take a production deployable down at startup. First, too, because the console imports
    `app/seeds/` (situations are built from the seed's building blocks, ADR-0194 §4): the
    refusal that arrives anywhere else must be `ConsoleRefused`, never `SeedRefused`, and
    `tests/unit/test_dev_console_gate.py` imports every module under each refused
    environment to prove it.
  - **Its reads are its own queries** over the contexts' projections (two, in `board.py`),
    and every port it takes is declared as a request dependency — the context's own where
    one exists, `app/api/dev/dependencies.py` where none does — so a test that replaces a
    port replaces it for the console too. The placement ADR-0194 re-argued: nothing
    shipped imports it, so deleting it changes nothing that ships, and every *write* it
    causes is a context's own use case.

  Its contract is checked for **freshness** (`make contract-freshness`), not by the client
  drift check, which has no purchase on a document with no client.

**`make openapi` writes one document per surface, and there are four.** The second is the
**dev console**'s `openapi.dev.json` — the roster and the console's routes, and no client,
so nothing generates types from it. The third is the **club website**'s `openapi.club.json`, which `frontend_club`
generates from; the fourth is the **public site**'s `openapi.public.json`, which
`frontend_public` generates from — **no route on it takes a session**, and its password
routes run the app's own rules and sign nobody in (#511). All four are committed and gated at
the repository root by `make contract-freshness`: re-emit and diff, which is a different
question from `make test-drift`'s (that one asks whether a *client's* generated types
reproduce from its document, and has no purchase on a document with no client).
`tests/unit/test_club_surface.py` and `tests/unit/test_public_surface.py` fail a stale club or
public document inside this suite too, before the root gate runs. Commit the regenerated
documents with whatever moved them, and hand the clients a `make gen-api` at the root.

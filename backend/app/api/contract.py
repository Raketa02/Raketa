"""Emit the API contracts, one document per surface.

The backend owns the contract and the player client generates its wire types
from this document, never hand-writing a DTO that mirrors a response
(``docs/adr/0006``). ``make openapi`` runs this module; ``make gen-api`` then
points the client's codegen at the file it writes.

    python -m app.api.contract           # writes the document

It is written as a *surface* rather than as "the app's OpenAPI" so that adding a
second client later is mounting a second router here, not restructuring this
file: ``build_surface_spec`` already generates one surface in isolation. The
second entry has arrived, and it is not a client: the **dev console**, emitted as
``openapi.dev.json``. Nothing generates types from that document — it is checked
for *freshness* instead (``.github/scripts/check-contract-freshness.sh``), because
``check-contract-drift.sh`` diffs a client's generated types against a
regeneration with that client's own pinned codegen, and here there is no client
and no codegen.

The third is the **club website**'s, ``openapi.club.json`` (``docs/adr/0187``
§5): a client of its own, under a prefix of its own, so the two client documents
never share a path (``tests/unit/test_club_surface.py``). The fourth is the
**public site**'s, ``openapi.public.json``: the same again, and the one document
with no bearer scheme in it, because nothing on it takes a session
(``tests/unit/test_public_surface.py``).

**Consequence, stated rather than discovered:** importing the dev router is
unconditional, so this module refuses to import wherever the console is not
served — everywhere but ``local`` (``app/api/dev/gate.py``), which is narrower
than the seeds' own refusal. That makes it a dev-time module like the seeds —
run by ``make openapi``, never by a server. ``app.main`` is what a server
imports, and it reads the gate rather than the router.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, FastAPI

from app.api.dev.routes import dev_api_router
from app.api.streaming import restore_stream_item_types
from app.api.v1.club import club_api_router
from app.api.v1.player import player_api_router
from app.api.v1.public import public_api_router
from app.core.config import get_settings
from app.core.exception_handlers import ErrorResponse

# Written next to this backend's package root, alongside the source the client
# reads with ``openapi-typescript ../backend/openapi.player.json``.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

SURFACES: dict[str, APIRouter] = {
    "player": player_api_router,
    # The games test console's (`docs/adr/0194`): the roster and every route
    # its page presses, as the accounts they name. The page itself is
    # `include_in_schema=False`, and nothing generates types from this document.
    "dev": dev_api_router,
    # The club website's, and nobody else's (`docs/adr/0187` §5). Its paths are
    # all under `/api/v1/club`, so this document and the player's never share
    # one.
    "club": club_api_router,
    # The public site's (`docs/adr/0187` §4–§5): the pages a group link or an
    # email opens without the app. No route on it takes a session.
    "public": public_api_router,
}


#: The name the client generates its error type from.
ERROR_SCHEMA_NAME = "ErrorResponse"


def _document_error_envelope(spec: dict) -> dict:
    """Publish the error envelope as a schema on this surface.

    Registered on ``components`` directly rather than declared per operation:
    the envelope is what *every* failure returns, including the ones no route
    can enumerate — an unrouted path, a rejected body. Attaching a guessed list
    of statuses to each operation would document claims the code does not make.
    """

    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    schemas[ERROR_SCHEMA_NAME] = ErrorResponse.model_json_schema()
    return spec


def build_surface_spec(title: str, router: APIRouter) -> dict:
    """Generate one surface's OpenAPI document in isolation.

    A throwaway app carrying only this surface's routes yields a document scoped
    to exactly that surface, so a second client added later cannot see the
    first's paths.
    """

    settings = get_settings()
    app = FastAPI(title=title, version=settings.VERSION)
    app.include_router(router)
    # The same repair ``app.main`` applies, and for the half that matters here:
    # a streaming route that lost its item type documents an opaque string where
    # the declared envelope should be, and the client would generate no type for
    # it (``app/api/streaming.py``).
    restore_stream_item_types(app)
    return _document_error_envelope(app.openapi())


def write_contracts(root: Path = _BACKEND_ROOT) -> list[Path]:
    written: list[Path] = []
    for surface, router in SURFACES.items():
        spec = build_surface_spec(f"Rakieta {surface.capitalize()} API", router)
        path = root / f"openapi.{surface}.json"
        path.write_text(json.dumps(spec, indent=2) + "\n")
        written.append(path)
    return written


def main() -> None:
    for path in write_contracts():
        print(f"Wrote {path.relative_to(_BACKEND_ROOT)}")


if __name__ == "__main__":
    main()

"""Emit the API contract as two documents, one per client.

One backend deployable serves both surfaces (``docs/adr/0016``), but each client
generates its wire types from its *own* document so neither can take a dependency
on the other's contract (``docs/adr/0006``). ``make openapi`` runs this module;
``make gen-api`` then points each client's codegen at its own file.

    python -m app.api.contract           # writes both documents
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, FastAPI

from app.api.v1.club import club_api_router
from app.api.v1.player import player_api_router
from app.core.config import get_settings

# Written next to this backend's package root, alongside the sources both clients
# read with ``openapi-typescript ../backend/openapi.<surface>.json``.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

SURFACES: dict[str, APIRouter] = {
    "player": player_api_router,
    "club": club_api_router,
}


def build_surface_spec(title: str, router: APIRouter) -> dict:
    """Generate one surface's OpenAPI document in isolation.

    A throwaway app carrying only this surface's routes yields a document scoped
    to exactly that surface — a player client never sees a club path and vice
    versa.
    """

    settings = get_settings()
    app = FastAPI(title=title, version=settings.VERSION)
    app.include_router(router)
    return app.openapi()


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

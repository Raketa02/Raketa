"""The public surface: its own document, no authentication, and no path shared.

The public site generates its wire types from ``openapi.public.json`` and from
nothing else (``docs/adr/0187`` §5). It serves strangers: somebody who tapped a
group link without the app, and somebody who opened an invitation or a reset
email on a laptop. So four claims are asserted here: the committed document is
the one the surface produces, it holds the public pages' operations and only
under its prefix, **no operation on it asks for a session**, and no path is in
two documents.

The freshness gate at the repository root re-emits every document, this one
included (#527); this is what fails the backend's own test run first when the
surface changed without regenerating it.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.api.contract import SURFACES, build_surface_spec

BACKEND_ROOT = Path(__file__).resolve().parents[2]

#: Every operation the public site may call today, as ``method path``.
PUBLIC_OPERATIONS = {
    "get /api/v1/public/friend-links/{code}",
    "get /api/v1/public/groups/{code}",
    "post /api/v1/public/invitations/by-token",
    "post /api/v1/public/invitations/password",
    "post /api/v1/public/password-resets/by-token",
    "post /api/v1/public/password-resets/password",
}


def _operations(spec: dict) -> set[str]:
    return {
        f"{method} {path}" for path, item in spec["paths"].items() for method in item
    }


def _spec() -> dict:
    return build_surface_spec("Rakieta Public API", SURFACES["public"])


def test_the_committed_public_document_is_the_one_the_surface_produces():
    on_disk = json.loads((BACKEND_ROOT / "openapi.public.json").read_text())

    assert on_disk == _spec()


def test_the_public_document_holds_the_public_pages_routes_under_its_prefix():
    spec = _spec()

    assert _operations(spec) == PUBLIC_OPERATIONS
    assert all(path.startswith("/api/v1/public/") for path in spec["paths"])


def test_no_public_operation_asks_for_a_session():
    """The public site has no sign-in, no session and no cookies
    (``docs/adr/0187`` §4). A route that declared the bearer scheme would be
    one the site could never call — and a sign that somebody mounted a player
    route here."""

    spec = _spec()

    secured = sorted(
        f"{method} {path}"
        for path, item in spec["paths"].items()
        for method, operation in item.items()
        if operation.get("security")
    )
    assert secured == []
    assert "securitySchemes" not in spec.get("components", {})


def test_no_path_is_in_the_public_document_and_another():
    public = set(
        json.loads((BACKEND_ROOT / "openapi.public.json").read_text())["paths"]
    )

    for surface in ("player", "club", "dev"):
        other = json.loads((BACKEND_ROOT / f"openapi.{surface}.json").read_text())
        assert not public & set(other["paths"]), surface
        assert not [p for p in other["paths"] if p.startswith("/api/v1/public")]

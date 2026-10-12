"""The club surface: its own document, and no path shared with the player's.

The club website generates its wire types from ``openapi.club.json`` and from
nothing else (``docs/adr/0187`` §5), so three claims are asserted here: the
committed document is the one the surface produces, it holds the club's routes,
and **no path is in both documents** — a club route leaking into the player
app's contract would ship in an app-store release, and a player route in the
club's would be a surface the website could call as a club.

The freshness gate at the repository root re-emits every document, this one
included (#527); this is what fails the backend's own test run first when the
surface changed without regenerating it.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.api.contract import SURFACES, build_surface_spec

BACKEND_ROOT = Path(__file__).resolve().parents[2]

#: Every operation the club website may call today, as ``method path``.
CLUB_OPERATIONS = {
    "post /api/v1/club/sign-up",
    "get /api/v1/club/details",
    "put /api/v1/club/details",
    "post /api/v1/club/auth/login",
    "post /api/v1/club/auth/refresh",
    "post /api/v1/club/auth/logout",
    "post /api/v1/club/auth/forgot-password",
    "post /api/v1/club/auth/forgot-password/claim",
    "post /api/v1/club/auth/forgot-password/new-password",
    "get /api/v1/club/administrators",
    "post /api/v1/club/administrators",
    "post /api/v1/club/administrators/{administrator_id}/invitation",
    "post /api/v1/club/administrators/{administrator_id}/password-reset",
    "delete /api/v1/club/administrators/{administrator_id}",
    "get /api/v1/club/groups",
    "put /api/v1/club/groups/{group_id}/administrator",
    "get /api/v1/club/groups/{group_id}/requests",
    "post /api/v1/club/groups/{group_id}/requests/{player_id}/approve",
    "post /api/v1/club/groups/{group_id}/requests/{player_id}/decline",
    "get /api/v1/club/courts",
    "post /api/v1/club/courts",
    "put /api/v1/club/courts/{court_id}",
    "delete /api/v1/club/courts/{court_id}",
    "put /api/v1/club/raketa-hours",
    "get /api/v1/club/exceptions",
    "post /api/v1/club/exceptions",
    "delete /api/v1/club/exceptions/{exception_id}",
    "get /api/v1/club/prices",
    "put /api/v1/club/prices",
    "get /api/v1/club/raketa-settings",
    "put /api/v1/club/raketa-settings",
    "get /api/v1/club/setup",
    "post /api/v1/club/payments/onboarding-link",
    "get /api/v1/club/bookings",
    "get /api/v1/club/bookings/{booking_id}/free-courts",
    "post /api/v1/club/bookings/{booking_id}/move",
    "get /api/v1/club/bookings/{booking_id}/cancellation/preview",
    "post /api/v1/club/bookings/{booking_id}/cancellation",
    "get /api/v1/club/money",
    "get /api/v1/club/payouts",
}


def _operations(spec: dict) -> set[str]:
    return {
        f"{method} {path}" for path, item in spec["paths"].items() for method in item
    }


def test_the_committed_club_document_is_the_one_the_surface_produces():
    on_disk = json.loads((BACKEND_ROOT / "openapi.club.json").read_text())

    assert on_disk == build_surface_spec("Raketa Club API", SURFACES["club"])


def test_the_club_document_holds_the_club_s_routes_and_only_under_its_prefix():
    spec = build_surface_spec("Raketa Club API", SURFACES["club"])

    assert _operations(spec) == CLUB_OPERATIONS
    assert all(path.startswith("/api/v1/club/") for path in spec["paths"])


def test_no_path_is_in_both_the_club_and_the_player_documents():
    club = json.loads((BACKEND_ROOT / "openapi.club.json").read_text())
    player = json.loads((BACKEND_ROOT / "openapi.player.json").read_text())

    assert not set(club["paths"]) & set(player["paths"])
    assert not [path for path in player["paths"] if path.startswith("/api/v1/club")]

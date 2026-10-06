"""The old loop's routes answer *not found* (#578, #579, PRD #569).

**Challenges and plans are gone**, and with them the old game card's dismissal
(#578); **so are the searches, the deck and the radar** — the shortlist and its
read-back, the line-ups and their forecast, a *Let's play* and its list, a deal
and *Show them again*, a pass, a prompt's *not now* and a reading (#579). A
game is made one way — a group's Games deck books it — and nothing a client
sends reaches any of them any more. Each route is asked **as a signed-in player
with a real id in the path and a body it used to take**, so the answer is the
router's — no such route — and never a refusal some surviving route gave about
the caller, the id or the body.

The removed routes the player document no longer carries are listed by hand
rather than derived from it: a list read off the document could not fail.
"""

from __future__ import annotations

import pytest

from app.shared.ids import new_uuid
from tests.api import players_world as players

#: What each route was sent with, so a body is never the reason it is refused.
_ANY_ID = str(new_uuid())

THE_OLD_LOOP = (
    ("GET", "/api/v1/challenges", None),
    ("POST", "/api/v1/challenges", {"search_id": _ANY_ID, "court": []}),
    ("GET", f"/api/v1/challenges/{_ANY_ID}", None),
    ("POST", f"/api/v1/challenges/{_ANY_ID}/accept", None),
    ("POST", f"/api/v1/challenges/{_ANY_ID}/decline", None),
    ("POST", f"/api/v1/challenges/{_ANY_ID}/departure", None),
    ("POST", f"/api/v1/challenges/{_ANY_ID}/dismissal", None),
    ("POST", f"/api/v1/challenges/{_ANY_ID}/seats", {"court": []}),
    ("POST", f"/api/v1/challenges/{_ANY_ID}/withdrawal", None),
    ("GET", "/api/v1/plans", None),
    ("PUT", f"/api/v1/plans/{_ANY_ID}/place", {"place": "Zabłocie"}),
    ("PUT", f"/api/v1/plans/{_ANY_ID}/day", {"day": "2026-10-10"}),
    ("PUT", f"/api/v1/plans/{_ANY_ID}/hour", {"hour": "18:00"}),
    ("PUT", f"/api/v1/plans/{_ANY_ID}/lock", None),
    ("POST", f"/api/v1/games/{_ANY_ID}/dismissal", None),
    ("POST", "/api/v1/searches", {"sport": "PADEL", "mode": "COMPETITIVE"}),
    ("GET", f"/api/v1/searches/{_ANY_ID}", None),
    ("POST", "/api/v1/lineups", {"sport": "PADEL", "mode": "COMPETITIVE"}),
    ("POST", "/api/v1/forecasts", {"search_id": _ANY_ID, "sport": "PADEL"}),
    (
        "POST",
        "/api/v1/interest",
        {"search_id": _ANY_ID, "sport": "PADEL", "player_id": _ANY_ID},
    ),
    ("GET", "/api/v1/interest", None),
    ("POST", "/api/v1/deck", {"sport": "PADEL"}),
    ("POST", "/api/v1/deck/reset", {"sport": "PADEL"}),
    ("POST", "/api/v1/passes", {"search_id": _ANY_ID, "player_id": _ANY_ID}),
    ("POST", "/api/v1/prompt-declines", {"prompt": "INTENT_DRIFT"}),
    ("POST", "/api/v1/radar", {"sport": "PADEL"}),
)


def _named(route) -> str:
    method, path, _ = route
    return f"{method} {path.replace(_ANY_ID, '{id}')}"


@pytest.mark.parametrize(
    ("method", "path", "body"), THE_OLD_LOOP, ids=[_named(r) for r in THE_OLD_LOOP]
)
async def test_a_route_of_the_old_loop_is_not_found(client, method, path, body):
    _, token = await players.register(client, "reader")

    response = await client.request(
        method, path, json=body, headers=players.auth(token)
    )

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "not_found"


async def test_the_games_list_and_its_pairing_are_still_served(client):
    """The old card's dismissal went; the games list it cleared cards from, and
    the pairing beside it, did not."""

    _, token = await players.register(client, "reader")

    listed = await client.get("/api/v1/games", headers=players.auth(token))
    assert listed.status_code == 200, listed.text
    assert listed.json()["games"] == []
    pairing = await client.get(
        f"/api/v1/games/{_ANY_ID}/pairing", headers=players.auth(token)
    )
    assert pairing.status_code == 404
    assert pairing.json()["code"] == "game_not_found"

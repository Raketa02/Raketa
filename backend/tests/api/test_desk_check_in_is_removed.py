"""**Desk check-in is removed** (#651; ``docs/adr/0195`` §4, §8).

It solved a problem nobody showed was real and put a desk queue in front of the
players at every club that used it, so it goes from every document the backend
emits: the club's route and its day rows' checked-in time, the *We check players
in* setting, the details' code and the tiles' flag, and the test console's press
and situation. What each read still carries is asserted where it is read
(``test_the_club_runs_its_bookings.py``, ``test_home_and_details.py``,
``test_club_raketa_settings.py``, the console's own files); this holds the
contract whole, and the routes that are no longer anybody's.
"""

from __future__ import annotations

import json
import re
from uuid import uuid4

import pytest

from app.api.contract import SURFACES, build_surface_spec
from tests.api.proposals_world import a_club_and_its_desk

#: Every spelling the removed feature was written in — *check-in*, *Check in*,
#: ``check_in``, ``checked_in_at``, *We check players in*, *the club checked
#: in*, *checked in ✓* — and not a form *checked in the order* it is read.
_CHECK_IN = re.compile(
    r"check[-_ ]?ins?\b|checked[-_]in\b|checks? players in"
    r"|(?:club|desk|\*)\s*checked (?:\w+ )?in\b",
    re.IGNORECASE,
)


def _code_of(response) -> str:
    return response.json()["code"]


@pytest.mark.parametrize("surface", sorted(SURFACES))
def test_no_api_document_mentions_check_in(surface):
    document = json.dumps(
        build_surface_spec(f"Raketa {surface} API", SURFACES[surface])
    )

    assert _CHECK_IN.findall(document) == []


async def test_the_club_has_no_check_in_route(client):
    _, desk = await a_club_and_its_desk(client)

    pressed = await client.post(
        "/api/v1/club/check-ins", json={"code": "ABCDEF"}, headers=desk
    )

    assert (pressed.status_code, _code_of(pressed)) == (404, "not_found")


async def test_the_console_has_no_check_in_press_and_no_check_in_situation(client):
    pressed = await client.post(
        f"/dev/clubs/{uuid4()}/check-ins", json={"code": "ABCDEF"}
    )
    situation = await client.post(
        "/dev/situations/check-in-at-the-club",
        json={
            "group_id": str(uuid4()),
            "sport": "PADEL",
            "protagonist_id": str(uuid4()),
        },
    )

    assert (pressed.status_code, _code_of(pressed)) == (404, "not_found")
    assert (situation.status_code, _code_of(situation)) == (404, "not_found")

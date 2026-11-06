"""A club's Raketa settings (#535, the mechanics §16.3, §16.6, §16.15, the
screens B5).

**One way of working, Only Raketa, until Raketa is the club's booking
software** (#670; ``docs/adr/0196`` §1): nothing to choose, so the settings
stand on their own — the release lead, the free-cancellation cut-off, other
clubs' courts for the club's groups, and pause, **confirmed** by saving them,
defaults included. *How you work with Raketa*, the minimum notice and the time
to confirm went with Instant and On request; *We check players in* went with
desk check-in (#651).
"""

from __future__ import annotations

import pytest

from tests.api.club_courts_world import (
    RAKETA_SETTINGS,
    a_desk,
    confirms_settings,
    settings,
)

DEFAULTS = {
    "release_lead_days": 3,
    "cut_off_hours": 24,
    # On by default since #746 (docs/adr/0202 §7).
    "other_clubs_courts": {"offered": True, "within_km": 10},
    "paused": False,
}


async def read(client, desk) -> dict:
    answered = await client.get(RAKETA_SETTINGS, headers=desk)
    assert answered.status_code == 200, answered.text
    return answered.json()


async def test_a_club_that_has_done_nothing_reads_the_defaults_and_no_way(client):
    _, desk = await a_desk(client)

    assert await read(client, desk) == DEFAULTS


async def test_the_desk_saves_its_settings_with_nothing_to_choose_first(client):
    _, desk = await a_desk(client)
    changed = settings(
        release_lead_days=5,
        cut_off_hours=12,
        # Switched off: the club's groups play only at the club.
        other_clubs_courts={"offered": False, "within_km": 15},
    )

    saved = await confirms_settings(client, desk, **changed)

    assert saved == changed
    assert await read(client, desk) == changed


async def test_there_is_no_way_of_working_to_choose(client):
    _, desk = await a_desk(client)

    refused = await client.put(
        "/api/v1/club/way-of-working",
        json={"way_of_working": "ONLY_RAKETA"},
        headers=desk,
    )

    assert refused.status_code in (404, 405), refused.text
    assert await read(client, desk) == DEFAULTS


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("way_of_working", "INSTANT"),
        ("minimum_notice_hours", 2),
        ("time_to_confirm_minutes", 30),
        ("check_in", True),
    ],
)
async def test_a_form_still_sending_a_removed_setting_is_refused(client, field, value):
    """Instant and On request are gone (#670), and desk check-in (#651): a form
    that still sends one of their fields is refused for a field the settings do
    not have, and nothing is saved."""

    _, desk = await a_desk(client)

    refused = await client.put(
        RAKETA_SETTINGS, json=settings(**{field: value}), headers=desk
    )

    assert (refused.status_code, refused.json()["code"]) == (422, "validation_error")
    assert await read(client, desk) == DEFAULTS


async def test_the_desk_pauses_raketa_bookings_and_resumes_them(client):
    _, desk = await a_desk(client)

    paused = await confirms_settings(client, desk, paused=True)
    resumed = await confirms_settings(client, desk, paused=False)

    assert paused["paused"] is True
    assert resumed["paused"] is False


@pytest.mark.parametrize(
    ("field", "value", "least", "most"),
    [
        ("release_lead_days", 0, 1, 13),
        ("release_lead_days", 14, 1, 13),
        ("cut_off_hours", -1, 0, 72),
        ("cut_off_hours", 73, 0, 72),
        ("other_clubs_courts", {"offered": True, "within_km": 0}, 1, 50),
        ("other_clubs_courts", {"offered": False, "within_km": 51}, 1, 50),
    ],
)
async def test_a_setting_out_of_its_range_is_refused_with_the_range(
    client, field, value, least, most
):
    _, desk = await a_desk(client)

    refused = await client.put(
        RAKETA_SETTINGS, json=settings(**{field: value}), headers=desk
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "setting_out_of_range"
    assert refused.json()["details"] == {"field": field, "least": least, "most": most}
    assert await read(client, desk) == DEFAULTS

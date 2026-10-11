"""How a club works with Raketa, and the settings that go with it (#535, the
mechanics §16.3, §16.6, §16.15, the screens B5).

**One way for the whole club** — Only Raketa, Instant or On request — chosen on
its own, and changeable later. Then the settings, **confirmed** by saving them,
defaults included: the release lead, the free-cancellation cut-off, the minimum
notice, the time to confirm, other clubs' courts for the club's groups, and
pause. The settings wait for a way, because which of them matter depends on it.
*We check players in* is gone with desk check-in (#651).
"""

from __future__ import annotations

import pytest

from tests.api.club_courts_world import (
    RAKETA_SETTINGS,
    WAY_OF_WORKING,
    a_desk,
    chooses,
    confirms_settings,
    settings,
)

DEFAULTS = {
    "way_of_working": None,
    "release_lead_days": 3,
    "cut_off_hours": 24,
    "minimum_notice_hours": 2,
    "time_to_confirm_minutes": 30,
    "other_clubs_courts": {"offered": False, "within_km": 10},
    "paused": False,
}


async def read(client, desk) -> dict:
    answered = await client.get(RAKETA_SETTINGS, headers=desk)
    assert answered.status_code == 200, answered.text
    return answered.json()


async def test_a_club_that_has_done_nothing_reads_no_way_and_the_defaults(client):
    _, desk = await a_desk(client)

    assert await read(client, desk) == DEFAULTS


@pytest.mark.parametrize("way", ["ONLY_RAKETA", "INSTANT", "ON_REQUEST"])
async def test_the_desk_chooses_how_it_works_with_raketa(client, way):
    _, desk = await a_desk(client)

    chosen = await chooses(client, desk, way)

    assert chosen == {**DEFAULTS, "way_of_working": way}
    assert await read(client, desk) == chosen


async def test_the_settings_wait_for_a_way_of_working(client):
    _, desk = await a_desk(client)

    refused = await client.put(RAKETA_SETTINGS, json=settings(), headers=desk)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "way_of_working_not_chosen"
    assert await read(client, desk) == DEFAULTS


async def test_the_desk_saves_its_settings_and_changing_the_way_keeps_them(client):
    _, desk = await a_desk(client)
    await chooses(client, desk, "ON_REQUEST")
    changed = settings(
        release_lead_days=5,
        cut_off_hours=12,
        minimum_notice_hours=3,
        time_to_confirm_minutes=45,
        other_clubs_courts={"offered": True, "within_km": 15},
    )

    saved = await confirms_settings(client, desk, **changed)

    assert saved == {"way_of_working": "ON_REQUEST", **changed}
    assert await chooses(client, desk, "INSTANT") == {
        "way_of_working": "INSTANT",
        **changed,
    }


async def test_the_settings_no_longer_take_we_check_players_in(client):
    """Desk check-in is removed (#651): a form that still sends the switch is
    refused for a field the settings do not have, and nothing is saved."""

    _, desk = await a_desk(client)
    await chooses(client, desk, "INSTANT")

    refused = await client.put(
        RAKETA_SETTINGS, json=settings(check_in=True), headers=desk
    )

    assert (refused.status_code, refused.json()["code"]) == (422, "validation_error")
    assert await read(client, desk) == {**DEFAULTS, "way_of_working": "INSTANT"}


async def test_the_desk_pauses_raketa_bookings_and_resumes_them(client):
    _, desk = await a_desk(client)
    await chooses(client, desk, "INSTANT")

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
        ("minimum_notice_hours", 0, 1, 48),
        ("minimum_notice_hours", 49, 1, 48),
        ("time_to_confirm_minutes", 4, 5, 60),
        ("time_to_confirm_minutes", 61, 5, 60),
        ("other_clubs_courts", {"offered": True, "within_km": 0}, 1, 50),
        ("other_clubs_courts", {"offered": False, "within_km": 51}, 1, 50),
    ],
)
async def test_a_setting_out_of_its_range_is_refused_with_the_range(
    client, field, value, least, most
):
    _, desk = await a_desk(client)
    await chooses(client, desk, "ONLY_RAKETA")

    refused = await client.put(
        RAKETA_SETTINGS, json=settings(**{field: value}), headers=desk
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "setting_out_of_range"
    assert refused.json()["details"] == {"field": field, "least": least, "most": most}
    assert await read(client, desk) == {**DEFAULTS, "way_of_working": "ONLY_RAKETA"}


async def test_a_way_outside_the_three_is_not_a_way(client):
    _, desk = await a_desk(client)

    refused = await client.put(
        WAY_OF_WORKING, json={"way_of_working": "SOMETIMES"}, headers=desk
    )

    assert refused.status_code == 422, refused.text

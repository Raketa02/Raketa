"""A club lists its courts and the hours each offers Raketa, on the club surface
(#535, the mechanics §16.4–§16.5, the screens B3).

A court has a name as the club uses it, **one sport** from the club's own, and
is indoor or outdoor. It can be switched off — kept, but not offered to Raketa —
and deleted, except while it has bookings ahead of it. Its Rakieta hours are the
player's own grid, seven days by sixteen hours from 07:00, because an hour
outside it could never match anybody.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import ANY
from uuid import uuid4

import pytest

from tests.api.administration_world import player_signs_up
from tests.api.club_courts_world import (
    COURTS,
    PRICES,
    RAKIETA_HOURS,
    a_desk,
    adds_a_court,
    court_path,
    sets_hours,
    sets_prices,
    with_bookings,
)

DETAILS = "/api/v1/club/details"


async def test_a_desk_adds_a_court_and_reads_it_back(client):
    _, desk = await a_desk(client)

    added = await client.post(
        COURTS,
        json={"name": "  Kort   centralny ", "sport": "TENNIS", "indoor": False},
        headers=desk,
    )

    assert added.status_code == 201, added.text
    court = added.json()
    # Trimmed and collapsed as the desk's other text is, switched on, and
    # offering nothing until its hours are painted.
    assert court == {
        "id": ANY,
        "name": "Kort centralny",
        "sport": "TENNIS",
        "indoor": False,
        "offered": True,
        "hours": [],
    }

    listed = await client.get(COURTS, headers=desk)

    assert listed.status_code == 200, listed.text
    assert listed.json() == {"courts": [court]}


async def test_the_courts_are_listed_in_the_order_they_were_added(client):
    _, desk = await a_desk(client)
    names = ["Court 2", "Court 1", "Kort centralny"]
    for name in names:
        await adds_a_court(client, desk, name=name)

    listed = await client.get(COURTS, headers=desk)

    assert [court["name"] for court in listed.json()["courts"]] == names


@pytest.mark.parametrize("name", ["", "   ", "x" * 41])
async def test_a_name_the_desk_has_to_correct_is_refused_under_its_field(client, name):
    _, desk = await a_desk(client)

    refused = await client.post(
        COURTS, json={"name": name, "sport": "PADEL", "indoor": True}, headers=desk
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "court_name_invalid"
    assert refused.json()["details"] == {"field": "name"}
    assert (await client.get(COURTS, headers=desk)).json() == {"courts": []}


async def test_two_courts_of_one_club_cannot_share_a_name_whatever_its_case(client):
    _, desk = await a_desk(client)
    await adds_a_court(client, desk, name="Court 2")

    refused = await client.post(
        COURTS,
        json={"name": " court  2", "sport": "TENNIS", "indoor": False},
        headers=desk,
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "court_name_taken"
    assert refused.json()["details"] == {"field": "name"}


async def test_two_clubs_may_each_have_a_court_2(client):
    _, ogrody = await a_desk(client)
    _, bonarka = await a_desk(client, name="Bonarka Arena", email="desk@bonarka.pl")
    await adds_a_court(client, ogrody, name="Court 2")

    await adds_a_court(client, bonarka, name="Court 2")

    listed = await client.get(COURTS, headers=ogrody)
    assert [court["name"] for court in listed.json()["courts"]] == ["Court 2"]


async def test_a_court_plays_one_of_the_club_s_own_sports(client):
    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))

    refused = await client.post(
        COURTS,
        json={"name": "Court 1", "sport": "SQUASH", "indoor": True},
        headers=desk,
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "court_sport_not_offered"
    assert refused.json()["details"] == {"field": "sport"}


async def test_a_player_s_session_cannot_add_a_court(client):
    player = await player_signs_up(client)

    refused = await client.post(
        COURTS,
        json={"name": "Court 1", "sport": "PADEL", "indoor": True},
        headers=player,
    )

    assert refused.status_code == 401, refused.text


async def test_the_desk_edits_a_court_s_name_sport_and_roof(client):
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1", sport="PADEL")

    changed = await client.put(
        court_path(court["id"]),
        json={
            "name": "Kort centralny",
            "sport": "TENNIS",
            "indoor": False,
            "offered": True,
        },
        headers=desk,
    )

    assert changed.status_code == 200, changed.text
    assert changed.json() == {
        **court,
        "name": "Kort centralny",
        "sport": "TENNIS",
        "indoor": False,
    }
    assert (await client.get(COURTS, headers=desk)).json() == {
        "courts": [changed.json()]
    }


async def test_a_court_switched_off_keeps_its_hours_and_comes_back_on(client):
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(1, 17), (1, 18)])

    off = await client.put(
        court_path(court["id"]),
        json={"name": "Court 1", "sport": "PADEL", "indoor": True, "offered": False},
        headers=desk,
    )

    assert off.status_code == 200, off.text
    assert off.json()["offered"] is False
    assert off.json()["hours"] == [{"day": 1, "hour": 17}, {"day": 1, "hour": 18}]

    on = await client.put(
        court_path(court["id"]),
        json={"name": "Court 1", "sport": "PADEL", "indoor": True, "offered": True},
        headers=desk,
    )

    assert on.json()["offered"] is True
    assert on.json()["hours"] == off.json()["hours"]


@pytest.mark.parametrize(
    ("change", "code", "field"),
    [
        ({"name": "  "}, "court_name_invalid", "name"),
        ({"sport": "SQUASH"}, "court_sport_not_offered", "sport"),
    ],
)
async def test_an_edit_the_desk_has_to_correct_is_refused_under_its_field(
    client, change, code, field
):
    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))
    court = await adds_a_court(client, desk, name="Court 1", sport="PADEL")
    body = {"name": "Court 1", "sport": "PADEL", "indoor": True, "offered": True}

    refused = await client.put(
        court_path(court["id"]), json={**body, **change}, headers=desk
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == code
    assert refused.json()["details"] == {"field": field}
    assert (await client.get(COURTS, headers=desk)).json() == {"courts": [court]}


async def test_a_court_keeps_its_own_name_in_another_case_but_not_a_neighbour_s(
    client,
):
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1")
    await adds_a_court(client, desk, name="Court 2")

    recased = await client.put(
        court_path(court["id"]),
        json={"name": "COURT 1", "sport": "PADEL", "indoor": True, "offered": True},
        headers=desk,
    )
    taken = await client.put(
        court_path(court["id"]),
        json={"name": "court 2", "sport": "PADEL", "indoor": True, "offered": True},
        headers=desk,
    )

    assert recased.status_code == 200, recased.text
    assert recased.json()["name"] == "COURT 1"
    assert taken.status_code == 409, taken.text
    assert taken.json()["code"] == "court_name_taken"


async def test_the_desk_deletes_a_court(client):
    _, desk = await a_desk(client)
    kept = await adds_a_court(client, desk, name="Court 1")
    gone = await adds_a_court(client, desk, name="Court 2")

    deleted = await client.delete(court_path(gone["id"]), headers=desk)

    assert deleted.status_code == 204, deleted.text
    assert (await client.get(COURTS, headers=desk)).json() == {"courts": [kept]}


async def test_a_court_nobody_has_or_another_club_s_is_not_found(client):
    _, ogrody = await a_desk(client)
    _, bonarka = await a_desk(client, name="Bonarka Arena", email="desk@bonarka.pl")
    theirs = await adds_a_court(client, bonarka, name="Court 1")
    body = {"name": "Court 1", "sport": "PADEL", "indoor": True, "offered": True}

    for court_id in (theirs["id"], str(uuid4())):
        changed = await client.put(court_path(court_id), json=body, headers=ogrody)
        deleted = await client.delete(court_path(court_id), headers=ogrody)

        for refused in (changed, deleted):
            assert refused.status_code == 404, refused.text
            assert refused.json()["code"] == "court_not_found"
    assert (await client.get(COURTS, headers=bonarka)).json() == {"courts": [theirs]}


async def test_a_court_with_a_booking_ahead_can_be_switched_off_but_not_deleted(
    client, app, clock
):
    """The mechanics §16.4 and the screens B3: a booked game is played as
    booked, so the court it is on stays — off, if the desk wants it off."""

    booked = with_bookings(app)
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1", sport="PADEL")
    booked.book(court["id"], clock.now() + timedelta(days=2))

    deleted = await client.delete(court_path(court["id"]), headers=desk)
    resported = await client.put(
        court_path(court["id"]),
        json={"name": "Court 1", "sport": "TENNIS", "indoor": True, "offered": True},
        headers=desk,
    )
    off = await client.put(
        court_path(court["id"]),
        json={
            "name": "Court 1 (repair)",
            "sport": "PADEL",
            "indoor": True,
            "offered": False,
        },
        headers=desk,
    )

    for refused in (deleted, resported):
        assert refused.status_code == 409, refused.text
        assert refused.json()["code"] == "court_has_bookings"
    assert off.status_code == 200, off.text
    assert off.json()["offered"] is False


async def test_a_court_whose_bookings_are_over_can_be_deleted(client, app, clock):
    booked = with_bookings(app)
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1")
    booked.book(court["id"], clock.now() - timedelta(hours=2))

    deleted = await client.delete(court_path(court["id"]), headers=desk)

    assert deleted.status_code == 204, deleted.text


# --------------------------------------------------------------------------- #
# Weekly hours for Rakieta
# --------------------------------------------------------------------------- #


async def test_one_save_gives_the_same_week_to_every_court_named(client):
    """*Copy to other courts* and *All courts of a sport* are one save."""

    _, desk = await a_desk(client)
    one = await adds_a_court(client, desk, name="Court 1")
    two = await adds_a_court(client, desk, name="Court 2")
    three = await adds_a_court(client, desk, name="Court 3")

    saved = await sets_hours(
        client,
        desk,
        [one["id"], three["id"], one["id"]],
        # Out of order and one cell twice: the week is a set, in the grid's order.
        [(6, 9), (1, 17), (1, 18), (6, 9), (6, 10)],
    )

    week = [
        {"day": 1, "hour": 17},
        {"day": 1, "hour": 18},
        {"day": 6, "hour": 9},
        {"day": 6, "hour": 10},
    ]
    assert [court["hours"] for court in saved["courts"]] == [week, [], week]
    assert saved == (await client.get(COURTS, headers=desk)).json()
    assert two["hours"] == []


async def test_a_blank_week_is_a_court_offering_nothing(client):
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(2, 19)])

    cleared = await sets_hours(client, desk, [court["id"]], [])

    assert cleared["courts"][0]["hours"] == []


async def test_a_court_the_club_does_not_have_refuses_the_whole_save(client):
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1")

    refused = await client.put(
        RAKIETA_HOURS,
        json={
            "court_ids": [court["id"], str(uuid4())],
            "hours": [{"day": 1, "hour": 7}],
        },
        headers=desk,
    )

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "court_not_found"
    assert (await client.get(COURTS, headers=desk)).json()["courts"][0]["hours"] == []


@pytest.mark.parametrize(
    "cell", [{"day": 1, "hour": 6}, {"day": 1, "hour": 23}, {"day": 8, "hour": 9}]
)
async def test_an_hour_off_the_grid_is_not_an_hour(client, cell):
    """07:00–23:00, the player's own grid: an hour outside it could never match
    anybody (the screens B3)."""

    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 1")

    refused = await client.put(
        RAKIETA_HOURS, json={"court_ids": [court["id"]], "hours": [cell]}, headers=desk
    )

    assert refused.status_code == 422, refused.text


# --------------------------------------------------------------------------- #
# The club's own sports
# --------------------------------------------------------------------------- #


def details(sports: list[str]) -> dict:
    return {
        "name": "Ogrody 33",
        "district": "Grzegórzki",
        "city": "Kraków",
        "sports": sports,
        "point": {"latitude": 50.06, "longitude": 19.95},
    }


async def test_the_desk_cannot_untick_a_sport_its_courts_play(client):
    """A court plays one of the club's own sports, so the sport stays ticked
    while a court plays it — switched off or not — and the refusal names the
    first such court (the club's order)."""

    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))
    await adds_a_court(client, desk, name="Court 1", sport="PADEL")
    tennis = await adds_a_court(client, desk, name="Kort centralny", sport="TENNIS")
    await client.put(
        court_path(tennis["id"]),
        json={
            "name": "Kort centralny",
            "sport": "TENNIS",
            "indoor": False,
            "offered": False,
        },
        headers=desk,
    )

    refused = await client.put(DETAILS, json=details(["PADEL"]), headers=desk)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "club_sport_has_courts"
    assert refused.json()["details"] == {
        "field": "sports",
        "sport": "TENNIS",
        "court": "Kort centralny",
    }

    assert (
        await client.delete(court_path(tennis["id"]), headers=desk)
    ).status_code == 204
    saved = await client.put(DETAILS, json=details(["PADEL"]), headers=desk)

    assert saved.status_code == 200, saved.text
    assert saved.json()["sports"] == ["PADEL"]


async def test_a_sport_the_club_stopped_offering_leaves_the_price_table(client):
    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))
    await sets_prices(
        client,
        desk,
        [
            {"sport": "PADEL", "price_grosze": 120_00, "bands": []},
            {"sport": "TENNIS", "price_grosze": 80_00, "bands": []},
        ],
    )

    assert (
        await client.put(DETAILS, json=details(["PADEL"]), headers=desk)
    ).status_code == 200

    read = await client.get(PRICES, headers=desk)
    assert [row["sport"] for row in read.json()["prices"]] == ["PADEL"]

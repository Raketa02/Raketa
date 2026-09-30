"""A club closes hours without touching its pattern — an hour, a day or a date
range, on every court or some of them, with a reason for its own records
(#535, the mechanics §16.5, the screens B3).

**Days are the club's own**: a local date in Warsaw, where every seeded club is.
An exception over an hour with cards on it is allowed — the cards move or
disappear — and one over a **booking** is refused, naming the booking to cancel
first.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import ANY
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from tests.api.club_courts_world import (
    COURTS,
    EXCEPTIONS,
    a_desk,
    adds_a_court,
    court_path,
    exception_path,
    with_bookings,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def today(clock) -> date:
    return clock.now().astimezone(WARSAW).date()


def at(day: date, hour: int) -> datetime:
    return datetime(day.year, day.month, day.day, hour, tzinfo=WARSAW)


def an_exception(first: date, last: date | None = None, **overrides) -> dict:
    return {
        "court_ids": None,
        "first_day": first.isoformat(),
        "last_day": (last or first).isoformat(),
        "from_hour": None,
        "until_hour": None,
        "reason": "Tournament",
        **overrides,
    }


async def adds(client, desk, body: dict) -> dict:
    added = await client.post(EXCEPTIONS, json=body, headers=desk)
    assert added.status_code == 201, added.text
    return added.json()


async def listed(client, desk) -> list[dict]:
    read = await client.get(EXCEPTIONS, headers=desk)
    assert read.status_code == 200, read.text
    return read.json()["exceptions"]


async def test_a_tournament_closes_every_court_for_two_days(client, clock):
    _, desk = await a_desk(client)
    first = today(clock) + timedelta(days=4)

    added = await adds(
        client,
        desk,
        an_exception(first, first + timedelta(days=1), reason=" Tournament "),
    )

    assert added == {
        "id": ANY,
        "court_ids": None,
        "first_day": first.isoformat(),
        "last_day": (first + timedelta(days=1)).isoformat(),
        "from_hour": None,
        "until_hour": None,
        "reason": "Tournament",
    }
    assert await listed(client, desk) == [added]


async def test_a_repair_closes_hours_on_one_court_and_the_list_runs_by_day(
    client, clock
):
    _, desk = await a_desk(client)
    court = await adds_a_court(client, desk, name="Court 2")
    later = await adds(client, desk, an_exception(today(clock) + timedelta(days=9)))

    repair = await adds(
        client,
        desk,
        an_exception(
            today(clock) + timedelta(days=5),
            court_ids=[court["id"]],
            from_hour=9,
            until_hour=12,
            reason="Repair",
        ),
    )

    assert repair["court_ids"] == [court["id"]]
    assert (repair["from_hour"], repair["until_hour"]) == (9, 12)
    assert await listed(client, desk) == [repair, later]


@pytest.mark.parametrize(
    ("overrides", "code", "field"),
    [
        ({"last_day": "SHIFT:-1"}, "exception_days_invalid", "days"),
        ({"from_hour": 9}, "exception_hours_invalid", "hours"),
        ({"until_hour": 12}, "exception_hours_invalid", "hours"),
        ({"from_hour": 12, "until_hour": 12}, "exception_hours_invalid", "hours"),
        ({"from_hour": 6, "until_hour": 9}, "exception_hours_invalid", "hours"),
        ({"from_hour": 22, "until_hour": 24}, "exception_hours_invalid", "hours"),
        ({"reason": "  "}, "exception_reason_invalid", "reason"),
        ({"reason": "x" * 81}, "exception_reason_invalid", "reason"),
        ({"court_ids": []}, "exception_courts_required", "courts"),
    ],
)
async def test_what_the_desk_has_to_correct_is_refused_under_its_field(
    client, clock, overrides, code, field
):
    _, desk = await a_desk(client)
    first = today(clock) + timedelta(days=3)
    if overrides.get("last_day") == "SHIFT:-1":
        overrides = {"last_day": (first - timedelta(days=1)).isoformat()}

    refused = await client.post(
        EXCEPTIONS, json=an_exception(first, **overrides), headers=desk
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == code
    assert refused.json()["details"] == {"field": field}
    assert await listed(client, desk) == []


async def test_a_court_the_club_does_not_have_is_not_found(client, clock):
    _, desk = await a_desk(client)

    refused = await client.post(
        EXCEPTIONS,
        json=an_exception(today(clock), court_ids=[str(uuid4())]),
        headers=desk,
    )

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "court_not_found"


async def test_closing_days_already_over_changes_nothing_and_is_refused(client, clock):
    _, desk = await a_desk(client)
    yesterday = today(clock) - timedelta(days=1)

    refused = await client.post(
        EXCEPTIONS,
        json=an_exception(yesterday - timedelta(days=2), yesterday),
        headers=desk,
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "exception_in_the_past"
    assert refused.json()["details"] == {"field": "days"}


async def test_an_exception_is_listed_through_its_last_day_and_not_after(client, clock):
    _, desk = await a_desk(client)
    added = await adds(client, desk, an_exception(today(clock)))

    assert await listed(client, desk) == [added]

    clock.move(timedelta(days=1))

    assert await listed(client, desk) == []


async def test_the_desk_removes_an_exception(client, clock):
    _, desk = await a_desk(client)
    kept = await adds(client, desk, an_exception(today(clock) + timedelta(days=1)))
    gone = await adds(client, desk, an_exception(today(clock) + timedelta(days=2)))

    removed = await client.delete(exception_path(gone["id"]), headers=desk)
    again = await client.delete(exception_path(gone["id"]), headers=desk)

    assert removed.status_code == 204, removed.text
    assert again.status_code == 404, again.text
    assert again.json()["code"] == "exception_not_found"
    assert await listed(client, desk) == [kept]


async def test_another_club_s_exception_is_not_found(client, clock):
    _, ogrody = await a_desk(client)
    _, bonarka = await a_desk(client, name="Bonarka Arena", email="desk@bonarka.pl")
    theirs = await adds(client, bonarka, an_exception(today(clock)))

    refused = await client.delete(exception_path(theirs["id"]), headers=ogrody)

    assert refused.status_code == 404, refused.text
    assert await listed(client, bonarka) == [theirs]


async def test_a_deleted_court_leaves_the_exceptions_that_named_it(client, clock):
    _, desk = await a_desk(client)
    one = await adds_a_court(client, desk, name="Court 1")
    two = await adds_a_court(client, desk, name="Court 2")
    day = today(clock) + timedelta(days=3)
    both = await adds(client, desk, an_exception(day, court_ids=[one["id"], two["id"]]))
    await adds(client, desk, an_exception(day, court_ids=[two["id"]], reason="Repair"))

    assert (await client.delete(court_path(two["id"]), headers=desk)).status_code == 204

    # The one that named both now names the court that is left; the one that
    # named only the deleted court closes nothing, and is gone.
    assert await listed(client, desk) == [{**both, "court_ids": [one["id"]]}]


async def test_closing_an_hour_a_booking_holds_is_refused_naming_the_booking(
    client, app, clock
):
    booked = with_bookings(app)
    _, desk = await a_desk(client)
    one = await adds_a_court(client, desk, name="Court 1")
    two = await adds_a_court(client, desk, name="Court 2")
    day = today(clock) + timedelta(days=2)
    booking_id = booked.book(one["id"], at(day, 18))

    over_the_booking = [
        an_exception(day),
        an_exception(day, court_ids=[one["id"]]),
        an_exception(day - timedelta(days=1), day + timedelta(days=1)),
        an_exception(day, court_ids=[one["id"]], from_hour=17, until_hour=19),
    ]
    for body in over_the_booking:
        refused = await client.post(EXCEPTIONS, json=body, headers=desk)

        assert refused.status_code == 409, refused.text
        assert refused.json()["code"] == "court_booked_then"
        assert refused.json()["details"] == {
            "court_id": one["id"],
            "booking_id": booking_id,
            "starts_at": ANY,
        }
        assert datetime.fromisoformat(refused.json()["details"]["starts_at"]) == at(
            day, 18
        )

    beside_the_booking = [
        an_exception(day, court_ids=[two["id"]]),
        an_exception(day, court_ids=[one["id"]], from_hour=19, until_hour=23),
        an_exception(day, from_hour=7, until_hour=18),
        an_exception(day + timedelta(days=1)),
    ]
    for body in beside_the_booking:
        await adds(client, desk, body)
    assert len(await listed(client, desk)) == len(beside_the_booking)
    assert (await client.get(COURTS, headers=desk)).status_code == 200

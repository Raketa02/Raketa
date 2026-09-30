"""The seeded clubs' courts, read back the way the club website reads them
(#535).

``app/seeds/club_courts.py`` sets every seeded club up **through the use cases a
desk's pages run**, so each is asserted by signing in as its desk and reading
its Overview, Courts & prices and Raketa settings — never a stream or a table.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.api.dependencies import get_clock
from app.core.config import get_settings
from app.kernel import instant
from app.seeds.catalog import SEED_PASSWORD, Centre
from app.seeds.club_courts import SEED_CLUB_COURTS, write_the_club_courts
from app.seeds.clubs import SEED_CLUBS, desk_email, write_the_clubs
from tests.api.club_courts_world import (
    COURTS,
    EXCEPTIONS,
    PRICES,
    RAKETA_SETTINGS,
    SETUP,
)
from tests.api.test_clubs import SIGN_IN, bearer
from tests.unit.fake_clock import MovableClock

NOW = instant(datetime(2026, 10, 5, 8, tzinfo=ZoneInfo("Europe/Warsaw")))
KRAKOW = Centre(latitude=50.06, longitude=19.94)


@pytest.fixture
def clock(app):
    fixed = MovableClock(NOW)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


async def seeded(session_factory):
    clubs = await write_the_clubs(
        session_factory, settings=get_settings(), now=NOW, centre=KRAKOW
    )
    return await write_the_club_courts(
        session_factory, settings=get_settings(), now=NOW, clubs=clubs
    )


async def desk_of(client, name: str) -> dict:
    club = next(club for club in SEED_CLUBS if club.name == name)
    signed_in = await client.post(
        SIGN_IN, json={"email": desk_email(club), "password": SEED_PASSWORD}
    )
    assert signed_in.status_code == 200, signed_in.text
    return bearer(signed_in.json())


async def read(client, desk: dict, path: str) -> dict:
    answered = await client.get(path, headers=desk)
    assert answered.status_code == 200, answered.text
    return answered.json()


async def test_the_clubs_work_all_three_ways_with_one_not_live_and_one_paused(
    client, clock, session_factory
):
    report = await seeded(session_factory)

    ways, live, paused = Counter(), [], []
    for declared in SEED_CLUB_COURTS:
        desk = await desk_of(client, declared.club)
        settings = await read(client, desk, RAKETA_SETTINGS)
        setup = await read(client, desk, SETUP)
        ways[settings["way_of_working"]] += 1
        if setup["live"]:
            live.append(declared.club)
        if settings["paused"]:
            paused.append(declared.club)

    assert set(ways) == {"ONLY_RAKETA", "INSTANT", "ON_REQUEST"}
    assert sorted(live) == sorted(
        club.name for club in SEED_CLUBS if club.name != "Wisła Park"
    )
    assert paused == ["Zabłocie Sport"]
    assert all(entry.for_sale > 0 for entry in report.clubs if entry.live)


async def test_the_club_that_is_not_live_has_half_its_checklist_done(
    client, clock, session_factory
):
    await seeded(session_factory)

    setup = await read(client, await desk_of(client, "Wisła Park"), SETUP)

    assert {row["step"]: row["state"] for row in setup["steps"]} == {
        "CONNECT_PAYMENTS": "PENDING",
        "WAY_OF_WORKING": "DONE",
        "COURTS": "DONE",
        "HOURS_AND_PRICES": "TO_DO",
        "SETTINGS": "TO_DO",
    }


async def test_every_club_has_courts_per_sport_hours_an_exception_and_bands(
    client, clock, session_factory
):
    """Every club has a court of each sport it offers, painted hours and one
    exception; every club but the one left half set up prices each sport, with
    a band."""

    await seeded(session_factory)

    for declared in SEED_CLUB_COURTS:
        desk = await desk_of(client, declared.club)
        courts = (await read(client, desk, COURTS))["courts"]
        prices = (await read(client, desk, PRICES))["prices"]
        exceptions = (await read(client, desk, EXCEPTIONS))["exceptions"]

        sports = {row["sport"] for row in prices}
        assert {court["sport"] for court in courts} == sports, declared.club
        assert all(court["hours"] for court in courts), declared.club
        assert len(exceptions) == 1, declared.club
        priced = [row["price_grosze"] and row["bands"] for row in prices]
        assert all(priced) if declared.confirmed else not any(priced), declared.club


async def test_a_second_run_sets_nobody_up_twice(client, clock, session_factory):
    await seeded(session_factory)
    desk = await desk_of(client, "Bonarka Arena")
    before = await read(client, desk, COURTS)

    again = await seeded(session_factory)

    assert not any(entry.set_up_by_this_run for entry in again.clubs)
    assert await read(client, desk, COURTS) == before

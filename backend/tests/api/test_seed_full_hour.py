"""Ogrody 33 full at one hour, read back the way the player app and the club
website read it (#746; ``docs/adr/0202`` §7).

``app/seeds/full_hour.py`` closes every Ogrody 33 court for an hour **through the
use case the desk's Hours & exceptions run**, so it is asserted by signing in —
as the protagonist reading Post a game in *Ogrody 33 Club*, and as the desk
reading its exceptions — never by looking in a table. A second run closes
nothing twice.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.modules.clubs.domain.court_hours import local_day
from app.seeds.administrators import write_the_administrators
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.full_hour import REASON, assert_the_full_hour, make_ogrody_33_full
from app.seeds.official_groups import write_the_official_groups
from app.seeds.runner import seed
from tests.api.club_courts_world import EXCEPTIONS
from tests.api.test_seed_club_courts import desk_of, read
from tests.api.test_seed_official_groups import signed_in


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def official_groups(session_factory, now):
    """Everything the layer reads: the named accounts, the clubs selling
    courts, and Ogrody 33's official groups."""

    async with session_factory() as session:
        await seed(session)
    settings = get_settings()
    clubs = await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_club_courts(
        session_factory, settings=settings, now=now, clubs=clubs
    )
    await write_the_administrators(session_factory, settings=settings, now=now)
    return await write_the_official_groups(session_factory, settings=settings, now=now)


async def test_ogrody_33_club_is_offered_other_clubs_only_at_the_hour_it_is_full(
    client, session_factory, now, official_groups
):
    full = await make_ogrody_33_full(
        session_factory, now=now, official_groups=official_groups
    )
    her = await signed_in(client, THE_POPULATED_PLAYER.email)

    read_ = await client.get(
        f"/api/v1/pools/{full.group_id}/posting-grid/slot",
        params={
            "sport": "PADEL",
            "kind": "COMPETITIVE",
            "who": "ANYONE",
            "day": local_day(full.start).isoformat(),
            "range": "MORNING",
        },
        headers=her,
    )

    assert read_.status_code == 200, read_.text
    rows = [
        (
            row["club"]["name"],
            datetime.fromisoformat(row["starts_at"]),
            row["home_club"],
            row["home_club_full"],
        )
        for row in read_.json()["free_courts"]
    ]
    then = [row for row in rows if row[1] == full.start]
    # Saturday at 10:00: other clubs within Ogrody 33's distance, each marked.
    assert then and all(not home and marked for _, _, home, marked in then)
    assert "Bonarka Arena" in {name for name, *_ in then}
    # At its other morning hours Ogrody 33 has a court, and is the only club.
    assert {name for name, start, *_ in rows if start != full.start} == {"Ogrody 33"}
    line = await assert_the_full_hour(
        session_factory, settings=get_settings(), now=now, full=full
    )
    assert "offered then, marked" in line


async def test_a_second_run_closes_nothing_twice(
    client, session_factory, now, official_groups
):
    first = await make_ogrody_33_full(
        session_factory, now=now, official_groups=official_groups
    )

    again = await make_ogrody_33_full(
        session_factory, now=now, official_groups=official_groups
    )

    assert (first.closed_by_this_run, again.closed_by_this_run) == (True, False)
    assert again.start == first.start
    desk = await desk_of(client, "Ogrody 33")
    closed = [
        row
        for row in (await read(client, desk, EXCEPTIONS))["exceptions"]
        if row["reason"] == REASON
    ]
    assert len(closed) == 1

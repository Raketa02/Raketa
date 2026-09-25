"""The seeded clubs, read back the way the club website reads them.

``app/seeds/clubs.py`` signs up about eight Kraków clubs **through the use case a
request runs** (``docs/adr/0182`` §7), so each is asserted by signing in as its
desk on the club surface with the seed password and reading its details back —
never by looking in a table. A club that is only a row would sign in and read
back perfectly; one with no stream behind it would read back nothing, which is
the difference this checks.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from app.core.config import get_settings
from app.kernel import Sport
from app.modules.clubs.domain.folding import fold
from app.seeds.catalog import SEED_EMAIL_DOMAIN, SEED_PASSWORD, Centre
from app.seeds.clubs import SEED_CLUBS, desk_email, write_the_clubs
from tests.api.test_clubs import DETAILS, SIGN_IN, bearer

NOW = datetime(2026, 9, 25, 9, 0, tzinfo=timezone.utc)
KRAKOW = Centre(latitude=50.06, longitude=19.94)


def kilometres_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance, written out here so the test does not borrow the
    arithmetic it is checking."""

    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


async def details_of(client, email: str) -> dict:
    signed_in = await client.post(
        SIGN_IN, json={"email": email, "password": SEED_PASSWORD}
    )
    assert signed_in.status_code == 200, f"{email}: {signed_in.text}"
    read = await client.get(DETAILS, headers=bearer(signed_in.json()))
    assert read.status_code == 200, read.text
    return read.json()


async def test_every_seeded_club_signs_in_on_the_seed_password_and_is_as_declared(
    client, session_factory
):
    await write_the_clubs(
        session_factory, settings=get_settings(), now=NOW, centre=KRAKOW
    )

    for club in SEED_CLUBS:
        details = await details_of(client, desk_email(club))
        assert details["name"] == club.name
        assert details["district"] == club.district
        assert details["city"] == "Kraków"
        assert details["sports"] == [s.value for s in Sport if s in club.sports]


async def test_each_club_sits_where_it_was_declared_relative_to_the_centre(
    client, session_factory
):
    await write_the_clubs(
        session_factory, settings=get_settings(), now=NOW, centre=KRAKOW
    )

    for club in SEED_CLUBS:
        point = (await details_of(client, desk_email(club)))["point"]
        measured = kilometres_between(
            (KRAKOW.latitude, KRAKOW.longitude),
            (point["latitude"], point["longitude"]),
        )
        declared = math.hypot(club.north_km, club.east_km)
        assert measured == pytest.approx(declared, rel=0.01), club.name


async def test_a_second_run_signs_nobody_up_twice(client, session_factory):
    first = await write_the_clubs(
        session_factory, settings=get_settings(), now=NOW, centre=KRAKOW
    )
    before = {
        club.name: await details_of(client, desk_email(club)) for club in SEED_CLUBS
    }

    second = await write_the_clubs(
        session_factory, settings=get_settings(), now=NOW, centre=KRAKOW
    )

    assert [club.signed_up for club in first.clubs] == [True] * len(SEED_CLUBS)
    assert [club.signed_up for club in second.clubs] == [False] * len(SEED_CLUBS)
    for club in SEED_CLUBS:
        assert await details_of(client, desk_email(club)) == before[club.name]


def test_the_clubs_are_about_eight_and_varied():
    districts = {club.district for club in SEED_CLUBS}
    offered = {sport for club in SEED_CLUBS for sport in club.sports}

    assert 7 <= len(SEED_CLUBS) <= 9
    assert len({club.name for club in SEED_CLUBS}) == len(SEED_CLUBS)
    assert len(districts) == len(SEED_CLUBS)
    assert offered == set(Sport)
    assert {len(club.sports) for club in SEED_CLUBS} >= {1, 2, 3}


def test_every_desk_signs_in_on_an_address_no_registry_will_sell():
    emails = [desk_email(club) for club in SEED_CLUBS]

    assert len(set(emails)) == len(emails)
    assert all(email.endswith(f"@{SEED_EMAIL_DOMAIN}") for email in emails)


def test_typing_b_finds_the_four_clubs_504_names_nearest_first():
    """#504's Tomek types ``b`` and gets Centrum Ruchu, Bonarka Arena, Zabłocie
    Sport and Wisła Park, nearest first — the seed's arrangement, asserted by
    the fold search will use, so a club renamed here fails now rather than in
    that ticket's walk."""

    found = sorted(
        (
            club
            for club in SEED_CLUBS
            if "b" in fold(club.name) or "b" in fold(club.district)
        ),
        key=lambda club: math.hypot(club.north_km, club.east_km),
    )

    assert [club.name for club in found] == [
        "Centrum Ruchu",
        "Bonarka Arena",
        "Zabłocie Sport",
        "Wisła Park",
    ]

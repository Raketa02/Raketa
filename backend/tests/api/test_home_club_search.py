"""Home-club search: a player types into *New group*'s home club field and finds
clubs by name or district, nearest first, each with the groups already there.

``docs/adr/0182`` §2 and §6, ``docs/adr/0183`` §9. The match is on the folded
name or district anywhere in the text; the order is the printed distance from
the caller's Location area, then the name; twenty to a page. A caller with no
Location area gets A–Z and no distance, because nothing should pretend to know
where they are.
"""

from __future__ import annotations

import math
import re

import pytest

from app.kernel import Sport
from tests.api import matchmaking_world as world
from tests.api.test_clubs import SIGN_UP, ogrody_33
from tests.api.test_groups import a_group, a_player, a_rated_player, join

SEARCH = "/api/v1/home-clubs"

#: Where the searching player's Location area is — the platform's coarse cell.
HOME = world.CENTRE


def kilometres_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance, written out here so the test does not borrow the
    arithmetic it is checking."""

    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def printed(kilometres: float) -> float:
    """One decimal, never below a tenth — the print the whole app uses."""

    return max(0.1, round(kilometres, 1))


def point_at(north_km: float, east_km: float) -> dict:
    latitude = HOME[0] + north_km / 111.195
    longitude = HOME[1] + east_km / (111.195 * math.cos(math.radians(HOME[0])))
    return {"latitude": round(latitude, 6), "longitude": round(longitude, 6)}


async def a_club_at(
    client,
    name: str,
    district: str,
    *,
    north_km: float = 0.0,
    east_km: float = 0.0,
    sports: tuple[str, ...] = ("PADEL", "TENNIS"),
) -> dict:
    slug = re.sub(r"[^a-z0-9]", "", name.lower())
    signed_up = await client.post(
        SIGN_UP,
        json=ogrody_33(
            name=name,
            district=district,
            sports=list(sports),
            point=point_at(north_km, east_km),
            email=f"desk.{slug}@clubs.example",
        ),
    )
    assert signed_up.status_code == 201, signed_up.text
    return signed_up.json()


async def a_located_player(client, name: str) -> dict:
    player = await a_player(client, name)
    token = player["headers"]["Authorization"].split()[1]
    await world.commit_profile(
        client, token, location={"latitude": HOME[0], "longitude": HOME[1]}
    )
    return player


async def search(client, player: dict, q: str, page: int | None = None) -> dict:
    params: dict = {"q": q}
    if page is not None:
        params["page"] = page
    found = await client.get(SEARCH, params=params, headers=player["headers"])
    assert found.status_code == 200, found.text
    return found.json()


async def krakow(client) -> dict[str, dict]:
    """#504's clubs, placed as the seed places them relative to the player."""

    clubs = [
        ("Ogrody 33", "Grzegórzki", 0.1, 0.6),
        ("Centrum Ruchu", "Dębniki", -0.6, -0.8),
        ("Kazimierz Padel", "Kazimierz", -1.4, 0.3),
        ("Bonarka Arena", "Podgórze Duchackie", -2.3, 0.6),
        ("Zabłocie Sport", "Podgórze", -1.8, 2.5),
        ("Wisła Park", "Błonia", 0.8, -3.9),
    ]
    return {
        name: await a_club_at(client, name, district, north_km=n, east_km=e)
        for name, district, n, e in clubs
    }


def names(page: dict) -> list[str]:
    return [club["name"] for club in page["clubs"]]


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #


async def test_typing_b_finds_the_four_clubs_with_a_b_nearest_first(client):
    tomek = await a_located_player(client, "tomek")
    await krakow(client)

    found = await search(client, tomek, "b")

    assert names(found) == [
        "Centrum Ruchu",
        "Bonarka Arena",
        "Zabłocie Sport",
        "Wisła Park",
    ]
    assert found["next_page"] is None


@pytest.mark.parametrize(
    ("typed", "club"),
    [
        ("debniki", "Centrum Ruchu"),
        ("DĘBNIKI", "Centrum Ruchu"),
        ("blonia", "Wisła Park"),
        ("zablocie", "Zabłocie Sport"),
        ("arena", "Bonarka Arena"),
        ("duchack", "Bonarka Arena"),
        ("33", "Ogrody 33"),
        ("  grzegórzki ", "Ogrody 33"),
    ],
)
async def test_the_name_or_district_is_matched_folded_anywhere(client, typed, club):
    tomek = await a_located_player(client, "tomek")
    await krakow(client)

    assert names(await search(client, tomek, typed)) == [club]


async def test_text_that_matches_nothing_finds_nothing(client):
    tomek = await a_located_player(client, "tomek")
    await krakow(client)

    assert await search(client, tomek, "perr") == {"clubs": [], "next_page": None}


@pytest.mark.parametrize("typed", ["", "   ", "%", "_", "\\"])
async def test_blank_text_or_a_wildcard_finds_nothing(client, typed):
    """A blank field is not a search, and ``%`` is a character, not a pattern."""

    tomek = await a_located_player(client, "tomek")
    await krakow(client)

    assert (await search(client, tomek, typed))["clubs"] == []


async def test_searching_needs_a_player(client):
    assert (await client.get(SEARCH, params={"q": "b"})).status_code == 401


# --------------------------------------------------------------------------- #
# Order and distance
# --------------------------------------------------------------------------- #


async def test_each_club_carries_its_district_distance_and_sports(client):
    tomek = await a_located_player(client, "tomek")
    club = await a_club_at(
        client,
        "Bonarka Arena",
        "Podgórze Duchackie",
        north_km=-2.3,
        east_km=0.6,
        sports=("BADMINTON", "PADEL"),
    )

    [found] = (await search(client, tomek, "bonarka"))["clubs"]

    point = club["point"]
    expected = printed(
        kilometres_between(HOME, (point["latitude"], point["longitude"]))
    )
    assert found == {
        "id": club["id"],
        "name": "Bonarka Arena",
        "district": "Podgórze Duchackie",
        "distance_km": expected,
        "sports": ["PADEL", "BADMINTON"],
        "groups": [],
    }


async def test_clubs_at_one_printed_distance_are_ordered_by_name(client):
    tomek = await a_located_player(client, "tomek")
    await a_club_at(client, "Club Zeta", "Zwierzyniec", north_km=1.0)
    await a_club_at(client, "Club Alfa", "Azory", north_km=1.0)
    await a_club_at(client, "Club Near", "Nowa Wieś", north_km=0.5)

    found = await search(client, tomek, "club")

    assert names(found) == ["Club Near", "Club Alfa", "Club Zeta"]
    assert [club["distance_km"] for club in found["clubs"]] == [0.5, 1.0, 1.0]


async def test_a_club_in_the_player_s_own_cell_prints_a_tenth_not_nought(client):
    tomek = await a_located_player(client, "tomek")
    await a_club_at(client, "Right Here", "Śródmieście")

    [found] = (await search(client, tomek, "here"))["clubs"]

    assert found["distance_km"] == 0.1


async def test_a_player_with_no_location_gets_a_to_z_and_no_distance(client):
    kuba = await a_player(client, "kuba")
    await krakow(client)

    found = await search(client, kuba, "b")

    assert names(found) == [
        "Bonarka Arena",
        "Centrum Ruchu",
        "Wisła Park",
        "Zabłocie Sport",
    ]
    assert [club["distance_km"] for club in found["clubs"]] == [None] * 4


# --------------------------------------------------------------------------- #
# Paging
# --------------------------------------------------------------------------- #


async def test_twenty_clubs_to_a_page(client):
    kuba = await a_player(client, "kuba")
    for number in range(1, 26):
        await a_club_at(client, f"Court {number:02d}", "Dzielnica")

    first = await search(client, kuba, "court")
    second = await search(client, kuba, "court", page=first["next_page"])
    past = await search(client, kuba, "court", page=3)

    assert names(first) == [f"Court {n:02d}" for n in range(1, 21)]
    assert first["next_page"] == 2
    assert names(second) == [f"Court {n:02d}" for n in range(21, 26)]
    assert second["next_page"] is None
    assert past == {"clubs": [], "next_page": None}


async def test_exactly_twenty_is_one_page(client):
    kuba = await a_player(client, "kuba")
    for number in range(1, 21):
        await a_club_at(client, f"Court {number:02d}", "Dzielnica")

    assert (await search(client, kuba, "court"))["next_page"] is None


@pytest.mark.parametrize("page", [0, -1, "two"])
async def test_a_page_is_a_whole_number_from_one(client, page):
    kuba = await a_player(client, "kuba")

    refused = await client.get(
        SEARCH, params={"q": "b", "page": page}, headers=kuba["headers"]
    )

    assert refused.status_code == 422


# --------------------------------------------------------------------------- #
# The groups already at a club
# --------------------------------------------------------------------------- #


async def test_a_club_carries_every_group_at_it_and_the_caller_s_relation(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_rated_player(client, "kuba", Sport.PADEL)
    zofia = await a_rated_player(client, "zofia", Sport.PADEL)
    clubs = await krakow(client)
    bonarka = clubs["Bonarka Arena"]
    kubas = await a_group(client, kuba, bonarka, name="Bonarka weekend")
    await join(client, zofia, kubas)
    tomeks = await a_group(
        client, tomek, bonarka, name="Tomek's own", join_policy="PEOPLE_I_APPROVE"
    )
    await a_group(client, kuba, clubs["Kazimierz Padel"], name="Elsewhere")

    [found] = (await search(client, tomek, "bonarka"))["clubs"]

    # The biggest crowd first, so a player joins it rather than splitting it.
    assert found["groups"] == [
        {
            "id": kubas["id"],
            "name": "Bonarka weekend",
            "monogram": kubas["monogram"],
            "sports": ["PADEL"],
            "member_count": 2,
            "join_policy": "ANYONE",
            "owner_name": "kuba",
            "relation": "NONE",
        },
        {
            "id": tomeks["id"],
            "name": "Tomek's own",
            "monogram": tomeks["monogram"],
            "sports": [],
            "member_count": 1,
            "join_policy": "PEOPLE_I_APPROVE",
            "owner_name": "tomek",
            "relation": "MEMBER",
        },
    ]


async def test_joining_from_the_search_turns_the_row_into_a_member_s(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    group = await a_group(client, kuba, clubs["Bonarka Arena"])

    joined = await join(client, tomek, group)
    [found] = (await search(client, tomek, "bonarka"))["clubs"]

    assert found["groups"] == [joined.json()]
    assert joined.json()["relation"] == "MEMBER"
    assert joined.json()["member_count"] == 2

"""Join search: one field on *Join a group* that finds a group by its club, its
club's district, its own name, or its link (#505, ``docs/adr/0183`` §9).

**The answer is always club cards with groups inside.** A card matched by its
club carries every group at it; a card matched only by a group's name carries
only the groups that matched; a link carries exactly its group. Cards come
nearest first, twenty to a page, or A–Z with no distance for a caller with no
Location area — the order home-club search already keeps.
"""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from tests.api.test_groups import a_group, a_player, join
from tests.api.test_home_club_search import (
    a_club_at,
    a_located_player,
    krakow,
    names,
)

SEARCH = "/api/v1/join-search"


async def search(client, player: dict, q: str, page: int | None = None) -> dict:
    params: dict = {"q": q}
    if page is not None:
        params["page"] = page
    found = await client.get(SEARCH, params=params, headers=player["headers"])
    assert found.status_code == 200, found.text
    return found.json()


def groups_by_club(found: dict) -> dict[str, list[str]]:
    return {
        club["name"]: [group["name"] for group in club["groups"]]
        for club in found["clubs"]
    }


def code_of(group: dict) -> str:
    return group["link"].rsplit("/join/", 1)[1]


# --------------------------------------------------------------------------- #
# By the club's name or district: the card with every group at it
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("typed", ["bonarka", "BONARKA arena", "duchack"])
async def test_a_club_matched_by_name_or_district_carries_all_its_groups(client, typed):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    await a_group(client, kuba, clubs["Bonarka Arena"], name="Weekend padel")
    await a_group(client, kuba, clubs["Bonarka Arena"], name="Tenis rano")
    await a_group(client, kuba, clubs["Centrum Ruchu"], name="Elsewhere")

    found = await search(client, tomek, typed)

    assert found["read_as"] == "TEXT"
    assert sorted(groups_by_club(found)["Bonarka Arena"]) == [
        "Tenis rano",
        "Weekend padel",
    ]
    assert list(groups_by_club(found)) == ["Bonarka Arena"]


async def test_a_matching_club_with_no_groups_is_a_card_with_none(client):
    """*No groups here yet* — the club is in Raketa, and empty."""

    tomek = await a_located_player(client, "tomek")
    await krakow(client)

    found = await search(client, tomek, "kazimierz")

    assert groups_by_club(found) == {"Kazimierz Padel": []}


# --------------------------------------------------------------------------- #
# By a group's name: the group inside its club's card
# --------------------------------------------------------------------------- #


async def test_a_group_matched_by_name_comes_inside_its_club_s_card_alone(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    await a_group(client, kuba, clubs["Ogrody 33"], name="Ogrody open play")
    await a_group(client, kuba, clubs["Ogrody 33"], name="Tenis o świcie")

    found = await search(client, tomek, "open play")

    # The club itself does not match, so only the group that did is shown.
    assert groups_by_club(found) == {"Ogrody 33": ["Ogrody open play"]}
    [card] = found["clubs"]
    assert card["district"] == "Grzegórzki"
    assert card["distance_km"] is not None


async def test_a_group_s_name_is_matched_folded_anywhere(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    await a_group(client, kuba, clubs["Wisła Park"], name="Błonia po pracy")
    await a_group(client, kuba, clubs["Centrum Ruchu"], name="Poranny SQUASH")

    assert groups_by_club(await search(client, tomek, "PO PRAC")) == {
        "Wisła Park": ["Błonia po pracy"]
    }
    assert groups_by_club(await search(client, tomek, "squash")) == {
        "Centrum Ruchu": ["Poranny SQUASH"]
    }


async def test_a_club_that_matches_carries_every_group_even_beside_a_name_match(
    client,
):
    """The typed text finds *Ogrody 33* by name and a group elsewhere by its own
    name: the club's card carries all its groups, the other card only the one
    that matched, and the cards are nearest first."""

    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    await a_group(client, kuba, clubs["Ogrody 33"], name="Tenis o świcie")
    await a_group(client, kuba, clubs["Ogrody 33"], name="Ogrody open play")
    await a_group(client, kuba, clubs["Wisła Park"], name="Ogrody fans")
    await a_group(client, kuba, clubs["Wisła Park"], name="Not this one")

    found = await search(client, tomek, "ogrody")

    assert names(found) == ["Ogrody 33", "Wisła Park"]
    assert sorted(groups_by_club(found)["Ogrody 33"]) == [
        "Ogrody open play",
        "Tenis o świcie",
    ]
    assert groups_by_club(found)["Wisła Park"] == ["Ogrody fans"]


async def test_matching_groups_inside_a_card_come_biggest_crowd_first(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    ola = await a_player(client, "ola")
    clubs = await krakow(client)
    await a_group(client, kuba, clubs["Wisła Park"], name="Padel small")
    big = await a_group(client, kuba, clubs["Wisła Park"], name="Padel big")
    await join(client, ola, big)

    found = await search(client, tomek, "padel ")

    assert groups_by_club(found)["Wisła Park"] == ["Padel big", "Padel small"]


# --------------------------------------------------------------------------- #
# By a link: exactly that group
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "pasted",
    [
        "{link}",
        "Join Ogrody 33 Club on Raketa: {link} — see you there!",
        "raketa.app/join/{code}",
        "https://staging.raketa.example/join/{code}?utm_source=whatsapp",
        "/join/{code}.",
    ],
)
async def test_a_link_finds_exactly_its_group_in_its_club_s_card(client, pasted):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    group = await a_group(client, kuba, clubs["Ogrody 33"], name="Ogrody 33 Club")
    await a_group(client, kuba, clubs["Ogrody 33"], name="Ogrody open play")

    found = await search(
        client, tomek, pasted.format(link=group["link"], code=code_of(group))
    )

    assert found["read_as"] == "LINK"
    assert found["next_page"] is None
    [card] = found["clubs"]
    assert card["name"] == "Ogrody 33"
    assert [row["id"] for row in card["groups"]] == [group["id"]]


async def test_a_link_is_read_whoever_s_domain_printed_it(client):
    """The domain is the setting's business; the code is the group's identity
    (``docs/adr/0183`` §4)."""

    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    group = await a_group(client, kuba, clubs["Bonarka Arena"])
    assert group["link"].startswith(get_settings().PUBLIC_SITE_URL.rstrip("/"))

    found = await search(client, tomek, f"http://elsewhere.test/join/{code_of(group)}")

    assert [row["id"] for row in found["clubs"][0]["groups"]] == [group["id"]]


@pytest.mark.parametrize(
    "dead",
    [
        # The right shape, and nobody's code.
        "https://raketa.app/join/abcdefgh",
        "look: raketa.app/join/zzzz2222 !",
        # Not a code at all: too short, too long, or a look-alike in it.
        "raketa.app/join/abc",
        "raketa.app/join/abcdefghj",
        "raketa.app/join/abcdefg0",
        "raketa.app/join/",
    ],
)
async def test_a_link_that_leads_nowhere_says_so_rather_than_no_match(client, dead):
    tomek = await a_located_player(client, "tomek")
    await krakow(client)

    found = await search(client, tomek, dead)

    assert found == {"clubs": [], "next_page": None, "read_as": "LINK"}


async def test_a_link_s_second_page_is_empty(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, kuba, (await krakow(client))["Ogrody 33"])

    found = await search(client, tomek, group["link"], page=2)

    assert found == {"clubs": [], "next_page": None, "read_as": "LINK"}


# --------------------------------------------------------------------------- #
# Nothing, and blank
# --------------------------------------------------------------------------- #


async def test_text_that_matches_nothing_finds_nothing(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    await a_group(client, kuba, (await krakow(client))["Ogrody 33"])

    found = await search(client, tomek, "co")

    assert found == {"clubs": [], "next_page": None, "read_as": "TEXT"}


@pytest.mark.parametrize("typed", ["", "   ", "%", "_"])
async def test_blank_text_or_a_wildcard_finds_nothing(client, typed):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    await a_group(client, kuba, (await krakow(client))["Ogrody 33"], name="100% fun")

    found = await search(client, tomek, typed)

    if typed == "%":
        # A percent sign is a character: it finds the one group that has one.
        assert groups_by_club(found) == {"Ogrody 33": ["100% fun"]}
    else:
        assert found["clubs"] == []


async def test_join_search_needs_a_player(client):
    assert (await client.get(SEARCH, params={"q": "b"})).status_code == 401


# --------------------------------------------------------------------------- #
# Order, distance and paging
# --------------------------------------------------------------------------- #


async def test_a_caller_with_no_location_gets_a_to_z_and_no_distance(client):
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    await a_group(client, kuba, clubs["Wisła Park"], name="Grupa A")
    await a_group(client, kuba, clubs["Bonarka Arena"], name="Grupa B")
    await a_group(client, kuba, clubs["Ogrody 33"], name="Grupa C")

    found = await search(client, kuba, "grupa")

    assert names(found) == ["Bonarka Arena", "Ogrody 33", "Wisła Park"]
    assert [club["distance_km"] for club in found["clubs"]] == [None] * 3


async def test_cards_come_nearest_first(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    clubs = await krakow(client)
    for club in ("Wisła Park", "Bonarka Arena", "Ogrody 33"):
        await a_group(client, kuba, clubs[club], name=f"Grupa {club}")

    found = await search(client, tomek, "grupa")

    assert names(found) == ["Ogrody 33", "Bonarka Arena", "Wisła Park"]
    distances = [club["distance_km"] for club in found["clubs"]]
    assert distances == sorted(distances)


async def test_twenty_cards_to_a_page(client):
    kuba = await a_player(client, "kuba")
    for number in range(1, 26):
        club = await a_club_at(client, f"Court {number:02d}", "Dzielnica")
        await a_group(client, kuba, club, name=f"Crew {number:02d}")

    first = await search(client, kuba, "crew")
    second = await search(client, kuba, "crew", page=first["next_page"])
    past = await search(client, kuba, "crew", page=3)

    assert names(first) == [f"Court {n:02d}" for n in range(1, 21)]
    assert first["next_page"] == 2
    assert names(second) == [f"Court {n:02d}" for n in range(21, 26)]
    assert second["next_page"] is None
    assert past == {"clubs": [], "next_page": None, "read_as": "TEXT"}


@pytest.mark.parametrize("page", [0, -1, "two"])
async def test_a_page_is_a_whole_number_from_one(client, page):
    kuba = await a_player(client, "kuba")

    refused = await client.get(
        SEARCH, params={"q": "b", "page": page}, headers=kuba["headers"]
    )

    assert refused.status_code == 422


# --------------------------------------------------------------------------- #
# The rows
# --------------------------------------------------------------------------- #


async def test_each_row_says_what_the_group_is_to_the_caller(client):
    tomek = await a_located_player(client, "tomek")
    karol = await a_player(client, "karol")
    wisla = (await krakow(client))["Wisła Park"]
    mine = await a_group(client, tomek, wisla, name="Grupa moja")
    asked = await a_group(
        client, karol, wisla, name="Grupa pytana", join_policy="PEOPLE_I_APPROVE"
    )
    await a_group(
        client, karol, wisla, name="Grupa obca", join_policy="PEOPLE_I_APPROVE"
    )
    anyone = await a_group(client, karol, wisla, name="Grupa otwarta")
    await join(client, tomek, asked)

    [card] = (await search(client, tomek, "wisła"))["clubs"]

    relations = {row["name"]: row["relation"] for row in card["groups"]}
    assert relations == {
        "Grupa moja": "MEMBER",
        "Grupa pytana": "REQUESTED",
        "Grupa obca": "NONE",
        "Grupa otwarta": "NONE",
    }
    rows = {row["id"]: row for row in card["groups"]}
    assert rows[mine["id"]]["join_policy"] == "ANYONE"
    assert rows[anyone["id"]]["join_policy"] == "ANYONE"
    assert rows[asked["id"]]["join_policy"] == "PEOPLE_I_APPROVE"


async def test_each_row_carries_its_monogram_count_and_the_owner_s_name(client):
    tomek = await a_located_player(client, "tomek")
    karol = await a_player(client, "karol")
    group = await a_group(
        client,
        karol,
        (await krakow(client))["Ogrody 33"],
        name="Ogrody 33 Club",
        join_policy="PEOPLE_I_APPROVE",
    )

    [card] = (await search(client, tomek, group["link"]))["clubs"]

    assert card["groups"] == [
        {
            "id": group["id"],
            "kind": "PLAYER",
            "name": "Ogrody 33 Club",
            "monogram": group["monogram"],
            "sports": [],
            "member_count": 1,
            "join_policy": "PEOPLE_I_APPROVE",
            "owner_name": "karol",
            "administrator_name": None,
            "is_administrator": False,
            "relation": "NONE",
        }
    ]


async def test_asking_from_the_search_turns_the_row_into_a_waiting_one(client):
    tomek = await a_located_player(client, "tomek")
    karol = await a_player(client, "karol")
    group = await a_group(
        client,
        karol,
        (await krakow(client))["Ogrody 33"],
        join_policy="PEOPLE_I_APPROVE",
    )

    asked = await join(client, tomek, group)
    [card] = (await search(client, tomek, group["link"]))["clubs"]

    # The join's answer is the search's row, so the card is patched in place.
    assert card["groups"] == [asked.json()]
    assert asked.json()["relation"] == "REQUESTED"


async def test_a_club_s_card_draws_its_header(client):
    tomek = await a_located_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    club = await a_club_at(
        client, "Hala MOSiR", "Nowa Huta", north_km=0.1, sports=("SQUASH", "BADMINTON")
    )
    await a_group(client, kuba, club, name="Squash crew")

    [card] = (await search(client, tomek, "squash crew"))["clubs"]

    assert {key: card[key] for key in ("id", "name", "district", "sports")} == {
        "id": club["id"],
        "name": "Hala MOSiR",
        "district": "Nowa Huta",
        "sports": ["SQUASH", "BADMINTON"],
    }
    assert card["distance_km"] == 0.1


async def test_a_declined_request_quietly_turns_back_into_none(client):
    """Nothing tells them it was declined — the row is *Ask to join* again
    (#500 story 43)."""

    tomek = await a_located_player(client, "tomek")
    karol = await a_player(client, "karol")
    group = await a_group(
        client,
        karol,
        (await krakow(client))["Ogrody 33"],
        join_policy="PEOPLE_I_APPROVE",
    )
    await join(client, tomek, group)
    declined = await client.post(
        f"/api/v1/groups/{group['id']}/requests/{tomek['id']}/decline",
        headers=karol["headers"],
    )
    assert declined.status_code == 204, declined.text

    [card] = (await search(client, tomek, group["link"]))["clubs"]

    assert [row["relation"] for row in card["groups"]] == ["NONE"]

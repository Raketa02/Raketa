"""Kasia taps a group link without the app, and the public page reads the group.

The page shows what a WhatsApp preview and a stranger need to decide to install:
the group's name, its tile, its club and district, its sport dots and how many
are in it — and **never who** (``docs/adr/0187`` §4–§5). Nobody signs in: every
request here carries no session at all.
"""

from __future__ import annotations

import pytest

from app.kernel import Sport
from tests.api.administration_world import (
    club_signs_up,
    invites,
    marta_sets_her_password,
    me,
)
from tests.api.test_group_leaving_and_editing import delete
from tests.api.test_groups import a_club, a_group, a_player, a_rated_player, join
from tests.api.test_official_groups import an_official_group

GROUP_PAGE = "/api/v1/public/groups"


def code_of(group: dict) -> str:
    return group["link"].rsplit("/join/", 1)[1]


async def the_page(client, code: str):
    return await client.get(f"{GROUP_PAGE}/{code}")


async def test_a_link_opens_the_group_s_name_tile_club_dots_and_size(client):
    tomek = await a_rated_player(client, "tomek", Sport.PADEL, Sport.TENNIS)
    kuba = await a_rated_player(client, "kuba", Sport.PADEL)
    zofia = await a_rated_player(client, "zofia", Sport.SQUASH)
    bonarka = await a_club(client, district="Podgórze")
    group = await a_group(client, tomek, bonarka, name="Ogrody wieczorem")
    await join(client, kuba, group)
    await join(client, zofia, group)

    page = await the_page(client, code_of(group))

    assert page.status_code == 200, page.text
    assert page.json() == {
        "name": "Ogrody wieczorem",
        "monogram": group["monogram"],
        "club": {"name": "Bonarka Arena", "district": "Podgórze"},
        # The dots rule: two members rated in padel is a dot; one in tennis and
        # one in squash is not.
        "sports": ["PADEL"],
        "member_count": 3,
    }


async def test_an_official_group_shows_the_sports_it_declares(
    client, ogrody_with_marta
):
    club_id, marta = ogrody_with_marta
    group = await an_official_group(
        client, marta, club_id, name="Ogrody 33 Club", sports=["TENNIS", "PADEL"]
    )

    page = await the_page(client, code_of(group))

    assert page.status_code == 200, page.text
    body = page.json()
    assert body["name"] == "Ogrody 33 Club"
    assert body["club"] == {"name": "Ogrody 33", "district": "Grzegórzki"}
    # Declared, in the registry's order, though nobody in it is rated in either.
    assert body["sports"] == ["PADEL", "TENNIS"]
    assert body["member_count"] == 0


async def test_the_page_never_says_who_is_in_the_group(client):
    tomek = await a_rated_player(client, "tomek", Sport.PADEL)
    kuba = await a_rated_player(client, "kuba", Sport.PADEL)
    group = await a_group(client, tomek, await a_club(client))
    await join(client, kuba, group)

    page = await the_page(client, code_of(group))

    assert set(page.json()) == {"name", "monogram", "club", "sports", "member_count"}
    assert set(page.json()["club"]) == {"name", "district"}
    for member in (tomek, kuba):
        assert str(member["id"]) not in page.text
    # Their names, as they named themselves (``world.register``).
    assert "tomek" not in page.text.lower()
    assert "kuba" not in page.text.lower()


async def test_the_page_never_says_who_runs_an_official_group_or_is_in_it(
    client, ogrody_with_marta
):
    club_id, marta = ogrody_with_marta
    group = await an_official_group(
        client, marta, club_id, name="Ogrody open play", join_policy="ANYONE"
    )
    kuba = await a_rated_player(client, "kuba", Sport.PADEL)
    assert (await join(client, kuba, group)).status_code == 200

    page = await the_page(client, code_of(group))

    assert page.json()["member_count"] == 1
    assert set(page.json()) == {"name", "monogram", "club", "sports", "member_count"}
    for person in (marta, kuba):
        assert str(person["id"]) not in page.text
    assert "Marta" not in page.text
    assert "Wójcik" not in page.text
    assert "kuba" not in page.text.lower()


async def test_the_link_still_opens_the_group_after_a_rename(client):
    tomek = await a_player(client, "tomek")
    group = await a_group(client, tomek, await a_club(client))
    renamed = await client.put(
        f"/api/v1/groups/{group['id']}/details",
        json={"name": "Padel po pracy", "join_policy": "ANYONE"},
        headers=tomek["headers"],
    )
    assert renamed.status_code == 200, renamed.text

    page = await the_page(client, code_of(group))

    assert page.json()["name"] == "Padel po pracy"


async def test_a_link_shouted_in_capitals_is_the_same_link(client):
    tomek = await a_player(client, "tomek")
    group = await a_group(client, tomek, await a_club(client))

    page = await the_page(client, code_of(group).upper())

    assert page.status_code == 200, page.text
    assert page.json()["name"] == group["name"]


@pytest.mark.parametrize(
    "code",
    [
        "zzzzzzzz",  # a code no group has
        "abc",  # too short to be anybody's
        "abcdefghj",  # too long
        "o0o0o0o0",  # look-alikes no code is minted from
    ],
)
async def test_a_link_that_leads_nowhere_is_not_found(client, code):
    missing = await the_page(client, code)

    assert missing.status_code == 404, missing.text
    assert missing.json()["code"] == "group_not_found"


async def test_a_deleted_group_s_link_is_not_found(client):
    tomek = await a_player(client, "tomek")
    group = await a_group(client, tomek, await a_club(client))
    assert (await delete(client, tomek, group)).status_code == 204

    missing = await the_page(client, code_of(group))

    assert missing.status_code == 404, missing.text
    assert missing.json()["code"] == "group_not_found"


@pytest.fixture
async def ogrody_with_marta(client, mailbox):
    """Ogrody 33 — padel and tennis — and Marta, who runs its official groups."""

    club_id, desk = await club_signs_up(client, sports=("PADEL", "TENNIS"))
    await invites(client, desk, name="Marta Wójcik", email="marta@ogrody33.pl")
    headers = await marta_sets_her_password(client, mailbox)
    return club_id, {"id": (await me(client, headers))["id"], "headers": headers}

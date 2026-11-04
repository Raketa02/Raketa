"""Official groups, run from the app — over HTTP, as the administrator profile
and the player app call it (#509, ``docs/adr/0183`` §3, ``docs/adr/0184`` §8).

Marta creates *Ogrody 33 Club* for her 48-person padel WhatsApp group. Its home
club is Ogrody 33, fixed, and joining needs her approval. Players see a padel
dot on it from the first minute and read *Administrator Marta Wójcik approves
joins*. Michał asks to join and Marta approves him from her group page, where
every player is listed newest first with the day they joined. Later she changes
the WhatsApp size to 52. Tomek, who runs another official group and plays, taps
Join on it from his player profile and is in at once. The desk tries to untick
padel and is refused, because *Ogrody 33 Club* plays it.

Every assertion reads what a person reads: an answer on the administrator's
paths, the player surface, or the club website's.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest

from app.core.config import get_settings
from app.kernel import Sport
from tests.api import players_world as players
from tests.api.administration_world import (
    ADMINISTRATORS,
    MARTA,
    accept_path,
    club_signs_up,
    invites,
    marta_sets_her_password,
    me,
)
from tests.api.test_group_members import a_padel_player, block, listed
from tests.api.test_groups import GROUPS, a_club, a_group, join, read
from tests.api.test_join_search import search

#: The group code's alphabet, spelled out rather than imported (``docs/adr/0183`` §4).
CODE = r"[abcdefghjkmnpqrstuvwxyz23456789]{8}"
DETAILS = "/api/v1/club/details"


def groups_at(club_id: str) -> str:
    return f"/api/v1/administrator/clubs/{club_id}/groups"


def group_at(club_id: str, group_id: str) -> str:
    return f"{groups_at(club_id)}/{group_id}"


def ogrody_33_club(**overrides) -> dict:
    return {
        "name": "Ogrody 33 Club",
        "join_policy": "PEOPLE_I_APPROVE",
        "whatsapp_size": 48,
        "sports": ["PADEL"],
        **overrides,
    }


@pytest.fixture
async def ogrody(client):
    """Ogrody 33 — padel and tennis — and its desk's session."""

    club_id, desk = await club_signs_up(client, sports=("PADEL", "TENNIS"))
    return {"id": club_id, "desk": desk}


@pytest.fixture
async def marta(client, ogrody, mailbox):
    """Marta, new to Raketa, whom the desk made an administrator; she set her
    password by the invitation's link and is signed in."""

    row = await invites(client, ogrody["desk"], name="Marta Wójcik", email=MARTA)
    headers = await marta_sets_her_password(client, mailbox)
    return {
        "id": (await me(client, headers))["id"],
        "headers": headers,
        "administrator_id": row["id"],
    }


async def an_administrator_who_plays(client, ogrody, name: str) -> dict:
    """A rated player the desk made an administrator, who accepted in the app."""

    player = await a_padel_player(client, name)
    row = await invites(
        client, ogrody["desk"], name=name.title(), email=f"{name}@example.com"
    )
    accepted = await client.post(accept_path(row["id"]), headers=player["headers"])
    assert accepted.status_code == 200, accepted.text
    return {**player, "administrator_id": row["id"]}


async def create(client, administrator: dict, club_id: str, **overrides):
    return await client.post(
        groups_at(club_id),
        json=ogrody_33_club(**overrides),
        headers=administrator["headers"],
    )


async def an_official_group(client, administrator: dict, club_id: str, **overrides):
    created = await create(client, administrator, club_id, **overrides)
    assert created.status_code == 201, created.text
    return created.json()


async def page_of(client, administrator: dict, club_id: str, group: dict) -> dict:
    read_ = await client.get(
        group_at(club_id, group["id"]), headers=administrator["headers"]
    )
    assert read_.status_code == 200, read_.text
    return read_.json()


async def answer(client, administrator, club_id, group, asker, verb: str):
    return await client.post(
        f"{group_at(club_id, group['id'])}/requests/{asker['id']}/{verb}",
        headers=administrator["headers"],
    )


async def save(client, administrator, club_id, group, **settings):
    return await client.put(
        f"{group_at(club_id, group['id'])}/settings",
        json=ogrody_33_club(**settings),
        headers=administrator["headers"],
    )


def row_in(found: dict, group: dict) -> dict:
    return next(
        row
        for card in found["clubs"]
        for row in card["groups"]
        if row["id"] == group["id"]
    )


# --------------------------------------------------------------------------- #
# Creating one
# --------------------------------------------------------------------------- #


async def test_marta_creates_a_group_with_no_owner_and_nobody_in_it(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])

    site = re.escape(get_settings().PUBLIC_SITE_URL.rstrip("/"))
    assert re.fullmatch(rf"{site}/join/{CODE}", group["link"]), group["link"]
    assert group["kind"] == "OFFICIAL"
    assert group["name"] == "Ogrody 33 Club"
    assert group["monogram"]["letters"] == "O3"
    assert group["join_policy"] == "PEOPLE_I_APPROVE"
    assert group["whatsapp_size"] == 48
    # Its dots are what it declares, from the first minute.
    assert group["sports"] == ["PADEL"]
    # Running an official group is not membership.
    assert group["member_count"] == 0
    assert group["players"] == []
    assert group["requests"] == []
    assert group["home_club"] == {
        "id": ogrody["id"],
        "name": "Ogrody 33",
        "sports": ["PADEL", "TENNIS"],
    }
    # And the read answers what the creation did.
    assert await page_of(client, marta, ogrody["id"], group) == group


async def test_the_sports_are_ticked_in_any_order_and_answered_in_the_registry_s(
    client, ogrody, marta
):
    group = await an_official_group(
        client, marta, ogrody["id"], sports=["TENNIS", "PADEL", "TENNIS"]
    )

    assert group["sports"] == ["PADEL", "TENNIS"]


@pytest.mark.parametrize(
    ("overrides", "code", "details"),
    [
        ({"name": "   "}, "group_name_invalid", {"field": "name"}),
        ({"name": "x" * 41}, "group_name_invalid", {"field": "name"}),
        ({"whatsapp_size": 1}, "whatsapp_size_invalid", {"field": "whatsapp_size"}),
        ({"whatsapp_size": 1025}, "whatsapp_size_invalid", {"field": "whatsapp_size"}),
        ({"sports": []}, "group_sports_required", {"field": "sports"}),
        (
            {"sports": ["PADEL", "SQUASH"]},
            "sport_not_offered_by_club",
            {"field": "sports", "sport": "SQUASH"},
        ),
        # In the form's order: the name is read before the size.
        ({"name": "", "whatsapp_size": 0}, "group_name_invalid", {"field": "name"}),
    ],
    ids=[
        "blank-name",
        "long-name",
        "size-one",
        "size-1025",
        "no-sports",
        "sport-not-the-club-s",
        "name-first",
    ],
)
async def test_each_field_is_refused_under_its_name_and_nothing_is_created(
    client, ogrody, marta, overrides, code, details
):
    refused = await create(client, marta, ogrody["id"], **overrides)

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == code
    assert refused.json()["details"] == details
    listed_ = await client.get(groups_at(ogrody["id"]), headers=marta["headers"])
    assert listed_.json()["groups"] == []


@pytest.mark.parametrize("size", [2, 1024])
async def test_the_whatsapp_size_runs_from_two_to_1024(client, ogrody, marta, size):
    group = await an_official_group(client, marta, ogrody["id"], whatsapp_size=size)

    assert group["whatsapp_size"] == size


async def test_a_whatsapp_size_is_required(client, ogrody, marta):
    body = ogrody_33_club()
    del body["whatsapp_size"]

    refused = await client.post(
        groups_at(ogrody["id"]), json=body, headers=marta["headers"]
    )

    assert refused.status_code == 422


# --------------------------------------------------------------------------- #
# The guard
# --------------------------------------------------------------------------- #


async def test_a_player_who_runs_nothing_is_refused_every_administrator_operation(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_padel_player(client, "kasia")
    path = group_at(ogrody["id"], group["id"])

    answers = [
        await client.post(
            groups_at(ogrody["id"]), json=ogrody_33_club(), headers=kasia["headers"]
        ),
        await client.get(groups_at(ogrody["id"]), headers=kasia["headers"]),
        await client.get(path, headers=kasia["headers"]),
        await client.put(
            f"{path}/settings", json=ogrody_33_club(), headers=kasia["headers"]
        ),
        await client.post(
            f"{path}/requests/{kasia['id']}/approve", headers=kasia["headers"]
        ),
        await client.post(
            f"{path}/requests/{kasia['id']}/decline", headers=kasia["headers"]
        ),
    ]

    assert [answer_.status_code for answer_ in answers] == [403] * 6
    assert {answer_.json()["code"] for answer_ in answers} == {"not_an_administrator"}


async def test_a_removed_administrator_is_refused_on_the_next_request(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])

    removed = await client.delete(
        f"{ADMINISTRATORS}/{marta['administrator_id']}", headers=ogrody["desk"]
    )
    refused = await client.get(
        group_at(ogrody["id"], group["id"]), headers=marta["headers"]
    )

    assert removed.status_code == 204, removed.text
    assert refused.status_code == 403
    assert refused.json()["code"] == "not_an_administrator"


async def test_an_administrator_is_refused_at_a_club_they_do_not_run(
    client, ogrody, marta
):
    other = await a_club(client, "Bonarka Arena")

    refused = await create(client, marta, other["id"])

    assert refused.status_code == 403
    assert refused.json()["code"] == "not_an_administrator"


async def test_a_colleague_s_group_and_a_player_group_are_not_found(
    client, ogrody, marta
):
    marta_s = await an_official_group(client, marta, ogrody["id"])
    ola = await an_administrator_who_plays(client, ogrody, "ola")
    karol = await a_padel_player(client, "karol")
    player_group = await a_group(
        client, karol, {"id": ogrody["id"]}, name="Ogrody wieczorem"
    )

    for group in (marta_s, player_group):
        path = group_at(ogrody["id"], group["id"])
        answers = [
            await client.get(path, headers=ola["headers"]),
            await client.put(
                f"{path}/settings", json=ogrody_33_club(), headers=ola["headers"]
            ),
            await client.post(
                f"{path}/requests/{karol['id']}/approve", headers=ola["headers"]
            ),
            await client.post(
                f"{path}/requests/{karol['id']}/decline", headers=ola["headers"]
            ),
        ]
        assert [answer_.status_code for answer_ in answers] == [404] * 4
        assert {answer_.json()["code"] for answer_ in answers} == {"group_not_found"}


# --------------------------------------------------------------------------- #
# The list
# --------------------------------------------------------------------------- #


async def test_the_list_holds_only_the_groups_this_administrator_runs_newest_first(
    client, ogrody, marta, clock
):
    first = await an_official_group(client, marta, ogrody["id"])
    clock.move(timedelta(minutes=1))
    second = await an_official_group(
        client,
        marta,
        ogrody["id"],
        name="Ogrody open play",
        join_policy="ANYONE",
        whatsapp_size=30,
        sports=["TENNIS", "PADEL"],
    )
    ola = await an_administrator_who_plays(client, ogrody, "ola")
    await an_official_group(client, ola, ogrody["id"], name="Ola's tennis")
    michal = await a_padel_player(client, "michal")
    await join(client, michal, first)

    listed_ = await client.get(groups_at(ogrody["id"]), headers=marta["headers"])

    assert listed_.status_code == 200, listed_.text
    body = listed_.json()
    assert body["club"] == {
        "id": ogrody["id"],
        "name": "Ogrody 33",
        "sports": ["PADEL", "TENNIS"],
    }
    assert body["groups"] == [
        {
            "id": second["id"],
            "kind": "OFFICIAL",
            "name": "Ogrody open play",
            "monogram": second["monogram"],
            "sports": ["PADEL", "TENNIS"],
            "member_count": 0,
            "waiting_count": 0,
            "home_club": {"id": ogrody["id"], "name": "Ogrody 33"},
        },
        {
            "id": first["id"],
            "kind": "OFFICIAL",
            "name": "Ogrody 33 Club",
            "monogram": first["monogram"],
            "sports": ["PADEL"],
            "member_count": 0,
            "waiting_count": 1,
            "home_club": {"id": ogrody["id"], "name": "Ogrody 33"},
        },
    ]


# --------------------------------------------------------------------------- #
# The page, and answering its requests
# --------------------------------------------------------------------------- #


async def test_marta_approves_michal_and_he_heads_the_players_newest_first(
    client, ogrody, marta, clock
):
    group = await an_official_group(client, marta, ogrody["id"])
    ewa = await a_padel_player(client, "ewa")
    michal = await a_padel_player(client, "michal", Sport.TENNIS)
    kasia = await a_padel_player(client, "kasia")
    await join(client, ewa, group)
    await answer(client, marta, ogrody["id"], group, ewa, "approve")
    clock.move(timedelta(minutes=1))
    await join(client, michal, group)
    await join(client, kasia, group)

    before = await page_of(client, marta, ogrody["id"], group)
    approved = await answer(client, marta, ogrody["id"], group, michal, "approve")
    after = await page_of(client, marta, ogrody["id"], group)

    # Waiting, in the order they asked — each with every sport and its Level.
    assert [row["nickname"] for row in before["requests"]] == ["michal", "kasia"]
    michal_s = before["requests"][0]["levels"]
    assert [level["sport"] for level in michal_s] == ["PADEL", "TENNIS"]
    assert michal_s[0]["level"] == michal["level"]
    assert approved.status_code == 204, approved.text
    assert after["member_count"] == 2
    assert [row["nickname"] for row in after["players"]] == ["michal", "ewa"]
    assert after["players"][0]["joined_at"] > after["players"][1]["joined_at"]
    assert [row["nickname"] for row in after["requests"]] == ["kasia"]
    # And from his side he is in.
    assert (await read(client, michal, group)).status_code == 200


async def test_a_block_hides_nobody_from_the_players_list(client, ogrody):
    """Kuba blocked Tomek as a player long ago, and Tomek, running the group,
    still reads him: a block keeps two people off one court and hides nobody in
    a group's people (``docs/adr/0193`` §2, superseding ADR-0183 §10)."""

    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"], join_policy="ANYONE")
    ewa = await a_padel_player(client, "ewa")
    kuba = await a_padel_player(client, "kuba")
    await join(client, ewa, group)
    await join(client, kuba, group)
    await block(client, kuba, tomek)

    page = await page_of(client, tomek, ogrody["id"], group)

    assert [row["nickname"] for row in page["players"]] == ["kuba", "ewa"]
    assert page["member_count"] == 2


async def test_marta_declines_silently_and_the_person_may_ask_again(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_padel_player(client, "kasia")
    await join(client, kasia, group)

    declined = await answer(client, marta, ogrody["id"], group, kasia, "decline")
    again = await answer(client, marta, ogrody["id"], group, kasia, "decline")
    asked_again = await join(client, kasia, group)

    assert declined.status_code == again.status_code == 204
    assert asked_again.json()["relation"] == "REQUESTED"


async def test_approving_somebody_with_nothing_waiting_is_refused(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_padel_player(client, "kasia")

    refused = await answer(client, marta, ogrody["id"], group, kasia, "approve")

    assert refused.status_code == 404
    assert refused.json()["code"] == "join_request_not_found"


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #


async def test_marta_changes_the_whatsapp_size_and_the_link_does_not_move(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])

    saved = await save(client, marta, ogrody["id"], group, whatsapp_size=52)

    assert saved.status_code == 200, saved.text
    assert saved.json()["admitted"] == []
    assert saved.json()["group"]["whatsapp_size"] == 52
    assert saved.json()["group"]["link"] == group["link"]
    assert (await page_of(client, marta, ogrody["id"], group))["whatsapp_size"] == 52


async def test_all_four_settings_save_together_and_anyone_admits_everybody_waiting(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    michal = await a_padel_player(client, "michal")
    kasia = await a_padel_player(client, "kasia")
    await join(client, michal, group)
    await join(client, kasia, group)

    saved = await save(
        client,
        marta,
        ogrody["id"],
        group,
        name="Ogrody nights",
        join_policy="ANYONE",
        whatsapp_size=52,
        sports=["TENNIS", "PADEL"],
    )

    body = saved.json()
    assert saved.status_code == 200, saved.text
    assert [person["nickname"] for person in body["admitted"]] == ["michal", "kasia"]
    assert body["group"]["name"] == "Ogrody nights"
    assert body["group"]["join_policy"] == "ANYONE"
    assert body["group"]["sports"] == ["PADEL", "TENNIS"]
    assert body["group"]["member_count"] == 2
    assert body["group"]["requests"] == []
    assert body["group"]["link"] == group["link"]
    assert body["group"]["monogram"]["colour"] == group["monogram"]["colour"]


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"name": ""}, "group_name_invalid"),
        ({"whatsapp_size": 1025}, "whatsapp_size_invalid"),
        ({"sports": []}, "group_sports_required"),
        ({"sports": ["BADMINTON"]}, "sport_not_offered_by_club"),
    ],
)
async def test_a_refused_setting_records_none_of_the_four(
    client, ogrody, marta, overrides, code
):
    group = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_padel_player(client, "kasia")
    await join(client, kasia, group)

    refused = await save(
        client,
        marta,
        ogrody["id"],
        group,
        **{"name": "Ogrody nights", "join_policy": "ANYONE", **overrides},
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == code
    after = await page_of(client, marta, ogrody["id"], group)
    assert after["name"] == "Ogrody 33 Club"
    assert after["join_policy"] == "PEOPLE_I_APPROVE"
    assert [row["nickname"] for row in after["requests"]] == ["kasia"]


# --------------------------------------------------------------------------- #
# No way out for its administrator
# --------------------------------------------------------------------------- #


async def test_no_administrator_operation_deletes_or_leaves_an_official_group(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    path = group_at(ogrody["id"], group["id"])

    deleted = await client.delete(path, headers=marta["headers"])
    left = await client.delete(f"{path}/membership", headers=marta["headers"])

    assert deleted.status_code == 405
    assert left.status_code in (404, 405)
    assert (await page_of(client, marta, ogrody["id"], group))["id"] == group["id"]


async def test_nobody_deletes_an_official_group_from_the_player_surface(client, ogrody):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"], join_policy="ANYONE")
    await join(client, tomek, group)

    refused = await client.delete(f"{GROUPS}/{group['id']}", headers=tomek["headers"])

    assert refused.status_code == 403
    assert refused.json()["code"] == "not_the_group_owner"


async def test_the_administrator_who_joined_as_a_player_leaves_as_one_and_still_runs_it(
    client, ogrody
):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"])
    await join(client, tomek, group)

    left = await client.delete(
        f"{GROUPS}/{group['id']}/membership", headers=tomek["headers"]
    )

    assert left.status_code == 204, left.text
    page = await page_of(client, tomek, ogrody["id"], group)
    assert page["member_count"] == 0


# --------------------------------------------------------------------------- #
# An administrator who plays
# --------------------------------------------------------------------------- #


async def test_an_administrator_who_plays_joins_their_group_directly(client, ogrody):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"])

    found = row_in(await search(client, tomek, "ogrody"), group)
    joined = await join(client, tomek, group)

    # *Join*, not *Ask to join*, even under People I approve.
    assert found["relation"] == "NONE"
    assert found["is_administrator"] is True
    assert joined.status_code == 200, joined.text
    assert joined.json()["relation"] == "MEMBER"
    assert joined.json()["is_administrator"] is True
    assert joined.json()["member_count"] == 1
    page = await page_of(client, tomek, ogrody["id"], group)
    assert [row["nickname"] for row in page["players"]] == ["tomek"]
    assert page["requests"] == []


async def test_an_administrator_of_another_group_asks_like_anybody(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")

    found = row_in(await search(client, tomek, "ogrody"), group)
    asked = await join(client, tomek, group)

    assert found["is_administrator"] is False
    assert asked.json()["relation"] == "REQUESTED"


async def test_a_removed_administrator_asks_like_anybody(client, ogrody):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"])
    await client.delete(
        f"{ADMINISTRATORS}/{tomek['administrator_id']}", headers=ogrody["desk"]
    )

    asked = await join(client, tomek, group)

    assert asked.json()["relation"] == "REQUESTED"
    assert asked.json()["is_administrator"] is False


# --------------------------------------------------------------------------- #
# What players see
# --------------------------------------------------------------------------- #


async def test_a_player_sees_the_declared_dots_and_administrator_marta_on_the_line(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    player_id, token = await players.register(client, "kasia")
    await players.rate(client, token, Sport.TENNIS)
    kasia = {"id": player_id, "headers": players.auth(token)}

    found = row_in(await search(client, kasia, "ogrody"), group)

    assert found == {
        "id": group["id"],
        "kind": "OFFICIAL",
        "name": "Ogrody 33 Club",
        "monogram": group["monogram"],
        # Declared, from the first minute — nobody here is rated in padel.
        "sports": ["PADEL"],
        "member_count": 0,
        "join_policy": "PEOPLE_I_APPROVE",
        "owner_nickname": None,
        "administrator_nickname": "Marta Wójcik",
        "is_administrator": False,
        "relation": "NONE",
    }


async def test_the_approver_line_says_the_account_s_own_name_where_it_has_one(
    client, ogrody
):
    """The club typed *Tomek*; the name he gave himself is *tomek*, and it is
    the one his admin-tagged Members row draws — so the line says it too."""

    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"])
    kasia = await a_padel_player(client, "kasia")

    found = row_in(await search(client, kasia, "ogrody"), group)

    assert found["administrator_nickname"] == "tomek"


async def test_a_member_s_page_reports_the_declared_sports_and_no_owner(
    client, ogrody, marta
):
    group = await an_official_group(
        client, marta, ogrody["id"], join_policy="ANYONE", sports=["TENNIS", "PADEL"]
    )
    kasia = await a_padel_player(client, "kasia")
    await join(client, kasia, group)

    page = (await read(client, kasia, group)).json()
    mine = (await client.get(GROUPS, headers=kasia["headers"])).json()["groups"]

    assert page["kind"] == "OFFICIAL"
    assert page["declared_sports"] == ["PADEL", "TENNIS"]
    assert page["sports"] == ["PADEL", "TENNIS"]
    assert page["is_owner"] is False
    assert page["member_count"] == 1
    # The Info tab's line names who runs it, as the search row does.
    assert page["administrator_nickname"] == "Marta Wójcik"
    assert page["is_administrator"] is False
    assert [(row["kind"], row["sports"]) for row in mine] == [
        ("OFFICIAL", ["PADEL", "TENNIS"])
    ]


async def test_the_administrator_who_joined_reads_that_they_run_it(client, ogrody):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"])
    await join(client, tomek, group)

    page = (await read(client, tomek, group)).json()

    # *You approve joins*, and his account's own Name.
    assert page["is_administrator"] is True
    assert page["administrator_nickname"] == "tomek"


async def test_a_player_group_s_page_declares_nothing(client):
    karol = await a_padel_player(client, "karol")
    group = await a_group(client, karol, await a_club(client))

    page = (await read(client, karol, group)).json()

    assert page["kind"] == "PLAYER"
    assert "declared_sports" not in page
    assert page["administrator_nickname"] is None
    assert page["is_administrator"] is False


async def test_members_carry_the_administrator_who_plays_with_the_admin_tag(
    client, ogrody, clock
):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"], join_policy="ANYONE")
    ewa = await a_padel_player(client, "ewa")
    kuba = await a_padel_player(client, "kuba")
    await join(client, ewa, group)
    clock.move(timedelta(minutes=1))
    await join(client, tomek, group)
    clock.move(timedelta(minutes=1))
    await join(client, kuba, group)

    rows = await listed(client, ewa, group)
    page = (await read(client, ewa, group)).json()
    his_page = (await read(client, tomek, group)).json()

    # The reader, then the administrator who plays, then newest first.
    assert [row["nickname"] for row in rows] == ["ewa", "tomek", "kuba"]
    assert [row["is_administrator"] for row in rows] == [False, True, False]
    assert {row["is_owner"] for row in rows} == {False}
    # Every count includes him.
    assert page["member_count"] == 3
    assert [face["nickname"] for face in page["member_faces"]] == ["tomek", "kuba"]
    # Running it is not owning it: he edits it from the administrator profile.
    assert his_page["is_owner"] is False


async def test_a_member_cannot_answer_or_edit_an_official_group_as_a_player(
    client, ogrody
):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"])
    await join(client, tomek, group)

    requests_ = await client.get(
        f"{GROUPS}/{group['id']}/requests", headers=tomek["headers"]
    )
    edited = await client.put(
        f"{GROUPS}/{group['id']}/details",
        json={"name": "Renamed", "join_policy": "ANYONE"},
        headers=tomek["headers"],
    )

    # His group is answered and edited from the administrator profile.
    assert requests_.status_code == edited.status_code == 403
    assert requests_.json()["code"] == edited.json()["code"] == "not_the_group_owner"


# --------------------------------------------------------------------------- #
# The club's details
# --------------------------------------------------------------------------- #


def ogrody_details(*sports: str) -> dict:
    return {
        "name": "Ogrody 33",
        "district": "Grzegórzki",
        "city": "Kraków",
        "sports": list(sports),
        "point": {"latitude": 50.06, "longitude": 19.95},
    }


async def test_the_desk_cannot_untick_a_sport_an_official_group_declares(
    client, ogrody, marta
):
    await an_official_group(client, marta, ogrody["id"])

    refused = await client.put(
        DETAILS, json=ogrody_details("TENNIS"), headers=ogrody["desk"]
    )
    allowed = await client.put(
        DETAILS, json=ogrody_details("PADEL"), headers=ogrody["desk"]
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "club_sport_declared_by_group"
    assert refused.json()["details"] == {
        "field": "sports",
        "sport": "PADEL",
        "group": "Ogrody 33 Club",
    }
    assert "Ogrody 33 Club" in refused.json()["message"]
    # Tennis is the club's to drop: no official group declares it.
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["sports"] == ["PADEL"]


async def test_a_player_group_at_the_club_holds_no_sport(client, ogrody):
    karol = await a_padel_player(client, "karol")
    await a_group(client, karol, {"id": ogrody["id"]})

    changed = await client.put(
        DETAILS, json=ogrody_details("TENNIS"), headers=ogrody["desk"]
    )

    assert changed.status_code == 200, changed.text

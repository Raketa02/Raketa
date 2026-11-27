"""The club watches its official groups and hands them between administrators —
over HTTP, as the club website and the player app call it (#510,
``docs/adr/0183`` §8, §11, ``docs/adr/0184`` §7).

Ogrody 33's desk sees two groups, both run by Marta: *Ogrody 33 Club*, eleven
players of a 48-person WhatsApp group and one more waiting, and *Ogrody open
play*, eight of 30 — and no games, because no group gives birth to one yet. The
desk removes Marta, and both groups *need an administrator*: players read
*Ogrody 33 approves joins* and the request waits. The desk hands *Ogrody 33
Club* to Tomek, and the waiting request is his to answer; the link, the rule
and the size never moved. And the desk answers who asked itself — while nobody
runs a group, and beside whoever does (``docs/adr/0191`` §1).

Every assertion reads what a person reads: an answer on the club surface, on
the administrator's paths or on the player surface.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from app.kernel import Sport
from tests.api.administration_world import (
    ADMINISTRATORS,
    MARTA,
    accept_path,
    club_signs_up,
    invites,
    listed,
    marta_sets_her_password,
    me,
)
from tests.api.test_groups import (
    a_club,
    a_group,
    a_player,
    a_rated_player,
    join,
    my_groups,
    read,
)
from tests.api.test_join_search import search
from tests.api.test_official_groups import (
    an_administrator_who_plays,
    an_official_group,
    answer,
    group_at,
    groups_at,
    page_of,
    row_in,
    save,
)

CLUB_GROUPS = "/api/v1/club/groups"

#: Eleven players and the one who asks after them — enough to fill the story.
PLAYERS = (
    "ania",
    "bartek",
    "celina",
    "darek",
    "ewa",
    "filip",
    "gosia",
    "henryk",
    "iga",
    "jacek",
    "kuba",
)


@pytest.fixture
async def ogrody(client):
    """Ogrody 33 — padel and tennis — and its desk's session."""

    club_id, desk = await club_signs_up(client, sports=("PADEL", "TENNIS"))
    return {"id": club_id, "desk": desk}


@pytest.fixture
async def marta(client, ogrody, mailbox):
    """Marta, new to Rakieta, whom the desk made an administrator; she set her
    password by the invitation's link and is signed in."""

    row = await invites(client, ogrody["desk"], name="Marta Wójcik", email=MARTA)
    headers = await marta_sets_her_password(client, mailbox)
    return {
        "id": (await me(client, headers))["id"],
        "headers": headers,
        "administrator_id": row["id"],
    }


async def the_club_s_groups(client, ogrody) -> list[dict]:
    read = await client.get(CLUB_GROUPS, headers=ogrody["desk"])
    assert read.status_code == 200, read.text
    return read.json()["groups"]


async def hands_over(client, desk: dict, group: dict, administrator_id: str):
    return await client.put(
        f"{CLUB_GROUPS}/{group['id']}/administrator",
        json={"administrator_id": administrator_id},
        headers=desk,
    )


async def removes(client, ogrody, administrator: dict) -> None:
    removed = await client.delete(
        f"{ADMINISTRATORS}/{administrator['administrator_id']}", headers=ogrody["desk"]
    )
    assert removed.status_code == 204, removed.text


async def the_groups_they_run(client, administrator: dict, club_id: str) -> list:
    read_ = await client.get(groups_at(club_id), headers=administrator["headers"])
    assert read_.status_code == 200, read_.text
    return [group["id"] for group in read_.json()["groups"]]


async def players_join(client, group: dict, names) -> list[dict]:
    players = [await a_player(client, name) for name in names]
    for player in players:
        joined = await join(client, player, group)
        assert joined.status_code == 200, joined.text
    return players


# --------------------------------------------------------------------------- #
# The club's list
# --------------------------------------------------------------------------- #


async def test_the_desk_sees_each_group_with_who_runs_it_and_its_crowd(
    client, ogrody, marta
):
    club = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    open_play = await an_official_group(
        client,
        marta,
        ogrody["id"],
        name="Ogrody open play",
        join_policy="ANYONE",
        whatsapp_size=30,
    )
    players = await players_join(client, club, PLAYERS)
    for player in players[:8]:
        await join(client, player, open_play)
    # Then Marta asks for approval, and one more asks.
    await save(client, marta, ogrody["id"], club)
    await players_join(client, club, ["kasia"])

    groups = await the_club_s_groups(client, ogrody)

    assert groups == [
        {
            "id": club["id"],
            "name": "Ogrody 33 Club",
            "monogram": club["monogram"],
            "administrator": {"id": marta["administrator_id"], "name": "Marta Wójcik"},
            "member_count": 11,
            "waiting_count": 1,
            "whatsapp_size": 48,
            "whatsapp_percent": 23,
            "games": 0,
        },
        {
            "id": open_play["id"],
            "name": "Ogrody open play",
            "monogram": open_play["monogram"],
            "administrator": {"id": marta["administrator_id"], "name": "Marta Wójcik"},
            "member_count": 8,
            "waiting_count": 0,
            "whatsapp_size": 30,
            "whatsapp_percent": 27,
            "games": 0,
        },
    ]


async def test_more_players_than_the_whatsapp_group_has_is_the_real_figure(
    client, ogrody, marta
):
    group = await an_official_group(
        client, marta, ogrody["id"], join_policy="ANYONE", whatsapp_size=2
    )
    await players_join(client, group, ["ania", "bartek", "celina"])

    (row,) = await the_club_s_groups(client, ogrody)

    assert (row["member_count"], row["whatsapp_size"]) == (3, 2)
    assert row["whatsapp_percent"] == 150


async def test_a_half_percent_is_rounded_up_and_an_empty_group_is_nought(
    client, ogrody, marta
):
    one_of_eight = await an_official_group(
        client, marta, ogrody["id"], join_policy="ANYONE", whatsapp_size=8
    )
    await an_official_group(client, marta, ogrody["id"], name="Ogrody nights")
    await players_join(client, one_of_eight, ["ania"])

    rows = await the_club_s_groups(client, ogrody)

    assert [(row["name"], row["whatsapp_percent"]) for row in rows] == [
        ("Ogrody 33 Club", 13),
        ("Ogrody nights", 0),
    ]


async def test_an_administrator_who_joined_as_a_player_is_one_of_the_players(
    client, ogrody
):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"])
    await join(client, tomek, group)

    (row,) = await the_club_s_groups(client, ogrody)

    assert row["member_count"] == 1
    assert row["waiting_count"] == 0


async def test_only_this_club_s_official_groups_are_listed(client, ogrody, marta):
    mine = await an_official_group(client, marta, ogrody["id"])
    karol = await a_player(client, "karol")
    await a_group(client, karol, {"id": ogrody["id"]}, name="Ogrody wieczorem")
    bonarka_id, bonarka_desk = await club_signs_up(
        client, name="Bonarka Arena", email="desk@bonarka.pl"
    )
    ola = await invites(client, bonarka_desk, name="Ola", email="ola@example.com")
    assert ola["status"] == "INVITED"

    rows = await the_club_s_groups(client, ogrody)
    theirs = await the_club_s_groups(client, {"desk": bonarka_desk})

    assert [row["id"] for row in rows] == [mine["id"]]
    assert theirs == []
    assert bonarka_id != ogrody["id"]


async def test_a_club_with_no_official_groups_has_an_empty_list(client, ogrody):
    await a_group(client, await a_player(client, "karol"), await a_club(client))

    assert await the_club_s_groups(client, ogrody) == []


async def test_a_player_token_is_refused_on_the_club_s_groups(client, ogrody):
    karol = await a_player(client, "karol")

    refused = await client.get(CLUB_GROUPS, headers=karol["headers"])

    assert refused.status_code == 401


# --------------------------------------------------------------------------- #
# Orphans: the club removes whoever ran them
# --------------------------------------------------------------------------- #


async def test_removing_marta_leaves_both_her_groups_needing_an_administrator(
    client, ogrody, marta
):
    club = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    await an_official_group(
        client, marta, ogrody["id"], name="Ogrody open play", join_policy="ANYONE"
    )
    (ewa,) = await players_join(client, club, ["ewa"])
    await save(client, marta, ogrody["id"], club)
    kasia = await a_player(client, "kasia")
    await join(client, kasia, club)

    await removes(client, ogrody, marta)

    rows = await the_club_s_groups(client, ogrody)
    assert [(row["name"], row["administrator"]) for row in rows] == [
        ("Ogrody 33 Club", None),
        ("Ogrody open play", None),
    ]
    # Players read "Ogrody 33 approves joins", and the request waits on it.
    seen = row_in(await search(client, kasia, "ogrody"), club)
    assert seen["administrator_nickname"] is None
    assert seen["relation"] == "REQUESTED"
    assert rows[0]["waiting_count"] == 1
    # A member's Info tab reads it too.
    page = (await read(client, ewa, club)).json()
    assert (page["administrator_nickname"], page["is_administrator"]) == (None, False)


# --------------------------------------------------------------------------- #
# The handover
# --------------------------------------------------------------------------- #


async def test_the_desk_hands_an_orphan_to_tomek_and_the_waiting_request_is_his(
    client, ogrody, marta
):
    club = await an_official_group(client, marta, ogrody["id"])
    before = await page_of(client, marta, ogrody["id"], club)
    kasia = await a_player(client, "kasia")
    await join(client, kasia, club)
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    await removes(client, ogrody, marta)

    handed = await hands_over(client, ogrody["desk"], club, tomek["administrator_id"])

    assert handed.status_code == 200, handed.text
    assert handed.json()["administrator"] == {
        "id": tomek["administrator_id"],
        "name": "Tomek",
    }
    assert handed.json()["waiting_count"] == 1
    assert await the_groups_they_run(client, tomek, ogrody["id"]) == [club["id"]]
    his_page = await page_of(client, tomek, ogrody["id"], club)
    assert [request["player_id"] for request in his_page["requests"]] == [
        str(kasia["id"])
    ]
    # The link, the rule and the size never moved.
    assert his_page["link"] == before["link"]
    assert his_page["join_policy"] == before["join_policy"] == "PEOPLE_I_APPROVE"
    assert his_page["whatsapp_size"] == before["whatsapp_size"] == 48
    # Players read his name on the line now, on the card and on the page.
    seen = row_in(await search(client, kasia, "ogrody"), club)
    assert seen["administrator_nickname"] == "tomek"

    approved = await answer(client, tomek, ogrody["id"], club, kasia, "approve")

    assert approved.status_code == 204, approved.text
    (row,) = await the_club_s_groups(client, ogrody)
    assert (row["member_count"], row["waiting_count"]) == (1, 0)
    assert (await read(client, kasia, club)).json()["administrator_nickname"] == "tomek"


async def test_the_old_administrator_stops_seeing_it_and_stays_in_it_as_a_player(
    client, ogrody
):
    ola = await an_administrator_who_plays(client, ogrody, "ola")
    group = await an_official_group(client, ola, ogrody["id"], join_policy="ANYONE")
    await join(client, ola, group)
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")

    handed = await hands_over(client, ogrody["desk"], group, tomek["administrator_id"])

    assert handed.status_code == 200, handed.text
    assert await the_groups_they_run(client, ola, ogrody["id"]) == []
    gone = await client.get(group_at(ogrody["id"], group["id"]), headers=ola["headers"])
    assert gone.status_code == 404
    assert gone.json()["code"] == "group_not_found"
    assert await the_groups_they_run(client, tomek, ogrody["id"]) == [group["id"]]
    # Running it was never membership, and her membership was never running it.
    assert [mine["id"] for mine in await my_groups(client, ola)] == [group["id"]]
    assert (await read(client, ola, group)).status_code == 200
    assert handed.json()["member_count"] == 1


async def test_a_group_is_handed_between_two_active_administrators_and_back(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")

    there = await hands_over(client, ogrody["desk"], group, tomek["administrator_id"])
    back = await hands_over(client, ogrody["desk"], group, marta["administrator_id"])

    assert there.json()["administrator"]["id"] == tomek["administrator_id"]
    assert back.json()["administrator"] == {
        "id": marta["administrator_id"],
        "name": "Marta Wójcik",
    }
    assert await the_groups_they_run(client, marta, ogrody["id"]) == [group["id"]]
    assert await the_groups_they_run(client, tomek, ogrody["id"]) == []


async def test_handing_a_group_to_whoever_runs_it_changes_nothing(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"])
    (before,) = await the_club_s_groups(client, ogrody)

    handed = await hands_over(client, ogrody["desk"], group, marta["administrator_id"])

    assert handed.status_code == 200, handed.text
    assert handed.json() == before


async def test_only_an_active_administrator_of_this_club_is_handed_a_group(
    client, ogrody, marta, clock
):
    group = await an_official_group(client, marta, ogrody["id"])
    invited = await invites(client, ogrody["desk"], name="Ewa", email="ewa@example.com")
    expired = await invites(
        client, ogrody["desk"], name="Filip", email="filip@example.com"
    )
    ola = await an_administrator_who_plays(client, ogrody, "ola")
    await removes(client, ogrody, ola)
    _, bonarka_desk = await club_signs_up(
        client, name="Bonarka Arena", email="desk@bonarka.pl"
    )
    kuba = await a_player(client, "kuba")
    elsewhere = await invites(
        client, bonarka_desk, name="Kuba", email="kuba@example.com"
    )
    accepted = await client.post(accept_path(elsewhere["id"]), headers=kuba["headers"])
    assert accepted.status_code == 200, accepted.text
    clock.move(timedelta(hours=73))
    # Ewa's invitation went out again this minute; Filip's has lapsed.
    resent = await client.post(
        f"{ADMINISTRATORS}/{invited['id']}/invitation", headers=ogrody["desk"]
    )
    assert resent.json()["status"] == "INVITED"

    refused = [
        await hands_over(client, ogrody["desk"], group, administrator_id)
        for administrator_id in (
            invited["id"],
            expired["id"],
            ola["administrator_id"],
            elsewhere["id"],
            str(uuid4()),
        )
    ]

    assert [answer_.status_code for answer_ in refused] == [409] * 5
    assert {answer_.json()["code"] for answer_ in refused} == {
        "administrator_not_active"
    }
    (row,) = await the_club_s_groups(client, ogrody)
    assert row["administrator"]["id"] == marta["administrator_id"]


async def test_only_this_club_s_official_group_is_handed_over(client, ogrody, marta):
    karol = await a_player(client, "karol")
    player_group = await a_group(
        client, karol, {"id": ogrody["id"]}, name="Ogrody wieczorem"
    )
    _, bonarka_desk = await club_signs_up(
        client, name="Bonarka Arena", email="desk@bonarka.pl"
    )
    theirs = await an_official_group(client, marta, ogrody["id"])

    refused = [
        await hands_over(client, bonarka_desk, theirs, marta["administrator_id"]),
        await hands_over(
            client, ogrody["desk"], player_group, marta["administrator_id"]
        ),
        await hands_over(
            client, ogrody["desk"], {"id": str(uuid4())}, marta["administrator_id"]
        ),
    ]

    assert [answer_.status_code for answer_ in refused] == [404] * 3
    assert {answer_.json()["code"] for answer_ in refused} == {"group_not_found"}


async def test_a_player_token_is_refused_the_handover(client, ogrody, marta):
    group = await an_official_group(client, marta, ogrody["id"])
    karol = await a_player(client, "karol")

    refused = await hands_over(
        client, karol["headers"], group, marta["administrator_id"]
    )

    assert refused.status_code == 401


async def test_marta_invited_back_runs_again_what_nobody_was_handed(
    client, ogrody, marta, mailbox
):
    """A call made while building #510: a group records who it was given to,
    and whether they run it is read — so the club inviting back somebody it
    removed gives them back **the groups it never handed on**, and nothing
    it did."""

    kept = await an_official_group(client, marta, ogrody["id"])
    moved = await an_official_group(client, marta, ogrody["id"], name="Ogrody nights")
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    await removes(client, ogrody, marta)
    await hands_over(client, ogrody["desk"], moved, tomek["administrator_id"])

    await invites(client, ogrody["desk"], name="Marta Wójcik", email=MARTA)
    back = await client.post(
        accept_path(marta["administrator_id"]), headers=marta["headers"]
    )

    assert back.status_code == 200, back.text
    assert await the_groups_they_run(client, marta, ogrody["id"]) == [kept["id"]]
    rows = await the_club_s_groups(client, ogrody)
    assert [(row["name"], row["administrator"]["name"]) for row in rows] == [
        ("Ogrody 33 Club", "Marta Wójcik"),
        ("Ogrody nights", "Tomek"),
    ]


async def test_a_reset_leaves_marta_s_groups_waiting_until_her_new_password(
    client, ogrody, marta, mailbox
):
    """Who runs a group is read off whether the administratorship is active,
    and the club's *Reset password* puts her back to *invited*: nobody can
    answer as Marta until she has set a new password, and the table says so."""

    group = await an_official_group(client, marta, ogrody["id"])
    reset = await client.post(
        f"{ADMINISTRATORS}/{marta['administrator_id']}/password-reset",
        headers=ogrody["desk"],
    )
    assert reset.status_code == 200, reset.text

    (waiting,) = await the_club_s_groups(client, ogrody)
    (row,) = await listed(client, ogrody["desk"])
    marta["headers"] = await marta_sets_her_password(client, mailbox, "ogrody-marta-2")
    (running,) = await the_club_s_groups(client, ogrody)

    assert waiting["administrator"] is None
    assert row["groups"] == []
    assert running["administrator"]["id"] == marta["administrator_id"]
    assert await the_groups_they_run(client, marta, ogrody["id"]) == [group["id"]]


# --------------------------------------------------------------------------- #
# The Administrators table's groups column
# --------------------------------------------------------------------------- #


def groups_of(rows: list[dict], email: str) -> list[str]:
    (row,) = [row for row in rows if row["email"] == email]
    return [group["name"] for group in row["groups"]]


async def test_each_administrator_s_row_names_the_groups_they_run(
    client, ogrody, marta
):
    open_play = await an_official_group(
        client, marta, ogrody["id"], name="Ogrody open play"
    )
    club = await an_official_group(client, marta, ogrody["id"])
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")

    before = await listed(client, ogrody["desk"])
    await hands_over(client, ogrody["desk"], open_play, tomek["administrator_id"])
    after = await listed(client, ogrody["desk"])

    assert groups_of(before, MARTA) == ["Ogrody 33 Club", "Ogrody open play"]
    assert groups_of(before, "tomek@example.com") == []
    assert groups_of(after, MARTA) == ["Ogrody 33 Club"]
    assert groups_of(after, "tomek@example.com") == ["Ogrody open play"]
    (marta_s,) = [row for row in after if row["email"] == MARTA]
    assert marta_s["groups"] == [{"id": club["id"], "name": "Ogrody 33 Club"}]


# --------------------------------------------------------------------------- #
# Whom it was handed to is told, once (docs/adr/0192)
# --------------------------------------------------------------------------- #


def handovers_seen(club_id: str) -> str:
    return f"/api/v1/administrator/clubs/{club_id}/handovers/seen"


async def untold(client, session: dict) -> list[dict]:
    return (await me(client, session["headers"]))["profiles"]["handovers"]


async def says_told(client, administrator: dict, club_id: str, *groups: dict):
    return await client.post(
        handovers_seen(club_id),
        json={"group_ids": [group["id"] for group in groups]},
        headers=administrator["headers"],
    )


async def test_tomek_is_told_the_desk_handed_him_a_group_and_then_he_knows(
    client, ogrody, marta
):
    club = await an_official_group(client, marta, ogrody["id"])
    await join(client, await a_player(client, "kasia"), club)
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    assert await untold(client, tomek) == []

    await hands_over(client, ogrody["desk"], club, tomek["administrator_id"])

    assert await untold(client, tomek) == [
        {
            "club_id": ogrody["id"],
            "club_name": "Ogrody 33",
            "group_id": club["id"],
            "group_name": "Ogrody 33 Club",
            "waiting_count": 1,
        }
    ]
    # Marta created it, and was handed nothing.
    assert await untold(client, marta) == []

    seen = await says_told(client, tomek, ogrody["id"], club)

    assert seen.status_code == 204, seen.text
    assert await untold(client, tomek) == []
    again = await says_told(client, tomek, ogrody["id"], club)
    assert again.status_code == 204, again.text


async def test_handovers_are_listed_oldest_first(client, ogrody, marta, clock):
    club = await an_official_group(client, marta, ogrody["id"])
    open_play = await an_official_group(
        client, marta, ogrody["id"], name="Ogrody open play"
    )
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")

    await hands_over(client, ogrody["desk"], open_play, tomek["administrator_id"])
    clock.move(timedelta(minutes=1))
    await hands_over(client, ogrody["desk"], club, tomek["administrator_id"])

    assert [row["group_name"] for row in await untold(client, tomek)] == [
        "Ogrody open play",
        "Ogrody 33 Club",
    ]


async def test_handed_on_before_he_was_told_it_is_the_next_one_s_to_know(
    client, ogrody, marta
):
    club = await an_official_group(client, marta, ogrody["id"])
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    ola = await an_administrator_who_plays(client, ogrody, "ola")
    await hands_over(client, ogrody["desk"], club, tomek["administrator_id"])

    await hands_over(client, ogrody["desk"], club, ola["administrator_id"])
    late = await says_told(client, tomek, ogrody["id"], club)

    assert await untold(client, tomek) == []
    # Tomek's word is about a group he no longer runs: it changes nothing.
    assert late.status_code == 204, late.text
    assert [row["group_id"] for row in await untold(client, ola)] == [club["id"]]


async def test_handed_back_to_marta_she_is_told_too(client, ogrody, marta):
    club = await an_official_group(client, marta, ogrody["id"])
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")

    await hands_over(client, ogrody["desk"], club, tomek["administrator_id"])
    await hands_over(client, ogrody["desk"], club, marta["administrator_id"])

    assert [row["group_id"] for row in await untold(client, marta)] == [club["id"]]


async def test_saying_so_about_another_s_group_changes_nothing(client, ogrody, marta):
    club = await an_official_group(client, marta, ogrody["id"])
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    ola = await an_administrator_who_plays(client, ogrody, "ola")
    await hands_over(client, ogrody["desk"], club, ola["administrator_id"])

    noted = await says_told(client, tomek, ogrody["id"], club, {"id": str(uuid4())})

    assert noted.status_code == 204, noted.text
    assert [row["group_id"] for row in await untold(client, ola)] == [club["id"]]


async def test_a_removed_administrator_is_told_nothing_and_says_nothing(
    client, ogrody, marta
):
    club = await an_official_group(client, marta, ogrody["id"])
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    await hands_over(client, ogrody["desk"], club, tomek["administrator_id"])

    await removes(client, ogrody, tomek)
    refused = await says_told(client, tomek, ogrody["id"], club)

    assert await untold(client, tomek) == []
    assert refused.status_code == 403
    assert refused.json()["code"] == "not_an_administrator"


async def test_saying_so_names_at_least_one_group(client, ogrody, marta):
    refused = await client.post(
        handovers_seen(ogrody["id"]), json={"group_ids": []}, headers=marta["headers"]
    )

    assert refused.status_code == 422


# --------------------------------------------------------------------------- #
# The club answers who asked (docs/adr/0191 §1)
# --------------------------------------------------------------------------- #


def requests_of(group: dict) -> str:
    return f"{CLUB_GROUPS}/{group['id']}/requests"


async def the_club_s_queue(client, ogrody, group: dict) -> list[dict]:
    read_ = await client.get(requests_of(group), headers=ogrody["desk"])
    assert read_.status_code == 200, read_.text
    return read_.json()["requests"]


async def the_club_answers(client, desk: dict, group: dict, asker: dict, verb: str):
    return await client.post(f"{requests_of(group)}/{asker['id']}/{verb}", headers=desk)


async def test_with_nobody_running_it_the_desk_lets_kasia_in(client, ogrody, marta):
    club = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_rated_player(client, "kasia", Sport.TENNIS, Sport.PADEL)
    await join(client, kasia, club)
    await removes(client, ogrody, marta)

    [request] = await the_club_s_queue(client, ogrody, club)

    # A nickname and her Levels: what deciding needs, and no photograph.
    assert set(request) == {"player_id", "nickname", "levels"}
    assert (request["player_id"], request["nickname"]) == (str(kasia["id"]), "kasia")
    assert [row["sport"] for row in request["levels"]] == ["PADEL", "TENNIS"]

    approved = await the_club_answers(client, ogrody["desk"], club, kasia, "approve")

    assert approved.status_code == 204, approved.text
    (row,) = await the_club_s_groups(client, ogrody)
    assert (row["member_count"], row["waiting_count"]) == (1, 0)
    # Answering is not running it: it still needs an administrator.
    assert row["administrator"] is None
    assert (await read(client, kasia, club)).status_code == 200
    assert await the_club_s_queue(client, ogrody, club) == []


async def test_the_desk_answers_beside_marta_and_her_queue_is_the_same_one(
    client, ogrody, marta
):
    club = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_player(client, "kasia")
    michal = await a_player(client, "michal")
    await join(client, kasia, club)
    await join(client, michal, club)

    queue = await the_club_s_queue(client, ogrody, club)
    declined = await the_club_answers(client, ogrody["desk"], club, kasia, "decline")

    # In the order they asked.
    assert [request["nickname"] for request in queue] == ["kasia", "michal"]
    assert declined.status_code == 204, declined.text
    page = await page_of(client, marta, ogrody["id"], club)
    assert [request["player_id"] for request in page["requests"]] == [str(michal["id"])]
    (row,) = await the_club_s_groups(client, ogrody)
    assert row["administrator"]["id"] == marta["administrator_id"]
    # Silently: Kasia reads it as never asked, and may ask again.
    assert row_in(await search(client, kasia, "ogrody"), club)["relation"] == "NONE"
    assert (await join(client, kasia, club)).json()["relation"] == "REQUESTED"


async def test_an_answer_marta_gave_first_stands(client, ogrody, marta):
    club = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_player(client, "kasia")
    michal = await a_player(client, "michal")
    await join(client, kasia, club)
    await answer(client, marta, ogrody["id"], club, kasia, "approve")

    late_yes = await the_club_answers(client, ogrody["desk"], club, kasia, "approve")
    late_no = await the_club_answers(client, ogrody["desk"], club, kasia, "decline")
    never_asked = await the_club_answers(
        client, ogrody["desk"], club, michal, "approve"
    )

    # She is in, and stays in: a decline never removes a member.
    assert (late_yes.status_code, late_no.status_code) == (204, 204)
    assert never_asked.status_code == 404
    assert never_asked.json()["code"] == "join_request_not_found"
    (row,) = await the_club_s_groups(client, ogrody)
    assert (row["member_count"], row["waiting_count"]) == (1, 0)


async def test_only_this_club_s_official_groups_are_its_to_answer(
    client, ogrody, marta
):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    player_group = await a_group(
        client,
        karol,
        {"id": ogrody["id"]},
        name="Ogrody wieczorem",
        join_policy="PEOPLE_I_APPROVE",
    )
    theirs = await an_official_group(client, marta, ogrody["id"])
    await join(client, kasia, player_group)
    await join(client, kasia, theirs)
    _, bonarka_desk = await club_signs_up(
        client, name="Bonarka Arena", email="desk@bonarka.pl"
    )

    refused = [
        await client.get(requests_of(theirs), headers=bonarka_desk),
        await the_club_answers(client, bonarka_desk, theirs, kasia, "approve"),
        await the_club_answers(client, bonarka_desk, theirs, kasia, "decline"),
        await client.get(requests_of(player_group), headers=ogrody["desk"]),
        await the_club_answers(client, ogrody["desk"], player_group, kasia, "approve"),
        await the_club_answers(client, ogrody["desk"], player_group, kasia, "decline"),
        await client.get(requests_of({"id": str(uuid4())}), headers=ogrody["desk"]),
    ]

    assert [answer_.status_code for answer_ in refused] == [404] * 7
    assert {answer_.json()["code"] for answer_ in refused} == {"group_not_found"}
    (row,) = await the_club_s_groups(client, ogrody)
    assert row["waiting_count"] == 1


async def test_a_player_token_is_refused_the_club_s_queue(client, ogrody, marta):
    group = await an_official_group(client, marta, ogrody["id"])
    kasia = await a_player(client, "kasia")
    await join(client, kasia, group)

    read_ = await client.get(requests_of(group), headers=kasia["headers"])
    approved = await the_club_answers(client, kasia["headers"], group, kasia, "approve")

    assert (read_.status_code, approved.status_code) == (401, 401)

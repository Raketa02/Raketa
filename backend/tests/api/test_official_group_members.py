"""Members of an official group, read by whoever runs it — over HTTP, as the
player app's administrator area calls it (#566, ``docs/adr/0183`` §10, and
``docs/adr/0159``'s amendment of 2026-10-02).

Marta runs *Ogrody 33 Club* and has never played: running a group is not
membership (``docs/adr/0183`` §7). She opens its players card, and Members lists
who in it plays padel, newest first, as anybody in it would read them — and not
her, because she is not in it. Kuba blocked her long ago, so she never sees his
row. She taps Ewa and reads her record, though Marta has no profile and so no
gender a preference could be read against. When the desk hands the group to
Tomek, Members and every record it opened are his to read and no longer hers.

Every assertion reads what a person reads: an answer on the player surface, the
administrator's paths or the club website's.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from tests.api import matchmaking_world as world
from tests.api import players_world as players
from tests.api.administration_world import (
    MARTA,
    accept_path,
    club_signs_up,
    invites,
    marta_sets_her_password,
    me,
)
from tests.api.test_club_groups import hands_over, removes
from tests.api.test_group_members import (
    a_padel_player,
    block,
    listed,
    members,
    names,
)
from tests.api.test_groups import a_group, a_player, join
from tests.api.test_official_groups import (
    an_administrator_who_plays,
    an_official_group,
    answer,
)


@pytest.fixture
async def ogrody(client):
    """Ogrody 33 — padel and tennis — and its desk's session."""

    club_id, desk = await club_signs_up(client, sports=("PADEL", "TENNIS"))
    return {"id": club_id, "desk": desk}


@pytest.fixture
async def marta(client, ogrody, mailbox):
    """Marta, new to Raketa, whom the desk made an administrator; she set her
    password by the invitation's link and is signed in — and has no profile."""

    row = await invites(client, ogrody["desk"], name="Marta Wójcik", email=MARTA)
    headers = await marta_sets_her_password(client, mailbox)
    return {
        "id": (await me(client, headers))["id"],
        "headers": headers,
        "administrator_id": row["id"],
    }


def refusal(answer) -> tuple[int, dict]:
    """A refusal as a reader can compare two of them: everything but the trace
    id, which is the request's and never the refusal's."""

    body = dict(answer.json())
    body.pop("trace_id", None)
    return answer.status_code, body


async def a_stranger_s_refusal(client, reader: dict) -> tuple[int, dict]:
    """What this reader is answered about a group that does not exist."""

    return refusal(await members(client, reader, {"id": str(uuid4())}))


async def a_member(client, session_factory, name: str, **facts) -> dict:
    """Somebody with a profile, a padel rating and an index row's worth of facts
    on the log — the subject a record can describe."""

    player_id, token = await players.a_player_on_the_log(
        client, session_factory, name, mu=3.0, **facts
    )
    return {"id": player_id, "token": token, "headers": players.auth(token)}


async def made_an_administrator(client, desk: dict, player: dict, name: str) -> dict:
    """A player the desk made an administrator, who accepted in the app."""

    row = await invites(client, desk, name=name, email=f"{name.lower()}@example.com")
    accepted = await client.post(accept_path(row["id"]), headers=player["headers"])
    assert accepted.status_code == 200, accepted.text
    return {**player, "administrator_id": row["id"]}


async def record(client, reader: dict, subject_id):
    return await client.get(
        f"/api/v1/players/{subject_id}/record", headers=reader["headers"]
    )


# --------------------------------------------------------------------------- #
# Members, for whoever runs it
# --------------------------------------------------------------------------- #


async def test_marta_reads_who_plays_in_the_group_she_runs(client, ogrody, marta):
    group = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    ewa = await a_padel_player(client, "ewa")
    fred = await a_player(client, "fred")
    kuba = await a_padel_player(client, "kuba")
    for player in (ewa, fred, kuba):
        joined = await join(client, player, group)
        assert joined.status_code == 200, joined.text

    rows = await listed(client, marta, group)

    # Newest first and nobody leading: she is not in it, so she is no row, and
    # whoever runs it leads only from inside it. Fred plays no padel.
    assert names(rows) == ["kuba", "ewa"]
    assert {(row["is_owner"], row["is_administrator"]) for row in rows} == {
        (False, False)
    }
    # The rows are the rows a member reads, in the same order after the reader.
    assert names(await listed(client, ewa, group)) == ["ewa", "kuba"]


async def test_somebody_waiting_is_a_row_once_she_lets_them_in(client, ogrody, marta):
    group = await an_official_group(client, marta, ogrody["id"])
    michal = await a_padel_player(client, "michal")
    asked = await join(client, michal, group)
    assert asked.json()["relation"] == "REQUESTED"

    assert await listed(client, marta, group) == []

    approved = await answer(client, marta, ogrody["id"], group, michal, "approve")

    assert approved.status_code == 204, approved.text
    assert names(await listed(client, marta, group)) == ["michal"]


async def test_the_administrator_who_plays_is_a_row_only_once_they_join(client, ogrody):
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    group = await an_official_group(client, tomek, ogrody["id"], join_policy="ANYONE")
    ewa = await a_padel_player(client, "ewa")
    await join(client, ewa, group)

    before = await listed(client, tomek, group)
    await join(client, tomek, group)
    after = await listed(client, tomek, group)

    # Rated in padel, and still no row until he is in it.
    assert names(before) == ["ewa"]
    assert names(after) == ["tomek", "ewa"]
    assert [row["is_administrator"] for row in after] == [True, False]


async def test_a_block_either_way_round_leaves_that_row_out(client, ogrody, marta):
    group = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    ewa = await a_padel_player(client, "ewa")
    kuba = await a_padel_player(client, "kuba")
    zofia = await a_padel_player(client, "zofia")
    for player in (ewa, kuba, zofia):
        await join(client, player, group)

    await block(client, kuba, marta)
    await block(client, marta, zofia)

    assert names(await listed(client, marta, group)) == ["ewa"]
    # A member still sees both of them: the block is between Marta and them.
    assert names(await listed(client, ewa, group)) == ["ewa", "zofia", "kuba"]


# --------------------------------------------------------------------------- #
# Everybody else is still a stranger
# --------------------------------------------------------------------------- #


async def test_running_a_group_opens_no_other_group_s_members(client, ogrody, marta):
    """A colleague's group, another club's and a player group at her own club
    answer Marta exactly as a group that does not exist does — and her own
    answers the colleague and the other club's administrator the same way."""

    martas = await an_official_group(client, marta, ogrody["id"])
    ola = await an_administrator_who_plays(client, ogrody, "ola")
    olas = await an_official_group(client, ola, ogrody["id"], name="Ogrody open play")
    bonarka_id, bonarka_desk = await club_signs_up(
        client, name="Bonarka", email="desk@bonarka.pl"
    )
    piotr = await made_an_administrator(
        client, bonarka_desk, await a_padel_player(client, "piotr"), "Piotr"
    )
    bonarkas = await an_official_group(client, piotr, bonarka_id, name="Bonarka 7")
    karol = await a_padel_player(client, "karol")
    player_group = await a_group(
        client, karol, {"id": ogrody["id"]}, name="Ogrody wieczorem"
    )

    for group in (olas, bonarkas, player_group):
        answered = await members(client, marta, group)
        assert answered.status_code == 404
        assert refusal(answered) == await a_stranger_s_refusal(client, marta)
    for reader in (ola, piotr):
        answered = await members(client, reader, martas)
        assert answered.json()["code"] == "group_not_found"
        assert refusal(answered) == await a_stranger_s_refusal(client, reader)


async def test_a_removed_administrator_is_a_stranger_again(client, ogrody, marta):
    group = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    await join(client, await a_padel_player(client, "ewa"), group)
    assert names(await listed(client, marta, group)) == ["ewa"]

    await removes(client, ogrody, marta)

    assert refusal(await members(client, marta, group)) == await a_stranger_s_refusal(
        client, marta
    )


async def test_a_handed_over_group_is_read_by_whoever_runs_it_now(
    client, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    await join(client, await a_padel_player(client, "ewa"), group)
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    refused = await members(client, tomek, group)
    assert refused.json()["code"] == "group_not_found"

    handed = await hands_over(client, ogrody["desk"], group, tomek["administrator_id"])

    assert handed.status_code == 200, handed.text
    assert refusal(await members(client, marta, group)) == await a_stranger_s_refusal(
        client, marta
    )
    assert names(await listed(client, tomek, group)) == ["ewa"]


# --------------------------------------------------------------------------- #
# The record a row opens
# --------------------------------------------------------------------------- #


async def test_marta_opens_the_record_of_anybody_in_the_group_she_runs(
    client, session_factory, ogrody, marta
):
    """She has no profile, so there is no gender of hers for anybody's
    preference to be read against — and running their group needs none."""

    group = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    ewa = await a_member(client, session_factory, "ewa")
    before = await record(client, marta, ewa["id"])

    await join(client, ewa, group)
    opened = await record(client, marta, ewa["id"])

    assert before.status_code == 404
    assert before.json()["code"] == "record_unavailable"
    assert opened.status_code == 200, opened.text
    assert opened.json()["name"] == "ewa"


async def test_the_record_closes_when_she_stops_running_it(
    client, session_factory, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    ewa = await a_member(client, session_factory, "ewa")
    await join(client, ewa, group)
    tomek = await an_administrator_who_plays(client, ogrody, "tomek")
    assert (await record(client, marta, ewa["id"])).status_code == 200
    assert (await record(client, tomek, ewa["id"])).status_code == 404

    handed = await hands_over(client, ogrody["desk"], group, tomek["administrator_id"])

    assert handed.status_code == 200, handed.text
    assert (await record(client, marta, ewa["id"])).status_code == 404
    assert (await record(client, tomek, ewa["id"])).status_code == 200

    await removes(client, ogrody, tomek)

    assert (await record(client, tomek, ewa["id"])).status_code == 404


async def test_a_preference_gates_no_record_for_whoever_runs_the_group_or_anybody(
    client, session_factory, ogrody
):
    """Kuba plays with women only. Piotr, a man in the same group, and Tomek, a
    man who runs it, both open his record: a preference says who a player is
    willing to be *matched* with, and the record reads no preference at all
    (#575) — whether or not Tomek has joined the group as a player."""

    tomek = await made_an_administrator(
        client,
        ogrody["desk"],
        await a_member(client, session_factory, "tomek", gender="MAN"),
        "Tomek",
    )
    group = await an_official_group(client, tomek, ogrody["id"], join_policy="ANYONE")
    kuba = await a_member(
        client, session_factory, "kuba", gender="MAN", gender_preference="WOMEN_ONLY"
    )
    ewa = await a_member(client, session_factory, "ewa")
    piotr = await a_member(client, session_factory, "piotr", gender="MAN")
    for player in (kuba, ewa, piotr):
        await join(client, player, group)

    assert (await record(client, piotr, ewa["id"])).status_code == 200
    assert (await record(client, piotr, kuba["id"])).status_code == 200
    assert (await record(client, tomek, kuba["id"])).status_code == 200

    await join(client, tomek, group)

    assert (await record(client, tomek, kuba["id"])).status_code == 200


async def test_every_other_gate_still_refuses_whoever_runs_it(
    client, session_factory, ogrody, marta
):
    group = await an_official_group(client, marta, ogrody["id"], join_policy="ANYONE")
    ewa = await a_member(client, session_factory, "ewa")
    kuba = await a_member(client, session_factory, "kuba")
    zofia = await a_member(client, session_factory, "zofia")
    for player in (ewa, kuba, zofia):
        await join(client, player, group)
    await block(client, kuba, marta)

    assert (await record(client, marta, kuba["id"])).status_code == 404

    world.hold_only(client, ewa["id"])
    assert (await record(client, marta, ewa["id"])).status_code == 404
    assert (await record(client, marta, zofia["id"])).status_code == 200

    world.hold_only(client, UUID(marta["id"]))
    assert (await record(client, marta, zofia["id"])).status_code == 404

    world.hold_only(client)
    world.may_not_show(client, zofia["id"])
    assert (await record(client, marta, zofia["id"])).status_code == 404
    assert (await record(client, marta, ewa["id"])).status_code == 200

"""**Friends** — a request between group-mates, and the answer, over HTTP as the
player app calls it (``docs/adr/0202`` §1–§2; the mechanics §3; #745).

The cast, all in **Kazimierz crew**, a padel group:

- **Inés** taps **+ Add** on Tomek in Members. Tomek taps **Not now**: she still
  reads *request sent* and can't ask again. Later he accepts from her record.
- **Kuba** and **Tomek** ask each other before either answers: friends at once.
- **Tomek** blocks **Michał**, his friend. The friendship ends silently. Michał
  asks again and reads *request sent* for ever; Tomek never sees it.
- **Kuba** reads Members while Tomek and Magda are friends, and nothing tells
  him so.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.kernel import Sport
from tests.api import players_world as players
from tests.api.test_group_members import a_padel_player, listed
from tests.api.test_groups import a_club, a_group, join

FRIENDS = "/api/v1/friends"
REQUESTS = f"{FRIENDS}/requests"


@pytest.fixture
async def crew(client) -> dict[str, dict]:
    """Kazimierz crew — Karol's group, with everybody else in it."""

    karol = await a_padel_player(client, "karol")
    group = await a_group(client, karol, await a_club(client), name="Kazimierz crew")
    cast = {"karol": karol}
    for name in ("ines", "tomek", "kuba", "magda", "michal"):
        cast[name] = await a_padel_player(client, name)
        joined = await join(client, cast[name], group)
        assert joined.status_code in (200, 201), joined.text
    cast["group"] = group
    return cast


async def asks(
    client, requester: dict, addressee: dict, group: dict | None = None, **extra
):
    body: dict = {"player_id": str(addressee["id"]), "made_from": "MEMBERS"}
    if group is not None:
        body |= {"group_id": group["id"], "sport": "PADEL"}
    return await client.post(REQUESTS, json=body | extra, headers=requester["headers"])


async def asked(client, requester: dict, addressee: dict, group: dict) -> str:
    answer = await asks(client, requester, addressee, group)
    assert answer.status_code == 200, answer.text
    return answer.json()["relation"]


async def accepts(client, reader: dict, requester: dict):
    return await client.post(
        f"{REQUESTS}/{requester['id']}/acceptance", headers=reader["headers"]
    )


async def sets_aside(client, reader: dict, requester: dict):
    return await client.post(
        f"{REQUESTS}/{requester['id']}/set-aside", headers=reader["headers"]
    )


async def relation_on_members(client, reader: dict, other: dict, group: dict) -> str:
    rows = await listed(client, reader, group)
    [row] = [row for row in rows if row["player_id"] == str(other["id"])]
    return row["relation"]


async def requests_of(client, reader: dict, direction: str) -> list[dict]:
    read = await client.get(
        REQUESTS, params={"direction": direction}, headers=reader["headers"]
    )
    assert read.status_code == 200, read.text
    return read.json()["requests"]


async def friends_of(client, reader: dict, **params) -> list[dict]:
    read = await client.get(FRIENDS, params=params, headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()["friends"]


def without_trace(body: dict) -> dict:
    return {key: value for key, value in body.items() if key != "trace_id"}


async def blocks(client, session_factory, blocker: dict, blocked: dict) -> None:
    made = await players.block_between(
        client, blocker["headers"]["Authorization"].split()[1], blocked["id"]
    )
    assert made.status_code == 204, made.text
    await players.deliver_the_outbox(session_factory)


# --------------------------------------------------------------------------- #
# Inés asks, Tomek sets it aside, then accepts
# --------------------------------------------------------------------------- #


async def test_a_request_reads_sent_to_the_asker_and_asked_you_to_the_asked(
    client, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]

    assert await asked(client, ines, tomek, group) == "SENT"

    assert await relation_on_members(client, ines, tomek, group) == "SENT"
    assert await relation_on_members(client, tomek, ines, group) == "ASKED_YOU"
    [waiting] = await requests_of(client, tomek, "ASKED_YOU")
    assert waiting["player_id"] == str(ines["id"])
    assert waiting["nickname"] == "ines"
    assert waiting["set_aside"] is False
    [mine] = await requests_of(client, ines, "YOU_ASKED")
    assert mine["player_id"] == str(tomek["id"])


async def test_not_now_keeps_the_request_open_and_the_asker_cannot_ask_again(
    client, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)

    set_aside = await sets_aside(client, tomek, ines)
    again = await sets_aside(client, tomek, ines)

    assert set_aside.status_code == 204, set_aside.text
    assert again.status_code == 204, again.text
    # Inés reads exactly what she read before.
    assert await relation_on_members(client, ines, tomek, group) == "SENT"
    [mine] = await requests_of(client, ines, "YOU_ASKED")
    assert mine["set_aside"] is False
    twice = await asks(client, ines, tomek, group)
    assert twice.status_code == 409
    assert twice.json()["code"] == "friend_request_already_sent"
    # Tomek can still answer it: it is on *Asked you*, set aside.
    [waiting] = await requests_of(client, tomek, "ASKED_YOU")
    assert waiting["set_aside"] is True
    assert await relation_on_members(client, tomek, ines, group) == "ASKED_YOU"


async def test_accepting_later_makes_them_friends_everywhere_at_once(client, crew):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)
    await sets_aside(client, tomek, ines)

    accepted = await accepts(client, tomek, ines)

    assert accepted.status_code == 200, accepted.text
    assert accepted.json() == {"relation": "FRIEND"}
    assert await relation_on_members(client, ines, tomek, group) == "FRIEND"
    assert await relation_on_members(client, tomek, ines, group) == "FRIEND"
    assert await requests_of(client, tomek, "ASKED_YOU") == []
    assert await requests_of(client, ines, "YOU_ASKED") == []
    assert [f["nickname"] for f in await friends_of(client, ines)] == ["tomek"]
    assert [f["nickname"] for f in await friends_of(client, tomek)] == ["ines"]


async def test_only_the_person_asked_answers(client, crew):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)

    by_the_asker = await accepts(client, ines, tomek)
    nothing_asked = await accepts(client, tomek, crew["kuba"])

    assert by_the_asker.status_code == 404
    assert by_the_asker.json()["code"] == "friend_request_not_found"
    assert nothing_asked.status_code == 404
    assert nothing_asked.json()["code"] == "friend_request_not_found"


# --------------------------------------------------------------------------- #
# Crossed requests
# --------------------------------------------------------------------------- #


async def test_two_requests_that_cross_make_friends_at_once(client, crew):
    kuba, tomek, group = crew["kuba"], crew["tomek"], crew["group"]

    assert await asked(client, kuba, tomek, group) == "SENT"
    assert await asked(client, tomek, kuba, group) == "FRIEND"

    assert await relation_on_members(client, kuba, tomek, group) == "FRIEND"
    assert await relation_on_members(client, tomek, kuba, group) == "FRIEND"
    assert await requests_of(client, kuba, "YOU_ASKED") == []
    assert await requests_of(client, tomek, "ASKED_YOU") == []


async def test_nobody_asks_a_friend(client, crew):
    kuba, tomek, group = crew["kuba"], crew["tomek"], crew["group"]
    await asked(client, kuba, tomek, group)
    await accepts(client, tomek, kuba)

    again = await asks(client, kuba, tomek, group)

    assert again.status_code == 409
    assert again.json()["code"] == "already_friends"


# --------------------------------------------------------------------------- #
# Cancelling and removing — silent, idempotent, and no game touched
# --------------------------------------------------------------------------- #


async def test_a_cancelled_request_is_gone_from_both_sides(client, crew):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)

    cancelled = await client.delete(
        f"{REQUESTS}/{tomek['id']}", headers=ines["headers"]
    )
    nothing_left = await client.delete(
        f"{REQUESTS}/{tomek['id']}", headers=ines["headers"]
    )

    assert cancelled.status_code == 204, cancelled.text
    assert nothing_left.status_code == 204, nothing_left.text
    assert await relation_on_members(client, tomek, ines, group) == "NONE"
    assert await relation_on_members(client, ines, tomek, group) == "NONE"
    assert await requests_of(client, tomek, "ASKED_YOU") == []
    # And she may ask again.
    assert await asked(client, ines, tomek, group) == "SENT"


async def test_the_asked_cannot_cancel_somebody_elses_request(client, crew):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)

    cancelled = await client.delete(
        f"{REQUESTS}/{ines['id']}", headers=tomek["headers"]
    )

    assert cancelled.status_code == 204
    assert await relation_on_members(client, tomek, ines, group) == "ASKED_YOU"


async def test_removing_a_friend_ends_it_for_both_and_records_nothing_twice(
    client, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)
    await accepts(client, tomek, ines)

    removed = await client.delete(f"{FRIENDS}/{ines['id']}", headers=tomek["headers"])
    again = await client.delete(f"{FRIENDS}/{ines['id']}", headers=tomek["headers"])

    assert removed.status_code == 204, removed.text
    assert again.status_code == 204, again.text
    assert await relation_on_members(client, ines, tomek, group) == "NONE"
    assert await friends_of(client, ines) == []
    assert await friends_of(client, tomek) == []


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #


async def test_a_block_ends_a_friendship_silently(client, session_factory, crew):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await asked(client, michal, tomek, group)
    await accepts(client, tomek, michal)

    await blocks(client, session_factory, tomek, michal)

    assert await relation_on_members(client, michal, tomek, group) == "NONE"
    assert await relation_on_members(client, tomek, michal, group) == "NONE"
    assert await friends_of(client, michal) == []


async def test_a_block_by_the_other_side_ends_it_too(client, session_factory, crew):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await asked(client, michal, tomek, group)
    await accepts(client, tomek, michal)

    await blocks(client, session_factory, michal, tomek)

    assert await friends_of(client, tomek) == []


async def test_a_block_ends_an_open_request(client, session_factory, crew):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await asked(client, tomek, michal, group)

    await blocks(client, session_factory, michal, tomek)

    assert await requests_of(client, tomek, "YOU_ASKED") == []
    assert await requests_of(client, michal, "ASKED_YOU") == []


async def test_a_blocked_players_request_reads_sent_and_the_blocker_never_sees_it(
    client, session_factory, crew
):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await asked(client, michal, tomek, group)
    await accepts(client, tomek, michal)
    await blocks(client, session_factory, tomek, michal)

    assert await asked(client, michal, tomek, group) == "SENT"

    # Michał reads exactly what a request set aside would show him.
    assert await relation_on_members(client, michal, tomek, group) == "SENT"
    [mine] = await requests_of(client, michal, "YOU_ASKED")
    assert mine["player_id"] == str(tomek["id"])
    twice = await asks(client, michal, tomek, group)
    assert twice.json()["code"] == "friend_request_already_sent"
    # Tomek sees nothing, anywhere.
    assert await relation_on_members(client, tomek, michal, group) == "NONE"
    assert await requests_of(client, tomek, "ASKED_YOU") == []
    refused = await accepts(client, tomek, michal)
    assert refused.status_code == 404
    assert refused.json()["code"] == "friend_request_not_found"
    set_aside = await sets_aside(client, tomek, michal)
    assert set_aside.status_code == 404


async def test_nobody_asks_somebody_they_blocked(client, session_factory, crew):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await blocks(client, session_factory, tomek, michal)

    refused = await asks(client, tomek, michal, group)

    assert refused.status_code == 409
    assert refused.json()["code"] == "unblock_them_first"


async def test_unblocking_brings_nothing_back(client, session_factory, crew):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await asked(client, michal, tomek, group)
    await accepts(client, tomek, michal)
    await blocks(client, session_factory, tomek, michal)

    lifted = await client.delete(
        f"/api/v1/blocks/{michal['id']}", headers=tomek["headers"]
    )
    await players.deliver_the_outbox(session_factory)

    assert lifted.status_code == 204
    assert await friends_of(client, tomek) == []
    assert await relation_on_members(client, tomek, michal, group) == "NONE"


# --------------------------------------------------------------------------- #
# Only the reader's own relations
# --------------------------------------------------------------------------- #


async def test_nothing_tells_a_third_player_that_two_others_are_friends(client, crew):
    kuba, tomek, magda, group = (
        crew["kuba"],
        crew["tomek"],
        crew["magda"],
        crew["group"],
    )
    await asked(client, tomek, magda, group)
    await accepts(client, magda, tomek)
    await asked(client, crew["ines"], magda, group)

    rows = await listed(client, kuba, group)

    assert {row["relation"] for row in rows} == {"NONE"}
    assert await friends_of(client, kuba) == []
    assert await requests_of(client, kuba, "ASKED_YOU") == []
    assert await requests_of(client, kuba, "YOU_ASKED") == []


async def test_the_readers_own_row_reads_none(client, crew):
    tomek, group = crew["tomek"], crew["group"]

    assert await relation_on_members(client, tomek, tomek, group) == "NONE"


# --------------------------------------------------------------------------- #
# Who can be asked
# --------------------------------------------------------------------------- #


async def test_nobody_asks_themselves(client, crew):
    refused = await asks(client, crew["tomek"], crew["tomek"])

    assert refused.status_code == 400
    assert refused.json()["code"] == "cannot_befriend_yourself"


async def test_a_switched_off_stranger_reads_as_an_id_nobody_holds(client, crew):
    """``docs/adr/0204`` §2: a stranger who turned *Show me to new people* off
    can't be asked, and the refusal names nothing."""

    rated = await players.a_rated_player(client, "stranger")
    stranger = {"id": rated["id"]}
    await players.closed_to_new_people(client, rated["token"])

    outside = await asks(client, crew["tomek"], stranger)
    nobody = await asks(client, crew["tomek"], {"id": uuid4()})

    assert outside.status_code == nobody.status_code == 404
    assert without_trace(outside.json()) == without_trace(nobody.json())
    assert outside.json()["code"] == "player_unavailable"


async def test_a_link_is_not_something_a_phone_sends(client, crew):
    refused = await asks(client, crew["tomek"], crew["ines"], made_from="LINK")

    assert refused.status_code == 422


# --------------------------------------------------------------------------- #
# The Friends page
# --------------------------------------------------------------------------- #


async def test_friends_are_listed_by_nickname_with_every_sport_they_play(client, crew):
    tomek, group = crew["tomek"], crew["group"]
    for name in ("magda", "ines", "kuba"):
        await asked(client, crew[name], tomek, group)
        await accepts(client, tomek, crew[name])

    friends = await friends_of(client, tomek)

    assert [friend["nickname"] for friend in friends] == ["ines", "kuba", "magda"]
    for friend in friends:
        [padel] = friend["sports"]
        assert padel["sport"] == "PADEL"
        assert isinstance(padel["level"], float)
        assert padel["band"]


async def test_with_a_sport_friends_come_highest_level_first_and_unrated_last(
    client, session_factory, crew
):
    tomek, group = crew["tomek"], crew["group"]
    tennis_only = await a_padel_player(client, "zofia")
    await join(client, tennis_only, group)
    for name, mu in (("magda", 2.2), ("ines", 3.4)):
        await players.rate_in(
            session_factory, UUID(str(crew[name]["id"])), Sport.TENNIS, mu=mu
        )
    for friend in (crew["magda"], crew["ines"], tennis_only):
        await asked(client, friend, tomek, group)
        await accepts(client, tomek, friend)

    friends = await friends_of(client, tomek, sport="TENNIS")

    assert [friend["nickname"] for friend in friends] == ["ines", "magda", "zofia"]
    assert [len(friend["sports"]) for friend in friends] == [1, 1, 0]
    assert friends[0]["sports"][0]["sport"] == "TENNIS"


# --------------------------------------------------------------------------- #
# Add friends — from your groups
# --------------------------------------------------------------------------- #


async def test_each_group_counts_who_the_reader_could_still_add(
    client, session_factory, crew
):
    tomek, group = crew["tomek"], crew["group"]
    # Seven in the crew: Karol, Inés, Tomek, Kuba, Magda, Michał — and a friend,
    # a request each way and a block take four of the other five.
    await asked(client, crew["ines"], tomek, group)
    await accepts(client, tomek, crew["ines"])
    await asked(client, tomek, crew["kuba"], group)
    await asked(client, crew["magda"], tomek, group)
    await sets_aside(client, tomek, crew["magda"])
    await blocks(client, session_factory, tomek, crew["michal"])

    read = await client.get(f"{FRIENDS}/groups", headers=tomek["headers"])

    assert read.status_code == 200, read.text
    [crew_row] = read.json()["groups"]
    assert crew_row == {
        "group_id": group["id"],
        "name": "Kazimierz crew",
        "member_count": 6,
        "to_add": 1,
    }


async def test_somebody_who_blocked_the_reader_is_still_counted_to_add(
    client, session_factory, crew
):
    tomek = crew["tomek"]
    await blocks(client, session_factory, crew["michal"], tomek)

    read = await client.get(f"{FRIENDS}/groups", headers=tomek["headers"])

    [crew_row] = read.json()["groups"]
    assert crew_row["to_add"] == 5


# --------------------------------------------------------------------------- #
# Notices: a request once, *friends made*, and the bell cleared on an answer
# --------------------------------------------------------------------------- #

NOTICES = "/api/v1/players/me/notices"
DEVICES = "/api/v1/players/me/devices"


async def has_a_phone(client, player: dict, name: str) -> str:
    token = f"ExponentPushToken[{name}-phone]"
    registered = await client.post(
        DEVICES, json={"token": token}, headers=player["headers"]
    )
    assert registered.status_code == 204, registered.text
    return token


async def bell_of(client, mailbox, player: dict) -> dict:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def test_a_request_is_told_to_the_person_asked_once(
    client, mailbox, pushes, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    phone = await has_a_phone(client, tomek, "tomek")

    await asked(client, ines, tomek, group)
    bell = await bell_of(client, mailbox, tomek)
    await bell_of(client, mailbox, tomek)

    [notice] = bell["notices"]
    assert notice["kind"] == "FRIEND_REQUEST"
    assert notice["title"] == "ines wants to be your friend"
    assert notice["body"] == "With you in Kazimierz crew · Padel"
    assert notice["opens"] == "HOME"
    assert notice["player_id"] == str(ines["id"])
    assert notice["pool_id"] == group["id"]
    assert notice["game_id"] is None
    assert bell["new_count"] == 1
    [push] = pushes.to(phone)
    assert (push.title, push.body) == (notice["title"], notice["body"])
    # Who asked, and the group and sport it names (#749 hands both to every
    # notice about no game).
    assert push.data == {
        "notice_id": notice["notice_id"],
        "kind": "FRIEND_REQUEST",
        "opens": "HOME",
        "player_id": str(ines["id"]),
        "pool_id": group["id"],
        "sport": "PADEL",
    }
    # The asker is told nothing.
    assert (await bell_of(client, mailbox, ines))["notices"] == []


async def test_not_now_clears_the_request_from_the_bell_and_tells_nobody(
    client, mailbox, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)
    await bell_of(client, mailbox, tomek)

    await sets_aside(client, tomek, ines)

    bell = await bell_of(client, mailbox, tomek)
    assert bell["notices"] == []
    assert bell["new_count"] == 0
    assert (await bell_of(client, mailbox, ines))["notices"] == []


async def test_accepting_tells_the_asker_and_clears_the_request(
    client, mailbox, pushes, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    phone = await has_a_phone(client, ines, "ines")
    await asked(client, ines, tomek, group)
    await bell_of(client, mailbox, tomek)

    await accepts(client, tomek, ines)

    assert (await bell_of(client, mailbox, tomek))["notices"] == []
    [told] = (await bell_of(client, mailbox, ines))["notices"]
    assert told["kind"] == "FRIENDS_MADE"
    assert told["title"] == "tomek said yes — you're friends"
    assert told["opens"] == "RECORD"
    assert told["player_id"] == str(tomek["id"])
    [push] = pushes.to(phone)
    assert push.title == "tomek said yes — you're friends"
    assert push.data == {
        "notice_id": told["notice_id"],
        "kind": "FRIENDS_MADE",
        "opens": "RECORD",
        "player_id": str(tomek["id"]),
    }


async def test_crossed_requests_tell_both_that_they_are_friends(client, mailbox, crew):
    kuba, tomek, group = crew["kuba"], crew["tomek"], crew["group"]
    await asked(client, kuba, tomek, group)
    await asked(client, tomek, kuba, group)

    [to_tomek] = (await bell_of(client, mailbox, tomek))["notices"]
    [to_kuba] = (await bell_of(client, mailbox, kuba))["notices"]

    assert to_tomek["title"] == "You and kuba are friends now"
    assert to_kuba["title"] == "You and tomek are friends now"
    assert {to_tomek["kind"], to_kuba["kind"]} == {"FRIENDS_MADE"}


async def test_a_cancelled_request_leaves_the_bell_and_is_told_nobody(
    client, mailbox, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)
    assert len((await bell_of(client, mailbox, tomek))["notices"]) == 1

    await client.delete(f"{REQUESTS}/{tomek['id']}", headers=ines["headers"])

    assert (await bell_of(client, mailbox, tomek))["notices"] == []


async def test_a_request_cancelled_before_its_delivery_is_never_told(
    client, mailbox, pushes, crew
):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    phone = await has_a_phone(client, tomek, "tomek")
    await asked(client, ines, tomek, group)
    await client.delete(f"{REQUESTS}/{tomek['id']}", headers=ines["headers"])

    assert (await bell_of(client, mailbox, tomek))["notices"] == []
    assert pushes.to(phone) == []


async def test_a_blocked_players_request_is_never_told_to_the_blocker(
    client, session_factory, mailbox, pushes, crew
):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    phone = await has_a_phone(client, tomek, "tomek")
    await blocks(client, session_factory, tomek, michal)

    await asked(client, michal, tomek, group)

    assert (await bell_of(client, mailbox, tomek))["notices"] == []
    assert pushes.to(phone) == []


async def test_a_block_clears_a_request_already_told(
    client, session_factory, mailbox, crew
):
    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await asked(client, michal, tomek, group)
    assert len((await bell_of(client, mailbox, tomek))["notices"]) == 1

    await blocks(client, session_factory, tomek, michal)

    assert (await bell_of(client, mailbox, tomek))["notices"] == []


async def test_removing_and_cancelling_tell_nobody(client, mailbox, crew):
    ines, tomek, group = crew["ines"], crew["tomek"], crew["group"]
    await asked(client, ines, tomek, group)
    await accepts(client, tomek, ines)
    before = (await bell_of(client, mailbox, ines))["notices"]

    await client.delete(f"{FRIENDS}/{tomek['id']}", headers=ines["headers"])

    assert (await bell_of(client, mailbox, ines))["notices"] == before
    assert (await bell_of(client, mailbox, tomek))["notices"] == []


async def test_a_request_from_a_screen_with_no_group_says_where_to_answer(
    client, mailbox, crew
):
    ines, tomek = crew["ines"], crew["tomek"]
    answer = await asks(client, ines, tomek, made_from="RECORD")
    assert answer.status_code == 200, answer.text

    [notice] = (await bell_of(client, mailbox, tomek))["notices"]

    assert notice["body"] == "Answer it on Home."
    assert notice["pool_id"] is None


async def test_a_request_made_during_a_block_stays_unseen_after_the_unblock(
    client, session_factory, mailbox, crew
):
    """*Michał reads request sent forever, and Tomek never sees it* — not after
    Tomek unblocks him either (the mechanics §3.5)."""

    tomek, michal, group = crew["tomek"], crew["michal"], crew["group"]
    await blocks(client, session_factory, tomek, michal)
    assert await asked(client, michal, tomek, group) == "SENT"

    lifted = await client.delete(
        f"/api/v1/blocks/{michal['id']}", headers=tomek["headers"]
    )
    await players.deliver_the_outbox(session_factory)

    assert lifted.status_code == 204
    assert await relation_on_members(client, tomek, michal, group) == "NONE"
    assert await requests_of(client, tomek, "ASKED_YOU") == []
    assert (await accepts(client, tomek, michal)).status_code == 404
    assert (await bell_of(client, mailbox, tomek))["notices"] == []
    assert await relation_on_members(client, michal, tomek, group) == "SENT"


async def test_a_group_the_two_do_not_share_is_not_named(client, mailbox, crew):
    """A client sending somebody else's group puts no name on the notice."""

    ines, tomek = crew["ines"], crew["tomek"]
    elsewhere = await a_group(
        client, crew["karol"], await a_club(client, "Wisła Park"), name="Elsewhere"
    )

    answer = await asks(client, ines, tomek, elsewhere)

    assert answer.status_code == 200, answer.text
    [notice] = (await bell_of(client, mailbox, tomek))["notices"]
    assert notice["pool_id"] is None
    assert notice["body"] == "Answer it on Home."

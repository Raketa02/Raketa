"""Strangers from the ranking: a listed player's record, a request from the
ranking with a daily limit, and a block closing the record both ways, read the
way the player app reads them (#773; ``docs/adr/0203`` §8–§9; the rankings
mechanics §11–§13).

Twelve padel players are listed on General, a hundredth apart. **Piotr** is
3rd, and shares nothing with **Tomek**:

- Tomek opens Piotr's record. It opens in full, and offers *Add friend*.
- Tomek sends Piotr a request from the ranking. Piotr's card and notice read
  *Found you in the padel ranking*.
- Tomek's 11th request that Warsaw day to people outside his groups is refused
  with the daily limit. A request to a group-mate still goes through.
- **Ola** has no level and only browses. She opens Piotr's record too.
- **Marek**, in a group with Tomek, blocks him: neither opens the other's
  record any more.

Every claim is read off the player routes — ``GET /players/{id}/record``,
``POST /friends/requests``, ``GET /home``, ``GET /players/me/notices`` — the
outbox delivered as the worker delivers it.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.kernel import instant
from tests.api import players_world as players
from tests.api.players_world import deliver_the_outbox
from tests.api.rankings_world import a_listed_crowd, move_on
from tests.api.test_group_members import a_padel_player
from tests.api.test_groups import a_club, a_group, join
from tests.api.test_ranking_hidden_and_blocks import turns

REQUESTS = "/api/v1/friends/requests"
NOTICES = "/api/v1/players/me/notices"
WARSAW = ZoneInfo("Europe/Warsaw")


@pytest.fixture
async def listed(client, session_factory, clock) -> list[dict]:
    """Twelve listed in padel, ``crowd000`` first, none of them *New*."""

    crowd = await a_listed_crowd(client, session_factory, clock, 12)
    for player in crowd:
        player["headers"] = players.auth(player["token"])
    return crowd


@pytest.fixture
async def tomek(client) -> dict:
    """Rated in padel, listed nowhere, in nobody's group."""

    return await a_padel_player(client, "tomek")


async def record_of(client, reader: dict, subject: dict):
    return await client.get(
        f"/api/v1/players/{subject['id']}/record",
        params={"sport": "PADEL"},
        headers=reader["headers"],
    )


async def asks(client, requester: dict, addressee: dict, **body):
    return await client.post(
        REQUESTS,
        json={"player_id": str(addressee["id"]), "made_from": "RANKING"}
        | {"sport": "PADEL"}
        | body,
        headers=requester["headers"],
    )


async def in_one_group(client, owner: dict, *others: dict) -> dict:
    group = await a_group(client, owner, await a_club(client), name="Padel po pracy")
    for player in others:
        joined = await join(client, player, group)
        assert joined.status_code in (200, 201), joined.text
    return group


async def blocks(client, blocker: dict, blocked: dict) -> None:
    made = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked["id"])},
        headers=blocker["headers"],
    )
    assert made.status_code == 204, made.text


def without_trace(body: dict) -> dict:
    return {key: value for key, value in body.items() if key != "trace_id"}


async def the_one_refusal(client, reader: dict) -> dict:
    """What a record nobody can open reads: an id nobody holds."""

    refused = await record_of(client, reader, {"id": uuid4()})
    assert refused.status_code == 404, refused.text
    return without_trace(refused.json())


# --------------------------------------------------------------------------- #
# The record: a fourth strand, for any reader
# --------------------------------------------------------------------------- #


async def test_a_stranger_opens_a_listed_players_full_record(client, listed, tomek):
    piotr = listed[2]

    opened = await record_of(client, tomek, piotr)

    assert opened.status_code == 200, opened.text
    record = opened.json()
    assert record["nickname"] == piotr["nickname"]
    assert record["is_self"] is False
    assert record["skill"]["sport"] == "PADEL"
    assert record["skill"]["level"] == pytest.approx(5.98)
    assert record["reliability"]["player_score"] == 100
    assert record["relation"] == "NONE"
    assert record["can_add_friend"] is True
    assert "blocked_by_you" not in record


async def test_a_reader_with_no_level_opens_it_and_may_ask(client, listed):
    piotr = listed[2]
    ola_id, token = await players.register(client, "ola")
    ola = {"id": ola_id, "headers": players.auth(token)}

    opened = await record_of(client, ola, piotr)
    asked = await asks(client, ola, piotr)

    assert opened.status_code == 200, opened.text
    assert opened.json()["can_add_friend"] is True
    assert asked.status_code == 200, asked.text
    assert asked.json()["relation"] == "SENT"


async def test_a_player_short_of_general_is_refused_to_a_stranger(
    client, session_factory, clock, tomek
):
    four_results, token = await players.a_player_on_the_log(
        client, session_factory, "kasia", mu=5.5
    )
    async with session_factory() as session:
        for result in range(4):
            await move_on(
                session,
                four_results,
                5.5,
                at=instant(clock.now() - timedelta(days=2, minutes=-result)),
            )
    await deliver_the_outbox(session_factory)

    refused = await record_of(client, tomek, {"id": four_results})

    assert refused.status_code == 404, refused.text
    assert without_trace(refused.json()) == await the_one_refusal(client, tomek)


async def test_a_player_off_the_list_for_90_days_is_refused_to_a_stranger(
    client, clock, listed, tomek
):
    piotr = listed[2]
    assert (await record_of(client, tomek, piotr)).status_code == 200

    # Their last results settled eight days ago: 83 more is past the 90.
    clock.move(timedelta(days=83))
    refused = await record_of(client, tomek, piotr)

    assert refused.status_code == 404, refused.text
    assert without_trace(refused.json()) == await the_one_refusal(client, tomek)


async def test_a_hidden_player_is_refused_to_a_stranger_and_open_to_a_group_mate(
    client, session_factory, listed, tomek
):
    piotr, karol = listed[2], listed[5]
    await in_one_group(client, karol, piotr)

    await turns(client, session_factory, piotr, "HIDDEN")
    stranger = await record_of(client, tomek, piotr)
    group_mate = await record_of(client, karol, piotr)

    assert stranger.status_code == 404, stranger.text
    assert without_trace(stranger.json()) == await the_one_refusal(client, tomek)
    assert group_mate.status_code == 200, group_mate.text
    # A hidden group-mate may still be asked, uncounted (the mechanics §18).
    assert group_mate.json()["can_add_friend"] is True


async def test_the_switch_closes_the_record_on_the_next_open_before_any_delivery(
    client, listed, tomek
):
    """The switch is read off the profile, live: a stranger's next tap is
    refused whether or not the ranking has followed it yet."""

    piotr = listed[2]
    switched = await client.put(
        "/api/v1/players/me/ranking-visibility",
        json={"visibility": "HIDDEN"},
        headers=piotr["headers"],
    )
    assert switched.status_code == 204, switched.text

    assert (await record_of(client, tomek, piotr)).status_code == 404


# --------------------------------------------------------------------------- #
# A block closes the record both ways, group-mates included
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("blocker", ["tomek", "marek"])
async def test_a_block_closes_the_record_both_ways_group_mates_included(
    client, listed, blocker
):
    """Tomek blocks Marek — or Marek blocks Tomek — and they share a group:
    neither opens the other's record, and both read the one refusal."""

    cast = {"marek": listed[4], "tomek": listed[6]}
    marek, tomek = cast["marek"], cast["tomek"]
    await in_one_group(client, marek, tomek)
    assert (await record_of(client, tomek, marek)).status_code == 200
    assert (await record_of(client, marek, tomek)).status_code == 200

    blocked = marek if blocker == "tomek" else tomek
    await blocks(client, cast[blocker], blocked)
    tomek_reads = await record_of(client, tomek, marek)
    marek_reads = await record_of(client, marek, tomek)

    refusal = await the_one_refusal(client, tomek)
    for refused in (tomek_reads, marek_reads):
        assert refused.status_code == 404, refused.text
        assert without_trace(refused.json()) == refusal


async def test_a_lifted_block_opens_the_record_again(client, listed):
    marek, tomek = listed[4], listed[6]
    await blocks(client, tomek, marek)
    assert (await record_of(client, marek, tomek)).status_code == 404

    lifted = await client.delete(
        f"/api/v1/blocks/{marek['id']}", headers=tomek["headers"]
    )
    assert lifted.status_code == 204, lifted.text

    assert (await record_of(client, marek, tomek)).status_code == 200
    assert (await record_of(client, tomek, marek)).status_code == 200


# --------------------------------------------------------------------------- #
# A request from the ranking
# --------------------------------------------------------------------------- #


async def test_a_strangers_request_from_the_ranking_reads_the_ranking(
    client, mailbox, listed, tomek
):
    piotr = listed[2]

    asked = await asks(client, tomek, piotr)
    await mailbox.drain()
    home = await client.get("/api/v1/home", headers=piotr["headers"])
    bell = await client.get(NOTICES, headers=piotr["headers"])

    assert asked.status_code == 200, asked.text
    assert asked.json()["relation"] == "SENT"
    [card] = home.json()["friend_requests"]
    assert card["player_id"] == str(tomek["id"])
    assert card["from_ranking"] is True
    assert card["by_link"] is False
    assert card["sport"] == "PADEL"
    assert card["group"] is None
    [notice] = bell.json()["notices"]
    assert notice["kind"] == "FRIEND_REQUEST"
    assert notice["title"] == "tomek wants to be your friend"
    assert notice["body"] == "Found you in the padel ranking"
    assert notice["sport"] == "PADEL"
    assert notice["pool_id"] is None
    # And the record reads it from Tomek's side.
    record = (await record_of(client, tomek, piotr)).json()
    assert (record["relation"], record["can_add_friend"]) == ("SENT", False)


async def test_a_request_from_the_ranking_to_a_group_mate_names_the_ranking(
    client, mailbox, listed
):
    piotr, karol = listed[2], listed[5]
    group = await in_one_group(client, karol, piotr)

    asked = await asks(client, karol, piotr, group_id=group["id"])
    await mailbox.drain()
    [card] = (await client.get("/api/v1/home", headers=piotr["headers"])).json()[
        "friend_requests"
    ]

    assert asked.status_code == 200, asked.text
    assert card["from_ranking"] is True
    assert card["group"] is None


async def test_a_request_from_the_ranking_names_its_sport(client, listed, tomek):
    refused = await client.post(
        REQUESTS,
        json={"player_id": str(listed[2]["id"]), "made_from": "RANKING"},
        headers=tomek["headers"],
    )

    assert refused.status_code == 422, refused.text


async def test_a_request_to_a_hidden_player_from_the_ranking_is_refused(
    client, session_factory, listed, tomek
):
    piotr = listed[2]
    unknown = await asks(client, tomek, {"id": uuid4()})

    await turns(client, session_factory, piotr, "HIDDEN")
    refused = await asks(client, tomek, piotr)

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "player_not_in_your_groups"
    assert without_trace(refused.json()) == without_trace(unknown.json())


async def test_a_record_opened_on_a_court_alone_offers_no_add_friend(
    client, session_factory, tomek
):
    """Somebody Tomek played with, in none of his groups and on no list:
    the court opens the record, and nothing admits a request."""

    met_id, token = await players.a_player_on_the_log(
        client, session_factory, "witek", mu=3.0
    )
    witek = {"id": met_id, "headers": players.auth(token)}
    await players.a_booked_game(
        session_factory, side_a=(tomek["id"],), side_b=(witek["id"],)
    )

    opened = await record_of(client, tomek, witek)
    asked = await asks(client, tomek, witek)

    assert opened.status_code == 200, opened.text
    assert opened.json()["relation"] == "NONE"
    assert opened.json()["can_add_friend"] is False
    assert asked.status_code == 404, asked.text
    assert asked.json()["code"] == "player_not_in_your_groups"


# --------------------------------------------------------------------------- #
# The daily limit
# --------------------------------------------------------------------------- #


async def test_the_eleventh_request_to_strangers_is_refused_and_group_mates_never_count(
    client, listed, tomek
):
    karol = await a_padel_player(client, "karol")
    await in_one_group(client, tomek, karol, listed[11])

    # A group-mate before, from the ranking too: never counted.
    assert (await asks(client, tomek, listed[11])).status_code == 200
    for stranger in listed[:10]:
        sent = await asks(client, tomek, stranger)
        assert sent.status_code == 200, (stranger["nickname"], sent.text)

    eleventh = await asks(client, tomek, listed[10])
    group_mate = await asks(client, tomek, karol, made_from="MEMBERS")

    assert eleventh.status_code == 429, eleventh.text
    assert eleventh.json()["code"] == "daily_request_limit"
    assert eleventh.json()["message"] == (
        "You've sent 10 requests to new people today. Try again tomorrow."
    )
    record = (await record_of(client, tomek, listed[10])).json()
    assert record["relation"] == "NONE"
    assert group_mate.status_code == 200, group_mate.text


async def test_a_request_taken_back_still_counts(client, listed, tomek):
    for stranger in listed[:10]:
        assert (await asks(client, tomek, stranger)).status_code == 200
    cancelled = await client.delete(
        f"{REQUESTS}/{listed[0]['id']}", headers=tomek["headers"]
    )
    assert cancelled.status_code == 204, cancelled.text

    again = await asks(client, tomek, listed[0])

    assert again.status_code == 429, again.text


async def test_answering_is_never_limited(client, listed):
    """Accepting, or asking somebody who asked you first, is an answer — an
    answer is not a request sent (the mechanics §13.3)."""

    piotr, rest = listed[0], listed[1:]
    for stranger in rest[:10]:
        assert (await asks(client, piotr, stranger)).status_code == 200
    ola_id, token = await players.register(client, "ola")
    ola = {"id": ola_id, "headers": players.auth(token)}
    for asker in (ola, rest[10]):
        assert (await asks(client, asker, piotr)).status_code == 200

    accepted = await client.post(
        f"{REQUESTS}/{ola['id']}/acceptance", headers=piotr["headers"]
    )
    crossed = await asks(client, piotr, rest[10])

    assert accepted.status_code == 200, accepted.text
    assert crossed.status_code == 200, crossed.text
    assert crossed.json()["relation"] == "FRIEND"


async def test_a_link_request_never_counts(client, listed, tomek):
    for stranger in listed[:10]:
        assert (await asks(client, tomek, stranger)).status_code == 200
    link = await client.get("/api/v1/friends/link", headers=tomek["headers"])
    assert link.status_code == 200, link.text

    opened = await client.post(
        f"/api/v1/friends/links/{link.json()['code']}/opening",
        headers=listed[10]["headers"],
    )

    assert opened.status_code == 200, opened.text
    assert opened.json()["relation"] == "ASKED_YOU"


def _next_warsaw(clock, at: time) -> datetime:
    """The next instant the Warsaw wall clock reads ``at``."""

    now = clock.now().astimezone(WARSAW)
    wall = datetime.combine(now.date(), at, tzinfo=WARSAW)
    if wall <= now:
        wall = datetime.combine(now.date() + timedelta(days=1), at, tzinfo=WARSAW)
    return wall.astimezone(timezone.utc)


async def test_the_limit_resets_at_warsaw_midnight_not_utcs(
    client, clock, listed, tomek
):
    clock.move(_next_warsaw(clock, time(23, 30)) - clock.now())
    for stranger in listed[:10]:
        assert (await asks(client, tomek, stranger)).status_code == 200
    assert (await asks(client, tomek, listed[10])).status_code == 429

    # Half past midnight in Warsaw — still the same day in UTC.
    clock.move(timedelta(hours=1))
    after_midnight = await asks(client, tomek, listed[10])

    assert after_midnight.status_code == 200, after_midnight.text

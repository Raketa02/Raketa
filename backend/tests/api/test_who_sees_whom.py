"""Who sees whom: any player opens any record and asks anyone, with no daily
limit; *Show me to new people* is the one way out; a block closes the record
both ways — read the way the player app reads them (#791; ``docs/adr/0204``
§2; the home-rows mechanics §4.1–§4.4).

- **Kuba**, rated in padel and a stranger to everybody, opens **Tomek**'s
  record — Tomek is listed nowhere — sees *Add friend* and asks him.
- **Ola** has no level and opens it too, and asks.
- Tomek's 11th and 50th requests of the day go through.
- **Bartek** turns the switch off: strangers read the record's one refusal and
  are refused a request with one unnamed code, while his group-mate, his
  game-mate and his friend still open his record. A request sent before stays.
- A player who had turned *Show me in General* off starts with it off.
- **Marek**, in a group with Tomek, blocks him: neither opens the other's
  record any more.
- A request found on the Rankings page reads *Found you in the padel ranking*.

Every claim is read off the player routes — ``GET /players/{id}/record``,
``POST /friends/requests``, ``PUT /players/me/show-me-to-new-people``,
``GET /home``, ``GET /players/me/notices`` — the outbox delivered as the worker
delivers it.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_player_profile_repository,
)
from app.modules.player_profile.domain.events import RankingVisibilitySet
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    PLAYER_PROFILE_AGGREGATE,
)
from tests.api import players_world as players
from tests.api.rankings_world import a_listed_crowd
from tests.api.test_groups import a_club, a_group, join
from tests.api.test_player_profile_surface import a_photo_held
from tests.demands import friends_world

REQUESTS = "/api/v1/friends/requests"
NOTICES = "/api/v1/players/me/notices"
SWITCH = "/api/v1/players/me/show-me-to-new-people"


async def a_padel_player(client, name: str) -> dict:
    """A player with a profile and a padel rating — somebody with a record."""

    player = await players.a_rated_player(client, name)
    return player | {"headers": players.auth(player["token"])}


@pytest.fixture
async def tomek(client) -> dict:
    """Rated in padel, listed nowhere, in nobody's group."""

    return await a_padel_player(client, "tomek")


@pytest.fixture
async def kuba(client) -> dict:
    """Rated in padel, a stranger to everybody."""

    return await a_padel_player(client, "kuba")


async def record_of(client, reader: dict, subject: dict, sport: str = "PADEL"):
    return await client.get(
        f"/api/v1/players/{subject['id']}/record",
        params={"sport": sport},
        headers=reader["headers"],
    )


async def asks(client, requester: dict, addressee: dict, **body):
    return await client.post(
        REQUESTS,
        json={"player_id": str(addressee["id"]), "made_from": "RECORD"} | body,
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


async def switches(client, player: dict, *, on: bool) -> None:
    """*Show me to new people*, through the You tab's route — and **not
    delivered**: the record and the ask read the profile live."""

    turned = await client.put(SWITCH, json={"on": on}, headers=player["headers"])
    assert turned.status_code == 204, turned.text


def without_trace(body: dict) -> dict:
    return {key: value for key, value in body.items() if key != "trace_id"}


async def the_one_refusal(client, reader: dict) -> dict:
    """What a record nobody can open reads: an id nobody holds."""

    refused = await record_of(client, reader, {"id": uuid4()})
    assert refused.status_code == 404, refused.text
    return without_trace(refused.json())


async def the_unnamed_request_refusal(client, requester: dict) -> dict:
    """What a request nobody can be sent reads: an id nobody holds."""

    refused = await asks(client, requester, {"id": uuid4()})
    assert refused.status_code == 404, refused.text
    return without_trace(refused.json())


async def some_players(client, count: int) -> list[dict]:
    """``count`` players with a committed profile — somebody who may be asked —
    and no rating, in no group."""

    crowd = []
    for n in range(count):
        player_id, token = await players.register(client, f"newcomer{n:02d}")
        await players.commit_profile(client, token)
        crowd.append({"id": player_id, "headers": players.auth(token)})
    return crowd


# --------------------------------------------------------------------------- #
# Any record, any request
# --------------------------------------------------------------------------- #


async def test_a_stranger_opens_a_record_and_sends_a_request(
    client, mailbox, kuba, tomek
):
    opened = await record_of(client, kuba, tomek)
    asked = await asks(client, kuba, tomek)
    await mailbox.drain()
    home = await client.get("/api/v1/home", headers=tomek["headers"])

    assert opened.status_code == 200, opened.text
    record = opened.json()
    assert record["nickname"] == "tomek"
    assert record["skill"]["sport"] == "PADEL"
    assert (record["relation"], record["can_add_friend"]) == ("NONE", True)
    assert asked.status_code == 200, asked.text
    assert asked.json()["relation"] == "SENT"
    [card] = home.json()["friend_requests"]
    assert card["player_id"] == str(kuba["id"])
    # And the record reads it from Kuba's side.
    again = (await record_of(client, kuba, tomek)).json()
    assert (again["relation"], again["can_add_friend"]) == ("SENT", False)


async def test_a_reader_with_no_level_opens_any_record_and_may_ask(client, tomek):
    ola_id, token = await players.register(client, "ola")
    ola = {"id": ola_id, "headers": players.auth(token)}

    opened = await record_of(client, ola, tomek)
    asked = await asks(client, ola, tomek)

    assert opened.status_code == 200, opened.text
    assert opened.json()["can_add_friend"] is True
    assert asked.status_code == 200, asked.text


async def test_every_photo_is_on_a_strangers_record(client, photo_storage, kuba):
    """All of them, in the player's own order — a stranger used to receive the
    first alone (``docs/adr/0204`` §2)."""

    marta_id, token = await players.register(client, "marta")
    photos = [a_photo_held(photo_storage, marta_id, {}) for _ in range(3)]
    await players.commit_profile(
        client, token, photo_ids=[str(photo) for photo in photos]
    )
    marta = {"id": marta_id, "headers": players.auth(token)}

    record = (await record_of(client, kuba, marta)).json()

    assert [photo["photo_id"] for photo in record["photos"]] == [
        str(photo) for photo in photos
    ]
    assert all(photo["photo_url"] for photo in record["photos"])
    assert record["photo_id"] == str(photos[0])
    assert record["photo_url"] == record["photos"][0]["photo_url"]


async def test_a_record_with_no_photo_carries_an_empty_list(client, kuba, tomek):
    record = (await record_of(client, kuba, tomek)).json()

    assert record["photos"] == []
    assert "photo_id" not in record


async def test_there_is_no_daily_limit_the_eleventh_and_the_fiftieth_go_through(
    client, tomek
):
    strangers = await some_players(client, 50)

    sent = [await asks(client, tomek, stranger) for stranger in strangers]

    assert [response.status_code for response in sent] == [200] * 50
    assert sent[10].json()["relation"] == "SENT"
    assert sent[49].json()["relation"] == "SENT"


# --------------------------------------------------------------------------- #
# Show me to new people, off
# --------------------------------------------------------------------------- #


async def test_switched_off_a_stranger_reads_the_one_refusal_on_the_next_tap(
    client, kuba
):
    """Read off the profile, live: nothing to deliver first."""

    bartek = await a_padel_player(client, "bartek")
    assert (await record_of(client, kuba, bartek)).status_code == 200

    await switches(client, bartek, on=False)
    record = await record_of(client, kuba, bartek)
    asked = await asks(client, kuba, bartek)

    assert record.status_code == 404, record.text
    assert without_trace(record.json()) == await the_one_refusal(client, kuba)
    assert asked.status_code == 404, asked.text
    assert asked.json()["code"] == "player_unavailable"
    assert without_trace(asked.json()) == await the_unnamed_request_refusal(
        client, kuba
    )


async def test_switched_off_a_group_mate_still_opens_the_record_and_may_ask(client):
    bartek = await a_padel_player(client, "bartek")
    karol = await a_padel_player(client, "karol")
    await in_one_group(client, karol, bartek)
    await switches(client, bartek, on=False)

    opened = await record_of(client, karol, bartek)
    asked = await asks(client, karol, bartek)

    assert opened.status_code == 200, opened.text
    assert opened.json()["can_add_friend"] is True
    assert asked.status_code == 200, asked.text


async def test_switched_off_a_game_mate_still_opens_the_record_and_may_ask(
    client, session_factory, tomek
):
    """Somebody Tomek played with, in none of his groups: the court keeps it
    open (the mechanics §4.1)."""

    met_id, token = await players.a_player_on_the_log(
        client, session_factory, "witek", mu=3.0
    )
    witek = {"id": met_id, "headers": players.auth(token)}
    await players.a_booked_game(
        session_factory, side_a=(tomek["id"],), side_b=(witek["id"],)
    )
    await switches(client, witek, on=False)

    opened = await record_of(client, tomek, witek)
    asked = await asks(client, tomek, witek)

    assert opened.status_code == 200, opened.text
    assert opened.json()["can_add_friend"] is True
    assert asked.status_code == 200, asked.text


async def test_switched_off_a_friend_still_opens_the_record(
    client, session_factory, kuba
):
    bartek = await a_padel_player(client, "bartek")
    async with session_factory() as session:
        await friends_world.befriends(session, kuba["id"], bartek["id"])
    await switches(client, bartek, on=False)

    opened = await record_of(client, kuba, bartek)

    assert opened.status_code == 200, opened.text
    assert (opened.json()["relation"], opened.json()["can_add_friend"]) == (
        "FRIEND",
        False,
    )


async def test_a_switched_off_players_request_opens_their_record_to_who_they_asked(
    client, mailbox, kuba
):
    """A call made by #791: Bartek, switched off, asks Kuba. Kuba's card opens
    Bartek's record, and *Add friend* there crosses the request — neither is a
    dead end reading *This record isn't available*."""

    bartek = await a_padel_player(client, "bartek")
    await switches(client, bartek, on=False)
    assert (await asks(client, bartek, kuba)).status_code == 200
    await mailbox.drain()

    opened = await record_of(client, kuba, bartek)
    crossed = await asks(client, kuba, bartek)

    assert opened.status_code == 200, opened.text
    assert opened.json()["relation"] == "ASKED_YOU"
    assert crossed.status_code == 200, crossed.text
    assert crossed.json()["relation"] == "FRIEND"


async def test_switched_off_they_still_see_everybody_and_may_ask_anybody(
    client, kuba, tomek
):
    await switches(client, tomek, on=False)

    opened = await record_of(client, tomek, kuba)
    asked = await asks(client, tomek, kuba)

    assert opened.status_code == 200, opened.text
    assert asked.status_code == 200, asked.text


async def test_a_request_sent_before_the_switch_went_off_stays_open(
    client, mailbox, kuba, tomek
):
    """What the switch stops is new (the mechanics §4.3, call 12)."""

    assert (await asks(client, kuba, tomek)).status_code == 200
    await switches(client, tomek, on=False)
    await mailbox.drain()

    [card] = (await client.get("/api/v1/home", headers=tomek["headers"])).json()[
        "friend_requests"
    ]
    accepted = await client.post(
        f"{REQUESTS}/{kuba['id']}/acceptance", headers=tomek["headers"]
    )

    assert card["player_id"] == str(kuba["id"])
    assert accepted.status_code == 200, accepted.text


async def test_turned_back_on_the_record_opens_to_strangers_again(client, kuba):
    bartek = await a_padel_player(client, "bartek")
    await switches(client, bartek, on=False)
    assert (await record_of(client, kuba, bartek)).status_code == 404

    await switches(client, bartek, on=True)

    assert (await record_of(client, kuba, bartek)).status_code == 200
    assert (await asks(client, kuba, bartek)).status_code == 200


async def test_a_player_who_hid_from_general_starts_with_the_switch_off(
    client, session_factory, kuba
):
    """*Show me in General* off, recorded before #791, folds into *Show me to
    new people* off: the profile read says so, and a stranger is refused."""

    bartek = await a_padel_player(client, "bartek")
    async with session_factory() as session:
        store = build_domain_event_store(session)
        profile = await build_player_profile_repository(
            event_store=store, events=build_event_publisher(session)
        ).load(bartek["id"])
        assert profile is not None
        await store.append(
            aggregate_type=PLAYER_PROFILE_AGGREGATE,
            aggregate_id=bartek["id"],
            expected_version=profile.version,
            events=[
                RankingVisibilitySet(
                    player_id=bartek["id"],
                    visibility="HIDDEN",
                    occurred_at=profile.updated_at,
                )
            ],
        )
        await session.commit()

    read = await client.get("/api/v1/players/me/profile", headers=bartek["headers"])

    assert read.json()["show_me_to_new_people"] is False
    assert (await record_of(client, kuba, bartek)).status_code == 404
    assert (await asks(client, kuba, bartek)).status_code == 404


# --------------------------------------------------------------------------- #
# A block closes the record both ways, group-mates included
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("blocker", ["tomek", "marek"])
async def test_a_block_closes_the_record_both_ways_group_mates_included(
    client, tomek, blocker
):
    """Tomek blocks Marek — or Marek blocks Tomek — and they share a group:
    neither opens the other's record, and both read the one refusal."""

    marek = await a_padel_player(client, "marek")
    cast = {"marek": marek, "tomek": tomek}
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


async def test_a_lifted_block_opens_the_record_again(client, kuba, tomek):
    await blocks(client, tomek, kuba)
    assert (await record_of(client, kuba, tomek)).status_code == 404

    lifted = await client.delete(
        f"/api/v1/blocks/{kuba['id']}", headers=tomek["headers"]
    )
    assert lifted.status_code == 204, lifted.text

    assert (await record_of(client, kuba, tomek)).status_code == 200
    assert (await record_of(client, tomek, kuba)).status_code == 200


async def test_a_request_to_somebody_who_blocked_you_is_swallowed(
    client, mailbox, kuba, tomek
):
    """As ADR-0202 §2 decided: *request sent*, and Tomek never sees it."""

    await blocks(client, tomek, kuba)

    asked = await asks(client, kuba, tomek)
    await mailbox.drain()
    home = (await client.get("/api/v1/home", headers=tomek["headers"])).json()

    assert asked.status_code == 200, asked.text
    assert asked.json()["relation"] == "SENT"
    assert home["friend_requests"] == []


# --------------------------------------------------------------------------- #
# A request from the ranking
# --------------------------------------------------------------------------- #


@pytest.fixture
async def listed(client, session_factory, clock) -> list[dict]:
    """Six listed in padel, ``crowd000`` first, none of them *New*."""

    crowd = await a_listed_crowd(client, session_factory, clock, 6)
    for player in crowd:
        player["headers"] = players.auth(player["token"])
    return crowd


async def asks_from_the_ranking(client, requester: dict, addressee: dict, **body):
    return await asks(
        client, requester, addressee, made_from="RANKING", sport="PADEL", **body
    )


async def test_a_strangers_request_from_the_ranking_reads_the_ranking(
    client, mailbox, listed, tomek
):
    piotr = listed[2]

    asked = await asks_from_the_ranking(client, tomek, piotr)
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


async def test_a_request_from_the_ranking_to_a_group_mate_names_the_ranking(
    client, mailbox, listed
):
    piotr, karol = listed[2], listed[5]
    group = await in_one_group(client, karol, piotr)

    asked = await asks_from_the_ranking(client, karol, piotr, group_id=group["id"])
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

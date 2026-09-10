"""The five plan routes, end to end over HTTP — and the thing they sit between.

The whole reachable path in one file: a searcher builds a court, sends it,
everybody accepts, a game exists — and only then is there anything to plan. That
ordering is the point of this file rather than a set-up cost.

Six things are asserted here and nowhere else:

**A plan is born by being used.** There is no route that creates one and none
that destroys one; a game with nothing agreed is simply absent from the list, and
the first slot write is the birth.

**A write of the value already there records nothing and answers 200.** From the
outside that is indistinguishable from a write that changed something — which is
the whole idea — so it is asserted through the room the lines land in.

**The four plan codes reach the conversation**, through the outbox, written by a
context that does not know this one exists.

**Bounded chips the platform offered, never a free instant.** The horizon, the
grid and the moment that has gone, each refused server-side.

**A plan carries no ``read_at``**, so Now has one clock by construction.

**The count and the lock are two facts** (``docs/adr/0155``). Completing the
three slots agrees nothing; locking is an act, it writes its own line, it freezes
nothing, and there is no unlock.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from app.modules.games.domain.windows import PLAN_HORIZON
from app.kernel import instant
from app.modules.plans.domain.slots import (
    PLACE_LENGTH_CAP,
    PLATFORM_ZONE,
    local_day,
)
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _an_arranged_game(client, session_factory, candidate_source, searcher):
    """A game nobody asked for: four seats, all accepted, nothing played yet.

    **The only way to reach one**, which is why every test here pays for it: a
    plan exists for a game, and a game exists because a line-up completed.

    **The outbox is drained before anybody plans anything**, which is what an API
    process does on its own and what this suite has to do by hand. A slot line is
    hung on the room *through its game*, so a room that has not yet been told
    which game it is about has nothing to hang one on — and, unlike the room's
    opening, there is no second delivery to repair it. In production the two are
    ordered by the outbox: ``GamePlanned`` is written in the transaction of the
    last accept and a slot write is a strictly later one. Here they can tie,
    because SQLite's ``CURRENT_TIMESTAMP`` has one-second granularity.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    response = await world.lineup(client, searcher["token"])
    assert response.status_code == 200, response.text
    body = response.json()
    court = [
        {
            "side": seat["side"],
            "player_id": seat.get("player_id", str(searcher["id"])),
        }
        for seat in body["lineup"]["seats"]
    ]
    sent = await client.post(
        "/api/v1/challenges",
        json={"search_id": body["search"]["search_id"], "court": court},
        headers=world.auth(searcher["token"]),
    )
    assert sent.status_code == 201, sent.text
    for person in people.values():
        answered = await client.post(
            f"/api/v1/challenges/{sent.json()['challenge_id']}/accept",
            headers=world.auth(person["token"]),
        )
        assert answered.status_code == 200, answered.text

    await world.deliver_the_outbox(session_factory)
    games = await client.get("/api/v1/games", headers=world.auth(searcher["token"]))
    assert games.status_code == 200, games.text
    (game,) = games.json()["games"]
    return people, game


async def _plans(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/plans", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["plans"]


def _the_day_it_was_arranged(game: dict) -> date:
    """The **local** day this game was arranged on, in the platform's own zone.

    Read the way the clamp reads it and not off the first ten characters of the
    instant: ``last_plannable_day`` converts through the platform's zone before
    taking a date, so between 22:00 and midnight UTC the UTC date is a day behind
    the day the platform is having — and a test that did the arithmetic in UTC
    would be off by one for two hours out of every twenty-four. Through the
    domain's own ``local_day``, so there is one answer to *what day is it*.
    """

    return local_day(instant(datetime.fromisoformat(game["planned_at"])))


def _a_plannable_day(game: dict) -> str:
    """A day inside this game's own horizon, read off the game's own record."""

    return (_the_day_it_was_arranged(game) + timedelta(days=2)).isoformat()


# ---------------------------------------------------------------------------
# Born by being used
# ---------------------------------------------------------------------------


async def test_a_game_with_nothing_agreed_has_no_plan_at_all(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — *no record at birth, and no plan is what a game with
    nothing agreed draws.*

    It is an absence and not a row of three nulls, so a client has one spelling
    for *nothing agreed* and cannot tell an empty plan from a missing one.
    """

    await _an_arranged_game(client, session_factory, candidate_source, searcher)

    assert await _plans(client, searcher["token"]) == []


async def test_the_first_slot_write_is_the_birth_and_answers_the_whole_plan(
    client, session_factory, candidate_source, searcher
):
    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    written = await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(searcher["token"]),
    )

    assert written.status_code == 200, written.text
    assert written.json() == {
        "game_id": game["game_id"],
        "place": "Zabłocie Sport",
        "day": None,
        "hour": None,
        "agreed_point": None,
        "locked_at": None,
    }
    assert await _plans(client, searcher["token"]) == [written.json()]


async def test_there_is_no_route_that_creates_or_destroys_a_plan(app):
    """A plan is born by being used and **is never unmade** — nobody turns up and
    the game ghosts, which is the record this platform keeps instead of a
    cancellation.

    ``lock`` arrived with ``docs/adr/0155`` and ``unlock`` did not: the lock is a
    thing that happened, so it has a route and its undoing has none.
    """

    plan_routes = {
        (route.path, method)
        for route in app.routes
        if getattr(route, "path", "").startswith("/api/v1/plans")
        for method in getattr(route, "methods", ())
    }

    assert {method for _, method in plan_routes} == {"GET", "PUT"}
    assert any(path.endswith("/lock") for path, _ in plan_routes)
    assert not any(
        segment in path
        for path, _ in plan_routes
        for segment in ("unlock", "cancel", "clear")
    )


# ---------------------------------------------------------------------------
# Any member, any slot, any number of times — and the value is the key
# ---------------------------------------------------------------------------


async def test_any_member_may_fill_or_change_any_slot(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — there is no lock and no rate limit; *the line is the
    friction*. Nothing requires the person who fills a slot to be the person who
    proposed it."""

    people, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    day = _a_plannable_day(game)

    first = await client.put(
        f"/api/v1/plans/{game['game_id']}/day",
        json={"day": day},
        headers=world.auth(searcher["token"]),
    )
    moved = await client.put(
        f"/api/v1/plans/{game['game_id']}/day",
        json={"day": (date.fromisoformat(day) + timedelta(days=1)).isoformat()},
        headers=world.auth(people["ana"]["token"]),
    )

    assert first.status_code == 200, first.text
    assert moved.status_code == 200, moved.text
    assert moved.json()["day"] != first.json()["day"]


async def test_writing_the_value_already_there_answers_two_hundred(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0148`` §8 — and it records nothing, which the conversation
    below is what actually proves."""

    people, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    once = await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(searcher["token"]),
    )
    again = await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(people["ana"]["token"]),
    )

    assert once.status_code == again.status_code == 200
    assert once.json() == again.json()


# ---------------------------------------------------------------------------
# The three codes reach the room
# ---------------------------------------------------------------------------


async def test_each_slot_writes_one_line_into_the_conversation(
    client, session_factory, candidate_source, searcher
):
    """``the-words.md`` §23 — three codes, each carrying who and what.

    **Through the outbox, by a context that does not know the room exists.** The
    plan publishes; the conversation subscribes; and the value on the line is the
    one thing membership could never supply.
    """

    people, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    day = _a_plannable_day(game)

    # **Delivered after each write**, because the outbox orders on a transaction
    # start time and this suite runs against SQLite, whose ``CURRENT_TIMESTAMP``
    # has one-second granularity — so three requests inside one second are
    # ordered by a minted uuid. That is a property of the harness rather than of
    # the queue (``docs/adr/0097``), and draining between writes is also what an
    # API process actually does.
    for path, body in (
        ("place", {"place": "Zabłocie Sport"}),
        ("day", {"day": day}),
        ("hour", {"hour": "18:00"}),
    ):
        written = await client.put(
            f"/api/v1/plans/{game['game_id']}/{path}",
            json=body,
            headers=world.auth(searcher["token"]),
        )
        assert written.status_code == 200, written.text
        await world.deliver_the_outbox(session_factory)

    lines = await _system_lines(client, people["ana"]["token"])

    assert [(one["code"], one["values"]["value"]) for one in lines[-3:]] == [
        ("PLACE_RECORDED", "Zabłocie Sport"),
        ("DAY_RECORDED", day),
        ("HOUR_RECORDED", "18:00"),
    ]
    assert {one["actor_id"] for one in lines[-3:]} == {str(searcher["id"])}


async def test_a_repeat_writes_no_second_line(
    client, session_factory, candidate_source, searcher
):
    """The idempotency that matters is the one a person can see. Without it the
    room fills with *Tomek set the place* three times over."""

    people, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    for _ in range(3):
        await client.put(
            f"/api/v1/plans/{game['game_id']}/place",
            json={"place": "Zabłocie Sport"},
            headers=world.auth(searcher["token"]),
        )
    await world.deliver_the_outbox(session_factory)
    lines = await _system_lines(client, people["ana"]["token"])

    assert [one["code"] for one in lines].count("PLACE_RECORDED") == 1


async def _system_lines(client, token: str) -> list[dict]:
    """Every system line in this player's one room, oldest first."""

    rooms = await client.get("/api/v1/conversations", headers=world.auth(token))
    assert rooms.status_code == 200, rooms.text
    (room,) = rooms.json()["conversations"]
    opened = await client.get(
        f"/api/v1/conversations/{room['conversation_id']}",
        headers=world.auth(token),
    )
    assert opened.status_code == 200, opened.text
    return [
        entry
        for entry in opened.json()["entries"]
        if entry["type"] == "system_line"
    ]


# ---------------------------------------------------------------------------
# Bounded chips the platform offered
# ---------------------------------------------------------------------------


async def test_a_day_past_the_horizon_is_refused(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — the clamp, so a plan can never name a day past the
    entry window and a card cannot walk from *Game on* to *Never played* while
    the plan still reads *next Saturday*."""

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    planned = _the_day_it_was_arranged(game)

    refused = await client.put(
        f"/api/v1/plans/{game['game_id']}/day",
        json={"day": (planned + PLAN_HORIZON + timedelta(days=1)).isoformat()},
        headers=world.auth(searcher["token"]),
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "the_day_is_past_the_horizon"


@pytest.mark.parametrize(
    "hour", ["05:30", "23:30", "18:15", "18:00:30"], ids=lambda one: one
)
async def test_an_hour_nobody_offered_is_refused(
    client, session_factory, candidate_source, searcher, hour
):
    """``docs/adr/0145`` §9 — *bounded chips the platform offered, never a free
    instant*. The client's grid is a convention; this is what makes it true."""

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    refused = await client.put(
        f"/api/v1/plans/{game['game_id']}/hour",
        json={"hour": hour},
        headers=world.auth(searcher["token"]),
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "the_hour_is_not_offered"


async def test_a_place_that_says_nothing_or_says_too_much_is_refused(
    client, session_factory, candidate_source, searcher
):
    """**A slot is never emptied**, so a blank value is not a way of clearing
    one; and an over-long note is refused rather than shortened."""

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    empty = await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "   "},
        headers=world.auth(searcher["token"]),
    )
    too_long = await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "x" * (PLACE_LENGTH_CAP + 1)},
        headers=world.auth(searcher["token"]),
    )

    assert empty.json()["code"] == "the_place_is_empty"
    assert too_long.json()["code"] == "the_place_is_too_long"


async def test_a_moment_already_in_the_past_is_refused_in_either_order(
    client, session_factory, candidate_source, searcher
):
    """``the-words.md`` §22.2 — one refusal naming both remedies, because the day
    and the hour are filled in either order and either can be the second."""

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    yesterday = (date.fromisoformat(game["planned_at"][:10]) - timedelta(days=1))

    await client.put(
        f"/api/v1/plans/{game['game_id']}/day",
        json={"day": yesterday.isoformat()},
        headers=world.auth(searcher["token"]),
    )
    refused = await client.put(
        f"/api/v1/plans/{game['game_id']}/hour",
        json={"hour": "18:00"},
        headers=world.auth(searcher["token"]),
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "that_moment_has_already_passed"


# ---------------------------------------------------------------------------
# The gate: the port's one question, and its two answers
# ---------------------------------------------------------------------------


async def test_somebody_who_was_not_on_the_court_is_told_there_is_no_such_plan(
    client, session_factory, candidate_source, searcher
):
    """**One code for two cases** — no such game, and a game that is not yours.

    A 403 would answer *is this id real* about four strangers' evening, which is
    ``challenge_not_found``'s argument verbatim.
    """

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    _, stranger = await world.a_signed_in_candidate(
        client, session_factory, "stranger", mu=searcher["mu"]
    )

    refused = await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(stranger),
    )

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "plan_not_found"
    assert await _plans(client, stranger) == []


async def test_a_plan_read_is_scoped_to_your_own_courts_and_needs_no_refusal(
    client, session_factory, candidate_source, searcher
):
    """The read is gated without a gate: a game the reader was not on the court
    of never becomes a game id it asks about, so there is no id to refuse."""

    people, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(searcher["token"]),
    )

    for token in [searcher["token"]] + [one["token"] for one in people.values()]:
        assert [one["game_id"] for one in await _plans(client, token)] == [
            game["game_id"]
        ]


# ---------------------------------------------------------------------------
# The agreed point, and the clock that is not here
# ---------------------------------------------------------------------------


async def test_the_agreed_point_appears_the_moment_a_day_does(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0145`` §3 — one value, defined whenever the day is, coarsened
    to the start of the following local day when no hour is recorded."""

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    day = _a_plannable_day(game)

    with_a_day = await client.put(
        f"/api/v1/plans/{game['game_id']}/day",
        json={"day": day},
        headers=world.auth(searcher["token"]),
    )
    with_an_hour = await client.put(
        f"/api/v1/plans/{game['game_id']}/hour",
        json={"hour": "18:00"},
        headers=world.auth(searcher["token"]),
    )

    coarse = with_a_day.json()["agreed_point"]
    exact = with_an_hour.json()["agreed_point"]

    assert coarse is not None and exact is not None
    # Coarsened **later, never earlier** — so nobody is asked for a result
    # before they could have played.
    assert exact < coarse
    assert coarse.startswith(
        (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    ) or coarse.startswith(date.fromisoformat(day).isoformat())


async def test_an_hour_with_no_day_names_no_moment(
    client, session_factory, candidate_source, searcher
):
    """An hour alone anchors as little as an empty plan: 18:00 on no day is not a
    moment, and the coarsening rule is about the **day**."""

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    written = await client.put(
        f"/api/v1/plans/{game['game_id']}/hour",
        json={"hour": "18:00"},
        headers=world.auth(searcher["token"]),
    )

    assert written.json()["hour"] == "18:00:00"
    assert written.json()["agreed_point"] is None


async def test_the_plan_list_carries_no_read_at(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0148`` §10 — a plan folds nothing against the clock, so there
    is no instant for it to have been folded against. **Now has one clock by
    construction**, and it is ``GET /games``'."""

    await _an_arranged_game(client, session_factory, candidate_source, searcher)

    response = await client.get(
        "/api/v1/plans", headers=world.auth(searcher["token"])
    )

    assert set(response.json()) == {"plans"}


async def test_one_zone_reads_the_same_for_everybody_in_the_room(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — **one platform zone**, recorded as a locale assumption.

    Per-device zones were refused because they would show two people on one court
    two different hours for one agreement, and there is no club record to hold the
    true one. The falsifier is the first shard whose players are somewhere else.
    """

    people, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    day = _a_plannable_day(game)
    await client.put(
        f"/api/v1/plans/{game['game_id']}/day",
        json={"day": day},
        headers=world.auth(searcher["token"]),
    )
    await client.put(
        f"/api/v1/plans/{game['game_id']}/hour",
        json={"hour": "18:00"},
        headers=world.auth(people["bo"]["token"]),
    )

    seen = {
        (await _plans(client, token))[0]["agreed_point"]
        for token in [searcher["token"]] + [one["token"] for one in people.values()]
    }

    assert len(seen) == 1
    assert str(PLATFORM_ZONE) == "Europe/Warsaw"


# ---------------------------------------------------------------------------
# The freeze
# ---------------------------------------------------------------------------


async def test_saying_you_played_freezes_the_slots(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — **the game leaving its entry window is the only thing
    that freezes the slots**, and it is not a lock: once somebody has said *we
    played*, the plan is history.

    The plan is still readable, because the game screen draws it read-only for
    the whole of a game's life.
    """

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(searcher["token"]),
    )
    played = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    assert played.status_code == 200, played.text

    frozen = await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Hala Sportowa"},
        headers=world.auth(searcher["token"]),
    )

    assert frozen.status_code == 409, frozen.text
    assert frozen.json()["code"] == "plan_is_history"
    assert (await _plans(client, searcher["token"]))[0]["place"] == "Zabłocie Sport"


# ---------------------------------------------------------------------------
# The lock — an act, and not the third slot under another name
# ---------------------------------------------------------------------------


async def _a_complete_plan(client, session_factory, candidate_source, searcher):
    """A game whose three slots are all filled, and nobody has agreed it yet."""

    people, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    for path, body in (
        ("place", {"place": "Zabłocie Sport"}),
        ("day", {"day": _a_plannable_day(game)}),
        ("hour", {"hour": "18:00"}),
    ):
        written = await client.put(
            f"/api/v1/plans/{game['game_id']}/{path}",
            json=body,
            headers=world.auth(searcher["token"]),
        )
        assert written.status_code == 200, written.text
        await world.deliver_the_outbox(session_factory)
    return people, game


async def _lock(client, game_id: str, token: str):
    return await client.put(
        f"/api/v1/plans/{game_id}/lock", headers=world.auth(token)
    )


async def test_a_complete_plan_is_not_a_locked_one(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0155`` — **the count and the lock are two facts.** Filling the
    third slot leaves ``locked_at`` null, because a complete plan is one
    everybody *could* agree and nobody has yet."""

    _, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )

    (plan,) = await _plans(client, searcher["token"])

    assert plan["place"] and plan["day"] and plan["hour"]
    assert plan["locked_at"] is None


async def test_locking_answers_the_plan_carrying_the_moment_it_was_agreed(
    client, session_factory, candidate_source, searcher
):
    people, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )

    locked = await _lock(client, game["game_id"], people["ana"]["token"])

    assert locked.status_code == 200, locked.text
    body = locked.json()
    assert body["locked_at"] is not None
    assert body["place"] == "Zabłocie Sport"
    assert await _plans(client, searcher["token"]) == [body]


async def test_an_incomplete_plan_refuses_the_lock(
    client, session_factory, candidate_source, searcher
):
    """A **conflict** and not a bad request: the body carried nothing at all, so
    there is no field to be wrong — what is wrong is the state of the plan.

    And a refusal rather than a silent `200`, which is the opposite shape from a
    second lock: a no-op here would leave a client believing it had agreed one.
    """

    _, game = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    await client.put(
        f"/api/v1/plans/{game['game_id']}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(searcher["token"]),
    )

    refused = await _lock(client, game["game_id"], searcher["token"])

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "the_plan_is_not_complete"
    assert (await _plans(client, searcher["token"]))[0]["locked_at"] is None


async def test_the_lock_writes_the_one_plan_line_that_carries_no_value(
    client, session_factory, candidate_source, searcher
):
    """``the-words.md`` §23 — ``{name} locked the plan``, filled from membership
    like every other line. The three slots are the value and the room already has
    a line for each of them."""

    people, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )

    locked = await _lock(client, game["game_id"], people["bo"]["token"])
    assert locked.status_code == 200, locked.text
    await world.deliver_the_outbox(session_factory)

    lines = await _system_lines(client, searcher["token"])

    assert lines[-1]["code"] == "PLAN_LOCKED"
    assert lines[-1]["actor_id"] == str(people["bo"]["id"])
    assert lines[-1]["values"] == {}


async def test_locking_an_already_locked_plan_answers_two_hundred_and_says_nothing(
    client, session_factory, candidate_source, searcher
):
    """This repository's idempotency language applied to an **act**: the same act
    twice lands the same state and records nothing. It is not a refusal, and the
    first lock's moment is the one that stands."""

    people, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )

    first = await _lock(client, game["game_id"], searcher["token"])
    await world.deliver_the_outbox(session_factory)
    again = await _lock(client, game["game_id"], people["ana"]["token"])
    await world.deliver_the_outbox(session_factory)

    assert first.status_code == again.status_code == 200
    assert first.json()["locked_at"] == again.json()["locked_at"]
    lines = await _system_lines(client, searcher["token"])
    assert [one["code"] for one in lines].count("PLAN_LOCKED") == 1


async def test_a_locked_plan_is_not_a_frozen_one(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0155`` — locking freezes nothing, and ADR-0145 §5 stands:
    *there is no un-agreeing to fear, only re-agreeing, and any member may do
    that at any time*.

    The plan stays locked and the move writes its own line; **the line trail is
    the friction**, as it already is for every slot change.
    """

    people, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    locked = await _lock(client, game["game_id"], searcher["token"])
    await world.deliver_the_outbox(session_factory)

    moved = await client.put(
        f"/api/v1/plans/{game['game_id']}/hour",
        json={"hour": "19:00"},
        headers=world.auth(people["ana"]["token"]),
    )
    await world.deliver_the_outbox(session_factory)

    assert moved.status_code == 200, moved.text
    assert moved.json()["hour"] == "19:00:00"
    assert moved.json()["locked_at"] == locked.json()["locked_at"]
    lines = await _system_lines(client, searcher["token"])
    assert [one["code"] for one in lines[-2:]] == ["PLAN_LOCKED", "HOUR_RECORDED"]


async def test_somebody_who_was_not_on_the_court_cannot_lock_and_is_told_nothing(
    client, session_factory, candidate_source, searcher
):
    """The gate first, and it is the slot writes' gate exactly — **one code for
    two cases**, because a 403 would answer *is this id real* about four
    strangers' evening."""

    _, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    _, stranger = await world.a_signed_in_candidate(
        client, session_factory, "stranger", mu=searcher["mu"]
    )

    refused = await _lock(client, game["game_id"], stranger)

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "plan_not_found"


async def test_a_held_account_may_not_lock(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0148`` §9 — **a hold refuses a lock exactly as it refuses a
    slot write**, because a lock writes a line other people read. It refuses no
    read: the plan is still there to look at."""

    _, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    world.hold_everybody_planning(client)

    refused = await _lock(client, game["game_id"], searcher["token"])

    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "account_held"
    assert (await _plans(client, searcher["token"]))[0]["locked_at"] is None


async def test_a_game_that_is_history_refuses_the_lock(
    client, session_factory, candidate_source, searcher
):
    """The freeze reaches the lock as it reaches the three slots: once *we
    played* has been said, there is nothing left to agree."""

    _, game = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    played = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    assert played.status_code == 200, played.text

    refused = await _lock(client, game["game_id"], searcher["token"])

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "plan_is_history"


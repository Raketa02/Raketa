"""Leaving a game before it is played — the seat reopens, the game survives, the
same game is re-seated (``docs/adr/0162``) — and leaving a court before it is
whole, after which a court is over when one is left (``docs/adr/0165``).

**The first test is the whole of #411's first rule.** A player on a completed four
leaves it: the challenge reads ``LINE_UP_INCOMPLETE`` with their seat ``LEFT``,
the game the others read draws that seat **empty rather than dropped**, the
leaver's own list no longer holds the game, the room names them on the line that
says they left, and the plan the three of them agreed is untouched.

Everything after it is what the record decided: whose act it is and until when,
that the fill and the acceptance re-seat the **same** game, that nobody may
leave, fill or accept once the agreed moment has passed, that two may leave, and
that singles is the same mechanism with one seat.

**The last section is #424**: a yes taken back before the court is whole, the
ending rule read organiser-blind, and the departure that leaves one player on
a game calling it off in its own transaction.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    UnitOfWorkDep,
    get_clock,
)
from app.bootstrap.composition import (
    build_block_query,
    build_challenge_handles,
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_planned_game_handover,
    build_player_profile_repository,
    build_seatable_game_query,
    build_user_repository,
)
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport, minute_of_day
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.application.leave_game import LeaveGame
from app.modules.challenges.presentation.dependencies import get_leave_game
from app.modules.plans.domain.slots import local_day, moment_of
from tests.api import matchmaking_world as world
from tests.unit.fake_event_store import FrozenClock

#: Enough people in the city for a four, a leaver, a newcomer, and a second one.
A_CITY = (("ana", 0.0), ("bo", 0.05), ("cy", -0.05), ("dee", 0.10), ("eve", -0.10))


@pytest.fixture
def clock(client):
    """The API's clock, stopped where this file starts and moved by hand.

    Handed to the application through the dependency a request resolves, so the
    agreed moment a plan names can be walked past without rewriting anything.
    """

    frozen = FrozenClock(at=datetime.now(timezone.utc))
    world.override(client, get_clock, lambda: frozen)
    return frozen


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    people = {}
    for name, delta in A_CITY:
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token, "name": name}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _search_id(client, token: str) -> str:
    found = await world.search(client, token)
    assert found.status_code == 200, found.text
    return found.json()["search"]["search_id"]


async def _send(client, token: str, search_id: str, court: list[dict]) -> str:
    sent = await client.post(
        "/api/v1/challenges",
        json={"search_id": search_id, "court": court},
        headers=world.auth(token),
    )
    assert sent.status_code == 201, sent.text
    return sent.json()["challenge_id"]


async def _answer(client, token: str, challenge_id: str, act: str):
    return await client.post(
        f"/api/v1/challenges/{challenge_id}/{act}", headers=world.auth(token)
    )


async def _accepted(client, token: str, challenge_id: str) -> dict:
    answered = await _answer(client, token, challenge_id, "accept")
    assert answered.status_code == 200, answered.text
    return answered.json()


async def _leave(client, token: str, challenge_id: str):
    return await client.post(
        f"/api/v1/challenges/{challenge_id}/departure", headers=world.auth(token)
    )


async def _games(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/games", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["games"]


async def _plans(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/plans", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["plans"]


async def _rooms(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/conversations", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["conversations"]


async def _entries(client, token: str, conversation_id: str) -> list[dict]:
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=world.auth(token),
    )
    assert response.status_code == 200, response.text
    return response.json()["entries"]


def _seat_of(court: dict, player_id) -> dict:
    return next(seat for seat in court["seats"] if seat["player_id"] == str(player_id))


async def _game_stream(session_factory, game_id: str) -> list[str]:
    """The game's stream, as event names in order — what the record says
    happened to it, which no read answers."""

    async with session_factory() as session:
        return [
            row.event_type
            for row in (
                await session.execute(
                    select(EventStoreORM)
                    .where(
                        EventStoreORM.aggregate_type == "game",
                        EventStoreORM.aggregate_id == UUID(game_id),
                    )
                    .order_by(EventStoreORM.version)
                )
            ).scalars()
        ]


def _advance(clock, candidate_source, *, to: datetime) -> None:
    """Move the API's clock to ``to``, and the candidate index with it.

    The staleness ladder reads the gap between the clock and the index's
    *caught up at*, so a clock walked two days forward on its own would put
    every ⚡ in this file past the twenty-four-hour refusal — which would be the
    fixture testing the ladder rather than the moment guard. The index is moved
    by the same amount, which is what its own loop would have done.
    """

    world.rewind_the_index(candidate_source, clock.at - to)
    clock.at = to


def _refusal(response) -> dict:
    """The body without the one field that is different on every response —
    ``trace_id`` ties a refusal to a log line and never to a case."""

    body = response.json()
    assert body.pop("trace_id"), "a refusal with no trace is a refusal nobody can chase"
    return body


async def _a_completed_four(client, searcher, people, *names) -> str:
    """A padel four sent to three people who all accept. **A game exists.**"""

    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people[names[0]]["id"])},
        {"side": "B", "player_id": str(people[names[1]]["id"])},
        {"side": "B", "player_id": str(people[names[2]]["id"])},
    ]
    challenge_id = await _send(
        client, searcher["token"], await _search_id(client, searcher["token"]), court
    )
    for name in names:
        standing = (await _accepted(client, people[name]["token"], challenge_id))[
            "standing"
        ]
    assert standing == "ON"
    return challenge_id


async def _the_game(client, token: str, challenge_id: str) -> dict:
    (game,) = [
        one
        for one in await _games(client, token)
        if one["challenge_id"] == challenge_id
    ]
    return game


# ---------------------------------------------------------------------------
# Leaving reopens the seat
# ---------------------------------------------------------------------------


async def test_leaving_a_completed_four_reopens_the_seat_and_the_game_survives(
    client, session_factory, candidate_source, searcher, clock
):
    """**The thing that could not happen.** One of the four leaves.

    The challenge is half built again with their seat ``LEFT``; the game the
    other three read is the same game, with that seat drawn empty; the leaver's
    list no longer holds it; the room names them on the line that says so; and
    the plan is untouched and still theirs to write.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    await world.deliver_the_outbox(session_factory)
    before = await _the_game(client, people["ana"]["token"], challenge_id)
    written = await client.put(
        f"/api/v1/plans/{challenge_id}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(people["ana"]["token"]),
    )
    assert written.status_code == 200, written.text
    # Drained before the act, so the line it writes is the room's last: the
    # outbox orders on a ``created_at`` that is one second granular on SQLite.
    await world.deliver_the_outbox(session_factory)

    left = await _leave(client, people["cy"]["token"], challenge_id)

    assert left.status_code == 200, left.text
    court = left.json()
    assert court["standing"] == "LINE_UP_INCOMPLETE"
    assert _seat_of(court, people["cy"]["id"])["answer"] == "LEFT"
    assert [seat["answer"] for seat in court["seats"]].count("ACCEPTED") == 3

    # The others read the same game, with the seat open rather than gone.
    for who in (searcher, people["ana"], people["bo"]):
        game = await _the_game(client, who["token"], challenge_id)
        assert game["game_id"] == before["game_id"]
        assert game["planned_at"] == before["planned_at"]
        assert game["standing"] == "AWAITING_ENTRY"
        assert len(game["seats"]) == 4, "an open seat is a seat"
        (open_seat,) = [seat for seat in game["seats"] if seat["player_id"] is None]
        assert open_seat["side"] == "B"
        assert open_seat["nickname"] is None
    assert await _games(client, people["cy"]["token"]) == [], (
        "the leaver is not on the court, so the game is not theirs to list"
    )

    # The room names them on the line that says they left.
    await world.deliver_the_outbox(session_factory)
    (room,) = await _rooms(client, people["ana"]["token"])
    assert {member["player_id"] for member in room["members"]} == {
        str(searcher["id"]),
        str(people["ana"]["id"]),
        str(people["bo"]["id"]),
    }
    assert str(people["cy"]["id"]) in {face["player_id"] for face in room["people"]}
    lines = [
        entry
        for entry in await _entries(
            client, people["ana"]["token"], room["conversation_id"]
        )
        if entry["type"] == "system_line"
    ]
    assert (lines[-1]["code"], lines[-1]["values"]) == (
        "SEAT_LEFT",
        {"departure": "LEFT"},
    )
    assert lines[-1]["actor_id"] == str(people["cy"]["id"])
    assert await _rooms(client, people["cy"]["token"]) == []

    # The plan is untouched, and still the remaining three's to write.
    (plan,) = await _plans(client, people["bo"]["token"])
    assert plan["challenge_id"] == challenge_id
    assert plan["anchor"] == before["planned_at"]
    assert plan["place"] == "Zabłocie Sport"
    day = local_day(clock.at) + timedelta(days=2)
    written = await client.put(
        f"/api/v1/plans/{challenge_id}/day",
        json={"day": day.isoformat()},
        headers=world.auth(people["bo"]["token"]),
    )
    assert written.status_code == 200, written.text
    assert await _plans(client, people["cy"]["token"]) == [], (
        "the plan is the challenge's, and the leaver is not on its court"
    )


# ---------------------------------------------------------------------------
# Whose act it is, and until when
# ---------------------------------------------------------------------------


STRAIGHT_SETS = {"sets": [{"a": 6, "b": 3}, {"a": 6, "b": 4}]}


async def _plan(client, token: str, challenge_id: str, slot: str, value: dict) -> None:
    written = await client.put(
        f"/api/v1/plans/{challenge_id}/{slot}", json=value, headers=world.auth(token)
    )
    assert written.status_code == 200, written.text


async def test_a_stranger_and_somebody_without_an_accepted_seat_are_told_the_same(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0162`` §1 — one code for three cases. A stranger, an invitee
    who has not answered, and somebody who has already left are told the same
    thing, byte for byte, because a departure's refusal must not confirm that
    you *were* on this court a moment ago."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people["ana"]["id"])},
        {"side": "B", "player_id": str(people["bo"]["id"])},
        {"side": "B", "player_id": str(people["cy"]["id"])},
    ]
    challenge_id = await _send(
        client, searcher["token"], await _search_id(client, searcher["token"]), court
    )
    await _accepted(client, people["ana"]["token"], challenge_id)

    stranger = await _leave(client, people["dee"]["token"], challenge_id)
    unanswered = await _leave(client, people["bo"]["token"], challenge_id)
    unknown = await _leave(client, people["dee"]["token"], str(uuid4()))

    for refused in (stranger, unanswered):
        assert refused.status_code == 404, refused.text
        assert _refusal(refused) == _refusal(unknown)

    # And somebody who has already left, once the court is a game.
    await _accepted(client, people["bo"]["token"], challenge_id)
    await _accepted(client, people["cy"]["token"], challenge_id)
    first = await _leave(client, people["cy"]["token"], challenge_id)
    assert first.status_code == 200, first.text
    again = await _leave(client, people["cy"]["token"], challenge_id)
    assert again.status_code == 404, again.text
    assert _refusal(again) == _refusal(unknown)


async def test_a_game_that_has_happened_is_history_and_nobody_leaves_it(
    client, session_factory, candidate_source, searcher, clock
):
    """After *we played* the line-up is the record of an evening. The challenge
    is still ``ON``, so the refusal names the game and not the challenge."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    game = await _the_game(client, searcher["token"], challenge_id)
    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": STRAIGHT_SETS},
        headers=world.auth(searcher["token"]),
    )
    assert stated.status_code == 200, stated.text

    left = await _leave(client, people["ana"]["token"], challenge_id)

    assert left.status_code == 409, left.text
    assert left.json()["code"] == "game_is_history"


async def test_a_game_whose_agreed_moment_has_passed_cannot_be_left(
    client, session_factory, candidate_source, searcher, clock
):
    """#411 rule 1 — once the moment has passed the game is *Needs result* and
    leaving would mean nothing, so a no-show cannot vacate a seat to block the
    result. The moment is the plan's: the agreed instant when both a day and an
    hour are recorded."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    day = local_day(clock.at) + timedelta(days=2)
    await _plan(
        client, searcher["token"], challenge_id, "day", {"day": day.isoformat()}
    )
    await _plan(client, searcher["token"], challenge_id, "hour", {"hour": "18:00"})
    (plan,) = await _plans(client, searcher["token"])
    agreed = datetime.fromisoformat(plan["agreed_point"])

    clock.at = agreed - timedelta(minutes=1)
    ahead = await _leave(client, people["ana"]["token"], challenge_id)
    assert ahead.status_code == 200, ahead.text

    clock.at = agreed + timedelta(minutes=1)
    behind = await _leave(client, people["bo"]["token"], challenge_id)
    assert behind.status_code == 409, behind.text
    assert behind.json()["code"] == "game_moment_has_passed"


async def test_a_day_alone_names_the_following_midnight_as_the_moment(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0145`` §3 — the day alone is coarsened *later*, to the start
    of the following local day, so nobody is refused a departure before they
    could have played."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    day = local_day(clock.at) + timedelta(days=1)
    await _plan(
        client, searcher["token"], challenge_id, "day", {"day": day.isoformat()}
    )
    (plan,) = await _plans(client, searcher["token"])
    agreed = datetime.fromisoformat(plan["agreed_point"])
    assert agreed == moment_of(day + timedelta(days=1), minute_of_day(0))

    clock.at = agreed - timedelta(hours=1)
    still_that_day = await _leave(client, people["ana"]["token"], challenge_id)
    assert still_that_day.status_code == 200, still_that_day.text

    clock.at = agreed + timedelta(minutes=1)
    past_midnight = await _leave(client, people["bo"]["token"], challenge_id)
    assert past_midnight.status_code == 409, past_midnight.text
    assert past_midnight.json()["code"] == "game_moment_has_passed"


def _hold_everybody(client) -> None:
    """A hold on every account, wired at ``challenges``' own gate.

    The departure reads the hold through ``CourtSafety`` exactly as the send and
    the fill do — the gate that fails closed — so the stand-in goes in where
    that gate is built, on ``test_challenges.py``'s precedent.
    """

    def factory(
        db: DbSession,
        clock: ClockDep,
        uow: UnitOfWorkDep,
        event_store: DomainEventStoreDep,
        events: EventPublisherDep,
    ) -> LeaveGame:
        return LeaveGame(
            challenges=build_challenge_repository(
                event_store=event_store, events=events
            ),
            handles=build_challenge_handles(db),
            safety=CourtSafety(
                blocks=build_block_query(db),
                holds=world.HoldingEverybody(),
                accounts=build_user_repository(db),
                profiles=build_player_profile_repository(
                    event_store=build_domain_event_store(db),
                    events=build_event_publisher(db),
                ),
            ),
            games=build_seatable_game_query(db),
            uow=uow,
            clock=clock,
            planned_games=build_planned_game_handover(db),
        )

    world.override(client, get_leave_game, factory)


async def test_a_held_account_may_not_leave(
    client, session_factory, candidate_source, searcher, clock
):
    """A departure writes a line into a room other people are in, which is
    reach (``docs/adr/0148`` §9) — refused at the entry point with the code a
    search returns, through the gate that fails closed."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    _hold_everybody(client)

    left = await _leave(client, people["ana"]["token"], challenge_id)

    assert left.status_code == 403, left.text
    assert left.json()["code"] == "account_held"


# ---------------------------------------------------------------------------
# The seat is filled the way a half-built court is, and the same game is re-seated
# ---------------------------------------------------------------------------


async def _fill_from_the_builder(client, token: str, challenge_id: str) -> dict:
    """The ⚡ that names the challenge, then the send of the court it built.

    Answers the challenge as the fill left it. The pool is asserted to leave the
    departed out on the way.
    """

    filling = await world.lineup(client, token, completing_challenge_id=challenge_id)
    assert filling.status_code == 200, filling.text
    lineup = filling.json()["lineup"]
    filled = await client.post(
        f"/api/v1/challenges/{challenge_id}/seats",
        json={
            "search_id": filling.json()["search"]["search_id"],
            "court": [
                {"side": seat["side"], "player_id": seat.get("player_id")}
                for seat in lineup["seats"]
            ],
        },
        headers=world.auth(token),
    )
    assert filled.status_code == 200, filled.text
    return filled.json()


def _newly_invited(court: dict) -> list[str]:
    return [
        seat["player_id"]
        for seat in court["seats"]
        if seat["answer"] is None and seat["player_id"] is not None
    ]


async def test_the_fill_after_a_leave_re_seats_the_same_game(
    client, session_factory, candidate_source, searcher, clock
):
    """#411 rule 3 — the same game, same id, same ``planned_at``, same plan row,
    ``LineUpReseated`` in the stream, and the room's members include the
    newcomer. The one who left is out of this court's pool for good."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    await world.deliver_the_outbox(session_factory)
    before = await _the_game(client, searcher["token"], challenge_id)
    await _plan(client, searcher["token"], challenge_id, "place", {"place": "Zabłocie"})
    await world.deliver_the_outbox(session_factory)
    left = await _leave(client, people["cy"]["token"], challenge_id)
    assert left.status_code == 200, left.text
    await world.deliver_the_outbox(session_factory)

    filling = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )
    assert filling.status_code == 200, filling.text
    seated = {seat.get("player_id") for seat in filling.json()["lineup"]["seats"]}
    assert str(people["cy"]["id"]) not in seated, "the one who left is out of the pool"
    assert {str(people["ana"]["id"]), str(people["bo"]["id"])} <= seated, (
        "the people still on the court are the locked seats"
    )
    filled = await _fill_from_the_builder(client, searcher["token"], challenge_id)
    assert filled["standing"] == "AWAITING_ANSWERS"
    (newcomer_id,) = _newly_invited(filled)
    newcomer = next(one for one in people.values() if str(one["id"]) == newcomer_id)
    await world.deliver_the_outbox(session_factory)

    accepted = await _accepted(client, newcomer["token"], challenge_id)
    assert accepted["standing"] == "ON"
    await world.deliver_the_outbox(session_factory)

    for who in (searcher, people["ana"], people["bo"], newcomer):
        game = await _the_game(client, who["token"], challenge_id)
        assert game["game_id"] == before["game_id"], "the same game, re-seated"
        assert game["planned_at"] == before["planned_at"], (
            "a re-seat does not re-date it"
        )
        assert {seat["player_id"] for seat in game["seats"]} == {
            str(searcher["id"]),
            str(people["ana"]["id"]),
            str(people["bo"]["id"]),
            newcomer_id,
        }
        (plan,) = await _plans(client, who["token"])
        assert plan["challenge_id"] == challenge_id and plan["place"] == "Zabłocie"
        assert plan["anchor"] == before["planned_at"], "a re-seat re-dates nothing"
    assert await _games(client, people["cy"]["token"]) == []
    # The newcomer is on the court now, and the plan is the court's to write.
    day = local_day(clock.at) + timedelta(days=2)
    await _plan(
        client, newcomer["token"], challenge_id, "day", {"day": day.isoformat()}
    )
    (plan,) = await _plans(client, searcher["token"])
    assert plan["day"] == day.isoformat()

    (room,) = await _rooms(client, newcomer["token"])
    assert room["game_id"] == before["game_id"]
    assert newcomer_id in {member["player_id"] for member in room["members"]}
    assert str(people["cy"]["id"]) not in {
        member["player_id"] for member in room["members"]
    }
    codes = [
        entry["code"]
        for entry in await _entries(client, newcomer["token"], room["conversation_id"])
        if entry["type"] == "system_line"
    ]
    assert codes[-3:] == ["SEAT_LEFT", "SEATS_INVITED", "SEAT_ACCEPTED"]

    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
        "games.line_up_reseated",
    ]


async def test_nobody_may_be_seated_into_a_game_whose_moment_has_passed(
    client, session_factory, candidate_source, searcher, clock
):
    """#411 rule 3 — a newcomer accepting into *Sunday* on Monday joins a game
    whose moment is gone. The fill and the acceptance refuse alike."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    day = local_day(clock.at) + timedelta(days=2)
    await _plan(
        client, searcher["token"], challenge_id, "day", {"day": day.isoformat()}
    )
    await _plan(client, searcher["token"], challenge_id, "hour", {"hour": "18:00"})
    (plan,) = await _plans(client, searcher["token"])
    agreed = datetime.fromisoformat(plan["agreed_point"])
    left = await _leave(client, people["cy"]["token"], challenge_id)
    assert left.status_code == 200, left.text

    # A fill sent after the moment is refused whole.
    _advance(clock, candidate_source, to=agreed + timedelta(minutes=1))
    filling = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )
    assert filling.status_code == 200, filling.text
    late_fill = await client.post(
        f"/api/v1/challenges/{challenge_id}/seats",
        json={
            "search_id": filling.json()["search"]["search_id"],
            "court": [
                {"side": seat["side"], "player_id": seat.get("player_id")}
                for seat in filling.json()["lineup"]["seats"]
            ],
        },
        headers=world.auth(searcher["token"]),
    )
    assert late_fill.status_code == 409, late_fill.text
    assert late_fill.json()["code"] == "game_moment_has_passed"

    # A fill sent in time, whose newcomer answers too late, is refused at the yes.
    _advance(clock, candidate_source, to=agreed - timedelta(hours=1))
    filled = await _fill_from_the_builder(client, searcher["token"], challenge_id)
    (newcomer_id,) = _newly_invited(filled)
    newcomer = next(one for one in people.values() if str(one["id"]) == newcomer_id)
    _advance(clock, candidate_source, to=agreed + timedelta(minutes=1))
    late_yes = await _answer(client, newcomer["token"], challenge_id, "accept")
    assert late_yes.status_code == 409, late_yes.text
    assert late_yes.json()["code"] == "game_moment_has_passed"
    assert (await _the_game(client, searcher["token"], challenge_id))["seats"][3][
        "player_id"
    ] is None, "the seat is still open"


# ---------------------------------------------------------------------------
# Two may leave, and singles is the same mechanism with one seat
# ---------------------------------------------------------------------------


async def test_two_departures_leave_two_seats_open_and_a_two_seat_fill_re_seats(
    client, session_factory, candidate_source, searcher, clock
):
    """Two people may leave; two seats may be open (#411 rule 3). The second
    departure is from a court that is already half built, and it is admitted
    because the court has been a game. The fill seats two, and each yes is
    consequential on its own: the first leaves a seat open, the second re-seats."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    before = await _the_game(client, searcher["token"], challenge_id)

    first = await _leave(client, people["bo"]["token"], challenge_id)
    assert first.status_code == 200 and first.json()["standing"] == "LINE_UP_INCOMPLETE"
    second = await _leave(client, people["cy"]["token"], challenge_id)
    assert second.status_code == 200, second.text
    assert second.json()["standing"] == "LINE_UP_INCOMPLETE"
    assert [seat["answer"] for seat in second.json()["seats"]].count("LEFT") == 2
    game = await _the_game(client, searcher["token"], challenge_id)
    assert [seat["player_id"] for seat in game["seats"]].count(None) == 2

    filled = await _fill_from_the_builder(client, searcher["token"], challenge_id)
    newcomers = [
        next(one for one in people.values() if str(one["id"]) == newcomer_id)
        for newcomer_id in _newly_invited(filled)
    ]
    assert len(newcomers) == 2
    first_yes = await _accepted(client, newcomers[0]["token"], challenge_id)
    assert first_yes["standing"] == "AWAITING_ANSWERS"
    game = await _the_game(client, searcher["token"], challenge_id)
    assert [seat["player_id"] for seat in game["seats"]].count(None) == 2, (
        "one yes does not re-seat: the court is re-seated whole, by the last one"
    )
    second_yes = await _accepted(client, newcomers[1]["token"], challenge_id)
    assert second_yes["standing"] == "ON"
    game = await _the_game(client, newcomers[1]["token"], challenge_id)
    assert game["game_id"] == before["game_id"]
    assert None not in [seat["player_id"] for seat in game["seats"]]


async def _a_player(client, name: str) -> dict:
    """One tennis player, through the four routes onboarding is — the shape the
    singles journey uses, because both halves of a two run a search of their
    own here."""

    player_id, token = await world.register(client, name)
    await world.commit_profile(client, token)
    mu = await world.rate(client, token, sport=Sport.TENNIS)
    await world.declare_intent(client, token, sport=Sport.TENNIS)
    return {"id": player_id, "token": token, "mu": mu, "name": name}


async def _a_singles_game(client, session_factory, candidate_source, sender, invitee):
    found = await world.search(client, sender["token"], sport=Sport.TENNIS)
    assert found.status_code == 200, found.text
    body = found.json()
    assert str(invitee["id"]) in {row["player_id"] for row in body["candidates"]}
    challenge_id = await _send(
        client,
        sender["token"],
        body["search"]["search_id"],
        [
            {"side": "A", "player_id": str(sender["id"])},
            {"side": "B", "player_id": str(invitee["id"])},
        ],
    )
    assert (await _accepted(client, invitee["token"], challenge_id))["standing"] == "ON"
    return challenge_id


async def test_in_singles_there_is_no_fill_after_a_departure(
    client, session_factory, candidate_source, clock
):
    """**#411 rule 9 reversed** (``docs/adr/0165`` §3, and its consequence
    *singles lose fill-after-departure*). A two whose opponent leaves is over —
    the game is called off by the departure — so the fill that used to seat a
    substitute meets a game that is history, and so does the remaining
    player's own departure."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await _a_player(client, "nia")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )

    left = await _leave(client, invitee["token"], challenge_id)
    assert left.status_code == 200, left.text
    assert (await _the_game(client, sender["token"], challenge_id))["standing"] == (
        "CALLED_OFF"
    )

    filling = await world.lineup(
        client,
        sender["token"],
        sport=Sport.TENNIS,
        completing_challenge_id=challenge_id,
    )
    assert filling.status_code == 200, filling.text
    filled = await client.post(
        f"/api/v1/challenges/{challenge_id}/seats",
        json={
            "search_id": filling.json()["search"]["search_id"],
            "court": [
                {"side": seat["side"], "player_id": seat.get("player_id")}
                for seat in filling.json()["lineup"]["seats"]
            ],
        },
        headers=world.auth(sender["token"]),
    )
    assert filled.status_code == 409, filled.text
    assert filled.json()["code"] == "game_is_history"
    alone = await _leave(client, sender["token"], challenge_id)
    assert alone.status_code == 409, alone.text
    assert alone.json()["code"] == "game_is_history"


# ---------------------------------------------------------------------------
# What a reopened court holds, refuses and draws
# ---------------------------------------------------------------------------


async def test_the_pair_rule_holds_a_reopened_court_and_releases_it_on_the_re_seat(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0142`` §1 stands: a pair is held while a challenge is being
    arranged. A completed line-up released it; a departure puts the court back
    into arranging, so a send between two people still on it is refused; and
    the re-seat releases it again."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people["ana"]["id"])},
        {"side": "B"},
        {"side": "B"},
    ]

    # **One search, reused**, because the rule under test is the pair rule
    # and not the pool: a fresh search would leave ana out while the pair is
    # held, and the send would refuse on the origin before the rule is reached.
    search_id = await _search_id(client, searcher["token"])

    async def _a_send_between_them():
        return await client.post(
            "/api/v1/challenges",
            json={"search_id": search_id, "court": court},
            headers=world.auth(searcher["token"]),
        )

    released = await _a_send_between_them()
    assert released.status_code == 201, released.text
    second_challenge = released.json()["challenge_id"]

    left = await _leave(client, people["cy"]["token"], challenge_id)
    assert left.status_code == 200, left.text
    # The second send is still awaiting ana's answer and would hold the pair
    # itself; declining it leaves the reopened court as the only thing between
    # searcher and ana.
    declined = await _answer(
        client, people["ana"]["token"], second_challenge, "decline"
    )
    assert declined.status_code == 200, declined.text
    held = await _a_send_between_them()
    assert held.status_code == 409, held.text
    assert held.json()["code"] == "open_challenge_stands"

    filled = await _fill_from_the_builder(client, searcher["token"], challenge_id)
    (newcomer_id,) = _newly_invited(filled)
    newcomer = next(one for one in people.values() if str(one["id"]) == newcomer_id)
    assert (await _accepted(client, newcomer["token"], challenge_id))[
        "standing"
    ] == "ON"
    again = await _a_send_between_them()
    assert again.status_code == 201, again.text


async def test_the_pairing_omits_the_forecast_and_the_stakes_while_a_seat_is_open(
    client, session_factory, candidate_source, exposure_ledger, searcher, clock
):
    """#411 rule 6, and ``docs/adr/0161`` §4's reserved absence: a forecast is a
    claim about a court, and this court is not yet the one that will play. The
    seats that are filled still name their Levels."""

    from tests.api.test_game_pairing import draw_real_pairings

    draw_real_pairings(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    game = await _the_game(client, searcher["token"], challenge_id)
    whole = await client.get(
        f"/api/v1/games/{game['game_id']}/pairing",
        headers=world.auth(searcher["token"]),
    )
    assert whole.status_code == 200, whole.text
    assert "forecast" in whole.json() and "at_stake" in whole.json()

    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200

    reopened = await client.get(
        f"/api/v1/games/{game['game_id']}/pairing",
        headers=world.auth(searcher["token"]),
    )
    assert reopened.status_code == 200, reopened.text
    body = reopened.json()
    assert "forecast" not in body and "split" not in body and "at_stake" not in body
    assert {seat["player_id"] for seat in body["seats"]} == {
        str(searcher["id"]),
        str(people["ana"]["id"]),
        str(people["bo"]["id"]),
    }
    gone = await client.get(
        f"/api/v1/games/{game['game_id']}/pairing",
        headers=world.auth(people["cy"]["token"]),
    )
    assert gone.status_code == 404, gone.text


async def test_a_reopened_court_cannot_record_a_result(
    client, session_factory, candidate_source, searcher, clock
):
    """A score on a court with a seat open is a score with a side nobody can
    price. The court's exit is the withdraw, which calls the game off
    (``docs/adr/0163``, ``tests/api/test_calling_off.py``)."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    game = await _the_game(client, searcher["token"], challenge_id)
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200

    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": STRAIGHT_SETS},
        headers=world.auth(searcher["token"]),
    )
    assert stated.status_code == 409, stated.text
    assert stated.json()["code"] == "the_court_has_an_open_seat"
    assert (await _the_game(client, searcher["token"], challenge_id))["standing"] == (
        "AWAITING_ENTRY"
    )


# ---------------------------------------------------------------------------
# A yes can be taken back, and a court is over when one is left (ADR-0165)
# ---------------------------------------------------------------------------


async def _a_padel_four_sent_to(client, searcher, people, *names) -> str:
    """A padel four sent to three people. **Nobody has answered.**"""

    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people[names[0]]["id"])},
        {"side": "B", "player_id": str(people[names[1]]["id"])},
        {"side": "B", "player_id": str(people[names[2]]["id"])},
    ]
    return await _send(
        client, searcher["token"], await _search_id(client, searcher["token"]), court
    )


async def _declined(client, token: str, challenge_id: str) -> dict:
    answered = await _answer(client, token, challenge_id, "decline")
    assert answered.status_code == 200, answered.text
    return answered.json()


async def _the_room(client, token: str, conversation_id: str):
    return await client.get(
        f"/api/v1/conversations/{conversation_id}", headers=world.auth(token)
    )


async def test_a_yes_can_be_taken_back_before_the_court_is_whole(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0165`` §1 — **the thing 0162 refused.** B and C accepted a
    padel four, D declined, and B leaves before the court is whole.

    The reply reads B's seat ``LEFT`` and the standing ``LINE_UP_INCOMPLETE``
    — the organiser and C are still in, and a seat is open; the room reads
    *B left — that seat is open again* for the people still on it; B is no
    longer a member and is told ``conversation_not_found``; B is out of the
    fill's pool (``docs/adr/0150`` §4, asserted rather than built); and there
    was never a game to tell.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_padel_four_sent_to(
        client, searcher, people, "ana", "bo", "cy"
    )
    await _accepted(client, people["ana"]["token"], challenge_id)
    await _accepted(client, people["bo"]["token"], challenge_id)
    await _declined(client, people["cy"]["token"], challenge_id)
    # Drained before the act, so the line it writes is the room's last.
    await world.deliver_the_outbox(session_factory)
    (room,) = await _rooms(client, people["ana"]["token"])

    left = await _leave(client, people["ana"]["token"], challenge_id)

    assert left.status_code == 200, left.text
    court = left.json()
    assert court["standing"] == "LINE_UP_INCOMPLETE"
    assert _seat_of(court, people["ana"]["id"])["answer"] == "LEFT"
    assert _seat_of(court, people["bo"]["id"])["answer"] == "ACCEPTED"
    assert _seat_of(court, people["cy"]["id"])["answer"] == "DECLINED"
    assert court["ended_at"] is None
    for who in (searcher, people["ana"], people["bo"]):
        assert await _games(client, who["token"]) == [], "there never was a game"

    # The room carries the line; the leaver is out of it.
    await world.deliver_the_outbox(session_factory)
    (still_there,) = await _rooms(client, people["bo"]["token"])
    assert still_there["conversation_id"] == room["conversation_id"]
    assert {member["player_id"] for member in still_there["members"]} == {
        str(searcher["id"]),
        str(people["bo"]["id"]),
    }
    lines = [
        entry
        for entry in await _entries(
            client, people["bo"]["token"], room["conversation_id"]
        )
        if entry["type"] == "system_line"
    ]
    assert (lines[-1]["code"], lines[-1]["values"], lines[-1]["actor_id"]) == (
        "SEAT_LEFT",
        {"departure": "LEFT"},
        str(people["ana"]["id"]),
    )
    assert await _rooms(client, people["ana"]["token"]) == []
    gone = await _the_room(client, people["ana"]["token"], room["conversation_id"])
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"

    # The leaver is out of this court's own pool, and so is the one who said no.
    filling = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )
    assert filling.status_code == 200, filling.text
    seated = {seat.get("player_id") for seat in filling.json()["lineup"]["seats"]}
    assert str(people["ana"]["id"]) not in seated, "the one who left is out of the pool"
    assert str(people["cy"]["id"]) not in seated, "and so is the one who said no"
    assert str(people["bo"]["id"]) in seated, "the person still on the court is locked"


async def test_one_left_with_nobody_deciding_ends_the_court_and_its_room(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0165`` §3 — the organiser alone with one seat still deciding
    is still arranging and the room still reads; the organiser alone once
    everybody else has declined or left is ``DECLINED``, because a departure
    is a no, and the room is gone with it — before any sweep has run."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_padel_four_sent_to(
        client, searcher, people, "ana", "bo", "cy"
    )
    await _accepted(client, people["ana"]["token"], challenge_id)
    await _declined(client, people["bo"]["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    (room,) = await _rooms(client, searcher["token"])

    # ana leaves; cy is still deciding, so nothing has ended.
    left = await _leave(client, people["ana"]["token"], challenge_id)
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "AWAITING_ANSWERS"
    assert left.json()["ended_at"] is None
    await world.deliver_the_outbox(session_factory)
    (still_there,) = await _rooms(client, searcher["token"])
    assert still_there["conversation_id"] == room["conversation_id"]
    assert (
        await _the_room(client, searcher["token"], room["conversation_id"])
    ).status_code == 200

    # cy declines: the organiser is alone with nobody deciding.
    declined = await _declined(client, people["cy"]["token"], challenge_id)
    assert declined["standing"] == "DECLINED", "a departure is a no"
    assert declined["ended_at"] is not None
    assert await _rooms(client, searcher["token"]) == []
    gone = await _the_room(client, searcher["token"], room["conversation_id"])
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"
    detail = await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(searcher["token"])
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["standing"] == "DECLINED"


async def test_the_ending_rule_is_organiser_blind(
    client, session_factory, candidate_source, searcher, clock
):
    """The organiser is a player in the rule: B alone after the organiser left,
    with nobody deciding, is ``DECLINED`` too — a case that could not exist
    while the organiser could not leave."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_padel_four_sent_to(
        client, searcher, people, "ana", "bo", "cy"
    )
    await _accepted(client, people["ana"]["token"], challenge_id)
    await _declined(client, people["bo"]["token"], challenge_id)
    await _declined(client, people["cy"]["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    (room,) = await _rooms(client, people["ana"]["token"])

    left = await _leave(client, searcher["token"], challenge_id)

    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "DECLINED"
    assert left.json()["organiser_id"] == str(searcher["id"]), (
        "a fact about who sent it"
    )
    assert await _rooms(client, people["ana"]["token"]) == []
    gone = await _the_room(client, people["ana"]["token"], room["conversation_id"])
    assert gone.status_code == 404, gone.text


async def test_in_singles_the_opponent_leaving_calls_the_game_off(
    client, session_factory, candidate_source, clock
):
    """``docs/adr/0165`` §3 — **#411 rule 9 reversed.** A two whose opponent
    leaves is over: the game reads ``CALLED_OFF`` on ``GET /games`` with no
    further act, the record shows the seat vacated and then the end, and the
    room is gone. The challenge stands, with nobody to fill the seat for."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )
    await world.deliver_the_outbox(session_factory)
    before = await _the_game(client, sender["token"], challenge_id)
    (room,) = await _rooms(client, sender["token"])
    assert room["game_id"] == before["game_id"]

    left = await _leave(client, invitee["token"], challenge_id)

    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "LINE_UP_INCOMPLETE"
    game = await _the_game(client, sender["token"], challenge_id)
    assert game["game_id"] == before["game_id"]
    assert game["standing"] == "CALLED_OFF"
    assert game["called_off_at"] is not None
    assert [seat["player_id"] for seat in game["seats"]] == [str(sender["id"]), None]
    assert await _games(client, invitee["token"]) == []
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
        "games.called_off",
    ]

    await world.deliver_the_outbox(session_factory)
    for who in (sender, invitee):
        assert await _rooms(client, who["token"]) == []
    gone = await _the_room(client, sender["token"], room["conversation_id"])
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"


async def test_in_singles_the_organiser_leaving_calls_the_game_off_too(
    client, session_factory, candidate_source, clock
):
    """Organiser-blind on a game as well: the opponent alone is one player with
    nobody deciding, and the game is called off by the organiser's departure."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )

    left = await _leave(client, sender["token"], challenge_id)

    assert left.status_code == 200, left.text
    game = await _the_game(client, invitee["token"], challenge_id)
    assert game["standing"] == "CALLED_OFF"
    assert [seat["player_id"] for seat in game["seats"]] == [None, str(invitee["id"])]
    assert await _games(client, sender["token"]) == []


async def test_in_doubles_the_third_departure_calls_it_off_and_the_first_two_open_seats(
    client, session_factory, candidate_source, searcher, clock
):
    """Doubles fill down to two on the court; the departure that leaves one is
    the one that ends it. The first two only open seats — the game is still
    awaiting its entry with a seat to fill — and the third calls it off."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    before = await _the_game(client, searcher["token"], challenge_id)

    for name, open_seats in (("cy", 1), ("bo", 2)):
        left = await _leave(client, people[name]["token"], challenge_id)
        assert left.status_code == 200, left.text
        game = await _the_game(client, searcher["token"], challenge_id)
        assert game["standing"] == "AWAITING_ENTRY"
        assert [seat["player_id"] for seat in game["seats"]].count(None) == open_seats

    third = await _leave(client, people["ana"]["token"], challenge_id)

    assert third.status_code == 200, third.text
    assert third.json()["standing"] == "LINE_UP_INCOMPLETE"
    game = await _the_game(client, searcher["token"], challenge_id)
    assert game["game_id"] == before["game_id"]
    assert game["standing"] == "CALLED_OFF"
    assert [seat["player_id"] for seat in game["seats"]].count(None) == 3
    for name in ("ana", "bo", "cy"):
        assert await _games(client, people[name]["token"]) == []


async def test_the_moment_guard_is_asked_only_where_there_is_a_game(
    client, session_factory, candidate_source, searcher, clock
):
    """The moment guard is asked exactly where it was (``docs/adr/0162`` §4): on
    a court that has been a game. A half-built court can carry a plan with a
    day and an hour (``docs/adr/0164``), and has no moment to guard — the
    departure is admitted after it as before it."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    day = local_day(clock.at) + timedelta(days=2)

    game = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    await _plan(client, searcher["token"], game, "day", {"day": day.isoformat()})
    await _plan(client, searcher["token"], game, "hour", {"hour": "18:00"})
    (plan,) = [
        one
        for one in await _plans(client, searcher["token"])
        if one["challenge_id"] == game
    ]
    agreed = datetime.fromisoformat(plan["agreed_point"])

    half_built = await _a_padel_four_sent_to(
        client, searcher, people, "dee", "eve", "ana"
    )
    await _accepted(client, people["dee"]["token"], half_built)
    await _plan(
        client, people["dee"]["token"], half_built, "day", {"day": day.isoformat()}
    )
    await _plan(client, people["dee"]["token"], half_built, "hour", {"hour": "18:00"})

    _advance(clock, candidate_source, to=agreed + timedelta(minutes=1))
    on_the_game = await _leave(client, people["bo"]["token"], game)
    assert on_the_game.status_code == 409, on_the_game.text
    assert on_the_game.json()["code"] == "game_moment_has_passed"

    on_the_court = await _leave(client, people["dee"]["token"], half_built)
    assert on_the_court.status_code == 200, on_the_court.text
    assert _seat_of(on_the_court.json(), people["dee"]["id"])["answer"] == "LEFT"

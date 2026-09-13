"""Calling a game off — the withdraw grown to a reopened court, and *Called off*
the fourth end (``docs/adr/0163``).

**The first test is the whole of #411's fourth rule.** The organiser withdraws a
four somebody left: the challenge reads ``WITHDRAWN``, the game the others read
is ``CALLED_OFF`` with the instant on it and its window gone, the room is
destroyed, the plan and the pairing are history, and a score is refused.

Everything after it is what the record decided: whose act it is once the
organiser has left; that a full court has no such exit; that a court that never
became a game withdraws exactly as before, with no game to tell; that the pair is
released; that in singles the departure itself calls the game off and the
withdraw that follows steps over that end (``docs/adr/0165`` §3); and that a
court whose window has already closed is withdrawn with the ghost left standing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.api.dependencies import get_clock
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.plans.domain.slots import local_day
from tests.api import matchmaking_world as world
from tests.api.test_departure import (
    STRAIGHT_SETS,
    _a_city,
    _a_completed_four,
    _a_player,
    _a_singles_game,
    _accepted,
    _advance,
    _game_stream,
    _games,
    _leave,
    _plans,
    _refusal,
    _rooms,
    _search_id,
    _send,
    _the_game,
)
from tests.unit.fake_event_store import FrozenClock


@pytest.fixture
def clock(client):
    """The API's clock, stopped where this file starts and moved by hand.

    ``test_departure.py``'s fixture, spelled again here on this directory's
    convention — every module here declares its own ``searcher`` and, where it
    moves time, its own ``clock`` — rather than imported: ruff reads an imported
    fixture used as a parameter as a redefinition of the import.
    """

    frozen = FrozenClock(at=datetime.now(timezone.utc))
    world.override(client, get_clock, lambda: frozen)
    return frozen


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _withdraw(client, token: str, challenge_id: str):
    return await client.post(
        f"/api/v1/challenges/{challenge_id}/withdrawal", headers=world.auth(token)
    )


# ---------------------------------------------------------------------------
# The organiser calls off a reopened four
# ---------------------------------------------------------------------------


async def test_the_organiser_calls_off_a_reopened_four_and_that_is_the_games_end(
    client, session_factory, candidate_source, searcher, clock
):
    """**The thing 0162 refused for a day.** One of the four leaves, and the
    organiser calls the game off.

    The challenge is ``WITHDRAWN`` with the seats as they were; every remaining
    member reads the same game as ``CALLED_OFF`` with the act's instant on it and
    no entry window; the leaver still does not hold it; the room is destroyed in
    the act, though it already held its game; the plan and the pairing are
    history; and a score is refused with the end it met.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    await world.deliver_the_outbox(session_factory)
    before = await _the_game(client, searcher["token"], challenge_id)
    (room,) = await _rooms(client, people["ana"]["token"])
    assert room["game_id"] == before["game_id"], "the room already holds its game"
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    placed = await client.put(
        f"/api/v1/plans/{challenge_id}/place",
        json={"place": "Zabłocie Sport"},
        headers=world.auth(people["ana"]["token"]),
    )
    assert placed.status_code == 200, placed.text
    await world.deliver_the_outbox(session_factory)

    withdrawn = await _withdraw(client, searcher["token"], challenge_id)

    assert withdrawn.status_code == 200, withdrawn.text
    court = withdrawn.json()
    assert court["standing"] == "WITHDRAWN"
    assert [seat["answer"] for seat in court["seats"]].count("ACCEPTED") == 3
    assert [seat["answer"] for seat in court["seats"]].count("LEFT") == 1

    for who in (searcher, people["ana"], people["bo"]):
        game = await _the_game(client, who["token"], challenge_id)
        assert game["game_id"] == before["game_id"]
        assert game["standing"] == "CALLED_OFF"
        assert game["called_off_at"] is not None
        assert game["entry_closes_at"] is None, "the window no longer matters"
        assert game["played_at"] is None and game["score"] is None
        assert [seat["player_id"] for seat in game["seats"]].count(None) == 1, (
            "the open seat is still on the record"
        )
    assert await _games(client, people["cy"]["token"]) == []
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
        "games.called_off",
    ]

    # The room is destroyed in the act, exactly as any withdrawal destroys it.
    await world.deliver_the_outbox(session_factory)
    for who in (searcher, people["ana"], people["bo"], people["cy"]):
        assert await _rooms(client, who["token"]) == []
    gone = await client.get(
        f"/api/v1/conversations/{room['conversation_id']}",
        headers=world.auth(people["ana"]["token"]),
    )
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"

    # The plan and the pairing are history.
    day = local_day(clock.at) + timedelta(days=2)
    frozen = await client.put(
        f"/api/v1/plans/{challenge_id}/day",
        json={"day": day.isoformat()},
        headers=world.auth(people["bo"]["token"]),
    )
    assert frozen.status_code == 409, frozen.text
    assert frozen.json()["code"] == "plan_is_history"
    (plan,) = await _plans(client, people["bo"]["token"])
    assert plan["challenge_id"] == challenge_id, "and still drawn beside the game"
    assert plan["place"] == "Zabłocie Sport"
    pairing = await client.get(
        f"/api/v1/games/{before['game_id']}/pairing",
        headers=world.auth(searcher["token"]),
    )
    assert pairing.status_code == 409, pairing.text
    assert pairing.json()["code"] == "pairing_is_history"

    # And nothing on the game moves.
    stated = await client.post(
        f"/api/v1/games/{before['game_id']}/result",
        json={"score": STRAIGHT_SETS},
        headers=world.auth(searcher["token"]),
    )
    assert stated.status_code == 409, stated.text
    assert stated.json()["code"] == "the_game_was_called_off"
    agreed = await client.post(
        f"/api/v1/games/{before['game_id']}/result/acceptance",
        headers=world.auth(people["bo"]["token"]),
    )
    assert agreed.status_code == 409, agreed.text
    assert agreed.json()["code"] == "the_result_is_settled"
    left = await _leave(client, people["ana"]["token"], challenge_id)
    assert left.status_code == 409, left.text
    assert left.json()["code"] == "challenge_is_over", (
        "the standing is asked before the game, so an ended court is refused as one"
    )
    again = await _withdraw(client, searcher["token"], challenge_id)
    assert again.status_code == 409, again.text
    assert again.json()["code"] == "not_a_half_built_line_up"


# ---------------------------------------------------------------------------
# Whose act it is
# ---------------------------------------------------------------------------


async def test_once_the_organiser_has_left_any_remaining_player_may_call_it_off(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0163`` §1 — the organiser's fallback, and the refusal that
    stands where the organiser is still in: asked first, one code."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])

    # The organiser is still in: a member is told the act is not theirs.
    organiser_in = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    assert (
        await _leave(client, people["cy"]["token"], organiser_in)
    ).status_code == 200
    refused = await _withdraw(client, people["ana"]["token"], organiser_in)
    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "withdraw_is_the_organisers"
    assert (await _the_game(client, people["ana"]["token"], organiser_in))[
        "standing"
    ] == "AWAITING_ENTRY"
    # Called off by the organiser, so the pair is released for the next court —
    # a reopened court holds it, and a fresh search would leave ana and bo out.
    assert (await _withdraw(client, searcher["token"], organiser_in)).status_code == 200

    # The organiser has left: a remaining player holds the exit — and the one
    # who left does not.
    organiser_out = await _a_completed_four(
        client, searcher, people, "ana", "bo", "dee"
    )
    assert (await _leave(client, searcher["token"], organiser_out)).status_code == 200
    not_remaining = await _withdraw(client, searcher["token"], organiser_out)
    assert not_remaining.status_code == 403, not_remaining.text
    assert not_remaining.json()["code"] == "withdraw_is_the_organisers"
    called_off = await _withdraw(client, people["bo"]["token"], organiser_out)
    assert called_off.status_code == 200, called_off.text
    assert called_off.json()["standing"] == "WITHDRAWN"
    assert called_off.json()["organiser_id"] == str(searcher["id"]), (
        "the organiser is a fact about who sent it, and it does not move"
    )
    for who in (people["ana"], people["bo"], people["dee"]):
        assert (await _the_game(client, who["token"], organiser_out))["standing"] == (
            "CALLED_OFF"
        )


async def test_a_full_court_has_no_such_exit(
    client, session_factory, candidate_source, searcher, clock
):
    """#411 rule 4 — only while a seat is open. A full court that will not play
    lets its window lapse into *Never played*, as today."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")

    refused = await _withdraw(client, searcher["token"], challenge_id)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "not_a_half_built_line_up"
    assert (await _the_game(client, searcher["token"], challenge_id))["standing"] == (
        "AWAITING_ENTRY"
    )


async def test_a_court_that_never_became_a_game_withdraws_exactly_as_before(
    client, session_factory, candidate_source, searcher, clock
):
    """The regression: no game, no hand-over, the organiser's alone."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people["ana"]["id"])},
        {"side": "B", "player_id": str(people["bo"]["id"])},
        {"side": "B"},
    ]
    challenge_id = await _send(
        client, searcher["token"], await _search_id(client, searcher["token"]), court
    )
    await _accepted(client, people["ana"]["token"], challenge_id)
    await _accepted(client, people["bo"]["token"], challenge_id)

    not_theirs = await _withdraw(client, people["ana"]["token"], challenge_id)
    assert not_theirs.status_code == 403, not_theirs.text
    assert not_theirs.json()["code"] == "withdraw_is_the_organisers"

    withdrawn = await _withdraw(client, searcher["token"], challenge_id)
    assert withdrawn.status_code == 200, withdrawn.text
    assert withdrawn.json()["standing"] == "WITHDRAWN"
    for who in (searcher, people["ana"], people["bo"]):
        assert await _games(client, who["token"]) == [], "there never was a game"


# ---------------------------------------------------------------------------
# The pair, and singles
# ---------------------------------------------------------------------------


async def test_the_pair_may_challenge_each_other_again_afterwards(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0142`` §1 releases on ``WITHDRAWN`` and ``docs/adr/0152`` §4 on
    a settled game; a called-off game is both. Held while the court was
    reopened, released by the call-off."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people["ana"]["id"])},
        {"side": "B"},
        {"side": "B"},
    ]
    search_id = await _search_id(client, searcher["token"])

    async def _a_send_between_them():
        return await client.post(
            "/api/v1/challenges",
            json={"search_id": search_id, "court": court},
            headers=world.auth(searcher["token"]),
        )

    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    held = await _a_send_between_them()
    assert held.status_code == 409, held.text
    assert held.json()["code"] == "open_challenge_stands"

    assert (await _withdraw(client, searcher["token"], challenge_id)).status_code == 200

    released = await _a_send_between_them()
    assert released.status_code == 201, released.text


async def test_in_singles_the_withdraw_after_the_departures_call_off_steps_over_it(
    client, session_factory, candidate_source, clock
):
    """**#411 rule 9 reversed** (``docs/adr/0165`` §3) — a two whose opponent
    leaves is over by the departure, with no act from the remaining player.
    The challenge still stands ``LINE_UP_INCOMPLETE`` with nobody to fill the
    seat for, and its exit is still the withdraw: admitted, ending the
    challenge, with the game keeping the end the departure gave it — no second
    ``GameCalledOff`` — exactly as a ghost is stepped over."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )
    before = await _the_game(client, sender["token"], challenge_id)
    left = await _leave(client, invitee["token"], challenge_id)
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "LINE_UP_INCOMPLETE"
    called_off = await _the_game(client, sender["token"], challenge_id)
    assert called_off["standing"] == "CALLED_OFF"
    assert [seat["player_id"] for seat in called_off["seats"]] == [
        str(sender["id"]),
        None,
    ]
    assert await _games(client, invitee["token"]) == []

    withdrawn = await _withdraw(client, sender["token"], challenge_id)

    assert withdrawn.status_code == 200, withdrawn.text
    assert withdrawn.json()["standing"] == "WITHDRAWN"
    after = await _the_game(client, sender["token"], challenge_id)
    assert after["game_id"] == before["game_id"]
    assert after["standing"] == "CALLED_OFF"
    assert after["called_off_at"] == called_off["called_off_at"], "the first end stands"
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
        "games.called_off",
    ]


async def test_in_singles_the_opponent_may_withdraw_once_the_organiser_left(
    client, session_factory, candidate_source, clock
):
    """Organiser-blind on a game: the organiser's departure leaves the opponent
    alone and calls the game off. The opponent holds the exit by the fallback
    (``docs/adr/0163`` §1) and the withdraw ends the challenge, the game
    keeping its end."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )
    assert (await _leave(client, sender["token"], challenge_id)).status_code == 200
    assert (await _the_game(client, invitee["token"], challenge_id))["standing"] == (
        "CALLED_OFF"
    )

    withdrawn = await _withdraw(client, invitee["token"], challenge_id)

    assert withdrawn.status_code == 200, withdrawn.text
    assert withdrawn.json()["standing"] == "WITHDRAWN"
    assert (await _the_game(client, invitee["token"], challenge_id))["standing"] == (
        "CALLED_OFF"
    )


# ---------------------------------------------------------------------------
# A court whose game has already ended by its clock
# ---------------------------------------------------------------------------


async def test_a_court_whose_window_has_closed_is_withdrawn_and_the_ghost_stands(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0163`` §6 — the one leniency. Nobody filled the seat and the
    window closed: the game is a ghost, charged already, and the challenge
    still holds its pair. The withdraw is the court's only exit, so it is
    admitted; the game is not un-ghosted, and the pair is released."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    before = await _the_game(client, searcher["token"], challenge_id)
    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people["ana"]["id"])},
        {"side": "B"},
        {"side": "B"},
    ]
    # **One search, made while the pair is released and reused**, because a
    # fresh one would leave ana out while the reopened court holds the pair.
    search_id = await _search_id(client, searcher["token"])
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200

    _advance(
        clock,
        candidate_source,
        to=datetime.fromisoformat(before["planned_at"])
        + PLAN_HORIZON
        + ENTRY_GRACE
        + timedelta(hours=1),
    )
    ghost = await _the_game(client, searcher["token"], challenge_id)
    assert ghost["standing"] == "NEVER_PLAYED"
    held = await client.post(
        "/api/v1/challenges",
        json={"search_id": search_id, "court": court},
        headers=world.auth(searcher["token"]),
    )
    assert held.status_code == 409 and held.json()["code"] == "open_challenge_stands"

    withdrawn = await _withdraw(client, searcher["token"], challenge_id)

    assert withdrawn.status_code == 200, withdrawn.text
    assert withdrawn.json()["standing"] == "WITHDRAWN"
    after = await _the_game(client, searcher["token"], challenge_id)
    assert after["standing"] == "NEVER_PLAYED", "a ghost is not un-ghosted"
    assert after["called_off_at"] is None
    assert after["entry_closes_at"] is not None
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
    ]
    detail = await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(people["ana"]["token"])
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["standing"] == "WITHDRAWN"
    released = await client.post(
        "/api/v1/challenges",
        json={"search_id": search_id, "court": court},
        headers=world.auth(searcher["token"]),
    )
    assert released.status_code == 201, released.text


async def test_the_refusals_name_nobody_and_carry_nothing(
    client, session_factory, candidate_source, searcher, clock
):
    """Every refusal on this path states the class of problem and the client
    re-reads what it already owns."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200

    refused = await _withdraw(client, people["ana"]["token"], challenge_id)

    assert refused.status_code == 403
    assert set(_refusal(refused)) == {"code", "message"}
    assert str(searcher["id"]) not in refused.text

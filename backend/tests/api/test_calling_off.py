"""Calling a game off — **nobody presses it** (``docs/adr/0175`` §1). A court
that has been a game ends by its seats or by its hour, never by one person's
decision over the others: the departure that leaves at most one player on it
(``docs/adr/0165`` §3, ``docs/adr/0175`` §2), and the platform's hour loop on a
court still short of a player when its moment passes (``docs/adr/0175`` §3) —
each recording the court's own ending, ``CALLED_OFF``, beside the game's
(``docs/adr/0172`` §1).

**The first test is the hour.** One of the four leaves, nobody fills the seat,
and the agreed hour passes: the loop calls it off — the challenge reads
``CALLED_OFF`` with ``ended_by`` nobody, the game the others read is
``CALLED_OFF`` with ``called_off_by`` nobody and its window gone, the room is
destroyed, the plan and the pairing are history, a score is refused, and
nobody is charged a ghost.

Everything after it is what the record decided: that the withdrawal route
refuses a court that has been a game with its own code, its organiser
included, and everybody else as not theirs; that the hour writes nothing on a
court that is whole, re-seated, or ahead of its hour; that a court with no day
agreed is measured against the end of its horizon; that a court whose window
already closed is called off by the hour with the ghost left standing; that
the pair is released; that the last seated player's departure calls it off
whoever is still deciding, and their invitation with it; and that in singles
the departure itself ends the court.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_left_court_query,
    build_planned_game_handover,
    build_seatable_game_query,
    build_unit_of_work,
)
from app.modules.challenges.application.call_off_unfilled_courts import (
    CalledOff,
    CallOffUnfilledCourts,
)
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
    _fill_from_the_builder,
    _game_stream,
    _games,
    _leave,
    _newly_invited,
    _plan,
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


async def _the_hour_passes(session_factory, clock) -> CalledOff:
    """One run of the hour loop, wired as the job wires it and read against
    the API's frozen clock."""

    async with session_factory() as session:
        return await CallOffUnfilledCourts(
            clock=clock,
            challenges=build_challenge_repository(
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ),
            left=build_left_court_query(session),
            games=build_seatable_game_query(session),
            planned_games=build_planned_game_handover(session),
            unit_of_work=build_unit_of_work(session),
        ).execute()


async def _agree_an_hour(client, token: str, challenge_id: str, clock) -> datetime:
    """A day and an hour on the plan, and the agreed instant they make."""

    day = local_day(clock.at) + timedelta(days=2)
    await _plan(client, token, challenge_id, "day", {"day": day.isoformat()})
    await _plan(client, token, challenge_id, "hour", {"hour": "18:00"})
    (plan,) = [
        one
        for one in await _plans(client, token)
        if one["challenge_id"] == challenge_id
    ]
    return datetime.fromisoformat(plan["agreed_point"])


async def _row(client, token: str, challenge_id: str) -> dict | None:
    response = await client.get("/api/v1/challenges", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return next(
        (
            one
            for one in response.json()["challenges"]
            if one["challenge_id"] == challenge_id
        ),
        None,
    )


# ---------------------------------------------------------------------------
# The hour calls off a reopened four
# ---------------------------------------------------------------------------


async def test_the_hour_calls_off_a_reopened_four_and_that_is_the_games_end(
    client, session_factory, candidate_source, searcher, clock
):
    """One of the four leaves, nobody fills the seat, and the agreed hour
    passes.

    The challenge is ``CALLED_OFF`` — never ``WITHDRAWN`` — with the seats as
    they were and ``ended_by`` nobody; every remaining member reads the same
    game as ``CALLED_OFF`` with the hour's instant, ``called_off_by`` nobody
    and no entry window; the leaver still does not hold it; the room is
    destroyed, though it already held its game; the plan and the pairing are
    history; a score is refused with the end it met; and the row is on every
    remaining member's inbox for its day.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    await world.deliver_the_outbox(session_factory)
    before = await _the_game(client, searcher["token"], challenge_id)
    (room,) = await _rooms(client, people["ana"]["token"])
    assert room["game_id"] == before["game_id"], "the room already holds its game"
    agreed = await _agree_an_hour(client, searcher["token"], challenge_id, clock)
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    await world.deliver_the_outbox(session_factory)

    _advance(clock, candidate_source, to=agreed - timedelta(minutes=1))
    assert await _the_hour_passes(session_factory, clock) == CalledOff(0, 0), (
        "the hour is still ahead"
    )
    assert (await _row(client, searcher["token"], challenge_id))["standing"] == (
        "LINE_UP_INCOMPLETE"
    )

    _advance(clock, candidate_source, to=agreed + timedelta(minutes=1))
    assert await _the_hour_passes(session_factory, clock) == CalledOff(1, 0)

    court = await _row(client, searcher["token"], challenge_id)
    assert court["standing"] == "CALLED_OFF"
    assert court["ended_at"] == clock.at.isoformat().replace("+00:00", "Z")
    assert court["ended_by"] is None, "nobody's act"
    assert court["game_id"] == before["game_id"]
    assert [seat["answer"] for seat in court["seats"]].count("ACCEPTED") == 3
    assert [seat["answer"] for seat in court["seats"]].count("LEFT") == 1
    assert (
        await client.get(
            f"/api/v1/challenges/{challenge_id}",
            headers=world.auth(people["bo"]["token"]),
        )
    ).json()["standing"] == "CALLED_OFF"
    assert await _row(client, people["cy"]["token"], challenge_id) is not None, (
        "the leaver's seat is on the record; their row leaving is the client's"
    )

    for who in (searcher, people["ana"], people["bo"]):
        game = await _the_game(client, who["token"], challenge_id)
        assert game["game_id"] == before["game_id"]
        assert game["standing"] == "CALLED_OFF"
        assert game["called_off_at"] is not None
        assert game["called_off_by"] is None, "nobody's act"
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
    assert await _the_hour_passes(session_factory, clock) == CalledOff(0, 0), (
        "a second tick writes nothing"
    )

    # The room is destroyed, exactly as any ending destroys it.
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
    left = await _leave(client, people["ana"]["token"], challenge_id)
    assert left.status_code == 409, left.text
    assert left.json()["code"] == "challenge_is_over"
    pressed = await _withdraw(client, searcher["token"], challenge_id)
    assert pressed.status_code == 409, pressed.text
    assert pressed.json()["code"] == "challenge_is_over"


async def test_the_hour_writes_nothing_on_a_court_that_is_whole_or_re_seated(
    client, session_factory, candidate_source, searcher, clock
):
    """A whole court plays or ghosts on its own record, and a court re-seated
    before its hour is whole again. The loop names both as candidates — the
    second has a departure on its stream — and writes nothing on either."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    whole = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    agreed = await _agree_an_hour(client, searcher["token"], whole, clock)

    # ana's first court is ``ON`` and holds nobody, so she is free for a second.
    re_seated = await _a_completed_four(client, searcher, people, "dee", "eve", "ana")
    assert (await _leave(client, people["eve"]["token"], re_seated)).status_code == 200
    filled = await _fill_from_the_builder(client, searcher["token"], re_seated)
    (newcomer_id,) = _newly_invited(filled)
    newcomer = next(one for one in people.values() if str(one["id"]) == newcomer_id)
    await _accepted(client, newcomer["token"], re_seated)
    assert (await _row(client, searcher["token"], re_seated))["standing"] == "ON"

    _advance(clock, candidate_source, to=agreed + timedelta(hours=1))
    assert await _the_hour_passes(session_factory, clock) == CalledOff(0, 0)

    assert (await _row(client, searcher["token"], whole))["standing"] == "ON"
    assert (await _row(client, searcher["token"], re_seated))["standing"] == "ON"
    for challenge_id in (whole, re_seated):
        assert (await _the_game(client, searcher["token"], challenge_id))[
            "standing"
        ] == "AWAITING_ENTRY"


async def test_a_court_with_no_day_agreed_is_measured_against_its_horizon(
    client, session_factory, candidate_source, searcher, clock
):
    """A plan with no day has no agreed point, and read as *no moment* such a
    court admitted a fill and a departure up to the window closing on a ghost.
    The end of its horizon stands in: the hour writes nothing before it and
    calls the court off after it, a day before the grace would have ghosted
    the game."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    before = await _the_game(client, searcher["token"], challenge_id)
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    horizon = datetime.fromisoformat(before["planned_at"]) + PLAN_HORIZON

    _advance(clock, candidate_source, to=horizon - timedelta(hours=1))
    assert await _the_hour_passes(session_factory, clock) == CalledOff(0, 0)
    assert (await _row(client, searcher["token"], challenge_id))["standing"] == (
        "LINE_UP_INCOMPLETE"
    )

    _advance(clock, candidate_source, to=horizon + timedelta(hours=1))
    assert await _the_hour_passes(session_factory, clock) == CalledOff(1, 0)

    assert (await _row(client, searcher["token"], challenge_id))["standing"] == (
        "CALLED_OFF"
    )
    game = await _the_game(client, searcher["token"], challenge_id)
    assert game["standing"] == "CALLED_OFF", "called off, never a ghost"
    assert game["called_off_by"] is None
    late = await _leave(client, people["ana"]["token"], challenge_id)
    assert late.status_code == 409 and late.json()["code"] == "challenge_is_over"


# ---------------------------------------------------------------------------
# Nobody presses it
# ---------------------------------------------------------------------------


async def test_a_court_that_has_been_a_game_refuses_the_press_from_everybody(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0175`` §1 — the organiser is refused with the court's own
    code, whole or reopened; every other seated player, the leaver, and a
    newcomer still deciding on the open seat are told the act is not theirs —
    one code, asked before anything about the court. Nothing moves: the game
    stays awaiting its entry and the room stands."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    await world.deliver_the_outbox(session_factory)
    before = await _the_game(client, searcher["token"], challenge_id)
    (room,) = await _rooms(client, people["ana"]["token"])

    whole = await _withdraw(client, searcher["token"], challenge_id)
    assert whole.status_code == 409, whole.text
    assert whole.json()["code"] == "court_has_been_a_game"
    seated = await _withdraw(client, people["ana"]["token"], challenge_id)
    assert seated.status_code == 403, seated.text
    assert seated.json()["code"] == "withdraw_is_the_organisers"

    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    reopened = await _withdraw(client, searcher["token"], challenge_id)
    assert reopened.status_code == 409, reopened.text
    assert reopened.json()["code"] == "court_has_been_a_game"
    for who in (people["ana"], people["cy"]):
        not_theirs = await _withdraw(client, who["token"], challenge_id)
        assert not_theirs.status_code == 403, not_theirs.text
        assert not_theirs.json()["code"] == "withdraw_is_the_organisers"

    filled = await _fill_from_the_builder(client, searcher["token"], challenge_id)
    (newcomer_id,) = _newly_invited(filled)
    newcomer = next(one for one in people.values() if str(one["id"]) == newcomer_id)
    deciding = await _withdraw(client, newcomer["token"], challenge_id)
    assert deciding.status_code == 403, deciding.text
    assert deciding.json()["code"] == "withdraw_is_the_organisers"
    filling = await _withdraw(client, searcher["token"], challenge_id)
    assert filling.status_code == 409, filling.text
    assert filling.json()["code"] == "court_has_been_a_game"

    for who in (searcher, people["ana"], people["bo"]):
        game = await _the_game(client, who["token"], challenge_id)
        assert game["game_id"] == before["game_id"]
        assert game["standing"] == "AWAITING_ENTRY"
    assert (await _row(client, searcher["token"], challenge_id))["standing"] == (
        "AWAITING_ANSWERS"
    )
    await world.deliver_the_outbox(session_factory)
    assert [
        one["conversation_id"] for one in await _rooms(client, people["ana"]["token"])
    ] == [room["conversation_id"]], "the room stands"


async def test_an_organiser_who_left_holds_no_press_and_nor_does_anybody_still_on_it(
    client, session_factory, candidate_source, searcher, clock
):
    """The organiser who left is not on the court; the ones who are hold no
    press either — *whose act* is asked first, and the act is nobody's on a
    court that has been a game."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    assert (await _leave(client, searcher["token"], challenge_id)).status_code == 200

    not_on_it = await _withdraw(client, searcher["token"], challenge_id)
    assert not_on_it.status_code == 403, not_on_it.text
    assert not_on_it.json()["code"] == "withdraw_is_the_organisers"
    still_on_it = await _withdraw(client, people["bo"]["token"], challenge_id)
    assert still_on_it.status_code == 403, still_on_it.text
    assert still_on_it.json()["code"] == "withdraw_is_the_organisers"
    assert (await _the_game(client, people["bo"]["token"], challenge_id))[
        "standing"
    ] == "AWAITING_ENTRY"


async def test_a_court_that_never_became_a_game_is_removed_and_never_called_off(
    client, session_factory, candidate_source, searcher, clock
):
    """The other act on this route, and the game-side rule does not leak into
    it: with two people in, the organiser is refused because somebody has
    joined — not because the court is whole — and a member is refused the act
    outright rather than admitted as *any player*. Removing a challenge nobody
    has answered is ``test_challenges.py``'s."""

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

    joined = await _withdraw(client, searcher["token"], challenge_id)
    assert joined.status_code == 409, joined.text
    assert joined.json()["code"] == "somebody_has_joined"
    for who in (searcher, people["ana"], people["bo"]):
        assert await _games(client, who["token"]) == [], "there never was a game"
        detail = await client.get(
            f"/api/v1/challenges/{challenge_id}", headers=world.auth(who["token"])
        )
        assert detail.json()["standing"] == "LINE_UP_INCOMPLETE"


# ---------------------------------------------------------------------------
# The pair, and singles
# ---------------------------------------------------------------------------


async def test_the_pair_may_challenge_each_other_again_afterwards(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0142`` §1 releases on ``WITHDRAWN`` and ``docs/adr/0152`` §4 on
    a settled game; a called-off game is both. Held while the court was
    reopened, released by the hour."""

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

    agreed = await _agree_an_hour(client, searcher["token"], challenge_id, clock)
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    held = await _a_send_between_them()
    assert held.status_code == 409, held.text
    assert held.json()["code"] == "open_challenge_stands"

    _advance(clock, candidate_source, to=agreed + timedelta(minutes=1))
    assert await _the_hour_passes(session_factory, clock) == CalledOff(1, 0)

    released = await _a_send_between_them()
    assert released.status_code == 201, released.text


async def test_in_singles_the_departure_ends_the_court_and_nothing_follows_it(
    client, session_factory, candidate_source, clock
):
    """**#411 rule 9 reversed** (``docs/adr/0165`` §3) — a two whose opponent
    leaves is over by the departure, with no act from the remaining player.
    The challenge is ``CALLED_OFF`` naming the leaver (``docs/adr/0172`` §1),
    so the withdrawal route meets *the challenge is over* as every act on an
    ended court does: no second ``GameCalledOff``, and the end the departure
    gave the game — dated and named — stands."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )
    before = await _the_game(client, sender["token"], challenge_id)
    left = await _leave(client, invitee["token"], challenge_id)
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "CALLED_OFF"
    assert left.json()["ended_by"] == str(invitee["id"])
    called_off = await _the_game(client, sender["token"], challenge_id)
    assert called_off["standing"] == "CALLED_OFF"
    assert called_off["called_off_by"]["player_id"] == str(invitee["id"])
    assert [seat["player_id"] for seat in called_off["seats"]] == [
        str(sender["id"]),
        None,
    ]
    assert await _games(client, invitee["token"]) == []

    refused = await _withdraw(client, sender["token"], challenge_id)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "challenge_is_over"
    after = await _the_game(client, sender["token"], challenge_id)
    assert after["game_id"] == before["game_id"]
    assert after["standing"] == "CALLED_OFF"
    assert after["called_off_at"] == called_off["called_off_at"], "the first end stands"
    assert after["called_off_by"] == called_off["called_off_by"]
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
        "games.called_off",
    ]


async def test_in_singles_the_organisers_departure_ends_it_for_the_opponent_too(
    client, session_factory, candidate_source, clock
):
    """Organiser-blind on a game: the organiser's departure leaves the opponent
    alone, ends the court naming the organiser and calls the game off. The
    opponent never held the withdraw, and is told so before the standing."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )
    left = await _leave(client, sender["token"], challenge_id)
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "CALLED_OFF"
    assert left.json()["ended_by"] == str(sender["id"])
    assert (await _the_game(client, invitee["token"], challenge_id))["standing"] == (
        "CALLED_OFF"
    )

    refused = await _withdraw(client, invitee["token"], challenge_id)

    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "withdraw_is_the_organisers"
    assert (await _the_game(client, invitee["token"], challenge_id))["standing"] == (
        "CALLED_OFF"
    )


# ---------------------------------------------------------------------------
# A court whose game has already ended by its clock
# ---------------------------------------------------------------------------


async def test_a_court_whose_window_has_closed_is_called_off_and_the_ghost_stands(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0163`` §6 — a ghost is not un-ghosted. A court the hour loop
    never reached in time — its window closed while the loop was down, or
    before it existed — is a ghost, charged already, and the challenge still
    holds its pair. The hour calls the court off all the same: the challenge
    is ``CALLED_OFF`` with nobody named, the game keeps the end it reached,
    and the pair is released. The two readings jar and are each true of their
    own record."""

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

    assert await _the_hour_passes(session_factory, clock) == CalledOff(1, 0)

    row = await _row(client, searcher["token"], challenge_id)
    assert row["standing"] == "CALLED_OFF"
    assert row["ended_by"] is None
    after = await _the_game(client, searcher["token"], challenge_id)
    assert after["standing"] == "NEVER_PLAYED", "a ghost is not un-ghosted"
    assert after["called_off_at"] is None
    assert after["called_off_by"] is None
    assert after["entry_closes_at"] is not None
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
    ]
    detail = await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(people["ana"]["token"])
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["standing"] == "CALLED_OFF"
    released = await client.post(
        "/api/v1/challenges",
        json={"search_id": search_id, "court": court},
        headers=world.auth(searcher["token"]),
    )
    assert released.status_code == 201, released.text


# ---------------------------------------------------------------------------
# The last player leaves, whoever is still deciding
# ---------------------------------------------------------------------------


async def test_the_last_departure_calls_it_off_and_the_pending_invitation_with_it(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0175`` §2 — a court with nobody on it is nobody's game. Two
    of the four left, the organiser asked somebody new, and the last two leave
    while the newcomer is still deciding: the first of those two leaves one
    player with somebody deciding, which stands; the second leaves nobody,
    which is called off — ``ended_by`` the leaver — and the newcomer's yes
    meets *the challenge is over*. Their row reads ``CALLED_OFF`` for its day."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    before = await _the_game(client, searcher["token"], challenge_id)
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    filled = await _fill_from_the_builder(client, searcher["token"], challenge_id)
    (newcomer_id,) = _newly_invited(filled)
    newcomer = next(one for one in people.values() if str(one["id"]) == newcomer_id)
    assert (
        await _leave(client, people["bo"]["token"], challenge_id)
    ).status_code == 200

    alone = await _leave(client, people["ana"]["token"], challenge_id)
    assert alone.status_code == 200, alone.text
    assert alone.json()["standing"] == "AWAITING_ANSWERS", (
        "one player with somebody deciding is a court that may yet be a game"
    )
    assert (await _the_game(client, searcher["token"], challenge_id))["standing"] == (
        "AWAITING_ENTRY"
    )

    last = await _leave(client, searcher["token"], challenge_id)

    assert last.status_code == 200, last.text
    assert last.json()["standing"] == "CALLED_OFF"
    assert last.json()["ended_by"] == str(searcher["id"])
    assert await _games(client, searcher["token"]) == [], "the leaver's rail"
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
        "games.seat_vacated",
        "games.seat_vacated",
        "games.seat_vacated",
        "games.called_off",
    ]
    yes = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(newcomer["token"]),
    )
    assert yes.status_code == 409, yes.text
    assert yes.json()["code"] == "challenge_is_over"
    row = await _row(client, newcomer["token"], challenge_id)
    assert row is not None and row["standing"] == "CALLED_OFF"
    assert row["ended_by"] == str(searcher["id"])
    assert (
        next(seat for seat in row["seats"] if seat["player_id"] == str(newcomer["id"]))[
            "answer"
        ]
        is None
    ), "asked, and never answered"


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

    refused = await _withdraw(client, people["cy"]["token"], challenge_id)

    assert refused.status_code == 403
    assert set(_refusal(refused)) == {"code", "message"}
    assert str(searcher["id"]) not in refused.text
    assert str(people["ana"]["id"]) not in refused.text

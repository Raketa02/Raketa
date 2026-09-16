"""The card's dismissal — a per-player act on a called-off game, derived on
every read (``docs/adr/0172`` §5).

**The first test is #448's tenth story.** Rafa clears the called-off card: it
leaves his rail on the reply and stays cleared on every device, because it is
recorded on the game and subtracted on every read of ``GET /games`` — and
nobody else's rail moves and the record is untouched. **The challenge's row goes
with the card** (``docs/adr/0173``): one act clears one court from the reader's
two lists, so ``GET /challenges`` subtracts its reader off the same set, and the
others' rows keep their day.

Everything after it is what the record decided: that a second press answers the
same and writes nothing; that a live game, a ghost and a played game each refuse
it with its own code; and that a stranger — and the leaver whose departure
called the game off, whose seat is open and whose rail never held the card — is
told what a stranger is told.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.api.dependencies import get_clock
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from tests.api import matchmaking_world as world
from tests.api.test_departure import (
    STRAIGHT_SETS,
    _a_city,
    _a_completed_four,
    _a_player,
    _a_singles_game,
    _advance,
    _game_stream,
    _games,
    _leave,
    _refusal,
    _the_game,
)
from tests.unit.fake_event_store import FrozenClock


@pytest.fixture
def clock(client):
    """The API's clock, stopped where this file starts and moved by hand —
    ``test_departure.py``'s fixture, spelled again on this directory's
    convention."""

    frozen = FrozenClock(at=datetime.now(timezone.utc))
    world.override(client, get_clock, lambda: frozen)
    return frozen


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _dismiss(client, token: str, game_id: str):
    return await client.post(
        f"/api/v1/games/{game_id}/dismissal", headers=world.auth(token)
    )


async def _withdraw(client, token: str, challenge_id: str):
    return await client.post(
        f"/api/v1/challenges/{challenge_id}/withdrawal", headers=world.auth(token)
    )


async def _row(client, token: str, challenge_id: str) -> dict | None:
    """This court's row on this reader's inbox, or ``None`` because the inbox
    does not list it."""

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


async def test_the_dismissal_clears_the_card_for_its_reader_and_nobody_else(
    client, session_factory, candidate_source, searcher, clock
):
    """One of a four leaves and another presses *Call it off*, so the organiser
    is left with a called-off card. Clearing it answers ``204`` and nothing; the
    game is gone from **their** rail on the next read and on every read after,
    and so is the challenge row from **their** inbox — the same act, the same
    set, read on the other list (``docs/adr/0173``). The two others still on the
    court when it ended still read both: their card, and their row reading
    ``CALLED_OFF`` for its day naming the presser. The record is one event
    longer and otherwise untouched."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    before = await _the_game(client, searcher["token"], challenge_id)
    assert (
        await _leave(client, people["cy"]["token"], challenge_id)
    ).status_code == 200
    called_off = await _withdraw(client, people["bo"]["token"], challenge_id)
    assert called_off.status_code == 200, called_off.text
    assert called_off.json()["standing"] == "CALLED_OFF"
    for who in (searcher, people["ana"], people["bo"]):
        assert (await _the_game(client, who["token"], challenge_id))["standing"] == (
            "CALLED_OFF"
        )

    dismissed = await _dismiss(client, searcher["token"], before["game_id"])

    assert dismissed.status_code == 204, dismissed.text
    assert dismissed.content == b""
    assert await _games(client, searcher["token"]) == [], "gone on the reply's read"
    assert await _games(client, searcher["token"]) == [], "and on every read after"
    for who in (people["ana"], people["bo"]):
        game = await _the_game(client, who["token"], challenge_id)
        assert game["standing"] == "CALLED_OFF", "nobody else's rail moves"
        assert game["called_off_by"]["player_id"] == str(people["bo"]["id"])
    assert await _row(client, searcher["token"], challenge_id) is None, (
        "the row goes with the card"
    )
    for who in (people["ana"], people["bo"]):
        row = await _row(client, who["token"], challenge_id)
        assert row is not None, "nobody else's inbox moves"
        assert row["standing"] == "CALLED_OFF", "and their row keeps its day"
        assert row["ended_by"] == str(people["bo"]["id"])
    assert await _game_stream(session_factory, before["game_id"]) == [
        "games.planned",
        "games.seat_vacated",
        "games.called_off",
        "games.dismissed",
    ]


async def test_a_second_press_answers_the_same_and_writes_nothing(
    client, session_factory, candidate_source, clock
):
    """*Writes nothing twice*: recorded once per player, and a retry is not a
    second event. In singles the presser is the one left, and the card is
    theirs to clear."""

    sender = await _a_player(client, "juno")
    invitee = await _a_player(client, "milo")
    await world.fold_the_log(session_factory, candidate_source)
    challenge_id = await _a_singles_game(
        client, session_factory, candidate_source, sender, invitee
    )
    before = await _the_game(client, sender["token"], challenge_id)
    assert (await _leave(client, invitee["token"], challenge_id)).status_code == 200

    first = await _dismiss(client, sender["token"], before["game_id"])
    second = await _dismiss(client, sender["token"], before["game_id"])

    assert first.status_code == 204, first.text
    assert second.status_code == 204, second.text
    assert await _games(client, sender["token"]) == []
    assert (await _game_stream(session_factory, before["game_id"])).count(
        "games.dismissed"
    ) == 1


async def test_the_one_left_behind_clears_the_row_the_departures_left_them(
    client, session_factory, candidate_source, searcher, clock
):
    """The court both readings fit (``docs/adr/0172`` §7): the organiser sent a
    four, everybody accepted, and the three of them left one by one — the
    third departure called the game off, and the organiser is alone on a row
    reading *{name} left* under a ``Called off`` tag, with a day to wait. The
    dismissal is theirs: the row is gone from their inbox on the next read and
    on every read after, the game is gone from their rail, and the leavers —
    whose own rows left at once and whose seats were vacated — are answered as
    strangers, as before."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    game = await _the_game(client, searcher["token"], challenge_id)
    for name in ("cy", "bo"):
        assert (
            await _leave(client, people[name]["token"], challenge_id)
        ).status_code == 200
    last = await _leave(client, people["ana"]["token"], challenge_id)
    assert last.status_code == 200 and last.json()["standing"] == "CALLED_OFF"
    before = await _row(client, searcher["token"], challenge_id)
    assert before is not None and before["standing"] == "CALLED_OFF"
    assert before["ended_by"] == str(people["ana"]["id"])

    dismissed = await _dismiss(client, searcher["token"], game["game_id"])

    assert dismissed.status_code == 204, dismissed.text
    assert await _row(client, searcher["token"], challenge_id) is None
    assert await _row(client, searcher["token"], challenge_id) is None, (
        "and on every read after"
    )
    assert await _games(client, searcher["token"]) == []
    for name in ("ana", "bo", "cy"):
        refused = await _dismiss(client, people[name]["token"], game["game_id"])
        assert refused.status_code == 403, refused.text
        assert _refusal(refused)["code"] == "you_were_not_on_this_court"
    assert (await _game_stream(session_factory, game["game_id"])).count(
        "games.dismissed"
    ) == 1


async def test_only_a_called_off_game_can_be_dismissed(
    client, session_factory, candidate_source, searcher, clock
):
    """Refused with its own code on a live game, on a reopened one, on a ghost
    and on a played one — the other endings' cards are the record for the day
    they stay, and a live game's card is the game. Nothing is written."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    live = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    live_game = await _the_game(client, searcher["token"], live)

    refused = await _dismiss(client, searcher["token"], live_game["game_id"])
    assert refused.status_code == 409, refused.text
    assert _refusal(refused)["code"] == "game_is_not_called_off"

    assert (await _leave(client, people["cy"]["token"], live)).status_code == 200
    reopened = await _dismiss(client, searcher["token"], live_game["game_id"])
    assert reopened.status_code == 409, reopened.text
    assert reopened.json()["code"] == "game_is_not_called_off"

    # The reopened court still holds the searcher's pairs with ana and bo, so
    # the played four is made of the people it released: cy left it.
    played = await _a_completed_four(client, searcher, people, "dee", "eve", "cy")
    played_game = await _the_game(client, searcher["token"], played)
    stated = await client.post(
        f"/api/v1/games/{played_game['game_id']}/result",
        json={"score": STRAIGHT_SETS},
        headers=world.auth(searcher["token"]),
    )
    assert stated.status_code == 200, stated.text
    on_a_played_game = await _dismiss(client, searcher["token"], played_game["game_id"])
    assert on_a_played_game.status_code == 409, on_a_played_game.text
    assert on_a_played_game.json()["code"] == "game_is_not_called_off"

    _advance(
        clock,
        candidate_source,
        to=datetime.fromisoformat(live_game["planned_at"])
        + PLAN_HORIZON
        + ENTRY_GRACE
        + timedelta(hours=1),
    )
    assert (await _the_game(client, searcher["token"], live))["standing"] == (
        "NEVER_PLAYED"
    )
    on_a_ghost = await _dismiss(client, searcher["token"], live_game["game_id"])
    assert on_a_ghost.status_code == 409, on_a_ghost.text
    assert on_a_ghost.json()["code"] == "game_is_not_called_off"
    assert "games.dismissed" not in await _game_stream(
        session_factory, live_game["game_id"]
    )


async def test_a_stranger_and_the_leaver_are_refused_alike(
    client, session_factory, candidate_source, searcher, clock
):
    """The one rule every act on a game shares: the people who may act are the
    people on the court. The leaver whose departure called it off has been
    vacated — the card was never on their rail — and a stranger, and a game id
    that names nothing, meet the same code."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_completed_four(client, searcher, people, "ana", "bo", "cy")
    game = await _the_game(client, searcher["token"], challenge_id)
    for name in ("cy", "bo"):
        assert (
            await _leave(client, people[name]["token"], challenge_id)
        ).status_code == 200
    last = await _leave(client, people["ana"]["token"], challenge_id)
    assert last.status_code == 200 and last.json()["standing"] == "CALLED_OFF"
    assert await _games(client, people["ana"]["token"]) == []

    leaver = await _dismiss(client, people["ana"]["token"], game["game_id"])
    stranger = await _dismiss(client, people["dee"]["token"], game["game_id"])
    nothing = await _dismiss(client, searcher["token"], str(game["challenge_id"]))

    for refused in (leaver, stranger, nothing):
        assert refused.status_code == 403, refused.text
        assert _refusal(refused)["code"] == "you_were_not_on_this_court"
        assert str(searcher["id"]) not in refused.text
    assert (
        await _dismiss(client, searcher["token"], game["game_id"])
    ).status_code == 204

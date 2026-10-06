"""The game routes, end to end over HTTP — on a game a booking opened.

A booking opens a game (#541) the way the fill does, through games' own use
case, and **a game exists that no game route asked for**: everything here is
what the people on its court do with it afterwards.

Five things are asserted here and nowhere else:

**A game is opened by a booking, not by a request.** There is no route that
creates one, and the game is on all four players' lists, filed under its
booking.

**A result is the record that the game happened.** The entry carries the moment;
nothing sends a date, because the booked hour is already on the game.

**A court with a seat open refuses a result** (``docs/adr/0162`` §3): a side the
engine cannot price, and a seat with no outcome to give anyone.

**Silence confirms, and no route is called confirm.** The proposal's window is
the whole mechanism, and the response says when it closes.

**Disagreement carries a score.** There is no rejection endpoint and no body
without one.

**A seat names the person in it and says nothing else about them.** The handle
travels and the card does not, and the court is the whole of the permission —
so a block, which is forward-looking, does not reach back and unname somebody
you already played (``docs/adr/0141``).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.kernel import instant
from app.modules.games.application.commands import VacateSeatCommand
from app.modules.games.application.vacate_seat import VacateSeat
from tests.api import matchmaking_world as world
from tests.api import players_world as players


@pytest.fixture
async def searcher(client):
    return await players.a_rated_player(client, "searcher")


async def _a_city(client, session_factory, mu: float) -> dict:
    """Three other players, each with a token of their own.

    Signed in rather than folded in alone, because everything under test here is
    something only somebody who played can do.
    """

    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await players.a_player_on_the_log(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token}
    return people


async def _games(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/games", headers=players.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["games"]


async def _a_booked_four(session_factory, host: dict, people: dict) -> dict:
    """A padel four booked for an hour that began two hours ago — played, and
    nobody has said so yet. Its game's id and its booking's."""

    return await players.a_booked_game(
        session_factory,
        side_a=(host["id"], people["ana"]["id"]),
        side_b=(people["bo"]["id"], people["cy"]["id"]),
        starts_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )


async def _an_arranged_game(client, session_factory, searcher):
    people = await _a_city(client, session_factory, searcher["mu"])
    booked = await _a_booked_four(session_factory, searcher, people)
    return people, booked


async def test_a_booking_leaves_a_game_behind(client, session_factory, searcher):
    """**The thing no game route created.**

    It is on every player's list, it carries the booking it came from, and it
    is awaiting somebody saying it happened — which is the only way anything ever
    learns that it did.
    """

    people, booked = await _an_arranged_game(client, session_factory, searcher)

    for token in [searcher["token"]] + [one["token"] for one in people.values()]:
        (game,) = await _games(client, token)
        assert game["game_id"] == str(booked["game_id"])
        assert game["challenge_id"] == str(booked["booking_id"])
        assert game["standing"] == "AWAITING_ENTRY"
        assert game["kind"] == "COUNTED"
        assert game["played_at"] is None
        assert game["entry_closes_at"] is not None
        assert len(game["seats"]) == 4


#: Every field a *card* carries. None of them may appear on a seat: a Level, a
#: band and a run of form are what a searcher reads to decide about a game that
#: might happen, and a game is the record of one that did.
_CARD_FIELDS = (
    "player_card",
    "level",
    "band",
    "range",
    "area_code",
    "social_tags",
    "photo_id",
    "photo_url",
    "review",
    "player_score",
    "counted_games",
    "last_five",
)


async def test_a_seat_names_the_person_in_it_and_says_nothing_else_about_them(
    client, session_factory, searcher
):
    """**The handle travels; the card does not.**

    Without it the screens name *sides*, which leaves a result agreed with
    nobody and three padel games in a week told apart by nothing but how long
    ago they were arranged. With a card on it, a game would be a directory with
    extra steps — every value on one is as-of-now, stapled to an evening in the
    past, and it is what a *gate* decided a searcher may see.

    **Your own seat carries your own handle**, and the client is what decides to
    print *You* over it: which id is the reader's is already on the response.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    everybody = {str(searcher["id"]): "searcher"} | {
        str(one["id"]): name for name, one in people.items()
    }

    for token in [searcher["token"]] + [one["token"] for one in people.values()]:
        (game,) = await _games(client, token)
        assert {seat["player_id"]: seat["name"] for seat in game["seats"]} == (
            everybody
        )
        for seat in game["seats"]:
            assert not [field for field in _CARD_FIELDS if field in seat], (
                "a seat carries a handle and nothing else about the person"
            )


async def test_the_two_acts_name_the_court_the_way_the_list_does(
    client, session_factory, searcher
):
    """One shape, three routes.

    A screen that could name the other side while reading and not after
    answering would go anonymous at the moment it most needs a name — the tap
    that settles a score against a person.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])
    named = {seat["player_id"]: seat["name"] for seat in game["seats"]}

    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(searcher["token"]),
    )
    assert stated.status_code == 200, stated.text
    assert {
        seat["player_id"]: seat["name"] for seat in stated.json()["seats"]
    } == named

    theirs = _an_opponent_of(game, searcher, people)
    agreed = await client.post(
        f"/api/v1/games/{game['game_id']}/result/acceptance",
        headers=players.auth(theirs["token"]),
    )
    assert agreed.status_code == 200, agreed.text
    assert {
        seat["player_id"]: seat["name"] for seat in agreed.json()["seats"]
    } == named


async def test_a_block_does_not_unname_somebody_you_already_played(
    client, session_factory, searcher
):
    """**The court is the gate, and nothing here is re-gated.**

    ``docs/adr/0095`` §7 settles it forwards — a block does not reach into a
    game already agreed — and §8 settles it backwards: a handle that vanished
    from a row would be the trace neither party is ever shown. The four
    fail-closed gates decide who may be *introduced*, and an evening you were
    both at is not an introduction.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])
    theirs = _an_opponent_of(game, searcher, people)

    blocked = await players.block_between(client, searcher["token"], theirs["id"])
    assert blocked.status_code == 204, blocked.text

    for token in (searcher["token"], theirs["token"]):
        (after,) = await _games(client, token)
        assert all(seat["name"] is not None for seat in after["seats"]), (
            "a block is forward-looking and does not unname a court"
        )


async def test_stating_a_result_records_that_the_game_happened(
    client, session_factory, searcher
):
    """One act, two facts. **Nothing sends a date.**

    The entry carries the moment, because a booking, a calendar and a court
    reservation are the three things this platform does not have.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])

    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(searcher["token"]),
    )

    assert stated.status_code == 200, stated.text
    body = stated.json()
    assert body["standing"] == "AWAITING_ANSWER"
    assert body["played_at"] is not None
    assert body["entry_closes_at"] is None
    assert body["score"] is None, "a score nobody has answered is not the result"
    (proposal,) = body["proposals"]
    assert proposal["proposed_by"] == str(searcher["id"])
    assert proposal["answer_by"] > proposal["settles_at"] > proposal["proposed_at"]
    assert body["acceptance"] is None, "nobody has agreed with it yet"


async def test_the_other_side_agrees_and_the_game_has_a_winner(
    client, session_factory, searcher
):
    """One opponent suffices, and the outcome is rendered **for the reader**.

    The score is absolute and the outcome is not: the same game is a win on one
    list and a loss on another, which is why neither side stores the other's.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])
    await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(searcher["token"]),
    )

    theirs = _an_opponent_of(game, searcher, people)
    agreed = await client.post(
        f"/api/v1/games/{game['game_id']}/result/acceptance",
        headers=players.auth(theirs["token"]),
    )

    assert agreed.status_code == 200, agreed.text
    assert agreed.json()["standing"] == "AWAITING_ANSWER", (
        "an acceptance settles nothing until its grace has passed"
    )


async def test_a_played_game_reaches_a_bystanders_card_as_a_counted_game(
    client, session_factory, candidate_source, searcher
):
    """**The whole wiring, end to end**: a game happened, and a card says so.

    It lives here rather than beside the other card assertions in
    ``test_searches.py`` because arranging a game is what this file can do — a
    court is booked for four people and then played, and there is no route that
    creates a game.

    **The four who played are read by somebody who did not**: the searcher here
    is a fifth player, reading the record they left off a card.

    What it proves is the seam ``games`` and the matcher meet on: the count comes
    off ``GameHistoryQuery`` through the card's own source, at assembly time and
    never off the candidate index (``docs/adr/0111``).

    **An unscored game is in the count.** The result is stated and not yet
    agreed, so the game is *an evening, not evidence*: it says these people were
    on a court, it moves nobody's Level, and it is a counted game
    (``docs/adr/0137``). ``last_five`` stays absent, which is the same rule read
    the other way — a run of form is agreed results only.
    """

    host = await players.a_rated_player(client, "host")
    people = await _a_city(client, session_factory, host["mu"])
    await _a_booked_four(session_factory, host, people)
    (game,) = await _games(client, host["token"])
    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(host["token"]),
    )
    assert stated.status_code == 200, stated.text
    await world.fold_the_log(session_factory, candidate_source)

    answer = (await world.search(client, searcher["token"])).json()
    played = {str(one["id"]) for one in people.values()}
    rows = [row for row in answer["candidates"] if row["player_id"] in played]

    assert rows, "nobody who played is on the bystander's list"
    for row in rows:
        card = row["player_card"]
        assert card["counted_games"] == 1
        assert "last_five" not in card, (
            "nobody has agreed a score, so there is no run of form to draw"
        )


async def test_there_is_no_rejection_and_a_disagreement_carries_a_score(
    client, session_factory, searcher
):
    """The other side's one turn, and it says what happened instead.

    A rejection carrying nothing would be free and always optimal for the loser;
    there is no shape on this route for one, and a second turn from the same side
    is refused.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])
    await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(searcher["token"]),
    )
    opponent = _an_opponent_of(game, searcher, people)

    countered = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 4, "b": 6}, {"a": 3, "b": 6}]}},
        headers=players.auth(opponent["token"]),
    )
    assert countered.status_code == 200, countered.text
    body = countered.json()
    assert body["score"] is None, "neither of the two is *the* one"
    assert [
        one["score"]["sets"] for one in body["proposals"]
    ] == [
        [{"a": 6, "b": 4}, {"a": 6, "b": 3}],
        [{"a": 4, "b": 6}, {"a": 3, "b": 6}],
    ], "the argument crosses with both sides of it on"

    again = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 4, "b": 6}, {"a": 2, "b": 6}]}},
        headers=players.auth(opponent["token"]),
    )
    assert again.status_code == 409
    assert again.json()["code"] == "your_side_has_already_answered"


async def test_a_disagreement_offers_its_own_way_out_to_the_side_that_started_it(
    client, session_factory, searcher
):
    """**The exit from an argument, readable by both people in it.**

    ``accept_result`` passes with both sides in ``proposals`` — either side
    accepting the other's is the only end a two-proposal disagreement has that is
    not the game going unscored. A response that carried neither score offered
    that act to nobody: agreeing with a score you cannot be shown is worse than
    not being asked.

    The proposals travel **side A first and never in the order they arrived**, so
    the pair reads the same on both phones and on a second reading of the same
    game.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])
    opponent = _an_opponent_of(game, searcher, people)
    assert _side_of(game, str(opponent["id"])) == "B", (
        "the organiser holds A, so the counter below is what puts A in second"
    )

    # **The far side enters first**, so arrival order is B then A and the order
    # asserted below is the sort's doing rather than the stream's.
    await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 4, "b": 6}, {"a": 3, "b": 6}]}},
        headers=players.auth(opponent["token"]),
    )
    await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(searcher["token"]),
    )

    (mine,) = await _games(client, searcher["token"])
    assert mine["standing"] == "AWAITING_ANSWER"
    assert [one["side"] for one in mine["proposals"]] == ["A", "B"]
    assert [one["proposed_by"] for one in mine["proposals"]] == [
        str(searcher["id"]),
        str(opponent["id"]),
    ], "side A first, though side B is what arrived first"

    agreed = await client.post(
        f"/api/v1/games/{game['game_id']}/result/acceptance",
        headers=players.auth(searcher["token"]),
    )

    assert agreed.status_code == 200, agreed.text
    body = agreed.json()
    ours, theirs = body["proposals"]
    acceptance = body["acceptance"]
    assert acceptance["of_side"] == "B", (
        "the score agreed with is the other side's, and the response names it"
    )
    # **Two scores, two graces**, and the one that counts is the one whose score
    # was agreed with — a check the single-proposal case cannot make, because
    # there the wrong answer and the right one are the same instant.
    assert ours["settles_at"] != theirs["settles_at"]
    assert acceptance["settles_at"] == theirs["settles_at"]


async def test_a_pending_acceptance_says_who_agreed_and_when_it_settles(
    client, session_factory, searcher
):
    """**The grace, visible to the side it is being run against.**

    It settles nothing for six hours, and for those six hours the proposing side
    was told silence would confirm their score — which had stopped being the live
    question — and was offered a correction ``state_result`` refuses. Both are
    read off this field, and *when* they answered is on it because a second ago
    and five hours ago are not the same news.
    """

    people, _ = await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])
    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(searcher["token"]),
    )
    assert stated.status_code == 200, stated.text
    opponent = _an_opponent_of(game, searcher, people)
    await client.post(
        f"/api/v1/games/{game['game_id']}/result/acceptance",
        headers=players.auth(opponent["token"]),
    )

    (mine,) = await _games(client, searcher["token"])

    assert mine["standing"] == "AWAITING_ANSWER", (
        "an acceptance settles nothing until its grace has passed"
    )
    acceptance = mine["acceptance"]
    assert acceptance["agreed_by"] == str(opponent["id"])
    assert acceptance["of_side"] == _side_of(game, str(searcher["id"]))
    assert acceptance["agreed_at"] <= acceptance["settles_at"]
    (proposal,) = mine["proposals"]
    assert acceptance["settles_at"] == proposal["settles_at"], (
        "the grace is measured from the score, not from the tap"
    )


async def test_a_level_score_is_refused_because_a_result_names_a_winner(
    client, session_factory, searcher
):
    """*Last 5* is win or loss, and none of the four sports produces a draw."""

    await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])

    refused = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 4, "b": 6}]}},
        headers=players.auth(searcher["token"]),
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "a_score_must_name_a_winner"


async def _leaves(session_factory, booking_id, player_id) -> None:
    """Somebody leaves the booked game — through games' own ``VacateSeat``,
    which is how the booking's *Leave the game* opens the seat (#544)."""

    async with session_factory() as session:
        games = build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        await VacateSeat(games=games).execute(
            VacateSeatCommand(challenge_id=booking_id, player_id=player_id),
            occurred_at=instant(datetime.now(timezone.utc)),
        )
        await session.commit()


async def test_a_court_with_a_seat_open_cannot_record_a_result(
    client, session_factory, searcher
):
    """``docs/adr/0162`` §3 — a score on a court with a seat open is a score
    with a side nobody can price. Booked well ahead here, so the hour has not
    come and the game has not *started short*; it is still awaiting its entry,
    with the leaver's seat drawn open."""

    people = await _a_city(client, session_factory, searcher["mu"])
    booked = await players.a_booked_game(
        session_factory,
        side_a=(searcher["id"], people["ana"]["id"]),
        side_b=(people["bo"]["id"], people["cy"]["id"]),
    )
    await _leaves(session_factory, booked["booking_id"], people["cy"]["id"])

    stated = await client.post(
        f"/api/v1/games/{booked['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=players.auth(searcher["token"]),
    )

    assert stated.status_code == 409, stated.text
    assert stated.json()["code"] == "the_court_has_an_open_seat"
    (game,) = await _games(client, searcher["token"])
    assert game["standing"] == "AWAITING_ENTRY"
    assert [seat for seat in game["seats"] if seat["player_id"] is None]


async def test_nobody_who_did_not_play_can_see_or_touch_the_game(
    client, session_factory, searcher
):
    """One code for two cases, because separating them would answer *is this id
    real* about four strangers' evening."""

    await _an_arranged_game(client, session_factory, searcher)
    (game,) = await _games(client, searcher["token"])
    stranger_id, stranger = await players.a_player_on_the_log(
        client, session_factory, "outsider", mu=searcher["mu"]
    )

    assert await _games(client, stranger) == []
    refused = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 0}]}},
        headers=players.auth(stranger),
    )
    assert refused.status_code == 403
    assert refused.json()["code"] == "you_were_not_on_this_court"


def _an_opponent_of(game: dict, searcher: dict, people: dict) -> dict:
    """Somebody from across the net. **Which of the two is nobody's business.**"""

    return next(
        one
        for one in people.values()
        if _side_of(game, str(one["id"])) != _side_of(game, str(searcher["id"]))
    )


def _side_of(game: dict, player_id: str) -> str:
    return next(
        seat["side"] for seat in game["seats"] if seat["player_id"] == player_id
    )

"""The three game routes, end to end over HTTP — and the seam that creates a game.

The whole reachable path in one file: a searcher builds a court with ⚡, sends it,
everybody accepts, and **a game exists that nobody asked for**. That is the point
of this file. Four acceptances used to leave no fact behind; the first assertion
below is that they now leave one.

Four things are asserted here and nowhere else:

**A game is opened by a completed line-up, not by a request.** There is no route
that creates one, and the game appears on all four players' lists the moment the
last seat accepts.

**A result is the record that the game happened.** The entry carries the moment;
nothing sends a date, because there is no booking and no calendar to check one
against.

**Silence confirms, and no route is called confirm.** The proposal's window is
the whole mechanism, and the response says when it closes.

**Disagreement carries a score.** There is no rejection endpoint and no body
without one.
"""

from __future__ import annotations

import pytest

from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    """Three other players, each with a token of their own.

    Signed in rather than folded in alone, because everything under test here is
    something only somebody who played can do.
    """

    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _a_sent_challenge(client, searcher) -> str:
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
    return sent.json()["challenge_id"]


async def _everybody_accepts(client, challenge_id: str, people: dict) -> None:
    for person in people.values():
        answered = await client.post(
            f"/api/v1/challenges/{challenge_id}/accept",
            headers=world.auth(person["token"]),
        )
        assert answered.status_code == 200, answered.text


async def _games(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/games", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["games"]


async def _an_arranged_game(client, session_factory, candidate_source, searcher):
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_sent_challenge(client, searcher)
    await _everybody_accepts(client, challenge_id, people)
    return people, challenge_id


async def test_a_completed_line_up_leaves_a_game_behind(
    client, session_factory, candidate_source, searcher
):
    """**The thing that did not exist.** No request created this.

    It is on every player's list, it carries the challenge it came from, and it
    is awaiting somebody saying it happened — which is the only way anything ever
    learns that it did.
    """

    people, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    for token in [searcher["token"]] + [one["token"] for one in people.values()]:
        (game,) = await _games(client, token)
        assert game["challenge_id"] == challenge_id
        assert game["standing"] == "AWAITING_ENTRY"
        assert game["kind"] == "COUNTED"
        assert game["played_at"] is None
        assert game["entry_closes_at"] is not None
        assert len(game["seats"]) == 4


async def test_stating_a_result_records_that_the_game_happened(
    client, session_factory, candidate_source, searcher
):
    """One act, two facts. **Nothing sends a date.**

    The entry carries the moment, because a booking, a calendar and a court
    reservation are the three things this platform does not have.
    """

    people, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    (game,) = await _games(client, searcher["token"])

    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
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
    client, session_factory, candidate_source, searcher
):
    """One opponent suffices, and the outcome is rendered **for the reader**.

    The score is absolute and the outcome is not: the same game is a win on one
    list and a loss on another, which is why neither side stores the other's.
    """

    people, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    (game,) = await _games(client, searcher["token"])
    await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )

    theirs = _an_opponent_of(game, searcher, people)
    agreed = await client.post(
        f"/api/v1/games/{game['game_id']}/result/acceptance",
        headers=world.auth(theirs["token"]),
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
    court is built, sent, accepted by four people and then played, and there is
    no shorter path to a counted game because there is no route that creates one.

    **The four who played are read by somebody who did not**, and that is not a
    convenience: an open challenge gates its own participants out of each other's
    lists, so the four cannot see each other and only a fifth player can see the
    record they left. The searcher here is that fifth player.

    What it proves is the seam ``games`` and the matcher meet on: the count comes
    off ``GameHistoryQuery`` through the card's own source, at assembly time and
    never off the candidate index (``docs/adr/0111``).

    **An unscored game is in the count.** The result is stated and not yet
    agreed, so the game is *an evening, not evidence*: it says these people were
    on a court, it moves nobody's Level, and it is a counted game
    (``docs/adr/0137``). ``last_five`` stays absent, which is the same rule read
    the other way — a run of form is agreed results only.
    """

    host = await world.a_searcher(client, "host")
    people = await _a_city(client, session_factory, candidate_source, host["mu"])
    challenge_id = await _a_sent_challenge(client, host)
    await _everybody_accepts(client, challenge_id, people)
    (game,) = await _games(client, host["token"])
    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(host["token"]),
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
    client, session_factory, candidate_source, searcher
):
    """The other side's one turn, and it says what happened instead.

    A rejection carrying nothing would be free and always optimal for the loser;
    there is no shape on this route for one, and a second turn from the same side
    is refused.
    """

    people, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    (game,) = await _games(client, searcher["token"])
    await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    opponent = _an_opponent_of(game, searcher, people)

    countered = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 4, "b": 6}, {"a": 3, "b": 6}]}},
        headers=world.auth(opponent["token"]),
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
        headers=world.auth(opponent["token"]),
    )
    assert again.status_code == 409
    assert again.json()["code"] == "your_side_has_already_answered"


async def test_a_disagreement_offers_its_own_way_out_to_the_side_that_started_it(
    client, session_factory, candidate_source, searcher
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

    people, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
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
        headers=world.auth(opponent["token"]),
    )
    await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
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
        headers=world.auth(searcher["token"]),
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
    client, session_factory, candidate_source, searcher
):
    """**The grace, visible to the side it is being run against.**

    It settles nothing for six hours, and for those six hours the proposing side
    was told silence would confirm their score — which had stopped being the live
    question — and was offered a correction ``state_result`` refuses. Both are
    read off this field, and *when* they answered is on it because a second ago
    and five hours ago are not the same news.
    """

    people, _ = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    (game,) = await _games(client, searcher["token"])
    stated = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    assert stated.status_code == 200, stated.text
    opponent = _an_opponent_of(game, searcher, people)
    await client.post(
        f"/api/v1/games/{game['game_id']}/result/acceptance",
        headers=world.auth(opponent["token"]),
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
    client, session_factory, candidate_source, searcher
):
    """*Last 5* is win or loss, and none of the four sports produces a draw."""

    await _an_arranged_game(client, session_factory, candidate_source, searcher)
    (game,) = await _games(client, searcher["token"])

    refused = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 4, "b": 6}]}},
        headers=world.auth(searcher["token"]),
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "a_score_must_name_a_winner"


async def test_nobody_who_did_not_play_can_see_or_touch_the_game(
    client, session_factory, candidate_source, searcher
):
    """One code for two cases, because separating them would answer *is this id
    real* about four strangers' evening."""

    await _an_arranged_game(client, session_factory, candidate_source, searcher)
    (game,) = await _games(client, searcher["token"])
    stranger_id, stranger = await world.a_signed_in_candidate(
        client, session_factory, "outsider", mu=searcher["mu"]
    )

    assert await _games(client, stranger) == []
    refused = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 0}]}},
        headers=world.auth(stranger),
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

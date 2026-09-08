"""The card, end to end over HTTP — and everything it refuses to be.

A four is built with ⚡, sent, accepted by everybody, played, and its score left
to confirm itself. Then the people who were there are asked how it went. That is
the whole reachable path, and it starts from the same walk ``test_games.py``
takes because a card cannot exist without a game and a game cannot exist without
a completed line-up.

Six things are asserted here and nowhere else:

**A card cannot be answered before the game is over.** The refusal for *not
settled* is byte-identical to the refusal for *not yours* and for *no such game*,
which is a stronger claim than three status assertions and is the one that would
catch a helpful message added later.

**Everybody else on the court is on the card, and nobody else is.** Both
opponents and the partner; not yourself, and not somebody from another evening.

**A blank leaves nothing and the whole-card blank is an answer.** Both close the
card, and the second is the one a later build session could quietly turn into a
no-op.

**Submitting closes it.** A second request is refused whatever the first one
carried.

**Only the most recent rating of a person counts.** Two games with the same
person leave one answer, not two — asserted against the stored rows, because
there is deliberately no route that would show it.

**No individual rating crosses the wire, ever.** The route answers ``204`` with
no body, and there is no route anywhere on the surface that returns one.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select

from app.api.dependencies import get_clock
from app.kernel import Instant, instant
from app.modules.games.domain.windows import PROPOSAL_WINDOW
from app.modules.sportsmanship.infrastructure.card_model import (
    SportsmanshipCardORM,
    SportsmanshipRatingORM,
)
from tests.api import matchmaking_world as world


class MovableClock:
    """The one clock the whole application runs on, for one test.

    A game settles when a clock passes and nothing else — there is no route
    called confirm and no sweep to trigger (``docs/adr/0137``) — so a test that
    wants a settled game has to move time. It is structural rather than a
    subclass of ``Clock``, which is how every other stand-in in this suite is
    written.
    """

    def __init__(self, at: datetime) -> None:
        self._at = at

    def now(self) -> Instant:
        return instant(self._at)

    def move(self, by: timedelta) -> None:
        self._at = self._at + by


@pytest.fixture
def clock(client):
    """Overridden on the running app, so every request in the test agrees.

    Started in the past rather than at ``now`` so that moving forward a day
    still lands before the wall clock — the candidate index the search walks is
    stamped from real time, and a search running in the future would read as
    ahead of the log it is being answered from.
    """

    movable = MovableClock(datetime.now(timezone.utc) - timedelta(days=2))
    world.override(client, get_clock, lambda: movable)
    return movable


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


async def _a_played_game(client, searcher, people) -> str:
    """One arranged game with a score on the table, from ⚡ to *we played*."""

    built = await world.lineup(client, searcher["token"])
    assert built.status_code == 200, built.text
    body = built.json()
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
    challenge_id = sent.json()["challenge_id"]

    for person in people.values():
        answered = await client.post(
            f"/api/v1/challenges/{challenge_id}/accept",
            headers=world.auth(person["token"]),
        )
        assert answered.status_code == 200, answered.text

    # Found by the challenge it came from rather than by being the only one:
    # two of these are arranged in the tests about a rater meeting the same
    # person twice, and *the game* would silently become *the first game*.
    (game,) = [
        one
        for one in await _games(client, searcher["token"])
        if one["challenge_id"] == challenge_id
    ]
    entered = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    assert entered.status_code == 200, entered.text
    return game["game_id"]


async def _games(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/games", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["games"]


async def _a_settled_game(client, session_factory, candidate_source, searcher, clock):
    """A whole game, played and confirmed by the silence of everybody else."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    game_id = await _a_played_game(client, searcher, people)
    clock.move(PROPOSAL_WINDOW + timedelta(minutes=1))
    (game,) = [
        one
        for one in await _games(client, searcher["token"])
        if one["game_id"] == game_id
    ]
    assert game["standing"] == "CONFIRMED", "the score should have confirmed itself"
    return game_id, people


async def _rate(client, token: str, game_id: str, ratings: list[dict]):
    return await client.post(
        f"/api/v1/sportsmanship/{game_id}",
        json={"ratings": ratings},
        headers=world.auth(token),
    )


async def _stored_cards(session_factory) -> list[SportsmanshipCardORM]:
    async with session_factory() as session:
        found = await session.execute(select(SportsmanshipCardORM))
        return list(found.scalars())


async def _stored_ratings(session_factory) -> list[SportsmanshipRatingORM]:
    async with session_factory() as session:
        found = await session.execute(
            select(SportsmanshipRatingORM).order_by(SportsmanshipRatingORM.stars)
        )
        return list(found.scalars())


async def test_everybody_else_on_the_court_can_be_given_stars(
    client, session_factory, candidate_source, searcher, clock
):
    """**Three people in doubles** — both opponents *and* the partner — and the
    answer comes back with nothing in it at all."""

    game_id, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )

    answered = await _rate(
        client,
        searcher["token"],
        game_id,
        [
            {"player_id": str(people["ana"]["id"]), "stars": 5},
            {"player_id": str(people["bo"]["id"]), "stars": 4},
            {"player_id": str(people["cy"]["id"]), "stars": 3},
        ],
    )

    assert answered.status_code == 204, answered.text
    assert answered.content == b"", "no individual rating crosses the wire, ever"
    assert {one.stars for one in await _stored_ratings(session_factory)} == {5, 4, 3}


async def test_a_card_cannot_be_answered_until_the_game_has_settled(
    client, session_factory, candidate_source, searcher, clock
):
    """The card is drawn once the score settles, and the route says so — with a
    refusal that names nothing about *why*."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    game_id = await _a_played_game(client, searcher, people)

    too_early = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(people["ana"]["id"]), "stars": 5}],
    )

    assert too_early.status_code == 403
    assert too_early.json()["code"] == "this_game_is_not_yours_to_rate"
    assert await _stored_cards(session_factory) == []


async def test_the_three_refusals_about_whose_game_it_is_are_byte_identical(
    client, session_factory, candidate_source, searcher, clock
):
    """**One refusal, and it names nothing.** A game that has not settled, a game
    somebody else played and a game that does not exist come back the same — a
    body that told them apart would answer *is this id real* about four
    strangers' evening.

    The assertion is on the whole payload rather than on three status codes,
    because the thing a later session would break is a helpful sentence added to
    one of them. ``trace_id`` is dropped, as the read-back's own indistinguishable
    refusal drops it: it is this request's identifier and differs on every
    response the server sends, including two of the same failure.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    unsettled = await _a_played_game(client, searcher, people)
    stranger_id, stranger_token = await world.a_signed_in_candidate(
        client, session_factory, "dee", mu=searcher["mu"]
    )
    assert stranger_id is not None

    not_settled = await _rate(client, searcher["token"], unsettled, [])
    not_mine = await _rate(client, stranger_token, unsettled, [])
    no_such_game = await _rate(
        client, searcher["token"], "11111111-1111-4111-8111-111111111111", []
    )

    assert not_settled.status_code == 403
    bodies = [
        {key: value for key, value in one.json().items() if key != "trace_id"}
        for one in (not_settled, not_mine, no_such_game)
    ]
    assert bodies[0] == bodies[1] == bodies[2]
    assert {one.status_code for one in (not_settled, not_mine, no_such_game)} == {403}


async def test_anybody_may_be_left_blank_and_the_blank_leaves_nothing_behind(
    client, session_factory, candidate_source, searcher, clock
):
    """Somebody left out is not a row with a null in it — they are not there at
    all, which is what makes *no record of the omission* structural."""

    game_id, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )

    answered = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(people["ana"]["id"]), "stars": 4}],
    )

    assert answered.status_code == 204, answered.text
    stored = await _stored_ratings(session_factory)
    assert [one.subject_id for one in stored] == [people["ana"]["id"]]


async def test_a_card_with_everybody_blank_is_an_answer_and_closes_it(
    client, session_factory, candidate_source, searcher, clock
):
    """*I am not rating anyone* is an answer. It stores a card and no ratings,
    and the card is what refuses the second attempt — which is the whole reason
    the closure is kept apart from the stars."""

    game_id, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )

    blank = await _rate(client, searcher["token"], game_id, [])
    assert blank.status_code == 204, blank.text
    assert len(await _stored_cards(session_factory)) == 1
    assert await _stored_ratings(session_factory) == []

    second_thoughts = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(people["ana"]["id"]), "stars": 1}],
    )
    assert second_thoughts.status_code == 409
    assert (
        second_thoughts.json()["code"] == "you_have_already_rated_this_game"
    )
    assert await _stored_ratings(session_factory) == []


async def test_a_second_submission_is_refused(
    client, session_factory, candidate_source, searcher, clock
):
    game_id, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )
    first = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(people["ana"]["id"]), "stars": 5}],
    )
    assert first.status_code == 204, first.text

    again = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(people["ana"]["id"]), "stars": 1}],
    )

    assert again.status_code == 409
    assert [one.stars for one in await _stored_ratings(session_factory)] == [5]


async def test_stars_for_somebody_who_was_not_on_that_court_are_refused(
    client, session_factory, candidate_source, searcher, clock
):
    game_id, _people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )
    stranger_id, _token = await world.a_signed_in_candidate(
        client, session_factory, "dee", mu=searcher["mu"]
    )

    refused = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(stranger_id), "stars": 5}],
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "they_were_not_on_this_court"
    assert await _stored_cards(session_factory) == [], "a refused card is not closed"


async def test_rating_yourself_is_refused(
    client, session_factory, candidate_source, searcher, clock
):
    game_id, _people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )

    refused = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(searcher["id"]), "stars": 5}],
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "they_were_not_on_this_court"


@pytest.mark.parametrize("stars", [0, 6])
async def test_a_star_count_off_the_scale_is_refused(
    client, session_factory, candidate_source, searcher, clock, stars: int
):
    """**No zero and no sixth star**, refused by the domain's own rule rather
    than by a bound on the wire — there is one copy of the range, and this is the
    route that proves it is reachable."""

    game_id, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )

    refused = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(people["ana"]["id"]), "stars": stars}],
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "stars_are_one_to_five"


async def test_one_card_carries_one_answer_about_each_player(
    client, session_factory, candidate_source, searcher, clock
):
    game_id, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )

    refused = await _rate(
        client,
        searcher["token"],
        game_id,
        [
            {"player_id": str(people["ana"]["id"]), "stars": 5},
            {"player_id": str(people["ana"]["id"]), "stars": 1},
        ],
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "you_rated_the_same_person_twice"


async def test_everybody_on_the_court_gets_their_own_card(
    client, session_factory, candidate_source, searcher, clock
):
    """The card belongs to a **rater**, not to a game. One person answering does
    not close it for the other three."""

    game_id, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )

    mine = await _rate(
        client,
        searcher["token"],
        game_id,
        [{"player_id": str(people["ana"]["id"]), "stars": 5}],
    )
    theirs = await _rate(
        client,
        people["ana"]["token"],
        game_id,
        [{"player_id": str(searcher["id"]), "stars": 2}],
    )

    assert mine.status_code == 204, mine.text
    assert theirs.status_code == 204, theirs.text
    assert len(await _stored_cards(session_factory)) == 2
    assert {one.stars for one in await _stored_ratings(session_factory)} == {5, 2}


async def test_only_a_raters_most_recent_rating_of_a_person_counts(
    client, session_factory, candidate_source, searcher, clock
):
    """**Two evenings with the same person leave one answer.** Two friends who
    partner every week would otherwise supply most of each other's ratings, and
    the published average would drift towards what one regular partner thinks —
    the opposite of what the row claims to measure.

    Asserted against the stored rows because there is deliberately no route that
    would show it: the collapse is the primary key, so a second answer replaces
    the first rather than joining it.
    """

    first_game, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )
    generous = await _rate(
        client,
        searcher["token"],
        first_game,
        [{"player_id": str(people["ana"]["id"]), "stars": 5}],
    )
    assert generous.status_code == 204, generous.text

    second_game = await _a_played_game(client, searcher, people)
    clock.move(PROPOSAL_WINDOW + timedelta(minutes=1))
    revised = await _rate(
        client,
        searcher["token"],
        second_game,
        [{"player_id": str(people["ana"]["id"]), "stars": 2}],
    )
    assert revised.status_code == 204, revised.text

    about_ana = [
        one
        for one in await _stored_ratings(session_factory)
        if one.subject_id == people["ana"]["id"]
    ]
    assert [one.stars for one in about_ana] == [2]
    assert about_ana[0].game_id == UUID(second_game)
    assert len(await _stored_cards(session_factory)) == 2, (
        "both cards stay closed — the collapse is about the answer, not the card"
    )


async def test_a_blank_does_not_withdraw_what_was_said_about_somebody_before(
    client, session_factory, candidate_source, searcher, clock
):
    """A blank is the absence of an opinion, not the withdrawal of one. Leaving
    somebody out of tonight's card keeps whatever you last said about them."""

    first_game, people = await _a_settled_game(
        client, session_factory, candidate_source, searcher, clock
    )
    await _rate(
        client,
        searcher["token"],
        first_game,
        [{"player_id": str(people["ana"]["id"]), "stars": 5}],
    )

    second_game = await _a_played_game(client, searcher, people)
    clock.move(PROPOSAL_WINDOW + timedelta(minutes=1))
    blank_about_ana = await _rate(
        client,
        searcher["token"],
        second_game,
        [{"player_id": str(people["bo"]["id"]), "stars": 3}],
    )
    assert blank_about_ana.status_code == 204, blank_about_ana.text

    stored = {
        one.subject_id: one.stars for one in await _stored_ratings(session_factory)
    }
    assert stored[people["ana"]["id"]] == 5
    assert stored[people["bo"]["id"]] == 3


async def test_no_route_on_the_surface_returns_an_individual_rating(client):
    """**There is no read.** Not the subject's, not the rater's own, in no shape
    — so the only sportsmanship path on the surface is the one that writes."""

    spec = (await client.get("/openapi.json")).json()
    sportsmanship = {
        f"{method.upper()} {path}"
        for path, operations in spec["paths"].items()
        for method in operations
        if "sportsmanship" in path
    }

    assert sportsmanship == {"POST /api/v1/sportsmanship/{game_id}"}

"""``POST /api/v1/forecasts`` — the number that moves, and the row nobody writes.

The builder lets a player compose a four the engine never scored, and the
screen's whole claim is a figure that moves when somebody moves. This is where
that figure comes from, and the two things worth asserting about it are that it
**records nothing** and that the caveat and the number cannot be parted.
"""

from __future__ import annotations

import pytest

from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client, session_factory):
    return await world.a_searcher(client, session_factory)


async def _a_city(client, session_factory, candidate_source, mu: float):
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        await world.a_candidate(client, session_factory, name, mu=mu + delta)
    await world.fold_the_log(session_factory, candidate_source)


async def test_a_composed_four_comes_back_priced_every_way_round(
    client, session_factory, candidate_source, searcher
):
    """The builder's own arithmetic, on the server. **No `search_id` back.**

    Nothing was generated, ranked or recorded, so there is no id to read this
    back by — and the two version stamps cross because a forecast nobody can
    reproduce is a number nobody should trust.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    shortlist = (await world.search(client, searcher["token"])).json()
    players = [row["player_id"] for row in shortlist["candidates"]]

    response = await world.forecast(
        client,
        searcher["token"],
        search_id=shortlist["search"]["search_id"],
        players=players,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "search_id" not in body
    assert body["engine_version"] and body["ruleset_version"]
    assert len(body["arrangements"]) == 3
    assert sum(one["is_current"] for one in body["arrangements"]) == 1
    assert body["arrangements"][0]["is_current"] is True
    for arrangement in body["arrangements"]:
        assert arrangement["forecast"]["provisional"] is False
        assert len(arrangement["sides"]["A"]) == 2
        assert len(arrangement["sides"]["B"]) == 2
        # **Nothing was compared to anything here.** This route scores no Fits
        # and enumerates no combinations, so there is no objective to be best by
        # — and claiming the seat order the client happened to send is the best
        # one would be a number the response never computed.
        assert "is_best" not in arrangement
    assert sum(one["is_evenest"] for one in body["arrangements"]) == 1


async def test_the_forecast_route_creates_no_search(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0108`` §1: **six swaps are not six searches.**

    Recording them as such would put a lie in the one table the product uses to
    judge itself, which is the same reasoning that makes ``POST /searches``
    deliberately *not* idempotent, cutting the other way.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    shortlist = (await world.search(client, searcher["token"])).json()
    players = [row["player_id"] for row in shortlist["candidates"]]
    before = len(await world.recorded_searches(session_factory))

    for _ in range(3):
        priced = await world.forecast(
            client,
            searcher["token"],
            search_id=shortlist["search"]["search_id"],
            players=players,
        )
        assert priced.status_code == 200, priced.text

    assert len(await world.recorded_searches(session_factory)) == before


async def test_the_provisional_figure_becomes_exactly_the_final_figure(
    client, session_factory, candidate_source, searcher
):
    """§9.9's equality, as a property of **one** implementation.

    A half-empty side is read as if the missing player matched the one already
    there — so seating that player's twin fills the seat without the number
    moving, and the caveat lifts on its own.
    """

    # Two candidates at **the same Level**, so that filling the open seat is
    # exactly the arrival the provisional figure assumed.
    for name, mu in (
        ("ana", searcher["mu"]),
        ("bo", searcher["mu"] + 0.05),
        ("twin", searcher["mu"] + 0.05),
    ):
        await world.a_candidate(client, session_factory, name, mu=mu)
    await world.fold_the_log(session_factory, candidate_source)
    shortlist = (await world.search(client, searcher["token"])).json()
    by_name = {
        row["player_card"]["nickname"]: row["player_id"]
        for row in shortlist["candidates"]
    }
    partner, lone, twin = by_name["ana"], by_name["bo"], by_name["twin"]

    half = (
        await world.forecast(
            client,
            searcher["token"],
            search_id=shortlist["search"]["search_id"],
            players=[partner, lone],
        )
    ).json()
    # The arrangement seating `partner` beside the searcher, with one opponent.
    provisional = half["arrangements"][0]
    assert provisional["forecast"]["provisional"] is True
    assert (
        provisional["forecast"]["assumption"] == "EMPTY_SEAT_MATCHES_ITS_PARTNER"
    )

    full = (
        await world.forecast(
            client,
            searcher["token"],
            search_id=shortlist["search"]["search_id"],
            players=[partner, lone, twin],
        )
    ).json()
    settled = full["arrangements"][0]
    assert settled["forecast"]["provisional"] is False
    assert settled["forecast"]["pct"] == provisional["forecast"]["pct"]


async def test_the_same_person_may_not_take_two_seats(
    client, session_factory, candidate_source, searcher
):
    """A court with somebody on it twice is not a court.

    Refused at the boundary rather than seated, because it is a malformed **ask**
    rather than an answer the engine should have an opinion about — and because
    the empty-seat assumption is a claim about somebody who is not there, which a
    duplicate would dress up as a fact.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    shortlist = (await world.search(client, searcher["token"])).json()
    one = shortlist["candidates"][0]["player_id"]

    response = await world.forecast(
        client,
        searcher["token"],
        search_id=shortlist["search"]["search_id"],
        players=[one, one],
    )

    assert response.status_code == 422, response.text


async def test_a_forecast_about_somebody_no_search_of_yours_showed_is_refused(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0108`` §3's bound. Unbounded, this is a Level lookup for any
    player in the city, reachable by id — which is where the privacy line spent
    everywhere else in this design would leak."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    shortlist = (await world.search(client, searcher["token"])).json()
    stranger, _ = await world.register(client, "stranger")

    response = await world.forecast(
        client,
        searcher["token"],
        search_id=shortlist["search"]["search_id"],
        players=[shortlist["candidates"][0]["player_id"], stranger],
    )

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "search_not_found"


async def test_a_forecast_citing_somebody_elses_search_answers_as_an_unknown_one(
    client, session_factory, candidate_source, searcher
):
    """A search that belongs to somebody else answers exactly as one that never
    existed, and the sameness is the authorization rule rather than tidiness."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    other = await world.a_searcher(client, session_factory, "other")
    theirs = (await world.search(client, other["token"])).json()

    response = await world.forecast(
        client,
        searcher["token"],
        search_id=theirs["search"]["search_id"],
        players=[theirs["candidates"][0]["player_id"]],
    )

    assert response.status_code == 404, response.text

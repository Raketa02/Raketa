"""``POST /api/v1/lineups`` — the four, the arrangements, and the honest partial.

Every assertion lands on HTTP, through the same in-memory client the shortlist's
suite uses. What is asserted is the product's promises: that a four comes back
seated with a forecast per arrangement before anybody has been asked, that a seat
is never filled below the floor to complete one, that every gate binds all six
pairs, and that the objective which chose the four never crosses as a number.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from sqlalchemy import select

from app.bootstrap.composition import build_clock
from app.modules.matchmaking.domain.ledgers import week_of
from app.modules.matchmaking.infrastructure.search_model import SearchORM
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _a_city(client, session_factory, candidate_source, mu: float):
    """Four candidates, which is one more than a four needs.

    Deliberately four rather than three: with exactly three there is one
    admissible combination, nothing was beaten, and a line-up that named a
    deciding term would be explaining an argument it never had.
    """

    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05), ("dee", 0.10)):
        await world.a_candidate(client, session_factory, name, mu=mu + delta)
    await world.fold_the_log(session_factory, candidate_source)


async def test_a_lineup_seats_a_four_with_every_arrangement_and_a_reason(
    client, session_factory, candidate_source, searcher
):
    """⚡ *Fill the seats.* A seated four, priced, before anybody has been asked.

    All three arrangements cross with a forecast each, so *Even it out* is a
    **selection** the player makes rather than a request they send — and the two
    booleans are separate, because the new fact the builder can state is that
    they differ.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    response = await world.lineup(client, searcher["token"])

    assert response.status_code == 200, response.text
    body = response.json()
    lineup = body["lineup"]
    assert [seat["relationship"] for seat in lineup["seats"]] == [
        "SELF",
        "PARTNER",
        "OPPONENT",
        "OPPONENT",
    ]
    assert [seat["side"] for seat in lineup["seats"]] == ["A", "A", "B", "B"]
    assert all("unfilled_reason" not in seat for seat in lineup["seats"])
    assert len(lineup["arrangements"]) == 3
    for arrangement in lineup["arrangements"]:
        forecast = arrangement["forecast"]
        assert 0 <= forecast["pct"] <= 100
        assert forecast["provisional"] is False
        assert forecast["assumption"] is None
        assert len(arrangement["sides"]["A"]) == 2
        assert len(arrangement["sides"]["B"]) == 2
    assert sum(one["is_best"] for one in lineup["arrangements"]) == 1
    assert sum(one["is_evenest"] for one in lineup["arrangements"]) == 1
    assert lineup["group_reason"] in {
        "EVENEST_ARRANGEMENT",
        "STRONGEST_WEAKEST_SEAT",
        "BEST_AVERAGE_FIT",
        "MOST_SHARED_SLOTS",
        "GROUP_RAPPORT",
    }
    assert body["search"]["optimised_for"] == "SEARCHER"


async def test_the_split_is_the_evidence_behind_the_percentage(
    client, session_factory, candidate_source, searcher
):
    """*90% - very even* says how even; the split says **between what and what.**

    Four views of one computation, on the scale players already read levels on.
    A card reading ``gap 0,00`` beside ``74%`` is the failure this exists to
    prevent, so the three numbers are asserted against each other and against
    the percent they were read from — and the gap is **served** rather than left
    to a subtraction, because a client subtracting two rounded figures and an
    engine subtracting two unrounded ones disagree at the boundary.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    lineup = (await world.lineup(client, searcher["token"])).json()["lineup"]

    for arrangement in lineup["arrangements"]:
        split = arrangement["split"]
        assert split["gap"] == pytest.approx(
            split["your_side"] - split["their_side"]
        )
    # The evenest of the three is the one closest to nought, and it carries the
    # highest percent: `pct` and the split cannot point at different arrangements.
    evenest = next(
        one for one in lineup["arrangements"] if one["is_evenest"]
    )
    assert abs(evenest["split"]["gap"]) == min(
        abs(one["split"]["gap"]) for one in lineup["arrangements"]
    )
    assert evenest["forecast"]["pct"] == max(
        one["forecast"]["pct"] for one in lineup["arrangements"]
    )


async def test_a_line_up_opens_on_the_evenest_arrangement(
    client, session_factory, candidate_source, searcher
):
    """**Who is on the court does not change; which way round they sit does.**

    The group objective still chose the four and ``group_reason`` still says
    why. What the builder opens on is the closest game of the three — the same
    re-seating *Even it out* already performs by hand — and ``lineup.seats``
    follows ``is_current``, so the seating in the response is that seating.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    body = (await world.lineup(client, searcher["token"])).json()
    lineup = body["lineup"]

    current = next(one for one in lineup["arrangements"] if one["is_current"])
    assert current["is_evenest"] is True
    assert sum(one["is_current"] for one in lineup["arrangements"]) == 1
    # `is_best` is untouched and still crosses, and the two may differ.
    assert sum(one["is_best"] for one in lineup["arrangements"]) == 1
    assert lineup["group_reason"]

    # `lineup.seats` follows `is_current`, seat for seat.
    def _who(seats):
        return {seat["seat_index"]: seat.get("player_id") for seat in seats}

    assert _who(lineup["seats"]) == _who(
        current["sides"]["A"] + current["sides"]["B"]
    )


async def test_a_line_up_opens_on_the_evenest_arrangement_when_filling_seats(
    client, session_factory, candidate_source, searcher
):
    """The same in both modes. Hand-seating somebody changes who, never which
    way round the four is drawn."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    shortlist = (await world.search(client, searcher["token"])).json()

    body = (
        await world.lineup(
            client,
            searcher["token"],
            locked_seats=[shortlist["candidates"][0]["player_id"]],
        )
    ).json()

    assert body["search"]["optimised_for"] == "GROUP"
    current = next(
        one for one in body["lineup"]["arrangements"] if one["is_current"]
    )
    assert current["is_evenest"] is True


async def test_a_provisional_arrangement_carries_a_split_like_any_other(
    client, session_factory, candidate_source, searcher
):
    """One caveat over all four numbers, or over none of them.

    The empty seat is read as if the missing player matched the one already
    there — exactly as ``pct`` already is — and ``provisional`` goes on carrying
    that for the whole arrangement rather than for the percent alone.
    """

    for name, delta in (("ana", 0.0), ("bo", 0.05)):
        await world.a_candidate(
            client, session_factory, name, mu=searcher["mu"] + delta
        )
    await world.fold_the_log(session_factory, candidate_source)

    lineup = (await world.lineup(client, searcher["token"])).json()["lineup"]

    for arrangement in lineup["arrangements"]:
        assert arrangement["forecast"]["provisional"] is True
        split = arrangement["split"]
        assert split["gap"] == pytest.approx(
            split["your_side"] - split["their_side"]
        )


async def test_a_line_up_asks_about_the_week_it_was_given(
    client, session_factory, candidate_source, searcher
):
    """**⚡ consumed the improvised week, so ⚡ asks about it.**

    A line-up already holds both grids — the one it ran on and the one on the
    profile — so the question is free here exactly as it is on a shortlist, and
    the sheet rides on the response of the route that used the week.
    """

    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05), ("dee", 0.10)):
        await world.a_candidate(
            client,
            session_factory,
            name,
            mu=searcher["mu"] + delta,
            availability=("4:19",),
        )
    await world.fold_the_log(session_factory, candidate_source)

    built = await world.lineup(
        client,
        searcher["token"],
        availability_override=[{"day": 4, "hour": 19}],
    )

    assert built.status_code == 200, built.text
    prompts = {
        prompt["prompt"]: prompt for prompt in built.json()["search"]["prompts"]
    }
    assert prompts["KEEP_THESE_TIMES"]["slots"] == [{"day": 4, "hour": 19}]
    assert await world.saved_grid(session_factory, searcher["id"]) == (
        "2:19",
        "6:10",
    ), "the profile is untouched"


async def test_a_line_up_on_a_cleared_week_seats_a_four(
    client, session_factory, candidate_source, searcher
):
    """The builder refused a blank grid with a `400` on the commit path's floor,
    one layer past where that floor's own docstring puts it."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    built = await world.lineup(
        client, searcher["token"], availability_override=[]
    )

    assert built.status_code == 200, built.text
    prompts = {
        prompt["prompt"]: prompt for prompt in built.json()["search"]["prompts"]
    }
    assert prompts["KEEP_THESE_TIMES"]["slots"] == []


async def test_a_line_up_on_the_profiles_own_week_asks_nothing(
    client, session_factory, candidate_source, searcher
):
    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    built = await world.lineup(client, searcher["token"])

    assert built.json()["search"]["prompts"] == []


async def test_the_objective_never_crosses_as_a_number(
    client, session_factory, candidate_source, searcher
):
    """``G`` chose these four and is **recorded, never returned.**

    A second score the player must trust is worse than none: it competes with Fit
    and nobody can act on it. What pays the evidence half is one closed reason
    code, and this asserts that nothing anywhere in the payload is the objective
    wearing another name.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    body = (await world.lineup(client, searcher["token"])).json()

    flat = _keys(body)
    for name in ("objective", "g", "group_score", "side_gap", "rank_key"):
        assert name not in flat, f"the objective reached the wire as {name!r}"


def _keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key for nested in value.values() for key in _keys(nested)
        }
    if isinstance(value, list):
        return {key for nested in value for key in _keys(nested)}
    return set()


async def test_a_seated_card_shows_the_number_the_shortlist_showed(
    client, session_factory, candidate_source, searcher
):
    """**Nothing is re-scored behind the player's back.**

    The card said 78 in the shortlist and it says 78 in the builder. The seat
    delta enters the objective and the line-up's reasons; it never enters a Fit.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    shortlist = (await world.search(client, searcher["token"])).json()
    seated = (await world.lineup(client, searcher["token"])).json()

    shown = {row["player_id"]: row["fit"] for row in shortlist["candidates"]}
    for row in seated["candidates"]:
        assert row["fit"] == shown[row["player_id"]]


async def test_hand_seating_somebody_says_it_is_now_optimising_for_the_group(
    client, session_factory, candidate_source, searcher
):
    """§8.4: with a seat locked the searcher may get a worse individual match.

    The screen has to say so rather than let it be discovered, and *line-up and
    fill-seats differ only by locked seats* — the same route, the same shape.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    shortlist = (await world.search(client, searcher["token"])).json()
    chosen = shortlist["candidates"][-1]["player_id"]

    response = await world.lineup(client, searcher["token"], locked_seats=[chosen])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["search"]["optimised_for"] == "GROUP"
    assert body["search"]["surface"] == "FILL_SEATS"
    seated = {
        seat["player_id"] for seat in body["lineup"]["seats"] if "player_id" in seat
    }
    assert chosen in seated, "the person the searcher seated is not on the court"


async def test_three_of_four_is_a_200_with_a_reason_and_a_provisional_forecast(
    client, session_factory, candidate_source, searcher
):
    """A four can be impossible where candidates are plentiful, and that is a
    partial line-up rather than an error.

    The forecast on a court with an open seat is **provisional**, and it names
    what it assumed — a half-empty side read as if the missing player matched the
    one already there.
    """

    for name, delta in (("ana", 0.0), ("bo", 0.05)):
        await world.a_candidate(
            client, session_factory, name, mu=searcher["mu"] + delta
        )
    await world.fold_the_log(session_factory, candidate_source)

    response = await world.lineup(client, searcher["token"])

    assert response.status_code == 200, response.text
    lineup = response.json()["lineup"]
    open_seats = [
        seat for seat in lineup["seats"] if "unfilled_reason" in seat
    ]
    assert len(open_seats) == 1
    assert open_seats[0]["unfilled_reason"] == "POOL_EXHAUSTED"
    for arrangement in lineup["arrangements"]:
        assert arrangement["forecast"]["provisional"] is True
        assert (
            arrangement["forecast"]["assumption"]
            == "EMPTY_SEAT_MATCHES_ITS_PARTNER"
        )
        assert "is_best" not in arrangement, (
            "an incomplete four has no objective, so there is nothing to be "
            "best by"
        )
    assert sum(one["is_evenest"] for one in lineup["arrangements"]) == 1
    assert "group_reason" not in lineup, "nothing was beaten, so nothing decided"


async def test_nobody_is_the_same_shape_with_every_seat_carrying_a_reason(
    client, session_factory, candidate_source, searcher
):
    """***Nobody* is not a different shape from *three of four*.**

    There is no separate empty state for a line-up: the same court comes back
    with three seats open and a reason on each, so a client renders one thing.
    """

    await world.fold_the_log(session_factory, candidate_source)

    response = await world.lineup(client, searcher["token"])

    assert response.status_code == 200, response.text
    lineup = response.json()["lineup"]
    assert len(lineup["seats"]) == 4
    assert [seat.get("unfilled_reason") for seat in lineup["seats"][1:]] == [
        "POOL_EXHAUSTED"
    ] * 3
    assert lineup["arrangements"] == []


async def test_a_pool_nobody_clears_reads_as_the_floor_and_never_as_an_empty_city(
    client, session_factory, candidate_source, searcher
):
    """**The four codes are four different sentences, and this is the second.**

    There were people. Not one of them was somebody this engine would seat, and
    *nobody good enough* is an answer the floor has to be able to give — a seat
    is never filled below it to complete a four. A screen that read this as an
    empty city would tell the player to widen a radius that is not the problem.
    """

    for name in ("ana", "bo", "cy"):
        await world.a_candidate(
            client,
            session_factory,
            name,
            mu=searcher["mu"] + 0.35,
            tags=world.SOCIABLE_TAGS,
            availability=("4:10",),
            intent="FOR_FUN",
        )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.lineup(client, searcher["token"])).json()

    lineup = body["lineup"]
    assert body["search"]["pool"]["players_in_range"] > 0, "there was nobody to fail"
    assert [seat.get("unfilled_reason") for seat in lineup["seats"][1:]] == [
        "NO_CANDIDATE_ABOVE_FLOOR"
    ] * 3


async def test_a_court_no_four_can_share_says_so_rather_than_saying_nobody(
    client, session_factory, candidate_source, searcher
):
    """**The code ``docs/adr/0116`` added, all the way out to a seat.**

    Three people the searcher can see and would happily play, and a block between
    two of them: every pair with the searcher is admissible, and the six-pair gate
    is what the court runs out of. Without this code on the seat the gate is
    indistinguishable from a thin pool on the screen, and the two want opposite
    things from the player.
    """

    one, one_token = await world.a_signed_in_candidate(
        client, session_factory, "ana", mu=searcher["mu"]
    )
    other = await world.a_candidate(
        client, session_factory, "bo", mu=searcher["mu"] + 0.05
    )
    await world.a_candidate(client, session_factory, "cy", mu=searcher["mu"] - 0.05)
    await world.fold_the_log(session_factory, candidate_source)
    blocked = await world.block_between(client, one_token, other)
    assert blocked.status_code == 204, blocked.text

    body = (await world.lineup(client, searcher["token"])).json()

    lineup = body["lineup"]
    assert body["search"]["pool"]["players_in_range"] == 3, (
        "a block between two candidates takes neither off the searcher's list"
    )
    open_seats = [seat for seat in lineup["seats"] if "unfilled_reason" in seat]
    assert [seat["unfilled_reason"] for seat in open_seats] == [
        "NO_ADMISSIBLE_COMBINATION"
    ], "there were people left over, and none of them could share this court"
    seated = {seat.get("player_id") for seat in lineup["seats"]}
    assert not {str(one), str(other)} <= seated, (
        "the two who blocked each other are on one court"
    )


async def test_a_four_with_no_hour_in_common_is_docked_and_nobody_leaves_the_court(
    client, session_factory, candidate_source, searcher
):
    """**The fourth code, and the only one that is not about a seat.**

    Three good pairwise overlaps do not make a four-way one: each of them shares
    an hour with the searcher and there is no hour all four share. That is a
    **dock**, never a refusal — the court stays full, the honest line is that
    everybody would have to bend, and the times rung relaxes exactly these cells.
    """

    for name, slots in (
        ("ana", ("2:19",)),
        ("bo", ("6:10",)),
        ("cy", ("2:19",)),
    ):
        await world.a_candidate(
            client,
            session_factory,
            name,
            mu=searcher["mu"],
            availability=slots,
        )
    await world.fold_the_log(session_factory, candidate_source)

    lineup = (await world.lineup(client, searcher["token"])).json()["lineup"]

    assert all("unfilled_reason" not in seat for seat in lineup["seats"]), (
        "a dock removes nobody from the court"
    )
    assert lineup["dock"] == "NO_SHARED_SLOTS"


async def test_a_seat_is_never_filled_below_the_floor_to_complete_a_four(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0099``: **a newcomer least of all.**

    Two good candidates and one nobody would seat gives *three of four*, not a
    four with somebody who should not be on the court.
    """

    for name, delta in (("ana", 0.0), ("bo", 0.05)):
        await world.a_candidate(
            client, session_factory, name, mu=searcher["mu"] + delta
        )
    # Far away, no shared slot and the opposite temperament: a real pairing this
    # engine has already decided not to show, and the floor is what says so.
    await world.a_candidate(
        client,
        session_factory,
        "poor",
        mu=searcher["mu"] + 0.4,
        latitude=51.60,
        tags=world.SOCIABLE_TAGS,
        availability=("4:10",),
        intent="FOR_FUN",
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.lineup(client, searcher["token"])).json()

    cards = {
        row["player_id"]: row["player_card"]["name"]
        for row in body["candidates"]
    }
    seated = {
        cards[seat["player_id"]]
        for seat in body["lineup"]["seats"]
        if "player_id" in seat and seat["player_id"] in cards
    }
    assert "poor" not in seated


async def test_the_relaxation_ladder_does_not_reach_the_court_either(
    client, session_factory, candidate_source, searcher
):
    """**The ladder ships on ``POST /searches`` alone**, and now in code.

    A line-up may *take* a rung — the workbench reads what one search was asked
    for, and both surfaces ask the same way — but it never **prices** one. So its
    record carries `null`, which is *the offers were not computed at all* and is
    the truth here, and a search citing a line-up for a rung is refused by the
    code a widening nobody offered gets.
    """

    await world.fold_the_log(session_factory, candidate_source)
    built = (await world.lineup(client, searcher["token"])).json()

    assert built["search"]["rung_offers"] is None, "a court prices no rung"

    refused = await world.search(
        client,
        searcher["token"],
        offered_by_search_id=built["search"]["search_id"],
        rung="B",
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "rung_offer_not_found"


async def test_the_line_up_records_layer_four_and_no_route_returns_it(
    client, session_factory, candidate_source, searcher
):
    """**Two rows, not two thousand**, and engine-internal like layer 3.

    The winning combination and the runner-up are what the deciding margin is
    computed from; without them ADR-0116's gate is unfalsifiable and the reason
    code is unreproducible.

    **And who sat down**, since the returned band became the pool
    ([#407](https://github.com/Raketa02/Raketa/issues/407)): a complete four's
    seated are the winner's members, but a partial line-up and a singles court
    record no winner, and a search-time fact the record used to hold is not one
    it may lose.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    body = (await world.lineup(client, searcher["token"])).json()

    assert "lineup" not in body["search"], "layer 4 reached the wire"
    async with session_factory() as session:
        rows = await session.execute(select(SearchORM))
        recorded = [row for row in rows.scalars() if row.surface == "LINEUP"]
    assert len(recorded) == 1
    layer_four = recorded[0].lineup
    assert layer_four is not None
    assert layer_four["combinations"] >= 1
    assert layer_four["refused_by_gate"] >= 0
    assert layer_four["max_fit_rank_seated"] >= 1
    assert [row["band"] for row in layer_four["rows"]][:1] == ["WINNER"]
    assert all(row["terms"] for row in layer_four["rows"])
    assert len(layer_four["rows"]) <= 2
    assert set(layer_four["seated"]) == {
        seat["player_id"]
        for seat in body["lineup"]["seats"]
        if seat["relationship"] != "SELF"
    }, "layer 4 does not say who sat down"


async def test_a_locked_seat_the_gates_no_longer_admit_is_refused_not_replaced(
    client, session_factory, candidate_source, searcher
):
    """A four that came back **without** the person the searcher put in it, with
    somebody else there instead, is the builder lying about what it was asked.

    It names nobody, for the reason a withheld row names no gate.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    stranger, _ = await world.register(client, "stranger")

    response = await world.lineup(
        client, searcher["token"], locked_seats=[stranger]
    )

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "locked_seat_not_available"


async def test_two_hand_seated_players_who_blocked_each_other_are_refused(
    client, session_factory, candidate_source, searcher
):
    """**Hand-seating is not a way past a gate** (``docs/adr/0116``).

    Both are people this search can still see — a block between two candidates
    takes neither of them off the searcher's shortlist — and what they cannot do
    is see **each other**. The refusal names nobody, for the reason a withheld
    row names no gate: saying *which two* would tell the searcher that one of
    them blocked the other.
    """

    one, one_token = await world.a_signed_in_candidate(
        client, session_factory, "ana", mu=searcher["mu"]
    )
    other = await world.a_candidate(
        client, session_factory, "bo", mu=searcher["mu"] + 0.05
    )
    await world.a_candidate(
        client, session_factory, "cy", mu=searcher["mu"] - 0.05
    )
    await world.fold_the_log(session_factory, candidate_source)
    blocked = await world.block_between(client, one_token, other)
    assert blocked.status_code == 204, blocked.text

    response = await world.lineup(
        client, searcher["token"], locked_seats=[one, other]
    )

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "locked_seat_not_available"


async def test_a_court_with_the_same_person_twice_is_refused_at_the_boundary(
    client, session_factory, candidate_source, searcher
):
    """A malformed **ask**, refused where asks are checked — not inside, where it
    would surface as a `503` about the platform for a mistake in the request."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    shortlist = (await world.search(client, searcher["token"])).json()
    one = shortlist["candidates"][0]["player_id"]

    response = await world.lineup(client, searcher["token"], locked_seats=[one, one])

    assert response.status_code == 422, response.text


async def test_a_line_up_reads_back_through_the_record_it_wrote(
    client, session_factory, candidate_source, searcher
):
    """``GET /searches/{id}`` reaches a line-up too, and the gates are re-run.

    The record is the answer's identity on every surface, so the pool the four
    were drawn from comes back the way it was shown — and **layer 4 comes back
    with it, into the record and no further**: the read-back renders the rows,
    and there is no field on any response for a combination to arrive in.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    seated = (await world.lineup(client, searcher["token"])).json()
    search_id = seated["search"]["search_id"]

    response = await client.get(
        f"/api/v1/searches/{search_id}", headers=world.auth(searcher["token"])
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["search"]["surface"] == "LINEUP"
    assert [row["player_id"] for row in body["candidates"]] == [
        row["player_id"] for row in seated["candidates"]
    ]
    assert all(row["withheld"] is False for row in body["candidates"])
    # **The court itself does not survive the round trip, and that is a stated
    # gap rather than an oversight.** `the-two-contracts.md` §1 asks for the same
    # schema either way; reproducing the seating needs a second stored shape —
    # *what was shown*, beside layer 4's *what was compared*, which no route may
    # return. Asserted here so the gap stays visible instead of being discovered
    # by a client that drew an empty court.
    assert "lineup" not in body, (
        "the read-back grew a court; the gap this asserts has been closed and "
        "the spec amendment should say so"
    )
    assert "lineup" not in body["search"], "layer 4 reached the wire"


async def test_a_seated_card_carries_its_photograph_like_any_other(
    client, session_factory, candidate_source, searcher
):
    """**The same rows, in the same shape, on every surface.**

    A line-up's returned band is the pool it seated from, rendered through the
    one function a shortlist and a deal go through — so a photograph that
    reached one surface and not this one would mean the link had been wired per
    route rather than per renderer.
    """

    photo = uuid4()
    seated = await world.a_candidate(
        client, session_factory, "ana", mu=searcher["mu"], photo_ids=(photo,)
    )
    for name, delta in (("bo", 0.05), ("cy", -0.05)):
        await world.a_candidate(
            client, session_factory, name, mu=searcher["mu"] + delta
        )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.lineup(client, searcher["token"])).json()

    cards = {
        row["player_id"]: row["player_card"] for row in body["candidates"]
    }
    assert cards[str(seated)]["photo_id"] == str(photo)
    assert cards[str(seated)]["photo_url"].endswith(f"{seated}/{photo}")
    assert all(
        "photo_url" not in card
        for player_id, card in cards.items()
        if player_id != str(seated)
    ), "a player with no photo was handed a link to one"


async def test_a_line_up_returns_the_pool_it_seated_from(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**A court is its answer, and the answer carries the pool it was drawn from.**

    Four candidates and three seats: the fourth is not on the court and is still
    a row, because ``candidates[]`` is the pool ⚡ seated from — the top rows by
    Fit, the seated among them — and not the seated alone
    ([#407](https://github.com/Raketa02/Raketa/issues/407)). A pool opened on
    this record therefore has somebody to offer, and a forecast or a send citing
    it may name anybody on it.

    **Exposure counts the seated only.** The court is what was shown; the pool
    behind it is shown only if the player opens it, and counting what may never
    be opened would sink two dozen people per ⚡.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])

    body = (await world.lineup(client, searcher["token"])).json()

    seated = {
        seat["player_id"]
        for seat in body["lineup"]["seats"]
        if seat["relationship"] != "SELF"
    }
    rows = [row["player_id"] for row in body["candidates"]]
    assert len(seated) == 3
    assert len(rows) == 4, "the record holds the seated alone, not the pool"
    assert seated < set(rows), "somebody sat down who is not a row of the answer"
    fits = [row["fit"] for row in body["candidates"]]
    assert fits == sorted(fits, reverse=True), "the pool is in Fit order"
    shown = await exposure_ledger.times_shown(
        sport=world.SPORT,
        week=week_of(build_clock().now()),
        player_ids=[UUID(player_id) for player_id in rows],
    )
    assert {str(player_id): count for player_id, count in shown.items()} == {
        player_id: (1 if player_id in seated else 0) for player_id in rows
    }, "⚡ counted the whole pool as shown"

"""*Nobody tonight* — the offers, the citation, and the profile left alone.

In a city with eleven players the honest answer is often nobody, and the player
has to be told plainly, told what would change it, and never handed a bad match
dressed up as a good one (``docs/adr/0099``). Over HTTP, that is four claims:

- the envelope carries **rung offers with real counts** when the shortlist came
  back short, and carries ``null`` — *not computed* — when it did not;
- a rung is taken by running **a new search citing the one that offered it**, and
  the searcher's saved radius and week are exactly where they were afterwards;
- a widening the engine never offered is **refused**, because the radius is read
  off the offer and never off the request;
- and the questions the platform asks — *keep these times?*, *keep this radius?*
  — ship with the search and change nothing until they are answered.
"""

from __future__ import annotations

import pytest

from app.modules.matchmaking.domain.prompts import REPEATED_WIDENINGS
from tests.api import matchmaking_world as world

#: Eleven kilometres north of the centre: outside a ten-kilometre ring and
#: inside ×1.5 of it, which is the whole of what a radius rung is worth.
JUST_PAST_THE_RING = 51.61

#: An evening the searcher has not ticked. ``commit_profile`` gives them Tuesday
#: evening and Saturday morning.
ANOTHER_EVENING = ("4:EVENING",)

#: Tags on the other side of both splits from ``COMPETITIVE_TAGS``, which is
#: what makes a candidate cost a for-fun search enough points that their week is
#: decisive.
AN_OPPOSITE_EVENING_OUT = ("STRAIGHT_HOME_AFTER", "QUIET_AND_FOCUSED")


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def test_a_short_shortlist_carries_what_widening_would_be_worth(
    client, session_factory, candidate_source, searcher
):
    """**The engine offers; it never takes the offer for the player.**

    The list comes back with the one person inside the ring, and beside it the
    two radius rungs with the count each would really produce — from a re-run,
    not from an estimate.
    """

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.a_candidate(
        client,
        session_factory,
        "past-the-ring",
        mu=searcher["mu"],
        latitude=JUST_PAST_THE_RING,
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, searcher["token"])).json()

    assert len(body["candidates"]) == 1, "only the one inside the ring is shown"
    offers = {offer["rung"]: offer for offer in body["search"]["rung_offers"]}
    assert set(offers) == {"B", "C"}
    assert offers["B"]["ask"] == "RADIUS"
    assert offers["B"]["radius_km"] == 15
    assert offers["C"]["radius_km"] == 20
    assert offers["B"]["candidates_above_floor"] == 2
    # Its own window, beside the count: a challenge sliding from one window to
    # another is part of what widening costs.
    assert offers["B"]["window"] == body["search"]["pool"]["window"]
    assert "slot" not in offers["B"], "a radius rung has no slot, rather than none"


async def test_a_times_rung_names_its_cell_in_the_two_fields_a_grid_is_drawn_from(
    client, session_factory, candidate_source, searcher
):
    """**The offered cell crosses as a day and a part of the day, never joined.**

    The client has to draw that cell on its own seven-by-three grid, marked as
    belonging to this one search (#283) — and that is the same grid every other
    slot is drawn on, from ``AvailabilitySlotResource``. A joined ``"4:EVENING"``
    here would make the one cell the player never ticked the one cell whose
    client had to split our persistence format, which the resource one schema
    over refuses by name.

    The scene is the honest way to earn a times rung: an evening asked for
    alone, and the one person in range free on a different one — near enough on
    level, far enough on everything a for-fun evening weighs that the empty week
    is what keeps them off the list.
    """

    await world.a_candidate(
        client,
        session_factory,
        "thursday",
        mu=searcher["mu"],
        availability=ANOTHER_EVENING,
        tags=AN_OPPOSITE_EVENING_OUT,
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (
        await world.search(
            client,
            searcher["token"],
            "FOR_FUN",
            availability_override=[{"day": 2, "part": "EVENING"}],
        )
    ).json()

    assert body["candidates"] == [], "somebody cleared the bar; this proves nothing"
    offers = {offer["rung"]: offer for offer in body["search"]["rung_offers"]}
    assert offers["A"]["ask"] == "TIMES"
    assert offers["A"]["candidates_above_floor"] == 1
    assert offers["A"]["slot"] == {"day": 4, "part": "EVENING"}
    assert "radius_km" not in offers["A"], (
        "a times rung has no radius, rather than a radius of nothing"
    )


async def test_a_long_enough_shortlist_computes_no_offers_at_all(
    client, session_factory, candidate_source, searcher
):
    """``MIN_SHORTLIST`` decides **only whether the offers are computed**.

    ``null`` and an empty list are different answers, and the difference is the
    constant's own falsifier: *were they even computed* is read off these rows.
    """

    for index in range(6):
        await world.a_candidate(
            client, session_factory, f"player-{index}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, searcher["token"])).json()

    assert len(body["candidates"]) == 6
    assert body["search"]["rung_offers"] is None
    assert body["search"]["radius_clamp"] is False


async def test_a_searcher_at_the_ceiling_is_offered_no_radius_rung_and_says_so(
    client, session_factory, candidate_source
):
    """**Never an offer that cannot happen.** A relaxation may not offer a radius
    the player could not have set for themselves, so the searcher already at the
    slider's maximum gets the honest empty state sooner — and the clamp bit is
    what counts how many of them there are."""

    player_id, token = await world.register(client, "at-the-ceiling")
    await world.commit_profile(client, token, search_radius_km=50)
    await world.rate(client, token)
    await world.declare_intent(client, token)
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, token)).json()

    assert body["candidates"] == []
    assert body["search"]["rung_offers"] == []
    assert body["search"]["radius_clamp"] is True
    # The pool is described rather than narrated, and post-gate: there is no
    # pre-gate count beside it for a delta to be read off.
    assert body["search"]["pool"]["post_gate"] is True
    assert body["search"]["pool"]["players_in_range"] == 0


async def test_the_clamp_bit_counts_a_searcher_at_the_ceiling_on_every_search(
    client, session_factory, candidate_source
):
    """The bit's job is to count the searchers already at the slider's maximum.

    A long shortlist means the offers were never computed — and recording
    ``false`` for a 50 km searcher because nobody needed a rung would undercount
    the exact population the column exists to find.
    """

    player_id, token = await world.register(client, "busy-at-the-ceiling")
    await world.commit_profile(client, token, search_radius_km=50)
    mu = await world.rate(client, token)
    await world.declare_intent(client, token)
    for index in range(6):
        await world.a_candidate(client, session_factory, f"player-{index}", mu=mu)
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, token)).json()

    assert len(body["candidates"]) == 6
    assert body["search"]["rung_offers"] is None, "nobody needed a rung"
    assert body["search"]["radius_clamp"] is True, "they are still at the ceiling"


async def test_taking_a_rung_is_a_new_search_citing_the_one_that_offered_it(
    client, session_factory, candidate_source, searcher
):
    """**Never a silent profile edit.** The widened search finds the person past
    the ring, and the searcher's saved radius is exactly where they left it."""

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.a_candidate(
        client,
        session_factory,
        "past-the-ring",
        mu=searcher["mu"],
        latitude=JUST_PAST_THE_RING,
    )
    await world.fold_the_log(session_factory, candidate_source)
    offered = (await world.search(client, searcher["token"])).json()

    widened = await world.search(
        client,
        searcher["token"],
        offered_by_search_id=offered["search"]["search_id"],
        rung="B",
    )

    assert widened.status_code == 200, widened.text
    body = widened.json()
    assert len(body["candidates"]) == 2
    assert body["search"]["pool"]["radius_km_used"] == 15
    assert body["search"]["search_id"] != offered["search"]["search_id"]

    assert await world.saved_radius_km(session_factory, searcher["id"]) == 10, (
        "the widen was for one search"
    )


async def test_the_pair_that_makes_take_up_a_join_is_recorded(
    client, session_factory, candidate_source, searcher
):
    """The offering search and the accepting one are two rows, and the second
    names the first. A flag on one row could not answer *what was offered, and
    what did the same person do next*."""

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    offered = (await world.search(client, searcher["token"])).json()

    await world.search(
        client,
        searcher["token"],
        offered_by_search_id=offered["search"]["search_id"],
        rung="B",
    )

    rows = await world.recorded_searches(session_factory)
    offering, accepting = rows
    assert offering.rung_offers, "the offer is on the row that made it"
    assert offering.rung_taken is None and offering.offered_by_search_id is None
    assert accepting.rung_taken == "B"
    assert accepting.offered_by_search_id == offering.id


async def test_a_taken_rung_prices_no_second_climb(
    client, session_factory, candidate_source, searcher
):
    """**One climb per search screen.** The ladder does not chain.

    The widened radius *is* the searcher's radius by the time the ladder would be
    priced, so a rung offered here would be a rung off the widening — and four
    taps from 8 km would land on the 50 km ceiling without the player being asked
    once. The widened list is still short and still carries no offer, which is
    the honest empty state arriving one climb in rather than four.
    """

    await world.a_candidate(
        client,
        session_factory,
        "past-the-ring",
        mu=searcher["mu"],
        latitude=JUST_PAST_THE_RING,
    )
    await world.fold_the_log(session_factory, candidate_source)
    offered = (await world.search(client, searcher["token"])).json()
    assert {one["rung"] for one in offered["search"]["rung_offers"]} >= {"B", "C"}

    widened = (
        await world.search(
            client,
            searcher["token"],
            offered_by_search_id=offered["search"]["search_id"],
            rung="C",
        )
    ).json()

    assert len(widened["candidates"]) == 1, "the widening found somebody"
    assert widened["search"]["pool"]["radius_km_used"] == 20
    # Empty rather than ``null``: *not computed* is what a long enough list
    # answers, and this list is not long enough.
    assert widened["search"]["rung_offers"] == []
    assert widened["search"]["radius_clamp"] is False


async def test_the_second_climb_is_refused_and_twice_the_radius_is_the_furthest(
    client, session_factory, candidate_source, searcher
):
    """The bound is a refusal and not a hidden button.

    Nothing on the widened screen offers a rung, and citing the widened search
    for one is refused by the same code a widening nobody offered gets — because
    it *is* a widening nobody offered. Twice the radius the player saved is as
    far as any accepted offer reaches, and their slider never moved.
    """

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    offered = (await world.search(client, searcher["token"])).json()
    widened = (
        await world.search(
            client,
            searcher["token"],
            offered_by_search_id=offered["search"]["search_id"],
            rung="C",
        )
    ).json()

    for rung in ("A", "B", "C"):
        again = await world.search(
            client,
            searcher["token"],
            offered_by_search_id=widened["search"]["search_id"],
            rung=rung,
        )
        assert again.status_code == 409, again.text
        assert again.json()["code"] == "rung_offer_not_found"

    assert widened["search"]["pool"]["radius_km_used"] == 20
    assert await world.saved_radius_km(session_factory, searcher["id"]) == 10


async def test_a_climb_that_lands_on_the_ceiling_is_offered_nothing_either(
    client, session_factory, candidate_source
):
    """**``radius_clamp`` still gates every offer.**

    A searcher at 40 km is offered one rung, not two, because both multipliers
    clamp to the same 50 km — and the search that takes it is at the slider's own
    maximum, where there was never anything left to offer. The two bounds agree
    rather than one covering for the other.
    """

    _, token = await world.register(client, "nearly-at-the-ceiling")
    await world.commit_profile(client, token, search_radius_km=40)
    await world.rate(client, token)
    await world.declare_intent(client, token)
    await world.fold_the_log(session_factory, candidate_source)
    offered = (await world.search(client, token)).json()
    assert [one["rung"] for one in offered["search"]["rung_offers"]] == ["B"], (
        "two multipliers that clamp to one radius are offered once"
    )

    climbed = (
        await world.search(
            client,
            token,
            offered_by_search_id=offered["search"]["search_id"],
            rung="B",
        )
    ).json()

    assert climbed["search"]["pool"]["radius_km_used"] == 50
    assert climbed["search"]["rung_offers"] == []
    assert climbed["search"]["radius_clamp"] is True


async def test_a_widening_nobody_offered_is_refused(
    client, session_factory, candidate_source, searcher
):
    """The radius a rung goes to is read off the **offer**, never off the
    request, so a citation that resolves to nothing is a refusal rather than a
    narrow search recorded as a wide one."""

    for index in range(6):
        await world.a_candidate(
            client, session_factory, f"player-{index}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)
    # A search long enough that no offers were computed at all.
    offered = (await world.search(client, searcher["token"])).json()

    refused = await world.search(
        client,
        searcher["token"],
        offered_by_search_id=offered["search"]["search_id"],
        rung="B",
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "rung_offer_not_found"


async def test_a_rung_cited_without_the_search_that_offered_it_is_refused(
    client, session_factory, candidate_source, searcher
):
    """They travel together or not at all."""

    await world.fold_the_log(session_factory, candidate_source)

    refused = await world.search(client, searcher["token"], rung="B")

    assert refused.status_code == 409
    assert refused.json()["code"] == "rung_offer_not_found"


async def test_another_players_search_cannot_be_cited(
    client, session_factory, candidate_source, searcher
):
    """A search belonging to somebody else answers exactly as one that never
    existed — the same sameness the read-back's 404 is built on."""

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    theirs = (await world.search(client, searcher["token"])).json()

    stranger = await world.a_searcher(client, name="stranger")
    refused = await world.search(
        client,
        stranger["token"],
        offered_by_search_id=theirs["search"]["search_id"],
        rung="B",
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "rung_offer_not_found"


async def test_an_improvised_week_runs_this_search_and_asks_about_the_profile(
    client, session_factory, candidate_source, searcher
):
    """**The grid edit is per search, and it offers to write back.**

    The search runs on the week the player just ticked — the window comes from
    it, and so does the recorded grid — and the profile keeps its own answer
    until the player says otherwise.
    """

    await world.a_candidate(
        client,
        session_factory,
        "thursday",
        mu=searcher["mu"],
        availability=ANOTHER_EVENING,
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (
        await world.search(
            client,
            searcher["token"],
            availability_override=[{"day": 4, "part": "EVENING"}],
        )
    ).json()

    assert body["search"]["pool"]["window"] == "THIS_WEEK"
    prompts = {prompt["prompt"]: prompt for prompt in body["search"]["prompts"]}
    assert prompts["KEEP_THESE_TIMES"]["slots"] == ["4:EVENING"]

    assert await world.saved_grid(session_factory, searcher["id"]) == (
        "2:EVENING",
        "6:MORNING",
    ), "the profile is untouched"

    (row,) = await world.recorded_searches(session_factory)
    assert list(row.searcher_grid) == ["4:EVENING"]
    assert row.searcher_slot_count == 1


async def test_a_cleared_week_runs_the_search_and_asks_about_it_too(
    client, session_factory, candidate_source, searcher
):
    """**Unticking every cell is an edit, and an edit searches.**

    The floor binds the answer a player is *asked for* at commit, not every later
    edit of it, so a blank grid on the search screen is a week like any other:
    the search runs, the term stands down for want of evidence rather than
    scoring a nought, and the app offers to save it afterwards.
    """

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    ran = await world.search(
        client, searcher["token"], availability_override=[]
    )

    assert ran.status_code == 200, ran.text
    body = ran.json()
    prompts = {prompt["prompt"]: prompt for prompt in body["search"]["prompts"]}
    assert prompts["KEEP_THESE_TIMES"]["slots"] == [], (
        "a cleared week crosses as an empty list, not as a missing field"
    )

    assert await world.saved_grid(session_factory, searcher["id"]) == (
        "2:EVENING",
        "6:MORNING",
    ), "the profile is untouched"

    (row,) = await world.recorded_searches(session_factory)
    assert list(row.searcher_grid) == []
    assert row.searcher_slot_count == 0


async def test_a_search_on_the_profiles_own_week_asks_nothing(
    client, session_factory, candidate_source, searcher
):
    """A prompt is raised by something having happened, not by a search running."""

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, searcher["token"])).json()

    assert body["search"]["prompts"] == []


async def test_a_widening_taken_again_and_again_offers_to_become_the_default(
    client, session_factory, candidate_source, searcher
):
    """*"Keep 15 km?"*, inline, bounded by the player's own slider, and **never a
    silent write**. The engine notices drift and asks; it never acts on it."""

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    offered = (await world.search(client, searcher["token"])).json()

    bodies = []
    for _ in range(REPEATED_WIDENINGS):
        taken = await world.search(
            client,
            searcher["token"],
            offered_by_search_id=offered["search"]["search_id"],
            rung="B",
        )
        bodies.append(taken.json())

    raised = [
        {prompt["prompt"] for prompt in body["search"]["prompts"]} for body in bodies
    ]
    assert "KEEP_THIS_RADIUS" not in raised[0], "once is not a habit"
    assert "KEEP_THIS_RADIUS" in raised[-1]
    keep = next(
        prompt
        for prompt in bodies[-1]["search"]["prompts"]
        if prompt["prompt"] == "KEEP_THIS_RADIUS"
    )
    assert keep["radius_km"] == 15

    assert await world.saved_radius_km(session_factory, searcher["id"]) == 10, (
        "asked, never written"
    )

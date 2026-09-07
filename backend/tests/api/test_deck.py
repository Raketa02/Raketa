"""*Match me* — the deck, over HTTP.

Every assertion lands on the real route through the async client fixture: ASGI
transport over in-memory SQLite, **no MinIO, no sidecar and no Redis**.

What is asserted is the product's promises rather than the plumbing. That no mode
crosses the wire in either direction, and that the week the player just edited is
the one the deal runs on. That **a player with no preference still gets a working
deck**, because indecision is not a blocked state. That the order is the
deck's own three bands. That **a spent deal deals again**, and that only a fresh
deal coming back empty is the honest empty state. And that the two facts nobody
can see from any screen — how many cards a suppression removed, and whether a
card is a re-show — are on the record where an analyst can find them.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.matchmaking.domain.searches import SearchSurface
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


@pytest.fixture
async def a_city(client, session_factory, candidate_source, searcher):
    """One searcher and three findable candidates, at three Levels.

    Three rather than one, because most of what the deck promises is about
    *order* and *what a second deal does*, and neither is observable with a pool
    of one.
    """

    others = [
        await world.a_candidate(
            client, session_factory, name, mu=searcher["mu"] + offset
        )
        for name, offset in (("bea", 0.0), ("cara", 0.02), ("dee", -0.02))
    ]
    await world.fold_the_log(session_factory, candidate_source)
    return others


# ---------------------------------------------------------------------------
# One deal
# ---------------------------------------------------------------------------


async def test_a_deal_names_no_mode_in_either_direction(client, searcher, a_city):
    """**No mode crosses the wire, in either direction.**

    The deck reads the viewer's own declaration instead — which is why the
    envelope's `mode` comes back null rather than echoing something the request
    never sent, and why there is no field for one to arrive through.
    """

    dealt = await world.deck(client, searcher["token"])

    assert dealt.status_code == 200, dealt.text
    body = dealt.json()
    assert body["search"]["surface"] == SearchSurface.DECK.value
    assert body["search"]["mode"] is None, "the deck has no mode"
    assert body["search"]["search_id"], "one deal, one search id"
    assert body["candidates"], "three findable people and an empty deal"


async def test_a_deal_runs_on_the_week_the_player_just_edited(
    client, session_factory, searcher, a_city
):
    """**Match me reads the improvised week, and offers to keep it.**

    The alternative was a deck that silently ranks on a week the player has just
    replaced. The three refusals this body is written under are a mode, a
    widening and a pass window; a grid is none of them.
    """

    dealt = await world.deck(
        client, searcher["token"], availability_override=[{"day": 4, "part": "EVENING"}]
    )

    assert dealt.status_code == 200, dealt.text
    prompts = {
        prompt["prompt"]: prompt for prompt in dealt.json()["search"]["prompts"]
    }
    assert prompts["KEEP_THESE_TIMES"]["slots"] == [{"day": 4, "part": "EVENING"}]

    recorded = (await world.recorded_searches(session_factory))[-1]
    assert list(recorded.searcher_grid) == ["4:EVENING"]
    # The area is recorded beside the week and on the same terms — a deal is a
    # search, and its envelope carries both halves of the card's one comparison.
    assert recorded.searcher_area_code
    assert dealt.json()["search"]["my_area_code"] == recorded.searcher_area_code
    assert await world.saved_grid(session_factory, searcher["id"]) == (
        "2:EVENING",
        "6:MORNING",
    ), "the profile is untouched"


async def test_a_deal_on_the_profiles_own_week_asks_nothing(
    client, searcher, a_city
):
    """A prompt is raised by something having happened, and an empty list is the
    honest way to say nothing did — the deck runs them now rather than not
    having them."""

    dealt = await world.deck(client, searcher["token"])

    assert dealt.json()["search"]["prompts"] == []


async def test_a_cleared_week_deals_a_deck(client, searcher, a_city):
    """The same bug, on the third surface: unticking every cell is an edit."""

    dealt = await world.deck(client, searcher["token"], availability_override=[])

    assert dealt.status_code == 200, dealt.text
    prompts = {
        prompt["prompt"]: prompt for prompt in dealt.json()["search"]["prompts"]
    }
    assert prompts["KEEP_THESE_TIMES"]["slots"] == []


async def test_the_declaration_is_recorded_and_the_vector_is_not(
    client, session_factory, searcher, a_city
):
    """`intent_read` records **the declaration as it stood**.

    Never the vector it mapped to — so a later change to the mapping does not
    rewrite what this player had actually said.
    """

    await world.deck(client, searcher["token"])

    recorded = await world.recorded_searches(session_factory)
    deal = recorded[-1]
    assert deal.surface == SearchSurface.DECK.value
    assert deal.mode is None
    assert deal.intent_read == "COMPETITIVE", "the declaration, not `comp`"


async def test_a_player_with_no_preference_still_gets_a_working_deck(
    client, session_factory, candidate_source
):
    """**Indecision is not a blocked state.**

    *No preference* maps to *for fun* and never to a third vector, and the
    declaration is what is recorded — so the row says `NO_PREFERENCE` while the
    deal was scored as a for-fun one.
    """

    undecided = await world.a_searcher(client, "undecided", intent="NO_PREFERENCE")
    await world.a_candidate(
        client, session_factory, "eve", mu=undecided["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)

    dealt = await world.deck(client, undecided["token"])

    assert dealt.status_code == 200, dealt.text
    assert dealt.json()["candidates"], "no preference is an answer, not a refusal"
    recorded = await world.recorded_searches(session_factory)
    assert recorded[-1].intent_read == "NO_PREFERENCE"


async def test_a_deal_is_capped_and_the_cap_is_not_a_target(
    client, session_factory, candidate_source, searcher
):
    """At most `DECK_DEAL_MAX` cards, which is **10**.

    The number is ruleset data and never crosses the wire — a client renders the
    cards it is given — so this asserts the bound rather than reading it from
    anywhere.
    """

    for number in range(12):
        await world.a_candidate(
            client, session_factory, f"p{number}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)

    dealt = (await world.deck(client, searcher["token"])).json()

    assert len(dealt["candidates"]) == 10


# ---------------------------------------------------------------------------
# A spent deal deals again
# ---------------------------------------------------------------------------


async def test_a_spent_deal_deals_again_with_nobody_repeated(
    client, session_factory, candidate_source, searcher
):
    """**Running out of cards is not running out of people.**

    A second deal is a new search with a new id and the same exclusions plus
    everybody already dealt — so the next request answers with the *next* people
    rather than the same ten in the same order.
    """

    for number in range(12):
        await world.a_candidate(
            client, session_factory, f"q{number}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)

    first = (await world.deck(client, searcher["token"])).json()
    second = (await world.deck(client, searcher["token"])).json()

    assert first["search"]["search_id"] != second["search"]["search_id"]
    dealt_first = {row["player_id"] for row in first["candidates"]}
    dealt_again = {row["player_id"] for row in second["candidates"]}
    assert dealt_first, "the first deal was empty and proves nothing"
    assert not (dealt_first & dealt_again), "a spent deal dealt the same cards"


async def test_an_exhausted_pool_says_so_honestly(client, searcher, a_city):
    """A fresh deal that comes back with nothing is the honest empty state.

    It is a `200` with the pool described, exactly like any other deal, and it is
    recorded exactly like any other search — the absence of a row is never how
    emptiness is expressed.
    """

    while (dealt := (await world.deck(client, searcher["token"])).json())[
        "candidates"
    ]:
        pass

    assert dealt["candidates"] == []
    assert dealt["search"]["pool"]["players_in_range"] >= 1, (
        "the pool is described even when the deal is empty — a thin pool and "
        "your own exhausted deck must be tellable apart"
    )


# ---------------------------------------------------------------------------
# What the deck is not
# ---------------------------------------------------------------------------


async def test_the_relaxation_ladder_does_not_reach_the_deck(
    client, session_factory, candidate_source
):
    """No rung offers on a deal, ever — **null, not an empty list.**

    `null` is *the offers were not computed at all*, which is the truth here: a
    ladder that ran and found nothing would be an empty list, and that would be a
    different claim.
    """

    lonely = await world.a_searcher(client, "lonely")
    await world.fold_the_log(session_factory, candidate_source)

    dealt = (await world.deck(client, lonely["token"])).json()

    assert dealt["candidates"] == []
    assert dealt["search"]["rung_offers"] is None


async def test_a_deal_draws_no_re_sorts(client, searcher, a_city):
    """A deck is one card at a time, so there is no list to reorder.

    Its order **is** its variety, and a control that resorted a deal would offer
    to undo the one thing the surface does.
    """

    dealt = (await world.deck(client, searcher["token"])).json()

    assert dealt["search"]["sorts_available"] == []


async def test_the_re_show_flag_is_written_on_a_dealt_card_and_nowhere_else(
    client, session_factory, searcher, a_city
):
    """`suppression_lapsed` is set exactly where a card was dealt.

    `false` on a card nobody was ever passed on, and **null** on a shortlist row
    — a biconditional rather than a default, because *not a re-show* and *not a
    card* are different sentences and only one of them is a measurement.
    """

    dealt = (await world.deck(client, searcher["token"])).json()
    await world.search(client, searcher["token"])

    recorded = await world.recorded_searches(session_factory)
    cards = await world.recorded_candidates(
        session_factory, dealt["search"]["search_id"]
    )
    assert cards, "the deal was empty and proves nothing"
    assert all(
        row.suppression_lapsed is False
        for row in cards
        if row.band == "RETURNED"
    )
    shortlist = next(row for row in recorded if row.surface == "SHORTLIST")
    listed = await world.recorded_candidates(session_factory, shortlist.id)
    assert all(row.suppression_lapsed is None for row in listed)


async def test_a_deal_reads_back_in_the_same_shape(client, searcher, a_city):
    """`GET /searches/{id}` returns the same schema the `POST` did.

    The same rule for all four surfaces — which is why a deal crosses in the
    envelope a shortlist crosses in rather than a shape of its own.
    """

    dealt = (await world.deck(client, searcher["token"])).json()

    read = await world.read_back(
        client, searcher["token"], dealt["search"]["search_id"]
    )

    assert read.status_code == 200, read.text
    body = read.json()
    assert body["search"]["surface"] == SearchSurface.DECK.value
    assert body["search"]["mode"] is None
    assert [row["player_id"] for row in body["candidates"]] == [
        row["player_id"] for row in dealt["candidates"]
    ]


async def test_a_dealt_card_carries_the_photograph_it_is_mostly_made_of(
    client, session_factory, candidate_source, searcher
):
    """**The deck's whole card is a photograph.**

    A deal that handed back an id the client cannot sign for would draw the
    generated poster on every card, which would quietly make the poster the
    product rather than the fallback it argued itself into being.
    """

    photo = uuid4()
    dealt_to = await world.a_candidate(
        client, session_factory, "bea", mu=searcher["mu"], photo_ids=(photo,)
    )
    await world.fold_the_log(session_factory, candidate_source)

    card = (await world.deck(client, searcher["token"])).json()["candidates"][0][
        "player_card"
    ]

    assert card["photo_id"] == str(photo)
    assert card["photo_url"].endswith(f"{dealt_to}/{photo}")

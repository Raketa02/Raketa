"""``POST /api/v1/searches`` — the tracer bullet, over the real routes.

Every assertion here lands on HTTP, through the async client fixture: ASGI
transport over in-memory SQLite, **no MinIO and no sidecar**. That is the
acceptance criterion rather than a convenience — a suite that only passes with
containers up is a suite CI cannot be trusted to run.

What is asserted is mostly the product's promises rather than the plumbing: that
the breakdown ships *with* the search, that the two modes are two different
games, that an empty city is a `200`, that the record is written before the
answer, and that a whole list of facts never crosses at all.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.modules.matchmaking.domain.errors import MatchmakingUnavailable
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client, session_factory):
    return await world.a_searcher(client, session_factory)


async def test_a_search_returns_a_ranked_shortlist_carrying_its_whole_working(
    client, session_factory, candidate_source, searcher
):
    """*Find me a game.* One tap, a ranked list, and **Why 78?** already in hand.

    The breakdown ships with the search rather than behind a tap, because that is
    the moment the product's central claim is tested and a spinner there is the
    claim failing.
    """

    await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    await world.a_candidate(
        client, session_factory, "far", mu=searcher["mu"] + 0.2, latitude=51.55
    )
    await world.fold_the_log(session_factory, candidate_source)

    response = await world.search(client, searcher["token"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["candidates"]) == 2
    for candidate in body["candidates"]:
        assert 0 <= candidate["fit"] <= 100
        assert candidate["terms"], "a row with no working behind its number"
        for term in candidate["terms"]:
            assert term["evidence"]["kind"], "a term with evidence that names no kind"
            assert term["contribution"] == pytest.approx(
                term["weight"] * term["value"]
            )
        assert candidate["player_card"]["nickname"]
        assert "degraded_terms" in candidate
        assert "modifiers" in candidate
        assert "liveness_reasons" in candidate


async def test_the_contributions_add_up_to_the_number_on_the_card(
    client, session_factory, candidate_source, searcher
):
    """A breakdown that does not reconcile is the explainability claim failing.

    The terms sum to the **Fit**; the modifiers are a second, printed list beside
    them rather than a term nobody weighted — so what is asserted is the Fit plus
    whatever the stack moved, and nothing is allowed to be missing from either.
    """

    await world.a_candidate(client, session_factory, "one", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    candidate = (await world.search(client, searcher["token"])).json()["candidates"][0]

    terms = sum(term["contribution"] for term in candidate["terms"])
    modifiers = sum(entry["points"] for entry in candidate["modifiers"])
    assert candidate["fit"] == pytest.approx(terms + modifiers, abs=1e-6)


async def test_competitive_and_for_fun_are_two_different_games(
    client, session_factory, candidate_source, searcher
):
    """The weights invert, and **that inversion is what *for fun* means.**

    One candidate is the stronger level match with nothing social to say; the
    other shares the searcher's vibe and sits further off in level. Competitive
    ranks on level; for fun ranks on vibe, availability and distance — so the two
    lists must not agree about who is first.
    """

    # The same seven terms fire for both, so the two lists differ because the
    # **weights** differ and not because one of them renormalised away.
    await world.a_candidate(
        client,
        session_factory,
        "level-twin",
        mu=searcher["mu"],
        availability=("1:MORNING",),
        latitude=51.58,
    )
    await world.a_candidate(
        client,
        session_factory,
        "kindred-spirit",
        mu=searcher["mu"] + 0.45,
    )
    await world.fold_the_log(session_factory, candidate_source)

    competitive = (await world.search(client, searcher["token"], "COMPETITIVE")).json()
    for_fun = (await world.search(client, searcher["token"], "FOR_FUN")).json()

    assert [row["player_id"] for row in competitive["candidates"]] == list(
        reversed([row["player_id"] for row in for_fun["candidates"]])
    ), "the list did not invert between the two modes"


async def test_an_empty_city_is_a_200_that_describes_the_pool(
    client, session_factory, candidate_source, searcher
):
    """**The honest empty state is an answer, not a failure.**

    And the pool is described on every search rather than only on the empty
    ones: a thin pool and a broken floor are indistinguishable without it.
    """

    await world.fold_the_log(session_factory, candidate_source)

    response = await world.search(client, searcher["token"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["candidates"] == []
    assert body["search"]["pool"]["players_in_range"] == 0
    assert body["search"]["pool"]["post_gate"] is True
    assert body["search"]["pool"]["radius_km_used"] == 10


async def test_the_search_is_recorded_before_the_answer_returns(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0104``: **the search id *is* the answer's identity.**

    The row is written in the request's own transaction and committed before the
    response, so by the time a caller is holding the body the record is already
    readable — including the counters the client never sees.
    """

    await world.a_candidate(client, session_factory, "somebody", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, searcher["token"])).json()

    recorded = await world.recorded_searches(session_factory)
    assert len(recorded) == 1
    row = recorded[0]
    assert str(row.id) == body["search"]["search_id"]
    assert row.surface == "SHORTLIST"
    assert row.initiation == "HUMAN"
    assert row.mode == "COMPETITIVE"
    assert row.intent_read is None, "only the deck records a declaration"
    assert row.n_returned == len(body["candidates"])
    assert row.searcher_slot_count == 2
    assert row.trace_id
    assert set(row.excluded_by_gate) == {
        "BLOCKED",
        "HELD_ACCOUNT",
        "NOT_RATED",
        "OUTSIDE_RADIUS",
        "OPEN_CHALLENGE",
        "PHOTO",
        "PROPOSALS_OPT_OUT",
        "ACCOUNT_INACTIVE",
        "GENDER_PREFERENCE",
        "LEVEL",
    }, "the gate histogram is the whole closed roster, zeroes included"


async def test_two_taps_are_two_searches(
    client, session_factory, candidate_source, searcher
):
    """**Deliberately not idempotent.** The index moved between them, and the
    product's own denominator is *searches run* — collapsing a double tap would
    put a lie in the one table the product uses to judge itself."""

    await world.fold_the_log(session_factory, candidate_source)

    first = (await world.search(client, searcher["token"])).json()
    second = (await world.search(client, searcher["token"])).json()

    assert first["search"]["search_id"] != second["search"]["search_id"]
    assert len(await world.recorded_searches(session_factory)) == 2


async def test_the_near_miss_band_is_recorded_and_never_returned(
    client, session_factory, candidate_source, searcher
):
    """*A player may ask why somebody was shown; nobody may ask who was
    withheld.*

    The candidate below the floor is in the store, in the near-miss band, and
    nowhere in the payload — not as a row, not as a count, not as a name.
    """

    # Nearly at the level tolerance, nothing declared, no tags and no grid — so
    # four of the seven live terms have nothing to read about this person.
    await world.a_candidate(
        client,
        session_factory,
        "poor-match",
        mu=searcher["mu"] + 0.5,
        latitude=51.58,
        availability=(),
        tags=(),
        intent=None,
    )
    await world.fold_the_log(session_factory, candidate_source)

    response = await world.search(client, searcher["token"])
    body = response.json()

    assert body["candidates"] == []
    rows = await world.recorded_candidates(
        session_factory, body["search"]["search_id"]
    )
    withheld = [row for row in rows if row.band == "NEAR_MISS"]
    assert len(withheld) == 1
    assert withheld[0].withheld_reason in {"BELOW_FLOOR", "INSUFFICIENT_EVIDENCE"}
    assert withheld[0].position == 1
    assert "poor-match" not in response.text
    assert "NEAR_MISS" not in response.text
    assert "withheld" not in response.text


async def test_a_searcher_with_no_rating_for_the_sport_is_refused_by_its_own_code(
    client, session_factory
):
    """Its own code rather than a generic conflict, because the client's recovery
    differs: this one is *go and rate this sport*."""

    player_id, token = await world.register(client, "unrated")
    await world.commit_profile(client, token)
    await world.declare_intent(session_factory, player_id)

    response = await world.search(client, token)

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "sport_not_rated"


async def test_a_searcher_who_has_not_declared_an_intent_is_refused(
    client, session_factory
):
    """ADR-0094's interstitial, as a backstop for a stale profile on a second
    device. It is never the designed path — the search screen is the edit
    surface — which is exactly why the code has to be distinguishable."""

    _, token = await world.register(client, "undeclared")
    await world.commit_profile(client, token)
    await world.rate(client, token)

    response = await world.search(client, token)

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "play_intent_not_declared"


async def test_a_searcher_with_no_profile_cannot_search(client):
    """There is no radius, no grid and no area to search with, and every gate
    would be evaluated on nothing."""

    _, token = await world.register(client, "profileless")

    response = await world.search(client, token)

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "player_profile_not_committed"


async def test_the_route_requires_a_token(client):
    response = await client.post(
        "/api/v1/searches", json={"sport": "PADEL", "mode": "COMPETITIVE"}
    )
    assert response.status_code == 401


async def test_a_block_removes_them_from_the_list_and_nothing_says_so(
    client, session_factory, candidate_source, searcher
):
    """The gate is live, both directions, and **the searcher is told nothing.**

    Not a count, not a code, not a shorter pool description that names a reason.
    The post-gate count simply drops by one, exactly as it would if that person
    had moved out of the city.
    """

    blocked = await world.a_candidate(
        client, session_factory, "not-them", mu=searcher["mu"]
    )
    await world.a_candidate(client, session_factory, "fine", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked), "surface": "SHORTLIST"},
        headers=world.auth(searcher["token"]),
    )

    response = await world.search(client, searcher["token"])

    body = response.json()
    assert [row["player_id"] for row in body["candidates"]] != []
    assert str(blocked) not in response.text
    assert "block" not in response.text.lower()


async def test_a_candidate_outside_the_searchers_own_ring_is_not_returned(
    client, session_factory, candidate_source, searcher
):
    """The radius is the **searcher's own ask**, read from their profile — so it
    is a filter, and the bounding box that admitted the row is corrected by the
    circle inside it."""

    await world.a_candidate(
        client, session_factory, "another-city", mu=searcher["mu"], latitude=52.60
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, searcher["token"])).json()

    assert body["candidates"] == []
    assert body["search"]["pool"]["players_in_range"] == 0


async def test_the_shortlist_is_bounded_and_unpaginated(
    client, session_factory, candidate_source, searcher
):
    """Twenty rows, no page two, and no cursor anywhere in the envelope.

    The bound is ruleset data, so a client never reads it from the contract — it
    renders the rows it is given, and the list ends where the engine stops
    believing in it.
    """

    for index in range(24):
        await world.a_candidate(
            client, session_factory, f"player-{index}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, searcher["token"])).json()

    assert len(body["candidates"]) == 20
    assert "next" not in body and "cursor" not in body
    assert "next" not in body["search"] and "page" not in body["search"]


async def test_no_response_carries_a_liveness_number_or_a_rank_key(
    client, session_factory, candidate_source, searcher
):
    """The central assertion is made over the emitted contract; this is the same
    claim about a real payload, because a schema can be right while a handler
    writes an extra key."""

    await world.a_candidate(client, session_factory, "somebody", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    text = (await world.search(client, searcher["token"])).text

    for forbidden in ("rank_key", "liveness_offset", "liveness_points"):
        assert forbidden not in text


async def test_the_card_states_the_range_the_level_is_likely_in(
    client, session_factory, candidate_source, searcher
):
    """A Level with no range shows two players at the same number with no way to
    tell that one of them is a guess.

    **It is the published range, not μ ± σ recomputed here.** The rating this
    world publishes carries `mu ± 0.30` against a σ of 0.34, so a card that
    derived the range at assembly would answer `± 0.34` and this assertion is
    what tells the two apart.

    The **band's numeric edges are not on the card**: the only thing that would
    draw them is the band bar, which lives on the player record sheet, and the
    glossary refuses them as a second range in any case.
    """

    mu = searcher["mu"]
    await world.a_candidate(client, session_factory, "ranged", mu=mu)
    await world.fold_the_log(session_factory, candidate_source)

    card = (await world.search(client, searcher["token"])).json()["candidates"][0][
        "player_card"
    ]

    assert card["level"] == mu
    assert card["band"] == "Improver"
    assert card["range"] == {
        "low": pytest.approx(mu - 0.3),
        "high": pytest.approx(mu + 0.3),
    }, "the card derived a range instead of printing the published one"
    assert "band_lower" not in card and "band_upper" not in card


async def test_the_card_carries_a_photo_id_and_never_a_url(
    client, session_factory, candidate_source, searcher
):
    """A presigned link cannot live in a record kept for ever, so what travels is
    the id — and it is **omitted** rather than null when there is no photo, which
    is what tells the client to draw the generated court poster."""

    await world.a_candidate(client, session_factory, "no-photo", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    card = (await world.search(client, searcher["token"])).json()["candidates"][0][
        "player_card"
    ]

    assert "photo_id" not in card
    assert "counted_games" not in card, "the games ledger has no provider today"
    assert "bio" not in card and "last_active_at" not in card
    assert "gender" not in card


async def test_the_envelope_carries_the_facts_about_the_search(
    client, session_factory, candidate_source, searcher
):
    """One object holding every fact about *the search* rather than a candidate:
    one renderer, one type."""

    await world.a_candidate(client, session_factory, "somebody", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    envelope = (await world.search(client, searcher["token"])).json()["search"]

    assert envelope["optimised_for"] == "SEARCHER"
    assert envelope["index_stale"] is False
    assert envelope["radius_clamp"] is False
    assert envelope["engine_version"] and envelope["ruleset_version"]
    assert envelope["pool"]["window"] in {
        "TODAY",
        "TOMORROW",
        "WEEKEND",
        "THIS_WEEK",
        "ANY",
    }
    assert set(envelope["sorts_available"]) <= {
        "BEST_FIT",
        "CLOSEST",
        "EVENEST",
        "MOST_RELIABLE",
    }
    assert "EVENEST" not in envelope["sorts_available"], (
        "a shortlist has no seats, so *Evenest* would reorder nothing"
    )
    assert "MOST_RELIABLE" not in envelope["sorts_available"], (
        "the reliability term stands down for everybody, so the control is not drawn"
    )
    for staged in ("n_generated", "n_scored", "n_cleared_floor", "excluded_by_gate"):
        assert staged not in envelope and staged not in envelope["pool"]


async def test_a_reason_that_only_reorders_never_crosses_the_wire(
    client, session_factory, candidate_source, searcher
):
    """**The store is open where the wire is closed.**

    Every candidate here has been shown to nobody this week, so every recorded
    row carries an inclusion reason — and none of them may cross, because
    *nobody has been shown them all week* is a third party's unpopularity and the
    searcher is owed no version of it.
    """

    await world.a_candidate(client, session_factory, "unseen", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    response = await world.search(client, searcher["token"])
    body = response.json()

    recorded = await world.recorded_candidates(
        session_factory, body["search"]["search_id"]
    )
    assert [row.inclusion_reason for row in recorded] == ["ZERO_EXPOSURE"]
    assert all("inclusion_reason" not in row for row in body["candidates"])
    assert "ZERO_EXPOSURE" not in response.text
    assert "NEWCOMER_WINDOW" not in response.text


async def test_a_process_with_no_index_says_so_and_never_answers_empty(
    client, searcher
):
    """**Never a fallback.** A search with no index is not a search with a
    smaller pool — and an empty shortlist would be indistinguishable on the wire
    from *there is nobody near you*. The 503 says which."""

    from app.modules.matchmaking.presentation.dependencies import (
        get_candidate_source,
    )

    def _no_index():
        raise MatchmakingUnavailable("the candidate index is not running")

    world.override(client, get_candidate_source, _no_index)

    response = await world.search(client, searcher["token"])

    assert response.status_code == 503, response.text
    assert response.json()["code"] == "matchmaking_unavailable"


async def test_an_index_a_day_behind_refuses_over_http(
    client, session_factory, candidate_source, searcher
):
    """The refusal stands on **quality, not safety** — every fact staleness can
    cost is a fact about who is worth meeting."""

    await world.a_candidate(client, session_factory, "somebody", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    world.rewind_the_index(candidate_source, timedelta(hours=25))

    response = await world.search(client, searcher["token"])

    assert response.status_code == 503, response.text
    assert response.json()["code"] == "index_too_stale"


async def test_a_block_set_that_cannot_be_read_refuses_over_http(
    client, session_factory, candidate_source, searcher
):
    """*A gate that cannot be evaluated excludes* — and its own code, because a
    503 about the platform is a different sentence from a 403 about you."""

    from app.modules.blocks.domain.errors import BlockStateUnavailable
    from app.modules.blocks.presentation.dependencies import get_block_query

    class Unreachable:
        async def exclusions_for(self, player_id):
            raise BlockStateUnavailable("the block store is unreachable")

        async def blocked_between(self, first, second):
            raise BlockStateUnavailable("the block store is unreachable")

    await world.a_candidate(client, session_factory, "somebody", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    world.override(client, get_block_query, Unreachable)

    response = await world.search(client, searcher["token"])

    assert response.status_code == 503, response.text
    assert response.json()["code"] == "gate_data_unavailable"


async def test_the_route_is_on_the_emitted_player_surface():
    """The contract the client generates from is the one this route is on."""

    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    spec = build_surface_spec("Raketa Player API", player_api_router)

    assert "/api/v1/searches" in spec["paths"]
    assert set(spec["paths"]["/api/v1/searches"]) == {"post"}

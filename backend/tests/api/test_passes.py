"""*Not today* — the pass, over HTTP.

Every assertion lands on the real route through the async client fixture, and the
two that matter most are assertions about **absence**.

**No route returns a pass, to anybody.** Not to the passer, not as a count, not
as a timestamp — so the only way to see one at all is to read the table, which is
what `world.recorded_passes` is for and why reaching past the wire is written
down in one place rather than improvised per test.

**A pass is a statement about my deck; a block is a statement about a person.**
Its three boundaries are the opposite of a block's, and all three are asserted
here: deck only, one-directional, never escalating.
"""

from __future__ import annotations

import pytest

from app.api.contract import build_surface_spec
from app.api.v1.player import player_api_router
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client, session_factory):
    return await world.a_searcher(client, session_factory)


@pytest.fixture
async def a_city(client, session_factory, candidate_source, searcher):
    """One searcher and two findable candidates."""

    others = [
        await world.a_candidate(
            client, session_factory, name, mu=searcher["mu"] + offset
        )
        for name, offset in (("bea", 0.0), ("cara", 0.02))
    ]
    await world.fold_the_log(session_factory, candidate_source)
    return others


async def _a_dealt_card(client, token):
    """One deal, and the first card in it. The origin key a pass needs."""

    dealt = (await world.deck(client, token)).json()
    assert dealt["candidates"], "nothing was dealt, so there is nothing to pass on"
    return dealt["search"]["search_id"], dealt["candidates"][0]["player_id"]


# ---------------------------------------------------------------------------
# Write-only
# ---------------------------------------------------------------------------


async def test_a_pass_answers_nothing_and_is_recorded_with_its_origin(
    client, session_factory, searcher, a_city
):
    """`204`, an empty body, and a durable row with the card it was made on.

    The Origin key is what makes *pass rate on re-shown profiles* computable at
    all, and it is read off the cited deal rather than sent — so a client cannot
    be wrong about where it was.
    """

    search_id, passed_on = await _a_dealt_card(client, searcher["token"])

    response = await world.pass_on(
        client, searcher["token"], player_id=passed_on, search_id=search_id
    )

    assert response.status_code == 204, response.text
    assert response.content == b"", "a pass never carries a body"
    rows = await world.recorded_passes(session_factory)
    assert len(rows) == 1
    assert str(rows[0].passed_id) == passed_on
    assert str(rows[0].origin_search_id) == search_id
    assert rows[0].origin_position >= 1


def test_no_response_shape_in_the_whole_contract_can_carry_a_pass():
    """**A schema test over every response type**, which is what §21 asks for.

    Not a sampled payload: three responses that happen not to mention a pass
    prove only that these three do not. What is asserted here is the stronger
    thing — that *there is no shape a pass could arrive in*, over the whole
    emitted contract, so a route added next year cannot quietly grow one.

    Two halves. **No response schema has a field named for one**: not a pass, not
    a suppression, not a window, not a count of either. And the pass route
    itself **declares no success body at all** — a `204`, so there is nowhere for
    one to be written even by accident.

    The vocabulary below is the ban list rather than a guess: `PASS_SUPPRESS`
    crosses in **no shape at all** (`docs/adr/0128` §4), so every spelling of it
    is a field this contract may not have.
    """

    spec = build_surface_spec("Raketa Player API", player_api_router)

    # Whole words, split on the snake case this contract is written in — so
    # `password` is a password and not a near miss. A substring match here would
    # be the kind of check that goes red for the wrong reason once and is then
    # loosened until it means nothing.
    forbidden = {
        "pass",
        "passed",
        "passes",
        "suppress",
        "suppressed",
        "suppression",
    }
    offenders = [
        f"{name}.{field}"
        for name, schema in spec["components"]["schemas"].items()
        for field in schema.get("properties", {})
        # The **request** body of `POST /passes` is the one place the word
        # belongs: it is how a pass is *sent*, and the promise is about what
        # comes back.
        if name != "RecordPassRequest"
        and forbidden & set(field.lower().split("_"))
    ]
    assert offenders == [], f"a response shape can carry a pass: {offenders}"

    answers = spec["paths"]["/api/v1/passes"]["post"]["responses"]
    assert "204" in answers, "a pass must answer no content"
    assert "content" not in answers["204"], (
        "the pass route declared a success body, which is a shape a pass could "
        "cross in"
    )
    assert not any(
        "content" in answers[status] for status in answers if status.startswith("2")
    )


async def test_a_pass_is_invisible_on_the_surfaces_that_could_show_one(
    client, searcher, a_city
):
    """The same promise, from the other end: the three live surfaces.

    The schema test above says no shape *could* carry a pass; this says the deck,
    the interest screen and the read-back do not name the passed player either —
    which is a different claim, because a passed person leaking as an ordinary
    card would break no schema.
    """

    search_id, passed_on = await _a_dealt_card(client, searcher["token"])
    await world.pass_on(
        client, searcher["token"], player_id=passed_on, search_id=search_id
    )

    dealt = (await world.deck(client, searcher["token"])).json()
    listed = (await world.read_interest(client, searcher["token"])).json()
    read = (await world.read_back(client, searcher["token"], search_id)).json()

    assert passed_on not in {row["player_id"] for row in dealt["candidates"]}
    assert passed_on not in {row["player_id"] for row in listed["outgoing"]}
    assert passed_on not in {row["player_id"] for row in listed["mutual"]}
    # The read-back is the one place they still appear, and **correctly**: it is
    # the deal they were dealt in, and a pass is not a gate — a row is withheld
    # by a block, a hold or an account state, never by a swipe.
    assert passed_on in {
        row["player_id"] for row in read["candidates"] if not row.get("withheld")
    }


async def test_a_pass_citing_a_search_that_never_showed_them_is_refused(
    client, searcher, a_city
):
    """**Refused, never linked as null.** A dropped link is a denominator that
    lies, and the four ways to get here answer with one code on purpose."""

    search_id, _ = await _a_dealt_card(client, searcher["token"])

    response = await world.pass_on(
        client,
        searcher["token"],
        player_id=searcher["id"],
        search_id=search_id,
    )

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "origin_search_not_found"


# ---------------------------------------------------------------------------
# The three boundaries
# ---------------------------------------------------------------------------


async def test_a_pass_keeps_them_out_of_my_deck(client, searcher, a_city):
    """The whole of what a pass does, on the one surface it reaches."""

    search_id, passed_on = await _a_dealt_card(client, searcher["token"])
    await world.pass_on(
        client, searcher["token"], player_id=passed_on, search_id=search_id
    )

    dealt = (await world.deck(client, searcher["token"])).json()

    assert passed_on not in {row["player_id"] for row in dealt["candidates"]}


async def test_a_pass_never_reaches_the_shortlist(client, searcher, a_city):
    """**The named cost, asserted rather than hidden**: pass on somebody
    tonight, find them in your shortlist tomorrow.

    A search is a question about the pool, and a search that hid people because
    of a swipe would be a search that lies about the city.
    """

    search_id, passed_on = await _a_dealt_card(client, searcher["token"])
    await world.pass_on(
        client, searcher["token"], player_id=passed_on, search_id=search_id
    )

    found = (await world.search(client, searcher["token"])).json()

    assert passed_on in {row["player_id"] for row in found["candidates"]}


async def test_a_pass_is_one_directional(
    client, session_factory, candidate_source, searcher
):
    """My pass suppresses in **my** deck and nowhere else.

    A pass costs the other person nothing, literally — where a symmetric one
    would spend their pool on my tap and they would never learn why.
    """

    other = await world.a_searcher(client, session_factory, "mirror")
    third = await world.a_candidate(
        client, session_factory, "bea", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)
    theirs = (await world.deck(client, other["token"])).json()
    assert str(third) in {row["player_id"] for row in theirs["candidates"]}
    passed = await world.pass_on(
        client,
        other["token"],
        player_id=third,
        search_id=theirs["search"]["search_id"],
    )
    assert passed.status_code == 204, passed.text

    mine = (await world.deck(client, searcher["token"])).json()

    assert str(third) in {row["player_id"] for row in mine["candidates"]}, (
        "somebody else's pass emptied my deck"
    )


async def test_the_deal_records_what_a_suppression_removed(
    client, session_factory, searcher, a_city
):
    """`n_excluded_by_suppression`, on the deal and on no other surface.

    It is the only thing that distinguishes *your own passes emptied your deck*
    from *the pool is empty* — a failure nobody can see from any screen, because
    no route returns a pass.
    """

    search_id, passed_on = await _a_dealt_card(client, searcher["token"])
    await world.pass_on(
        client, searcher["token"], player_id=passed_on, search_id=search_id
    )

    await world.deck(client, searcher["token"])

    recorded = await world.recorded_searches(session_factory)
    assert recorded[-1].n_excluded_by_suppression == 1
    shortlists = [
        row for row in recorded if row.surface == "SHORTLIST"
    ]
    assert all(
        row.n_excluded_by_suppression is None for row in shortlists
    ), "a shortlist counted a suppression it does not have"

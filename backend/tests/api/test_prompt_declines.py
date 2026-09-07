"""*Not now* — the decline, over HTTP.

Every assertion lands on the real route through the async client fixture, and the
claims are the four the design rests on.

**A decline is a row.** It is the one of a prompt's three outcomes that nothing
else records — a raise is recomputable from the search store and an accept writes
a value — so the table is the only place *how often does anybody say no to this*
can ever be read from.

**It is keyed by the question and never by the value quoted.** A padel screen
raised it, and what goes quiet depends on the question rather than on the screen:
a declaration is per sport, a radius and a week are one fact each.

**It retires nothing.** The standing prompt is left exactly where the loop put
it, to expire on its own — which is what keeps ``PromptLedger``'s *two methods
and no delete* true.

**And one prompt has no *not now*.** *Keep these times?* is asked again next
Tuesday, because next Tuesday's improvised week is a different week.
"""

from __future__ import annotations

import pytest

from app.kernel import Sport
from app.modules.matchmaking.domain.prompts import REPEATED_WIDENINGS, Prompt
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


@pytest.fixture
async def a_city(client, session_factory, candidate_source, searcher):
    """One searcher and somebody to find, so a search is an ordinary search."""

    await world.a_candidate(client, session_factory, "bea", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)


async def a_stale_week(prompt_ledger, searcher):
    """The staleness loop's tick, as it leaves the ledger.

    Raised here rather than by running the job, because what is under test is
    what a search does with a standing question — and the loop's own idempotence
    is asserted where the loop is.
    """

    await prompt_ledger.raise_prompt(
        player_id=searcher["id"], prompt=Prompt.REFRESH_YOUR_TIMES
    )


def raised(body) -> set[str]:
    return {prompt["prompt"] for prompt in body["search"]["prompts"]}


# ---------------------------------------------------------------------------
# The row
# ---------------------------------------------------------------------------


async def test_a_decline_answers_nothing_and_is_recorded(
    client, session_factory, searcher
):
    """`204`, an empty body, and a durable row. **No origin key**: the pass's was
    bought for a named falsifier, and two of these questions are raised by a loop
    with no search to cite."""

    response = await world.decline_prompt(
        client, searcher["token"], prompt="REFRESH_YOUR_TIMES"
    )

    assert response.status_code == 204, response.text
    assert response.content == b"", "a decline never carries a body"
    rows = await world.recorded_declines(session_factory)
    assert len(rows) == 1
    assert rows[0].player_id == searcher["id"]
    assert rows[0].prompt == "REFRESH_YOUR_TIMES"


async def test_a_second_no_is_a_second_row(client, session_factory, searcher):
    """Append-only, and nothing counts them: what it buys is the same month."""

    for _ in range(2):
        await world.decline_prompt(
            client, searcher["token"], prompt="REFRESH_YOUR_TIMES"
        )

    assert len(await world.recorded_declines(session_factory)) == 2


async def test_the_improvised_week_is_the_one_question_with_no_not_now(
    client, session_factory, searcher
):
    """Refused rather than written: a row the filter never reads would look like
    evidence of a suppression that never happened."""

    response = await world.decline_prompt(
        client, searcher["token"], prompt="KEEP_THESE_TIMES"
    )

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "prompt_does_not_suppress"
    assert await world.recorded_declines(session_factory) == []


# ---------------------------------------------------------------------------
# What it is keyed on
# ---------------------------------------------------------------------------


async def test_a_week_and_a_radius_are_declined_for_the_player_not_the_sport(
    client, session_factory, searcher
):
    """The asymmetry, at the one place a row is made. The grid is one week and
    not seven, and the radius is one number on a profile with no sport
    dimension — so the sport the screen sent is **dropped**, not stored."""

    for prompt in ("REFRESH_YOUR_TIMES", "KEEP_THIS_RADIUS"):
        await world.decline_prompt(
            client, searcher["token"], prompt=prompt, sport=Sport.PADEL
        )

    rows = await world.recorded_declines(session_factory)

    assert [row.sport for row in rows] == [None, None]


async def test_a_declaration_is_declined_for_the_sport_it_was_declared_for(
    client, session_factory, searcher
):
    """ADR-0094's *for that sport*, kept literally: one declaration per sport."""

    await world.decline_prompt(
        client, searcher["token"], prompt="UPDATE_PLAY_INTENT", sport=Sport.PADEL
    )

    rows = await world.recorded_declines(session_factory)

    assert [row.sport for row in rows] == [Sport.PADEL.value]


# ---------------------------------------------------------------------------
# What it buys, and what it does not touch
# ---------------------------------------------------------------------------


async def test_a_declined_question_is_not_raised_on_the_next_search(
    client, searcher, a_city, prompt_ledger
):
    """**The whole point**, end to end: the loop goes on raising it and the
    search stays quiet."""

    await a_stale_week(prompt_ledger, searcher)
    before = (await world.search(client, searcher["token"])).json()
    assert "REFRESH_YOUR_TIMES" in raised(before)

    await world.decline_prompt(
        client, searcher["token"], prompt="REFRESH_YOUR_TIMES"
    )

    after = (await world.search(client, searcher["token"])).json()
    assert raised(after) == set()


async def test_a_decline_retires_nothing(client, searcher, a_city, prompt_ledger):
    """``PromptLedger`` is *two methods and no delete*, and this route does not
    become the delete: the standing question is left to expire on its own, and
    what a decline stops is the next **raise**."""

    await a_stale_week(prompt_ledger, searcher)

    await world.decline_prompt(
        client, searcher["token"], prompt="REFRESH_YOUR_TIMES"
    )

    standing = await prompt_ledger.raised_for(
        player_id=searcher["id"], sport=Sport.PADEL
    )
    assert Prompt.REFRESH_YOUR_TIMES in standing


async def test_declining_one_question_leaves_the_others_asked(
    client, session_factory, candidate_source, searcher, a_city, prompt_ledger
):
    """Four questions about four facts. Declining the stale-week offer says
    nothing about the widening the player keeps taking."""

    await a_stale_week(prompt_ledger, searcher)
    await world.decline_prompt(
        client, searcher["token"], prompt="REFRESH_YOUR_TIMES"
    )
    offered = (await world.search(client, searcher["token"])).json()

    for _ in range(REPEATED_WIDENINGS):
        taken = await world.search(
            client,
            searcher["token"],
            offered_by_search_id=offered["search"]["search_id"],
            rung="B",
        )

    assert raised(taken.json()) == {"KEEP_THIS_RADIUS"}


async def test_a_decline_writes_no_value_of_the_players(
    client, session_factory, searcher, a_city, prompt_ledger
):
    """**Nothing in this module writes a profile**, and the one answer that
    writes no value is the least likely place to break that — which is exactly
    why it is worth asserting once."""

    before = await world.saved_radius_km(session_factory, searcher["id"])
    grid_before = await world.saved_grid(session_factory, searcher["id"])

    for prompt in ("KEEP_THIS_RADIUS", "REFRESH_YOUR_TIMES", "UPDATE_PLAY_INTENT"):
        await world.decline_prompt(client, searcher["token"], prompt=prompt)

    assert await world.saved_radius_km(session_factory, searcher["id"]) == before
    assert await world.saved_grid(session_factory, searcher["id"]) == grid_before

"""*Let's play* — the two interest routes, over HTTP.

Every assertion lands on the real routes through the async client fixture: ASGI
transport over in-memory SQLite, **no MinIO, no sidecar and no Redis**.

What is asserted is the product's promises rather than the plumbing. That one tap
costs nothing and does something. That **nobody is ever shown an inbox**, so
saying yes stays low-stakes. That a yes is **dated at birth** and the client is
never asked to compute an expiry. That the cap **refuses** rather than quietly
shortening something the player was never shown. And that the ``+14`` reaches the
next search **printed**, so a lift is never mistaken for a match.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from sqlalchemy import select

from app.api.dependencies import ClockDep, DbSession, UnitOfWorkDep
from app.modules.matchmaking.infrastructure.interest_model import InterestORM
from app.bootstrap.composition import (
    build_interest_ledger,
    build_mutual_challenge_minting,
    build_ruleset,
    build_search_store,
)
from app.modules.matchmaking.application.express_interest import ExpressInterest
from app.modules.matchmaking.presentation.dependencies import get_express_interest
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


@pytest.fixture
async def a_city(client, session_factory, candidate_source, searcher):
    """One searcher and one findable candidate. The smallest honest world."""

    other = await world.a_candidate(
        client, session_factory, "bea", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)
    return other


# ---------------------------------------------------------------------------
# One tap
# ---------------------------------------------------------------------------


async def test_one_tap_records_a_yes_dated_at_birth(client, searcher, a_city):
    """**The expiry is on the row from the moment it is created.**

    The client renders a moment the backend computed rather than deriving one:
    a phone in somebody's hand can be months behind the backend, which is why
    the window itself never crosses the wire as a number.
    """

    found = (await world.search(client, searcher["token"])).json()

    response = await world.express_interest(
        client,
        searcher["token"],
        player_id=a_city,
        search_id=found["search"]["search_id"],
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["interest"]["player_id"] == str(a_city)
    at = datetime.fromisoformat(body["interest"]["at"])
    expires = datetime.fromisoformat(body["interest"]["expires_at"])
    assert expires > at
    assert body["mutual"] is False, "a one-sided yes is not a match"
    assert body["outstanding"]["outstanding"] == 1
    assert body["outstanding"]["cap"] >= 1


async def test_a_second_tap_creates_nothing_and_extends_nothing(
    client, searcher, a_city
):
    """**Idempotent per (from, to, sport)**, and — the part that matters — the
    expiry does not move.

    A button that says it costs nothing must not be a way to keep a yes alive for
    ever, which is what re-dating on every tap would be.
    """

    found = (await world.search(client, searcher["token"])).json()
    first = await world.express_interest(
        client,
        searcher["token"],
        player_id=a_city,
        search_id=found["search"]["search_id"],
    )

    again = await world.search(client, searcher["token"])
    second = await world.express_interest(
        client,
        searcher["token"],
        player_id=a_city,
        search_id=again.json()["search"]["search_id"],
    )

    assert first.status_code == 201
    assert second.status_code == 200, "a repeat tap is not an error"
    assert (
        second.json()["interest"]["expires_at"]
        == first.json()["interest"]["expires_at"]
    )
    assert second.json()["outstanding"]["outstanding"] == 1

    listed = (await world.read_interest(client, searcher["token"])).json()
    assert len(listed["outgoing"]) == 1, "a second tap became a second row"


async def test_a_lapsed_yes_can_be_sent_again_without_waiting_for_the_sweep(
    client, session_factory, searcher, a_city
):
    """**The expiry loop is a tidy-up and never load-bearing for a write.**

    A lapsed row still occupies its key until the sweep gets to it, and the key
    is exactly `(from, to, sport)`. Nothing here waits for the loop: the yes
    lapsed, so the next one is a **new** yes with its own expiry, at `201`.

    Written as an HTTP case because the failure it guards is a `500` — the one
    shape of refusal this feature has no code for, and the one a player would
    hit by doing the most ordinary thing there is: asking again, later.
    """

    found = (await world.search(client, searcher["token"])).json()
    first = await world.express_interest(
        client,
        searcher["token"],
        player_id=a_city,
        search_id=found["search"]["search_id"],
    )
    assert first.status_code == 201, first.text
    await _age_every_yes(session_factory, by=timedelta(days=30))

    again = await world.search(client, searcher["token"])
    second = await world.express_interest(
        client,
        searcher["token"],
        player_id=a_city,
        search_id=again.json()["search"]["search_id"],
    )

    assert second.status_code == 201, second.text
    assert (
        second.json()["interest"]["expires_at"]
        != first.json()["interest"]["expires_at"]
    ), "the lapsed yes was resurrected rather than replaced"
    listed = (await world.read_interest(client, searcher["token"])).json()
    assert len(listed["outgoing"]) == 1


async def test_a_yes_citing_somebody_elses_search_is_refused(
    client, session_factory, candidate_source, searcher, a_city
):
    """**The origin key is refused, never linked as null.**

    A silently dropped link is a denominator that lies, and *interests per
    search* is how this engine is judged.
    """

    stranger = await world.a_searcher(client, name="stranger")
    await world.fold_the_log(session_factory, candidate_source)
    theirs = (await world.search(client, stranger["token"])).json()

    response = await world.express_interest(
        client,
        searcher["token"],
        player_id=a_city,
        search_id=theirs["search"]["search_id"],
    )

    assert response.status_code == 409, response.text
    assert response.json()["code"] == "origin_search_not_found"


async def test_a_yes_at_somebody_that_search_never_showed_is_refused(
    client, session_factory, candidate_source, searcher, a_city
):
    """The position has to resolve against a **returned** row or there is no
    origin key — and a link that cannot be made true is not a link to drop
    quietly."""

    unseen = await world.a_candidate(
        client,
        session_factory,
        "far-away",
        mu=searcher["mu"],
        # Comfortably outside the searcher's ten-kilometre ring.
        latitude=52.20,
    )
    await world.fold_the_log(session_factory, candidate_source)
    found = (await world.search(client, searcher["token"])).json()
    assert str(unseen) not in {
        row["player_id"] for row in found["candidates"]
    }

    response = await world.express_interest(
        client,
        searcher["token"],
        player_id=unseen,
        search_id=found["search"]["search_id"],
    )

    assert response.status_code == 409
    assert response.json()["code"] == "origin_search_not_found"


async def test_an_unknown_search_answers_exactly_as_a_foreign_one(
    client, searcher, a_city
):
    """Four refusals, one code. Telling them apart would answer *does this
    ``search_id`` exist* for a stranger's id."""

    response = await world.express_interest(
        client,
        searcher["token"],
        player_id=a_city,
        search_id="99999999-9999-9999-9999-999999999999",
    )

    assert response.status_code == 409
    assert response.json()["code"] == "origin_search_not_found"


# ---------------------------------------------------------------------------
# The cap
# ---------------------------------------------------------------------------


async def test_the_cap_refuses_rather_than_making_room(
    client, session_factory, candidate_source, searcher
):
    """**Nothing of the player's is quietly shortened to make room.**

    The soft cap — *past it the oldest decays faster* — reaches backwards and
    shortens yeses already sent, under a rule the player was never told, because
    a twenty-first arrived (``docs/adr/0127`` §3). This refuses instead.

    The cap is driven down to one for this test rather than twenty candidates
    being stood up, because what is under test is the refusal and not the
    integer: the number is a ruleset row and the *shape* around it — the refusal
    code and the outstanding/cap pair — is what is contract.
    """

    first = await world.a_candidate(
        client, session_factory, "bea", mu=searcher["mu"]
    )
    second = await world.a_candidate(
        client, session_factory, "cai", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)
    _cap_at(client, one=1)

    found = (await world.search(client, searcher["token"])).json()
    search_id = found["search"]["search_id"]
    allowed = await world.express_interest(
        client, searcher["token"], player_id=first, search_id=search_id
    )
    refused = await world.express_interest(
        client, searcher["token"], player_id=second, search_id=search_id
    )

    assert allowed.status_code == 201, allowed.text
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "outstanding_interest_cap_reached"

    listed = (await world.read_interest(client, searcher["token"])).json()
    assert len(listed["outgoing"]) == 1, "the yes already sent was shortened"


async def test_the_cap_is_shown_before_it_bites(client, searcher, a_city):
    """**A cap the player cannot see is a refusal they cannot predict.**

    Sent for every sport, on every read, whether or not the player is anywhere
    near it — a limit that only appears once you are close to it arrives as a
    surprise.
    """

    listed = (await world.read_interest(client, searcher["token"])).json()

    assert listed["outstanding"], "no cap was shown at all"
    for entry in listed["outstanding"]:
        assert entry["cap"] >= 1
        assert entry["outstanding"] == 0
    assert len({entry["sport"] for entry in listed["outstanding"]}) == len(
        listed["outstanding"]
    ), "a sport was listed twice"


# ---------------------------------------------------------------------------
# What the recipient is told, which is nothing
# ---------------------------------------------------------------------------


async def test_a_one_sided_yes_is_never_revealed_to_its_recipient(
    client, session_factory, candidate_source, searcher
):
    """**There is no inbox**, and that is what keeps saying yes low-stakes.

    The recipient here is a full player with their own routes; they read their
    own interest and are told nothing at all about the yes pointed at them.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=searcher,
        towards=other["id"],
    )

    theirs = (await world.read_interest(client, other["token"])).json()

    assert theirs["outgoing"] == []
    assert theirs["mutual"] == []
    assert str(searcher["id"]) not in theirs["outgoing"].__str__()
    # And there is nowhere in the shape for one to appear later.
    assert set(theirs) == {"outgoing", "mutual", "outstanding"}


async def test_a_mutual_yes_is_told_to_both_sides(
    client, session_factory, candidate_source, searcher
):
    """The one shape in which somebody else's yes reaches them — and it reaches
    them only because they said it back."""

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=searcher,
        towards=other["id"],
    )

    back = await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=other,
        towards=searcher["id"],
    )

    assert back.json()["mutual"] is True, "the second yes was not told it landed"
    mine = (await world.read_interest(client, searcher["token"])).json()
    theirs = (await world.read_interest(client, other["token"])).json()
    assert [row["player_id"] for row in mine["mutual"]] == [str(other["id"])]
    assert [row["player_id"] for row in theirs["mutual"]] == [str(searcher["id"])]
    assert mine["outgoing"] == [], "a mutual is still listed as in flight"


async def test_a_mutual_stops_counting_against_the_cap(
    client, session_factory, candidate_source, searcher
):
    """**Outstanding means sent, unexpired and not yet mutual.** A mutual has been
    answered and is no longer in flight, which is the one way room opens up other
    than waiting."""

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=searcher,
        towards=other["id"],
    )
    before = (await world.read_interest(client, searcher["token"])).json()

    await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=other,
        towards=searcher["id"],
    )
    after = (await world.read_interest(client, searcher["token"])).json()

    assert _padel(before)["outstanding"] == 1
    assert _padel(after)["outstanding"] == 0


# ---------------------------------------------------------------------------
# The lift
# ---------------------------------------------------------------------------


async def test_the_lift_reaches_the_next_search_printed(
    client, session_factory, candidate_source, searcher
):
    """**A player is told when somebody was shown to them because that person
    said *Let's play* first.**

    Two things print, and they are two different sentences: the liveness reason
    says *they moved for this*, and the inclusion reason says *this is why they
    are here at all*. Only the second can admit somebody below the floor, which
    is why it is the only inclusion reason that crosses the wire.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=other,
        towards=searcher["id"],
    )

    found = (await world.search(client, searcher["token"])).json()

    row = next(
        candidate
        for candidate in found["candidates"]
        if candidate["player_id"] == str(other["id"])
    )
    assert "INTEREST_RECEIVED" in row["liveness_reasons"]
    assert row["inclusion_reason"] == "INTEREST_LIFT"
    assert "liveness" not in row, "the offset itself must never cross"


async def test_the_lift_is_recorded_with_the_age_of_the_yes_and_never_a_boolean(
    client, session_factory, candidate_source, searcher
):
    """``search-telemetry.md`` §3: the raw input is the **age in days**.

    The ``+14`` is flat, so a boolean would be the *sufficient* input and the age
    — the entire x-axis of *acceptance by age of yes* — would be gone within the
    month. The **offset** is never stored, because it is a function of the
    ruleset's bounds and storing it would make a bounds change undiffable.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=other,
        towards=searcher["id"],
    )
    found = (await world.search(client, searcher["token"])).json()

    rows = await world.recorded_candidates(
        session_factory, found["search"]["search_id"]
    )

    lifted = next(
        row for row in rows if row.player_id == other["id"]
    )
    assert lifted.liveness_signals["INTEREST_RECEIVED"] == 0
    assert lifted.inclusion_reason == "INTEREST_LIFT"


async def test_the_lift_is_gone_the_day_the_yes_lapses(
    client, session_factory, candidate_source, searcher
):
    """**A cliff, and the cliff is the price** (``docs/adr/0127``).

    A candidate lifted on a twenty-day-old yes is not lifted the next morning.
    The soft version would have faded them out instead, and a fade is
    unexplainable where a cliff is at least dated — ``expires_at`` was on the row
    from the first day.

    Nothing has swept the row: expiry is a **date**, and the sweep is a tidy-up.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client,
        session_factory,
        candidate_source,
        sender=other,
        towards=searcher["id"],
    )
    await _age_every_yes(session_factory, by=timedelta(days=30))

    found = (await world.search(client, searcher["token"])).json()

    row = next(
        candidate
        for candidate in found["candidates"]
        if candidate["player_id"] == str(other["id"])
    )
    assert "INTEREST_RECEIVED" not in row["liveness_reasons"]
    assert "inclusion_reason" not in row
    assert row["player_id"] == str(other["id"]), (
        "a lapsed yes removed the person rather than the lift"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _padel(listed: dict) -> dict:
    return next(
        entry for entry in listed["outstanding"] if entry["sport"] == "PADEL"
    )


def _cap_at(client, *, one: int) -> None:
    """Run the write path against a ruleset whose cap is a smaller integer.

    The cap is ruleset configuration and the **refusal** is contract, so a test
    that stood up twenty candidates to reach it would be testing the integer —
    and would go red the day somebody released a different one. What is asserted
    below is the shape: refused at the cap, with a closed code, and nothing of
    the player's shortened.

    The override rebuilds the same use case the route would have got, from the
    same composition root, with one field of the ruleset replaced.
    """

    ruleset = build_ruleset()
    tightened = replace(
        ruleset, interest=replace(ruleset.interest, outstanding_cap_per_sport=one)
    )

    def factory(
        db: DbSession, clock: ClockDep, uow: UnitOfWorkDep
    ) -> ExpressInterest:
        return ExpressInterest(
            clock=clock,
            ruleset=tightened,
            interest=build_interest_ledger(db),
            searches=build_search_store(db),
            challenges=build_mutual_challenge_minting(db),
            unit_of_work=uow,
        )

    world.override(client, get_express_interest, factory)


async def _age_every_yes(session_factory, *, by: timedelta) -> None:
    """Move every yes backwards in time, sent date and expiry together.

    The rows are aged rather than the clock being moved forward, because moving
    the clock would also age the candidate index past its own staleness ladder —
    the test would then be asserting a refusal instead of a lift, and would pass
    for the wrong reason. Both columns move by the same amount, so the yes is one
    that was sent thirty days ago and lapsed nine days later, which is exactly the
    state under test.
    """

    async with session_factory() as session:
        rows = (await session.scalars(select(InterestORM))).all()
        for row in rows:
            row.sent_at = row.sent_at - by
            row.expires_at = row.expires_at - by
        await session.commit()

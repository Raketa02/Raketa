"""The five plan routes, end to end over HTTP — and the thing they sit between.

The whole reachable path in one file: a searcher builds a court, sends it,
somebody says yes — and from that yes there is a plan. The rest of the court
filling is what moves the anchor and admits the lock, and that ordering is the
point of this file rather than a set-up cost (``docs/adr/0164``).

Seven things are asserted here and nowhere else:

**A plan is the challenge's, and it exists from the first yes.** ``GET /plans``
lists one row for every court the reader holds an accepted seat on, written or
not, keyed by ``challenge_id``; an invitee still deciding and somebody who said
no get no row.

**A plan is born by being used.** There is no route that creates one and none
that destroys one; a court nobody has written on is a row with three empty
slots, and the first slot write is the birth in the store.

**The anchor is the send until the game exists, then ``planned_at``**, and it
only ever moves later — so a day refused before the court fills can be admitted
after it does.

**The lock waits for the court.** Two of four may set where, day and hour and
may not agree them for four; the refusal has its own code; the lock is admitted
once the last seat accepts; and a lock already taken survives a later departure.

**A write of the value already there answers 200.** From the outside that is
indistinguishable from a write that changed something — which is the whole idea.

**Bounded chips the platform offered, never a free instant.** The horizon, the
grid and the moment that has gone, each refused server-side.

**A plan carries no ``read_at``**, so Now has one clock by construction.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.api.dependencies import get_clock
from app.kernel import Sport, instant
from app.modules.games.domain.windows import PLAN_HORIZON
from app.modules.plans.domain.slots import (
    PLACE_LENGTH_CAP,
    PLATFORM_ZONE,
    last_plannable_day,
    local_day,
)
from tests.api import matchmaking_world as world
from tests.unit.fake_event_store import FrozenClock


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


@pytest.fixture
def clock(client):
    """The API's clock, stopped where this file starts and moved by hand.

    Handed to the application through the dependency a request resolves, so the
    instant a court fills — and with it the plan's anchor — is the test's own.
    """

    frozen = FrozenClock(at=datetime.now(timezone.utc))
    world.override(client, get_clock, lambda: frozen)
    return frozen


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _a_padel_four_sent(client, session_factory, candidate_source, searcher):
    """A padel four sent to three people, none of whom has answered yet.

    Built from a real search so every seat has an origin, exactly as a phone
    would send it. The answers are the tests' own, one at a time, because which
    yes has arrived is the whole of what this file is about.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
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
    return people, sent.json()["challenge_id"]


async def _accept(client, token: str, challenge_id: str) -> dict:
    answered = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept", headers=world.auth(token)
    )
    assert answered.status_code == 200, answered.text
    return answered.json()


async def _the_game(client, token: str, challenge_id: str) -> dict:
    games = await client.get("/api/v1/games", headers=world.auth(token))
    assert games.status_code == 200, games.text
    (game,) = [
        one for one in games.json()["games"] if one["challenge_id"] == challenge_id
    ]
    return game


async def _an_arranged_game(client, session_factory, candidate_source, searcher):
    """A game nobody asked for: four seats, all accepted, nothing played yet.

    **The outbox is drained before anybody plans anything**, which is what an API
    process does on its own and what this suite has to do by hand.
    """

    people, challenge_id = await _a_padel_four_sent(
        client, session_factory, candidate_source, searcher
    )
    for person in people.values():
        await _accept(client, person["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    return (
        people,
        await _the_game(client, searcher["token"], challenge_id),
        challenge_id,
    )


async def _plans(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/plans", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["plans"]


async def _plan_of(client, token: str, challenge_id: str) -> dict:
    (plan,) = [
        one
        for one in await _plans(client, token)
        if one["challenge_id"] == challenge_id
    ]
    return plan


async def _put(client, token: str, challenge_id: str, slot: str, body: dict):
    return await client.put(
        f"/api/v1/plans/{challenge_id}/{slot}", json=body, headers=world.auth(token)
    )


async def _lock(client, challenge_id: str, token: str):
    return await client.put(
        f"/api/v1/plans/{challenge_id}/lock", headers=world.auth(token)
    )


def _the_day_it_was_arranged(game: dict) -> date:
    """The **local** day this game was arranged on, in the platform's own zone.

    Read the way the clamp reads it and not off the first ten characters of the
    instant: ``last_plannable_day`` converts through the platform's zone before
    taking a date, so between 22:00 and midnight UTC the UTC date is a day behind
    the day the platform is having — and a test that did the arithmetic in UTC
    would be off by one for two hours out of every twenty-four. Through the
    domain's own ``local_day``, so there is one answer to *what day is it*.
    """

    return local_day(instant(datetime.fromisoformat(game["planned_at"])))


def _a_plannable_day(game: dict) -> str:
    """A day inside this game's own horizon, read off the game's own record."""

    return (_the_day_it_was_arranged(game) + timedelta(days=2)).isoformat()


def _instant(text: str) -> datetime:
    """An instant off the wire, compared as one rather than as its spelling."""

    return datetime.fromisoformat(text)


# ---------------------------------------------------------------------------
# From the first yes
# ---------------------------------------------------------------------------


async def test_the_first_yes_lists_the_court_for_both_with_nothing_agreed(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0164`` §3–§4 — after the first acceptance on a doubles,
    ``GET /plans`` lists the court for the organiser and for the one who said
    yes: three empty slots, nothing locked, and the anchor at the **send**. An
    invitee still deciding and one who said no get no row, and are told the same
    thing when they try to write."""

    people, challenge_id = await _a_padel_four_sent(
        client, session_factory, candidate_source, searcher
    )
    sent_at = clock.at
    clock.at = sent_at + timedelta(hours=1)
    await _accept(client, people["ana"]["token"], challenge_id)
    declined = await client.post(
        f"/api/v1/challenges/{challenge_id}/decline",
        headers=world.auth(people["cy"]["token"]),
    )
    assert declined.status_code == 200, declined.text

    for who in (searcher, people["ana"]):
        (plan,) = await _plans(client, who["token"])
        assert _instant(plan.pop("anchor")) == sent_at, "anchored at the send"
        assert plan == {
            "challenge_id": challenge_id,
            "place": None,
            "day": None,
            "hour": None,
            "agreed_point": None,
            "locked_at": None,
        }
    for who in (people["bo"], people["cy"]):
        assert await _plans(client, who["token"]) == []
        refused = await _put(
            client, who["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
        )
        assert refused.status_code == 404, refused.text
        assert refused.json()["code"] == "plan_not_found"


async def test_slots_written_before_the_court_is_whole_are_read_back_after_it_fills(
    client, session_factory, candidate_source, searcher, clock
):
    """The plan is the same plan: what two of four agreed is what four read, and
    the anchor on the row moves to the instant the court filled — **later, never
    earlier**."""

    people, challenge_id = await _a_padel_four_sent(
        client, session_factory, candidate_source, searcher
    )
    sent_at = clock.at
    await _accept(client, people["ana"]["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    written = await _put(
        client,
        people["ana"]["token"],
        challenge_id,
        "place",
        {"place": "Zabłocie Sport"},
    )
    assert written.status_code == 200, written.text
    assert _instant(written.json()["anchor"]) == sent_at

    clock.at = sent_at + timedelta(hours=3)
    for name in ("bo", "cy"):
        await _accept(client, people[name]["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    game = await _the_game(client, searcher["token"], challenge_id)

    for who in [searcher] + list(people.values()):
        plan = await _plan_of(client, who["token"], challenge_id)
        assert plan["place"] == "Zabłocie Sport"
        assert plan["anchor"] == game["planned_at"]
        assert _instant(plan["anchor"]) > sent_at


async def test_the_lock_waits_for_the_court_and_survives_a_later_departure(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0164`` §5 — two of four may fill every slot and may not agree
    them for four: `the_court_is_not_whole`, its own code beside
    `the_plan_is_not_complete`. Admitted once the last seat accepts. A lock
    already taken survives somebody leaving afterwards, and asking again on the
    reopened court is the idempotent `200` it always was."""

    people, challenge_id = await _a_padel_four_sent(
        client, session_factory, candidate_source, searcher
    )
    await _accept(client, people["ana"]["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    day = (local_day(instant(clock.at)) + timedelta(days=2)).isoformat()
    for slot, body in (
        ("place", {"place": "Zabłocie Sport"}),
        ("day", {"day": day}),
        ("hour", {"hour": "18:00"}),
    ):
        written = await _put(client, people["ana"]["token"], challenge_id, slot, body)
        assert written.status_code == 200, written.text
        await world.deliver_the_outbox(session_factory)

    refused = await _lock(client, challenge_id, people["ana"]["token"])
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "the_court_is_not_whole"
    assert (await _plan_of(client, searcher["token"], challenge_id))[
        "locked_at"
    ] is None

    for name in ("bo", "cy"):
        await _accept(client, people[name]["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    locked = await _lock(client, challenge_id, people["bo"]["token"])
    assert locked.status_code == 200, locked.text
    assert locked.json()["locked_at"] is not None
    await world.deliver_the_outbox(session_factory)

    left = await client.post(
        f"/api/v1/challenges/{challenge_id}/departure",
        headers=world.auth(people["cy"]["token"]),
    )
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "LINE_UP_INCOMPLETE"
    plan = await _plan_of(client, searcher["token"], challenge_id)
    assert plan["locked_at"] == locked.json()["locked_at"], "the lock survives"
    again = await _lock(client, challenge_id, searcher["token"])
    assert again.status_code == 200, again.text
    assert again.json()["locked_at"] == locked.json()["locked_at"]
    assert await _plans(client, people["cy"]["token"]) == [], (
        "the leaver is not on the court, so the plan is not theirs"
    )


async def test_a_lock_on_a_whole_court_with_a_slot_empty_is_refused_on_the_count(
    client, session_factory, candidate_source, searcher
):
    """The two refusals are two codes: once the court is whole, an empty slot is
    `the_plan_is_not_complete` — the greyed button, not the count line."""

    people, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    await _put(client, searcher["token"], challenge_id, "place", {"place": "Zabłocie"})

    refused = await _lock(client, challenge_id, searcher["token"])

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "the_plan_is_not_complete"


async def test_a_day_past_the_sends_horizon_is_admitted_once_the_court_fills_later(
    client, session_factory, candidate_source, searcher, clock
):
    """``docs/adr/0164`` §4 — before the game exists the horizon runs from the
    send; once it exists, from ``planned_at``. A court that fills a day after
    it was sent widens the week by a day, so the day refused before is admitted
    after — and the anchor is what the row said it was each time."""

    people, challenge_id = await _a_padel_four_sent(
        client, session_factory, candidate_source, searcher
    )
    sent_at = clock.at
    await _accept(client, people["ana"]["token"], challenge_id)
    one_past = last_plannable_day(instant(sent_at)) + timedelta(days=1)

    refused = await _put(
        client,
        people["ana"]["token"],
        challenge_id,
        "day",
        {"day": one_past.isoformat()},
    )
    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "the_day_is_past_the_horizon"

    clock.at = sent_at + timedelta(days=1)
    for name in ("bo", "cy"):
        await _accept(client, people[name]["token"], challenge_id)
    await world.deliver_the_outbox(session_factory)
    plan = await _plan_of(client, searcher["token"], challenge_id)
    assert one_past <= last_plannable_day(
        instant(datetime.fromisoformat(plan["anchor"]))
    )

    admitted = await _put(
        client,
        people["ana"]["token"],
        challenge_id,
        "day",
        {"day": one_past.isoformat()},
    )
    assert admitted.status_code == 200, admitted.text
    assert admitted.json()["day"] == one_past.isoformat()


async def test_before_the_first_yes_there_is_no_plan_even_for_the_organiser(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0164`` §2 — a plan exists from the first yes. The organiser's
    own seat is accepted from birth and makes no court on its own, so there is
    no row and the write is refused as a stranger's."""

    _, challenge_id = await _a_padel_four_sent(
        client, session_factory, candidate_source, searcher
    )

    assert await _plans(client, searcher["token"]) == []
    refused = await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
    )
    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "plan_not_found"


async def test_a_court_that_ended_after_a_yes_is_history_and_still_listed(
    client, session_factory, candidate_source, searcher
):
    """B said yes, the other two said no, and the organiser left: B is alone
    with nobody deciding, so the court is over by itself (``docs/adr/0165``
    §3). It had a yes, so its plan is a row that no longer moves rather than
    an absence — for B, who is still on it; the organiser left it, and has no
    row to be history."""

    people, challenge_id = await _a_padel_four_sent(
        client, session_factory, candidate_source, searcher
    )
    await _accept(client, people["ana"]["token"], challenge_id)
    for name in ("bo", "cy"):
        declined = await client.post(
            f"/api/v1/challenges/{challenge_id}/decline",
            headers=world.auth(people[name]["token"]),
        )
        assert declined.status_code == 200, declined.text
    left = await client.post(
        f"/api/v1/challenges/{challenge_id}/departure",
        headers=world.auth(searcher["token"]),
    )
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "DECLINED"

    frozen = await _put(
        client, people["ana"]["token"], challenge_id, "place", {"place": "Zabłocie"}
    )

    assert frozen.status_code == 409, frozen.text
    assert frozen.json()["code"] == "plan_is_history"
    hers = await _plans(client, people["ana"]["token"])
    assert [one["challenge_id"] for one in hers] == [challenge_id]
    assert await _plans(client, searcher["token"]) == []
    gone = await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Zabłocie"}
    )
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "plan_not_found"


async def test_a_singles_court_lists_its_plan_as_before_addressed_by_the_challenge(
    client, session_factory, candidate_source
):
    """Singles: the one yes completes the court, so the game exists at once
    and the plan is whole from birth — anchored on ``planned_at``, lockable
    once the three slots are set, keyed by the challenge the game carries."""

    sender = await world.a_searcher(client, "juno", sport=Sport.TENNIS)
    invitee = await world.a_searcher(client, "milo", sport=Sport.TENNIS)
    await world.fold_the_log(session_factory, candidate_source)
    found = await world.search(client, sender["token"], sport=Sport.TENNIS)
    assert found.status_code == 200, found.text
    sent = await client.post(
        "/api/v1/challenges",
        json={
            "search_id": found.json()["search"]["search_id"],
            "court": [
                {"side": "A", "player_id": str(sender["id"])},
                {"side": "B", "player_id": str(invitee["id"])},
            ],
        },
        headers=world.auth(sender["token"]),
    )
    assert sent.status_code == 201, sent.text
    challenge_id = sent.json()["challenge_id"]
    assert (await _accept(client, invitee["token"], challenge_id))["standing"] == "ON"
    await world.deliver_the_outbox(session_factory)
    game = await _the_game(client, sender["token"], challenge_id)
    assert game["challenge_id"] == challenge_id

    (plan,) = await _plans(client, invitee["token"])
    assert plan["challenge_id"] == challenge_id
    assert plan["anchor"] == game["planned_at"]
    for slot, body in (
        ("place", {"place": "Zabłocie Sport"}),
        ("day", {"day": _a_plannable_day(game)}),
        ("hour", {"hour": "18:00"}),
    ):
        written = await _put(client, invitee["token"], challenge_id, slot, body)
        assert written.status_code == 200, written.text
        await world.deliver_the_outbox(session_factory)
    locked = await _lock(client, challenge_id, sender["token"])
    assert locked.status_code == 200, locked.text
    assert locked.json()["locked_at"] is not None


async def test_a_mutual_interest_opening_lists_its_plan_as_before(
    client, session_factory, candidate_source
):
    """The mutual-born singles is ``ON`` the instant it exists, so its game
    exists at once and its plan is whole from birth, addressed by the
    challenge the second yes minted (``docs/adr/0154``)."""

    one = await world.a_searcher(client, "juno", sport=Sport.TENNIS)
    other = await world.a_searcher(client, "milo", sport=Sport.TENNIS)
    await world.fold_the_log(session_factory, candidate_source)
    for sender, towards in ((one, other), (other, one)):
        found = await world.search(client, sender["token"], sport=Sport.TENNIS)
        assert found.status_code == 200, found.text
        said = await world.express_interest(
            client,
            sender["token"],
            player_id=towards["id"],
            search_id=found.json()["search"]["search_id"],
            sport=Sport.TENNIS,
        )
        assert said.status_code in (200, 201), said.text
    assert said.json()["mutual"] is True
    challenge_id = said.json()["challenge_id"]
    assert challenge_id is not None, "the mutual names the game it has"
    await world.deliver_the_outbox(session_factory)
    game = await _the_game(client, one["token"], challenge_id)

    for who in (one, other):
        (plan,) = await _plans(client, who["token"])
        assert plan["challenge_id"] == challenge_id
        assert plan["anchor"] == game["planned_at"]
        assert plan["place"] is None
    written = await _put(
        client, other["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
    )
    assert written.status_code == 200, written.text


# ---------------------------------------------------------------------------
# Born by being used
# ---------------------------------------------------------------------------


async def test_a_court_with_nothing_agreed_is_a_row_with_three_empty_slots(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0164`` §4 — no record at birth, and a row with three nulls is
    what a court with nothing agreed draws, so a client has the anchor and knows
    there is a plan to draw before anybody has written on it."""

    _, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    assert await _plans(client, searcher["token"]) == [
        {
            "challenge_id": challenge_id,
            "place": None,
            "day": None,
            "hour": None,
            "agreed_point": None,
            "anchor": game["planned_at"],
            "locked_at": None,
        }
    ]


async def test_the_first_slot_write_is_the_birth_and_answers_the_whole_plan(
    client, session_factory, candidate_source, searcher
):
    _, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    written = await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
    )

    assert written.status_code == 200, written.text
    assert written.json() == {
        "challenge_id": challenge_id,
        "place": "Zabłocie Sport",
        "day": None,
        "hour": None,
        "agreed_point": None,
        "anchor": game["planned_at"],
        "locked_at": None,
    }
    assert await _plans(client, searcher["token"]) == [written.json()]


async def test_there_is_no_route_that_creates_or_destroys_a_plan(app):
    """A plan is born by being used and **is never unmade** — nobody turns up and
    the game ghosts, which is the record this platform keeps instead of a
    cancellation.

    ``lock`` arrived with ``docs/adr/0155`` and ``unlock`` did not: the lock is a
    thing that happened, so it has a route and its undoing has none. And every
    write is addressed by the **challenge's** id (``docs/adr/0164`` §1).
    """

    plan_routes = {
        (route.path, method)
        for route in app.routes
        if getattr(route, "path", "").startswith("/api/v1/plans")
        for method in getattr(route, "methods", ())
    }

    assert {method for _, method in plan_routes} == {"GET", "PUT"}
    assert {path for path, method in plan_routes if method == "PUT"} == {
        f"/api/v1/plans/{{challenge_id}}/{slot}"
        for slot in ("place", "day", "hour", "lock")
    }
    assert not any(
        segment in path
        for path, _ in plan_routes
        for segment in ("unlock", "cancel", "clear", "game_id")
    )


# ---------------------------------------------------------------------------
# Any member, any slot, any number of times — and the value is the key
# ---------------------------------------------------------------------------


async def test_any_member_may_fill_or_change_any_slot(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — there is no lock and no rate limit; *the line is the
    friction*. Nothing requires the person who fills a slot to be the person who
    proposed it."""

    people, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    day = _a_plannable_day(game)

    first = await _put(client, searcher["token"], challenge_id, "day", {"day": day})
    moved = await _put(
        client,
        people["ana"]["token"],
        challenge_id,
        "day",
        {"day": (date.fromisoformat(day) + timedelta(days=1)).isoformat()},
    )

    assert first.status_code == 200, first.text
    assert moved.status_code == 200, moved.text
    assert moved.json()["day"] != first.json()["day"]


async def test_writing_the_value_already_there_answers_two_hundred(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0148`` §8 — the same answer as the write that set it."""

    people, _, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    once = await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
    )
    again = await _put(
        client,
        people["ana"]["token"],
        challenge_id,
        "place",
        {"place": "Zabłocie Sport"},
    )

    assert once.status_code == again.status_code == 200
    assert once.json() == again.json()


# ---------------------------------------------------------------------------
# Bounded chips the platform offered
# ---------------------------------------------------------------------------


async def test_a_day_past_the_horizon_is_refused(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — the clamp, so a plan can never name a day past the
    entry window and a card cannot walk from *Game on* to *Never played* while
    the plan still reads *next Saturday*."""

    _, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    planned = _the_day_it_was_arranged(game)

    refused = await _put(
        client,
        searcher["token"],
        challenge_id,
        "day",
        {"day": (planned + PLAN_HORIZON + timedelta(days=1)).isoformat()},
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "the_day_is_past_the_horizon"


@pytest.mark.parametrize(
    "hour", ["05:30", "23:30", "18:15", "18:00:30"], ids=lambda one: one
)
async def test_an_hour_nobody_offered_is_refused(
    client, session_factory, candidate_source, searcher, hour
):
    """``docs/adr/0145`` §9 — *bounded chips the platform offered, never a free
    instant*. The client's grid is a convention; this is what makes it true."""

    _, _, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    refused = await _put(
        client, searcher["token"], challenge_id, "hour", {"hour": hour}
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "the_hour_is_not_offered"


async def test_a_place_that_says_nothing_or_says_too_much_is_refused(
    client, session_factory, candidate_source, searcher
):
    """**A slot is never emptied**, so a blank value is not a way of clearing
    one; and an over-long note is refused rather than shortened."""

    _, _, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    empty = await _put(
        client, searcher["token"], challenge_id, "place", {"place": "   "}
    )
    too_long = await _put(
        client,
        searcher["token"],
        challenge_id,
        "place",
        {"place": "x" * (PLACE_LENGTH_CAP + 1)},
    )

    assert empty.json()["code"] == "the_place_is_empty"
    assert too_long.json()["code"] == "the_place_is_too_long"


async def test_a_moment_already_in_the_past_is_refused_in_either_order(
    client, session_factory, candidate_source, searcher
):
    """``the-words.md`` §22.2 — one refusal naming both remedies, because the day
    and the hour are filled in either order and either can be the second."""

    _, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    yesterday = date.fromisoformat(game["planned_at"][:10]) - timedelta(days=1)

    await _put(
        client, searcher["token"], challenge_id, "day", {"day": yesterday.isoformat()}
    )
    refused = await _put(
        client, searcher["token"], challenge_id, "hour", {"hour": "18:00"}
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "that_moment_has_already_passed"


# ---------------------------------------------------------------------------
# The gate: the port's one question, and its two answers
# ---------------------------------------------------------------------------


async def test_somebody_who_was_not_on_the_court_is_told_there_is_no_such_plan(
    client, session_factory, candidate_source, searcher
):
    """**One code for three cases** — no such challenge, a court that is not
    yours, and a seat you have not said yes to.

    A 403 would answer *is this id real* about four strangers' evening, which is
    ``challenge_not_found``'s argument verbatim.
    """

    _, _, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    _, stranger = await world.a_signed_in_candidate(
        client, session_factory, "stranger", mu=searcher["mu"]
    )

    refused = await _put(
        client, stranger, challenge_id, "place", {"place": "Zabłocie Sport"}
    )

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "plan_not_found"
    assert await _plans(client, stranger) == []


async def test_a_plan_read_is_scoped_to_your_own_courts_and_needs_no_refusal(
    client, session_factory, candidate_source, searcher
):
    """The read is gated without a gate: a court the reader holds no accepted
    seat on never becomes an id it asks about, so there is no id to refuse."""

    people, _, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
    )

    for token in [searcher["token"]] + [one["token"] for one in people.values()]:
        assert [one["challenge_id"] for one in await _plans(client, token)] == [
            challenge_id
        ]


# ---------------------------------------------------------------------------
# The agreed point, and the clock that is not here
# ---------------------------------------------------------------------------


async def test_the_agreed_point_appears_the_moment_a_day_does(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0145`` §3 — one value, defined whenever the day is, coarsened
    to the start of the following local day when no hour is recorded."""

    _, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    day = _a_plannable_day(game)

    with_a_day = await _put(
        client, searcher["token"], challenge_id, "day", {"day": day}
    )
    with_an_hour = await _put(
        client, searcher["token"], challenge_id, "hour", {"hour": "18:00"}
    )

    coarse = with_a_day.json()["agreed_point"]
    exact = with_an_hour.json()["agreed_point"]

    assert coarse is not None and exact is not None
    # Coarsened **later, never earlier** — so nobody is asked for a result
    # before they could have played.
    assert exact < coarse
    assert coarse.startswith(
        (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    ) or coarse.startswith(date.fromisoformat(day).isoformat())


async def test_an_hour_with_no_day_names_no_moment(
    client, session_factory, candidate_source, searcher
):
    """An hour alone anchors as little as an empty plan: 18:00 on no day is not a
    moment, and the coarsening rule is about the **day**."""

    _, _, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )

    written = await _put(
        client, searcher["token"], challenge_id, "hour", {"hour": "18:00"}
    )

    assert written.json()["hour"] == "18:00:00"
    assert written.json()["agreed_point"] is None


async def test_the_plan_list_carries_no_read_at(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0148`` §10 — a plan folds nothing against the clock, so there
    is no instant for it to have been folded against. **Now has one clock by
    construction**, and it is ``GET /games``'."""

    await _an_arranged_game(client, session_factory, candidate_source, searcher)

    response = await client.get("/api/v1/plans", headers=world.auth(searcher["token"]))

    assert set(response.json()) == {"plans"}


async def test_one_zone_reads_the_same_for_everybody_in_the_room(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — **one platform zone**, recorded as a locale assumption.

    Per-device zones were refused because they would show two people on one court
    two different hours for one agreement, and there is no club record to hold the
    true one. The falsifier is the first shard whose players are somewhere else.
    """

    people, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    day = _a_plannable_day(game)
    await _put(client, searcher["token"], challenge_id, "day", {"day": day})
    await _put(client, people["bo"]["token"], challenge_id, "hour", {"hour": "18:00"})

    seen = {
        (await _plans(client, token))[0]["agreed_point"]
        for token in [searcher["token"]] + [one["token"] for one in people.values()]
    }

    assert len(seen) == 1
    assert str(PLATFORM_ZONE) == "Europe/Warsaw"


# ---------------------------------------------------------------------------
# The freeze
# ---------------------------------------------------------------------------


async def test_saying_you_played_freezes_the_slots(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0144`` — **the game leaving its entry window is the only thing
    that freezes the slots**, and it is not a lock: once somebody has said *we
    played*, the plan is history.

    The plan is still readable, because the game screen draws it read-only for
    the whole of a game's life.
    """

    _, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
    )
    played = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    assert played.status_code == 200, played.text

    frozen = await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Hala Sportowa"}
    )

    assert frozen.status_code == 409, frozen.text
    assert frozen.json()["code"] == "plan_is_history"
    assert (await _plans(client, searcher["token"]))[0]["place"] == "Zabłocie Sport"


# ---------------------------------------------------------------------------
# The lock — an act, and not the third slot under another name
# ---------------------------------------------------------------------------


async def _a_complete_plan(client, session_factory, candidate_source, searcher):
    """A whole court whose three slots are all filled, and nobody has agreed it
    yet."""

    people, game, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    for slot, body in (
        ("place", {"place": "Zabłocie Sport"}),
        ("day", {"day": _a_plannable_day(game)}),
        ("hour", {"hour": "18:00"}),
    ):
        written = await _put(client, searcher["token"], challenge_id, slot, body)
        assert written.status_code == 200, written.text
        await world.deliver_the_outbox(session_factory)
    return people, game, challenge_id


async def test_a_complete_plan_is_not_a_locked_one(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0155`` — **the count and the lock are two facts.** Filling the
    third slot leaves ``locked_at`` null, because a complete plan is one
    everybody *could* agree and nobody has yet."""

    await _a_complete_plan(client, session_factory, candidate_source, searcher)

    (plan,) = await _plans(client, searcher["token"])

    assert plan["place"] and plan["day"] and plan["hour"]
    assert plan["locked_at"] is None


async def test_locking_answers_the_plan_carrying_the_moment_it_was_agreed(
    client, session_factory, candidate_source, searcher
):
    people, _, challenge_id = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )

    locked = await _lock(client, challenge_id, people["ana"]["token"])

    assert locked.status_code == 200, locked.text
    body = locked.json()
    assert body["locked_at"] is not None
    assert body["place"] == "Zabłocie Sport"
    assert await _plans(client, searcher["token"]) == [body]


async def test_an_incomplete_plan_refuses_the_lock(
    client, session_factory, candidate_source, searcher
):
    """A **conflict** and not a bad request: the body carried nothing at all, so
    there is no field to be wrong — what is wrong is the state of the plan.

    And a refusal rather than a silent `200`, which is the opposite shape from a
    second lock: a no-op here would leave a client believing it had agreed one.
    """

    _, _, challenge_id = await _an_arranged_game(
        client, session_factory, candidate_source, searcher
    )
    await _put(
        client, searcher["token"], challenge_id, "place", {"place": "Zabłocie Sport"}
    )

    refused = await _lock(client, challenge_id, searcher["token"])

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "the_plan_is_not_complete"
    assert (await _plans(client, searcher["token"]))[0]["locked_at"] is None


async def test_locking_an_already_locked_plan_answers_two_hundred_and_says_nothing(
    client, session_factory, candidate_source, searcher
):
    """This repository's idempotency language applied to an **act**: the same act
    twice lands the same state and records nothing. It is not a refusal, and the
    first lock's moment is the one that stands."""

    people, _, challenge_id = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )

    first = await _lock(client, challenge_id, searcher["token"])
    await world.deliver_the_outbox(session_factory)
    again = await _lock(client, challenge_id, people["ana"]["token"])
    await world.deliver_the_outbox(session_factory)

    assert first.status_code == again.status_code == 200
    assert first.json()["locked_at"] == again.json()["locked_at"]


async def test_a_locked_plan_is_not_a_frozen_one(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0155`` — locking freezes nothing, and ADR-0145 §5 stands:
    *there is no un-agreeing to fear, only re-agreeing, and any member may do
    that at any time*.

    The plan stays locked, and the move is admitted as every slot change is.
    """

    people, _, challenge_id = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    locked = await _lock(client, challenge_id, searcher["token"])
    await world.deliver_the_outbox(session_factory)

    moved = await _put(
        client, people["ana"]["token"], challenge_id, "hour", {"hour": "19:00"}
    )
    await world.deliver_the_outbox(session_factory)

    assert moved.status_code == 200, moved.text
    assert moved.json()["hour"] == "19:00:00"
    assert moved.json()["locked_at"] == locked.json()["locked_at"]


async def test_somebody_who_was_not_on_the_court_cannot_lock_and_is_told_nothing(
    client, session_factory, candidate_source, searcher
):
    """The gate first, and it is the slot writes' gate exactly — **one code for
    three cases**, because a 403 would answer *is this id real* about four
    strangers' evening."""

    _, _, challenge_id = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    _, stranger = await world.a_signed_in_candidate(
        client, session_factory, "stranger", mu=searcher["mu"]
    )

    refused = await _lock(client, challenge_id, stranger)

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "plan_not_found"


async def test_a_held_account_may_not_lock(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0148`` §9 — **a hold refuses a lock exactly as it refuses a
    slot write**, because a lock is a write other people read. It refuses no
    read: the plan is still there to look at."""

    _, _, challenge_id = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    world.hold_everybody_planning(client)

    refused = await _lock(client, challenge_id, searcher["token"])

    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "account_held"
    assert (await _plans(client, searcher["token"]))[0]["locked_at"] is None


async def test_a_game_that_is_history_refuses_the_lock(
    client, session_factory, candidate_source, searcher
):
    """The freeze reaches the lock as it reaches the three slots: once *we
    played* has been said, there is nothing left to agree."""

    _, game, challenge_id = await _a_complete_plan(
        client, session_factory, candidate_source, searcher
    )
    played = await client.post(
        f"/api/v1/games/{game['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(searcher["token"]),
    )
    assert played.status_code == 200, played.text

    refused = await _lock(client, challenge_id, searcher["token"])

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "plan_is_history"

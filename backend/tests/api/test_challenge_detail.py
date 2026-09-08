"""The challenge detail read, end to end over HTTP.

**The screen somebody answers on**, and the four things it promises that nothing
else in this suite covers:

**The pairing is recomputed for the reader.** The card block is assembled by the
matcher when the screen is opened, in the reader's own direction — so this file
wires the **real** port over the test's own index rather than a stub, and asserts
against a Fit that was genuinely computed.

**The card block is the arrangement's.** Two standings draw one and every other
draws none; one level down, a seat that has left draws none either, inside a
court that is still open.

**Answering is never gated on any of it.** A reader with no rating in the sport
gets the arrangement, a code saying whose gap the missing pairing is, and two
buttons that still work.

**One code for two refusals.** A challenge that is not yours and one that does
not exist answer alike, because separating them would answer *is this id real*
about a stranger's evening.
"""

from __future__ import annotations

import pytest

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import build_court_pairing_query_over
from app.modules.challenges.presentation.dependencies import (
    get_court_pairing_query,
)
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


def draw_real_cards(client, candidate_source, exposure_ledger):
    """Wire the **real** pairing query over the test's own index and ledger.

    The production declaration reaches for the process's candidate index and for
    the Redis pool, and neither exists under ``ASGITransport``. That default is
    the right one for this suite — it is what makes the *could not be read* case
    below the production path rather than a simulation — and the wrong one for
    every case about a card actually being drawn.

    What is wired instead is the **same assembly the route builds**, declared
    with its own dependencies so the session is still the request's, over the two
    seams ``app/bootstrap/challenge_demands.py`` names: the process's index and
    an exposure ledger that needs no server.
    """

    def _pairings(
        db: DbSession,
        clock: ClockDep,
        uow: UnitOfWorkDep,
        event_store: DomainEventStoreDep,
        events: EventPublisherDep,
        settings: SettingsDep,
    ):
        return build_court_pairing_query_over(
            session=db,
            clock=clock,
            unit_of_work=uow,
            event_store=event_store,
            events=events,
            settings=settings,
            exposure=exposure_ledger,
            candidates=candidate_source,
        )

    world.override(client, get_court_pairing_query, _pairings)


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    """Three other players, each of them a **whole** player.

    Built through the routes rather than appended straight to the log, which is
    the one thing this file needs that ``test_challenges.py`` does not: an
    invitee here is a *reader*, and ``searcher_facts`` reads a profile, a rating
    and a declaration live from the aggregates. A person folded into the index
    alone is somebody the index can describe and the pairing cannot be computed
    **for** — which is a real state, and it is the one the *nothing to compute*
    case below reaches deliberately rather than by accident.
    """

    people = {}
    for name in ("ana", "bo", "cy"):
        person = await world.a_searcher(client, name)
        people[name] = {"id": person["id"], "token": person["token"]}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _an_undeclared_city(
    client, session_factory, candidate_source, mu: float
) -> dict:
    """Three people the index can describe and who have declared no intent.

    A real state and not a fixture trick: a rating and a declaration are two
    separate acts, and somebody who was assessed and never said what kind of
    evening they want has exactly this shape. They are seatable — ⚡ reads the
    index — and a pairing cannot be computed **for** them.
    """

    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta, intent=None
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _a_court(client, searcher) -> tuple[str, list[dict]]:
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
    return body["search"]["search_id"], court


async def _send(client, token: str, search_id: str, court: list[dict]) -> str:
    response = await client.post(
        "/api/v1/challenges",
        json={"search_id": search_id, "court": court},
        headers=world.auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["challenge_id"]


async def _detail(client, token: str, challenge_id: str):
    return await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(token)
    )


async def _answer(client, token: str, challenge_id: str, how: str):
    response = await client.post(
        f"/api/v1/challenges/{challenge_id}/{how}", headers=world.auth(token)
    )
    assert response.status_code == 200, response.text
    return response.json()


def _seat_of(body: dict, player_id) -> dict:
    return next(
        seat for seat in body["seats"] if seat.get("player_id") == str(player_id)
    )


# ---------------------------------------------------------------------------
# The card, drawn
# ---------------------------------------------------------------------------


async def test_an_invitee_reads_who_is_asking_and_what_the_platform_makes_of_it(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**The whole point of the screen**, and every block on it.

    The person: a whole handle, an area, a Level, a band and a range. The
    pairing: a Fit computed in *this reader's* direction, the terms that made it,
    the basis it was renormalised over and a forecast. And no card on the
    reader's own seat, because a pairing with yourself is not a question.
    """

    draw_real_cards(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = await _send(client, searcher["token"], search_id, court)

    them = people["ana"]
    response = await _detail(client, them["token"], challenge_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert "pairing_absence" not in body
    organiser = _seat_of(body, searcher["id"])
    assert organiser["nickname"] == "searcher"
    card = organiser["card"]
    assert card["person"]["nickname"] == "searcher"
    assert card["person"]["range"]["low"] <= card["person"]["level"]
    assert card["pairing"]["terms"]
    assert 0 <= card["pairing"]["forecast"]["pct"] <= 100
    assert "card" not in _seat_of(body, them["id"])


async def test_the_answer_is_folded_against_one_instant_the_response_names(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """``read_at`` is on the detail as it is on the list, and it is its own.

    The detail is its own fold against its own instant, so the two reads carry
    two moments rather than sharing one — and every deadline on this response is
    rendered against the one beside it.
    """

    draw_real_cards(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = await _send(client, searcher["token"], search_id, court)

    body = (await _detail(client, people["ana"]["token"], challenge_id)).json()
    listed = await client.get(
        "/api/v1/challenges", headers=world.auth(people["ana"]["token"])
    )

    assert body["read_at"]
    assert listed.json()["read_at"]
    assert body["challenge_id"] == challenge_id


async def test_the_list_gains_a_handle_on_every_seat_and_nothing_else(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**The list stays cheap** (``docs/adr/0143`` §1).

    It gains an instant at the envelope and a handle on the seat, and it gains no
    card: a card is a profile read and an object-store signature per person, and
    the list is *every challenge you hold a seat in* with ended ones deliberately
    in it — the bound is somebody's whole history of being asked.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    await _send(client, searcher["token"], search_id, court)

    listed = await client.get(
        "/api/v1/challenges", headers=world.auth(people["ana"]["token"])
    )

    (one,) = listed.json()["challenges"]
    seats = one["seats"]
    assert {seat["nickname"] for seat in seats if seat["player_id"]} == {
        "searcher",
        "ana",
        "bo",
        "cy",
    }
    assert all("card" not in seat for seat in seats)


# ---------------------------------------------------------------------------
# The card's lifetime — ``docs/adr/0143`` §8
# ---------------------------------------------------------------------------


async def test_a_challenge_that_ended_draws_the_arrangement_and_the_handles_alone(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """The pair releases when a seat leaves, and a card is as-of-now.

    A live card of a stranger on a screen reopenable for ever is a directory with
    extra steps. **The handles stay**, because the standing's own sentence names
    them.
    """

    draw_real_cards(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = await _send(client, searcher["token"], search_id, court)
    for name in ("ana", "bo", "cy"):
        await _answer(client, people[name]["token"], challenge_id, "decline")

    body = (await _detail(client, people["ana"]["token"], challenge_id)).json()

    assert body["standing"] == "DECLINED"
    assert "pairing_absence" not in body
    assert all("card" not in seat for seat in body["seats"])
    assert _seat_of(body, searcher["id"])["nickname"] == "searcher"


async def test_a_seat_that_left_a_still_open_court_draws_no_card_and_the_others_do(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**One level down, the same rule** (``docs/adr/0143`` §8).

    Somebody who declined inside a court that is still being filled has left, and
    *that person is a stranger to you once more the moment they leave* — so their
    seat keeps its handle and loses its card, while everybody still in keeps
    both.
    """

    draw_real_cards(client, candidate_source, exposure_ledger)
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = await _send(client, searcher["token"], search_id, court)
    await _answer(client, people["ana"]["token"], challenge_id, "accept")
    await _answer(client, people["cy"]["token"], challenge_id, "accept")
    await _answer(client, people["bo"]["token"], challenge_id, "decline")

    body = (await _detail(client, people["ana"]["token"], challenge_id)).json()

    assert body["standing"] == "LINE_UP_INCOMPLETE"
    left = _seat_of(body, people["bo"]["id"])
    assert left["answer"] == "DECLINED"
    assert left["nickname"] == "bo"
    assert "card" not in left
    assert "card" in _seat_of(body, searcher["id"])
    assert "card" in _seat_of(body, people["cy"]["id"])


# ---------------------------------------------------------------------------
# The three absences, and the refusal — §2 and §6
# ---------------------------------------------------------------------------


async def test_a_reader_with_nothing_declared_still_answers_their_challenge(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """**Answering is never gated on the pairing.**

    Being asked to play a sport you have declared nothing for is how this feature
    works rather than a corner of it: the arrangement answers, the code says
    whose gap the missing pairing is — theirs, not an outage's — and the two
    buttons still work. A `503` here, or a screen that drew nothing, would turn
    *you have not finished setting up* into *you cannot answer your challenge*.
    """

    draw_real_cards(client, candidate_source, exposure_ledger)
    people = await _an_undeclared_city(
        client, session_factory, candidate_source, searcher["mu"]
    )
    search_id, court = await _a_court(client, searcher)
    challenge_id = await _send(client, searcher["token"], search_id, court)
    them = people["ana"]

    body = (await _detail(client, them["token"], challenge_id)).json()
    accepted = await _answer(client, them["token"], challenge_id, "accept")

    assert body["standing"] == "AWAITING_ANSWERS"
    assert body["pairing_absence"] == "NOTHING_TO_COMPUTE"
    assert all("card" not in seat for seat in body["seats"])
    assert _seat_of(body, searcher["id"])["nickname"] == "searcher"
    assert accepted["standing"] in {"AWAITING_ANSWERS", "LINE_UP_INCOMPLETE"}


async def test_a_matcher_this_process_cannot_reach_is_a_code_and_not_a_failure(
    client, session_factory, candidate_source, searcher
):
    """**The production wiring, exercised.** Nothing overrides the port here.

    Under ``ASGITransport`` there is no index on the application's state and no
    Redis pool, which is exactly the shape of an outage — and the promise is that
    it costs the pairing and never the screen. A ``503`` here would turn somebody
    else's outage into *you cannot answer your challenge*.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = await _send(client, searcher["token"], search_id, court)

    response = await _detail(client, people["ana"]["token"], challenge_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["pairing_absence"] == "COULD_NOT_BE_READ"
    assert all("card" not in seat for seat in body["seats"])
    assert _seat_of(body, searcher["id"])["nickname"] == "searcher"


async def test_a_stranger_is_told_the_challenge_does_not_exist(
    client, session_factory, candidate_source, searcher
):
    """**One code for two cases.** Separating them would answer *is this id real*
    about a stranger's evening, which is the refusal the answer routes already
    make and the reason this route could be keyed on a challenge id at all."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = await _send(client, searcher["token"], search_id, court)
    _, stranger = await world.register(client, "stranger")

    theirs = await _detail(client, stranger, challenge_id)
    nothing = await _detail(client, people["ana"]["token"], str(searcher["id"]))

    assert theirs.status_code == 404
    assert theirs.json()["code"] == "challenge_not_found"
    assert nothing.status_code == 404
    assert nothing.json()["code"] == "challenge_not_found"

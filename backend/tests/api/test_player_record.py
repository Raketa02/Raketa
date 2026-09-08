"""``GET /api/v1/players/{id}/record`` and ``/players/me/record``.

A player taps a face and is told who that person is. The rule the route runs on
(``docs/adr/0155``): **a record is read through a prior disclosure, never about a
person** — and the four fail-closed gates are re-evaluated live on every open,
so a disclosure entitles a reader to ask and never to be answered.

**The refusal is the thing most worth testing here**, and it is tested as a
*sameness* rather than as four statuses: never disclosed, blocked, held and no
such player produce the same bytes, because a response that named which would
deliver a block to the one person a block is meant to be invisible to.

Every assertion lands on HTTP, through the async client fixture: ASGI transport
over in-memory SQLite, **no MinIO, no Redis and no sidecar**.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.kernel import Sport, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.matchmaking.presentation.dependencies import get_candidate_source
from app.modules.player_profile.domain.availability import Window
from app.modules.rating.domain.events import RatingInitialised
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.candidate_index_fixtures import append
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def a_search_that_showed(client, session_factory, candidate_source, searcher):
    """One search of the reader's, and the one person it returned.

    The disclosure this route is built on, made the way the platform makes one:
    a real candidate in the index and a real search over it, so what entitles the
    read is a row the platform wrote rather than a fixture's say-so.
    """

    subject = await world.a_candidate(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)
    response = await world.search(client, searcher["token"])
    assert response.status_code == 200, response.text
    shown = [row["player_id"] for row in response.json()["candidates"]]
    assert shown == [str(subject)], shown
    return subject


async def record_of(client, token: str, player_id: UUID, *, sport: Sport | None = None):
    return await client.get(
        f"/api/v1/players/{player_id}/record",
        params={} if sport is None else {"sport": sport.value},
        headers=world.auth(token),
    )


async def own_record(client, token: str, *, sport: Sport | None = None):
    return await client.get(
        "/api/v1/players/me/record",
        params={} if sport is None else {"sport": sport.value},
        headers=world.auth(token),
    )


async def also_rated_in(session_factory, player_id: UUID, *, sport: Sport, mu: float):
    """One more Level for somebody already rated, filed where a rating lives.

    Through the log at the stream id the rating context derives, because that is
    the address the read port asks — a rating filed anywhere else is one the
    sheet can never find (``docs/adr/0105``).
    """

    at = datetime.now(timezone.utc) - timedelta(days=3)
    await append(
        session_factory,
        RatingInitialised(
            rating_id=skill_rating_id(player_id, sport),
            player_id=player_id,
            sport=sport.value,
            mu=mu,
            sigma=0.20,
            confidence=83,
            range_low=mu - 0.2,
            range_high=mu + 0.2,
            band_name="Established",
            band_lower=2.7,
            band_upper=3.8,
            status="INITIAL_ESTIMATE",
            engine_version="v3",
            source_assessment_id=new_uuid(),
            occurred_at=at,
        ),
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(player_id, sport),
    )


async def a_confirmed_game(
    session_factory, a: UUID, b: UUID, *, sport: Sport, a_won: bool
):
    """One counted singles game between them, played and confirmed by silence.

    Written through the aggregate rather than as rows, which is the rule every
    suite in this repository takes about somebody else's context: what the record
    reads is a fold, and the only honest way to exercise one is to make the
    history it folds.

    **Dated a month back on purpose.** A confirmation is a clock passing rather
    than an act (``docs/adr/0137``), so a game is made in the past instead of
    anything being told it is over.
    """

    played = instant(datetime.now(timezone.utc) - timedelta(days=30))
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=sport,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=a),
                Seating(side=GameSide.B, player_id=b),
            )
        ),
        occurred_at=instant(played - timedelta(hours=1)),
    )
    game.state_result(
        by=a,
        score=Score.of(
            [SetScore(a=6, b=4), SetScore(a=6, b=3)]
            if a_won
            else [SetScore(a=4, b=6), SetScore(a=3, b=6)]
        ),
        occurred_at=played,
    )
    async with session_factory() as session:
        await build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(game)
        await session.commit()


def without_the_trace(response) -> str:
    """One refusal's body, minus the one field that is per-request.

    ``trace_id`` ties a client failure to a server log and is different on every
    response by design. Everything else has to be identical, and comparing the
    **text** rather than a parsed dictionary is deliberate: key order and
    spelling are part of what a client sees.
    """

    body = json.loads(response.text)
    assert body.pop("trace_id"), "a refusal with no trace is a refusal nobody can chase"
    return json.dumps(body, sort_keys=False)


# ---------------------------------------------------------------------------
# What opens
# ---------------------------------------------------------------------------


async def test_a_search_that_showed_them_opens_their_record(
    client, session_factory, candidate_source, searcher
):
    """The ordinary case, and the whole identity zone with it."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )

    response = await record_of(client, searcher["token"], subject)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "is_self": False,
        "nickname": "subject",
        "area_code": "A+05151-000013",
        "social_tags": list(world.COMPETITIVE_TAGS),
        "sports": [
            {
                "sport": "PADEL",
                "level": pytest.approx(searcher["mu"]),
                "band": "Improver",
            }
        ],
        "skill": {
            "sport": "PADEL",
            "level": pytest.approx(searcher["mu"]),
            "band": "Improver",
            "confidence": 62,
            # A Level out of the questionnaire that no game has tested yet. **A
            # measured nought and not an absence** — the confidence beside it is
            # what makes that readable.
            "counted_games": 0,
            "likely_range": {
                "low": pytest.approx(searcher["mu"] - 0.3),
                "high": pytest.approx(searcher["mu"] + 0.3),
            },
            "last_five": [],
        },
    }
    # The photograph's three fields are **omitted together** for a player with
    # none, and never sent as nulls: the client draws the generated poster.
    assert "photo_id" not in body and "photo_url" not in body
    assert "review" not in body


async def test_your_own_record_opens_with_nothing_behind_it(client, searcher):
    """*How others see you* — the one record needing no prior disclosure, and the
    one the client must not have to compare identifiers to recognise."""

    response = await own_record(client, searcher["token"])

    assert response.status_code == 200, response.text
    assert response.json()["is_self"] is True
    assert response.json()["nickname"] == "searcher"


async def test_asking_about_yourself_by_id_is_still_your_own_record(
    client, searcher
):
    response = await record_of(client, searcher["token"], searcher["id"])

    assert response.status_code == 200, response.text
    assert response.json()["is_self"] is True


async def test_the_person_who_was_invited_can_open_the_organiser_s_record(
    client, session_factory, candidate_source, searcher
):
    """**The strand a search cannot supply.** A court is sent off the organiser's
    search, so the organiser has been shown the invitee and the invitee has been
    shown nothing — and they are the person who most obviously needs to know who
    they have just been asked to give up an evening to."""

    people = {}
    for name, latitude in (("ana", 51.52), ("bea", 51.53), ("caro", 51.54)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=searcher["mu"], latitude=latitude
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    built = await world.lineup(client, searcher["token"])
    assert built.status_code == 200, built.text
    body = built.json()
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
    invitee = next(
        person
        for person in people.values()
        if str(person["id"]) in {seat["player_id"] for seat in court}
    )

    response = await record_of(client, invitee["token"], searcher["id"])

    assert response.status_code == 200, response.text
    assert response.json()["nickname"] == "searcher"


# ---------------------------------------------------------------------------
# The one refusal
# ---------------------------------------------------------------------------


async def test_a_person_you_have_never_been_shown_is_refused(
    client, session_factory, candidate_source, searcher
):
    """Without this the route is a player-enumeration endpoint, and a UUID being
    hard to guess is not an authorization model."""

    stranger, _ = await world.a_signed_in_candidate(
        client, session_factory, "stranger", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)

    response = await record_of(client, searcher["token"], stranger)

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "record_unavailable"


async def test_a_block_in_either_direction_closes_a_record_a_search_opened(
    client, session_factory, candidate_source, searcher
):
    """The disclosure stands for ever and the gates are live, which is the whole
    reason they are re-run rather than recorded."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    assert (await record_of(client, searcher["token"], subject)).status_code == 200

    blocked = await world.block_between(client, searcher["token"], subject)

    assert blocked.status_code == 204, blocked.text
    assert (await record_of(client, searcher["token"], subject)).status_code == 404


async def test_a_gate_that_cannot_be_evaluated_excludes(
    client, session_factory, candidate_source, searcher
):
    """A subject with no row in the partition the disclosure happened in has no
    preference to read, so the mutual gender gate cannot be evaluated — and *a
    gate that cannot be evaluated excludes*. This is the half of the partition
    rule HTTP can see; which partition is chosen is pinned in
    ``tests/unit/test_record_admission.py``."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    world.override(
        client, get_candidate_source, lambda: world.an_empty_index(candidate_source)
    )

    response = await record_of(client, searcher["token"], subject)

    assert response.status_code == 404, response.text


async def test_the_four_refusals_are_byte_identical(
    client, session_factory, candidate_source, searcher
):
    """**Asserted as a sameness, not as four statuses.**

    Never disclosed, blocked, held and no such player. A payload naming which
    would deliver a block to the one person the block was meant to be invisible
    to; a payload separating *never disclosed* from *no such player* would answer
    *is this id real* about a stranger.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    stranger, _ = await world.a_signed_in_candidate(
        client, session_factory, "stranger", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)

    never_disclosed = await record_of(client, searcher["token"], stranger)
    no_such_player = await record_of(client, searcher["token"], uuid4())
    # **The last two are refused about somebody the reader *was* shown**, so they
    # come from the live gate rather than from the disclosure. Run against a
    # stranger they would take the same path `never_disclosed` just took, and the
    # sameness below would be a claim about three causes wearing four names.
    world.hold_only(client, subject)
    held = await record_of(client, searcher["token"], subject)
    world.hold_only(client)
    assert (
        await record_of(client, searcher["token"], subject)
    ).status_code == 200, "the hold, not the fixture, is what refused"
    blocked_by = await world.block_between(client, searcher["token"], subject)
    assert blocked_by.status_code == 204, blocked_by.text
    blocked = await record_of(client, searcher["token"], subject)

    refusals = (never_disclosed, no_such_player, blocked, held)
    assert {one.status_code for one in refusals} == {404}
    assert len({without_the_trace(one) for one in refusals}) == 1


async def test_the_held_reader_is_refused_by_the_same_line(
    client, session_factory, candidate_source, searcher
):
    """A hold points **both ways** (``docs/adr/0095``), so it reaches the route
    that remembers what a search already showed — and it reaches it as this
    route's one refusal rather than as a second thing to draw."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    world.hold_only(client, searcher["id"])

    response = await record_of(client, searcher["token"], subject)

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "record_unavailable"


async def test_a_held_player_can_still_read_their_own_record(client, searcher):
    """The one screen that tells somebody how they appear is the one a penalty
    must not close: *a penalty nobody can look up is a penalty nobody can fix.*"""

    world.hold_only(client, searcher["id"])

    response = await own_record(client, searcher["token"])

    assert response.status_code == 200, response.text


async def test_an_account_that_may_not_be_shown_is_refused(
    client, session_factory, candidate_source, searcher
):
    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    world.may_not_show(client, subject)

    response = await record_of(client, searcher["token"], subject)

    assert response.status_code == 404, response.text


async def test_a_record_needs_a_signed_in_reader(client, searcher):
    assert (
        await client.get(f"/api/v1/players/{searcher['id']}/record")
    ).status_code == 401
    assert (await client.get("/api/v1/players/me/record")).status_code == 401


async def test_me_is_never_parsed_as_a_player_id(client, searcher):
    """The route ordering, asserted rather than assumed: a parameterised segment
    declared ahead of the literal one would answer the refusal to everybody
    asking for their own record, and nothing else would look wrong."""

    response = await own_record(client, searcher["token"])

    assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Which sport the sheet is about
# ---------------------------------------------------------------------------


async def test_the_sport_asked_for_is_the_one_the_skill_card_draws(
    client, session_factory, candidate_source, searcher
):
    """The overwhelming case, and the pills beside it name every sport they hold
    **in the registry's own order** rather than the order the ratings arrived."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await also_rated_in(session_factory, subject, sport=Sport.SQUASH, mu=4.10)

    asked = await record_of(client, searcher["token"], subject, sport=Sport.SQUASH)
    body = asked.json()

    assert [one["sport"] for one in body["sports"]] == ["PADEL", "SQUASH"]
    assert body["skill"]["sport"] == "SQUASH"
    assert body["skill"]["level"] == pytest.approx(4.10)
    assert body["skill"]["band"] == "Established"
    assert body["skill"]["confidence"] == 83


async def test_a_sport_they_do_not_play_falls_back_and_never_refuses(
    client, session_factory, candidate_source, searcher
):
    """**The parameter chooses what is drawn and never whether it is.** Admission
    ran in the partition of the search that showed them, which is a fact the
    platform holds — so naming a sport nobody was ever shown in changes the
    header and nothing else."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )

    response = await record_of(client, searcher["token"], subject, sport=Sport.TENNIS)

    assert response.status_code == 200, response.text
    assert response.json()["skill"]["sport"] == "PADEL"


async def test_asking_for_no_sport_falls_back_the_same_way(
    client, session_factory, candidate_source, searcher
):
    """A record opened from a surface with no sport behind it — a chat, a games
    list — takes the same fallback rather than a third rule."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["skill"]["sport"] == "PADEL"


async def test_your_own_record_takes_the_sport_too(client, session_factory, searcher):
    """The same resolution on the one sheet nothing gates."""

    await also_rated_in(session_factory, searcher["id"], sport=Sport.SQUASH, mu=2.40)

    body = (await own_record(client, searcher["token"], sport=Sport.SQUASH)).json()

    assert body["is_self"] is True
    assert body["skill"]["sport"] == "SQUASH"
    assert [one["sport"] for one in body["sports"]] == ["PADEL", "SQUASH"]


# ---------------------------------------------------------------------------
# The run of five
# ---------------------------------------------------------------------------


async def test_the_run_of_five_is_the_resolved_sports_and_nobody_elses(
    client, session_factory, candidate_source, searcher
):
    """**The defect this ticket fixes, over the wire.** A run built across every
    sport and drawn beneath a single sport's Level was squash results under a
    padel number.

    The subject has one padel result and two squash ones; the padel sheet draws
    the padel one alone.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await also_rated_in(session_factory, subject, sport=Sport.SQUASH, mu=4.10)
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.SQUASH, a_won=False
    )
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.SQUASH, a_won=True
    )

    padel = (
        await record_of(client, searcher["token"], subject, sport=Sport.PADEL)
    ).json()
    squash = (
        await record_of(client, searcher["token"], subject, sport=Sport.SQUASH)
    ).json()

    assert padel["skill"]["last_five"] == ["WIN"]
    assert sorted(squash["skill"]["last_five"]) == ["LOSS", "WIN"]
    # And the count the certainty rests on is **not** the run's length: a Level
    # moves when the rating context walks a result forward, and nothing here has.
    assert padel["skill"]["counted_games"] == 0


async def test_a_run_shorter_than_five_is_never_padded(
    client, session_factory, candidate_source, searcher
):
    """One result means one, and the client draws the gap rather than filling
    it. An empty list is what somebody with none gets."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=False
    )

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["skill"]["last_five"] == ["LOSS"]

"""``GET /api/v1/players/{id}/record`` and ``/players/me/record``.

A player taps a face and is told who that person is. The rule the route runs on
(``docs/adr/0159``): **a record is read through a prior disclosure, never about a
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
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_sportsmanship_ledger,
)
from app.engines.matchfit.core import ReliabilityStrand, SearchMode
from app.kernel import Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.player_score.domain.strands import (
    PUBLISHED_WEIGHTS,
    out_of_a_hundred,
)
from app.modules.matchmaking.presentation.dependencies import get_candidate_source
from app.modules.player_profile.domain.weekly_hours import Window
from app.modules.rating.domain.events import RatingInitialised
from app.modules.sportsmanship.domain.card import (
    SettledCourt,
    SportsmanshipCard,
    StarsGiven,
)
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.candidate_index_fixtures import append
from tests.api import matchmaking_world as world
from tests.api.test_groups import a_club, a_group
from tests.api.test_groups import join as join_group


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


async def a_ghosted_plan(session_factory, a: UUID, b: UUID, *, sport: Sport):
    """A plan nobody ever claimed, old enough that its entry window has shut.

    The miss half of *shows up*, and it is charged to **everybody who was on that
    court**: a dissolved arrangement is a fact about the court and there is
    nobody in it to blame. The age is read off ``games``' own two windows rather
    than typed, so a change to either moves this with it.
    """

    # A day past the far edge of both windows, so the plan's entry window has
    # certainly shut. Read off ``games``' own two constants rather than typed, so
    # a change to either moves this with it.
    made = instant(
        datetime.now(timezone.utc) - PLAN_HORIZON - ENTRY_GRACE - timedelta(days=1)
    )
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
        occurred_at=made,
    )
    async with session_factory() as session:
        await build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(game)
        await session.commit()


async def a_kept_booked_game(session_factory, player: UUID):
    """A padel game the player stayed in until its hour — the good half of
    *keeps plans* (#544). Booked five days before its hour, four days ago,
    through the aggregate."""

    starts = instant(datetime.now(timezone.utc) - timedelta(days=4))
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=starts,
        share_grosze=30_00,
        first_side=(player, new_uuid()),
        second_side=(new_uuid(), new_uuid()),
        cut_off=instant(starts - timedelta(hours=24)),
        game_id=new_uuid(),
        at=instant(starts - timedelta(days=5)),
    )
    async with session_factory() as session:
        await build_booking_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(booking)
        await session.commit()


def every_key(payload) -> list[str]:
    """Every property name anywhere in a response, however deeply nested.

    Keys rather than the raw text, deliberately: a tag id or a handle that
    happened to contain the word would make a text search fail for a reason that
    has nothing to do with the rule being kept.
    """

    if isinstance(payload, dict):
        return [
            name
            for key, value in payload.items()
            for name in (key, *every_key(value))
        ]
    if isinstance(payload, list):
        return [name for one in payload for name in every_key(one)]
    return []


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
        # The one read about another player that carries both halves of the
        # naming (``docs/adr/0171`` §4): two people may share a name, and the
        # record is where a friend tells them apart.
        "name": "subject",
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
    # And nobody has watched them play, so there is no habit to describe: the
    # row is **absent** rather than drawn at nought over nought.
    assert "variety" not in body


async def test_a_record_quotes_the_line_they_wrote_and_omits_it_otherwise(
    client, session_factory, candidate_source, searcher
):
    """**The record sheet draws the intro under the name** (``docs/adr/0170``
    §4), verbatim and off the profile — and a player who skipped has no key at
    all, never an empty string."""

    karol = await world.a_candidate(
        client,
        session_factory,
        "karol",
        mu=searcher["mu"],
        intro="Moved from Wrocław in May. Needs opponents.",
    )
    ola = await world.a_candidate(client, session_factory, "ola", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    shown = await world.search(client, searcher["token"])
    assert {row["player_id"] for row in shown.json()["candidates"]} == {
        str(karol),
        str(ola),
    }

    wrote = await record_of(client, searcher["token"], karol)
    skipped = await record_of(client, searcher["token"], ola)

    assert wrote.status_code == 200, wrote.text
    assert wrote.json()["intro"] == "Moved from Wrocław in May. Needs opponents."
    assert skipped.status_code == 200, skipped.text
    assert "intro" not in skipped.json()


async def test_your_own_record_opens_with_nothing_behind_it(client, searcher):
    """*How others see you* — the one record needing no prior disclosure, and the
    one the client must not have to compare identifiers to recognise."""

    response = await own_record(client, searcher["token"])

    assert response.status_code == 200, response.text
    assert response.json()["is_self"] is True
    assert response.json()["name"] == "searcher"
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
    assert response.json()["name"] == "searcher"
    assert response.json()["nickname"] == "searcher"


async def two_strangers_in_one_group(
    client, session_factory, candidate_source, searcher
) -> tuple[dict, dict, dict]:
    """The searcher and a candidate nobody has shown them, both in the searcher's
    *Anyone* group — the pair a group's Members lists to each other (#514)."""

    subject_id, subject_token = await world.a_signed_in_candidate(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)
    owner = {"id": searcher["id"], "headers": world.auth(searcher["token"])}
    member = {"id": subject_id, "headers": world.auth(subject_token)}
    group = await a_group(client, owner, await a_club(client))
    joined = await join_group(client, member, group)
    assert joined.status_code == 200, joined.text
    return group, {**owner, "token": searcher["token"]}, {
        **member,
        "token": subject_token,
    }


async def test_a_group_you_are_both_in_opens_the_record_both_ways(
    client, session_factory, candidate_source, searcher
):
    """**The strand Members promises** (#529): *Press and hold anyone for the
    full record* is read by a member who never searched, about people no search
    of theirs returned — the group is what introduced them."""

    subject_id, subject_token = await world.a_signed_in_candidate(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)
    assert (await record_of(client, searcher["token"], subject_id)).status_code == 404

    owner = {"id": searcher["id"], "headers": world.auth(searcher["token"])}
    group = await a_group(client, owner, await a_club(client))
    joined = await join_group(
        client, {"id": subject_id, "headers": world.auth(subject_token)}, group
    )
    assert joined.status_code == 200, joined.text

    theirs = await record_of(client, searcher["token"], subject_id)
    mine = await record_of(client, subject_token, searcher["id"])

    assert theirs.status_code == 200, theirs.text
    assert theirs.json()["name"] == "subject"
    assert mine.status_code == 200, mine.text
    assert mine.json()["name"] == "searcher"


async def test_leaving_the_group_closes_the_record_it_opened(
    client, session_factory, candidate_source, searcher
):
    """**Membership as it stands, not as it was** — Members lists who is in the
    group now, so the strand is the group now: unlike a game, a group left is no
    longer one the pair are in."""

    group, owner, member = await two_strangers_in_one_group(
        client, session_factory, candidate_source, searcher
    )
    assert (await record_of(client, owner["token"], member["id"])).status_code == 200

    left = await client.delete(
        f"/api/v1/groups/{group['id']}/membership", headers=member["headers"]
    )

    assert left.status_code == 204, left.text
    assert (await record_of(client, owner["token"], member["id"])).status_code == 404
    assert (await record_of(client, member["token"], owner["id"])).status_code == 404


async def test_a_block_between_two_members_closes_the_record_the_group_opened(
    client, session_factory, candidate_source, searcher
):
    """The gates stay live whatever the strand: Members leaves a blocked pair out
    of each other's list, and the record refuses them either way round."""

    _, owner, member = await two_strangers_in_one_group(
        client, session_factory, candidate_source, searcher
    )

    blocked = await world.block_between(client, member["token"], owner["id"])

    assert blocked.status_code == 204, blocked.text
    assert (await record_of(client, owner["token"], member["id"])).status_code == 404
    assert (await record_of(client, member["token"], owner["id"])).status_code == 404


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


# ---------------------------------------------------------------------------
# Opponent variety
# ---------------------------------------------------------------------------


async def test_the_record_says_how_widely_they_spread_their_games(
    client, session_factory, candidate_source, searcher
):
    """**A pair and never a share**, over the **whole** record.

    Three counted games against two people: two different faces, three evenings.
    The percentage is the client's division, because *two of three* and *twenty
    of thirty* are the same share and different claims — the same argument the
    rows above it print their raw fractions for.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    somebody_else = uuid4()
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=False
    )
    await a_confirmed_game(
        session_factory, subject, somebody_else, sport=Sport.TENNIS, a_won=True
    )

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["variety"] == {"distinct_opponents": 2, "times_on_court": 3}


async def test_variety_counts_every_sport_and_the_sport_asked_for_moves_it_not(
    client, session_factory, candidate_source, searcher
):
    """**It is about no sport at all**, unlike the run of five above it.

    The same sheet asked for padel and for squash draws the same variety and two
    different runs of form: one is a habit and the other is this sport's record.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await also_rated_in(session_factory, subject, sport=Sport.SQUASH, mu=4.10)
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await a_confirmed_game(
        session_factory, subject, uuid4(), sport=Sport.SQUASH, a_won=True
    )

    padel = (
        await record_of(client, searcher["token"], subject, sport=Sport.PADEL)
    ).json()
    squash = (
        await record_of(client, searcher["token"], subject, sport=Sport.SQUASH)
    ).json()

    assert padel["variety"] == {"distinct_opponents": 2, "times_on_court": 2}
    assert squash["variety"] == padel["variety"]
    assert padel["skill"]["last_five"] == ["WIN"]
    assert squash["skill"]["last_five"] == ["WIN"]


async def test_your_own_record_carries_the_same_pair(
    client, session_factory, searcher
):
    """*How others see you* draws the number everybody else is shown, which is
    the whole reason the screen exists."""

    await a_confirmed_game(
        session_factory, searcher["id"], uuid4(), sport=Sport.PADEL, a_won=True
    )

    body = (await own_record(client, searcher["token"])).json()

    assert body["is_self"] is True
    assert body["variety"] == {"distinct_opponents": 1, "times_on_court": 1}


# ---------------------------------------------------------------------------
# What the platform watched — the pill and the metered rows
# ---------------------------------------------------------------------------


async def test_each_strand_crosses_as_its_raw_pair_and_its_own_figure(
    client, session_factory, candidate_source, searcher
):
    """**A perfect record over nine and one over forty are different claims**,
    and a bar alone hides which — so the two counts cross beside the figure.

    One plan that produced a game and one nobody ever claimed: an opportunity
    each, one of them good.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await a_ghosted_plan(session_factory, subject, searcher["id"], sport=Sport.PADEL)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["reliability"]["strands"] == [
        {"strand": "SHOWS_UP", "good": 1, "opportunities": 2, "pct": 50}
    ]
    assert body["reliability"]["player_score"] == 50


async def test_the_pill_is_the_blend_a_reader_can_take_from_the_rows(
    client, session_factory, candidate_source, searcher
):
    """**The published figure is the weighted mean of the figures beneath it**,
    recomputed here through the published weights from the rows that actually
    crossed.

    The two strands are deliberately unequal, so a pill blended without the
    weights — or one taken over the unrounded ratios — would land somewhere else.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await a_ghosted_plan(session_factory, subject, searcher["id"], sport=Sport.PADEL)
    await a_kept_booked_game(session_factory, subject)

    reliability = (await record_of(client, searcher["token"], subject)).json()[
        "reliability"
    ]

    assert [row["strand"] for row in reliability["strands"]] == [
        "SHOWS_UP",
        "KEEPS_PLANS",
    ]
    weighted = sum(
        PUBLISHED_WEIGHTS[ReliabilityStrand(row["strand"])] * row["pct"]
        for row in reliability["strands"]
    )
    basis = sum(
        PUBLISHED_WEIGHTS[ReliabilityStrand(row["strand"])]
        for row in reliability["strands"]
    )
    assert reliability["player_score"] == out_of_a_hundred(weighted, 100 * basis)


async def test_no_weight_crosses_on_this_response_in_any_shape(
    client, session_factory, candidate_source, searcher
):
    """**The weights are a fact about how the number is made, not about the
    person.** A client holding them could draw one strand as worth more than
    another, which no screen here claims — and could re-derive the pill, which is
    a second rounding of a figure the matcher acts on."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await a_kept_booked_game(session_factory, subject)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["reliability"]["strands"]
    assert [name for name in every_key(body) if "weight" in name.lower()] == []


async def test_a_player_nothing_has_fallen_due_for_has_no_section_at_all(
    client, session_factory, candidate_source, searcher
):
    """**Omitted whole, and never a section of noughts.** Nobody has failed to
    turn up who was never due to, and a zero here is how *no record* becomes *a
    bad record* on the one screen nobody can appeal.

    **No field of it is nulled or emptied either** — there is no `reliability`
    key at all, so there is no `player_score: 0` to draw a red pill from and no
    empty `strands` to draw a heading over.

    This subject has a Level, which is the other half of the claim: the sheet
    draws what exists, and a newcomer reads as a newcomer rather than as a
    failure.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )

    body = (await record_of(client, searcher["token"], subject)).json()

    assert "reliability" not in body
    assert body["skill"] is not None


async def test_your_own_record_carries_the_number_that_decides_your_exposure(
    client, session_factory, searcher
):
    """*How others see you* draws the pill the matcher acts on — which is the
    whole argument for the screen: a penalty nobody can look up is a penalty
    nobody can fix, and a player working their record back up must be able to
    watch it lift."""

    await a_ghosted_plan(session_factory, searcher["id"], uuid4(), sport=Sport.PADEL)

    body = (await own_record(client, searcher["token"])).json()

    assert body["is_self"] is True
    assert body["reliability"] == {
        "player_score": 0,
        "strands": [
            {"strand": "SHOWS_UP", "good": 0, "opportunities": 1, "pct": 0}
        ],
    }
    # **And the two absences are different questions**, which this arrangement
    # is the proof of: a plan that dissolved is an opportunity and is not a game
    # anybody played, so there are rows here and no variety at all. `0` is a
    # measured figure on a row that exists; an omitted zone is not a nought.
    assert "variety" not in body


# ---------------------------------------------------------------------------
# What other players said
# ---------------------------------------------------------------------------


async def stars_for(session_factory, subject: UUID, *stars: int) -> None:
    """One card per rater, each giving this person that many stars.

    Written through ``sportsmanship``'s own aggregate rather than an ``INSERT``
    (``docs/adr/0029``), because the collapse *only a rater's most recent stars
    count* lives in that store's key — a row inserted beside the card would be
    this suite arranging away the very thing it wants to read.
    """

    async with session_factory() as session:
        ledger = build_sportsmanship_ledger(session)
        for given in stars:
            at = instant(datetime.now(timezone.utc) - timedelta(days=1))
            await ledger.record(
                SportsmanshipCard.answered(
                    court=SettledCourt(
                        game_id=new_uuid(),
                        rater_id=new_uuid(),
                        others=(subject,),
                        played_at=at,
                    ),
                    given=[StarsGiven(subject_id=subject, stars=given)],
                    at=at,
                )
            )
        await session.commit()


async def test_a_reader_is_told_the_figure_and_how_many_people_it_rests_on(
    client, session_factory, candidate_source, searcher
):
    """**Its own zone, and both numbers in it.** The card above promises
    *counted by the system, not written by people*; this is the one thing on the
    sheet people typed, so it crosses under its own name and never among the
    metered rows."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await stars_for(session_factory, subject, 5, 4, 5)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["sportsmanship"] == {"average": 4.7, "raters": 3}


async def test_it_publishes_from_a_single_rating_with_the_count_beside_it(
    client, session_factory, candidate_source, searcher
):
    """**No minimum**, because the count does a minimum's work honestly: over one
    player the field visibly reads as one person's opinion, which is the same
    discipline the metered rows take by printing their raw pairs."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await stars_for(session_factory, subject, 3)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["sportsmanship"] == {"average": 3.0, "raters": 1}


async def test_a_person_nobody_has_rated_has_the_zone_absent_entirely(
    client, session_factory, candidate_source, searcher
):
    """A **fourth absence**, and a fourth question: rating is a favour, ignoring
    a card costs nothing and nothing records the omission — so this is never a
    nought and never an empty object."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )

    body = (await record_of(client, searcher["token"], subject)).json()

    assert "sportsmanship" not in body


async def test_nothing_is_trimmed_at_either_end_of_the_window(
    client, session_factory, candidate_source, searcher
):
    """**No outlier trimming of any kind**, because trimming is the platform
    deciding which raters were wrong — a larger claim than publishing the number,
    and one with no appeal route behind it either."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await stars_for(session_factory, subject, 1, 5, 5)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["sportsmanship"] == {"average": 3.7, "raters": 3}


async def test_your_own_record_carries_the_figure_and_the_count(
    client, session_factory, searcher
):
    """**The subject reads what a reader reads** (``docs/adr/0179`` §5).

    The sheet titled *How others see you* draws *Sportsmanship, by players ·
    4,7 / 5 · 3 players* — the published average over the fifty most recent
    raters and how many different people it rests on — exactly as it is drawn
    for anybody else. The subtraction ``docs/adr/0158`` §6 named is real and is
    accepted by name; the band that used to stand in for the figure is gone
    from the shape, asserted as an absence of the whole field.
    """

    await stars_for(session_factory, searcher["id"], 5, 4, 5)

    body = (await own_record(client, searcher["token"])).json()

    assert body["is_self"] is True
    assert body["sportsmanship"] == {"average": 4.7, "raters": 3}
    assert "sportsmanship_band" not in body


async def test_the_subject_and_a_reader_are_served_one_figure(
    client, session_factory, candidate_source, searcher
):
    """**One record, one resolution, whoever is reading.** The figure on your
    own sheet is byte-for-byte the figure a stranger a search showed you to is
    served about you — no coarsening, no withheld count, no second fold."""

    subject, token = await world.a_signed_in_candidate(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)
    shown = (await world.search(client, searcher["token"])).json()["candidates"]
    assert [row["player_id"] for row in shown] == [str(subject)]
    await stars_for(session_factory, subject, 5, 3, 4, 4)

    as_a_reader = (await record_of(client, searcher["token"], subject)).json()
    as_the_subject = (await own_record(client, token)).json()

    assert as_a_reader["is_self"] is False
    assert as_the_subject["is_self"] is True
    assert as_a_reader["sportsmanship"] == {"average": 4.0, "raters": 4}
    assert as_the_subject["sportsmanship"] == as_a_reader["sportsmanship"]


async def test_asking_about_yourself_by_id_is_answered_with_the_figure_too(
    client, session_factory, searcher
):
    """The parameterised route reaches the same sheet: ``is_self`` retitles it
    and moves nothing else, whichever route was called."""

    await stars_for(session_factory, searcher["id"], 1, 2)

    body = (await record_of(client, searcher["token"], searcher["id"])).json()

    assert body["is_self"] is True
    assert body["sportsmanship"] == {"average": 1.5, "raters": 2}


async def test_a_subject_nobody_has_rated_has_the_zone_absent_on_their_own_record(
    client, searcher
):
    """The same absence a stranger's sheet spells, so a newcomer's own record
    draws neither an empty zone nor a nought."""

    body = (await own_record(client, searcher["token"])).json()

    assert "sportsmanship" not in body


async def test_the_sport_asked_for_does_not_move_what_players_said(
    client, session_factory, candidate_source, searcher
):
    """It is about **no sport**, like the metered rows and the variety beside it:
    how somebody is to play with is not a padel fact, and `?sport=` says what the
    sheet is about rather than which record is folded."""

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await stars_for(session_factory, subject, 4, 4)

    padel = (
        await record_of(client, searcher["token"], subject, sport=Sport.PADEL)
    ).json()
    tennis = (
        await record_of(client, searcher["token"], subject, sport=Sport.TENNIS)
    ).json()

    assert (
        padel["sportsmanship"]
        == tennis["sportsmanship"]
        == {
            "average": 4.0,
            "raters": 2,
        }
    )


async def test_stars_move_no_part_of_the_reliability_pill(
    client, session_factory, candidate_source, searcher
):
    """**The figure does not enter the pill, and the matcher reads it nowhere.**

    A star average is not a ratio out of a hundred, so it cannot be a term in a
    weighted mean over ratios — but that is an argument, and this is the check.
    The record is read twice over the same watched history, once before anybody
    has an opinion and once after three people have given the lowest stars there
    are, and the whole block is identical: no extra row, no moved figure, no
    moved pill.

    It matters because the pill is exactly what the platform acts on
    (``docs/adr/0158``): the moment an opinion the matcher ignores got into the
    number a player can see, the number they can see would stop being the number
    that demotes them, and the penalty would become the unexplainable kind the
    reliability floor's own rule forbids. The `.importlinter` contract beside
    this refuses the matcher the import; this refuses the arithmetic.
    """

    subject = await a_search_that_showed(
        client, session_factory, candidate_source, searcher
    )
    await a_ghosted_plan(session_factory, subject, searcher["id"], sport=Sport.PADEL)
    await a_kept_booked_game(session_factory, subject)

    before = (await record_of(client, searcher["token"], subject)).json()["reliability"]

    await stars_for(session_factory, subject, 1, 1, 1)

    after = (await record_of(client, searcher["token"], subject)).json()
    assert after["sportsmanship"] == {"average": 1.0, "raters": 3}
    assert after["reliability"] == before
    assert "SPORTSMANSHIP" not in [
        row["strand"] for row in after["reliability"]["strands"]
    ]

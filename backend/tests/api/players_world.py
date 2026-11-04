"""Players, made the way the platform makes one — for every test of the games
the product makes (#573).

**Every player goes through the real routes**: signed up, signed in and named;
a profile committed; rated through an assessment, or — where a test needs a
chosen Level, which the questionnaire does not take dictation for — a rating
filed on the log exactly where the rating context files one; a Play intent
declared. Nothing here searches, deals a deck or sends a challenge, so a test
built on it stands without the old matchmaking world.

Beside the players, the few moves those tests share: blocking somebody,
replacing one dependency for one test, and delivering the outbox the way the
worker does.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.bootstrap.composition import (
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_nudge_publisher,
)
from app.bootstrap.events import build_event_runtime
from app.kernel import Sport, instant
from app.modules.conversations.infrastructure.absent_providers import (
    NobodyIsFollowing,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.notifications.infrastructure.push import RecordingPush
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.modules.player_profile.domain.events import (
    IntroWritten,
    PlayerProfileCreated,
    PlayIntentDeclared,
)
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    PLAYER_PROFILE_AGGREGATE,
)
from app.modules.rating.domain.events import RatingInitialised
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.event_log import append

#: Where a profile is committed unless a test says otherwise, at the platform's
#: own coarse precision.
CENTRE = (51.51, -0.13)

#: A rating filed on the log is filed this long ago, clear of every window a
#: test runs its clock through.
LONG_AGO = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)

SPORT = Sport.PADEL

#: Two tags the platform actually serves, so a profile commits with a style.
COMPETITIVE_TAGS = ("PLAYS_TO_WIN", "HERE_TO_IMPROVE")

#: The week a player filed on the log keeps unless a test says otherwise: two
#: hours that overlap ``commit_profile``'s own.
SHARED_SLOTS = ("2:19", "6:10")


async def register(
    client, name: str, *, domain: str = "example.com"
) -> tuple[UUID, str]:
    """Sign one player up, in, and name them. Returns their id and a bearer token.

    The naming is the player's own act after sign-up (``docs/adr/0199`` §3); the
    one word is the address's local part and the nickname alike, so an
    assertion reading a seat's ``nickname`` finds what the test registered.
    ``domain`` is where they
    are addressed — ``raketa.example``, the seed system's reserved TLD, makes an
    account the games test console may act as (``docs/adr/0194`` §2).
    """

    signup = await client.post(
        "/api/v1/users",
        json={
            "email": f"{name}@{domain}",
            "password1": "hunter22!",
            "password2": "hunter22!",
            "adult_attested": True,
        },
    )
    assert signup.status_code == 201, signup.text
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@{domain}", "password": "hunter22!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    named = await client.put(
        "/api/v1/users/me/name",
        json={"nickname": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert named.status_code == 200, named.text
    return UUID(signup.json()["id"]), token


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def commit_profile(client, token: str, **overrides) -> None:
    """The player's own profile, through the route the client uses."""

    body = {
        "social_tag_ids": list(COMPETITIVE_TAGS),
        "photo_ids": [],
        "weekly_hours": [
            {"day": 2, "hour": 19},
            {"day": 6, "hour": 10},
        ],
        "location": {"latitude": CENTRE[0], "longitude": CENTRE[1]},
        "gender": "WOMAN",
    }
    body.update(overrides)
    response = await client.post(
        "/api/v1/players/me/profile",
        json=body,
        headers={**auth(token), "Idempotency-Key": f"commit-{token[:12]}"},
    )
    assert response.status_code == 201, response.text


async def rate(client, token: str, sport: Sport = SPORT) -> float:
    """The shortest honest path to a stored rating, and the μ it produced."""

    created = (
        await client.post(
            "/api/v1/assessments", json={"sport": sport.value}, headers=auth(token)
        )
    ).json()
    await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/answers",
        json={"question_id": created["question"]["id"], "option_id": "never-played"},
        headers=auth(token),
    )
    done = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/completion",
        headers=auth(token),
    )
    assert done.status_code == 200, done.text
    return float(done.json()["result"]["mu"])


async def declare_intent(
    client,
    token: str,
    *,
    intent: str = "COMPETITIVE",
    sport: Sport = SPORT,
) -> None:
    """The player's Play intent, through ADR-0094's own route — ``RATING_TAIL``,
    where a first declaration is made."""

    response = await client.put(
        f"/api/v1/play-intents/{sport.value}",
        json={"intent": intent, "surface": "RATING_TAIL"},
        headers=auth(token),
    )
    assert response.status_code == 200, response.text


async def a_rated_player(
    client,
    name: str,
    *,
    intent: str = "COMPETITIVE",
    sport: Sport = SPORT,
    location: tuple[float, float] = CENTRE,
    gender: str = "WOMAN",
    intro: str | None = None,
) -> dict:
    """One player with a profile, a rating from a real assessment and a declared
    intent — each through the route a person would use. Their id, token and μ."""

    player_id, token = await register(client, name)
    profile: dict = {
        "location": {"latitude": location[0], "longitude": location[1]},
        "gender": gender,
    }
    if intro is not None:
        profile["intro"] = intro
    await commit_profile(client, token, **profile)
    mu = await rate(client, token, sport)
    await declare_intent(client, token, intent=intent, sport=sport)
    return {"id": player_id, "token": token, "mu": mu}


async def a_player_on_the_log(
    client,
    session_factory,
    name: str,
    *,
    mu: float,
    latitude: float = CENTRE[0],
    longitude: float = CENTRE[1],
    tags: tuple[str, ...] = COMPETITIVE_TAGS,
    photo_ids: tuple[UUID, ...] = (),
    availability: tuple[str, ...] = SHARED_SLOTS,
    gender: str = "WOMAN",
    gender_preference: str = "ANY",
    intent: str | None = "COMPETITIVE",
    at: datetime = LONG_AGO,
    intro: str | None = None,
) -> tuple[UUID, str]:
    """A player whose profile, Level and intent are **filed on the log** at a
    chosen instant — for a test that needs a fact the routes do not take
    dictation for: a chosen Level, a chosen week, a profile committed long ago.
    Registered and named through the routes, so every surface that reads a
    name finds one. Their id and a bearer token.
    """

    player_id, token = await register(client, name)
    await append(
        session_factory,
        PlayerProfileCreated(
            player_id=player_id,
            social_tags=tags,
            photo_ids=tuple(str(photo_id) for photo_id in photo_ids),
            weekly_hours=availability,
            latitude=latitude,
            longitude=longitude,
            idempotency_key=f"key-{player_id}",
            occurred_at=at,
            gender=gender,
            gender_preference=gender_preference,
        ),
        # **A profile's stream id is the player id itself**, and the card is
        # assembled from the profile port rather than from the index — so a
        # profile filed under a random id is one the card source cannot load,
        # and every candidate here would silently have no photograph.
        aggregate_type=PLAYER_PROFILE_AGGREGATE,
        aggregate_id=player_id,
    )
    if intro is not None:
        # Only where a line was written — and on the profile's own stream, at
        # the version after the creating event, because the record reads the
        # line off the *fold* while the card reads it off the index
        # (`docs/adr/0170` §3).
        await append(
            session_factory,
            IntroWritten(player_id, intro, at),
            aggregate_type=PLAYER_PROFILE_AGGREGATE,
            aggregate_id=player_id,
            version=2,
        )
    await append(
        session_factory,
        a_rating(player_id, mu=mu, at=at),
        # **A rating's stream id is derived from ``(player, sport)``**, and until
        # ``docs/adr/0139`` nothing read one back by that address — the candidate
        # index tails the log by sequence, so a rating filed under a random
        # profile-shaped id was indistinguishable from a real one. ``at_stake``
        # reads the stream, so a candidate filed anywhere else is a candidate the
        # block is silently never drawn for.
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(player_id, SPORT),
    )
    if intent is not None:
        await append(
            session_factory,
            PlayIntentDeclared(player_id, SPORT.value, intent, "RATING_TAIL", at),
        )
    return player_id, token


async def rate_in(session_factory, player_id: UUID, sport: Sport, *, mu: float) -> None:
    """A Level of ``mu`` in ``sport``, filed on its own stream, keyed by
    ``(player, sport)`` as the rating context keys one."""

    await append(
        session_factory,
        a_rating(player_id, mu=mu, at=LONG_AGO, sport=sport),
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(player_id, sport),
    )


def a_rating(
    player_id: UUID, *, mu: float, at: datetime, sport: Sport = SPORT
) -> RatingInitialised:
    """One player's Level, filed where the rating context files one."""

    return RatingInitialised(
        rating_id=skill_rating_id(player_id, sport),
        player_id=player_id,
        sport=sport.value,
        mu=mu,
        sigma=0.34,
        confidence=62,
        range_low=mu - 0.3,
        range_high=mu + 0.3,
        band_name="Improver",
        band_lower=2.5,
        band_upper=3.0,
        status="INITIAL_ESTIMATE",
        engine_version="v3",
        source_assessment_id=UUID(int=player_id.int ^ 1),
        occurred_at=at,
    )


async def a_confirmed_game(
    session_factory, a: UUID, b: UUID, *, sport: Sport, a_won: bool
) -> None:
    """One counted singles game between them, booked for an hour a month ago,
    played, and its score confirmed by silence.

    Written through the aggregate, opened the way a booking opens one — its hour
    on it — because what a record reads is a fold over the history, and the only
    honest way to exercise one is to make that history. **Dated a month back**:
    a confirmation is a clock passing rather than an act (``docs/adr/0137``).
    """

    played = instant(datetime.now(timezone.utc) - timedelta(days=30))
    starts_at = instant(played - timedelta(hours=1))
    game = Game.planned(
        game_id=new_uuid(),
        # A booked game is filed under its booking's id.
        challenge_id=new_uuid(),
        sport=sport,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=a),
                Seating(side=GameSide.B, player_id=b),
            )
        ),
        occurred_at=instant(starts_at - timedelta(days=2)),
        starts_at=starts_at,
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


async def a_booked_game(
    session_factory,
    *,
    side_a: tuple[UUID, ...],
    side_b: tuple[UUID, ...],
    sport: Sport = SPORT,
    kind: GameKind = GameKind.COUNTED,
    starts_at: datetime | None = None,
    booked_at: datetime | None = None,
) -> dict:
    """A booked game, opened through the aggregate the way the fill opens one —
    filed under its booking's id, its hour on it. Its id and its booking's.

    **Its room opens when the outbox is delivered** (#575): ``GamePlanned`` with
    an hour on it is what opens a booked game's chat, so a test that reads the
    room calls :func:`deliver_the_outbox` after this. Unless told otherwise the
    game is booked now and played tomorrow at the same time.
    """

    now = datetime.now(timezone.utc)
    starts = instant(starts_at or now + timedelta(days=1))
    game = Game.planned(
        game_id=new_uuid(),
        # A booked game is filed under its booking's id.
        challenge_id=new_uuid(),
        sport=sport,
        kind=kind,
        window=None,
        line_up=LineUp.of(
            (
                *(Seating(side=GameSide.A, player_id=one) for one in side_a),
                *(Seating(side=GameSide.B, player_id=one) for one in side_b),
            )
        ),
        occurred_at=instant(booked_at or min(now, starts - timedelta(days=2))),
        starts_at=starts,
    )
    async with session_factory() as session:
        await build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(game)
        await session.commit()
    return {"game_id": game.game_id, "booking_id": game.challenge_id}


async def block_between(client, token: str, player_id: UUID):
    """One player blocking another, through the route a person would use."""

    return await client.post(
        "/api/v1/blocks",
        json={"player_id": str(player_id)},
        headers=auth(token),
    )


def override(client, dependency, factory) -> None:
    """Replace one dependency on the running application, for one test.

    The ``client`` fixture holds the app rather than exposing it, so reaching for
    it is a private access — written once, here.
    """

    client._transport.app.dependency_overrides[dependency] = factory  # noqa: SLF001


def hold_only(client, *player_ids) -> None:
    """A hold on these players and **nobody else** — the reader included out.

    The hold has no producer in this build — nothing can hold anybody, which is
    why the gate ships true-over-empty — so the only way to drive it over HTTP is
    to replace the query. It answers **only about ids it was asked about**, which
    is the port's own contract and not a shortcut taken here.
    """

    from app.modules.matchmaking.presentation.dependencies import (
        get_account_hold_query,
    )

    held = frozenset(player_ids)

    class Holding:
        async def held_among(self, asked):
            return frozenset(asked) & held

    override(client, get_account_hold_query, Holding)


def may_not_show(client, *player_ids) -> None:
    """``users`` refusing to have these players shown, and saying so to nobody."""

    from app.modules.matchmaking.presentation.dependencies import (
        get_account_status_query,
    )

    unshowable = frozenset(player_ids)

    class Unshowable:
        async def may_not_be_shown(self, candidate_ids):
            return frozenset(candidate_ids) & unshowable

    override(client, get_account_status_query, Unshowable)


async def deliver_the_outbox(
    session_factory,
    *,
    rounds: int = 6,
    live_channel=None,
    payments=None,
    proposer_due=None,
    push=None,
) -> int:
    """Run the transactional outbox to exhaustion, the way the worker does.

    Built through ``EventRuntime.create_event_batch_for``, so the delivery this
    drives is the delivery that ships. **Rounds, because delivery cascades**: a
    room opened by a booking publishes its own events, so it drains until a round
    publishes nothing.

    - ``live_channel`` makes the delivery live — the fake the ``client`` fixture
      publishes and follows over; left out, nobody is following.
    - ``payments`` is the provider a released card or a refund is asked of —
      the ``payments`` fixture when a test reads it; otherwise a fake nobody
      reads.
    - ``proposer_due`` is the proposer listening (#540); left out, nobody is.
    - ``push`` is the push service a notice is pushed through — the ``pushes``
      fixture when a test reads what a phone was pushed (#549).
    """

    runtime = build_event_runtime()
    provider = payments if payments is not None else FakePayments()
    nudges = (
        NobodyIsFollowing()
        if live_channel is None
        else build_nudge_publisher(live_channel)
    )
    published = 0
    for _ in range(rounds):
        async with session_factory() as session:
            batch = runtime.create_event_batch_for(
                session=session,
                clock=build_clock(),
                batch_size=100,
                nudges=nudges,
                payments=provider,
                push=push if push is not None else RecordingPush(),
                proposer_due=proposer_due,
            )
            delivered = await batch.execute(worker_id="tests")
        published += delivered
        if not delivered:
            break
    return published

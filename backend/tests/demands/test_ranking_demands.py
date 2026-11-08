"""What Rankings demands of other contexts (#768, #771, #772), run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/ranking_demands.py`` is enrolled here automatically. **Every
rating is arranged through the rating's own aggregate**, saved by its own
repository, and every account through the player routes — never an ``INSERT``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_skill_rating_repository,
)
from app.bootstrap.ranking_demands import (
    RANKING_DEMANDS,
    RANKING_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import STATUS_INITIAL_ESTIMATE
from app.kernel import Sport, instant
from app.modules.rankings.domain.ports import (
    BlocksEitherWay,
    GeneralSwitches,
    RankedFace,
    RankedFaces,
    RatingHistories,
    ReadersFriends,
    SportLevels,
)
from app.modules.rankings.domain.ranking import LevelMove
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.api import players_world as players
from tests.api.rankings_world import move_on
from tests.demands import friends_world
from tests.unit import image_fixtures

OPENED = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))
BAND = BandView(name="Improver", lower=2.5, upper=3.0)


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _ratings(session):
    return build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


async def _rated(session, player_id: UUID, *, mu: float, sport: Sport) -> None:
    await _ratings(session).save(
        SkillRating.initialise(
            rating_id=skill_rating_id(player_id, sport),
            player_id=player_id,
            sport=sport,
            result=AssessmentResult(
                mu=mu,
                sigma=0.34,
                confidence=50,
                range_low=round(mu - 0.34, 2),
                range_high=round(mu + 0.34, 2),
                band=BAND,
                status=STATUS_INITIAL_ESTIMATE,
                questions_asked=7,
                engine_version="racketskill-fusion-v3",
                confidence_ceiling=50,
            ),
            source_assessment_id=new_uuid(),
            occurred_at=OPENED,
        )
    )
    await session.commit()


async def _moved(
    session, player_id: UUID, *, mu: float, won: bool, hours: int, sport: Sport
) -> UUID:
    return await move_on(
        session,
        player_id,
        mu,
        at=instant(OPENED + timedelta(hours=hours)),
        won=won,
        sport=sport,
    )


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_demand_has_at_least_one_implementation():
    assert [p.__name__ for p in RANKING_DEMANDS if not implementations_of(p)] == []


def test_every_registered_implementation_is_of_a_demand():
    assert all(one.port in RANKING_DEMANDS for one in RANKING_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# RatingHistories — the record every row is folded from
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(RatingHistories))
async def test_a_history_is_the_opening_and_every_move_in_stream_order(
    implementation, session
):
    histories: RatingHistories = implementation.build(session)
    player = new_uuid()
    await _rated(session, player, mu=2.5, sport=Sport.PADEL)
    first = await _moved(session, player, mu=2.56, won=True, hours=1, sport=Sport.PADEL)
    second = await _moved(
        session, player, mu=2.51, won=False, hours=2, sport=Sport.PADEL
    )

    history = await histories.history_of(player, Sport.PADEL)
    opened, *moved = await build_domain_event_store(session).load_stream(
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(player, Sport.PADEL),
    )

    assert history is not None
    assert (history.player_id, history.sport) == (player, Sport.PADEL)
    assert (history.initial_mu, history.initialised_at) == (2.5, OPENED)
    # Each carries the stored event that recorded it, which keys its point in
    # the level history (#769).
    assert history.opened_by == opened.id
    assert history.moves == (
        LevelMove(
            game_id=first,
            won=True,
            mu=2.56,
            sigma=0.3,
            at=instant(OPENED + timedelta(hours=1)),
            event_id=moved[0].id,
        ),
        LevelMove(
            game_id=second,
            won=False,
            mu=2.51,
            sigma=0.3,
            at=instant(OPENED + timedelta(hours=2)),
            event_id=moved[1].id,
        ),
    )


@pytest.mark.parametrize("implementation", registered(RatingHistories))
async def test_a_sport_with_no_rating_has_no_history(implementation, session):
    histories: RatingHistories = implementation.build(session)
    player = new_uuid()
    await _rated(session, player, mu=2.5, sport=Sport.PADEL)

    assert await histories.history_of(player, Sport.SQUASH) is None
    unmoved = await histories.history_of(player, Sport.PADEL)
    assert unmoved is not None and unmoved.moves == ()


@pytest.mark.parametrize("implementation", registered(RatingHistories))
async def test_every_history_is_every_rating_there_is(implementation, session):
    histories: RatingHistories = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    await _rated(session, one, mu=2.5, sport=Sport.PADEL)
    await _rated(session, other, mu=3.0, sport=Sport.TENNIS)
    await _rated(session, one, mu=2.0, sport=Sport.SQUASH)
    await _moved(session, other, mu=3.04, won=True, hours=1, sport=Sport.TENNIS)

    every = await histories.every_history()

    assert [
        (history.player_id, history.sport, len(history.moves)) for history in every
    ] == [
        (one, Sport.PADEL, 0),
        (other, Sport.TENNIS, 1),
        (one, Sport.SQUASH, 0),
    ]


# --------------------------------------------------------------------------- #
# RankedFaces — a nickname and a photograph
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(RankedFaces))
async def test_everybody_asked_about_is_answered(implementation, client, session):
    faces: RankedFaces = implementation.build(session)
    tomek, _ = await players.register(client, "tomek")
    nobody = new_uuid()

    found = await faces.faces_of([tomek, nobody])

    assert found == {
        tomek: RankedFace(player_id=tomek, nickname="tomek"),
        nobody: RankedFace(player_id=nobody),
    }
    assert await faces.faces_of([]) == {}


# --------------------------------------------------------------------------- #
# SportLevels — a level held, read live
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(SportLevels))
async def test_a_level_is_held_in_a_rated_sport_and_no_other(implementation, session):
    levels: SportLevels = implementation.build(session)
    player = new_uuid()
    await _rated(session, player, mu=2.5, sport=Sport.PADEL)

    assert await levels.holds_a_level(player, Sport.PADEL) is True
    assert await levels.holds_a_level(player, Sport.BADMINTON) is False
    assert await levels.holds_a_level(new_uuid(), Sport.PADEL) is False


@pytest.mark.parametrize("implementation", registered(RankedFaces))
async def test_a_face_is_the_first_photograph_with_a_link_to_it(
    implementation, client, session
):
    faces: RankedFaces = implementation.build(session)
    ewa, token = await players.register(client, "ewa")
    uploaded = await client.post(
        "/api/v1/photos",
        content=image_fixtures.plain_jpeg(),
        headers={**players.auth(token), "Content-Type": "image/jpeg"},
    )
    assert uploaded.status_code == 201, uploaded.text
    photo_id = UUID(uploaded.json()["photo_id"])
    await players.commit_profile(client, token, photo_ids=[str(photo_id)])

    face = (await faces.faces_of([ewa]))[ewa]

    assert (face.nickname, face.photo_id) == ("ewa", photo_id)
    assert face.photo_url is not None and str(photo_id) in face.photo_url


# --------------------------------------------------------------------------- #
# ReadersFriends — the reader's friends now (#771)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ReadersFriends))
async def test_the_readers_friends_are_friends_now_and_nobody_merely_asked(
    implementation, session
):
    tomek, karol, zofia, ines, ewa = (new_uuid() for _ in range(5))
    await friends_world.befriends(session, tomek, karol)
    await friends_world.befriends(session, zofia, tomek)
    await friends_world.asks(session, tomek, ines)
    await friends_world.asks(session, ewa, tomek, set_aside=True)
    await friends_world.befriends(session, karol, zofia)
    friends: ReadersFriends = implementation.build(session)

    assert await friends.friends_of(tomek) == {karol, zofia}
    assert await friends.friends_of(ines) == frozenset()


@pytest.mark.parametrize("implementation", registered(ReadersFriends))
async def test_a_friendship_ended_or_blocked_is_no_friend(implementation, session):
    tomek, karol, zofia = (new_uuid() for _ in range(3))
    await friends_world.befriends(session, tomek, karol)
    await friends_world.befriends(session, tomek, zofia)
    await friends_world.removes(session, karol, tomek)
    await friends_world.ends_by_a_block(session, zofia, tomek)
    friends: ReadersFriends = implementation.build(session)

    assert await friends.friends_of(tomek) == frozenset()


# --------------------------------------------------------------------------- #
# BlocksEitherWay — whose rows each view leaves out (#772)
# --------------------------------------------------------------------------- #


async def _blocks(client, blocker_token: str, blocked: UUID) -> None:
    made = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked)},
        headers=players.auth(blocker_token),
    )
    assert made.status_code == 204, made.text


@pytest.mark.parametrize("implementation", registered(BlocksEitherWay))
async def test_a_block_is_answered_for_both_of_them_and_a_lifted_one_for_neither(
    implementation, client, session
):
    blocks: BlocksEitherWay = implementation.build(session)
    tomek, tomeks = await players.register(client, "tomek")
    marek, mareks = await players.register(client, "marek")
    ewa, ewas = await players.register(client, "ewa")
    await _blocks(client, tomeks, marek)
    await _blocks(client, ewas, tomek)

    # Whichever of them made it, in one flat set.
    assert await blocks.blocked_either_way(tomek) == {marek, ewa}
    assert await blocks.blocked_either_way(marek) == {tomek}
    assert await blocks.blocked_either_way(ewa) == {tomek}

    lifted = await client.delete(
        f"/api/v1/blocks/{marek}", headers=players.auth(tomeks)
    )
    assert lifted.status_code == 204, lifted.text

    assert await blocks.blocked_either_way(marek) == frozenset()
    assert await blocks.blocked_either_way(tomek) == {ewa}
    assert await blocks.blocked_either_way(new_uuid()) == frozenset()


# --------------------------------------------------------------------------- #
# GeneralSwitches — a player's Show me in General, read live (#772)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(GeneralSwitches))
async def test_a_switch_is_the_profile_as_it_stands_and_the_version_it_stands_at(
    implementation, client, session
):
    switches: GeneralSwitches = implementation.build(session)
    tomek = await players.a_rated_player(client, "tomek")

    shown = await switches.switch_of(tomek["id"])
    turned = await client.put(
        "/api/v1/players/me/ranking-visibility",
        json={"visibility": "HIDDEN"},
        headers=players.auth(tomek["token"]),
    )
    assert turned.status_code == 204, turned.text
    hidden = await switches.switch_of(tomek["id"])

    # Every profile starts shown.
    assert shown is not None and (shown.player_id, shown.hidden) == (tomek["id"], False)
    assert hidden is not None and hidden.hidden is True
    # A later reading is at a later version, which is what lets the rows
    # refuse an older one.
    assert hidden.version > shown.version
    assert await switches.switch_of(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(GeneralSwitches))
async def test_every_switch_is_every_profiles_rated_or_not(
    implementation, client, session
):
    switches: GeneralSwitches = implementation.build(session)
    tomek = await players.a_rated_player(client, "tomek")
    ewa, token = await players.register(client, "ewa")
    await players.commit_profile(client, token)
    turned = await client.put(
        "/api/v1/players/me/ranking-visibility",
        json={"visibility": "HIDDEN"},
        headers=players.auth(token),
    )
    assert turned.status_code == 204, turned.text
    # An account with no profile has no switch to keep.
    await players.register(client, "nobody")

    every = await switches.every_switch()

    assert {(one.player_id, one.hidden) for one in every} == {
        (tomek["id"], False),
        (ewa, True),
    }

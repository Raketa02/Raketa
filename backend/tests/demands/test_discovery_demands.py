"""What Discovery demands of other contexts (#793), run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/discovery_demands.py`` is enrolled here automatically. Accounts
and profiles are arranged through the player routes, friendships and blocks
through their aggregates (``friends_world``), a rating through the rating's own
repository — never an ``INSERT``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_ruleset,
    build_skill_rating_repository,
)
from app.bootstrap.discovery_demands import (
    DISCOVERY_DEMANDS,
    DISCOVERY_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import STATUS_INITIAL_ESTIMATE, SkillEstimate
from app.engines.racketskill.update_v1 import MovedRating, Stakes
from app.kernel import Sport, instant
from app.modules.discovery.domain.directory import Area
from app.modules.discovery.domain.levels import Band, CurrentLevel, Estimate
from app.modules.discovery.domain.ports import (
    BlocksEitherWay,
    DirectoryFaces,
    DirectorySources,
    HowEven,
    LevelSources,
    LevelsHeld,
    ReadersRelations,
    SportLevel,
)
from app.modules.discovery.domain.relation import Relation
from app.modules.matchmaking.domain.balance import forecast_the_sides
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.users.domain.events import UserRegistered
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.shared.ids import new_uuid
from tests.api import players_world as players
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


async def _rated(session, player_id: UUID, *, mu: float, sport: Sport) -> None:
    await build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(
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


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_demand_has_at_least_one_implementation():
    assert [p.__name__ for p in DISCOVERY_DEMANDS if not implementations_of(p)] == []


def test_every_registered_implementation_is_of_a_demand():
    assert all(one.port in DISCOVERY_DEMANDS for one in DISCOVERY_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# DirectorySources — what the owners hold now
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(DirectorySources))
async def test_a_player_is_their_nickname_and_their_profile_as_it_stands(
    implementation, client, session, clock
):
    sources: DirectorySources = implementation.build(session)
    ewa, token = await players.register(client, "ewa")
    uploaded = await client.post(
        "/api/v1/photos",
        content=image_fixtures.plain_jpeg(),
        headers={**players.auth(token), "Content-Type": "image/jpeg"},
    )
    assert uploaded.status_code == 201, uploaded.text
    photo_id = UUID(uploaded.json()["photo_id"])
    await players.commit_profile(
        client,
        token,
        photo_ids=[str(photo_id)],
        location={"latitude": 50.06, "longitude": 19.94},
    )
    await players.closed_to_new_people(client, token)

    entry = await sources.entry_of(ewa)

    assert entry is not None and entry.plays
    assert entry.nickname == "ewa"
    assert entry.player is not None
    assert entry.player.photo_id == photo_id
    assert entry.player.area == Area(latitude=50.06, longitude=19.94)
    assert entry.player.tags == frozenset(players.COMPETITIVE_TAGS)
    assert entry.player.open_to_new_people is False
    # *Joined* is the commit's instant, on the clock the request ran on.
    assert entry.player.joined_at == clock.now()


@pytest.mark.parametrize("implementation", registered(DirectorySources))
async def test_an_account_with_no_profile_doesnt_play_and_one_nobody_holds_is_gone(
    implementation, client, session
):
    sources: DirectorySources = implementation.build(session)
    halfway, _ = await players.register(client, "halfway")

    entry = await sources.entry_of(halfway)

    assert entry is not None
    assert (entry.nickname, entry.plays) == ("halfway", False)
    assert await sources.entry_of(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(DirectorySources))
async def test_a_disabled_account_is_gone(implementation, session):
    sources: DirectorySources = implementation.build(session)
    disabled = new_uuid()
    await SqlAlchemyUserRepository(session).project_registered(
        UserRegistered(
            user_id=disabled,
            email="disabled@example.com",
            password_hash="x" * 12,
            authority="USER",
            is_admin=False,
            is_active=False,
            occurred_at=OPENED,
            adult_attested=True,
        )
    )

    assert await sources.entry_of(disabled) is None


@pytest.mark.parametrize("implementation", registered(DirectorySources))
async def test_every_account_is_every_account_oldest_first(
    implementation, client, session
):
    sources: DirectorySources = implementation.build(session)
    first, _ = await players.register(client, "first")
    second, _ = await players.register(client, "second")

    assert list(await sources.every_account()) == [first, second]


# --------------------------------------------------------------------------- #
# ReadersRelations — the round friend button
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ReadersRelations))
async def test_everybody_asked_about_is_answered_from_the_readers_side(
    implementation, session
):
    tomek, karol, ines, ewa, nobody = (new_uuid() for _ in range(5))
    await friends_world.befriends(session, tomek, karol)
    await friends_world.asks(session, tomek, ines)
    await friends_world.asks(session, ewa, tomek, set_aside=True)
    relations: ReadersRelations = implementation.build(session)

    assert await relations.relations_of(tomek, [karol, ines, ewa, nobody]) == {
        karol: Relation.FRIEND,
        ines: Relation.SENT,
        ewa: Relation.ASKED_YOU,
        nobody: Relation.NONE,
    }


@pytest.mark.parametrize("implementation", registered(ReadersRelations))
async def test_a_request_the_readers_own_block_hides_reads_none(
    implementation, session
):
    tomek, marek = new_uuid(), new_uuid()
    await friends_world.asks(session, marek, tomek)
    await friends_world.blocks(session, tomek, marek)
    relations: ReadersRelations = implementation.build(session)

    assert await relations.relations_of(tomek, [marek]) == {marek: Relation.NONE}


# --------------------------------------------------------------------------- #
# BlocksEitherWay
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(BlocksEitherWay))
async def test_blocks_either_way_are_one_set(implementation, session):
    tomek, blocked, blocker, stranger = (new_uuid() for _ in range(4))
    await friends_world.blocks(session, tomek, blocked)
    await friends_world.blocks(session, blocker, tomek)
    await friends_world.blocks(session, blocker, stranger)
    blocks: BlocksEitherWay = implementation.build(session)

    assert await blocks.either_way(tomek) == {blocked, blocker}
    assert await blocks.either_way(new_uuid()) == frozenset()


# --------------------------------------------------------------------------- #
# LevelsHeld
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(LevelsHeld))
async def test_every_sport_with_a_level_in_the_sports_order_and_none_for_unrated(
    implementation, session
):
    bartek, ola = new_uuid(), new_uuid()
    await _rated(session, bartek, mu=2.10, sport=Sport.BADMINTON)
    await _rated(session, bartek, mu=2.35, sport=Sport.PADEL)
    levels: LevelsHeld = implementation.build(session)

    assert await levels.levels_of([bartek, ola]) == {
        bartek: (
            SportLevel(sport=Sport.PADEL, level=2.35),
            SportLevel(sport=Sport.BADMINTON, level=2.10),
        ),
        ola: (),
    }
    assert await levels.levels_of([]) == {}


# --------------------------------------------------------------------------- #
# DirectoryFaces
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(DirectoryFaces))
async def test_a_face_is_a_link_to_the_owners_photograph(implementation, session):
    faces: DirectoryFaces = implementation.build(session)
    owner, photo = new_uuid(), new_uuid()

    url = await faces.photo_url(owner, photo)

    assert str(photo) in url and str(owner) in url


# --------------------------------------------------------------------------- #
# LevelSources — where a rating stands (#794)
# --------------------------------------------------------------------------- #


async def _moved(session, player_id: UUID, *, mu: float, sigma: float, sport: Sport):
    ratings = build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    rating = await ratings.find_for(player_id=player_id, sport=sport)
    assert rating is not None
    rating.move_on_result(
        game_id=new_uuid(),
        moved=MovedRating(
            mu=mu,
            sigma=sigma,
            confidence=70,
            range_low=round(mu - sigma, 2),
            range_high=round(mu + sigma, 2),
            band=BandView(name="Established", lower=2.7, upper=3.8),
            status="Calibrating",
            stakes=Stakes(win=0.03, loss=-0.03),
        ),
        won=True,
        opposition=SkillEstimate(mu=mu, sigma=0.3),
        information_share=0.5,
        occurred_at=OPENED,
    )
    await ratings.save(rating)
    await session.commit()


@pytest.mark.parametrize("implementation", registered(LevelSources))
async def test_a_rating_stands_at_its_opening_then_at_its_last_result(
    implementation, session
):
    sources: LevelSources = implementation.build(session)
    zofia, ola = new_uuid(), new_uuid()
    await _rated(session, zofia, mu=2.60, sport=Sport.PADEL)

    opened = await sources.level_of(zofia, Sport.PADEL)
    assert opened == CurrentLevel(
        player_id=zofia,
        sport=Sport.PADEL,
        mu=2.60,
        sigma=0.34,
        band=Band(name="Improver", lower=2.5, upper=3.0),
        results=0,
    )

    await _moved(session, zofia, mu=2.69, sigma=0.21, sport=Sport.PADEL)
    moved = await sources.level_of(zofia, Sport.PADEL)
    assert moved == CurrentLevel(
        player_id=zofia,
        sport=Sport.PADEL,
        mu=2.69,
        sigma=0.21,
        band=Band(name="Established", lower=2.7, upper=3.8),
        results=1,
    )
    assert await sources.level_of(zofia, Sport.TENNIS) is None
    assert await sources.level_of(ola, Sport.PADEL) is None


@pytest.mark.parametrize("implementation", registered(LevelSources))
async def test_every_level_is_every_rating_as_it_stands(implementation, session):
    sources: LevelSources = implementation.build(session)
    zofia = new_uuid()
    await _rated(session, zofia, mu=2.60, sport=Sport.PADEL)
    await _rated(session, zofia, mu=2.55, sport=Sport.SQUASH)
    await _moved(session, zofia, mu=2.69, sigma=0.21, sport=Sport.PADEL)

    levels = {
        (one.sport, one.mu, one.results)
        for one in await sources.every_level()
        if one.player_id == zofia
    }

    assert levels == {(Sport.PADEL, 2.69, 1), (Sport.SQUASH, 2.55, 0)}


# --------------------------------------------------------------------------- #
# HowEven — the matcher's own forecast, one a side (#794)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(HowEven))
@pytest.mark.parametrize("sport", list(Sport))
def test_the_percent_is_the_matchers_forecast_one_player_a_side(implementation, sport):
    even: HowEven = implementation.build(None)
    you, them = UUID(int=10), UUID(int=11)

    for yours, theirs in [((2.71, 0.13), (2.69, 0.13)), ((2.71, 0.13), (2.35, 0.8))]:
        sides = forecast_the_sides(
            (you,),
            (them,),
            {you: SkillEstimate(*yours), them: SkillEstimate(*theirs)},
            sport=sport,
            rules=build_ruleset().balance,
        )
        assert sides is not None
        assert even.percent_even(sport, Estimate(*yours), Estimate(*theirs)) == (
            sides[0].pct
        )


@pytest.mark.parametrize("implementation", registered(HowEven))
def test_the_percent_falls_with_the_gap_and_with_either_doubt(implementation):
    even: HowEven = implementation.build(None)
    rules = build_ruleset().balance

    def pct(gap: float, yours: float = 0.1, theirs: float = 0.1) -> int:
        return even.percent_even(
            Sport.PADEL, Estimate(2.71, yours), Estimate(2.71 + gap, theirs)
        )

    assert pct(0.0) >= pct(0.05) >= pct(0.2) >= pct(1.0)
    assert pct(0.0) > pct(0.2)
    assert pct(0.05) == pct(-0.05)
    assert pct(0.05, theirs=0.1) > pct(0.05, theirs=0.8)
    assert pct(0.05, yours=0.1) > pct(0.05, yours=0.8)
    # The forecast's own bounds.
    assert pct(0.0, 0.0, 0.0) == rules.pct_max
    assert pct(3.0) == rules.pct_min

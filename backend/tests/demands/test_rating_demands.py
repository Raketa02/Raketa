"""What ``rating`` owes the rest of the platform, run against every implementation.

**One port, and it is contracted for the reason the other two registers exist**
(``docs/adr/0098``, ``docs/adr/0139``). ``RatedPlayerQuery`` has one consumer —
the at-stake block — and that consumer **fails soft**, so a read that quietly
stopped finding anybody would draw no block and raise nothing. An absence nobody
can tell from a measured one is exactly what this suite is for.

**Every arrangement goes through ``rating``'s own aggregate**, never through the
adapter's storage: a demand asserted against the thing that implements it is a
demand satisfied by construction.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_skill_rating_repository,
)
from app.bootstrap.rating_demands import (
    RATING_DEMANDS,
    RATING_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import (
    STATUS_INITIAL_ESTIMATE,
    band_for,
    confidence_percent,
    likely_range,
)
from app.kernel import Sport
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.ports import RatedPlayerQuery
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


async def _rated(session, *, mu: float, sigma: float, sport: Sport, player_id=None):
    player_id = player_id or new_uuid()
    band = band_for(mu)
    low, high = likely_range(mu, sigma)
    ratings = build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    await ratings.save(
        SkillRating.initialise(
            rating_id=skill_rating_id(player_id, sport),
            player_id=player_id,
            sport=sport,
            result=AssessmentResult(
                mu=mu,
                sigma=sigma,
                confidence=confidence_percent(sigma),
                range_low=round(low, 2),
                range_high=round(high, 2),
                band=BandView(name=band.label, lower=band.lower, upper=band.upper),
                status=STATUS_INITIAL_ESTIMATE,
                questions_asked=7,
                engine_version="racketskill-fusion-v3",
                confidence_ceiling=confidence_percent(sigma),
            ),
            source_assessment_id=new_uuid(),
            occurred_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()
    return player_id


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_a_rated_player_crosses_as_the_level_and_the_uncertainty(
    implementation, session
):
    """Both, and never the Level alone.

    *Skill and certainty are separate variables*, and a port that answered μ
    without σ would let the one consumer price a pairing it could not know how
    sure of.
    """

    port = implementation.build(session)
    player_id = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)

    found = await port.estimates_for([player_id], sport=Sport.PADEL)

    assert found[player_id].mu == 3.20
    assert found[player_id].sigma == 0.30


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_one_player_crosses_with_every_sport_they_are_rated_in(
    implementation, session
):
    """**The record's read, and the mirror of the one above it.** The matcher
    holds twenty rows in one sport; a record is one person opened by a tap and
    wants every sport they hold."""

    port = implementation.build(session)
    player_id = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)
    await _rated(
        session, mu=4.10, sigma=0.50, sport=Sport.SQUASH, player_id=player_id
    )

    held = await port.ratings_of(player_id)

    assert set(held) == {Sport.PADEL, Sport.SQUASH}
    assert held[Sport.PADEL].mu == 3.20
    assert held[Sport.SQUASH].mu == 4.10
    assert held[Sport.SQUASH].band_name == band_for(4.10).label


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_a_published_rating_carries_what_a_screen_prints_and_no_more(
    implementation, session
):
    """The figures the rating already committed to its own stream — the
    certainty, the range the engine rounded and the band's published name — with
    nothing derived a second time on the way out."""

    port = implementation.build(session)
    player_id = await _rated(session, mu=2.60, sigma=0.40, sport=Sport.TENNIS)

    (rating,) = (await port.ratings_of(player_id)).values()

    low, high = likely_range(2.60, 0.40)
    assert rating.sport is Sport.TENNIS
    assert rating.confidence == confidence_percent(0.40)
    assert (rating.range_low, rating.range_high) == (round(low, 2), round(high, 2))
    assert rating.band_name == band_for(2.60).label


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_a_rating_no_game_has_tested_rests_on_nought_counted_results(
    implementation, session
):
    """**A measured nought and not an absence.** A Level straight out of the
    questionnaire has moved on no result, and the number the skill card prints
    beside its certainty says exactly that (``docs/adr/0139``)."""

    port = implementation.build(session)
    player_id = await _rated(session, mu=3.00, sigma=0.35, sport=Sport.PADEL)

    assert (await port.ratings_of(player_id))[Sport.PADEL].counted_results == 0


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_a_player_rated_in_nothing_holds_nothing(implementation, session):
    """The ordinary state part way through onboarding, and never an error."""

    port = implementation.build(session)

    assert await port.ratings_of(new_uuid()) == {}


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_an_unrated_player_is_absent_and_never_a_population_mean(
    implementation, session
):
    """The rule the whole platform applies to a fact nobody has measured.

    A middle-of-the-scale stand-in would price a pairing against somebody who does
    not exist, and the block would be drawn confidently about nothing.
    """

    port = implementation.build(session)

    assert await port.estimates_for([new_uuid()], sport=Sport.PADEL) == {}


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_a_rating_is_per_player_and_sport_and_answers_about_neither_alone(
    implementation, session
):
    """A padel Level is not a tennis Level, and asking for one never finds the other."""

    port = implementation.build(session)
    player_id = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)

    assert await port.estimates_for([player_id], sport=Sport.PADEL)
    assert await port.estimates_for([player_id], sport=Sport.TENNIS) == {}


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_it_answers_only_about_ids_it_was_asked_about(implementation, session):
    """A batch read, and never a scan of everybody who happens to be rated."""

    port = implementation.build(session)
    asked = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)
    await _rated(session, mu=2.10, sigma=0.30, sport=Sport.PADEL)

    found = await port.estimates_for([asked], sport=Sport.PADEL)

    assert set(found) == {asked}


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_asking_about_nobody_answers_about_nobody(implementation, session):
    port = implementation.build(session)

    assert await port.estimates_for([], sport=Sport.PADEL) == {}


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_a_court_crosses_as_the_published_figures_in_one_sport(
    implementation, session
):
    """**The third read, and the shape the game's pairing needs.** Four seats in
    one sport, each with the figures a screen prints — the Level, the band's
    name, the range the engine rounded and the certainty — and nothing derived
    on the way out. A seat is not the matcher's twenty rows (that read carries
    the engine's currency) and not a record's one person (that one walks every
    sport), so neither existing read can stand in for it."""

    port = implementation.build(session)
    one = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)
    two = await _rated(session, mu=2.60, sigma=0.40, sport=Sport.PADEL)
    await _rated(session, mu=4.10, sigma=0.50, sport=Sport.SQUASH, player_id=one)

    found = await port.published_for([one, two], sport=Sport.PADEL)

    low, high = likely_range(2.60, 0.40)
    assert set(found) == {one, two}
    assert found[one].sport is Sport.PADEL
    assert found[one].mu == 3.20
    assert found[two].band_name == band_for(2.60).label
    assert found[two].confidence == confidence_percent(0.40)
    assert (found[two].range_low, found[two].range_high) == (
        round(low, 2),
        round(high, 2),
    )


@pytest.mark.parametrize("implementation", registered(RatedPlayerQuery))
async def test_a_court_read_leaves_the_unrated_seat_absent(implementation, session):
    """Absent, on the rule every read here applies: a seat whose person holds no
    rating in this sport is not in the answer, and nothing is invented for it."""

    port = implementation.build(session)
    rated = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)
    elsewhere = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.TENNIS)

    found = await port.published_for([rated, elsewhere, new_uuid()], sport=Sport.PADEL)

    assert set(found) == {rated}


@pytest.mark.parametrize("port", RATING_DEMANDS, ids=lambda port: port.__name__)
def test_every_published_read_has_something_answering_it(port):
    """A port nothing implements is a demand nothing runs against.

    **This is the test that stands under the parameterised ones.** A port whose
    register row is deleted does not turn its own contract tests red: an empty
    ``parametrize`` collects as *skipped*, and a skipped test is a test nobody is
    watching.
    """

    assert implementations_of(port)


@pytest.mark.parametrize(
    "implementation",
    RATING_IMPLEMENTATIONS,
    ids=[implementation.name for implementation in RATING_IMPLEMENTATIONS],
)
async def test_a_registered_implementation_answers_the_port_it_registered_against(
    implementation, session
):
    assert isinstance(implementation.build(session), implementation.port)

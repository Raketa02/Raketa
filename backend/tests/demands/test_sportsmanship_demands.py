"""What ``sportsmanship`` publishes outward, run against every implementation.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/sportsmanship_demands.py`` is enrolled here automatically, so a
second one either satisfies the demand or turns the build red.

**Every arrangement here is a card answered through this context's own
aggregate** — never an ``INSERT`` (``docs/adr/0029``) — because what this port
answers is a fold over rows the card wrote, and the two rules worth proving are
properties of those rows rather than of the arithmetic above them:

**The collapse.** *Only a rater's most recent stars about a person count* is the
primary key of ``sportsmanship_rating``, so a weekly partner contributes **one**
opinion however many evenings they play. It is asserted here rather than in a
unit test because the place it can fail is a database.

**The window is fifty people, not fifty ratings.** With the collapse in the key
those two only differ once fifty-one different people have said something, which
is exactly the arrangement below.

**And the subject's answer carries neither number.** ``band_for`` folds the same
window and returns three steps wide; a caller holding it cannot subtract, which
is ``docs/adr/0154``'s whole privacy argument made structural rather than
promised.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from app.bootstrap.composition import build_sportsmanship_ledger
from app.bootstrap.sportsmanship_demands import (
    SPORTSMANSHIP_DEMANDS,
    SPORTSMANSHIP_IMPLEMENTATIONS,
    implementations_of,
)
from app.kernel import Instant, instant
from app.modules.sportsmanship.domain.card import (
    SettledCourt,
    SportsmanshipCard,
    StarsGiven,
)
from app.modules.sportsmanship.domain.ports import PublishedSportsmanshipQuery
from app.modules.sportsmanship.domain.published import (
    RATER_WINDOW,
    SportsmanshipBand,
)

SUBJECT = uuid4()


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _at(**offset) -> Instant:
    """A moment that far behind now, so *most recent* has something to order."""

    return instant(datetime.now(timezone.utc) - timedelta(**offset))


async def _rated(
    session,
    *,
    rater: UUID,
    subject: UUID = SUBJECT,
    stars: int,
    at: Instant,
) -> None:
    """One rater answers one court, giving one person stars.

    Written through the card, because the card is what carries the collapse: a
    row inserted beside it would be this suite arranging the thing it is meant to
    be proving.
    """

    await build_sportsmanship_ledger(session).record(
        SportsmanshipCard.answered(
            court=SettledCourt(
                game_id=uuid4(),
                rater_id=rater,
                others=(subject,),
                played_at=at,
            ),
            given=[StarsGiven(subject_id=subject, stars=stars)],
            at=at,
        )
    )
    await session.commit()


# ---------------------------------------------------------------------------
# The register checks itself
# ---------------------------------------------------------------------------


def test_every_demand_has_at_least_one_implementation():
    """A port nothing signs is a port nothing runs against."""

    unanswered = [
        port.__name__ for port in SPORTSMANSHIP_DEMANDS if not implementations_of(port)
    ]

    assert unanswered == [], f"declared and unanswered: {unanswered}"


def test_every_registered_implementation_is_of_a_declared_demand():
    """A row for a port nobody declared is a row the suite would run blind."""

    stray = [
        implementation.name
        for implementation in SPORTSMANSHIP_IMPLEMENTATIONS
        if implementation.port not in SPORTSMANSHIP_DEMANDS
    ]

    assert stray == [], f"registered against no declared demand: {stray}"


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
def test_every_implementation_satisfies_the_protocol_it_registered_under(
    implementation, session
):
    assert isinstance(implementation.build(session), implementation.port)


# ---------------------------------------------------------------------------
# What other players said
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_one_rating_publishes_with_the_count_beside_it(implementation, session):
    """**No minimum.** The figure crosses from the very first rating, and the
    count is what keeps that honest: ``3,0 / 5 · 1 player`` reads as one
    person's opinion because it says so."""

    await _rated(session, rater=uuid4(), stars=3, at=_at(days=1))

    published = await implementation.build(session).published_for(SUBJECT)

    assert published is not None
    assert (published.average, published.raters) == (3.0, 1)


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_nobody_has_rated_them_is_an_absence_and_never_a_nought(
    implementation, session
):
    """Most people, and the record omits the whole zone rather than drawing a
    nought — nobody has been unpleasant who has never been asked about."""

    assert await implementation.build(session).published_for(uuid4()) is None


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_a_weekly_partner_contributes_one_opinion_and_not_ten(
    implementation, session
):
    """**The collapse, against a database.** Ten evenings with the same person
    leave one standing answer, so the count means *how many different people
    have an opinion* — and the average cannot drift towards what one regular
    partner thinks.

    The later card is the one that stands, which is the key's own reading of
    *what does this person currently think*.
    """

    partner = uuid4()
    for day, stars in enumerate((1, 1, 1, 1, 1, 1, 1, 1, 1, 5), start=1):
        await _rated(session, rater=partner, stars=stars, at=_at(days=20 - day))
    await _rated(session, rater=uuid4(), stars=3, at=_at(days=1))

    published = await implementation.build(session).published_for(SUBJECT)

    assert published is not None
    assert published.raters == 2
    assert published.average == 4.0


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_the_window_is_the_fifty_most_recent_people(implementation, session):
    """**Fifty raters, and the fifty-first drops out by being the oldest.**

    Fifty-one different people, the oldest of them alone in disagreeing: the
    figure is taken over the fifty who spoke most recently, so somebody can
    recover from a bad patch without the platform deciding which raters were
    wrong.
    """

    await _rated(session, rater=uuid4(), stars=1, at=_at(days=400))
    for day in range(RATER_WINDOW):
        await _rated(session, rater=uuid4(), stars=5, at=_at(days=day + 1))

    published = await implementation.build(session).published_for(SUBJECT)

    assert published is not None
    assert (published.average, published.raters) == (5.0, RATER_WINDOW)


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_nothing_is_trimmed_at_either_end(implementation, session):
    """**No outlier trimming of any kind.** Trimming is the platform deciding
    which raters were wrong, which is a larger claim than publishing the number
    — so the one star and the two fives are all in the mean."""

    for stars in (1, 5, 5):
        await _rated(session, rater=uuid4(), stars=stars, at=_at(days=1))

    published = await implementation.build(session).published_for(SUBJECT)

    assert published is not None
    assert (published.average, published.raters) == (3.7, 3)


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_a_figure_is_only_about_the_person_it_was_given_about(
    implementation, session
):
    """Stars given to somebody else are not in this person's window, which is
    the one thing a ``subject_id`` filter could get wrong invisibly."""

    somebody_else = uuid4()
    await _rated(session, rater=uuid4(), subject=somebody_else, stars=1, at=_at(days=1))
    await _rated(session, rater=uuid4(), stars=5, at=_at(days=1))

    published = await implementation.build(session).published_for(SUBJECT)

    assert published is not None
    assert (published.average, published.raters) == (5.0, 1)


# ---------------------------------------------------------------------------
# What the subject is told about themselves
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_the_subject_is_answered_with_a_band_and_nothing_else(
    implementation, session
):
    """**The method the subject's sheet calls cannot say the figure.** What
    comes back is one of three steps: no average to subtract from, no count to
    subtract with, and therefore no answer identifiable by the one person who
    must never see it."""

    for stars in (5, 4, 5):
        await _rated(session, rater=uuid4(), stars=stars, at=_at(days=1))

    band = await implementation.build(session).band_for(SUBJECT)

    assert band is SportsmanshipBand.GOOD
    assert not hasattr(band, "average")
    assert not hasattr(band, "raters")


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_the_band_and_the_figure_are_folded_from_one_window(
    implementation, session
):
    """One record read at two resolutions. A band that disagreed with the figure
    a reader is shown would mean two folds, and the second one would be the copy
    that got believed."""

    for stars in (2, 3, 2):
        await _rated(session, rater=uuid4(), stars=stars, at=_at(days=1))

    query = implementation.build(session)
    published = await query.published_for(SUBJECT)

    assert published is not None
    assert published.average < 3.0
    assert await query.band_for(SUBJECT) is SportsmanshipBand.POOR


@pytest.mark.parametrize("implementation", registered(PublishedSportsmanshipQuery))
async def test_a_subject_nobody_has_rated_has_no_band_either(implementation, session):
    """The same absence the figure spells, so the sheet omits one field or the
    other and never draws an empty one."""

    assert await implementation.build(session).band_for(uuid4()) is None

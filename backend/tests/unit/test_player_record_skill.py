"""The skill card's two borrowed facts, and the word each of them is renamed to.

``player_record`` declares its own types rather than reusing another context's
(``docs/adr/0159``), which puts two enums with the same two strings a few
directories apart — the same deliberate duplication ``OnCourtVerdict`` carries
beside ``PhotoReviewDecision``, and the same risk: **two spellings that drift are
worse than an import**, because a client reading a search card and a record would
be handed two words for one fact. So the agreement is asserted, in both
directions.

The two adapters are here too, because each of them makes exactly one decision
worth pinning and neither is visible over HTTP:

**``counted_games`` is the games that moved this Level**, and not ``games``' count
of how many counted games somebody has played. The second is over every sport and
counts an evening two people never agreed a score for; the skill card claims to
say what a certainty *rests on*, and the honest answer to that is the results that
actually moved it.

**A run is outcomes and never moments.** ``CountedResult`` carries when a game was
played, and nothing that crosses this seam does — activity recency is a standing
refusal on this platform at every granularity, and a type that cannot carry a
moment is the cheapest way to keep it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Collection, Mapping
from uuid import UUID, uuid4

from app.kernel import Instant, Sport, instant
from app.modules.games.domain.ports import CountedResult
from app.modules.games.domain.results import Outcome
from app.modules.player_record.domain.record import GameOutcome
from app.modules.player_record.infrastructure.games_subject_form import (
    GamesSubjectForm,
)
from app.modules.player_record.infrastructure.rating_subject_ratings import (
    RatingSubjectRatings,
)
from app.modules.rating.domain.ports import RatedSport

NOW: Instant = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))
SUBJECT = uuid4()


def test_the_two_outcome_vocabularies_agree_on_the_wire():
    """Both directions, so a value added to either side is red rather than a
    third answer arriving on one surface and not the other."""

    assert {one.value for one in GameOutcome} == {one.value for one in Outcome}


class PublishedRatings:
    def __init__(self, held: Mapping[Sport, RatedSport]) -> None:
        self.held = held
        self.asked: list[UUID] = []

    async def estimates_for(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, object]:
        raise AssertionError("a record reads one player and every sport")

    async def ratings_of(self, player_id: UUID) -> Mapping[Sport, RatedSport]:
        self.asked.append(player_id)
        return self.held


class History:
    def __init__(self, results: tuple[CountedResult, ...] = ()) -> None:
        self.results = results
        self.asked: list[tuple[UUID, Sport]] = []

    async def recent_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[CountedResult, ...]:
        self.asked.append((player_id, sport))
        return self.results


def a_published_rating(**overrides) -> RatedSport:
    return RatedSport(
        **{
            "sport": Sport.PADEL,
            "mu": 3.25,
            "confidence": 77,
            "range_low": 2.9,
            "range_high": 3.6,
            "band_name": "Established",
            "counted_results": 21,
            **overrides,
        }
    )


async def test_a_rating_crosses_with_its_figures_and_nothing_recomputed():
    published = PublishedRatings({Sport.PADEL: a_published_rating()})

    held = await RatingSubjectRatings(published).ratings_of(SUBJECT)

    (rating,) = held.values()
    assert rating.sport is Sport.PADEL
    assert rating.level == 3.25
    assert rating.band == "Established"
    assert rating.confidence == 77
    assert rating.likely_range.low == 2.9 and rating.likely_range.high == 3.6
    assert published.asked == [SUBJECT]


async def test_counted_games_is_what_moved_this_level_and_not_what_they_played():
    """The number this card claims a certainty rests on, taken off the same
    stream as the Level beside it so the two move together
    (``docs/adr/0139``)."""

    published = PublishedRatings({Sport.PADEL: a_published_rating(counted_results=3)})

    held = await RatingSubjectRatings(published).ratings_of(SUBJECT)

    assert held[Sport.PADEL].counted_games == 3


async def test_a_rating_from_the_questionnaire_alone_counts_nought_games():
    """**A real answer and not an absence.** A Level no game has tested yet is
    exactly what `0` says, and the confidence beside it is what makes that
    readable."""

    published = PublishedRatings({Sport.PADEL: a_published_rating(counted_results=0)})

    held = await RatingSubjectRatings(published).ratings_of(SUBJECT)

    assert held[Sport.PADEL].counted_games == 0


async def test_a_player_rated_in_nothing_holds_nothing():
    assert await RatingSubjectRatings(PublishedRatings({})).ratings_of(SUBJECT) == {}


def a_result(outcome: Outcome, *, sport: Sport = Sport.PADEL) -> CountedResult:
    return CountedResult(
        game_id=uuid4(), sport=sport, outcome=outcome, played_at=NOW
    )


async def test_a_run_is_outcomes_in_the_order_it_was_given():
    history = History((a_result(Outcome.WIN), a_result(Outcome.LOSS)))

    run = await GamesSubjectForm(history).last_results_in(
        SUBJECT, sport=Sport.PADEL, now=NOW
    )

    assert run == (GameOutcome.WIN, GameOutcome.LOSS)
    assert history.asked == [(SUBJECT, Sport.PADEL)]


async def test_a_run_carries_no_moment_at_any_granularity():
    """The seam is where activity recency would arrive, and the type is what
    stops it: there is nowhere on ``GameOutcome`` for a date to be added."""

    run = await GamesSubjectForm(History((a_result(Outcome.WIN),))).last_results_in(
        SUBJECT, sport=Sport.PADEL, now=NOW
    )

    assert all(isinstance(one, GameOutcome) for one in run)


async def test_a_player_with_no_counted_result_in_that_sport_has_an_empty_run():
    """Never padded, and never a placeholder square: the client draws the gap."""

    assert (
        await GamesSubjectForm(History()).last_results_in(
            SUBJECT, sport=Sport.SQUASH, now=NOW
        )
        == ()
    )

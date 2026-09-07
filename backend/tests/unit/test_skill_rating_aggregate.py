"""The SkillRating aggregate — its two transitions, and what a replay rebuilds.

Initialisation was its only one until ``docs/adr/0139``, which is exactly why
these tests mattered before there was a second: everything the result-update rule
appends to this stream lands on state rebuilt by ``from_history``, and the rule
that a replayed aggregate records nothing is what keeps a read from writing
through.

The result is built here rather than run through the engine. What is under test is
the aggregate's carrying of a result, not the engine's producing of one — and a
hand-built result can hold values a real run would not, which is how a field
quietly dropped on the way to the event gets caught.
"""

from __future__ import annotations

import pytest

from app.engines.assessment import (
    CALIBRATION_PRIORITY_ELEVATED,
    CALIBRATION_PRIORITY_STANDARD,
    AssessmentResult,
    BandView,
    ConfidenceReason,
)
from app.kernel import Sport
from app.modules.rating.domain.events import RatingInitialised
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import utc

RATED_AT = utc(2026, 8, 14)
#: One player and one assessment, for the block below. Named constants rather
#: than fresh uuids per test, because a replay has to be handed a stream whose
#: opening event names the same player as the moves after it.
PLAYER = new_uuid()
SOURCE = new_uuid()


def a_result(
    *,
    calibration_priority: str = CALIBRATION_PRIORITY_STANDARD,
    confidence_reason: ConfidenceReason | None = None,
) -> AssessmentResult:
    return AssessmentResult(
        mu=2.85,
        sigma=0.42,
        confidence=27,
        range_low=2.01,
        range_high=3.69,
        band=BandView(name="Intermediate", lower=2.5, upper=3.4),
        status="provisional",
        questions_asked=7,
        engine_version="racketskill-v3",
        calibration_priority=calibration_priority,
        confidence_reason=confidence_reason,
    )


def initialised(
    *,
    calibration_priority: str = CALIBRATION_PRIORITY_STANDARD,
    confidence_reason: ConfidenceReason | None = None,
) -> SkillRating:
    player_id = new_uuid()
    return SkillRating.initialise(
        rating_id=skill_rating_id(player_id, Sport.PADEL),
        player_id=player_id,
        sport=Sport.PADEL,
        result=a_result(
            calibration_priority=calibration_priority,
            confidence_reason=confidence_reason,
        ),
        source_assessment_id=new_uuid(),
        occurred_at=RATED_AT,
    )


def test_initialising_carries_every_number_the_result_holds() -> None:
    rating = initialised()

    result = a_result()
    assert rating.mu == result.mu
    assert rating.sigma == result.sigma
    assert rating.confidence == result.confidence
    assert rating.range_low == result.range_low
    assert rating.range_high == result.range_high
    # The band's own boundaries travel on the rating, so a screen never reads
    # them from a second source.
    assert rating.band_name == result.band.name
    assert rating.band_lower == result.band.lower
    assert rating.band_upper == result.band.upper
    assert rating.status == result.status
    assert rating.engine_version == result.engine_version
    assert rating.sport is Sport.PADEL
    assert rating.updated_at == RATED_AT


def test_the_rating_is_keyed_by_the_player_and_the_sport() -> None:
    # A deterministic id means the pair has exactly one stream, found without a
    # lookup table.
    player_id = new_uuid()
    rating = SkillRating.initialise(
        rating_id=skill_rating_id(player_id, Sport.TENNIS),
        player_id=player_id,
        sport=Sport.TENNIS,
        result=a_result(),
        source_assessment_id=new_uuid(),
        occurred_at=RATED_AT,
    )

    assert rating.id == skill_rating_id(player_id, Sport.TENNIS)
    assert rating.id != skill_rating_id(player_id, Sport.PADEL)
    assert rating.player_id == player_id


def test_initialising_records_one_event_and_moves_the_version() -> None:
    rating = initialised()

    assert rating.version == 1
    pending = rating.pull_events()
    assert [type(event) for event in pending] == [RatingInitialised]


def test_pulling_events_twice_yields_nothing_the_second_time() -> None:
    # What makes ``save`` a no-op on an aggregate that decided nothing, and what
    # stops a second save in one request writing the same event again.
    rating = initialised()
    rating.pull_events()

    assert rating.pull_events() == []


def test_the_calibration_priority_and_the_confidence_reason_travel_with_it() -> None:
    # Both are facts about the rating, not about the assessment, so they follow it
    # into the match-update engine rather than living only on the run.
    reason = ConfidenceReason(
        key="answers-disagreed", sentence="Your answers pulled apart."
    )
    rating = initialised(
        calibration_priority=CALIBRATION_PRIORITY_ELEVATED,
        confidence_reason=reason,
    )

    assert rating.calibration_priority == CALIBRATION_PRIORITY_ELEVATED
    # The key, not the sentence: the sentence is server-authored copy that changes
    # without a client release, and a stored copy of it would be a second one.
    assert rating.confidence_reason_key == "answers-disagreed"


def test_a_result_with_no_confidence_reason_stores_none() -> None:
    rating = initialised()

    assert rating.confidence_reason_key is None
    assert rating.calibration_priority == CALIBRATION_PRIORITY_STANDARD


def test_replaying_the_stream_reproduces_the_rating_and_records_nothing() -> None:
    written = initialised(
        calibration_priority=CALIBRATION_PRIORITY_ELEVATED,
        confidence_reason=ConfidenceReason(
            key="thin-evidence", sentence="Not much yet."
        ),
    )
    history = written.pull_events()

    replayed = SkillRating.from_history(history)

    assert replayed == written
    assert replayed.version == 1
    # A read must never write through: replay applies, it does not record.
    assert replayed.pull_events() == []


def test_an_event_this_aggregate_does_not_know_is_refused() -> None:
    # Silence here would be a rating replayed from a stream it does not
    # understand, reporting numbers from the events it happened to recognise.
    class NotARatingEvent:
        pass

    with pytest.raises(TypeError):
        SkillRating.from_history([NotARatingEvent()])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# The second transition — one confirmed result
# ---------------------------------------------------------------------------


def a_move(*, won: bool = True, results_so_far: int = 0):
    from app.engines.racketskill.core import SkillEstimate
    from app.engines.racketskill.update_v1 import rating_after

    return rating_after(
        player=SkillEstimate(mu=3.00, sigma=0.84),
        opposition=SkillEstimate(mu=3.00, sigma=0.20),
        won=won,
        results_so_far=results_so_far,
    )


def a_moved_rating() -> SkillRating:
    rating = SkillRating.initialise(
        rating_id=skill_rating_id(PLAYER, Sport.PADEL),
        player_id=PLAYER,
        sport=Sport.PADEL,
        result=a_result(),
        source_assessment_id=SOURCE,
        occurred_at=RATED_AT,
    )
    rating.pull_events()
    return rating


def _move(rating: SkillRating, game_id, **overrides) -> None:
    from app.engines.racketskill.core import SkillEstimate

    rating.move_on_result(
        game_id=game_id,
        moved=overrides.pop("moved", a_move()),
        won=overrides.pop("won", True),
        opposition=SkillEstimate(mu=3.00, sigma=0.20),
        information_share=1.0,
        occurred_at=utc(2026, 8, 20),
    )


def test_a_confirmed_result_moves_the_level_and_records_the_game():
    rating = a_moved_rating()
    game = new_uuid()

    _move(rating, game)

    assert rating.mu > 3.00
    assert rating.applied_games == (game,)
    assert rating.counted_results == 1
    assert [type(event).__name__ for event in rating.pull_events()] == [
        "RatingMovedOnResult"
    ]


def test_the_same_game_twice_records_nothing_the_second_time():
    """**The whole of the catch-up's idempotency**, and it lives here.

    Nothing announces a confirmation, so results are read forward and re-read; a
    second sighting is the ordinary case rather than an error, and answering it
    with a refusal would make an at-least-once loop something a caller had to
    guard.
    """

    rating = a_moved_rating()
    game = new_uuid()

    _move(rating, game)
    moved_to = rating.mu
    rating.pull_events()
    _move(rating, game)

    assert rating.pull_events() == []
    assert rating.mu == moved_to
    assert rating.applied_games == (game,)


def test_the_engine_version_moves_with_the_number_it_produced():
    """A Level tested by results was last written by the result-update rule."""

    rating = a_moved_rating()
    onboarding = rating.engine_version

    _move(rating, new_uuid())

    assert rating.engine_version != onboarding

    assert rating.engine_version == "racketskill-result-update-v1"


def test_a_replay_rebuilds_every_move_and_records_nothing():
    rating = a_moved_rating()
    first, second = new_uuid(), new_uuid()
    _move(rating, first)
    _move(rating, second, moved=a_move(won=False, results_so_far=1))

    stream = [
        RatingInitialised(
            rating_id=skill_rating_id(PLAYER, Sport.PADEL),
            player_id=PLAYER,
            sport=Sport.PADEL.value,
            mu=a_result().mu,
            sigma=a_result().sigma,
            confidence=a_result().confidence,
            range_low=a_result().range_low,
            range_high=a_result().range_high,
            band_name=a_result().band.name,
            band_lower=a_result().band.lower,
            band_upper=a_result().band.upper,
            status=a_result().status,
            engine_version=a_result().engine_version,
            source_assessment_id=SOURCE,
            occurred_at=RATED_AT,
        ),
        *rating.pull_events(),
    ]

    replayed = SkillRating.from_history(stream)

    assert replayed.pull_events() == []
    assert replayed.applied_games == (first, second)
    assert replayed.mu == rating.mu
    assert replayed.sigma == rating.sigma
    assert replayed.status == rating.status
    assert replayed.updated_at == rating.updated_at

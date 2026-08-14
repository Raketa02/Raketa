"""The SkillRating aggregate — named by no unit test until now.

Initialisation is its only transition today, which is exactly why these tests
matter: everything the match-update engine will later append to this stream has to
land on state rebuilt by ``from_history``, and the rule that a replayed aggregate
records nothing is what keeps a read from writing through.

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

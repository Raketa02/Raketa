"""The rating context's stream as a **durable** contract.

``AssessmentCompleted`` gained its stop rationale as appended fields with
defaults rather than as a new catalog version, which is only sound if a row
written before them still decodes. ``AnswerRevised`` is a whole new event, and
what it needs pinning is its *name*: the transcript is a projection that
truncates when it replays one, so a row filed under a name nothing decodes is a
run whose replayed answers are not the answers the engine consumed.

Both are asserted against the real catalog registration — the codec the
application runs — because the name and version a row is filed under are what
history is recorded as, not the Python class name.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from app.application.events.envelope import SerializedEventEnvelope
from app.modules.rating.domain.events import AnswerRevised, AssessmentCompleted
from tests.unit.fake_event_store import rating_event_codec

NOW = datetime(2026, 8, 14, tzinfo=timezone.utc)

COMPLETED = AssessmentCompleted(
    assessment_id=uuid4(),
    mu=2.84,
    sigma=0.7412,
    confidence=27,
    range_low=2.1,
    range_high=3.58,
    band_name="Developing",
    band_lower=2.0,
    band_upper=3.0,
    status="Initial Estimate",
    questions_asked=6,
    engine_version="racketskill-fusion-v3",
    occurred_at=NOW,
    stop_reason="marginal-value-below-threshold",
    stop_value=0.0138,
)


def _envelope(payload: dict[str, object]) -> SerializedEventEnvelope:
    return SerializedEventEnvelope(
        id=uuid4(),
        event_type="rating.assessment_completed",
        schema_version=1,
        payload=payload,
        occurred_at=NOW,
    )


def test_the_stop_reason_and_value_round_trip() -> None:
    codec = rating_event_codec()

    encoded = codec.encode(COMPLETED)

    # The name and version are unchanged: appended defaults, not a new contract.
    assert encoded.event_type == "rating.assessment_completed"
    assert encoded.schema_version == 1
    assert encoded.payload["stop_reason"] == "marginal-value-below-threshold"
    assert encoded.payload["stop_value"] == 0.0138
    assert codec.decode(_envelope(encoded.payload)) == COMPLETED


def test_a_payload_written_before_the_stop_fields_still_decodes() -> None:
    # An assessment completed before this change, as its row actually looks: the
    # same event type and version, with the two keys simply absent. Derived by
    # dropping them from a current payload rather than typed in, so the rest of
    # the row cannot drift away from what the encoder really writes.
    codec = rating_event_codec()
    payload = dict(codec.encode(COMPLETED).payload)
    del payload["stop_reason"]
    del payload["stop_value"]

    decoded = codec.decode(_envelope(payload))

    assert decoded == replace(COMPLETED, stop_reason=None, stop_value=None)


def test_a_stop_value_of_zero_survives_as_zero() -> None:
    # The beginner fast path stops on a value of exactly 0.0, which is also what
    # a missing field decodes to under any "falsy means absent" reading. They are
    # different facts — *stopped with nothing left to gain* against *completed
    # before stops were recorded* — so the codec must keep them apart.
    codec = rating_event_codec()
    beginner = replace(COMPLETED, stop_reason="beginner-fast-path", stop_value=0.0)

    decoded = codec.decode(_envelope(codec.encode(beginner).payload))

    assert isinstance(decoded, AssessmentCompleted)
    assert decoded.stop_reason == "beginner-fast-path"
    assert decoded.stop_value == 0.0


# --- The revision, as a new event rather than an amended one --------------------


def test_a_revision_is_filed_under_its_own_name_and_first_version() -> None:
    codec = rating_event_codec()
    revision = AnswerRevised(
        assessment_id=uuid4(),
        question_id="opening.regularity",
        option_id="frequent",
        occurred_at=NOW,
    )

    encoded = codec.encode(revision)

    assert encoded.event_type == "rating.answer_revised"
    assert encoded.schema_version == 1
    assert (
        codec.decode(
            SerializedEventEnvelope(
                id=uuid4(),
                event_type=encoded.event_type,
                schema_version=encoded.schema_version,
                payload=encoded.payload,
                occurred_at=NOW,
            )
        )
        == revision
    )


def test_a_revision_records_what_was_chosen_and_not_what_it_replaced() -> None:
    # The option it superseded and the answers it discarded are both already on
    # the stream, in the events before it. Writing them here as well would be the
    # same facts in two places and so two places for them to disagree; a reader
    # that wants "changed from what" replays the prefix.
    codec = rating_event_codec()
    payload = codec.encode(
        AnswerRevised(
            assessment_id=uuid4(),
            question_id="opening.regularity",
            option_id="frequent",
            occurred_at=NOW,
        )
    ).payload

    assert set(payload) == {"assessment_id", "question_id", "option_id", "occurred_at"}

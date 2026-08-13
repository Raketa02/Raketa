"""The Assessment aggregate — event-sourced.

Its stream *is* the transcript the engine consumes: replaying the events yields
exactly the ordered answers the engine saw. The aggregate holds no engine logic;
it records what was asked and answered and guards the one invariant that makes
retries safe — an answer is accepted only for the question currently outstanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable, Optional
from uuid import UUID

from app.engines.assessment import (
    AnsweredQuestion,
    AssessmentResult,
    BandView,
    Transcript,
)
from app.kernel import Sport
from app.modules.rating.domain.errors import (
    AssessmentAlreadyFinished,
    QuestionNotOutstanding,
)
from app.modules.rating.domain.events import (
    AnswerSubmitted,
    AssessmentAbandoned,
    AssessmentCompleted,
    AssessmentStarted,
    QuestionAsked,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


class AssessmentStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class Assessment:
    id: UUID
    player_id: UUID
    sport: Sport
    engine_version: str
    status: AssessmentStatus = AssessmentStatus.IN_PROGRESS
    version: int = 0
    _answered: list[AnsweredQuestion] = field(default_factory=list, repr=False)
    _outstanding_question_id: Optional[str] = field(default=None, repr=False)
    _last_answered_question_id: Optional[str] = field(default=None, repr=False)
    _result: Optional[AssessmentResult] = field(default=None, repr=False)
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # --- reconstruction ---------------------------------------------------

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Assessment":
        assessment = cls._empty()
        for event in events:
            assessment._apply(event)
        return assessment

    @classmethod
    def _empty(cls) -> "Assessment":
        assessment = cls.__new__(cls)
        assessment.status = AssessmentStatus.IN_PROGRESS
        assessment.version = 0
        assessment._answered = []
        assessment._outstanding_question_id = None
        assessment._last_answered_question_id = None
        assessment._result = None
        assessment._events = EventRecorder()
        return assessment

    # --- factory + commands ----------------------------------------------

    @classmethod
    def start(
        cls,
        *,
        assessment_id: UUID,
        player_id: UUID,
        sport: Sport,
        engine_version: str,
        occurred_at: datetime,
    ) -> "Assessment":
        assessment = cls._empty()
        assessment._record_that(
            AssessmentStarted(
                assessment_id=assessment_id,
                player_id=player_id,
                sport=sport.value,
                engine_version=engine_version,
                occurred_at=occurred_at,
            )
        )
        return assessment

    def ask(
        self,
        *,
        question_id: str,
        reason: str,
        mu: float,
        sigma: float,
        occurred_at: datetime,
    ) -> None:
        self._record_that(
            QuestionAsked(
                assessment_id=self.id,
                question_id=question_id,
                reason=reason,
                mu=mu,
                sigma=sigma,
                occurred_at=occurred_at,
            )
        )

    def answer(
        self, *, question_id: str, option_id: str, occurred_at: datetime
    ) -> None:
        if (
            self.status is not AssessmentStatus.IN_PROGRESS
            or question_id != self._outstanding_question_id
        ):
            raise QuestionNotOutstanding()
        self._record_that(
            AnswerSubmitted(
                assessment_id=self.id,
                question_id=question_id,
                option_id=option_id,
                occurred_at=occurred_at,
            )
        )

    def abandon(self, *, occurred_at: datetime) -> None:
        """End an in-progress assessment, freeing the sport to be started again.

        Abandoning an already-abandoned assessment is a no-op so a retried
        request cannot fail; a finished (completed) assessment cannot be
        abandoned — its rating already exists.
        """
        if self.status is AssessmentStatus.ABANDONED:
            return
        if self.status is not AssessmentStatus.IN_PROGRESS:
            raise AssessmentAlreadyFinished()
        self._record_that(
            AssessmentAbandoned(
                assessment_id=self.id,
                occurred_at=occurred_at,
            )
        )

    def complete(self, *, result: AssessmentResult, occurred_at: datetime) -> None:
        self._record_that(
            AssessmentCompleted(
                assessment_id=self.id,
                mu=result.mu,
                sigma=result.sigma,
                confidence=result.confidence,
                range_low=result.range_low,
                range_high=result.range_high,
                band_name=result.band.name,
                band_lower=result.band.lower,
                band_upper=result.band.upper,
                status=result.status,
                questions_asked=result.questions_asked,
                engine_version=result.engine_version,
                occurred_at=occurred_at,
                calibration_priority=result.calibration_priority,
                confidence_reason_key=(
                    result.confidence_reason.key
                    if result.confidence_reason is not None
                    else None
                ),
            )
        )

    # --- read model -------------------------------------------------------

    @property
    def transcript(self) -> Transcript:
        return tuple(self._answered)

    @property
    def outstanding_question_id(self) -> Optional[str]:
        return self._outstanding_question_id

    @property
    def last_answered_question_id(self) -> Optional[str]:
        return self._last_answered_question_id

    @property
    def is_completed(self) -> bool:
        return self.status is AssessmentStatus.COMPLETED

    @property
    def is_abandoned(self) -> bool:
        return self.status is AssessmentStatus.ABANDONED

    @property
    def is_in_progress(self) -> bool:
        return self.status is AssessmentStatus.IN_PROGRESS

    @property
    def result(self) -> Optional[AssessmentResult]:
        """The result as it was **recorded**: the numbers, and nothing derived.

        The explanation — the factor rows and the confidence sentence — is
        reproduced from the transcript by the engine that produced them rather
        than stored a second time, exactly as the outstanding question is. See
        ``application/assessment_view.completed_result``, which is what the
        client is served.
        """

        return self._result

    # --- event application ------------------------------------------------

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, AssessmentStarted):
            self.id = event.assessment_id
            self.player_id = event.player_id
            self.sport = Sport(event.sport)
            self.engine_version = event.engine_version
            self.status = AssessmentStatus.IN_PROGRESS
            self.version += 1
            return
        if isinstance(event, QuestionAsked):
            self._outstanding_question_id = event.question_id
            self.version += 1
            return
        if isinstance(event, AnswerSubmitted):
            self._answered.append(
                AnsweredQuestion(
                    question_id=event.question_id, option_id=event.option_id
                )
            )
            self._last_answered_question_id = event.question_id
            self._outstanding_question_id = None
            self.version += 1
            return
        if isinstance(event, AssessmentCompleted):
            self.status = AssessmentStatus.COMPLETED
            self._result = AssessmentResult(
                mu=event.mu,
                sigma=event.sigma,
                confidence=event.confidence,
                range_low=event.range_low,
                range_high=event.range_high,
                band=BandView(
                    name=event.band_name,
                    lower=event.band_lower,
                    upper=event.band_upper,
                ),
                status=event.status,
                questions_asked=event.questions_asked,
                engine_version=event.engine_version,
                calibration_priority=event.calibration_priority,
            )
            self.version += 1
            return
        if isinstance(event, AssessmentAbandoned):
            self.status = AssessmentStatus.ABANDONED
            self._outstanding_question_id = None
            self.version += 1
            return
        raise TypeError(f"Unsupported assessment event {event!r}")

"""The Assessment aggregate — event-sourced.

Replaying its stream yields exactly the ordered answers the engine saw. The
aggregate holds no engine logic; it records what was asked and answered and
guards the two invariants that make retries safe — an answer is accepted only for
the question currently outstanding, and an answer is *changed* only for a question
the transcript already holds.

**The stream is append-only; the transcript is a projection over it.** A revision
appends an ``AnswerRevised`` and nothing is deleted, but replaying one truncates
the transcript at that question: every answer after it was pitched at a difficulty
chosen from the estimate as it then stood, so an answer that outlived a change to
an earlier one would mean something the player never said (``docs/adr/0020``).
A revision therefore shortens the past; it never edits it.
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
    Complete,
    Transcript,
)
from app.kernel import Sport
from app.modules.rating.domain.errors import (
    AssessmentAlreadyFinished,
    QuestionNotOutstanding,
)
from app.modules.rating.domain.events import (
    AnswerRevised,
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
    _stop_reason: Optional[str] = field(default=None, repr=False)
    _stop_value: Optional[float] = field(default=None, repr=False)
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
        assessment._stop_reason = None
        assessment._stop_value = None
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

    def revise(
        self, *, question_id: str, option_id: str, occurred_at: datetime
    ) -> None:
        """Change an answer already given, discarding every answer after it.

        Guarded exactly as ``answer`` is, on the other side of the transcript: an
        answer can be changed only while the run is in progress and only for a
        question the transcript already holds. A question that was never answered
        is not revisable, and reaching here with one means the caller confused a
        revision with an answer.

        **Re-selecting the option already recorded records nothing**, the same
        no-op shape ``abandon`` takes on an already-abandoned run. Changing your
        mind and changing it back is not a decision the stream needs to hold, and
        a revision event that revised nothing would truncate the transcript at
        that question for no reason — discarding later answers the player never
        asked to lose.
        """

        recorded = self.recorded_option(question_id)
        if self.status is not AssessmentStatus.IN_PROGRESS or recorded is None:
            raise QuestionNotOutstanding()
        if recorded == option_id:
            return
        self._record_that(
            AnswerRevised(
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

    def complete(
        self, *, result: AssessmentResult, stop: Complete, occurred_at: datetime
    ) -> None:
        """Record the finalised numbers, and why the questionnaire stopped.

        The stop arrives as the engine's own step rather than as two loose
        arguments, so a reason cannot be recorded beside a value that did not
        cause it — the same reason the result arrives whole.
        """

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
                stop_reason=stop.reason,
                stop_value=stop.value,
            )
        )

    # --- read model -------------------------------------------------------

    @property
    def transcript(self) -> Transcript:
        return tuple(self._answered)

    def recorded_option(self, question_id: str) -> Optional[str]:
        """Which option this question is answered with, or ``None`` if it is not.

        The transcript holds each question at most once — the engine never asks
        one twice, and a revision truncates rather than appending a second entry
        — so *the* recorded option is a well-formed question to ask of it.

        This is what separates the three things a submission can be: an answer to
        the outstanding question (no recorded option), a revision (a different
        one recorded), or a replay of an answer already given (the same one).
        """

        position = self._position_of(question_id)
        return None if position is None else self._answered[position].option_id

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

    @property
    def stop_reason(self) -> Optional[str]:
        """Why the questionnaire stopped asking, as the engine's stable key.

        On a completed run ``None`` means one thing and permanently — *this run
        was completed before stops were recorded* — and never "we do not know".
        Every completion since carries one, so the absence dates a row rather
        than describing it.

        Nothing serves this to a player. It is an engine diagnostic: what a
        training projection reads to learn why a question was *never* asked, and
        what would catch the hard-ceiling stop firing when the engine's own
        sequence says it cannot.
        """

        return self._stop_reason

    @property
    def stop_value(self) -> Optional[float]:
        """The number that drove the stop — the marginal gain that fell below
        threshold, the ceiling that was reached. Absent under the same rule as
        ``stop_reason``, and absent together with it."""

        return self._stop_value

    # --- event application ------------------------------------------------

    def _position_of(self, question_id: str) -> Optional[int]:
        for position, entry in enumerate(self._answered):
            if entry.question_id == question_id:
                return position
        return None

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
        if isinstance(event, AnswerRevised):
            # The one place the transcript shortens. The event stays on the
            # stream; the *projection* truncates at the revised question and puts
            # the new option there, which is what makes the replayed transcript
            # the one the engine consumed rather than a merge of two runs.
            position = self._position_of(event.question_id)
            if position is None:
                raise ValueError(
                    f"Revision of unanswered question {event.question_id!r} on "
                    f"assessment {event.assessment_id}"
                )
            self._answered[position:] = [
                AnsweredQuestion(
                    question_id=event.question_id, option_id=event.option_id
                )
            ]
            self._last_answered_question_id = event.question_id
            # The outstanding question was chosen from the estimate as it stood
            # before the change, so it is no longer the question to ask; the
            # caller asks the engine what this transcript wants next.
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
            self._stop_reason = event.stop_reason
            self._stop_value = event.stop_value
            self.version += 1
            return
        if isinstance(event, AssessmentAbandoned):
            self.status = AssessmentStatus.ABANDONED
            self._outstanding_question_id = None
            self.version += 1
            return
        raise TypeError(f"Unsupported assessment event {event!r}")

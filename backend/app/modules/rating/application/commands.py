"""Commands and the step view the rating use cases speak in."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.engines.assessment import AssessmentResult, Question
from app.kernel import Sport


@dataclass(frozen=True)
class CreateAssessmentCommand:
    player_id: UUID
    sport: Sport


@dataclass(frozen=True)
class SubmitAnswerCommand:
    player_id: UUID
    assessment_id: UUID
    question_id: str
    option_id: str


@dataclass(frozen=True)
class GetAssessmentQuery:
    player_id: UUID
    assessment_id: UUID


@dataclass(frozen=True)
class FindInProgressQuery:
    player_id: UUID
    sport: Sport


@dataclass(frozen=True)
class ListInProgressQuery:
    """Which of this player's runs are unfinished — the question, not per sport.

    ``FindInProgressQuery`` asks it of one sport, which is what a client resuming
    a sport it has already chosen wants. This asks it of the player, which is
    what the entry gate wants, and what it previously had to spell as one request
    per sport.
    """

    player_id: UUID


@dataclass(frozen=True)
class InProgressAssessmentView:
    """One unfinished run, as much of it as a router needs: which, and what of.

    Deliberately not a step. The outstanding question is reproduced by running
    the engine over the transcript, and a caller deciding *where to send the
    player* does not render it — it re-reads the run it routes to. Putting it
    here would make the common answer, an empty collection, the only cheap one.
    """

    assessment_id: UUID
    sport: Sport


@dataclass(frozen=True)
class AbandonAssessmentCommand:
    player_id: UUID
    assessment_id: UUID


@dataclass(frozen=True)
class ListRatingsQuery:
    player_id: UUID


@dataclass(frozen=True)
class AssessmentStep:
    """The server-driven step: the current question, or the final result.

    Exactly one of ``question`` / ``result`` is set. The client holds no flow
    state — this mutation response *is* the current state of the assessment.

    ``questions_asked`` is how many answers are already behind the run, which is
    what lets a resumed run report the position it is really at. It is required
    rather than optional so that no step can be built without it: see
    ``assessment_view.questions_asked`` for what it counts and what it does not.
    """

    assessment_id: UUID
    status: str
    questions_asked: int
    question: Question | None
    result: AssessmentResult | None


@dataclass(frozen=True)
class AssessmentStart:
    """A step, and whether this call is what opened the run it describes.

    Starting is idempotent per player and sport, so the step alone cannot say
    whether a run was created or an open one was handed back. The flag is not a
    fact about the assessment — it is a fact about *this call* — which is why it
    travels beside the step rather than on it, and why presentation spends it on
    a status code rather than putting it on the wire.
    """

    step: AssessmentStep
    created: bool

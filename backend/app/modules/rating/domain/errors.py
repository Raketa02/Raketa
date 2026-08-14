"""Rating-context errors, rendered as structured JSON over HTTP.

Each carries its own wire code. The three 409s are the reason that matters: they
arrive on the same status from the same endpoint family — a double-tapped
confirm, the same assessment resumed on a second device, a sport already rated —
and they ask the client for opposite recoveries.
"""

from __future__ import annotations

from app.core.exception_handlers import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class AssessmentNotFound(NotFoundError):
    """No assessment with this id belongs to this player."""

    code = "assessment_not_found"

    def __init__(self) -> None:
        super().__init__("Assessment not found.")


class QuestionNotOutstanding(ConflictError):
    """The answer is not for the question currently awaiting a response.

    Answers are append-only and irreversible; the engine accepts an answer only
    for the question it last asked, so a stale or out-of-order submission can
    never double-record or rewrite history.

    The client recovery is to refetch the current step and re-render it — which
    is why this must not arrive looking like ``assessment_already_finished``.
    """

    code = "question_not_outstanding"

    def __init__(self) -> None:
        super().__init__("This answer is not for the question awaiting a response.")


class AssessmentAlreadyFinished(ConflictError):
    """A completed assessment cannot be abandoned — its rating already exists.

    The client recovery is to jump to the result, not to refetch a question that
    no longer exists.
    """

    code = "assessment_already_finished"

    def __init__(self) -> None:
        super().__init__("This assessment is already finished.")


class SportAlreadyRated(ConflictError):
    """This player already holds a Skill rating for this sport.

    A rating's stream is keyed by ``(player, sport)`` and initialisation is its
    only transition today, so a second completed run for a sport would append a
    second opening event to a stream that already has one — which the store
    rejects, *after* the player has answered every question.

    Refusing the start is the only place where refusing is cheap. Whether a
    second assessment should instead **replace** a rating is a real domain
    question, and it is deliberately not answered here: the same transition is
    what the match-update engine will need, and designing it with only
    onboarding in view would settle its shape for the wrong caller (#53).

    The client recovery is to offer the sport as already rated rather than as
    startable — which is what the picker does today, so no shipped flow reaches
    this.
    """

    code = "sport_already_rated"

    def __init__(self) -> None:
        super().__init__("This player is already rated at this sport.")


class InvalidAnswerOption(BadRequestError):
    """The chosen option is not one this question offers."""

    code = "invalid_answer_option"

    def __init__(self) -> None:
        super().__init__("The selected option is not offered for this question.")

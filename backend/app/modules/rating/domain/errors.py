"""Rating-context errors, rendered as structured JSON over HTTP.

Each carries its own wire code. The two 409s are the reason that matters: they
arrive on the same status from the same endpoint family — a double-tapped
confirm, or the same assessment resumed on a second device — and they ask the
client for opposite recoveries.
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


class InvalidAnswerOption(BadRequestError):
    """The chosen option is not one this question offers."""

    code = "invalid_answer_option"

    def __init__(self) -> None:
        super().__init__("The selected option is not offered for this question.")

"""Rating-context errors, rendered as structured JSON over HTTP."""

from __future__ import annotations

from app.core.exception_handlers import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class AssessmentNotFound(NotFoundError):
    """No assessment with this id belongs to this player."""

    def __init__(self) -> None:
        super().__init__("Assessment not found.")


class QuestionNotOutstanding(ConflictError):
    """The answer is not for the question currently awaiting a response.

    Answers are append-only and irreversible; the engine accepts an answer only
    for the question it last asked, so a stale or out-of-order submission can
    never double-record or rewrite history.
    """

    def __init__(self) -> None:
        super().__init__("This answer is not for the question awaiting a response.")


class InvalidAnswerOption(BadRequestError):
    """The chosen option is not one this question offers."""

    def __init__(self) -> None:
        super().__init__("The selected option is not offered for this question.")

"""Rating-context errors, rendered as structured JSON over HTTP.

Each carries its own wire code. The five 409s are the reason that matters: they
arrive on the same status from the same endpoint family — a double-tapped
confirm, the same assessment resumed on a second device, a sport already rated, a
change arriving after the rating exists, a rating asked for before the
questionnaire has stopped — and they ask the client for opposite recoveries.
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
    """The submission is for a question this run has no answer to give it.

    A submission is an answer when it names the outstanding question, and a
    **revision** when it names one the transcript already holds (``docs/adr/0020``).
    This is everything else: a question from another run, one this engine version
    would no longer ask, or any submission at all to a run that has ended without
    a rating. So a stale or out-of-order submission still cannot double-record.

    The client recovery is to refetch the current step and re-render it — which
    is why this must not arrive looking like ``assessment_already_finished`` or
    ``answer_not_revisable``, both of which mean the run is over.
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


class AnswerNoLongerRevisable(ConflictError):
    """The answers are settled: this run's Skill rating already exists.

    An answer is revisable for as long as the run is, and no longer
    (``docs/adr/0020``). A rating is what the platform starts relying on — Match
    Fit, the balance forecast, the level range on match creation — so the account
    of a player stops moving at the moment it comes into existence. A Level is
    proved, never declared, and never re-declared.

    Distinguishable from ``question_not_outstanding`` because the recoveries are
    opposite: that one says *refetch and re-render the question*, and there is no
    question to render here. It is separate from
    ``assessment_already_finished`` — which answers the abandonment route — so
    that a client need not read the endpoint to know what it was told.

    The client recovery is to show the rating this run produced.
    """

    code = "answer_not_revisable"

    def __init__(self) -> None:
        super().__init__("This assessment's rating exists; its answers are settled.")


class AssessmentNotStopped(ConflictError):
    """A rating was asked for from a questionnaire that has not stopped asking.

    **Stopping and completing are two moments** (``docs/adr/0020``). The
    questionnaire stops when the engine judges no remaining question would
    meaningfully tighten the estimate; the rating is created by a separate,
    explicit request, and that request is refused until the stop has happened.
    Between the two the run sits in progress with nothing outstanding, which is
    what lets a review screen exist without inventing a status.

    Two runs get this, and one recovery answers both: a run still holding an
    outstanding question, and a run that ended by being **abandoned** — which
    never stopped, it stopped being. In both cases the client refetches the
    current step and renders it, which is a question in the first case and a way
    out of the flow in the second.

    Not ``assessment_already_finished``, which says a rating already exists, and
    not ``question_not_outstanding``, which is about a submission naming the
    wrong question. This one is about *when* a rating may be created.
    """

    code = "assessment_not_stopped"

    def __init__(self) -> None:
        super().__init__("This assessment's questionnaire has not finished asking.")


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

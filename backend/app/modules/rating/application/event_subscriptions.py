from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.games.domain.events import ResultAccepted
from app.modules.rating.application.handlers import (
    LogRatingEvent,
    SettleRatingsOnAnAgreement,
)
from app.modules.rating.application.settle_results import SettleRatingsOnResults
from app.modules.rating.domain.events import (
    AnswerRevised,
    AnswerSubmitted,
    AssessmentAbandoned,
    AssessmentCompleted,
    AssessmentStarted,
    QuestionAsked,
    RatingInitialised,
    RatingMovedOnResult,
)


def register_rating_events(catalog: EventCatalog) -> None:
    catalog.register(AssessmentStarted, name="rating.assessment_started", version=1)
    catalog.register(QuestionAsked, name="rating.question_asked", version=1)
    catalog.register(AnswerSubmitted, name="rating.answer_submitted", version=1)
    catalog.register(AnswerRevised, name="rating.answer_revised", version=1)
    catalog.register(
        AssessmentCompleted, name="rating.assessment_completed", version=1
    )
    catalog.register(
        AssessmentAbandoned, name="rating.assessment_abandoned", version=1
    )
    catalog.register(RatingInitialised, name="rating.rating_initialised", version=1)
    catalog.register(
        RatingMovedOnResult, name="rating.moved_on_result", version=1
    )


def subscribe_rating_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(AssessmentStarted, LogRatingEvent("rating.assessment_started"))
    dispatcher.subscribe(QuestionAsked, LogRatingEvent("rating.question_asked"))
    dispatcher.subscribe(AnswerSubmitted, LogRatingEvent("rating.answer_submitted"))
    dispatcher.subscribe(AnswerRevised, LogRatingEvent("rating.answer_revised"))
    dispatcher.subscribe(
        AssessmentCompleted, LogRatingEvent("rating.assessment_completed")
    )
    dispatcher.subscribe(
        AssessmentAbandoned, LogRatingEvent("rating.assessment_abandoned")
    )
    dispatcher.subscribe(
        RatingInitialised, LogRatingEvent("rating.rating_initialised")
    )
    dispatcher.subscribe(
        RatingMovedOnResult, LogRatingEvent("rating.moved_on_result")
    )


def subscribe_the_rating_settler(
    dispatcher: EventDispatcher, settle: SettleRatingsOnResults
) -> None:
    """The subscriber that moves the Levels of a game *That's right* settled
    (#654; ``docs/adr/0195`` §5). It **writes** — a rating stream per seat — so
    it is added per delivery run over that run's session, as the room teller
    is; the catch-up job still walks every result a window closing settled."""

    dispatcher.subscribe(ResultAccepted, SettleRatingsOnAnAgreement(settle))

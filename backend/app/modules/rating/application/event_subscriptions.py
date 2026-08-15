from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.rating.application.handlers import LogRatingEvent
from app.modules.rating.domain.events import (
    AnswerRevised,
    AnswerSubmitted,
    AssessmentAbandoned,
    AssessmentCompleted,
    AssessmentStarted,
    QuestionAsked,
    RatingInitialised,
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

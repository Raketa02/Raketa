"""One request's worth of the assessment use cases, over a faked event store.

The repository is built **per request**, exactly as ``get_assessment_repository``
builds it — it remembers the versions it loaded, and one request's versions must
never answer for another's. So every helper here builds a fresh bundle rather
than reusing one across calls; a shared repository would carry an identity map
across what are really separate requests and hide the collision it exists to
raise.

The engine is the real one. It decides which question comes next and when it has
heard enough, and a stub that answered otherwise would be a test of the stub.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.engines.assessment import AssessmentResult
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.kernel import Sport
from app.modules.rating.application.commands import (
    AssessmentStart,
    AssessmentStep,
    CompleteAssessmentCommand,
    CreateAssessmentCommand,
    GetAssessmentQuery,
    SubmitAnswerCommand,
)
from app.modules.rating.application.complete_assessment import CompleteAssessment
from app.modules.rating.application.create_assessment import CreateAssessment
from app.modules.rating.application.get_assessment import GetAssessment
from app.modules.rating.application.list_ratings import ListPlayerRatings
from app.modules.rating.application.submit_answer import SubmitAnswer
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    EventSourcedAssessmentRepository,
)
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    EventSourcedSkillRatingRepository,
)
from tests.unit.fake_event_store import (
    CountingUnitOfWork,
    FrozenClock,
    InMemoryEventStore,
    RecordingPublisher,
)


@dataclass
class Request:
    """The use cases one HTTP request would have been given, and what they used."""

    store: InMemoryEventStore
    repository: EventSourcedAssessmentRepository
    ratings_repository: EventSourcedSkillRatingRepository
    events: RecordingPublisher
    uow: CountingUnitOfWork
    create: CreateAssessment
    submit: SubmitAnswer
    complete: CompleteAssessment
    get: GetAssessment
    list_ratings: ListPlayerRatings


def request(store: InMemoryEventStore) -> Request:
    engine = RacketSkillEngineV3()
    events = RecordingPublisher()
    uow = CountingUnitOfWork()
    clock = FrozenClock()
    repository = EventSourcedAssessmentRepository(event_store=store, events=events)
    ratings = EventSourcedSkillRatingRepository(event_store=store, events=events)
    return Request(
        store=store,
        repository=repository,
        ratings_repository=ratings,
        events=events,
        uow=uow,
        create=CreateAssessment(
            engine=engine,
            assessments=repository,
            ratings=ratings,
            uow=uow,
            clock=clock,
        ),
        submit=SubmitAnswer(
            engine=engine,
            assessments=repository,
            uow=uow,
            clock=clock,
        ),
        complete=CompleteAssessment(
            engine=engine,
            assessments=repository,
            ratings=ratings,
            uow=uow,
            clock=clock,
        ),
        get=GetAssessment(engine=engine, assessments=repository),
        list_ratings=ListPlayerRatings(ratings=ratings),
    )


async def start(
    store: InMemoryEventStore, player_id: UUID, sport: Sport = Sport.PADEL
) -> AssessmentStart:
    return await request(store).create.execute(
        CreateAssessmentCommand(player_id=player_id, sport=sport)
    )


async def answer(
    store: InMemoryEventStore,
    player_id: UUID,
    step: AssessmentStep,
    option: int = -1,
) -> AssessmentStep:
    """Answer whatever is outstanding, picking one of its options by position."""

    assert step.question is not None
    return await request(store).submit.execute(
        SubmitAnswerCommand(
            player_id=player_id,
            assessment_id=step.assessment_id,
            question_id=step.question.id,
            option_id=step.question.options[option].id,
        )
    )


async def read(
    store: InMemoryEventStore, player_id: UUID, assessment_id: UUID
) -> AssessmentStep:
    return await request(store).get.execute(
        GetAssessmentQuery(player_id=player_id, assessment_id=assessment_id)
    )


async def run_to_stop(
    store: InMemoryEventStore,
    player_id: UUID,
    sport: Sport = Sport.PADEL,
    option: int = -1,
) -> tuple[AssessmentStep, Request]:
    """Answer until the engine stops asking; hand back the last request too.

    The caller cannot know which question is the last one — the engine decides it
    has heard enough only after an answer arrives — so this is the same loop a
    client runs. The step it ends on carries **neither** a question nor a result:
    the questionnaire has stopped and no rating exists yet.
    """

    step = (await start(store, player_id, sport)).step
    last = request(store)
    while step.question is not None:
        last = request(store)
        assert step.question is not None
        step = await last.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=step.assessment_id,
                question_id=step.question.id,
                option_id=step.question.options[option].id,
            )
        )
    return step, last


async def run_to_result(
    store: InMemoryEventStore,
    player_id: UUID,
    sport: Sport = Sport.PADEL,
    option: int = -1,
) -> tuple[AssessmentStep, Request]:
    """Answer to the stop, then ask for the rating — the whole client flow.

    The final ``Request`` is the **completing** one, because what that call
    wrote, published and committed is the thing worth asserting about. It is a
    separate request now: answering the last question no longer creates
    anything (``docs/adr/0020``).
    """

    stopped, _ = await run_to_stop(store, player_id, sport, option)
    last = request(store)
    step = await last.complete.execute(
        CompleteAssessmentCommand(
            player_id=player_id, assessment_id=stopped.assessment_id
        )
    )
    return step, last


def result_of(step: AssessmentStep) -> AssessmentResult:
    assert step.result is not None
    return step.result

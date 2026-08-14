"""The rating context's endpoints: the assessment exchange, and the ratings held.

Creating an assessment returns the first question; submitting an answer returns
either the next question or the final result. The client holds no flow state; the
mutation response *is* the current question.

``/ratings`` is the other side of that — not a run in progress but the ratings a
player already holds. Two routers, because they are two resources; the client's
entry gate reads both, in parallel, and neither answers the other's question.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.rating.application.commands import (
    AbandonAssessmentCommand,
    CreateAssessmentCommand,
    FindInProgressQuery,
    GetAssessmentQuery,
    ListInProgressQuery,
    ListRatingsQuery,
    SubmitAnswerCommand,
)
from app.modules.rating.domain.ids import PlayerId
from app.modules.rating.presentation.dependencies import (
    AbandonAssessmentDep,
    CreateAssessmentDep,
    FindInProgressAssessmentDep,
    GetAssessmentDep,
    ListInProgressAssessmentsDep,
    ListPlayerRatingsDep,
    SubmitAnswerDep,
)
from app.modules.rating.presentation.schemas import (
    AssessmentStepResponse,
    CreateAssessmentRequest,
    InProgressAssessmentsResponse,
    RatingsResponse,
    SubmitAnswerRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/assessments", tags=["assessments"])
ratings_router = APIRouter(prefix="/ratings", tags=["ratings"])


@ratings_router.get(
    "",
    response_model=RatingsResponse,
    status_code=status.HTTP_200_OK,
    summary="The Skill ratings this player holds, one per rated sport",
)
async def list_ratings(
    current_user: CurrentUserDep,
    use_case: ListPlayerRatingsDep,
) -> RatingsResponse:
    ratings = await use_case.execute(
        ListRatingsQuery(player_id=PlayerId(current_user.id))
    )
    return RatingsResponse.from_domain(ratings)


@router.post(
    "",
    response_model=AssessmentStepResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {
            "model": AssessmentStepResponse,
            "description": (
                "An assessment for this sport was already in progress; its "
                "outstanding question is returned and nothing was created."
            ),
        },
        status.HTTP_201_CREATED: {
            "model": AssessmentStepResponse,
            "description": (
                "A new assessment was started; its opening question is returned."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`sport_already_rated` — this player already holds a Skill rating "
                "for this sport, so no assessment is started."
            ),
        },
    },
    summary="Start an assessment and receive its opening question",
    description=(
        "Idempotent per player and sport. Starting a sport that already has an "
        "unfinished run returns **that** run and its outstanding question with a "
        "200, rather than opening a second one — so a double-tapped confirm, or a "
        "retry after a lost response, costs nothing. A sport whose previous run was "
        "abandoned still starts a new run, with a 201.\n\n"
        "Both outcomes carry the same body, so a client that only routes on the "
        "step needs no branch; the status code is there for one that wants to tell "
        "the two apart.\n\n"
        "**A sport this player is already rated at is refused with a 409** "
        "(`sport_already_rated`). A rating stream is keyed by player and sport and "
        "initialisation is its only transition, so a second completed run for one "
        "sport cannot be stored — and refusing at the start is the only point at "
        "which refusing costs the player nothing rather than a whole questionnaire. "
        "The picker offers unrated sports, so no shipped flow reaches this."
    ),
)
async def create_assessment(
    body: CreateAssessmentRequest,
    current_user: CurrentUserDep,
    use_case: CreateAssessmentDep,
    response: Response,
) -> AssessmentStepResponse:
    started = await use_case.execute(
        CreateAssessmentCommand(
            player_id=PlayerId(current_user.id),
            sport=body.sport,
        )
    )
    if not started.created:
        response.status_code = status.HTTP_200_OK
    return AssessmentStepResponse.from_step(started.step)


@router.get(
    "/in-progress",
    response_model=AssessmentStepResponse | InProgressAssessmentsResponse,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "No assessment in progress for that sport. Only ever returned "
                "when `sport` is supplied."
            )
        }
    },
    summary="Resume: one sport's in-progress assessment, or every sport's",
    description=(
        "One question — *which of this player's runs are unfinished* — asked two "
        "ways.\n\n"
        "**With `sport`,** the answer is that sport's outstanding run as an "
        "`AssessmentStepResponse`, carrying its outstanding question, or a 204 "
        "when there is none. This is the resume read, unchanged.\n\n"
        "**Without `sport`,** the answer is an `InProgressAssessmentsResponse`: "
        "every unfinished run this player holds, at most one per sport, ordered "
        "by the sport registry, and an empty list — with a 200, never a 204 or a "
        "404 — when there are none. Each entry carries the assessment id and its "
        "sport, which is what a router needs; it carries no question, because the "
        "caller re-reads the run it routes to and the empty answer is the common "
        "one.\n\n"
        "Which shape comes back is decided by the parameter, so a caller that "
        "always omits `sport` always sees the collection."
    ),
)
async def find_in_progress(
    current_user: CurrentUserDep,
    use_case: FindInProgressAssessmentDep,
    list_use_case: ListInProgressAssessmentsDep,
    sport: Sport | None = None,
) -> Response | AssessmentStepResponse | InProgressAssessmentsResponse:
    if sport is None:
        entries = await list_use_case.execute(
            ListInProgressQuery(player_id=PlayerId(current_user.id))
        )
        return InProgressAssessmentsResponse.from_views(entries)

    step = await use_case.execute(
        FindInProgressQuery(
            player_id=PlayerId(current_user.id),
            sport=sport,
        )
    )
    if step is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return AssessmentStepResponse.from_step(step)


@router.get(
    "/{assessment_id}",
    response_model=AssessmentStepResponse,
    summary="Fetch an assessment's current state — its question or its result",
)
async def get_assessment(
    assessment_id: UUID,
    current_user: CurrentUserDep,
    use_case: GetAssessmentDep,
) -> AssessmentStepResponse:
    step = await use_case.execute(
        GetAssessmentQuery(
            player_id=PlayerId(current_user.id),
            assessment_id=assessment_id,
        )
    )
    return AssessmentStepResponse.from_step(step)


@router.post(
    "/{assessment_id}/abandonment",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Abandon an in-progress assessment, freeing the sport to start again",
)
async def abandon_assessment(
    assessment_id: UUID,
    current_user: CurrentUserDep,
    use_case: AbandonAssessmentDep,
) -> Response:
    await use_case.execute(
        AbandonAssessmentCommand(
            player_id=PlayerId(current_user.id),
            assessment_id=assessment_id,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{assessment_id}/answers",
    response_model=AssessmentStepResponse,
    status_code=status.HTTP_200_OK,
    summary="Answer the outstanding question and receive the next step",
)
async def submit_answer(
    assessment_id: UUID,
    body: SubmitAnswerRequest,
    current_user: CurrentUserDep,
    use_case: SubmitAnswerDep,
) -> AssessmentStepResponse:
    step = await use_case.execute(
        SubmitAnswerCommand(
            player_id=PlayerId(current_user.id),
            assessment_id=assessment_id,
            question_id=body.question_id,
            option_id=body.option_id,
        )
    )
    return AssessmentStepResponse.from_step(step)

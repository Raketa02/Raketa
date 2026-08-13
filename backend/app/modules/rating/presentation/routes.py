"""The assessment endpoints — server-driven, one exchange per answer.

Creating an assessment returns the first question; submitting an answer returns
either the next question or the final result. The client holds no flow state; the
mutation response *is* the current question.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.kernel import Sport
from app.modules.rating.application.commands import (
    AbandonAssessmentCommand,
    CreateAssessmentCommand,
    FindInProgressQuery,
    GetAssessmentQuery,
    SubmitAnswerCommand,
)
from app.modules.rating.domain.ids import PlayerId
from app.modules.rating.presentation.dependencies import (
    AbandonAssessmentDep,
    CreateAssessmentDep,
    FindInProgressAssessmentDep,
    GetAssessmentDep,
    SubmitAnswerDep,
)
from app.modules.rating.presentation.schemas import (
    AssessmentStepResponse,
    CreateAssessmentRequest,
    SubmitAnswerRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post(
    "",
    response_model=AssessmentStepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an assessment and receive its opening question",
)
async def create_assessment(
    body: CreateAssessmentRequest,
    current_user: CurrentUserDep,
    use_case: CreateAssessmentDep,
) -> AssessmentStepResponse:
    step = await use_case.execute(
        CreateAssessmentCommand(
            player_id=PlayerId(current_user.id),
            sport=body.sport,
        )
    )
    return AssessmentStepResponse.from_step(step)


@router.get(
    "/in-progress",
    response_model=AssessmentStepResponse,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "No assessment in progress"}
    },
    summary="Resume: the sport's in-progress assessment, or nothing",
)
async def find_in_progress(
    sport: Sport,
    current_user: CurrentUserDep,
    use_case: FindInProgressAssessmentDep,
) -> Response | AssessmentStepResponse:
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

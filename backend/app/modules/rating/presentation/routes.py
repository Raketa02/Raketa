"""The assessment endpoints — server-driven, one exchange per answer.

Creating an assessment returns the first question; submitting an answer returns
either the next question or the final result. The client holds no flow state; the
mutation response *is* the current question.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.modules.rating.application.commands import (
    CreateAssessmentCommand,
    SubmitAnswerCommand,
)
from app.modules.rating.domain.ids import PlayerId
from app.modules.rating.presentation.dependencies import (
    CreateAssessmentDep,
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

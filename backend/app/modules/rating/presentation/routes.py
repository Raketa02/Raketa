"""The rating context's endpoints: the assessment exchange, and the ratings held.

Creating an assessment returns the first question; submitting an answer returns
the next one, or the news that there is none left to ask. The client holds no flow
state; the mutation response *is* the current question. Submitting an answer for a
question already answered **changes** it, discarding the answers that depended on
it — one route, because the client is not asked to know which of the two it is
doing (``docs/adr/0020``).

**The rating is created by its own request**, on ``/completion``. The
questionnaire stopping and the assessment completing are two moments, and the
second is the irreversible one — which is what lets a review of every answer sit
between them.

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
    CompleteAssessmentCommand,
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
    CompleteAssessmentDep,
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
from app.modules.users.presentation.dependencies import (
    ADULT_ATTESTATION_MISSING,
    AttestedPlayerDep,
    CurrentUserDep,
)

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
        **ADULT_ATTESTATION_MISSING,
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
    current_user: AttestedPlayerDep,
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
    "/{assessment_id}/completion",
    response_model=AssessmentStepResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`assessment_not_stopped` — the questionnaire has not finished "
                "asking, or the run was abandoned. Refetch the current step and "
                "render it."
            ),
        },
    },
    summary="Finish a stopped assessment: create its Skill rating",
    description=(
        "**The irreversible one.** The questionnaire *stopping* and the "
        "assessment *completing* are two moments: answering the question that "
        "stops the run creates nothing and leaves every answer revisable, and "
        "this request is what turns those answers into a Skill rating. So a "
        "client can show the whole set of answers back to the player, still "
        "changeable, before anything is committed.\n\n"
        "Callable only on a **stopped** run — one whose step carries neither a "
        "`question` nor a `result` while `status` is still `in_progress`. A run "
        "with a question outstanding, and one that was abandoned, are both "
        "refused with `assessment_not_stopped`.\n\n"
        "The finished step comes back inline, `result` and all, because the "
        "player is shown their rating on the very next screen. **Calling it "
        "twice is safe**: the second call records nothing and returns the same "
        "result, so a double-tapped submit produces one rating rather than a "
        "conflict the client has to translate.\n\n"
        "Once this has been called the run's answers are settled: a change is "
        "refused with `answer_not_revisable`."
    ),
)
async def complete_assessment(
    assessment_id: UUID,
    current_user: CurrentUserDep,
    use_case: CompleteAssessmentDep,
) -> AssessmentStepResponse:
    step = await use_case.execute(
        CompleteAssessmentCommand(
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
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`invalid_answer_option` — the chosen option is not one that "
                "question offers."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`question_not_outstanding` — the question is neither the one "
                "awaiting a response nor one this run has answered; refetch the "
                "current step and re-render it. `answer_not_revisable` — this "
                "run's Skill rating already exists, so its answers are settled; "
                "show the rating instead."
            ),
        },
    },
    summary="Answer the outstanding question, or change an answer already given",
    description=(
        "**One request, decided by what the run has already answered.**\n\n"
        "- A `question_id` the run has *not* answered must be the outstanding "
        "one: this is an ordinary answer, and the next question comes back — or "
        "**no question at all**, which is the questionnaire stopping.\n"
        "- A `question_id` the run *has* answered with a **different** "
        "`option_id` is a **revision**. The answers given after it are "
        "discarded, because each was pitched at a difficulty chosen from the "
        "estimate as it then stood, and the response is whatever the "
        "questionnaire asks next given the shortened set of answers. That may "
        "be a question, and it may be the stop — changing the opening answer to "
        "*I have never played* ends the questioning there.\n"
        "- A `question_id` the run has answered with the **same** `option_id` "
        "records nothing and returns the current step. So a retry after a lost "
        "response is free, and so is changing your mind and changing it back.\n\n"
        "**`question` and `result` both null, with `status` still `in_progress`, "
        "is the stop.** No further question would meaningfully tighten the "
        "estimate, and nothing has been rated: the run waits, with every answer "
        "still revisable, until `POST /completion` is called. Answering never "
        "creates a Skill rating, so a client need not — and cannot — predict "
        "which question is the last one.\n\n"
        "The `transcript` on every response is the answers as they now stand; "
        "after a revision it is **shorter**, and a client showing the run's "
        "progress should read it rather than remember what it last drew.\n\n"
        "**Answers are revisable for as long as the run is, and no longer.** "
        "Once the run has produced a Skill rating, a change is refused with "
        "`answer_not_revisable` — a code of its own, because the recovery is to "
        "show the rating rather than to re-render a question."
    ),
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

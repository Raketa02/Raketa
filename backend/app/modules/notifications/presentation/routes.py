"""The player surface of **Notifications** (#549; the mechanics §17.2; the
screens A7.2, A9): the three choices, a phone's push token, and the recent
notices behind the bell on Home."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.exception_handlers import ErrorResponse
from app.modules.notifications.application.preferences import (
    SetNotificationChoicesCommand,
)
from app.modules.notifications.presentation.dependencies import (
    ReadNotificationPreferencesDep,
    ReadRecentNoticesDep,
    RegisterAPhoneDep,
    RemoveAPhoneDep,
    SetNotificationChoicesDep,
)
from app.modules.notifications.presentation.schemas import (
    NoticeSchema,
    NotificationChoicesSchema,
    PushDeviceRequest,
    RecentNoticesResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/players/me", tags=["notifications"])


@router.get(
    "/notifications",
    response_model=NotificationChoicesSchema,
    summary="My notification choices",
    description=(
        "You › Account › *Notifications*: the three notices a player chooses — "
        "*You complete it* and *Challenges for you* on, *Fill in alerts* off, "
        "until changed. The seven always-on notices are no choice."
    ),
)
async def read_notification_choices(
    user: CurrentUserDep, read: ReadNotificationPreferencesDep
) -> NotificationChoicesSchema:
    return NotificationChoicesSchema.from_preferences(await read.execute(user.id))


@router.put(
    "/notifications",
    response_model=NotificationChoicesSchema,
    summary="Save my notification choices",
    description=(
        "All three, as the screen saves them on every tap. The same answer "
        "records nothing. Answers what is now saved."
    ),
)
async def set_notification_choices(
    body: NotificationChoicesSchema,
    user: CurrentUserDep,
    save: SetNotificationChoicesDep,
) -> NotificationChoicesSchema:
    saved = await save.execute(
        SetNotificationChoicesCommand(player_id=user.id, choices=body.as_choices())
    )
    return NotificationChoicesSchema.from_preferences(saved)


@router.post(
    "/devices",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "This phone is pushed every notice given to you. Also the answer "
                "when it already was. A phone signed in as somebody else before "
                "is theirs no more."
            ),
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "`push_token_invalid` — not an Expo push token.",
        },
    },
    summary="Push to this phone",
    description=(
        "What a phone sends once it is allowed to show notifications, and again "
        "whenever its token changes. You keep at most ten phones; past them the "
        "one registered longest ago is let go."
    ),
)
async def register_a_phone(
    body: PushDeviceRequest, user: CurrentUserDep, register: RegisterAPhoneDep
) -> None:
    await register.execute(user.id, body.token)


@router.post(
    "/devices/removal",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "This phone is pushed nothing more for you. Also the answer when "
                "it was not registered."
            ),
        },
    },
    summary="Stop pushing to this phone",
    description=(
        "What a phone sends as it signs out, before its session ends. The token "
        "travels in the body, never the path, so it is in no access log."
    ),
)
async def remove_a_phone(
    body: PushDeviceRequest, user: CurrentUserDep, remove: RemoveAPhoneDep
) -> None:
    await remove.execute(user.id, body.token)


@router.get(
    "/notices",
    response_model=RecentNoticesResponse,
    summary="My recent notices",
    description=(
        "Everything you were told — the list behind the bell on Home — the "
        "newest first, each in the words it was pushed in and with where a tap "
        "opens it. A notice past its kind's daily cap that was bundled is not "
        "its own row: the row it joined says how many it holds (`gathered`)."
    ),
)
async def read_recent_notices(
    user: CurrentUserDep,
    read: ReadRecentNoticesDep,
    limit: int = Query(30, ge=1, le=100, description="The most notices to answer."),
) -> RecentNoticesResponse:
    return RecentNoticesResponse(
        notices=[
            NoticeSchema.from_recent(recent)
            for recent in await read.execute(user.id, limit=limit)
        ]
    )

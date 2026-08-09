from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.users.domain.events import (
    UserDisabled,
    UserPromotedToAdmin,
    UserRegistered,
)

logger = logging.getLogger(__name__)


class LogUserRegistered:
    """Audit-trail handler for `UserRegistered`.

    Concrete production handlers (send welcome email, push to analytics,
    create default workspace, etc.) follow the same shape: implement
    `async __call__(event)` and register against `UserRegistered` at
    startup. Replace this stub once a real side-effect is wired up.
    """

    async def __call__(self, event: UserRegistered, context: DeliveryContext) -> None:
        logger.info(
            "user.registered",
            extra={
                "user_id": str(event.user_id),
                "email": event.email,
                "nickname": event.nickname,
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogUserDisabled:
    async def __call__(self, event: UserDisabled, context: DeliveryContext) -> None:
        logger.info(
            "user.disabled",
            extra={
                "user_id": str(event.user_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogUserPromotedToAdmin:
    async def __call__(
        self, event: UserPromotedToAdmin, context: DeliveryContext
    ) -> None:
        logger.info(
            "user.promoted_to_admin",
            extra={
                "user_id": str(event.user_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )

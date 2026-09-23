from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.users.domain.events import (
    UserDisabled,
    UserMarkedAsTester,
    UserNamed,
    UserPromotedToAdmin,
    UserRegistered,
    UserUnmarkedAsTester,
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
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogUserNamed:
    """Audit-trail handler for the naming (``docs/adr/0171`` §2).

    A subscriber exists because an event with none fails delivery and is retried
    for ever; nothing else reacts to a player being named — every read that says
    a name reads it live off ``users``, so a corrected name fixes the whole
    backlog without anybody being told.
    """

    async def __call__(self, event: UserNamed, context: DeliveryContext) -> None:
        logger.info(
            "user.named",
            extra={
                "user_id": str(event.user_id),
                "name": event.name,
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


class LogUserMarkedAsTester:
    """Audit trail for the tester mark (``docs/adr/0180`` §9). Nothing else
    reacts to it: the player app reads ``is_tester`` off its own account at the
    next launch or foreground, and no datafile is told."""

    async def __call__(
        self, event: UserMarkedAsTester, context: DeliveryContext
    ) -> None:
        logger.info(
            "user.marked_as_tester",
            extra={
                "user_id": str(event.user_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogUserUnmarkedAsTester:
    async def __call__(
        self, event: UserUnmarkedAsTester, context: DeliveryContext
    ) -> None:
        logger.info(
            "user.unmarked_as_tester",
            extra={
                "user_id": str(event.user_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )

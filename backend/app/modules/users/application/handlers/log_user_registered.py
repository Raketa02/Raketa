from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    AdultAttested,
    PasswordChanged,
    PasswordCleared,
    UserDisabled,
    UserNamed,
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


class LogPasswordChanged:
    """Audit-trail handler for a password change — **never the hash**. The line
    says which account signed out everywhere, and when."""

    async def __call__(
        self, event: PasswordChanged, context: DeliveryContext
    ) -> None:
        logger.info(
            "user.password_changed",
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


class LogAccountOpenedByInvitation:
    """Audit trail for an account an Invitation opened (``docs/adr/0184`` §2)
    — **never the hash, the email or the name**: the id says which account."""

    async def __call__(
        self, event: AccountOpenedByInvitation, context: DeliveryContext
    ) -> None:
        logger.info(
            "user.opened_by_invitation",
            extra={
                "user_id": str(event.user_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogAdultAttested:
    async def __call__(self, event: AdultAttested, context: DeliveryContext) -> None:
        logger.info(
            "user.adult_attested",
            extra={
                "user_id": str(event.user_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogPasswordCleared:
    """Audit trail for the club's *Reset password* of an administrator: which
    account was signed out everywhere, and when (``docs/adr/0184`` §6)."""

    async def __call__(self, event: PasswordCleared, context: DeliveryContext) -> None:
        logger.info(
            "user.password_cleared",
            extra={
                "user_id": str(event.user_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )

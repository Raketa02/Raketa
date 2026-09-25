from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)

logger = logging.getLogger(__name__)


class LogRefreshTokenIssued:
    async def __call__(
        self, event: RefreshTokenIssued, context: DeliveryContext
    ) -> None:
        logger.info(
            "auth.refresh_token.issued",
            extra={
                "account_id": str(event.account_id),
                "audience": event.audience,
                "jti": event.jti,
                "expires_at": event.expires_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogRefreshTokenRevoked:
    async def __call__(
        self, event: RefreshTokenRevoked, context: DeliveryContext
    ) -> None:
        logger.info(
            "auth.refresh_token.revoked",
            extra={
                "account_id": str(event.account_id),
                "audience": event.audience,
                "jti": event.jti,
                "reason": event.reason,
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogRefreshTokenRotated:
    async def __call__(
        self, event: RefreshTokenRotated, context: DeliveryContext
    ) -> None:
        logger.info(
            "auth.refresh_token.rotated",
            extra={
                "account_id": str(event.account_id),
                "audience": event.audience,
                "revoked_jti": event.revoked_jti,
                "issued_jti": event.issued_jti,
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )

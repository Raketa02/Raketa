from __future__ import annotations

import logging

from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)

logger = logging.getLogger(__name__)


class LogRefreshTokenIssued:
    async def __call__(self, event: RefreshTokenIssued) -> None:
        logger.info(
            "auth.refresh_token.issued",
            extra={
                "user_id": str(event.user_id),
                "jti": event.jti,
                "expires_at": event.expires_at.isoformat(),
            },
        )


class LogRefreshTokenRevoked:
    async def __call__(self, event: RefreshTokenRevoked) -> None:
        logger.info(
            "auth.refresh_token.revoked",
            extra={
                "user_id": str(event.user_id),
                "jti": event.jti,
                "reason": event.reason,
            },
        )


class LogRefreshTokenRotated:
    async def __call__(self, event: RefreshTokenRotated) -> None:
        logger.info(
            "auth.refresh_token.rotated",
            extra={
                "user_id": str(event.user_id),
                "revoked_jti": event.revoked_jti,
                "issued_jti": event.issued_jti,
            },
        )

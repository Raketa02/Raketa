"""The Club context's subscribers: a log line each, and nothing else.

Nothing reacts to a club yet — the projection is written in the act's own
transaction, not by a subscriber — but a delivered event with no handler is a
delivery failure, so each is logged as ``users``' are. **The account's line
carries neither its hash nor its email** — the ids say which account it was.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.clubs.domain.events import (
    ClubAccountOpened,
    ClubDetailsChanged,
    ClubRegistered,
)

logger = logging.getLogger(__name__)


class LogClubRegistered:
    async def __call__(self, event: ClubRegistered, context: DeliveryContext) -> None:
        logger.info(
            "clubs.club.registered",
            extra={
                "club_id": str(event.club_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogClubDetailsChanged:
    async def __call__(
        self, event: ClubDetailsChanged, context: DeliveryContext
    ) -> None:
        logger.info(
            "clubs.club.details_changed",
            extra={
                "club_id": str(event.club_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogClubAccountOpened:
    async def __call__(
        self, event: ClubAccountOpened, context: DeliveryContext
    ) -> None:
        logger.info(
            "clubs.club_account.opened",
            extra={
                "account_id": str(event.account_id),
                "club_id": str(event.club_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )

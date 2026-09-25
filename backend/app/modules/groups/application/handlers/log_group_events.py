"""The Groups context's subscribers: a log line each, and nothing else.

Nothing reacts to a group yet — the projections are written in the act's own
transaction, not by a subscriber — but a delivered event with no handler is a
delivery failure, so each is logged as ``clubs``' are. **The lines carry ids and
never a group's name**, which is something a person typed.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.groups.domain.events import GroupJoined, PlayerGroupCreated

logger = logging.getLogger(__name__)


class LogPlayerGroupCreated:
    async def __call__(
        self, event: PlayerGroupCreated, context: DeliveryContext
    ) -> None:
        logger.info(
            "groups.player_group.created",
            extra={
                "group_id": str(event.group_id),
                "home_club_id": str(event.home_club_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogGroupJoined:
    async def __call__(self, event: GroupJoined, context: DeliveryContext) -> None:
        logger.info(
            "groups.group.joined",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )

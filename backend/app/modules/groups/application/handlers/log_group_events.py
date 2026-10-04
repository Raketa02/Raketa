"""The Groups context's subscribers: a log line each, and nothing else.

Nothing reacts to a group yet — the projections are written in the act's own
transaction, not by a subscriber — but a delivered event with no handler is a
delivery failure, so each is logged as ``clubs``' are. **The lines carry ids and
never a group's name**, which is something a person typed.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.groups.domain.events import (
    AdministratorAssigned,
    GroupDeleted,
    GroupJoined,
    GroupLeft,
    GroupRenamed,
    HandoverSeen,
    JoinPolicyChanged,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    OfficialGroupCreated,
    OwnershipPassed,
    PlayerGroupCreated,
    SportsDeclared,
    WhatsAppSizeSet,
)

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


class LogOfficialGroupCreated:
    async def __call__(
        self, event: OfficialGroupCreated, context: DeliveryContext
    ) -> None:
        logger.info(
            "groups.official_group.created",
            extra={
                "group_id": str(event.group_id),
                "home_club_id": str(event.home_club_id),
                "administrator_id": str(event.administrator_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogWhatsAppSizeSet:
    async def __call__(self, event: WhatsAppSizeSet, context: DeliveryContext) -> None:
        logger.info(
            "groups.whatsapp_size.set",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogSportsDeclared:
    async def __call__(self, event: SportsDeclared, context: DeliveryContext) -> None:
        logger.info(
            "groups.sports.declared",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogAdministratorAssigned:
    async def __call__(
        self, event: AdministratorAssigned, context: DeliveryContext
    ) -> None:
        logger.info(
            "groups.administrator.assigned",
            extra={
                "group_id": str(event.group_id),
                "administrator_id": str(event.administrator_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogHandoverSeen:
    async def __call__(self, event: HandoverSeen, context: DeliveryContext) -> None:
        logger.info(
            "groups.handover.seen",
            extra={
                "group_id": str(event.group_id),
                "administrator_id": str(event.administrator_id),
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


class LogJoinRequested:
    async def __call__(self, event: JoinRequested, context: DeliveryContext) -> None:
        logger.info(
            "groups.join.requested",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogJoinRequestApproved:
    async def __call__(
        self, event: JoinRequestApproved, context: DeliveryContext
    ) -> None:
        logger.info(
            "groups.join_request.approved",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogJoinRequestDeclined:
    async def __call__(
        self, event: JoinRequestDeclined, context: DeliveryContext
    ) -> None:
        logger.info(
            "groups.join_request.declined",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogOwnershipPassed:
    async def __call__(self, event: OwnershipPassed, context: DeliveryContext) -> None:
        logger.info(
            "groups.ownership.passed",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogGroupLeft:
    async def __call__(self, event: GroupLeft, context: DeliveryContext) -> None:
        logger.info(
            "groups.group.left",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogGroupRenamed:
    async def __call__(self, event: GroupRenamed, context: DeliveryContext) -> None:
        logger.info(
            "groups.group.renamed",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogJoinPolicyChanged:
    async def __call__(
        self, event: JoinPolicyChanged, context: DeliveryContext
    ) -> None:
        logger.info(
            "groups.join_policy.changed",
            extra={
                "group_id": str(event.group_id),
                "join_policy": event.join_policy,
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


class LogGroupDeleted:
    async def __call__(self, event: GroupDeleted, context: DeliveryContext) -> None:
        logger.info(
            "groups.group.deleted",
            extra={
                "group_id": str(event.group_id),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )

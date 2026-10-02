"""The Notifications context's two repositories, and the recent list.

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``) — and **their projections are written by
``save``, in the caller's transaction**, as a proposal's are. **``load`` answers
the defaults for a stream never written**: a player who never chose, a day
nobody was told anything on.

**Constructed per unit of work**: the versions they remember belong to one
transaction.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import date
from typing import final
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Sport
from app.modules.notifications.domain.events import (
    NoticeBundled,
    NoticeGiven,
    NotificationChoiceSwitched,
    PushDeviceRegistered,
    PushDeviceRemoved,
)
from app.modules.notifications.domain.notices import NoticesOfADay, day_id_for
from app.modules.notifications.domain.ports import RecordedNotice
from app.modules.notifications.domain.preferences import (
    DEFAULT_CHOICES,
    NotificationChoice,
    NotificationPreferences,
)
from app.modules.notifications.infrastructure.notification_models import (
    NoticeORM,
    NotificationPreferencesORM,
    PushDeviceORM,
)

PREFERENCES_AGGREGATE = "notification_preferences"

#: Each choice's column — what the projection writes and what ``wanting`` reads.
_ROW = NotificationPreferencesORM
_COLUMNS = {
    NotificationChoice.YOU_COMPLETE_IT: _ROW.you_complete_it,
    NotificationChoice.CHALLENGES_FOR_YOU: _ROW.challenges_for_you,
    NotificationChoice.FILL_IN_ALERTS: _ROW.fill_in_alerts,
}
NOTICE_DAY_AGGREGATE = "notice_day"


@final
class EventSourcedNotificationPreferencesRepository:
    """``NotificationPreferencesRepository`` over ``DomainEventStore`` and the
    choices' and phones' projections."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._session = session
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, player_id: UUID) -> NotificationPreferences:
        stored = await self._event_store.load_stream(
            aggregate_type=PREFERENCES_AGGREGATE, aggregate_id=player_id
        )
        preferences = NotificationPreferences.from_history(
            player_id, (record.event for record in stored)
        )
        self._versions[player_id] = preferences.version
        return preferences

    async def save(self, preferences: NotificationPreferences) -> None:
        pending = preferences.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=PREFERENCES_AGGREGATE,
            aggregate_id=preferences.player_id,
            expected_version=self._versions.get(preferences.player_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        for event in pending:
            if isinstance(event, PushDeviceRegistered):
                await self._session.execute(
                    delete(PushDeviceORM).where(PushDeviceORM.device == event.device)
                )
                await self._session.execute(
                    insert(PushDeviceORM).values(
                        device=event.device,
                        token=preferences.token_of(event.device),
                        player_id=event.player_id,
                        registered_at=event.occurred_at,
                    )
                )
            elif isinstance(event, PushDeviceRemoved):
                await self._session.execute(
                    delete(PushDeviceORM).where(
                        PushDeviceORM.device == event.device,
                        PushDeviceORM.player_id == event.player_id,
                    )
                )
        if any(isinstance(event, NotificationChoiceSwitched) for event in pending):
            await self._project_choices(preferences)
        await self._session.flush()
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[preferences.player_id] = preferences.version

    async def _project_choices(self, preferences: NotificationPreferences) -> None:
        values = {
            column.key: preferences.wants(choice) for choice, column in _COLUMNS.items()
        }
        row = await self._session.get(NotificationPreferencesORM, preferences.player_id)
        if row is None:
            self._session.add(
                NotificationPreferencesORM(player_id=preferences.player_id, **values)
            )
        else:
            await self._session.execute(
                update(NotificationPreferencesORM)
                .where(NotificationPreferencesORM.player_id == preferences.player_id)
                .values(**values)
            )

    async def holder_of(self, device: str) -> UUID | None:
        return await self._session.scalar(
            select(PushDeviceORM.player_id).where(PushDeviceORM.device == device)
        )

    async def tokens_of(self, player_id: UUID) -> Mapping[str, str]:
        rows = (
            await self._session.execute(
                select(PushDeviceORM.device, PushDeviceORM.token)
                .where(PushDeviceORM.player_id == player_id)
                .order_by(PushDeviceORM.registered_at, PushDeviceORM.device)
            )
        ).all()
        return {device: token for device, token in rows}

    async def wanting(
        self, choice: NotificationChoice, among: Collection[UUID]
    ) -> frozenset[UUID]:
        if not among:
            return frozenset()
        rows = (
            await self._session.execute(
                select(NotificationPreferencesORM.player_id, _COLUMNS[choice]).where(
                    NotificationPreferencesORM.player_id.in_(list(among))
                )
            )
        ).all()
        chosen = {player_id: bool(on) for player_id, on in rows}
        # A player with no row never chose, and is at the defaults.
        return frozenset(
            player for player in among if chosen.get(player, DEFAULT_CHOICES[choice])
        )


@final
class EventSourcedNoticeDayRepository:
    """``NoticeDayRepository`` over ``DomainEventStore`` and the recent list."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._session = session
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, player_id: UUID, day: date) -> NoticesOfADay:
        day_id = day_id_for(player_id, day)
        stored = await self._event_store.load_stream(
            aggregate_type=NOTICE_DAY_AGGREGATE, aggregate_id=day_id
        )
        notices = NoticesOfADay.from_history(
            player_id, day, (record.event for record in stored)
        )
        self._versions[day_id] = notices.version
        return notices

    async def save(self, notices: NoticesOfADay) -> None:
        pending = notices.pull_events()
        if not pending:
            return
        stored = await self._event_store.append(
            aggregate_type=NOTICE_DAY_AGGREGATE,
            aggregate_id=notices.day_id,
            expected_version=self._versions.get(notices.day_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        for record in stored:
            event = record.event
            if isinstance(event, NoticeGiven):
                await self._session.execute(
                    insert(NoticeORM).values(
                        notice_id=event.notice_id,
                        player_id=event.player_id,
                        kind=event.kind,
                        game_id=event.game_id,
                        pool_id=event.pool_id,
                        sport=event.sport,
                        game_kind=event.game_kind,
                        club_id=event.club_id,
                        starts_at=event.starts_at,
                        opens=event.opens,
                        amount_grosze=event.amount_grosze,
                        people=",".join(str(person) for person in event.people),
                        reason=event.reason,
                        given_at=event.occurred_at,
                        sequence_no=record.sequence_no,
                        gathered=0,
                    )
                )
            elif isinstance(event, NoticeBundled):
                # Gathering one more moves it up the list, newest first.
                await self._session.execute(
                    update(NoticeORM)
                    .where(NoticeORM.notice_id == event.notice_id)
                    .values(
                        gathered=NoticeORM.gathered + 1,
                        given_at=event.occurred_at,
                        sequence_no=record.sequence_no,
                    )
                )
        await self._session.flush()
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[notices.day_id] = notices.version


@final
class SqlAlchemyNoticeDirectory:
    """``NoticeDirectory`` over the ``notices`` projection."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def recent(self, player_id: UUID, *, limit: int) -> Sequence[RecordedNotice]:
        rows = (
            await self._session.scalars(
                select(NoticeORM)
                .where(NoticeORM.player_id == player_id)
                .order_by(NoticeORM.given_at.desc(), NoticeORM.sequence_no.desc())
                .limit(limit)
            )
        ).all()
        return [
            RecordedNotice(
                notice_id=row.notice_id,
                kind=row.kind,
                game_id=row.game_id,
                pool_id=row.pool_id,
                sport=Sport(row.sport),
                game_kind=row.game_kind,
                club_id=row.club_id,
                starts_at=stored_instant(row.starts_at),
                opens=row.opens,
                amount_grosze=row.amount_grosze,
                people=tuple(UUID(one) for one in row.people.split(",") if one),
                reason=row.reason,
                given_at=stored_instant(row.given_at),
                gathered=row.gathered,
            )
            for row in rows
        ]

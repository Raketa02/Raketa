"""The Club account repository: the stream, and the row sign-in reads.

Reads come from the row — sign-in looks an account up by email, and every club
request resolves its token's account by id, which is the one read per request
``docs/adr/0185`` §7 prices in. Writes append to the stream and write the row in
the caller's transaction, as the club's repository does.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.infrastructure.database.stored_time import stored_instant_or_none
from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.clubs.domain.events import (
    ClubAccountOpened,
    ClubAccountPasswordChanged,
)
from app.modules.clubs.infrastructure.club_model import ClubAccountORM
from app.modules.users.domain.value_objects import Email, HashedPassword
from app.shared.domain import DomainEvent

CLUB_ACCOUNT_AGGREGATE = "club_account"


def _to_domain(row: ClubAccountORM) -> ClubAccount:
    return ClubAccount(
        id=row.id,
        club_id=row.club_id,
        email=Email(row.email),
        password_hash=HashedPassword(row.password_hash),
        credentials_changed_at=stored_instant_or_none(row.credentials_changed_at),
    )


class EventSourcedClubAccountRepository:
    """``ClubAccountRepository`` over ``DomainEventStore`` and ``club_accounts``."""

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
        # Account id -> the stream version this unit of work has written it to.
        # An account read from its row carries no version and has no entry, so
        # it is appended at version zero: a second write to a stream that
        # already exists is refused as concurrent rather than written over it.
        self._versions: dict[UUID, int] = {}

    async def load(self, account_id: UUID) -> Optional[ClubAccount]:
        stored = await self._event_store.load_stream(
            aggregate_type=CLUB_ACCOUNT_AGGREGATE, aggregate_id=account_id
        )
        if not stored:
            return None
        account = ClubAccount.from_history(record.event for record in stored)
        self._versions[account.id] = account.version
        return account

    async def get_by_id(self, account_id: UUID) -> Optional[ClubAccount]:
        row = await self._session.get(ClubAccountORM, account_id)
        return _to_domain(row) if row else None

    async def get_by_email(self, email: Email) -> Optional[ClubAccount]:
        result = await self._session.execute(
            select(ClubAccountORM).where(ClubAccountORM.email == email.value)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def save(self, account: ClubAccount) -> None:
        pending = account.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=CLUB_ACCOUNT_AGGREGATE,
            aggregate_id=account.id,
            expected_version=self._versions.get(account.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        for event in pending:
            await self._project(event)
        await self._session.flush()
        self._versions[account.id] = account.version

    async def _project(self, event: DomainEvent) -> None:
        if isinstance(event, ClubAccountOpened):
            self._session.add(
                ClubAccountORM(
                    id=event.account_id,
                    club_id=event.club_id,
                    email=event.email,
                    password_hash=event.password_hash,
                )
            )
            return
        if isinstance(event, ClubAccountPasswordChanged):
            row = await self._session.get(ClubAccountORM, event.account_id)
            if row is None:
                raise RuntimeError(
                    f"the password of club account {event.account_id} has no "
                    f"row to land on"
                )
            # The hash sign-in reads, and the instant every club request reads.
            row.password_hash = event.password_hash
            row.credentials_changed_at = event.occurred_at
            return
        raise TypeError(f"Unsupported club account event {event!r}")

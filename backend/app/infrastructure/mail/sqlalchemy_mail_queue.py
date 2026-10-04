from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.mail import OutgoingMessage, QueuedMail
from app.infrastructure.mail.mail_queue_model import MailQueueORM
from app.kernel import Instant
from app.shared.ids import new_uuid


class SqlAlchemyMailQueue:
    """``MailQueue`` and ``PendingMail`` over ``mail_queue``.

    **Both sides of one table**, in the session they are given and without
    committing it: a use case's ``enqueue`` commits with the act that wrote the
    email, and the worker commits after each mark.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(self, message: OutgoingMessage, *, at: Instant) -> None:
        self._session.add(
            MailQueueORM(
                id=new_uuid(),
                kind=message.kind,
                recipient=message.to,
                subject=message.subject,
                text_body=message.text,
                html_body=message.html,
                queued_at=at,
            )
        )
        await self._session.flush()

    async def next_due(self, *, now: Instant) -> Optional[QueuedMail]:
        result = await self._session.execute(
            select(MailQueueORM)
            .where(
                MailQueueORM.sent_at.is_(None),
                MailQueueORM.given_up_at.is_(None),
                or_(
                    MailQueueORM.next_attempt_at.is_(None),
                    MailQueueORM.next_attempt_at <= now,
                ),
            )
            .order_by(MailQueueORM.queued_at, MailQueueORM.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if row.text_body is None or row.html_body is None:
            # A pending row whose body is gone would be sent as an empty email.
            # Nothing writes one, so this is a broken precondition.
            raise RuntimeError(f"queued mail {row.id} has no body to send")
        return QueuedMail(
            id=row.id,
            message=OutgoingMessage(
                kind=row.kind,
                to=row.recipient,
                subject=row.subject,
                text=row.text_body,
                html=row.html_body,
            ),
            attempts=row.attempts,
        )

    async def mark_sent(self, mail_id: UUID, *, at: Instant) -> None:
        await self._session.execute(
            update(MailQueueORM)
            .where(MailQueueORM.id == mail_id)
            .values(
                sent_at=at,
                text_body=None,
                html_body=None,
                next_attempt_at=None,
            )
        )

    async def mark_failed(
        self,
        mail_id: UUID,
        *,
        attempts: int,
        error: str,
        retry_at: Optional[Instant],
        at: Instant,
    ) -> None:
        values: dict[str, object] = {
            "attempts": attempts,
            "last_error": error,
            "next_attempt_at": retry_at,
        }
        if retry_at is None:
            values.update(given_up_at=at, text_body=None, html_body=None)
        await self._session.execute(
            update(MailQueueORM).where(MailQueueORM.id == mail_id).values(**values)
        )

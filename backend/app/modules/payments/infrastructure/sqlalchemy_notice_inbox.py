"""The notice inbox, over its table.

A read and then a write, in the caller's transaction. **Two deliveries of one
notice racing each other** both read nothing, and the second write meets the
primary key: its transaction fails, the endpoint answers an error, the provider
sends the notice again later — and that delivery finds the row. Nothing is
applied twice, and nothing here has to know which database it is on.
"""

from __future__ import annotations

from typing import final

from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant
from app.modules.payments.infrastructure.payment_models import PaymentNoticeORM


@final
class SqlAlchemyNoticeInbox:
    """``NoticeInbox`` over ``payment_notices``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def first_reading(self, notice_id: str, *, kind: str, at: Instant) -> bool:
        if await self._session.get(PaymentNoticeORM, notice_id) is not None:
            return False
        self._session.add(PaymentNoticeORM(notice_id=notice_id, kind=kind, read_at=at))
        return True

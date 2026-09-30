"""The Payments context's two tables: a projection, and the notice inbox.

**``payment_customers`` is a projection** of the Payment method streams, written
by the repository's ``save`` in the caller's transaction, as a club's search row
is: which player a customer at the provider is. A notice names a customer and
never a player, and this is how it finds its stream without asking the provider.

**``payment_notices`` is the webhook's inbox**, the outbox's mirror: the id of
every notice already read, written in the transaction that acted on it, so a
second delivery of the same notice finds its row and does nothing. It holds no
domain fact — only *that* a notice was read, its kind and when — which is why it
is a table and not a stream (``docs/adr/0190``).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class PaymentCustomerORM(Base):
    """A player's customer at the payment provider. One each, for ever."""

    __tablename__ = "payment_customers"

    customer_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), nullable=False, unique=True
    )


class PaymentNoticeORM(Base):
    """One provider notice, read."""

    __tablename__ = "payment_notices"

    notice_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    kind: Mapped[str] = mapped_column(String(128), nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

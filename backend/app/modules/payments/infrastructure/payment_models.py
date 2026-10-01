"""The Payments context's tables: two projections, and the notice inbox.

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
from typing import Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
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


class SeatChargeORM(Base):
    """One seat charge, as receipts, notices and the next fill read it — a
    **projection** of its stream, written by the repository's ``save`` in the
    caller's transaction (#541). ``status`` is the stream's fold, kept here so a
    list of receipts is one read; the stream stays the record."""

    __tablename__ = "seat_charges"
    __table_args__ = (
        CheckConstraint(
            "status IN ('AUTHORISED', 'FAILED', 'TAKING', 'CAPTURED', 'RELEASING', "
            "'CANCELLED')",
            name="ck_seat_charges_status",
        ),
        Index("ix_seat_charges_game_id", "game_id"),
        Index("ix_seat_charges_player_id_taken_at", "player_id", "taken_at"),
        Index("ix_seat_charges_payment_id", "payment_id"),
    )

    charge_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    #: The proposal that filled — its booking's id too.
    game_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    club_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount_grosze: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    taken_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

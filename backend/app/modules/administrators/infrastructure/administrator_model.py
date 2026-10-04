"""The ``administrators`` row — the projection of every Administrator's stream.

Written beside the event in the same transaction (``docs/adr/0184`` §1): the
stream is the record. **One column is not an event's**: ``last_used_at``, when
the administrator profile was last used, which the guard moves at most once an
hour — a use is not a fact any context reads, so it earns no event.

``(club_id, email)`` is unique, because there is exactly one Administrator per
club and email — inviting a removed person again continues their stream and
their row.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class AdministratorORM(Base):
    __tablename__ = "administrators"
    __table_args__ = (
        UniqueConstraint("club_id", "email", name="uq_administrators_club_email"),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("clubs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    account_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True, index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reset_pending: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

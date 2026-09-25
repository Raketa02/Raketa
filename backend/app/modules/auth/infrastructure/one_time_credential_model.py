from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class OneTimeCredentialORM(Base):
    """One issued link-and-code, **as hashes** (``docs/adr/0184`` §3).

    A plain table and never an event stream: a row expires, and it can be
    purged. Nothing here can be read back into a link or a code — the token and
    the ticket are SHA-256 digests of 256 random bits, and the code is a
    password-hasher hash — so a copy of this table opens nothing.

    ``subject_id`` is not a foreign key because what it names depends on the
    purpose: a User or a Club account for a reset, an Administrator for an
    invitation. ``audience`` says which surface may use it.

    ``issued_at`` is written from the application's clock rather than by the
    database, because the throttle and a claim's look-back both count from it.
    """

    __tablename__ = "one_time_credentials"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_one_time_credentials_token_hash"),
        UniqueConstraint("ticket_hash", name="uq_one_time_credentials_ticket_hash"),
        Index(
            "ix_one_time_credentials_email",
            "email",
            "purpose",
            "audience",
            "issued_at",
        ),
        Index(
            "ix_one_time_credentials_subject",
            "subject_id",
            "purpose",
            "audience",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    audience: Mapped[str] = mapped_column(String(16), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    wrong_codes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ticket_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ticket_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

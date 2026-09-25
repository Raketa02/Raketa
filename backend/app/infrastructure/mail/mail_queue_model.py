from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class MailQueueORM(Base):
    """One email between the act that wrote it and the relay that took it
    (``docs/adr/0186`` §2).

    **The body is the secret**, so it is the one thing that does not stay:
    ``text_body`` and ``html_body`` are cleared the moment the message is sent or
    given up on. What stays is what a person debugging delivery needs — the
    kind, the recipient, the subject, when it was queued and sent, how many
    attempts it took and the last error.

    ``next_attempt_at`` is empty until a send fails, which is what makes a new
    message due at once whatever clock queued it.
    """

    __tablename__ = "mail_queue"
    __table_args__ = (
        Index(
            "ix_mail_queue_pending",
            "sent_at",
            "given_up_at",
            "queued_at",
            postgresql_where=text("sent_at IS NULL AND given_up_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    text_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    next_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    given_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

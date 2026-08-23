"""The table behind ADR-0030's command log.

One row per destructive command that has been applied once, under the key its
client chose for it. **Not an event and not history**: it answers *did I already
do this, and what happened* for twenty-four hours and is then rubbish. It is
therefore an ordinary table with an ordinary unique constraint rather than a
stream, and the one thing on it that matters is that the constraint is the
**key ADR-0030 names** — ``(command, idempotency key)`` — so a second client
choosing the same key collides rather than quietly applying its command.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class CommandLogORM(Base):
    """A destructive command, its key, and what it did."""

    __tablename__ = "command_log"
    __table_args__ = (
        # Named, and the name matters: `tests/unit/test_command_log.py` compares
        # this table's DDL with the migration's string for string, and an
        # unnamed constraint on one side is a difference that reads as an
        # accident either way round.
        PrimaryKeyConstraint("command", "key", name="pk_command_log"),
        # The prune's index, and it is on the command as well as the moment:
        # expiry is swept per command on that command's own write, so a busy
        # act never walks another act's rows.
        Index("ix_command_log_expiry", "command", "recorded_at"),
    )

    # ADR-0030's key, **as the primary key** rather than beside one: a surrogate
    # id here would be a second identity for a row whose whole content is its
    # key, and a unique constraint alongside it would be the same index twice.
    command: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    # What happened, as the short label its command reads back. A departure's is
    # an `Outcome` value; the column is a plain string because the log is
    # cross-cutting and must not import one command's vocabulary to store
    # another's.
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

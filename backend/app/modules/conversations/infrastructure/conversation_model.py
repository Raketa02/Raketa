"""The conversation table. **One row per room, and it exists for the sequence.**

The stream is in ``event_store`` beside every other aggregate's; this row is not
a projection of it and holds nothing a reader draws. It is here for three things
``docs/adr/0147`` §2 asks for and one the list read asks for.

- **``last_seq`` is the allocator.** A gapless per-conversation sequence is
  ``last_seq + 1`` read and written **under this row's lock**, inside the
  appending transaction. Not a Postgres sequence object, which is documented not
  to be gapless — aborts and crashes leave holes — and not a timestamp, which
  ``docs/adr/0097`` disqualified when it found ``func.now()`` is transaction-start
  time, identical across a transaction and not unique.
- **The lock is the row.** ``SELECT … FOR UPDATE`` on one row serialises appends
  at a contention of two-to-four members, which is nil. It is also what makes the
  total order the aggregate's own fact rather than a database object's side
  effect.
- **It is the value the live channel publishes**, with no second read in the
  publish path.
- **``booking_id`` is unique**, which is what makes *one booking is one room* an
  invariant the database holds rather than a race between two deliveries
  arriving in one poll. It was ``challenge_id`` until #575, when a room stopped
  being opened by anything but a booked game.

**``game_id`` is nullable and unique.** Unique because one booking is one game is
already ``games``' invariant and a second room claiming a game would be this
context contradicting it. Nullable for the rooms a challenge's first acceptance
opened before a game existed — nothing opens one any more, and a booked game's
room is born with its game.

**Nothing derived is here.** No member list — membership is derived from the
game's line-up (``docs/adr/0146`` §7) — no standing, no unread mark, and no last
entry: the entries are the stream's.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class ConversationORM(Base):
    """One room's identity and its sequence allocator."""

    __tablename__ = "conversation"
    __table_args__ = (
        # The list read's only index: every room filed under the booking of one
        # of the games this player is on.
        Index("ix_conversation_booking_id", "booking_id", unique=True),
        Index("ix_conversation_game_id", "game_id", unique=True),
        # **A check constraint, not a convention.** ``seq`` 1 is the beginning of
        # the conversation, so a room has landed nothing or it has landed a
        # positive count of things; a negative one would make the gapless promise
        # unfalsifiable.
        CheckConstraint("last_seq >= 0", name="ck_conversation_last_seq_is_a_count"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True
    )
    #: The booking whose game opened this room, which is what lets the list read
    #: find every room a player is in through the games they are on.
    booking_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    #: The game this room is about.
    game_id: Mapped[UUID | None] = mapped_column(UUIDType(binary=False), nullable=True)
    sport: Mapped[str] = mapped_column(String(50), nullable=False)
    #: **The allocator.** Zero in a room where nothing has landed yet, which is a
    #: real state: the opening is not a line.
    last_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

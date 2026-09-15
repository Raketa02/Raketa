"""The deck-reset table. **Append-only, unexpiring, and returned by no route.**

One row per press of *Show them again* (``docs/adr/0169`` §5): whose deck, which
sport, and when. It is the moment and nothing else — what the reset cleared is
derived at the next deal from the pass record, the search record and the game,
each read against this moment, so a column listing any of it would be a copy of
another table free to disagree with it.

**A surrogate primary key, on the pass row's own argument.** ``(player, sport)``
would collapse a second press into the first, and every reset is a moment the
``PASS_SUPPRESS`` falsifier has to exclude from its sample — a deal between two
presses was shaped by the first, and only the rows can say so. Two rows are two
facts with two moments.

**No event and no outbox**, on the argument the four ledgers beside it were
exempted under and the amendment that made this the fifth: a small fact with no
life story, and nothing subscribes to one being written. The deal reads the
latest moment on its next run, which is the whole of what happens.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class DeckResetORM(Base):
    """One *Show them again*, dated."""

    __tablename__ = "deck_reset"
    __table_args__ = (
        # The deal's read: *when did this player last reset this sport's deck*.
        # The moment is in the index so the latest is the end of one keyed
        # range rather than a scan over every press a player ever made.
        Index("ix_deck_reset_player", "player_id", "sport", "reset_at"),
    )

    #: A surrogate, because the fact is the **press** and not the deck. See the
    #: module docstring: a natural key would make a second press
    #: unrepresentable, and two presses a week apart are two facts.
    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    #: Sport-scoped, because the button is on a deck and a deck is one sport.
    sport: Mapped[str] = mapped_column(String(50), nullable=False)
    reset_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

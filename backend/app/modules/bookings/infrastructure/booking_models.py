"""The Bookings context's two projections of the booking streams (#541).

**``bookings``** is one row per booking: where and when, so a club's taken
court hours are one read by club and start (the screens C5). **``booking_seats``**
is one row per player on one, so a player's booked games are one read by
player. Both are written beside the events in the act's own transaction; the
stream is the record.

**A court hour is held by one booking**, and the unique index says so: two
cards filling at once on the last court of an hour cannot both book it — the
second's transaction fails, and nothing it held is taken. **A booking waiting
for its club holds its court as a booked one does** (#543), and **a booking
called off holds nothing**: the index is partial, so the hour is the club's to
sell again the moment a request is refused, unanswered or withdrawn — and the
called-off row stays, since its players still read why.

**A leaver keeps their seat row, marked with when they left** (#544): the
record reads who ever held a seat — a mark is a leaver's — while every read of
the game as it stands now reads only the seats still held.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class BookingORM(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index(
            "ux_bookings_court_id_start",
            "court_id",
            "start",
            unique=True,
            postgresql_where=text("state <> 'CALLED_OFF'"),
            sqlite_where=text("state <> 'CALLED_OFF'"),
        ),
        Index("ix_bookings_club_id_start", "club_id", "start"),
        # The requests whose answer is due — the timeout job's read.
        Index("ix_bookings_state_answer_by", "state", "answer_by"),
        # The games whose cut-off came with a seat open — the cut-off job's.
        Index("ix_bookings_state_cut_off", "state", "cut_off"),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    pool_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    club_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    court_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    sport: Mapped[str] = mapped_column(String(32), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    share_grosze: Mapped[int] = mapped_column(Integer, nullable=False)
    cut_off: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: ``WAITING_FOR_THE_CLUB``, ``BOOKED``, ``SEAT_OPEN`` or ``CALLED_OFF``.
    state: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="BOOKED"
    )
    #: The Game it opened — ``NULL`` until an On request club says yes.
    game_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True
    )
    #: When the club's answer is due, on a booking that was ever put to it.
    answer_by: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    booked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    #: When the first seat still open on it opened — ``NULL`` while every seat
    #: is held (#544). A seat open since before the cut-off is what calls a
    #: game off at it.
    open_since: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BookingSeatORM(Base):
    """One player on one booked game, and the side they were drawn on."""

    __tablename__ = "booking_seats"
    __table_args__ = (Index("ix_booking_seats_player_id", "player_id"),)

    booking_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: ``A`` — the first side — or ``B``.
    side: Mapped[str] = mapped_column(String(1), nullable=False)
    #: When they left the booked game, or ``NULL`` while the seat is theirs.
    left_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

"""The Bookings context's two projections of the booking streams (#541).

**``bookings``** is one row per booking: where and when, so a club's taken
court hours are one read by club and start (the screens C5). **``booking_seats``**
is one row per player on one, so a player's booked games are one read by
player. Both are written beside the events in the act's own transaction; the
stream is the record.

**A court hour is held by one booking**, and the unique index says so: two
cards filling at once on the last court of an hour cannot both book it — the
second's transaction fails, and nothing it held is taken. **A booking called
off holds nothing**: the index is partial, so the hour is the club's to sell
again the moment the game is called off — and the called-off row stays, since
its players still read why.

**A leaver keeps their seat row, marked with when they left** (#544): the
record reads who ever held a seat — a mark is a leaver's — while every read of
the game as it stands now reads only the seats still held. **A seat whose
holding was refused is marked until when its card may be fixed** (#639).

**``booking_invitations``** is one row per invited seat of a friends game
(#751): the friend's Home reads the ones still waiting, and the invitations job
the ones whose time is up. **``bookings.sender_id``** names a friends game's
sender, so the friends games waiting on them are counted.

**``booking_keeps``** is one row per rescuer whose share was refused and a
seat kept for them (#640) — not a seat of theirs, so never a ``booking_seats``
row: the time-to-pay job reads the keeps run out by it, and a rescuer's *To
confirm* rows theirs. Run out, the row stays, marked, while their refused
payment is still theirs to confirm; it goes when they take a seat, and with the
game.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, text
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
        # The games whose cut-off came with a seat open — the cut-off job's.
        Index("ix_bookings_state_cut_off", "state", "cut_off"),
        # A day's new bookings — the club's daily summary (#548).
        Index("ix_bookings_booked_at", "booked_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    pool_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    club_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    court_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    sport: Mapped[str] = mapped_column(String(32), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    share_grosze: Mapped[int] = mapped_column(Integer, nullable=False)
    cut_off: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: ``BOOKED``, ``SEAT_OPEN`` or ``CALLED_OFF``.
    state: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="BOOKED"
    )
    #: The Game it opened. Nullable from On request, when a booking waited for
    #: its club's yes before it had one (#543, removed by #669).
    game_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True
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
    #: A friends game's sender (#751) — ``NULL`` on every game a fill booked.
    sender_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True, index=True
    )


class BookingSeatORM(Base):
    """One player on one booked game, and the side they were drawn on."""

    __tablename__ = "booking_seats"
    __table_args__ = (
        Index("ix_booking_seats_player_id", "player_id"),
        # The times to fix the card that ran out — the time-to-pay job's read
        # (#639).
        Index("ix_booking_seats_card_to_fix_until", "card_to_fix_until"),
    )

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
    #: Their holding was refused, and their time to fix the card runs until
    #: then (#639) — ``NULL`` while there is nothing to fix.
    card_to_fix_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BookingKeepORM(Base):
    """A seat kept on one booked game for one rescuer whose share was refused,
    and until when (#640)."""

    __tablename__ = "booking_keeps"
    __table_args__ = (
        Index("ix_booking_keeps_player_id", "player_id"),
        # The keeps run out — the time-to-pay job's read.
        Index("ix_booking_keeps_until", "until"),
    )

    booking_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Its running out is recorded: out of the time-to-pay job's read.
    ran_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class BookingInvitationORM(Base):
    """One invited seat of a friends game (#751): the friend, the side the card
    drew them on, until when they may answer, and how they did — or an
    invitation into an empty seat, on that seat's side (#752)."""

    __tablename__ = "booking_invitations"
    __table_args__ = (
        Index("ix_booking_invitations_player_id", "player_id"),
        # The invitations whose time is up — the invitations job's read.
        Index("ix_booking_invitations_answer_until", "answer", "until"),
    )

    booking_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: ``A`` — the first side — or ``B``.
    side: Mapped[str] = mapped_column(String(1), nullable=False)
    until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: ``WAITING``, ``ACCEPTED``, ``DECLINED``, ``RAN_OUT`` — or ``TAKEN``,
    #: somebody else took the seat first (#752).
    answer: Mapped[str] = mapped_column(String(16), nullable=False)
    answered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

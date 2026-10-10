"""The Notifications context's four tables — **projections all four**, written
by the repositories' ``save`` beside the events in the act's own transaction;
the streams are the record (#549, #621).

``notification_preferences`` is each player's three choices, one row per player
who ever chose — so *who in this pool wants Fill in alerts* is one read, and a
player with no row is at the defaults. ``push_devices`` is which player each
phone is pushed to as, one row per phone, so a phone signing in as somebody
else is found and moved — and the one place a phone's push token is kept,
which the stream may not hold. ``notices`` is the recent list: one row per notice
given, and how many of its kind the day gathered into it. ``notices_opened`` is
when each player last opened it, and the newest notice it held then — what the
bell's number counts from.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class NotificationPreferencesORM(Base):
    """A player's three choices, as their stream leaves them."""

    __tablename__ = "notification_preferences"

    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    you_complete_it: Mapped[bool] = mapped_column(Boolean, nullable=False)
    challenges_for_you: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fill_in_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False)


class PushDeviceORM(Base):
    """One phone, and the player it is pushed to as — **the only place its
    push token is kept**: the stream names a phone by the token's SHA-256, since
    the token would let anybody holding it push to the phone (ADR-0184 §4). A
    phone removed is a row deleted, and its token is gone."""

    __tablename__ = "push_devices"

    #: The token's SHA-256 — the name the stream knows the phone by.
    device: Mapped[str] = mapped_column(String(64), primary_key=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), nullable=False, index=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class NoticeORM(Base):
    """One notice given, as the recent list reads it."""

    __tablename__ = "notices"
    __table_args__ = (
        # The list's read: a player's, newest first.
        Index("ix_notices_player_id_given_at", "player_id", "given_at", "sequence_no"),
        # The bell's number: a player's, since the last visit.
        Index("ix_notices_player_id_sequence_no", "player_id", "sequence_no"),
    )

    notice_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    game_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    pool_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    sport: Mapped[str] = mapped_column(String(16), nullable=False)
    game_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    club_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    opens: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_grosze: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    #: The players it names, comma-separated, in the order it names them.
    people: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reason: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    #: When it was given — or when the day last gathered a notice into it, which
    #: is what moves it up the list.
    given_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Its event's place in the whole store — what orders two notices given at
    #: one instant, which a fill's or a leaving's often are, and what says
    #: whether it reached the list since the player last opened it.
    sequence_no: Mapped[int] = mapped_column(BigInteger, nullable=False)
    #: How many notices of its kind the day gathered into it.
    gathered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: Of the player's own act: born seen, never counted on the bell.
    own: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    #: The deadline it names — when the club must answer, on *It's a game!* at
    #: a club that confirms.
    until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    #: Told to a player who had left the game, in a leaver's words (Q108).
    you_left: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class NoticesOpenedORM(Base):
    """When a player last opened their recent notices, as their bell's stream
    leaves it."""

    __tablename__ = "notices_opened"

    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: The newest place in the store among the player's notices the list held
    #: when it was opened — ``-1`` for none. A notice whose own place is past
    #: it reached the list since: given, or gathered into and moved up.
    seen_through: Mapped[int] = mapped_column(BigInteger, nullable=False)

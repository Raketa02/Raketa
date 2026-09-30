"""The Proposals context's three tables: the pools, and two projections of the
proposal streams.

**``pools`` is a table of its own** (the screens C5): the pool is first-class,
and a proposal's ``pool_id`` references it rather than a group. It is a
**projection** too — a pool holds no fact of its own, a group's being its group
— written by the first proposal made in it, under the group's id. The kind
decides what the pool is made of, and a check constraint holds the one kind
there is.

**``proposals`` and ``proposal_people`` are projections**, written beside the
events in the act's own transaction, as a group's are (``docs/adr/0183`` §1) —
the stream is the record. ``proposals.ended`` is the recorded ending and never
the whole answer: a proposal past its ``book_by`` is over whether or not the
sweep has written it, so every live read compares ``book_by`` with its clock too.

``proposal_people`` is **one row per person the game is anything to** — dealt a
version, In, or gone — keyed by the game and the person, since each person is on
one version at most. ``version`` is ``NULL`` for somebody In who was never dealt
one: a poster.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class PoolORM(Base):
    """One pool. A group's has the group's own id."""

    __tablename__ = "pools"
    __table_args__ = (CheckConstraint("kind IN ('GROUP')", name="ck_pools_kind"),)

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProposalORM(Base):
    """One proposed game, as the live reads and the sweep read it."""

    __tablename__ = "proposals"
    __table_args__ = (
        CheckConstraint(
            "ended IS NULL OR ended IN ('EXPIRED', 'WITHDRAWN')",
            name="ck_proposals_ended",
        ),
        # The sweep's read: unrecorded endings, by book-by.
        Index("ix_proposals_ended_book_by", "ended", "book_by"),
        # Court hours are read by club and start (the screens C5).
        Index("ix_proposals_club_id_start", "club_id", "start"),
        Index("ix_proposals_pool_id_start", "pool_id", "start"),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    pool_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("pools.id", ondelete="RESTRICT"),
        nullable=False,
    )
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    poster_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True
    )
    sport: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    club_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    share_grosze: Mapped[int] = mapped_column(Integer, nullable=False)
    book_by: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    made_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)


class ProposalPersonORM(Base):
    """One person on one proposed game: the version they were dealt, and their
    answer — ``YES`` while In, ``NO`` or ``WITHDRAWN`` once gone, ``NULL`` while
    they have not swiped."""

    __tablename__ = "proposal_people"
    __table_args__ = (
        CheckConstraint(
            "answer IS NULL OR answer IN ('YES', 'NO', 'WITHDRAWN')",
            name="ck_proposal_people_answer",
        ),
        Index("ix_proposal_people_player_id_answer", "player_id", "answer"),
    )

    proposal_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("proposals.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    answer: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    answered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

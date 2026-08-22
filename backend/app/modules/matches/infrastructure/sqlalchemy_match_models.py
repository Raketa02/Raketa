"""Three tables: the match, its seats, and the holes departures left.

**No constraint here is a decision the way the exclusion constraint is** — a
match contends for nothing that another match could take, because what is
contended is the *court*, and that is enforced one context over
(``app/modules/courts/``). What these tables carry instead is ADR-0034's own
guarantee: **a version column**, which is where *"two concurrent writers cannot
interleave: one wins, one retries"* actually lives.

**The seats are rows and the count is not stored.** A sport is sold in a fixed
number of seats, so they are written once with the match and thereafter only
occupied and emptied — which is what lets *how full is this* be a count over
rows rather than a number somebody has to remember to decrement. The unique
index on ``(match_id, seat_index)`` is the database's half of *a seat is its
position*, and the one on ``(match_id, player_id)`` is the database's half of
*one player, one seat*: partial over the occupied rows, because every empty seat
has a null player and a plain unique index would allow exactly one of them.

**A vacancy is filled, never deleted**, the same shape as a released
reservation and an effective-dated series' closed row. *When did this match lose
a player, and when did it get one back* is a support question, and a row that
vanishes cannot answer it.

**The score is a JSON column and not a fourth table.** It is a *value* — no
identity, no lifecycle, never read or written apart from the match — and giving
it row identity would be inventing one. The list of sets is stored as the pairs
of integers it crosses the wire as (``Raketa02/Raketa#74``), never as a display
string, so no rendering decision is frozen into history.
"""

import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base

#: One player holds at most one seat in a match — but every *empty* seat has a
#: null player, and there are three of them in a fresh padel match. The index is
#: therefore partial over the occupied rows; a plain unique index would allow one
#: empty seat and refuse the rest.
SEAT_OCCUPIED = "player_id IS NOT NULL"

#: The name, so a test can drop it and get a real negative control.
ONE_SEAT_PER_PLAYER = "uq_match_seats_one_per_player"

#: A row is **due to be looked at** exactly when it names a moment. Written as
#: the column being present rather than as a SQL restatement of *non-terminal*,
#: which the four cancellation flags would be: that copy is a second ladder in
#: the schema (ADR-0040), and it fails in the silent direction — indexing a row
#: nothing will look at costs a page, while missing one means a court is never
#: given back. A terminal match stores `NULL` because `next_wake` says `None`
#: for one, so the narrower predicate is *implied* by the wider one rather than
#: maintained beside it. It is also true of a settled match past its result
#: window, which is not terminal and has nothing left to wake for.
SCHEDULED = "next_wake_at IS NOT NULL"

#: The name, so a test can drop it and get a real negative control.
DUE_WAKE = "ix_matches_due_wake"


class MatchORM(Base):
    """The record: what was posted, what has been declared, and a version."""

    __tablename__ = "matches"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )

    # -- Constitutive -------------------------------------------------------
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    #: What was bought, and what the price attaches to. `RESTRICT` because a
    #: category is retired and never deleted.
    category_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("club_court_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sport: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #: What one seat costs, in integer grosze (ADR-0023).
    share_grosze: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    counted: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    created: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    pay_model: Mapped[str] = mapped_column(sa.String(16), nullable=False)

    #: The club's four hold-policy fields **as they stood when the match was
    #: posted**, honoured as booked (ADR-0077). Copied rather than joined, which
    #: is what makes a situation one row-set away.
    policy_window_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    policy_join_cut_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    policy_max_hold_age_minutes: Mapped[Optional[int]] = mapped_column(
        sa.Integer, nullable=True
    )
    policy_prob_hold: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)

    #: Mutable, deliberately (ADR-0032). Indexed because every read of Now is a
    #: window over it.
    start: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True
    )

    # -- Occupancy ----------------------------------------------------------
    transferring: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
    open_seats: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0, server_default="0"
    )

    # -- Allocation ---------------------------------------------------------
    held_since: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    released_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    inventory_lost: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )

    # -- Crossing -----------------------------------------------------------
    committed_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    # -- Declaration --------------------------------------------------------
    court_locked: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
    club_extended: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
    club_cancelled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
    weather: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
    no_show: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )

    #: The two receipts. Not a sixth kind — the situation derives without them,
    #: and they record only that the money moved (ADR-0034).
    form_cancelled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
    checkpoint_cancelled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )

    #: The score's four facts: what is on the table, who put it there, how many
    #: proposals there have been, and whether it has settled. A count, never a
    #: sequence — the conversation belongs to the announcements.
    score_sets: Mapped[Optional[Any]] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    score_by: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True
    )
    proposals: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0, server_default="0"
    )
    result_agreed: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )

    version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    # -- Schedule -----------------------------------------------------------
    # Last, and physically so: migration `0010` adds them with `ALTER TABLE`,
    # which appends, and `tests/unit/test_matches_migration.py` compares the two
    # descriptions of this table DDL string for string.
    #
    #: **The one derived thing this table stores, and ADR-0076 is the licence.**
    #: Every other column passes *a reader cannot derive this*; these two fail it
    #: outright — `kernel.next_wake` computes them from the row they sit on. What
    #: buys them their place is that the question they answer is asked the other
    #: way round: not *when does this match next change* for one match in hand,
    #: but *which matches change in the next second* over the whole table. A
    #: function cannot be indexed; a column can, and a partial one over the rows
    #: that have a moment is the whole timekeeper.
    #:
    #: **Never serialised onto a card.** ADR-0076 says so in terms: it is the
    #: earliest instant *anything* could differ, chosen by a `min()` over
    #: candidates the player is not being told about, and pointing a countdown at
    #: it drifts the number away from the words above it (ADR-0053). It is
    #: internal, and `tests/unit/test_now_contract_document.py` is what keeps it
    #: off the wire.
    next_wake_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    #: A label, and half of `{matchId}:{threshold}:{scheduledFor}`. **Nothing
    #: branches on it** — a wake is a look, and the handler re-derives.
    wake_reason: Mapped[Optional[str]] = mapped_column(sa.String(24), nullable=True)

    __table_args__ = (
        sa.Index(
            DUE_WAKE,
            "next_wake_at",
            sqlite_where=sa.text(SCHEDULED),
            postgresql_where=sa.text(SCHEDULED),
        ),
    )


class MatchSeatORM(Base):
    """One seat: its position, who is on it, and whether it is paid for."""

    __tablename__ = "match_seats"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    #: The seat's identity within the match, and the order the record keeps.
    seat_index: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #: Not a foreign key: a player lives behind a projection in another context,
    #: and Matches never reads that context's write model.
    player_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True, index=True
    )
    paid: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
    taken_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint("match_id", "seat_index", name="uq_match_seats_position"),
        sa.Index(
            ONE_SEAT_PER_PLAYER,
            "match_id",
            "player_id",
            unique=True,
            sqlite_where=sa.text(SEAT_OCCUPIED),
            postgresql_where=sa.text(SEAT_OCCUPIED),
        ),
    )


class MatchVacancyORM(Base):
    """A hole a departure left, and when it closed if it has.

    No amount, no outcome and no player: what the leaver recovered is her
    departure's fact, on an axis of its own (ADR-0033). Storing a settlement
    beside a hole is exactly the welding those two decisions refuse.
    """

    __tablename__ = "match_vacancies"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seat_index: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    vacated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    filled_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

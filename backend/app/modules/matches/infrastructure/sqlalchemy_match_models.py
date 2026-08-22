"""Five tables: the match, its seats, the holes left, the leavers, and the claims.

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

**The departures are a fourth table and not two more columns on the third.** A
hole and a settlement are two facts with two lifecycles (ADR-0033): the hole
closes when anybody takes the seat, the settlement closes when nobody can any
more, and a filler routinely closes one while settling a *different* leaver's
money. Two rows are what makes that expressible; a single row would be the
scalar the two ADRs were written to replace.

**A seat claim is a fifth table and not three columns on the second.** It is
deliberately *not* a fact about a seat (ADR-0081): the seat is untouched while
somebody is buying it, and columns on ``match_seats`` would be that decision
reversed in the schema. It is also many-to-one over time — a seat can be claimed,
let go and claimed again, and each of those has its own five minutes and its own
receipt — which is a shape a row per seat cannot hold at all.

**The score is a JSON column and not a sixth table.** It is a *value* — no
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

#: A claim nobody has written a receipt for. The narrow index over these is what
#: answers *is this player already buying a seat*, and it is partial for the
#: reason every other partial index here is: the ended rows are the overwhelming
#: majority within minutes of a busy evening, and none of them is ever an answer.
#:
#: **It says `ended_at IS NULL` and the query says more.** *Live* is unended
#: **and** not yet expired, and the second half cannot be an index predicate
#: because it needs a clock. That asymmetry is the right way round: the index
#: over-covers by the rows a reaper has not reached yet, and the query composes
#: the truth on top of it — where a *unique* index on the same predicate would
#: have to spell *live* as *unended* and would refuse a player on the strength of
#: a row nobody had got round to closing.
CLAIM_UNENDED = "ended_at IS NULL"

#: The name, so a test can drop it and get a real negative control.
UNENDED_CLAIMS = "ix_match_seat_claims_unended"

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


class MatchDepartureORM(Base):
    """One leaver: what she was promised, what she paid, and what she got.

    ``amount_grosze`` is **null when nothing was taken**, and that is the
    storage half of ADR-0072's two payload forms rather than an optional field
    smuggled back in. The domain reconstructs the union from it and refuses the
    two rows that cannot mean anything — an amount on a reversal, and a reversal
    with no amount is the only reversal there is. A zero was refused outright:
    *nothing was taken* and *nothing has come back yet* are opposite sentences
    and a zero cannot tell them apart.

    ``outcome`` is null exactly while the departure is unsettled, and it only
    ever moves **upward** thereafter. Nothing in the schema enforces that — a
    ``CHECK`` cannot see the old value — so it is a property of the domain type,
    which has no operation that lowers one.

    ``quoted`` is stored rather than re-derived. Every deadline hangs off
    ``matches.start`` and a consented shift moves all five, so *what was she
    shown* stops being answerable from the record the moment the match moves.

    No unique index on ``(match_id, player_id)``: a player may leave, be talked
    back in, and leave again, and each of those is its own departure with its
    own money. The primary key is derived from the match, the seat and the
    instant, which is already exactly *one leaving*.
    """

    __tablename__ = "match_departures"

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
    #: Not a foreign key, for the reason ``match_seats.player_id`` is not one:
    #: a player lives behind a projection in another context.
    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), nullable=False, index=True
    )
    departed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    #: The outcome label she acted on (ADR-0033's **Quote**).
    quoted: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    #: What she paid in, or null because nothing was taken.
    amount_grosze: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    #: Null until settled. Monotonic upward thereafter.
    outcome: Mapped[Optional[str]] = mapped_column(sa.String(16), nullable=True)
    settled_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )


class MatchSeatClaimORM(Base):
    """One player's five minutes in front of one seat, and whether they are over.

    **Ended, never deleted**, like every other child here: the thirty-second
    cooldown is measured from ``ended_at``, so a row that vanished would take the
    cooldown with it — and *why could I not take that seat at 18:03* is a support
    question a missing row cannot answer.

    ``ended_at`` is **when the claim stopped being live**, which for an expiry is
    the moment its five minutes ran out and not the moment a scheduled look
    noticed. A worker that was down for an hour must not extend anybody's thirty
    seconds by an hour, so the domain dates the receipt at the expiry rather than
    at the write.

    **No unique index on ``(match_id, seat_index)`` over the unended rows.** Two
    claims on one seat are impossible, and what makes them impossible is the
    version column on ``matches``: both writers read the same version and the
    second loses on ``rowcount``, which is ADR-0034's concurrency answer doing
    the job it was chosen for. A partial unique index would additionally refuse
    the *legitimate* second claim on a seat whose previous claim expired and has
    not been reaped — and the write that would be refused is the one that reaps
    it.

    ``expires_at`` is stored rather than recomputed from ``claimed_at``: it is
    the fact the match's schedule is armed against and the moment a client counts
    down to, and recomputing it would let a change to the five minutes silently
    move a deadline already announced.
    """

    __tablename__ = "match_seat_claims"

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
    #: Not a foreign key, for the reason ``match_seats.player_id`` is not one:
    #: a player lives behind a projection in another context.
    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), nullable=False
    )
    claimed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.Index(
            UNENDED_CLAIMS,
            "player_id",
            "expires_at",
            sqlite_where=sa.text(CLAIM_UNENDED),
            postgresql_where=sa.text(CLAIM_UNENDED),
        ),
    )

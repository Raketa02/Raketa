"""Two tables, and one constraint that is the whole reason this context exists.

**The exclusion constraint is the decision.** ADR-0035: two reservations may
never overlap on one court, *"enforced by the database, never by read ordering"*.
It is spelled once, here, as ``RESERVATION_EXCLUSION_DDL`` — assembled from four
named constants rather than written as one literal, because **four separate
properties are load-bearing** and each has to be breakable on its own for
`scripts/test-postgres-gates.sh` to prove the assertions above it fire:

- ``ONE_COURT`` scopes it to one court. Without it a club could sell one hour a
  day across its whole site.
- ``OVERLAPS`` is the conflict test. Its neighbouring operator is *adjacent*,
  which is the same constraint meaning the opposite thing: back-to-back
  reservations would collide and overlapping ones would not.
- ``RANGE_BOUNDS`` is half-open. A court freed at 18:00 and taken at 18:00 do
  not overlap, which is what lets ``turnaroundMin`` widen a claim by padding
  rather than by arithmetic on somebody else's row.
- ``LIVE_CLAIM`` is what makes *released, never deleted* affordable. A withdrawn
  hold keeps its row so a court's booking history is answerable, and stops
  claiming the court the instant it is released.

**PostgreSQL only, and that is ADR-0035's own stated cost** — *"the sharpest cost
of the decision"*. SQLite has no `EXCLUDE USING gist`, so the fast suite is
tested against a store that does not enforce this. The split is the one
`backend/README.md` writes down: the ordinary path — scan, pick, claim — runs on
SQLite in milliseconds, and the **race** lives in `tests/integration/`, which is
the directory `Raketa02/Raketa#62` built for exactly this constraint.

It is attached with a dialect-scoped `after_create` listener rather than in
``__table_args__``, because an `ExcludeConstraint` in the metadata would break
`Base.metadata.create_all` on SQLite — and that call is what the entire fast
suite stands on.

**``court_id`` is not a foreign key, and that is not an omission.** A court's
identity lives across the rows of `club_court_catalogue`, whose primary key is
the *row*; ``court_id`` is unique there only among the open rows, which is a
partial unique index and cannot be referenced. The catalogue's own constraint is
what keeps a court from existing twice; this column names one.
"""

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base

#: A live reservation is one that has not been given back. The same shape as the
#: club series' *open row*, and spelled once for the same reason.
LIVE_CLAIM = "released_at IS NULL"

#: `court_id WITH =` needs an equality operator class GiST does not carry for
#: uuid out of the box. `btree_gist` is therefore part of the guarantee rather
#: than an implementation detail — a PostgreSQL image without contrib cannot run
#: this migration, which `tests/integration/` has been asserting since #62.
BTREE_GIST_DDL = "CREATE EXTENSION IF NOT EXISTS btree_gist"

#: The constraint's name, so a test can drop it by name and get a real negative
#: control rather than a copied table.
RESERVATION_EXCLUSION = "ex_reservations_no_overlapping_claim"

#: Scopes the constraint to one court. Without it a club sells one hour a day
#: across its whole site.
ONE_COURT = "court_id WITH ="

#: Half-open. A court freed at 18:00 and taken at 18:00 do not overlap, which is
#: what lets ``turnaroundMin`` widen a claim by padding rather than by arithmetic
#: on somebody else's row.
RANGE_BOUNDS = "[)"

#: The operator that decides a conflict. Its neighbour ``-|-`` is *adjacent*,
#: which is the same constraint meaning the opposite thing.
OVERLAPS = "WITH &&"

#: Four named parts rather than one string, so each of the four properties
#: below can be broken **on its own** — which is what
#: `scripts/test-postgres-gates.sh` does, one mutation per constant, and what a
#: single literal would have made impossible to do precisely.
RESERVATION_EXCLUSION_DDL = (
    f"ALTER TABLE reservations ADD CONSTRAINT {RESERVATION_EXCLUSION} "
    f"EXCLUDE USING gist ({ONE_COURT}, "
    f"tstzrange(claimed_from, claimed_to, '{RANGE_BOUNDS}') {OVERLAPS}"
    f") WHERE ({LIVE_CLAIM})"
)


class ReservationORM(Base):
    """One court, one claimed range, one holder — and a version to race on."""

    __tablename__ = "reservations"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    #: Not a foreign key — see the module docstring.
    court_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), nullable=False, index=True
    )
    #: What was bought, and what is published. `RESTRICT` because a category is
    #: retired and never deleted, so nothing should be able to take one out from
    #: under a reservation that names it.
    category_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("club_court_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    #: The interval the players get. The only one anybody outside is shown.
    played_from: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    played_to: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    #: The interval that excludes everybody else: `played` widened by the club's
    #: turnaround when Raketa created it, and `played` exactly when the club
    #: published it. Stored rather than derived because the policy that produced
    #: it is versioned and may since have changed — and a claim that moved
    #: because a club edited a number would double-book the gap it was widened
    #: for.
    claimed_from: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    claimed_to: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )

    #: `booking` · `match` · `club`. Exactly one holder, and the two id columns
    #: below are the payload of the first two — nullable together with the kind
    #: rather than one nullable column pretending to be both.
    holder_kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True
    )
    match_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True
    )

    #: Released, never deleted. Also the exclusion constraint's predicate.
    released_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


class BookingORM(Base):
    """A player buying a court outright. It **references** a reservation.

    No court and no interval: a copy of either would be a second answer to *when
    is this booked and where*. Everything about the court and the clock is read
    through `reservation_id`, and `tests/unit/test_booking.py` asserts the
    absence, because it is the whole content of *a Booking is not a Reservation*.
    """

    __tablename__ = "bookings"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), nullable=False, index=True
    )
    #: The claim this booking holds — one booking, one reservation.
    reservation_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("reservations.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    #: What the player was quoted, in grosze, at the moment they were quoted it.
    #: A `CourtPrice` is whole złoty by construction; it is stored in grosze
    #: because every other money column in this application is (ADR-0023).
    price_grosze: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    booked_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0, server_default="0"
    )


#: The exclusion constraint, on PostgreSQL and nowhere else. `execute_if` is what
#: keeps `Base.metadata.create_all` working on SQLite, which is what the whole
#: fast suite stands on.
sa.event.listen(
    ReservationORM.__table__,
    "after_create",
    sa.DDL(BTREE_GIST_DDL).execute_if(dialect="postgresql"),
)
sa.event.listen(
    ReservationORM.__table__,
    "after_create",
    sa.DDL(RESERVATION_EXCLUSION_DDL).execute_if(dialect="postgresql"),
)

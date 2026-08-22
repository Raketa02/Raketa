"""create Courts and Bookings: reservations exclusive by overlapping interval

A reservation is one court and one time range, and two of them may never overlap
on one court (ADR-0035). The rule is enforced by an **exclusion constraint**, not
by read ordering and not by a unique index on a slot's start — the second is the
dead repo's `#127`, which lets 14:00–15:30 and 14:30–16:00 both land on court 3.

**PostgreSQL only, and that is the decision's own stated cost.** `EXCLUDE USING
gist` has no SQLite equivalent, so this migration guards the statement by dialect
and `tests/integration/test_reservation_exclusion.py` is where the guarantee is
asserted against a real database.

`btree_gist` is created here because `court_id WITH =` needs an equality operator
class GiST does not carry for uuid out of the box. It is part of the guarantee
rather than an implementation detail: a PostgreSQL image without contrib cannot
run this migration.

A Booking holds a reservation and is not one, so `bookings` carries no court and
no interval — only the claim it holds, who bought it, and what they were quoted.

Revision ID: 0008_courts
Revises: 0007_clubs
Create Date: 2026-08-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0008_courts"
down_revision = "0007_clubs"
branch_labels = None
depends_on = None

#: A live reservation is one that has not been given back — released, never
#: deleted, so a court's booking history stays a query over reservations. It is
#: the same string `app/modules/courts/infrastructure/sqlalchemy_court_models.py`
#: declares, and `tests/unit/test_courts_migration.py` fails if the two drift.
LIVE_CLAIM = "released_at IS NULL"

BTREE_GIST_DDL = "CREATE EXTENSION IF NOT EXISTS btree_gist"

RESERVATION_EXCLUSION = "ex_reservations_no_overlapping_claim"

RESERVATION_EXCLUSION_DDL = (
    f"ALTER TABLE reservations ADD CONSTRAINT {RESERVATION_EXCLUSION} "
    "EXCLUDE USING gist ("
    "court_id WITH =, "
    "tstzrange(claimed_from, claimed_to, '[)') WITH &&"
    f") WHERE ({LIVE_CLAIM})"
)


def upgrade() -> None:
    op.create_table(
        "reservations",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # Not a foreign key: a court's identity lives across the rows of
        # `club_court_catalogue`, whose primary key is the row, and `court_id`
        # is unique there only among the open rows — a partial unique index,
        # which cannot be referenced.
        sa.Column("court_id", UUIDType(binary=False), nullable=False),
        sa.Column(
            "category_id",
            UUIDType(binary=False),
            sa.ForeignKey("club_court_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # The interval the players get, and the one everybody outside is shown.
        sa.Column("played_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("played_to", sa.DateTime(timezone=True), nullable=False),
        # The interval that excludes everybody else: `played` widened by the
        # club's turnaround when Raketa created it, and `played` exactly when
        # the club published it.
        sa.Column("claimed_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("holder_kind", sa.String(length=16), nullable=False),
        sa.Column("booking_id", UUIDType(binary=False), nullable=True),
        sa.Column("match_id", UUIDType(binary=False), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_reservations_club_id", "reservations", ["club_id"])
    op.create_index("ix_reservations_court_id", "reservations", ["court_id"])

    op.create_table(
        "bookings",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        # One booking, one claim. The database's half of *a Booking holds a
        # Reservation*: a second booking against one reservation would sell one
        # court twice by a route that never touches the exclusion constraint.
        sa.Column(
            "reservation_id",
            UUIDType(binary=False),
            sa.ForeignKey("reservations.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("price_grosze", sa.Integer(), nullable=False),
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_bookings_club_id", "bookings", ["club_id"])
    op.create_index("ix_bookings_player_id", "bookings", ["player_id"])

    if op.get_bind().dialect.name == "postgresql":
        op.execute(BTREE_GIST_DDL)
        op.execute(RESERVATION_EXCLUSION_DDL)


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("reservations")

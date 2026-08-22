"""create the Clubs context: one record, one child table, four series tables

A club is a record with a version, and history belongs to three named facts
rather than to the aggregate (ADR-0077). ``ClubPolicy`` is eight fields versioned
whole (ADR-0078); a category is club-authored and is the priced unit (ADR-0079).

The four partial unique indexes are the guarantee: **at most one open row per
series**, enforced by the database rather than by read ordering. They are partial
because the closed rows are history and history repeats — a club that has changed
its hold cap four times has four rows carrying its id.

``changed_by`` is NOT NULL from this first migration, per ADR-0077: a column added
later would leave every pre-existing row claiming an actor it never had, and a
nullable one cannot distinguish *we did not know* from *nobody did it*. It reads
``system`` until a club-staff identity exists.

Revision ID: 0007_clubs
Revises: 0006_event_store
Create Date: 2026-08-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0007_clubs"
down_revision = "0006_event_store"
branch_labels = None
depends_on = None

#: One spelling of *the row in force*, shared by the three series' indexes, so a
#: fourth series cannot be added with a subtly different one. It is the same
#: string `app/modules/clubs/infrastructure/sqlalchemy_club_models.py` declares,
#: and `tests/unit/test_clubs_migration.py` fails if the two drift.
OPEN_ROW = "valid_to IS NULL"
LIVE_CATEGORY = "retired_at IS NULL"


def upgrade() -> None:
    op.create_table(
        "clubs",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address_line", sa.String(length=160), nullable=False),
        sa.Column("address_city", sa.String(length=160), nullable=False),
        sa.Column("address_postal_code", sa.String(length=160), nullable=False),
        sa.Column("address_country", sa.String(length=2), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column(
            "price_multiplier_num", sa.Integer(), nullable=False, server_default="100"
        ),
        sa.Column(
            "price_multiplier_den", sa.Integer(), nullable=False, server_default="100"
        ),
        sa.Column(
            "slot_discount_num", sa.Integer(), nullable=False, server_default="100"
        ),
        sa.Column(
            "slot_discount_den", sa.Integer(), nullable=False, server_default="100"
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("name", name="uq_clubs_name"),
    )
    op.create_index("ix_clubs_name", "clubs", ["name"])

    op.create_table(
        "club_card_offsets",
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sport", sa.String(length=32), primary_key=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("amount_grosze", sa.Integer(), nullable=True),
    )

    op.create_table(
        "club_policies",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("window_minutes", sa.Integer(), nullable=False),
        sa.Column("join_cut_minutes", sa.Integer(), nullable=False),
        # Nullable and three-valued: NULL is *never stale*, 0 is *this club does
        # not hold speculatively at all*. There is no platform floor to collapse
        # them onto (ADR-0078).
        sa.Column("max_hold_age_minutes", sa.Integer(), nullable=True),
        sa.Column("prob_hold", sa.Boolean(), nullable=False),
        sa.Column("rebooking_credit", sa.Boolean(), nullable=False),
        # No reader in v1 (#64) — the two dark fields.
        sa.Column("free_cancel_hours", sa.Integer(), nullable=True),
        sa.Column("turnaround_minutes", sa.Integer(), nullable=False),
        sa.Column("counts_cash", sa.Boolean(), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("changed_by", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_club_policies_club_id", "club_policies", ["club_id"])
    op.create_index(
        "uq_club_policies_open_row",
        "club_policies",
        ["club_id"],
        unique=True,
        postgresql_where=sa.text(OPEN_ROW),
        sqlite_where=sa.text(OPEN_ROW),
    )

    op.create_table(
        "club_payout_destinations",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("account_holder", sa.String(length=160), nullable=False),
        sa.Column("iban", sa.String(length=34), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("changed_by", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_club_payout_destinations_club_id", "club_payout_destinations", ["club_id"]
    )
    op.create_index(
        "uq_club_payout_destinations_open_row",
        "club_payout_destinations",
        ["club_id"],
        unique=True,
        postgresql_where=sa.text(OPEN_ROW),
        sqlite_where=sa.text(OPEN_ROW),
    )

    op.create_table(
        "club_court_categories",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sport", sa.String(length=32), nullable=False),
        sa.Column("rate_grosze", sa.Integer(), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_club_court_categories_club_id", "club_court_categories", ["club_id"]
    )
    op.create_index(
        "uq_club_court_categories_live_name",
        "club_court_categories",
        ["club_id", "name"],
        unique=True,
        postgresql_where=sa.text(LIVE_CATEGORY),
        sqlite_where=sa.text(LIVE_CATEGORY),
    )

    op.create_table(
        "club_court_catalogue",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("court_id", UUIDType(binary=False), nullable=False),
        sa.Column(
            "category_id",
            UUIDType(binary=False),
            sa.ForeignKey("club_court_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=60), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("changed_by", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_club_court_catalogue_club_id", "club_court_catalogue", ["club_id"]
    )
    # Keyed on the **court**, not the club: a club has many courts and each has
    # its own series, so one open row per club would be one court per club.
    op.create_index(
        "uq_club_court_catalogue_open_row",
        "club_court_catalogue",
        ["court_id"],
        unique=True,
        postgresql_where=sa.text(OPEN_ROW),
        sqlite_where=sa.text(OPEN_ROW),
    )


def downgrade() -> None:
    op.drop_table("club_court_catalogue")
    op.drop_table("club_court_categories")
    op.drop_table("club_payout_destinations")
    op.drop_table("club_policies")
    op.drop_table("club_card_offsets")
    op.drop_table("clubs")

"""create Matches: a record with a version, its seats, and the holes left behind

ADR-0034: Matches is **a record with a version and an outbox**, and no aggregate
in the context keeps event history. So there is no stream table here and no
`expected_version` on an append — the concurrency guard is the `version` column
on `matches`, and it gives the identical guarantee ADR-0002 took from a stream.

Three tables, because a match has two children with lives of their own:

- `matches` — everything ADR-0034's five kinds classify, including the four
  hold-policy fields copied from the club at posting and honoured as booked
  (ADR-0077), which is what lets a situation be resolved from one row-set.
- `match_seats` — one row per seat, written once with the match and thereafter
  only occupied and emptied. `uq_match_seats_position` is *a seat is its
  position*; `uq_match_seats_one_per_player` is *one player, one seat*, partial
  over the occupied rows because every empty seat has a null player and a plain
  unique index would allow exactly one of them.
- `match_vacancies` — a hole a departure left. **Filled, never deleted**, so
  *when did this match lose a player, and when did it get one back* stays a
  query. It carries no amount and no outcome: what a leaver recovered is her
  departure's fact, on an axis of its own (ADR-0033), and
  `Raketa02/Raketa#67` is the ticket that adds it.

Nothing here is PostgreSQL-only. The partial unique index has a SQLite spelling
and gets one, so the fast suite enforces the same rule a real database does;
the only Postgres-specific decision is `JSONB` for the stored score, which is a
storage variant and not a guarantee.

Revision ID: 0009_matches
Revises: 0008_courts
Create Date: 2026-08-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0009_matches"
down_revision = "0008_courts"
branch_labels = None
depends_on = None

#: An occupied seat is one somebody is on. It is the same string
#: `app/modules/matches/infrastructure/sqlalchemy_match_models.py` declares, and
#: `tests/unit/test_matches_migration.py` fails if the two drift.
SEAT_OCCUPIED = "player_id IS NOT NULL"


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        # -- Constitutive ---------------------------------------------------
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            UUIDType(binary=False),
            sa.ForeignKey("club_court_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("share_grosze", sa.Integer(), nullable=False),
        sa.Column("counted", sa.Boolean(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("pay_model", sa.String(16), nullable=False),
        sa.Column("policy_window_minutes", sa.Integer(), nullable=False),
        sa.Column("policy_join_cut_minutes", sa.Integer(), nullable=False),
        sa.Column("policy_max_hold_age_minutes", sa.Integer(), nullable=True),
        sa.Column("policy_prob_hold", sa.Boolean(), nullable=False),
        sa.Column("start", sa.DateTime(timezone=True), nullable=False),
        # -- Occupancy ------------------------------------------------------
        sa.Column(
            "transferring", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("open_seats", sa.Integer(), nullable=False, server_default="0"),
        # -- Allocation -----------------------------------------------------
        sa.Column("held_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "inventory_lost", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        # -- Crossing -------------------------------------------------------
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        # -- Declaration ----------------------------------------------------
        sa.Column(
            "court_locked", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "club_extended", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "club_cancelled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("weather", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("no_show", sa.Boolean(), nullable=False, server_default=sa.false()),
        # The two receipts, and they are an annotation rather than a sixth kind.
        sa.Column(
            "form_cancelled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "checkpoint_cancelled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "score_sets",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column("score_by", UUIDType(binary=False), nullable=True),
        sa.Column("proposals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "result_agreed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_matches_club_id", "matches", ["club_id"])
    op.create_index("ix_matches_start", "matches", ["start"])

    op.create_table(
        "match_seats",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "match_id",
            UUIDType(binary=False),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seat_index", sa.Integer(), nullable=False),
        # Not a foreign key: a player lives behind a projection in another
        # context, and Matches never reads that context's write model.
        sa.Column("player_id", UUIDType(binary=False), nullable=True),
        sa.Column("paid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("match_id", "seat_index", name="uq_match_seats_position"),
    )
    op.create_index("ix_match_seats_match_id", "match_seats", ["match_id"])
    op.create_index("ix_match_seats_player_id", "match_seats", ["player_id"])
    op.create_index(
        "uq_match_seats_one_per_player",
        "match_seats",
        ["match_id", "player_id"],
        unique=True,
        postgresql_where=sa.text(SEAT_OCCUPIED),
        sqlite_where=sa.text(SEAT_OCCUPIED),
    )

    op.create_table(
        "match_vacancies",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "match_id",
            UUIDType(binary=False),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seat_index", sa.Integer(), nullable=False),
        sa.Column("vacated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_match_vacancies_match_id", "match_vacancies", ["match_id"])


def downgrade() -> None:
    op.drop_table("match_vacancies")
    op.drop_table("match_seats")
    op.drop_table("matches")

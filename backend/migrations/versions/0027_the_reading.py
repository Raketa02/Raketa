"""the reading — a fifth surface with no mode, a bearing and the sport chips on its rows

The radar's **reading** is the fifth recorded search surface, ``RADAR``
([#460](https://github.com/Rakieta02/Rakieta/issues/460),
[ADR-0174](../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
§1). Like the deck it scores every pairing under one ruler and takes no mode,
so the two constraints that said *no mode exactly on the deck* and *a
declaration recorded on the deck alone* widen to the two surfaces that score
under one ruler. Nothing else about either constraint moves: a shortlist and a
line-up still carry a mode, and the deck's own rows are admitted as they were.

Two columns join ``search_candidate``, both **radar rows only** and null
everywhere else, and both recorded for the reason ``distance_km`` is: a
read-back never recomputes. ``bearing_deg`` is the compass bearing from the
viewer's drawn spot to the player's (north 0, clockwise, a whole degree), spot
to spot, so the cell under a spot moving would move it; ``ratings`` is every
sport the player was rated in and the Level held there, the card's sport chips,
and a Level moves. The suppression count and the re-show flag stay the deck's
alone: a pass reaches no other surface, and the radar hides nobody for one.

No row moves. Every search recorded so far is one of the four older surfaces,
which the widened constraints admit exactly as the narrower ones did, and both
new columns are null on every existing row.

Revision ID: 0027_the_reading
Revises: 0026_the_drawn_spot
Create Date: 2026-09-16

The revision id fits ``alembic_version.version_num``'s ``VARCHAR(32)``.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0027_the_reading"
down_revision = "0026_the_drawn_spot"
branch_labels = None
depends_on = None

BLOB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.drop_constraint("ck_search_mode_null_exactly_on_the_deck", "search")
    op.create_check_constraint(
        "ck_search_mode_null_exactly_under_one_ruler",
        "search",
        "(mode IS NULL) = (surface IN ('DECK', 'RADAR'))",
    )
    op.drop_constraint("ck_search_intent_read_only_on_the_deck", "search")
    op.create_check_constraint(
        "ck_search_intent_read_only_under_one_ruler",
        "search",
        "(intent_read IS NULL) OR (surface IN ('DECK', 'RADAR'))",
    )
    op.add_column(
        "search_candidate", sa.Column("bearing_deg", sa.Integer(), nullable=True)
    )
    op.add_column("search_candidate", sa.Column("ratings", BLOB, nullable=True))


def downgrade() -> None:
    # A reading recorded under this revision has no mode on a `RADAR` row,
    # which the older constraint refuses; there is no mode to put there that
    # would not be an invented one, so the downgrade refuses rather than lying
    # about what a reading ran under. Only `local` runs, and a reset is the
    # other way down.
    op.drop_column("search_candidate", "ratings")
    op.drop_column("search_candidate", "bearing_deg")
    op.drop_constraint("ck_search_intent_read_only_under_one_ruler", "search")
    op.create_check_constraint(
        "ck_search_intent_read_only_on_the_deck",
        "search",
        "(intent_read IS NULL) OR (surface = 'DECK')",
    )
    op.drop_constraint("ck_search_mode_null_exactly_under_one_ruler", "search")
    op.create_check_constraint(
        "ck_search_mode_null_exactly_on_the_deck",
        "search",
        "(mode IS NULL) = (surface = 'DECK')",
    )

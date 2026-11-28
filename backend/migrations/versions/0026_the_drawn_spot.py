"""the distance a card printed is one decimal, spot to spot

Every candidate's ``distance_km`` is now the one-decimal distance between two
**drawn spots** — a fixed point inside each player's coarse cell, derived from a
stable digest of who they are — rather than the whole-kilometre distance between
two cell centres ([#458](https://github.com/Rakieta02/Rakieta/issues/458),
[ADR-0174](../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
§2). The recorded row keeps what the card printed (ADR-0109: a read-back
reproduces the answer that was given), so the column widens from an integer to
a float.

**No row moves, and no row is re-derived.** A distance recorded before this
revision stays the whole kilometre that card said — ``2`` reads back as ``2.0``
— which is the honest read-back of a search that printed *2 km*. Re-deriving
it spot to spot would answer a question about a search that never ran, and the
spot's inputs (the two cells as they stood) are not on the row anyway. Only
``local`` runs and its store is disposable, so the difference is cosmetic
there; a store that outlived this keeps the old prints as they were.

The Fit does not move with this revision: the distance term and the radius gate
still read cell to cell, and nothing about a recorded ``fit`` or ``terms``
changes.

Revision ID: 0026_the_drawn_spot
Revises: 0025_the_naming
Create Date: 2026-09-16

The revision id fits ``alembic_version.version_num``'s ``VARCHAR(32)``.
"""

import sqlalchemy as sa
from alembic import op

revision = "0026_the_drawn_spot"
down_revision = "0025_the_naming"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "search_candidate",
        "distance_km",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # A one-decimal print does not fit an integer without losing the decimal,
    # and rounding it would change what a card said. Only ``local`` runs, so a
    # reset is the other way down; this narrows the column and lets the
    # database's own cast decide, which on Postgres rounds to nearest.
    op.alter_column(
        "search_candidate",
        "distance_km",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="round(distance_km)::integer",
    )

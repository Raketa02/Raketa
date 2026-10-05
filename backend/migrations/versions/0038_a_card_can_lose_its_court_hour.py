"""proposals: a card can lose its court hour

When the last court at a card's club and hour goes, the card stops filling and
the people who were In are dealt a new card first (the mechanics §5.2, §19;
[#540](https://github.com/Raketa02/Raketa/issues/540)). The proposal stream
records it as ``proposals.court_hour_lost``, and the ``proposals`` projection's
recorded ending gains the value, so the live reads — which filter on an
unrecorded ending — drop the card the moment it is written.

Revision ID: 0038_a_card_can_lose_its_court_hour
Revises: 0037_pools_and_proposals
Create Date: 2026-09-30
"""

from alembic import op

revision = "0038_a_card_can_lose_its_court_hour"
down_revision = "0037_pools_and_proposals"
branch_labels = None
depends_on = None

_ENDED = "ck_proposals_ended"


def upgrade() -> None:
    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED,
        "proposals",
        "ended IS NULL OR ended IN ('EXPIRED', 'WITHDRAWN', 'COURT_HOUR_LOST')",
    )


def downgrade() -> None:
    # A card that lost its court hour is over and nobody paid, which is what an
    # expired one says too.
    op.execute("UPDATE proposals SET ended = 'EXPIRED' WHERE ended = 'COURT_HOUR_LOST'")
    op.drop_constraint(_ENDED, "proposals", type_="check")
    op.create_check_constraint(
        _ENDED, "proposals", "ended IS NULL OR ended IN ('EXPIRED', 'WITHDRAWN')"
    )

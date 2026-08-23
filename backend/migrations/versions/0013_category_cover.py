"""club_court_categories gains cover: whether there is a roof

ADR-0090, closing `Raketa02/Raketa#98`. ADR-0073 put indoor-or-outdoor on the
spine of every card and `#73` shipped it as a **required** field of
`PlaceResponse`; nothing in the system could answer it, because whether there
was a roof lived inside a category's free-text *name* — `Padel · indoor`,
`Padel · Wall, outdoor`. A convention in a display string is not a fact.

**It goes on the category rather than on the court**, because the specific court
is not assigned until fifteen minutes before play (`kernel.court_named_at`), so
a card composed on Monday for a match on Thursday has no court to read it off.
The category is already the priced unit and the thing a caller asks for
(ADR-0035), and ADR-0079 put the price there on exactly this argument: a court
that costs differently is a different category, and so is one with a roof.

**The backfill parses the name, once, here.** That is the whole difference
between this and the thing #98 refuses: parsing a name *on the compose path*
would be deriving a domain fact from copy on the busiest read in the product;
parsing it once, in a migration, in a diff somebody reviewed, is how prose
becomes a fact. A name containing *indoor* becomes `indoor`; everything else
becomes `outdoor` — and that default is not a coin toss. Telling a player a
court is outdoor when it has a roof costs her a match she would have wanted;
telling her it is indoor when it has none costs her a soaking in ADR-0073's own
November. The answer that never claims shelter a club did not declare goes in.

**Three statements rather than one**, because the honest column is `NOT NULL`
with **no server default**: a default would mean a row inserted without a cover
silently becomes outdoor, which is the fabricated observation this exists to
remove. So the column arrives nullable, every row is given its answer, and only
then is the constraint applied — which is also the order that lets `downgrade`
be a plain drop.

Revision ID: 0013_category_cover
Revises: 0012_match_seat_claims
Create Date: 2026-08-23
"""

import sqlalchemy as sa
from alembic import op

revision = "0013_category_cover"
down_revision = "0012_match_seat_claims"
branch_labels = None
depends_on = None

#: Where the fact has been living. Lower-cased on both sides so a club that
#: wrote `Padel · Indoor` is read the same way — this runs once and there is no
#: second chance to notice a capital.
_BACKFILL = sa.text(
    "UPDATE club_court_categories SET cover = 'indoor' "
    "WHERE lower(name) LIKE '%indoor%'"
)

_DEFAULT = sa.text("UPDATE club_court_categories SET cover = 'outdoor' "
                   "WHERE cover IS NULL")


def upgrade() -> None:
    op.add_column(
        "club_court_categories",
        sa.Column("cover", sa.String(length=16), nullable=True),
    )
    op.execute(_BACKFILL)
    op.execute(_DEFAULT)
    op.alter_column(
        "club_court_categories",
        "cover",
        existing_type=sa.String(length=16),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("club_court_categories", "cover")

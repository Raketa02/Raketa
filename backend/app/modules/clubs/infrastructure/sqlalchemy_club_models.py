"""The six tables a club lives in: one record, one child table, four series rows.

**Four partial unique indexes, and they are the point of the schema.** ADR-0077
puts a version on the club *and* an index per series, because they answer
different questions: the version stops a race, the index stops an invariant
violation from ever reaching disk. Discipline alone would mean the invariant is
asserted by code review, which is what ADR-0035 refused when it said exclusion is
*"enforced by the database, never by read ordering."*

**They are declared for SQLite as well as for PostgreSQL, deliberately.** This is
the cheap case of ADR-0035's pattern and does not inherit its cost: a club has at
most one open row per series, so the constraint is *at most one row with a null
``valid_to``* — a partial unique index, which both engines support, where an
overlapping-interval exclusion needs `EXCLUDE USING gist` and only PostgreSQL
has it. So the guarantee holds in the fast tests as well as in production, and
`tests/integration/test_club_series.py` asserts it against a real PostgreSQL for
what SQLite cannot speak for: uuid comparison, `timestamptz`, and the real DDL
this metadata emits.

**Two of the eight policy columns have no reader (#64).** `free_cancel_hours`
and `counts_cash` are stored and nothing in `app/` reads them — see
`app/modules/clubs/domain/policy.py`, which carries the reasons. Do not read that
silence as *nobody needed this*.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base

#: The predicate that defines *the row in force*. One spelling, used by every
#: series' index, so a fifth series cannot be added with a subtly different one.
OPEN_ROW = "valid_to IS NULL"

#: The same idea for a catalogue entry that is not a series row: a category is
#: retired rather than deleted, so *live* is the absence of a retirement.
LIVE_CATEGORY = "retired_at IS NULL"


def _partial_unique(name: str, *columns: Mapped[object], where: str) -> sa.Index:
    """A unique index over the open rows only, on both engines we run on.

    Partial on purpose: the closed rows are history and history repeats — a club
    that has changed its hold cap four times has four rows carrying its id, and a
    plain unique index would refuse the second change.

    The table is inferred from the columns, so the index cannot be attached to
    the wrong one; the predicate is dialect-scoped because SQLAlchemy has no
    engine-neutral spelling for it, and both of ours are named so that neither
    engine silently gets a *whole-table* unique index instead.
    """

    return sa.Index(
        name,
        *columns,
        unique=True,
        postgresql_where=sa.text(where),
        sqlite_where=sa.text(where),
    )


class ClubORM(Base):
    """The unversioned record: everything a change to which is not a dispute."""

    __tablename__ = "clubs"
    __table_args__ = (sa.UniqueConstraint("name", name="uq_clubs_name"),)

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False, index=True)

    address_line: Mapped[str] = mapped_column(sa.String(160), nullable=False)
    address_city: Mapped[str] = mapped_column(sa.String(160), nullable=False)
    address_postal_code: Mapped[str] = mapped_column(sa.String(160), nullable=False)
    address_country: Mapped[str] = mapped_column(sa.String(2), nullable=False)

    # Numeric, not float: what a human types is a decimal literal, and six places
    # is about eleven centimetres. `km` is derived at read time from this and the
    # player's anchor, and is stored nowhere (ADR-0078).
    latitude: Mapped[Decimal] = mapped_column(sa.Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(sa.Numeric(9, 6), nullable=False)

    #: An IANA name, entered with the address. A constant `Europe/Warsaw` would
    #: be true today and is the one-market assumption ADR-0078 refuses.
    timezone: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    # Pricing as exact rationals, for the reason `Ratio` is a `Fraction`:
    # `Fraction(0.9)` is not nine tenths, and a float would round every price the
    # same way as nine tenths for years before the one time it did not.
    price_multiplier_num: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=100, server_default="100"
    )
    price_multiplier_den: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=100, server_default="100"
    )
    slot_discount_num: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=100, server_default="100"
    )
    slot_discount_den: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=100, server_default="100"
    )

    #: The optimistic-concurrency guard. Bumped by the repository on every save,
    #: never by the aggregate — two counters for one fact is one too many.
    version: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0, server_default="0"
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


class ClubCardOffsetORM(Base):
    """The standing per-sport club-card allowance — a *rate*, not a balance.

    ADR-0078: *"a rate a club sets and a ledger of credits a player has accrued
    at that club are not one object."* This is the rate, and it is unversioned
    because it is an input to a price copied onto the match at quote time. A
    sport with no row means no allowance.
    """

    __tablename__ = "club_card_offsets"

    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sport: Mapped[str] = mapped_column(sa.String(32), primary_key=True)
    #: `allowance` (capped, `amount_grosze` set) or `covers` (the whole share).
    #: There is no `none` row: absent is `NoCard`.
    kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    amount_grosze: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)


class ClubPolicyORM(Base):
    """One version of a club's policy — eight fields, closed and opened whole."""

    __tablename__ = "club_policies"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    window_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    join_cut_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #: NULL is *never stale*; 0 is *this club does not hold speculatively at
    #: all*. Two different facts, so the column is nullable rather than
    #: defaulted — there is no platform floor to collapse them onto.
    max_hold_age_minutes: Mapped[Optional[int]] = mapped_column(
        sa.Integer, nullable=True
    )
    prob_hold: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    rebooking_credit: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    #: No reader in v1 (#64). Hours, not minutes — see the domain's policy module.
    free_cancel_hours: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    turnaround_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #: No reader in v1 (#64).
    counts_cash: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)

    valid_from: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    changed_by: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class ClubPayoutDestinationORM(Base):
    """Where the club is paid. Its own series, so a bank change is not buried."""

    __tablename__ = "club_payout_destinations"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_holder: Mapped[str] = mapped_column(sa.String(160), nullable=False)
    iban: Mapped[str] = mapped_column(sa.String(34), nullable=False)

    valid_from: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    changed_by: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class ClubCourtCategoryORM(Base):
    """A club-authored group of interchangeable courts, and its rate.

    Retired, never deleted — so a past reservation still resolves, and a category
    with no courts left survives as a group that can never be assigned.
    """

    __tablename__ = "club_court_categories"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    #: Exactly one sport. The platform's only constraint on a category, and it is
    #: there because a category spanning two sports makes a seat share undefined.
    sport: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    #: What one booked block costs before the club's multipliers, in grosze. The
    #: price attaches here and never to a court: v37's `court.pm` is deleted.
    rate_grosze: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    retired_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


class ClubCourtCatalogueORM(Base):
    """One row of a court's catalogue series: it was this, between these instants.

    ADR-0077's narrowing of ADR-0034 for the Courts context: a court's **state**
    stays a record with no history, and what gains a validity interval is the
    catalogue row — *this court existed, in this category, between these
    instants*.
    """

    __tablename__ = "club_court_catalogue"

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    #: The court's own identity, stable across every row of its series. A court
    #: *exists* exactly while one of its rows is open.
    court_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    category_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("club_court_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(sa.String(60), nullable=False)

    valid_from: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    changed_by: Mapped[str] = mapped_column(sa.String(64), nullable=False)


#: The three series, plus the category catalogue's own liveness. Declared here
#: rather than inline in each `__table_args__` so all four read as one decision
#: and share one spelling of *the row in force*.
CLUB_POLICY_OPEN_ROW = _partial_unique(
    "uq_club_policies_open_row", ClubPolicyORM.club_id, where=OPEN_ROW
)
CLUB_PAYOUT_OPEN_ROW = _partial_unique(
    "uq_club_payout_destinations_open_row",
    ClubPayoutDestinationORM.club_id,
    where=OPEN_ROW,
)
CLUB_COURT_OPEN_ROW = _partial_unique(
    "uq_club_court_catalogue_open_row",
    ClubCourtCatalogueORM.court_id,
    where=OPEN_ROW,
)
CLUB_CATEGORY_LIVE_NAME = _partial_unique(
    "uq_club_court_categories_live_name",
    ClubCourtCategoryORM.club_id,
    ClubCourtCategoryORM.name,
    where=LIVE_CATEGORY,
)

"""Reading a club out of six tables, and writing the delta back into them.

**The write order is the load-bearing part.** A change to a history-bearing fact
is two statements — close the row in force, open a new one — and a partial unique
index refuses two open rows. So every close is issued and flushed *before* any
open is inserted. Doing it the other way round is not a style preference: it is a
constraint violation on the ordinary path, and it would look like the index being
wrong rather than like the write being out of order.

**The delta is computed from the database, not remembered.** ``save`` re-reads
the row ids it already holds for this club and compares them with the aggregate's
— one SELECT per table, inside a transaction that has already taken the version
guard, so nothing can move underneath it. A repository that remembered what it
loaded would be a second piece of state to keep in step with the session.

**Row identity is positional within a series.** A series is append-only and
ordered, so the *n*th row in memory is the *n*th row on disk; a row that has
gained a ``valid_to`` is the same row it was, and everything past the stored
count is new. That is what lets *close and open* be an UPDATE followed by an
INSERT rather than a delete-and-rewrite, which would throw away the history this
whole context exists to keep.

That premise is only as good as the ORDER BY that rebuilds the position, and
there is exactly one — ``_series_order`` — used by both the read and the delta,
because the two disagreeing is the same bug wearing either hat. It is total
rather than *usually* total; see the function for what an ambiguous one did.

Naive datetimes come back from SQLite, which drops the offset it was handed. They
are re-attached to UTC on the way in, the same normalisation
``app/infrastructure/events/json_event_codec.py`` makes and for the same reason:
the stored instant *is* UTC — ``Instant`` normalises before anything is written —
so this restores what the engine dropped rather than guessing at it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from typing import Any, Sequence, cast
from uuid import UUID

from sqlalchemy import Select, delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import (
    CardAllowance,
    CardCoversShare,
    ClubCard,
    Cover,
    Instant,
    NoCard,
    Ratio,
    Sport,
    exhaustive,
    grosze,
    instant,
    minutes,
)
from app.modules.clubs.domain.catalogue import CatalogueEntry, Court, CourtCategory
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.errors import ConcurrentClubModification
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.series import Series, Version
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ChangedBy,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
    zone_named,
)
from app.modules.clubs.infrastructure.sqlalchemy_club_models import (
    ClubCardOffsetORM,
    ClubCourtCatalogueORM,
    ClubCourtCategoryORM,
    ClubORM,
    ClubPayoutDestinationORM,
    ClubPolicyORM,
)
from app.shared.ids import new_uuid

_ALLOWANCE = "allowance"
_COVERS = "covers"


def _as_instant(value: datetime) -> Instant:
    """Re-attach UTC to what SQLite dropped, then normalise."""

    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))


def _series_order(model: Any) -> tuple[Any, ...]:
    """The one ordering that rebuilds a series in the order it was appended.

    ``valid_from`` alone is ambiguous, and exactly where it matters: two rows of
    one series share an instant precisely when the earlier is **zero-width** —
    opened and closed at the same moment, which is what two changes at one clock
    reading produce. Ordering broke the tie on ``id``, and ``new_uuid`` is
    ``uuid4``, so which of the two came back first was a coin flip — and half the
    draws put the open row **first**, which ``Series`` refuses to construct. The
    symptom was a club that loaded fine until it did not, and read as a broken
    database rather than as an ambiguous ORDER BY. Measured at 29 failures in 60
    draws before this existed; `tests/unit/test_club_repository.py` keeps the
    measurement.

    ``valid_to IS NULL`` sorts **after** ``valid_to IS NOT NULL`` because ``False``
    precedes ``True``, so the open row is last by construction rather than by the
    dialect's opinion about where NULLs go — Postgres puts them last by default
    and SQLite puts them first, and this file is read on both. Among closed rows
    sharing an instant, the one that ended first is the one that began first.
    """

    return (
        model.valid_from,
        model.valid_to.is_(None),
        model.valid_to,
        model.id,
    )


def _optional_instant(value: datetime | None) -> Instant | None:
    return None if value is None else _as_instant(value)


def _ratio(numerator: int, denominator: int) -> Ratio:
    return Ratio(Fraction(numerator, denominator))


def _card_of(row: ClubCardOffsetORM) -> ClubCard:
    if row.kind == _COVERS:
        return CardCoversShare()
    if row.kind == _ALLOWANCE:
        return CardAllowance(grosze(row.amount_grosze or 0))
    raise ValueError(f"unknown club card kind: {row.kind!r}")


def _card_row(club_id: UUID, sport: Sport, card: ClubCard) -> ClubCardOffsetORM | None:
    """One row per sport that has an allowance. ``NoCard`` is *no row*."""

    match card:
        case NoCard():
            return None
        case CardAllowance(amount):
            return ClubCardOffsetORM(
                club_id=club_id,
                sport=sport.value,
                kind=_ALLOWANCE,
                amount_grosze=int(amount),
            )
        case CardCoversShare():
            return ClubCardOffsetORM(
                club_id=club_id, sport=sport.value, kind=_COVERS, amount_grosze=None
            )
        case _:  # pragma: no cover - `exhaustive` never returns
            exhaustive(card)


def _policy_of(row: ClubPolicyORM) -> Version[ClubPolicy]:
    return Version(
        value=ClubPolicy(
            window=minutes(row.window_minutes),
            join_cut=minutes(row.join_cut_minutes),
            max_hold_age=(
                None
                if row.max_hold_age_minutes is None
                else minutes(row.max_hold_age_minutes)
            ),
            prob_hold=row.prob_hold,
            rebooking_credit=row.rebooking_credit,
            free_cancel_hours=row.free_cancel_hours,
            turnaround_min=minutes(row.turnaround_minutes),
            counts_cash=row.counts_cash,
        ),
        valid_from=_as_instant(row.valid_from),
        valid_to=_optional_instant(row.valid_to),
        changed_by=ChangedBy(row.changed_by),
    )


def _policy_row(club_id: UUID, version: Version[ClubPolicy]) -> ClubPolicyORM:
    policy = version.value
    return ClubPolicyORM(
        id=new_uuid(),
        club_id=club_id,
        window_minutes=int(policy.window),
        join_cut_minutes=int(policy.join_cut),
        max_hold_age_minutes=(
            None if policy.max_hold_age is None else int(policy.max_hold_age)
        ),
        prob_hold=policy.prob_hold,
        rebooking_credit=policy.rebooking_credit,
        free_cancel_hours=policy.free_cancel_hours,
        turnaround_minutes=int(policy.turnaround_min),
        counts_cash=policy.counts_cash,
        valid_from=version.valid_from,
        valid_to=version.valid_to,
        changed_by=version.changed_by.value,
    )


def _payout_of(row: ClubPayoutDestinationORM) -> Version[PayoutDestination]:
    return Version(
        value=PayoutDestination(account_holder=row.account_holder, iban=row.iban),
        valid_from=_as_instant(row.valid_from),
        valid_to=_optional_instant(row.valid_to),
        changed_by=ChangedBy(row.changed_by),
    )


def _payout_row(
    club_id: UUID, version: Version[PayoutDestination]
) -> ClubPayoutDestinationORM:
    return ClubPayoutDestinationORM(
        id=new_uuid(),
        club_id=club_id,
        account_holder=version.value.account_holder,
        iban=version.value.iban,
        valid_from=version.valid_from,
        valid_to=version.valid_to,
        changed_by=version.changed_by.value,
    )


def _catalogue_of(row: ClubCourtCatalogueORM) -> Version[CatalogueEntry]:
    return Version(
        value=CatalogueEntry(
            category_id=row.category_id, label=CourtLabel(row.label)
        ),
        valid_from=_as_instant(row.valid_from),
        valid_to=_optional_instant(row.valid_to),
        changed_by=ChangedBy(row.changed_by),
    )


def _catalogue_row(
    club_id: UUID, court_id: UUID, version: Version[CatalogueEntry]
) -> ClubCourtCatalogueORM:
    return ClubCourtCatalogueORM(
        id=new_uuid(),
        club_id=club_id,
        court_id=court_id,
        category_id=version.value.category_id,
        label=version.value.label.value,
        valid_from=version.valid_from,
        valid_to=version.valid_to,
        changed_by=version.changed_by.value,
    )


class _Stored:
    """The row ids this club already has, per series, oldest first."""

    def __init__(
        self,
        *,
        policies: list[UUID],
        payouts: list[UUID],
        categories: set[UUID],
        catalogue: dict[UUID, list[UUID]],
    ) -> None:
        self.policies = policies
        self.payouts = payouts
        self.categories = categories
        self.catalogue = catalogue

    @classmethod
    def none_yet(cls) -> "_Stored":
        return cls(policies=[], payouts=[], categories=set(), catalogue={})


class SqlAlchemyClubRepository:
    """A record repository: rows in, rows out, and a version on the way out."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- reading -------------------------------------------------------------

    async def get(self, club_id: UUID) -> Club | None:
        row = (
            await self._session.execute(select(ClubORM).where(ClubORM.id == club_id))
        ).scalar_one_or_none()
        return None if row is None else await self._hydrate(row)

    async def get_by_name(self, name: ClubName) -> Club | None:
        row = (
            await self._session.execute(
                select(ClubORM).where(ClubORM.name == name.value)
            )
        ).scalar_one_or_none()
        return None if row is None else await self._hydrate(row)

    async def find_all(self) -> list[Club]:
        rows = await self._all(select(ClubORM).order_by(ClubORM.name))
        return [await self._hydrate(row) for row in rows]

    async def find_by_ids(self, club_ids: Sequence[UUID]) -> list[Club]:
        if not club_ids:
            # `IN ()` is not portable, and a round trip to learn nothing is a
            # round trip on the busiest read in the product.
            return []
        rows = await self._all(
            select(ClubORM).where(ClubORM.id.in_(list(club_ids))).order_by(ClubORM.name)
        )
        return [await self._hydrate(row) for row in rows]

    async def _all(self, statement: Select[Any]) -> Sequence[Any]:
        return (await self._session.execute(statement)).scalars().all()

    async def _hydrate(self, row: ClubORM) -> Club:
        cards = await self._all(
            select(ClubCardOffsetORM).where(ClubCardOffsetORM.club_id == row.id)
        )
        policies = await self._all(
            select(ClubPolicyORM)
            .where(ClubPolicyORM.club_id == row.id)
            .order_by(*_series_order(ClubPolicyORM))
        )
        payouts = await self._all(
            select(ClubPayoutDestinationORM)
            .where(ClubPayoutDestinationORM.club_id == row.id)
            .order_by(*_series_order(ClubPayoutDestinationORM))
        )
        categories = await self._all(
            select(ClubCourtCategoryORM)
            .where(ClubCourtCategoryORM.club_id == row.id)
            .order_by(ClubCourtCategoryORM.created_at, ClubCourtCategoryORM.id)
        )
        catalogue = await self._all(
            select(ClubCourtCatalogueORM)
            .where(ClubCourtCatalogueORM.club_id == row.id)
            .order_by(*_series_order(ClubCourtCatalogueORM))
        )

        by_court: dict[UUID, list[Version[CatalogueEntry]]] = {}
        for entry in catalogue:
            by_court.setdefault(entry.court_id, []).append(_catalogue_of(entry))

        return Club(
            id=row.id,
            name=ClubName(row.name),
            address=StreetAddress(
                line=row.address_line,
                city=row.address_city,
                postal_code=row.address_postal_code,
                country=row.address_country,
            ),
            point=GeoPoint(
                latitude=Decimal(row.latitude), longitude=Decimal(row.longitude)
            ),
            timezone=zone_named(row.timezone),
            pricing=ClubPricing(
                price_multiplier=_ratio(
                    row.price_multiplier_num, row.price_multiplier_den
                ),
                slot_discount=_ratio(row.slot_discount_num, row.slot_discount_den),
                card_offsets={Sport(card.sport): _card_of(card) for card in cards},
            ),
            policy=Series(tuple(_policy_of(p) for p in policies)),
            payout=Series(tuple(_payout_of(p) for p in payouts)),
            categories=[
                CourtCategory(
                    id=category.id,
                    name=CategoryName(category.name),
                    sport=Sport(category.sport),
                    cover=Cover(category.cover),
                    rate=grosze(category.rate_grosze),
                    retired_at=_optional_instant(category.retired_at),
                )
                for category in categories
            ],
            courts=[
                Court(id=court_id, catalogue=Series(tuple(versions)))
                for court_id, versions in by_court.items()
            ],
            version=row.version,
            created_at=_as_instant(row.created_at),
        )

    # -- writing -------------------------------------------------------------

    async def add(self, club: Club) -> Club:
        self._session.add(self._record(club, version=0))
        await self._session.flush()
        await self._write_children(club, stored=_Stored.none_yet())
        club.version = 0
        return club

    async def save(self, club: Club) -> Club:
        """Bump the version or refuse, then write the delta.

        The version guard runs first and in the same statement that bumps it, so
        a second writer that read the same club loses on ``rowcount`` rather than
        on whichever series it happened to touch. ADR-0077 keeps this beside the
        partial unique index deliberately: the version stops a race, the index
        stops an invariant violation from reaching disk, and neither does the
        other's job.
        """

        result = await self._session.execute(
            update(ClubORM)
            .where(ClubORM.id == club.id, ClubORM.version == club.version)
            .values(**self._columns(club), version=club.version + 1)
        )
        # `session.execute` is typed as returning `Result`, which has no
        # `rowcount`; a DML statement always yields a `CursorResult`, which does.
        if cast(CursorResult[Any], result).rowcount != 1:
            raise ConcurrentClubModification()

        await self._write_children(club, stored=await self._stored(club.id))
        club.version += 1
        return club

    def _columns(self, club: Club) -> dict[str, Any]:
        return {
            "name": club.name.value,
            "address_line": club.address.line,
            "address_city": club.address.city,
            "address_postal_code": club.address.postal_code,
            "address_country": club.address.country,
            "latitude": club.point.latitude,
            "longitude": club.point.longitude,
            "timezone": str(club.timezone),
            "price_multiplier_num": club.pricing.price_multiplier.numerator,
            "price_multiplier_den": club.pricing.price_multiplier.denominator,
            "slot_discount_num": club.pricing.slot_discount.numerator,
            "slot_discount_den": club.pricing.slot_discount.denominator,
        }

    def _record(self, club: Club, *, version: int) -> ClubORM:
        return ClubORM(id=club.id, version=version, **self._columns(club))

    async def _stored(self, club_id: UUID) -> _Stored:
        catalogue: dict[UUID, list[UUID]] = {}
        rows = await self._session.execute(
            select(ClubCourtCatalogueORM.court_id, ClubCourtCatalogueORM.id)
            .where(ClubCourtCatalogueORM.club_id == club_id)
            .order_by(*_series_order(ClubCourtCatalogueORM))
        )
        for court_id, row_id in rows:
            catalogue.setdefault(court_id, []).append(row_id)

        return _Stored(
            policies=list(
                await self._all(
                    select(ClubPolicyORM.id)
                    .where(ClubPolicyORM.club_id == club_id)
                    .order_by(*_series_order(ClubPolicyORM))
                )
            ),
            payouts=list(
                await self._all(
                    select(ClubPayoutDestinationORM.id)
                    .where(ClubPayoutDestinationORM.club_id == club_id)
                    .order_by(*_series_order(ClubPayoutDestinationORM))
                )
            ),
            categories=set(
                await self._all(
                    select(ClubCourtCategoryORM.id).where(
                        ClubCourtCategoryORM.club_id == club_id
                    )
                )
            ),
            catalogue=catalogue,
        )

    async def _write_children(self, club: Club, *, stored: _Stored) -> None:
        """Close everything, flush, then open everything.

        One flush between the two halves is enough: the constraint is *at most
        one open row per series*, and after the closes there are none.
        """

        await self._close(ClubPolicyORM, stored.policies, club.policy)
        await self._close(ClubPayoutDestinationORM, stored.payouts, club.payout)
        for court in club.courts:
            await self._close(
                ClubCourtCatalogueORM,
                stored.catalogue.get(court.id, []),
                court.catalogue,
            )
        await self._update_categories(club, stored)
        await self._session.flush()

        for policy_version in club.policy.versions[len(stored.policies) :]:
            self._session.add(_policy_row(club.id, policy_version))
        for payout_version in club.payout.versions[len(stored.payouts) :]:
            self._session.add(_payout_row(club.id, payout_version))
        for category in club.categories:
            if category.id not in stored.categories:
                self._session.add(
                    ClubCourtCategoryORM(
                        id=category.id,
                        club_id=club.id,
                        name=category.name.value,
                        sport=category.sport.value,
                        cover=category.cover.value,
                        rate_grosze=int(category.rate),
                        retired_at=category.retired_at,
                    )
                )
        for court in club.courts:
            written = len(stored.catalogue.get(court.id, []))
            for entry_version in court.catalogue.versions[written:]:
                self._session.add(
                    _catalogue_row(club.id, court.id, entry_version)
                )
        await self._rewrite_cards(club)
        await self._session.flush()

    async def _close(
        self, model: Any, row_ids: list[UUID], series: Series[Any]
    ) -> None:
        """Write ``valid_to`` onto every stored row the aggregate has closed.

        Guarded on ``valid_to IS NULL`` so a re-save writes nothing: closing an
        already-closed row would be an update that changes the instant a version
        ended, which is history being rewritten rather than extended.
        """

        # Not strict: the aggregate holds every stored row *plus* whatever this
        # save is about to open, so the versions are the longer side by design.
        for row_id, version in zip(row_ids, series.versions, strict=False):
            if version.valid_to is not None:
                await self._session.execute(
                    update(model)
                    .where(model.id == row_id, model.valid_to.is_(None))
                    .values(valid_to=version.valid_to)
                )

    async def _update_categories(self, club: Club, stored: _Stored) -> None:
        """A category is a record, not a series: its columns are updated in place.

        Its *retirement* is the fact that has to survive, and that is what
        ``retired_at`` carries. ADR-0079 keeps the category's price out of the
        history for the same reason ADR-0078 keeps `pm` out of the policy row:
        the price quoted is copied onto the match at booking, so nothing ever
        asks what a category cost last Friday.

        **``sport`` and ``cover`` are absent from the update, and neither is an
        oversight.** They are the two facts the platform constrains, and both
        are fixed at construction: a category that changed either would be a
        different category, and a court that gains a roof **moves** rather than
        having one edited on to it (ADR-0090). Adding them here is how *the
        club roofed Court 3* would silently become *every court in this
        category has always had a roof*.
        """

        for category in club.categories:
            if category.id in stored.categories:
                await self._session.execute(
                    update(ClubCourtCategoryORM)
                    .where(ClubCourtCategoryORM.id == category.id)
                    .values(
                        name=category.name.value,
                        rate_grosze=int(category.rate),
                        retired_at=category.retired_at,
                    )
                )

    async def _rewrite_cards(self, club: Club) -> None:
        """Delete and re-insert. There is no history here and no row identity.

        Four rows at most, unversioned by decision (ADR-0078: a rate is an input
        to a price copied onto the match at quote time), so a diff would be more
        machinery than the fact deserves.
        """

        await self._session.execute(
            delete(ClubCardOffsetORM).where(ClubCardOffsetORM.club_id == club.id)
        )
        await self._session.flush()
        for sport, card in club.pricing.card_offsets.items():
            row = _card_row(club.id, sport, card)
            if row is not None:
                self._session.add(row)

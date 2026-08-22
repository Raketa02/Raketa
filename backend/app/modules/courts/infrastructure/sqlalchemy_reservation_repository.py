"""Reading and writing reservations — and translating one SQLSTATE.

**The savepoint is the part to read.** ADR-0035 makes losing a race an ordinary
event: the claim is written, the exclusion constraint refuses it, and the caller
looks again. On PostgreSQL a constraint violation aborts the surrounding
transaction, so without a savepoint the *first* refusal would poison every
subsequent statement and the re-ask would fail for a reason that has nothing to
do with courts. ``begin_nested()`` scopes the failure to the one INSERT: it rolls
back to the savepoint and the outer transaction carries on, which is what makes
*"one winner and one query result — never a lock timeout or a partial write"*
true rather than aspirational.

**Two SQLSTATEs mean *the court is taken*, and the second one was measured
rather than reasoned about.** The obvious one is ``23P01``,
``exclusion_violation``. The other is ``40P01``, ``deadlock_detected``, and it
arrives when the two writers are *exactly* simultaneous: a GiST exclusion index
inserts its entry before it scans for a conflict, so each transaction can find
the other's pending entry and wait for it, and PostgreSQL breaks the cycle by
aborting one. Measured on a real PostgreSQL over forty races on one court: **30
losers got ``23P01`` and 10 got ``40P01``**, exactly one row landed every time,
and the loser recovered through the savepoint in both cases.

That second code is the whole reason this catches ``DBAPIError`` rather than
``IntegrityError``: a deadlock is **not** an ``IntegrityError``, so a narrower
catch would let the closest race of all — the one this context exists for —
escape as a 500 while the ordinary near-miss was handled. Both mean *somebody
else reached this court*; the answer to both is to look again.

**And the codes are asserted, never inferred.** ``IntegrityError`` covers a
primary-key collision and a foreign-key violation just as happily, and mapping
all of them to *the court is taken* would report a bug as a busy afternoon.
Anything that is not one of the two is re-raised as itself. SQLite has neither
the constraint nor the SQLSTATEs, so the translation simply never fires there —
see this module's suite, and `tests/integration/test_reservation_exclusion.py`
for the guarantee itself.

Naive datetimes come back from SQLite, which drops the offset it was handed. They
are re-attached to UTC on the way in, the same normalisation
`app/modules/clubs/infrastructure/sqlalchemy_club_repository.py` makes and for
the same reason: the stored instant *is* UTC, so this restores what the engine
dropped rather than guessing at it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence, cast
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant, exhaustive, instant

from app.modules.courts.domain.errors import (
    ConcurrentReservationModification,
    CourtAlreadyClaimed,
)
from app.modules.courts.domain.reservation import (
    BookingHeld,
    ClubHeld,
    Holder,
    HolderKind,
    MatchHeld,
    Reservation,
)
from app.modules.courts.domain.time_range import TimeRange
from app.modules.courts.infrastructure.sqlalchemy_court_models import ReservationORM

#: PostgreSQL's `exclusion_violation` — the ordinary refusal.
EXCLUSION_VIOLATION = "23P01"

#: PostgreSQL's `deadlock_detected` — the *exactly* simultaneous refusal. See
#: the module docstring; it is the same event and it is not an `IntegrityError`.
DEADLOCK_DETECTED = "40P01"

#: What the database says when a court is already taken. Both members mean one
#: thing to a caller: look again.
COURT_IS_TAKEN = frozenset({EXCLUSION_VIOLATION, DEADLOCK_DETECTED})


def _as_instant(value: datetime) -> Instant:
    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))


def _optional_instant(value: datetime | None) -> Instant | None:
    return None if value is None else _as_instant(value)


def _holder_of(row: ReservationORM) -> Holder:
    kind = HolderKind(row.holder_kind)
    match kind:
        case HolderKind.BOOKING:
            if row.booking_id is None:
                raise ValueError(f"reservation {row.id} is booking-held by nothing")
            return BookingHeld(row.booking_id)
        case HolderKind.MATCH:
            if row.match_id is None:
                raise ValueError(f"reservation {row.id} is match-held by nothing")
            return MatchHeld(row.match_id)
        case HolderKind.CLUB:
            return ClubHeld()
        case _:  # pragma: no cover - `exhaustive` never returns
            exhaustive(kind)


def _holder_columns(holder: Holder) -> dict[str, Any]:
    """The kind and its payload together, so neither can be written alone."""

    match holder:
        case BookingHeld(booking_id):
            return {
                "holder_kind": HolderKind.BOOKING.value,
                "booking_id": booking_id,
                "match_id": None,
            }
        case MatchHeld(match_id):
            return {
                "holder_kind": HolderKind.MATCH.value,
                "booking_id": None,
                "match_id": match_id,
            }
        case ClubHeld():
            return {
                "holder_kind": HolderKind.CLUB.value,
                "booking_id": None,
                "match_id": None,
            }
        case _:  # pragma: no cover - `exhaustive` never returns
            exhaustive(holder)


def _reservation_of(row: ReservationORM) -> Reservation:
    return Reservation(
        id=row.id,
        club_id=row.club_id,
        court_id=row.court_id,
        category_id=row.category_id,
        played=TimeRange(
            start=_as_instant(row.played_from), end=_as_instant(row.played_to)
        ),
        claimed=TimeRange(
            start=_as_instant(row.claimed_from), end=_as_instant(row.claimed_to)
        ),
        holder=_holder_of(row),
        released_at=_optional_instant(row.released_at),
        version=row.version,
    )


def _history_order() -> tuple[Any, ...]:
    """The one ordering that rebuilds a court's history in the order it happened.

    ``claimed_from`` alone is ambiguous, and exactly where it matters: two rows
    of one court share a claimed start precisely when the earlier one was
    **released** and replaced — a withdrawn hold and the booking that took the
    slot. The tie then broke on ``id``, and ``new_uuid`` is ``uuid4``, so which
    came back first was a coin flip decided when the row was written. The same
    defect `app/modules/clubs/infrastructure/sqlalchemy_club_repository.py`
    measured at 29 failures in 60 draws, one context over, and it reads as a
    broken database rather than as an ordering.

    ``released_at IS NULL`` sorts **after** ``IS NOT NULL`` because ``False``
    precedes ``True``, so the live claim is last by construction rather than by
    the dialect's opinion about where NULLs go — PostgreSQL puts them last by
    default and SQLite puts them first, and this file is read on both. That is
    also the right answer semantically: a live claim on a window can only exist
    because whatever held it before was released first, or the exclusion
    constraint would have refused it. Among released rows, the one given back
    first was taken first.
    """

    return (
        ReservationORM.claimed_from,
        ReservationORM.released_at.is_(None),
        ReservationORM.released_at,
        ReservationORM.id,
    )


def _means_the_court_is_taken(error: DBAPIError) -> bool:
    return getattr(error.orig, "sqlstate", None) in COURT_IS_TAKEN


class SqlAlchemyReservationRepository:
    """A record repository: rows in, rows out, and a version on the way out."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- reading -------------------------------------------------------------

    async def get(self, reservation_id: UUID) -> Reservation | None:
        row = (
            await self._session.execute(
                select(ReservationORM).where(ReservationORM.id == reservation_id)
            )
        ).scalar_one_or_none()
        return None if row is None else _reservation_of(row)

    async def overlapping(
        self, *, court_ids: Sequence[UUID], window: TimeRange
    ) -> list[Reservation]:
        """The live claims on those courts that touch ``window``.

        The overlap is written the same way `TimeRange.overlaps` writes it and
        the same way the exclusion constraint reads it — half-open, so a claim
        ending exactly at ``window.start`` is not returned. Three spellings of
        one rule is already one too many; three *disagreeing* spellings is the
        defect ADR-0035 was written about.
        """

        if not court_ids:
            return []
        rows = await self._all(
            select(ReservationORM)
            .where(
                ReservationORM.court_id.in_(list(court_ids)),
                ReservationORM.released_at.is_(None),
                ReservationORM.claimed_from < window.end,
                ReservationORM.claimed_to > window.start,
            )
            .order_by(*_history_order())
        )
        return [_reservation_of(row) for row in rows]

    async def for_court(self, court_id: UUID) -> list[Reservation]:
        rows = await self._all(
            select(ReservationORM)
            .where(ReservationORM.court_id == court_id)
            .order_by(*_history_order())
        )
        return [_reservation_of(row) for row in rows]

    async def for_match(self, match_id: UUID) -> Reservation | None:
        rows = await self._all(
            select(ReservationORM)
            .where(
                ReservationORM.holder_kind == HolderKind.MATCH.value,
                ReservationORM.match_id == match_id,
                ReservationORM.released_at.is_(None),
            )
            .order_by(*_history_order())
        )
        return _reservation_of(rows[0]) if rows else None

    async def _all(self, statement: Select[Any]) -> Sequence[Any]:
        return (await self._session.execute(statement)).scalars().all()

    # -- writing -------------------------------------------------------------

    async def add(self, reservation: Reservation) -> Reservation:
        """Claim the court, inside a savepoint, or refuse with the court's name.

        The savepoint is not caution. Without it the first refused claim leaves
        the transaction unusable, and the re-ask this context is built around
        fails for an unrelated reason three frames away.
        """

        try:
            async with self._session.begin_nested():
                self._session.add(self._row(reservation, version=0))
        except DBAPIError as error:
            if _means_the_court_is_taken(error):
                raise CourtAlreadyClaimed() from error
            raise
        reservation.version = 0
        return reservation

    async def save(self, reservation: Reservation) -> Reservation:
        """Bump the version or refuse, then write the columns.

        The version guard runs in the same statement that bumps it, so a second
        writer that read the same reservation loses on ``rowcount`` rather than
        on whichever column it happened to touch. The **exclusion** constraint is
        a different guard answering a different question, and a reassignment can
        lose to either: the version means *somebody else edited this*, the
        exclusion means *somebody else holds that court*.
        """

        try:
            async with self._session.begin_nested():
                result = await self._session.execute(
                    update(ReservationORM)
                    .where(
                        ReservationORM.id == reservation.id,
                        ReservationORM.version == reservation.version,
                    )
                    .values(
                        **self._columns(reservation),
                        version=reservation.version + 1,
                    )
                )
                # `session.execute` is typed as returning `Result`, which has no
                # `rowcount`; a DML statement always yields a `CursorResult`.
                if cast(CursorResult[Any], result).rowcount != 1:
                    raise ConcurrentReservationModification()
        except DBAPIError as error:
            if _means_the_court_is_taken(error):
                raise CourtAlreadyClaimed() from error
            raise

        reservation.version += 1
        return reservation

    def _columns(self, reservation: Reservation) -> dict[str, Any]:
        return {
            "court_id": reservation.court_id,
            "category_id": reservation.category_id,
            "played_from": reservation.played.start,
            "played_to": reservation.played.end,
            "claimed_from": reservation.claimed.start,
            "claimed_to": reservation.claimed.end,
            "released_at": reservation.released_at,
            **_holder_columns(reservation.holder),
        }

    def _row(self, reservation: Reservation, *, version: int) -> ReservationORM:
        return ReservationORM(
            id=reservation.id,
            club_id=reservation.club_id,
            version=version,
            **self._columns(reservation),
        )

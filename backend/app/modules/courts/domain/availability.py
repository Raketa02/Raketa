"""Availability, computed. There is no availability number anywhere.

ADR-0035: *"Availability is a projection over reservations, never a stored
number."* Which is what stops it drifting from the thing it summarises — the
counter alternative the same decision rejected has to be decremented by the
club's own private bookings too, and a count kept beside the rows it counts is a
second thing to keep true.

Both functions here are **pure and take everything they read**. The repository
fetches the reservations that could possibly matter; this decides. That split is
what lets *"is a court of this category free for this window"* be tested without
a database, and it is why `pick` is deterministic: the funnel above it must give
the same answer twice for the same facts, and a set iteration order is not that.
"""

from __future__ import annotations

from typing import Iterable, Sequence
from uuid import UUID

from app.modules.courts.domain.reservation import Reservation
from app.modules.courts.domain.time_range import TimeRange


def claimed_courts(
    reservations: Iterable[Reservation], window: TimeRange
) -> frozenset[UUID]:
    """Which courts are spoken for across ``window``.

    A **released** reservation claims nothing: it is history, kept so a court's
    booking history is answerable, and the partial exclusion constraint ignores
    it for the same reason.
    """

    return frozenset(
        reservation.court_id
        for reservation in reservations
        if reservation.is_live and reservation.claimed.overlaps(window)
    )


def free_courts(
    *,
    courts: Sequence[UUID],
    reservations: Iterable[Reservation],
    window: TimeRange,
) -> tuple[UUID, ...]:
    """The courts of a category with nothing claiming them across ``window``.

    Order is ``courts``' order, unchanged. The caller hands in the club's live
    courts in catalogue order, so two identical asks pick the same court — which
    is what makes a losing race legible as *somebody took court 3* rather than
    as the funnel having changed its mind.
    """

    taken = claimed_courts(reservations, window)
    return tuple(court for court in courts if court not in taken)


def pick_court(
    *,
    courts: Sequence[UUID],
    reservations: Iterable[Reservation],
    window: TimeRange,
) -> UUID | None:
    """The first free court, or nothing — *"`pickCourt` returns the first
    available one"*, with the mechanism ADR-0035 gave it.

    ``None`` is not an error and not a race: it is the query result the whole
    decision turns on. Nothing was free.
    """

    free = free_courts(courts=courts, reservations=reservations, window=window)
    return free[0] if free else None

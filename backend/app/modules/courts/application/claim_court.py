"""Ask for a court of a category, for a window, and be given one or refused.

ADR-0035's central path. Three things about it are decisions rather than code:

**The scan is not the guarantee.** Free courts are found by asking reservations,
and then the claim is written and the *database* decides. Two matches crossing
their hold threshold in the same second both scan, both see court 3 free, and
both try — and the exclusion constraint refuses the second. Read ordering is not
being trusted with anything; it is being used to pick.

**A refused claim is a re-ask, not a failure.** ``CourtAlreadyClaimed`` means
somebody won the race, and the answer to that is to look again with that court
removed. Only when nothing is free does a caller hear ``InventoryLost`` — which
is why *"nothing was free"* is the single story ADR-0035 promises the player,
and why losing inventory is always a query result and never a race outcome.

**The loop is bounded by the courts, not by an attempt count.** Each refusal
eliminates exactly one court, and eliminated courts are remembered for this ask.
A bare retry count would either give up while courts remained or spin against a
conflicting write that has not committed yet — the second inserter *waits* on the
first transaction, so re-scanning alone can hand back the same court forever.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.courts.application.commands import ClaimCourtCommand
from app.modules.courts.domain.availability import free_courts
from app.modules.courts.domain.errors import CourtAlreadyClaimed, InventoryLost
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.courts.domain.reservation import (
    Holder,
    Reservation,
    claimed_interval,
)
from app.modules.courts.domain.time_range import TimeRange
from app.shared.ids import new_uuid


class ClaimCourt:
    """*A court of this category, for this window.*"""

    def __init__(
        self,
        clubs: ClubRepository,
        reservations: ReservationRepository,
        uow: UnitOfWork,
    ) -> None:
        self._clubs = clubs
        self._reservations = reservations
        self._uow = uow

    async def execute(self, command: ClaimCourtCommand) -> Reservation:
        reservation = await self.claim(
            club_id=command.club_id,
            category_id=command.category_id,
            played=command.played,
            holder=command.holder,
        )
        await self._uow.commit()
        return reservation

    async def claim(
        self,
        *,
        club_id: UUID,
        category_id: UUID,
        played: TimeRange,
        holder: Holder,
    ) -> Reservation:
        """The claim, without committing.

        Public and separate from ``execute`` for one reason, and it is ADR-0035's:
        *"a seat payment that earns a court, and the court it earns, are one
        event or they are a bug."* A caller that has its own write to join — a
        booking here, a seat payment in `Raketa02/Raketa#70` — takes this and
        commits once. A committing claim would make that transaction unwritable
        from the outside.
        """

        club = await self._clubs.get(club_id)
        if club is None:
            raise ClubNotFound()

        category = club.category(category_id)
        if category.is_retired:
            # ADR-0079: *no free court* and *no courts at all* are one answer,
            # and a retired category is the second. A category nobody may sell
            # is not a not-found — it existed, and the player's story is that
            # there is nothing to have.
            raise InventoryLost()

        # Identity on the club's own number: `ClubPolicy` refuses a negative
        # turnaround at construction, and there is no platform floor here for
        # the same reason there is none under `maxHoldAge` (ADR-0078). Whether
        # it applies at all is the *holder's* answer, given by
        # `claimed_interval`, and it is asked exactly once so the interval that
        # is scanned for and the interval that is written are one value.
        turnaround = club.policy_now.turnaround_min
        claimed = claimed_interval(played, holder, turnaround)
        catalogue = tuple(court.id for court in club.courts_in(category_id))

        blocked: set[UUID] = set()
        while True:
            candidates = tuple(c for c in catalogue if c not in blocked)
            overlapping = await self._reservations.overlapping(
                court_ids=candidates, window=claimed
            )
            free = free_courts(
                courts=candidates, reservations=overlapping, window=claimed
            )
            if not free:
                raise InventoryLost()

            try:
                return await self._reservations.add(
                    Reservation.claim(
                        reservation_id=new_uuid(),
                        club_id=club_id,
                        court_id=free[0],
                        category_id=category_id,
                        played=played,
                        holder=holder,
                        turnaround=turnaround,
                    )
                )
            except CourtAlreadyClaimed:
                # Somebody reached this court first. Take it out of *this* ask —
                # re-scanning alone would hand it back, because the writer that
                # beat us may not have committed yet.
                blocked.add(free[0])

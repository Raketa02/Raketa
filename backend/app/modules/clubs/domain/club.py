"""The Club aggregate: a record with a version, and history on three facts.

ADR-0077, the last of ADR-0002's five per-context choices, and the only one that
is neither a plain record nor an event-sourced stream. **Not** event-sourced: the
hold ladder reads policy on every evaluation and every card on Now needs its
club, so rehydration would sit on the busiest path in the product. **Not** a
record plus an audit table either: that is the dual write ADR-0017 refused,
because the day the row and the log disagree there is nothing to say which one
lied. There is one representation of a policy here — the open row **is** the
policy in force.

**One aggregate.** ``ClubPolicy`` is a value the club holds, not a second
aggregate: a separate one would have exactly one invariant, *"belongs to a
club"*, which is not an invariant. The hold ladder wanting to ask a policy
question without loading a club is an interface concern answered by a port.

**No outbox.** Clubs does not inherit ADR-0034's announcement obligation:
nothing has to *react* to a policy change, because the ladder is evaluated on
current facts and never latches, and availability is a query over reservations.
ADR-0071 narrowed that pattern to *a named future reader*, and Clubs has none.
Effective-dated rows can be projected into events after the fact; the reverse is
not true, which is why the asymmetry favours waiting.

**The domain never reads the past.** Every read here is *as of now*. Where a
value must be honoured **as booked** — a cancellation window in force when a
player committed — ADR-0077 puts the fix on the match record as a Constitutive
fact, not in a temporal query, so no state on Now inherits another aggregate's
fold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import final
from uuid import UUID

from app.kernel import Grosze, Instant, Sport, Zone

from app.modules.clubs.domain.catalogue import Court, CourtCategory
from app.modules.clubs.domain.errors import (
    CategoryAlreadyRetired,
    CategoryNameAlreadyUsed,
    CategoryNotFound,
    CourtAlreadyRetired,
    CourtNotFound,
)
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.series import Series, series_from
from app.modules.clubs.domain.value_objects import (
    SYSTEM,
    CategoryName,
    ChangedBy,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
)


@final
@dataclass
class Club:
    """One venue: what it is, what it charges, and the three facts that remember.

    ``version`` is the **stored** row version and is not touched by the methods
    below — the repository compares it on the way out and bumps it. An aggregate
    that incremented its own would have to be told what the store did next, and
    the two counters would be one fact in two places.
    """

    id: UUID
    name: ClubName
    address: StreetAddress
    point: GeoPoint
    timezone: Zone
    pricing: ClubPricing

    #: The three series. Everything above this line is a mutable column: a club
    #: renaming itself is not a dispute (ADR-0077).
    policy: Series[ClubPolicy]
    payout: Series[PayoutDestination]
    categories: list[CourtCategory] = field(default_factory=list)
    courts: list[Court] = field(default_factory=list)

    version: int = 0

    #: When this club's row was written, read back from the store and never set
    #: here. It is a fact about the record rather than about the venue — a club
    #: that has traded for forty years is *new on Raketa* the week it registers —
    #: and it is `None` on a club that has not been through the store yet, which
    #: is the only state in which nothing can have stamped it.
    created_at: Instant | None = None

    # -- the record ---------------------------------------------------------

    @classmethod
    def found(
        cls,
        *,
        club_id: UUID,
        name: ClubName,
        address: StreetAddress,
        point: GeoPoint,
        timezone: Zone,
        pricing: ClubPricing,
        policy: ClubPolicy,
        payout: PayoutDestination,
        at: Instant,
        changed_by: ChangedBy = SYSTEM,
    ) -> "Club":
        """A new club, with the first row of each of its two club-wide series.

        Both series open at once and neither may be absent: a club with no policy
        would leave the hold ladder reading nothing, and a club with no payout
        destination is one that cannot be paid. The court catalogue starts empty,
        because a club with no courts yet is an ordinary state during authoring.
        """

        return cls(
            id=club_id,
            name=name,
            address=address,
            point=point,
            timezone=timezone,
            pricing=pricing,
            policy=series_from(policy, at=at, changed_by=changed_by),
            payout=series_from(payout, at=at, changed_by=changed_by),
        )

    def rename(self, name: ClubName) -> None:
        self.name = name

    def relocate(
        self, *, address: StreetAddress, point: GeoPoint, timezone: Zone
    ) -> None:
        """The three location facts move together, because they describe one door.

        Separately, a club could carry last year's point beside this year's
        address, and the distance on every card would be quietly wrong.
        """

        self.address = address
        self.point = point
        self.timezone = timezone

    def reprice(self, pricing: ClubPricing) -> None:
        self.pricing = pricing

    # -- series 1: the policy ------------------------------------------------

    @property
    def policy_now(self) -> ClubPolicy:
        """The policy in force. **The only policy read the domain ever makes.**

        Never ``None``: ``found`` opens the series and nothing closes it, so a
        club that exists has a policy. A club whose series had somehow been left
        closed would be one the ladder reads nothing from, and that is a state
        this type refuses rather than represents.
        """

        current = self.policy.current
        if current is None:  # pragma: no cover - unreachable through this type
            raise ValueError(f"club {self.id} has no policy in force")
        return current

    def change_policy(
        self, policy: ClubPolicy, *, at: Instant, changed_by: ChangedBy = SYSTEM
    ) -> None:
        """Close the row in force and open a new one. Never an update in place.

        Unconditional, including when the new policy equals the old one: the
        authoring screen is authoring a *version*, and a club that re-asserted
        its policy on Friday said so on Friday. Collapsing that would be the
        model deciding a human's action was not worth recording.
        """

        self.policy = self.policy.opened(policy, at=at, changed_by=changed_by)

    # -- series 2: the payout destination ------------------------------------

    @property
    def payout_now(self) -> PayoutDestination:
        current = self.payout.current
        if current is None:  # pragma: no cover - unreachable through this type
            raise ValueError(f"club {self.id} has no payout destination")
        return current

    def change_payout_destination(
        self,
        destination: PayoutDestination,
        *,
        at: Instant,
        changed_by: ChangedBy = SYSTEM,
    ) -> None:
        self.payout = self.payout.opened(
            destination, at=at, changed_by=changed_by
        )

    # -- series 3: the court catalogue ---------------------------------------

    @property
    def live_categories(self) -> tuple[CourtCategory, ...]:
        return tuple(c for c in self.categories if not c.is_retired)

    @property
    def live_courts(self) -> tuple[Court, ...]:
        return tuple(c for c in self.courts if not c.is_retired)

    def category(self, category_id: UUID) -> CourtCategory:
        for candidate in self.categories:
            if candidate.id == category_id:
                return candidate
        raise CategoryNotFound()

    def court(self, court_id: UUID) -> Court:
        for candidate in self.courts:
            if candidate.id == court_id:
                return candidate
        raise CourtNotFound()

    def courts_in(self, category_id: UUID) -> tuple[Court, ...]:
        """The live courts of one category — what ``pickCourt`` scans.

        A category with no live courts is possible and correct: retire every
        court in one and it survives as a group that can never be assigned. The
        ladder must treat *no free court* and *no courts at all* identically,
        which is ``inventoryLost`` in both cases (ADR-0079).
        """

        return tuple(c for c in self.live_courts if c.category_id == category_id)

    def add_category(
        self,
        *,
        category_id: UUID,
        name: CategoryName,
        sport: Sport,
        rate: Grosze,
    ) -> CourtCategory:
        for existing in self.live_categories:
            if existing.name == name:
                raise CategoryNameAlreadyUsed()
        category = CourtCategory(
            id=category_id, name=name, sport=sport, rate=rate
        )
        self.categories.append(category)
        return category

    def reprice_category(self, category_id: UUID, rate: Grosze) -> CourtCategory:
        category = self.category(category_id)
        if category.is_retired:
            raise CategoryAlreadyRetired()
        category.rate = rate
        return category

    def retire_category(self, category_id: UUID, *, at: Instant) -> CourtCategory:
        """Retire a category, and every court still in it.

        A court left pointing at a retired category would be a court that can be
        assigned out of a group nobody may sell, which is the one way this shape
        can lie. Retiring the courts with it is the honest reading of *the club
        no longer offers this*, and each court's own series records it.
        """

        category = self.category(category_id)
        if category.is_retired:
            raise CategoryAlreadyRetired()
        for court in self.courts_in(category_id):
            court.retire(at=at)
        category.retire(at=at)
        return category

    def add_court(
        self,
        *,
        court_id: UUID,
        category_id: UUID,
        label: CourtLabel,
        at: Instant,
        changed_by: ChangedBy = SYSTEM,
    ) -> Court:
        category = self.category(category_id)
        if category.is_retired:
            raise CategoryAlreadyRetired()
        court = Court(id=court_id)
        court.move_to(
            category_id=category_id, label=label, at=at, changed_by=changed_by
        )
        self.courts.append(court)
        return court

    def move_court(
        self,
        court_id: UUID,
        *,
        category_id: UUID,
        label: CourtLabel | None = None,
        at: Instant,
        changed_by: ChangedBy = SYSTEM,
    ) -> Court:
        """Move a court into another category, or relabel it. Ordinary, both.

        Reassignment *within* a category is ordinary too and is not this — that
        happens on a reservation and never touches the catalogue.
        """

        court = self.court(court_id)
        if court.is_retired:
            raise CourtAlreadyRetired()
        category = self.category(category_id)
        if category.is_retired:
            raise CategoryAlreadyRetired()
        entry = court.entry
        assert entry is not None  # a live court has an open row, by definition
        court.move_to(
            category_id=category_id,
            label=label or entry.label,
            at=at,
            changed_by=changed_by,
        )
        return court

    def retire_court(self, court_id: UUID, *, at: Instant) -> Court:
        court = self.court(court_id)
        if court.is_retired:
            raise CourtAlreadyRetired()
        court.retire(at=at)
        return court

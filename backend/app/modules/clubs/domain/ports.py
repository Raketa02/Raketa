"""What the Club context needs from the outside world, and the one read it
publishes to it.

**Two published reads.** ``ClubDirectory`` (#504): the clubs as the search
projection holds them, for home-club search, join search and anything that names
a group's home club. ``SellableCourtHours`` (#535): the court hours each club can
sell through Raketa, derived and never stored. A consumer reads them and never a
table or a stream, and never gets an aggregate back.

**Two demands on contexts it does not write**: what the official groups at a
club declare (``OfficialGroupSports``), because the desk may not untick a sport
one of them plays (``docs/adr/0182`` §5) and that is a fact about groups; and
which court hours a booking holds (``CourtBookings``), because a court with a
booking ahead cannot be deleted, an hour a booking holds cannot be closed, and
what a club can sell is its pattern **less** what is booked — facts about
bookings, which have no context yet (#541) and one adapter that says so.

**Each repository writes the search projection in the caller's transaction.**
A club's projection is what home-club search and join search read, and a club
edit must be visible to the next search rather than *eventually*
(``docs/adr/0182`` §2) — so ``save`` appends to the stream, enqueues the events
on the outbox and writes the row, all in the unit of work the use case commits,
and there is no second step a caller could forget. The same holds for the
account's row, which is what sign-in and every club request read.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Optional, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.sellable import ClubOffer
from app.modules.users.domain.value_objects import Email


@runtime_checkable
class ClubRepository(Protocol):
    async def load(self, club_id: UUID) -> Optional[Club]:
        """The club as its stream tells it, or ``None`` for a stream that does
        not exist. Its version is what the next ``save`` expects."""
        ...

    async def save(self, club: Club) -> None:
        """Append what the club recorded, enqueue it, and write its search row —
        in the caller's transaction, and without committing it."""
        ...


@runtime_checkable
class ClubAccountRepository(Protocol):
    async def load(self, account_id: UUID) -> Optional[ClubAccount]:
        """The account as its stream tells it, or ``None``. Its version is what
        the next ``save`` expects — the read an act that changes an existing
        account makes, where ``get_by_id`` is the row every request reads."""
        ...

    async def get_by_id(self, account_id: UUID) -> Optional[ClubAccount]:
        """The account, **read from its row**, which is the read every club
        request pays (``docs/adr/0185`` §7). The row carries no stream version,
        so an account read here is saved at version zero and a second write to
        an existing stream is refused as a concurrent one rather than lost."""
        ...

    async def get_by_email(self, email: Email) -> Optional[ClubAccount]:
        """The account that signs in with this email, **among club accounts
        only** — a User holding the same address is somebody else."""
        ...

    async def save(self, account: ClubAccount) -> None:
        """Append what the account recorded, enqueue it, and write its row — in
        the caller's transaction, and without committing it."""
        ...


@runtime_checkable
class ClubCourtsRepository(Protocol):
    """A club's courts and terms: one stream per club, under the club's id.

    **No projection is written beside it**, unlike the club's search row: every
    reader wants one club's whole state, or a derivation over a few clubs' —
    which is a stream read each — and nothing searches courts.
    """

    async def load(self, club_id: UUID) -> ClubCourts:
        """The club's courts as its stream tells them — **an unwritten
        aggregate, never ``None``**, for a club that has done nothing here yet.
        Its version is what the next ``save`` expects."""
        ...

    async def save(self, club: ClubCourts) -> None:
        """Append what the club recorded and enqueue it, in the caller's
        transaction, without committing it."""
        ...


@final
@dataclass(frozen=True, slots=True)
class ClubListing:
    """A club as its search projection holds it: what a player reads about a
    club they did not sign up.

    The point is the club's precise one, as the desk dropped it
    (``docs/adr/0182`` §6); the sports are in the registry's order.
    """

    id: UUID
    name: str
    district: str
    sports: tuple[Sport, ...]
    latitude: float
    longitude: float


@runtime_checkable
class ClubDirectory(Protocol):
    """**What this context publishes to the rest of the platform**: the clubs,
    read off the search projection and nothing else (``docs/adr/0182`` §2).

    Home-club search and join search both read it (``docs/adr/0183`` §9), and so
    does anything that names a group's home club. It never answers with an
    aggregate, so a reader has no path to change a club.
    """

    async def listed(self, club_ids: Collection[UUID]) -> Mapping[UUID, ClubListing]:
        """Each of these clubs. A club that does not exist is absent."""
        ...

    async def matching(self, text: str) -> Sequence[ClubListing]:
        """Every club whose name or district contains ``text`` anywhere, **both
        folded by** ``clubs/domain/folding.py`` — the one function the stored
        copies were folded by, so the two sides of a match cannot disagree about
        what a letter is. ``text`` is matched as typed: ``%`` and ``_`` are
        characters, not patterns. In no particular order."""
        ...


# --------------------------------------------------------------------------- #
# A demand on groups: what the club's official groups play
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class DeclaringGroup:
    """An official group at a club, by its name, and the sports it declares."""

    name: str
    sports: frozenset[Sport]


@runtime_checkable
class OfficialGroupSports(Protocol):
    """What the official groups at a club play — **as each declared it**
    (``docs/adr/0183`` §3). Player groups play whatever their members are rated
    in and declare nothing, so they are never here."""

    async def declared_at(self, club_id: UUID) -> Sequence[DeclaringGroup]:
        """Every official group at this club, in no particular order."""
        ...


# --------------------------------------------------------------------------- #
# A demand on bookings: which court hours a booking holds
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class TakenCourtHour:
    """A court hour a booking holds — **booked**, or **reserved** while an On
    request club answers (the mechanics §16.8: *while a request waits, the hour
    stays reserved for it*). Which of the two is the booking's business; to a
    court it is the same hour gone."""

    court_id: UUID
    start: Instant
    #: The booking holding it, so a refusal can link to what to cancel first
    #: (the screens B3).
    booking_id: UUID


@runtime_checkable
class CourtBookings(Protocol):
    """The court hours of a club that bookings hold, **in bookings' words and
    never in a booking's shape**: a court, an hour and whose it is.

    Asked by three acts and one read: deleting a court or changing its sport
    (refused while a booking is ahead of it), closing hours (refused over a
    booked one) and the sellable hours (the pattern less what is taken)."""

    async def taken(
        self, club_id: UUID, *, start: Instant, end: Instant | None = None
    ) -> Sequence[TakenCourtHour]:
        """Every court hour of this club a booking holds, starting at or after
        ``start`` and before ``end`` — **for ever, when ``end`` is ``None``**. In
        no particular order."""
        ...


# --------------------------------------------------------------------------- #
# Published: the court hours a club can sell
# --------------------------------------------------------------------------- #


@runtime_checkable
class SellableCourtHours(Protocol):
    """**What this context publishes about courts**: the court hours each club
    can sell through Raketa, derived from its pattern, its exceptions and what
    bookings hold — never stored hour by hour (``docs/adr/0189`` §5). The
    proposer, posting and the fill read it here rather than a court or a
    stream, so a card and the club cannot disagree about what is for sale.
    """

    async def between(
        self,
        club_ids: Collection[UUID],
        *,
        start: Instant,
        end: Instant,
        now: Instant,
    ) -> Mapping[UUID, ClubOffer]:
        """Each **live** club's offer among the hours starting from ``start``
        until ``end``, as of ``now`` — an hour past its book-by at ``now`` is not
        for sale. A club that is not live, or does not exist, is absent. In the
        order the ids were given."""
        ...

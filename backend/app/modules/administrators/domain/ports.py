"""What the Administrators context needs, in its own words.

**Two ports are this context's own store**: the aggregate repository, whose
``save`` writes the ``administrators`` projection in the caller's transaction,
and the directory that reads it back — and writes the one thing on it no event
carries, *last used* (``docs/adr/0184`` §1).

**The other three are demands on contexts it does not write.** The account an
administratorship belongs to is a User, and everything done to one — opened by
an invitation, its password set or cleared, whether it acts as a player — is
done by ``users`` on its own stream (``AccountHolders``). A club's name is read
off the clubs' published directory (``ClubNames``). And which official groups
each Administrator was given is a fact about groups (``OfficialGroupAssignments``)
— declared here and **signed in ``groups/infrastructure/``**, because ``groups``
already reads this context and an adapter here would point the arrow back.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Optional, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.administrators.domain.administrator import (
    Administrator,
    AdministratorStanding,
    AdministratorState,
    standing_of,
)
from app.modules.users.domain.value_objects import Email, Name

# --------------------------------------------------------------------------- #
# This context's own store
# --------------------------------------------------------------------------- #


@runtime_checkable
class AdministratorRepository(Protocol):
    async def load(self, administrator_id: UUID) -> Optional[Administrator]:
        """The administratorship as its stream tells it, or ``None``. Its
        version is what the next ``save`` expects."""
        ...

    async def at_club(self, club_id: UUID, email: Email) -> Optional[Administrator]:
        """The one Administrator this club has for this email, removed
        included — there is at most one, and inviting a removed person again
        continues its stream (``docs/adr/0184`` §1)."""
        ...

    async def save(self, administrator: Administrator) -> None:
        """Append what it recorded, enqueue it, and write its projection row —
        in the caller's transaction, without committing it."""
        ...


@final
@dataclass(frozen=True, slots=True)
class AdministratorListing:
    """One administratorship as the projection holds it."""

    id: UUID
    club_id: UUID
    email: str
    name: str
    state: AdministratorState
    account_id: Optional[UUID]
    expires_at: Optional[Instant]
    #: When the administrator profile was last used, to the hour
    #: (``docs/adr/0184`` §1). ``None`` until the first use.
    last_used_at: Optional[Instant]

    def standing(self, *, now: Instant) -> AdministratorStanding:
        return standing_of(self.state, expires_at=self.expires_at, now=now)


@runtime_checkable
class AdministratorDirectory(Protocol):
    """The ``administrators`` projection, read — and *last used*, written.

    Written by ``AdministratorRepository.save`` in the act's transaction, so a
    read straight after a write already sees it.
    """

    async def of_club(self, club_id: UUID) -> Sequence[AdministratorListing]:
        """Every administratorship this club has that is not removed, in no
        particular order."""
        ...

    async def active_for(self, account_id: UUID) -> Sequence[AdministratorListing]:
        """Every club this account runs the groups of, now."""
        ...

    async def active_at(
        self, club_id: UUID, account_id: UUID
    ) -> Optional[AdministratorListing]:
        """This account's administratorship at this club, **only while it is
        active** — the one read the administrator guard makes."""
        ...

    async def active_among(
        self, administrator_ids: Collection[UUID]
    ) -> Sequence[AdministratorListing]:
        """Those of these administratorships that are **active now**, in no
        particular order — who runs a set of official groups, read in one
        question about the set (#509). A removed or never-accepted one is
        absent."""
        ...

    async def invited_as(self, email: Email) -> Sequence[AdministratorListing]:
        """Every administratorship waiting on this address, at any club —
        expired ones included; the reader decides what is still pending."""
        ...

    async def record_use(self, administrator_id: UUID, *, at: Instant) -> None:
        """The administrator profile was used ``at``. Not committed. **The one
        write to this row no event carries**: a use is not a fact any context
        reads, and a stream of them would be a stream of page views."""
        ...


# --------------------------------------------------------------------------- #
# Demands on the contexts it does not write
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class AccountHolder:
    """The account an address signs in with, as far as an invitation needs to
    know it: which one, and whether anything can sign in to it — false only
    between a club clearing its password and a new one being set."""

    id: UUID
    can_sign_in: bool


@runtime_checkable
class AccountHolders(Protocol):
    """The Users behind administratorships — **everything done to one is done
    by ``users``, on its own stream**, in the caller's transaction."""

    async def holder_of(self, email: Email) -> Optional[AccountHolder]:
        """The account that signs in with this address, or ``None``."""
        ...

    async def open_account(
        self, *, email: Email, name: Name, password_hash: str, at: Instant
    ) -> UUID:
        """Open the account an invitation is for: the club-typed name, no
        nickname, no Adult attestation (``docs/adr/0185`` §4–§5)."""
        ...

    async def set_password(
        self, account_id: UUID, *, password_hash: str, at: Instant
    ) -> None:
        """A new password, and ``at`` the instant every older access token
        stops counting."""
        ...

    async def clear_password(self, account_id: UUID, *, at: Instant) -> None:
        """No password at all, from ``at`` (``docs/adr/0184`` §6)."""
        ...

    async def acts_as_player(self, account_id: UUID) -> bool:
        """**Whether this account holds more than administrator profiles**
        (``docs/adr/0185`` §1–§2): it has given the Adult attestation — the
        first act of playing, which every sign-up gave and *Start playing* asks
        for — or it has a Player profile. What the club's *Reset password* is
        refused on, and what ``/users/me`` reports."""
        ...


@runtime_checkable
class ClubNames(Protocol):
    """A club's name, from the clubs' published directory."""

    async def names_of(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """Each of these clubs' names. A club that does not exist is absent."""
        ...


@final
@dataclass(frozen=True, slots=True)
class AssignedGroup:
    """An official group at a club, and the Administrator it was last given
    to — at its creation, or by the club's latest handover."""

    id: UUID
    name: str
    administrator_id: UUID


@runtime_checkable
class OfficialGroupAssignments(Protocol):
    """Which of a club's official groups are given to which of its
    Administrators — the Administrators table's *groups* column (#510)."""

    async def assigned_at(self, club_id: UUID) -> Sequence[AssignedGroup]:
        """Every official group at this club and whom it names, in no
        particular order — **one naming an administratorship that is no longer
        active included**: whether a group is still run by whom it names is
        this context's to decide (``docs/adr/0184`` §7), never the answer's."""
        ...


async def club_name_of(clubs: ClubNames, club_id: UUID) -> str:
    """One club's name — of a club an Administrator belongs to, which a signed-in
    club created and nothing deletes, so a club with no name is a broken store
    rather than an answer."""

    name = (await clubs.names_of([club_id])).get(club_id)
    if name is None:
        raise RuntimeError(f"club {club_id} has no name")
    return name


# --------------------------------------------------------------------------- #
# Where an invitation's button goes
# --------------------------------------------------------------------------- #

#: The page an invitation's link opens, under the public site:
#: ``<site>/invite/<token>`` — the club's reset of an administrator included
#: (``docs/adr/0186`` §3). A path the public site and the app's link handling
#: claim, so it is not configuration; only the address in front of it is.
INVITE_PATH: Final = "/invite/"


@final
@dataclass(frozen=True, slots=True)
class InvitationLinks:
    """Where an invitation email's button goes: the public site's
    ``/invite/<token>`` for somebody who has a password to set, and the app
    itself for an account that only has to accept. Both addresses are
    configuration (``docs/adr/0187`` §7); the shapes are not."""

    site: str
    app_scheme: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "site", self.site.rstrip("/"))

    def invitation(self, token: str) -> str:
        return f"{self.site}{INVITE_PATH}{token}"

    def app(self) -> str:
        return f"{self.app_scheme}://"

"""What the Groups context needs from the outside world, in its own words.

**Two ports are this context's own store**: the aggregate repository, whose
``save`` writes the groups and group-members projections in the caller's
transaction, and the directory that reads those projections back. **The other
five are demands on contexts it does not write** — clubs, rating, users with the
Player profile, and the Player profile again for where the reader is — each
declared here in this context's vocabulary and answered by an adapter in
``infrastructure/`` over that provider's own port, never its table.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Optional, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Sport, invariant
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.value_objects import GroupCode, GroupName, JoinPolicy

# --------------------------------------------------------------------------- #
# This context's own store
# --------------------------------------------------------------------------- #


@runtime_checkable
class GroupRepository(Protocol):
    async def load(self, group_id: UUID) -> Optional[Group]:
        """The group as its stream tells it, or ``None`` for a stream that does
        not exist. Its version is what the next ``save`` expects."""
        ...

    async def save(self, group: Group) -> None:
        """Append what the group recorded, enqueue it, and write its projections
        — in the caller's transaction, and without committing it."""
        ...


@final
@dataclass(frozen=True, slots=True)
class GroupListing:
    """One group as the projections hold it: what a row, a card and a page are
    drawn from.

    ``members`` is every Group member **in the order they joined**, the Owner
    first, so a count is its length and *the first to join* is a prefix.
    ``waiting`` is everybody whose Join request waits, **in the order they
    asked** — the Owner's *Want to join* queue, and what a reader's relation to
    the group is read from.
    """

    id: UUID
    name: GroupName
    home_club_id: UUID
    join_policy: JoinPolicy
    owner_id: UUID
    code: GroupCode
    members: tuple[UUID, ...]
    waiting: tuple[UUID, ...] = ()

    @property
    def member_count(self) -> int:
        return len(self.members)


@runtime_checkable
class GroupDirectory(Protocol):
    """The groups and group-members projections, read.

    Written only by ``GroupRepository.save``, in the transaction of the act, so
    a read straight after a write already sees it.
    """

    async def listings(
        self, group_ids: Collection[UUID]
    ) -> Mapping[UUID, GroupListing]:
        """Each of these groups. A group that does not exist is absent."""
        ...

    async def groups_of(self, player_id: UUID) -> Sequence[UUID]:
        """Every group this player belongs to, **newest joined first**."""
        ...

    async def listings_at(
        self, club_ids: Collection[UUID]
    ) -> Mapping[UUID, Sequence[GroupListing]]:
        """Every group at each of these home clubs. A club with none is absent."""
        ...

    async def with_code(self, code: GroupCode) -> GroupListing | None:
        """The group whose link carries this code, or ``None`` for a code no
        group has — a link that leads nowhere."""
        ...

    async def named(self, text: str) -> Mapping[UUID, frozenset[UUID]]:
        """Every group whose name contains ``text`` **anywhere, once both are
        folded** — by the fold the stored copy was made with, the one clubs'
        search folds by (``docs/adr/0183`` §9) — **by home club**. Ids only: a
        search reads the members of the page it serves and of nothing else."""
        ...


@runtime_checkable
class GroupCodeMinter(Protocol):
    """A code no group has, to be carried by a new group's link for ever."""

    async def mint(self) -> GroupCode: ...


# --------------------------------------------------------------------------- #
# Clubs: the home club, and the clubs a player searches
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class HomeClub:
    """A club as a group's home and as a search result: what it is called,
    where it is, and what it offers. The point is the club's precise one, as its
    desk dropped it (``docs/adr/0182`` §6)."""

    id: UUID
    name: str
    district: str
    sports: tuple[Sport, ...]
    latitude: float
    longitude: float


@runtime_checkable
class HomeClubs(Protocol):
    """Every club in Raketa, as somewhere a group can live."""

    async def by_id(self, club_ids: Collection[UUID]) -> Mapping[UUID, HomeClub]:
        """Each of these clubs. A club that does not exist is absent."""
        ...

    async def matching(self, text: str) -> Sequence[HomeClub]:
        """Every club whose name or district contains ``text`` **anywhere, once
        both are folded** — lower case, accents stripped, *ł* read as *l* — by
        the one fold the clubs' own search copies were made with
        (``docs/adr/0182`` §2). In no particular order: ordering is this
        context's rule, not the provider's."""
        ...


# --------------------------------------------------------------------------- #
# Rating: who is rated in what
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class SportLevel:
    """One sport somebody is rated in, and their **published** Level in it —
    the figure a rating route already prints, never re-derived here."""

    sport: Sport
    level: float


@runtime_checkable
class RatedGroupMembers(Protocol):
    """Which of these players hold a Skill rating in each sport, and at what
    Level.

    **Read and never held**: the dots and the Games tab's *N of M* are computed
    when a group is read (``docs/adr/0183`` §6), so a rating earned or a member
    leaving moves them on the next read with nothing to keep in step — and a
    Join request shows the Level the person holds when the Owner looks, not the
    one they held when they asked.
    """

    async def rated_in(
        self, player_ids: Collection[UUID]
    ) -> Mapping[Sport, frozenset[UUID]]:
        """For each sport, the ones among these players rated in it. A sport
        nobody here is rated in may be absent or empty — both mean none."""
        ...

    async def levels_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, tuple[SportLevel, ...]]:
        """Every sport each of these players is rated in, **with its Level as
        RacketSkill published it**, in the registry's order — what a Join
        request shows its Owner (*Padel 2,44 · Tennis 2,60*). A player rated in
        nothing may be absent or empty — both mean none."""
        ...


# --------------------------------------------------------------------------- #
# Users and the Player profile: a member's face
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class GroupFace:
    """What a member is called and what they look like — a name, a photograph,
    and nothing else.

    ``name`` is the **Name** and never the nickname (``docs/adr/0171`` §4).
    ``None`` for an account ``users`` can no longer name; **the member keeps
    their seat**, because they are still in the group. ``photo_id`` and
    ``photo_url`` are present **exactly together**, and neither means the
    client draws the player's initials.
    """

    player_id: UUID
    name: str | None = None
    photo_id: UUID | None = None
    photo_url: str | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.photo_id is None) == (self.photo_url is None),
            f"a photograph with only half an address: {self!r}",
        )


@runtime_checkable
class GroupFaces(Protocol):
    """A fourth spelling of the names read, and the duplication is the decision:
    two contexts needing *what do I draw on this seat* is not a reason for one to
    own the other's vocabulary (the conversations' ``MemberFaces`` says the same
    of the three before it)."""

    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, GroupFace]:
        """Each of these players, in **one question about the union** — never
        one per seat. A player absent from the answer keeps their seat."""
        ...

    async def names_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """The Name of each of these players and **nothing else** — a face with
        no photograph, for a line that names somebody and draws nobody: the
        Owner on *Karol approves joins*. One question about the union; a player
        ``users`` cannot name is absent."""
        ...


# --------------------------------------------------------------------------- #
# The Player profile: where the reader is
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class ReaderArea:
    """The reader's Location area — the coarse cell and never anything finer
    (``player_profile/domain/location.py``)."""

    latitude: float
    longitude: float


@runtime_checkable
class ReaderAreas(Protocol):
    async def of(self, player_id: UUID) -> ReaderArea | None:
        """This player's Location area, or ``None`` for somebody with none —
        who then gets clubs A–Z and no distance, because nothing should pretend
        to know where they are (``docs/adr/0182`` §6)."""
        ...

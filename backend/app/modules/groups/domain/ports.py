"""What the Groups context needs from the outside world, in its own words.

**Two ports are this context's own store**: the aggregate repository, whose
``save`` writes the groups, group-members and join-requests projections in the
caller's transaction, and the directory that reads those projections back.
**The other eight are demands on contexts it does not write** — clubs, rating,
users with the Player profile, the Player profile again for where the reader
is, the Player Score, administrators, and the games a group gave birth to —
each declared here in this context's vocabulary and answered by an adapter in
``infrastructure/`` over that provider's own port, never its table. The last
is answered from outside this context — by Proposals, which knows a group's pool
is filed under the group's id — so ``groups`` never learns a game was booked
(``GroupBornGames``, #542).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import ReliabilityBand
from app.modules.friends.domain.relation import FriendRelation
from app.kernel import Instant, Sport, invariant
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.value_objects import (
    DeclaredSports,
    GroupCode,
    GroupKind,
    GroupName,
    JoinPolicy,
    WhatsAppSize,
)

# --------------------------------------------------------------------------- #
# This context's own store
# --------------------------------------------------------------------------- #


@runtime_checkable
class GroupRepository(Protocol):
    async def load(self, group_id: UUID) -> Optional[Group]:
        """The group as its stream tells it, or ``None`` for a stream that does
        not exist **or that ends in its deletion** — a deleted group is no
        group, and every act on one meets what an act on a missing one meets.
        Its version is what the next ``save`` expects."""
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

    ``members`` is every Group member **in the order they joined** — a player
    group's Owner first — so a count is its length and *the first to join* is a
    prefix. ``waiting`` is everybody whose Join request waits, **in the order
    they asked** — the *Want to join* queue, and what a reader's relation to
    the group is read from. ``joined_at`` is when each member joined — this
    stay, for somebody who left and came back.

    **The kind decides the rest** (``docs/adr/0183`` §3): a player group has an
    ``owner_id``; an official group has none, and its ``administrator_id``,
    ``whatsapp_size`` and ``declared_sports``.
    """

    id: UUID
    name: GroupName
    home_club_id: UUID
    join_policy: JoinPolicy
    owner_id: UUID | None
    code: GroupCode
    members: tuple[UUID, ...]
    waiting: tuple[UUID, ...]
    joined_at: Mapping[UUID, datetime]
    kind: GroupKind
    administrator_id: UUID | None
    whatsapp_size: WhatsAppSize | None
    declared_sports: DeclaredSports | None
    #: When the club handed it to whoever runs it now, while they have not been
    #: told (``docs/adr/0192`` §1).
    handed_over_at: Instant | None = None

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def is_official(self) -> bool:
        return self.kind is GroupKind.OFFICIAL


@final
@dataclass(frozen=True, slots=True)
class GroupCrowd:
    """How big a group is today and how much of it is new — what Hottest groups'
    heat reads of the members (#792, ``docs/adr/0204`` §11)."""

    group_id: UUID
    #: Members today.
    players: int
    #: Of them, the ones whose joining — this stay, for somebody who left and
    #: came back — was after the instant asked about.
    new: int


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

    async def every(self) -> Sequence[UUID]:
        """Every group there is, **oldest created first** — what the proposer
        walks, since every group is a pool (``docs/adr/0189`` §1)."""
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

    async def official_at(self, club_id: UUID) -> Sequence[GroupListing]:
        """Every **official** group at this club, in no particular order —
        whoever runs it or nobody. A player group whose home club it is is not
        the club's, and is never here."""
        ...

    async def run_by(self, administrator_id: UUID) -> Sequence[GroupListing]:
        """Every official group this Administrator runs, **newest created
        first** — the administrator's Groups tab, and the settings rows on
        their You tab."""
        ...

    async def named(self, text: str) -> Mapping[UUID, frozenset[UUID]]:
        """Every group whose name contains ``text`` **anywhere, once both are
        folded** — by the fold the stored copy was made with, the one clubs'
        search folds by (``docs/adr/0183`` §9) — **by home club**. Ids only: a
        search reads the members of the page it serves and of nothing else."""
        ...

    async def crowds(
        self, *, at_least: int, joined_after: Instant
    ) -> Sequence[GroupCrowd]:
        """**Every group with at least ``at_least`` members today**, player or
        official, with how many of them joined after ``joined_after`` — one
        question about every group, counted where the members are kept, so
        Hottest groups reads no group's members it will not show (#792). A
        member who joined and left is in neither count; a Join request is a
        member from its approval. In no particular order."""
        ...

    async def first_joined(
        self, *, after: Instant, by: Instant
    ) -> Mapping[UUID, Instant]:
        """**When each account first joined a group** (#727): every account in
        at least one group, player or official, whose earliest join **among
        the groups it is in now** was after ``after`` and by ``by`` — with that
        join's instant. A join is the moment the account was admitted, so a
        Join request counts from its approval. An account that left every group
        is in none, and absent."""
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

    async def levels_in(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, float]:
        """The **published** Level of each of these players rated in this one
        sport — what a Members row prints beside a name (*Padel 2,71*). Somebody
        not rated in it is absent — the same people ``rated_in`` names for that
        sport, both being read off the one stream a rating is kept in."""
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
    """What a member is called and what they look like — a nickname, a
    photograph, and nothing else.

    ``nickname`` is whole and never written with an @ (``docs/adr/0199`` §1).
    ``None`` for an account ``users`` can no longer name; **the member keeps
    their seat**, because they are still in the group. ``photo_id`` and
    ``photo_url`` are present **exactly together**, and neither means the
    client draws the player's initials.
    """

    player_id: UUID
    nickname: str | None = None
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
        """The nickname of each of these players and **nothing else** — a face
        with no photograph, for a line that names somebody and draws nobody: the
        Owner on *karol approves joins*. One question about the union; a player
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


# --------------------------------------------------------------------------- #
# Player reliability: what the platform watched of a member
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class MemberReliability:
    """A member's **Player reliability** as a Members row prints it — the
    figure in points and its band (*Padel 2,71 · 92 Very high*), copied from
    their record and never re-derived (``docs/adr/0195`` §6)."""

    points: int
    band: ReliabilityBand


@runtime_checkable
class GroupMemberReliability(Protocol):
    """Each member's **Player reliability** — the figure and band their own
    record prints, never re-derived here."""

    async def reliability_of(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, MemberReliability]:
        """Every one of these players' reliability — **all of them**: everyone
        starts at a hundred, so a member nothing has happened to reads 100. One
        question about the set, against one instant."""
        ...


@runtime_checkable
class MemberRelations(Protocol):
    """The reader's relation to each member a Members list draws — the pill or
    tag on the right of the row (``docs/adr/0202`` §1–§2). **The reader's own
    relations and nobody else's**, lent by Friends."""

    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, FriendRelation]:
        """Everybody asked about is answered: ``NONE`` where nothing stands, the
        reader included. One question about the rows."""
        ...


# --------------------------------------------------------------------------- #
# Administrators: who runs an official group now
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class RunningAdministrator:
    """Who runs an official group now: the account behind its Administrator,
    the club they act for, and **the name the club gave them**.

    That name is what **the club's own tables** print — its Groups table names
    the person its Administrators table lists (#510). The player side's
    *approves joins* line says the **account's** nickname, as their admin-tagged
    Members row does, and falls back to this one only where ``users`` cannot
    answer: an Administrator who has never played and has no nickname yet
    (``docs/adr/0199`` §4)."""

    account_id: UUID
    club_id: UUID
    name: str


@runtime_checkable
class GroupAdministrators(Protocol):
    """Who runs each official group **now** (``docs/adr/0183`` §3).

    A group records the Administrator who runs it, and whether that
    administratorship is still active is a fact about administrators — so it is
    **read and never held**: a club removing somebody takes their groups from
    them on the next read, with nothing here to keep in step. The account is
    what a player-side read needs — it joins directly (§7), and its Members
    row carries the **admin** tag — and the name is the approver line's.
    """

    async def running(
        self, administrator_ids: Collection[UUID]
    ) -> Mapping[UUID, RunningAdministrator]:
        """Each of these Administrators, **only while their administratorship
        is active**. A removed one is absent — nobody runs its groups until the
        club hands them over (``docs/adr/0184`` §7) — and so is one still
        invited: nobody is handed a group before they have taken the
        administratorship up (``docs/adr/0183`` §8). One question about the
        set."""
        ...


# --------------------------------------------------------------------------- #
# Games: how many a group gave birth to
# --------------------------------------------------------------------------- #


@runtime_checkable
class GroupBornGames(Protocol):
    """How many games each group **gave birth to** — the club's *Games* figure
    (``docs/adr/0183`` §11), and Hottest groups' *games this week*
    (``docs/adr/0204`` §11). Only a game the group itself picked counts: a game
    two of its members arranged elsewhere never does, because the club would
    read it as the group's work.

    **The games booked in the group** (``docs/adr/0189`` §8): every game its
    pool filled into a booking — answered by an adapter signed in
    ``proposals/infrastructure/``, so the arrow runs ``proposals → groups`` and
    this context knows nothing of proposals or bookings (#542).
    """

    async def born_in(self, group_ids: Collection[UUID]) -> Mapping[UUID, int]:
        """How many games each of these groups gave birth to — one question
        about the set. A group absent from the answer gave birth to none."""
        ...

    async def born_between(
        self, group_ids: Collection[UUID], *, after: Instant, by: Instant
    ) -> Mapping[UUID, int]:
        """How many games booked in each of these groups have **a court time
        after ``after`` and by ``by``** — *games this week* (#792): every one
        not called off, **whether or not it was scored**, a friends game booked
        in the group included. One question about the set; a group absent from
        the answer had none then."""
        ...

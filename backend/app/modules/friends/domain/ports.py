"""The seams this context is built on, each in its own words.

- ``FriendshipRepository`` — the aggregate's, keyed on the pair.
- ``FriendLinkRepository`` and ``FriendLinkCodes`` — a player's Friend link,
  and every code a link ever carried: a fresh one minted, and whose link a code
  is **now** (#748).
- ``FriendshipDirectory`` — the ``friend_relations`` projection, read **from one
  reader's side**: there is no method that answers about two other people,
  which is what keeps *Kuba never learns that Tomek and Magda are friends* a
  property of the port rather than of its callers.
- ``LevelsAskedByTheReader``, ``AsksWaitingOnALevel`` and
  ``LevelAsksOfTheReader`` — the ``friend_level_asks`` projection (#749,
  #764), **three ports for three audiences**: the sports the reader asked each
  friend for, from the reader's side; who is waiting on a friend's level in a
  sport, which names who asked somebody else and so is handed to the one
  subscriber that answers the asks, never to a read; and the asks made **of**
  the reader, from the reader's side — who asked them — for their Home, their
  bell and their *Not now*.
- ``OpenToTheRequester`` — whether a player may be asked by this requester at
  all: the record's rule (b), *Show me to new people* on or a group, a game or a
  friendship shared (``docs/adr/0204`` §2, #791). **Signed in
  ``player_record/infrastructure/``**, so the arrow runs ``player_record →
  friends``.
- ``ReadersBlocks`` — whom the reader blocked, **the reader's own blocks
  only**, which is what hides a blocked player's request from them
  (``docs/adr/0202`` §2).
- ``FriendFaces``, ``FriendLevels``, ``FriendReliabilities`` and
  ``ReadersGroups`` — what the lists draw, each signed over its provider's own
  published read. ``ReadersGroups`` is signed in ``groups/infrastructure/``, so
  the arrow runs ``groups → friends`` and this context imports no group.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import ReliabilityBand
from app.kernel import Instant, Sport, invariant
from app.modules.friends.domain.friendship import Friendship, Where
from app.modules.friends.domain.link import FriendLink, FriendLinkCode
from app.modules.friends.domain.relation import FriendRelation


@runtime_checkable
class FriendshipRepository(Protocol):
    async def load(self, one: UUID, other: UUID) -> Friendship:
        """The pair's stream, replayed — **never ``None``**: a pair with no
        history is a Friendship with nothing standing between them, and its
        first act opens the stream at version one."""
        ...

    async def save(self, friendship: Friendship) -> None:
        """Append the pending events, publish them, and rewrite the pair's two
        projection rows — in the caller's transaction, never committing."""
        ...


@runtime_checkable
class FriendLinkRepository(Protocol):
    async def load(self, owner: UUID) -> FriendLink:
        """The owner's link, replayed — **never ``None``**: a link never read is
        a FriendLink with no code yet."""
        ...

    async def save(self, link: FriendLink) -> None:
        """Append the pending events, publish them, and record the codes they
        made and retired — in the caller's transaction, never committing."""
        ...


@runtime_checkable
class FriendLinkCodes(Protocol):
    async def mint(self) -> FriendLinkCode:
        """A random code **no link has ever carried**, current or replaced."""
        ...

    async def owner_of(self, code: FriendLinkCode) -> UUID | None:
        """Whose link carries ``code`` now — ``None`` for a code replaced, or one
        no link ever carried."""
        ...


@final
@dataclass(frozen=True, slots=True)
class RelationRow:
    """One row of the projection, from the reader's side: the other player, the
    relation as recorded (``SENT``, ``ASKED_YOU`` or ``FRIEND`` — no row is
    ``NONE``), and since when."""

    other_id: UUID
    relation: FriendRelation
    #: When they became friends, or when the request was made.
    since: Instant
    #: On ``ASKED_YOU``: the reader set it aside.
    set_aside: bool = False
    #: On a request: where it was made.
    where: Where | None = None

    def __post_init__(self) -> None:
        invariant(
            self.relation is not FriendRelation.NONE, f"a row of nothing: {self!r}"
        )


@runtime_checkable
class FriendshipDirectory(Protocol):
    async def rows_of(
        self, reader: UUID, *, among: Collection[UUID] | None = None
    ) -> tuple[RelationRow, ...]:
        """Every row on the reader's side — or only those about ``among``, one
        question for the whole set. Nobody's row about anybody else."""
        ...


@runtime_checkable
class LevelsAskedByTheReader(Protocol):
    async def sports_asked_by(
        self, asker: UUID, *, among: Collection[UUID]
    ) -> Mapping[UUID, frozenset[Sport]]:
        """Each of these players the asker ever asked for a level, and in which
        sports — answered or not: the picker's *Asked*. Somebody never asked is
        absent. The asker's own asks alone."""
        ...


@runtime_checkable
class AsksWaitingOnALevel(Protocol):
    async def askers_waiting_on(self, friend: UUID, sport: Sport) -> tuple[UUID, ...]:
        """Everybody who asked ``friend`` for a level in ``sport`` and is not
        answered yet. **Handed only to the subscriber that answers them**
        (``handlers/level_got.py``), never to a read: it names who asked
        somebody else."""
        ...


@final
@dataclass(frozen=True, slots=True)
class AskOfTheReader:
    """An ask for a level made **of the reader**, still waiting and not set
    aside (#764): who asked, in which sport, and when."""

    asker_id: UUID
    sport: Sport
    asked_at: Instant


@runtime_checkable
class LevelAsksOfTheReader(Protocol):
    async def asks_of(self, reader: UUID) -> tuple[AskOfTheReader, ...]:
        """Every ask made of the reader that is **not answered and not set
        aside**, whoever made it — friend or not now, which is the read's to
        decide. The reader's own side alone: who asked them, never whom
        anybody else was asked by."""
        ...


@runtime_checkable
class OpenToTheRequester(Protocol):
    async def open_to(self, addressee: UUID, *, requester: UUID) -> bool:
        """Whether the addressee may be asked by this requester **now**: their
        *Show me to new people* is on, or the two share a group, a game or a
        friendship, or the requester runs a group they are in — **the rule a
        record is reached by** (``docs/adr/0204`` §2), so the ask and the
        record's *Add friend* never disagree. ``False`` for an id nobody
        holds."""
        ...


@runtime_checkable
class ReadersBlocks(Protocol):
    async def blocked_by(self, reader: UUID) -> frozenset[UUID]:
        """Every player **the reader** blocked and has not unblocked. Never who
        blocked the reader: nothing on this port can answer that."""
        ...


@final
@dataclass(frozen=True, slots=True)
class FriendFace:
    """A nickname, whole and never with an @ (``docs/adr/0199`` §1), and a
    photograph — ``photo_id`` and ``photo_url`` exactly together. ``nickname`` is
    ``None`` for an id nobody can name — an account deleted — and every list
    leaves such a row off."""

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
class FriendFaces(Protocol):
    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, FriendFace]:
        """Everybody asked about is answered, in one question about the set."""
        ...


@final
@dataclass(frozen=True, slots=True)
class FriendLevel:
    """A published Level in one sport and its band's name (*2,75 ·
    established*), as rating publishes them — derived from nothing here."""

    sport: Sport
    level: float
    band: str


@runtime_checkable
class FriendLevels(Protocol):
    async def levels_in(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, FriendLevel]:
        """Each of these players rated in ``sport``; anybody unrated is absent."""
        ...


@final
@dataclass(frozen=True, slots=True)
class FriendReliability:
    """Player reliability as a Members row prints it: points and the band."""

    points: int
    band: ReliabilityBand


@runtime_checkable
class FriendReliabilities(Protocol):
    async def reliability_of(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, FriendReliability]:
        """Everybody asked about is answered: everyone starts at a hundred."""
        ...


@final
@dataclass(frozen=True, slots=True)
class ReadersGroup:
    """One group the reader is in: its name and its members, the reader too."""

    group_id: UUID
    name: str
    members: tuple[UUID, ...]


@runtime_checkable
class ReadersGroups(Protocol):
    async def groups_of(self, reader: UUID) -> tuple[ReadersGroup, ...]:
        """Every group the reader is in now, in the order their groups list
        reads."""
        ...

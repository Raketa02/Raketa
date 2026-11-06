"""Every read this context answers — each **from the reader's side alone**
(``docs/adr/0202`` §1–§2; the mechanics §3.6–§3.7).

**The one rule a read adds to the record**: a request from a player the reader
blocked is never shown to the reader. It is applied here, live, from the
reader's own blocks (``as_the_reader_sees``) — never recorded, so the requester's
*request sent* is the same bytes as a request set aside would show them, and
unblocking shows a request made since as it stands.

- ``ReadRelations`` — the reader's relation to a set of players, what every
  face is lent. ``friends_among`` is the cheaper question a face asks: a friend
  is never hidden (a block ends a friendship), so it reads no block.
- ``ReadFriends`` — the reader's friends, each with every sport they are rated
  in, or one: alphabetical without a sport (call 11), highest Level first with
  one (call 4).
- ``ReadFriendRequests`` — *Asked you* and *You asked*.
- ``ReadGroupsToAddFrom`` — per group, how many members the reader could still
  add.
- ``ReadRequestsOnHome`` — the friend requests on the reader's Home, and
  ``ReadRequestsWaiting`` — only whose and when, for the bell.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant, invariant
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.ports import (
    FriendFace,
    FriendFaces,
    FriendLevel,
    FriendLevels,
    FriendReliabilities,
    FriendReliability,
    FriendshipDirectory,
    ReadersBlocks,
    ReadersGroups,
    RelationRow,
)
from app.modules.friends.domain.relation import FriendRelation


def as_the_reader_sees(
    rows: Collection[RelationRow], *, blocked_by_reader: frozenset[UUID]
) -> tuple[RelationRow, ...]:
    """The rows the reader may see: every one but a request **to** the reader
    from somebody the reader blocked."""

    return tuple(
        row
        for row in rows
        if not (
            row.relation is FriendRelation.ASKED_YOU
            and row.other_id in blocked_by_reader
        )
    )


async def _seen_rows(
    directory: FriendshipDirectory,
    blocks: ReadersBlocks,
    reader: UUID,
    *,
    among: Collection[UUID] | None = None,
) -> tuple[RelationRow, ...]:
    rows = await directory.rows_of(reader, among=among)
    if not any(row.relation is FriendRelation.ASKED_YOU for row in rows):
        # Nothing a block could hide: the blocks are not read.
        return rows
    return as_the_reader_sees(rows, blocked_by_reader=await blocks.blocked_by(reader))


@final
class ReadRelations:
    """The reader's relation to each of a set of players — **everybody asked is
    answered**, ``NONE`` where nothing stands, the reader included."""

    def __init__(
        self, *, directory: FriendshipDirectory, blocks: ReadersBlocks
    ) -> None:
        self._directory = directory
        self._blocks = blocks

    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, FriendRelation]:
        wanted = set(players) - {reader}
        relations = dict.fromkeys(players, FriendRelation.NONE)
        if not wanted:
            return relations
        for row in await _seen_rows(
            self._directory, self._blocks, reader, among=wanted
        ):
            relations[row.other_id] = row.relation
        return relations

    async def friends_among(
        self, reader: UUID, players: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these are the reader's friends — what a face's *friend* tag
        reads. One question about the set, and no block read."""

        wanted = set(players) - {reader}
        if not wanted:
            return frozenset()
        return frozenset(
            row.other_id
            for row in await self._directory.rows_of(reader, among=wanted)
            if row.relation is FriendRelation.FRIEND
        )


# --------------------------------------------------------------------------- #
# The reader's friends
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Friend:
    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    since: Instant
    #: Every sport they are rated in, in the registry's order — or only the
    #: sport asked for, empty when they are not rated in it.
    levels: tuple[FriendLevel, ...]


@final
class ReadFriends:
    def __init__(
        self,
        *,
        directory: FriendshipDirectory,
        faces: FriendFaces,
        levels: FriendLevels,
    ) -> None:
        self._directory = directory
        self._faces = faces
        self._levels = levels

    async def execute(self, reader: UUID, *, sport: Sport | None) -> tuple[Friend, ...]:
        rows = [
            row
            for row in await self._directory.rows_of(reader)
            if row.relation is FriendRelation.FRIEND
        ]
        if not rows:
            return ()
        ids = [row.other_id for row in rows]
        faces = await self._faces.faces_of(ids)
        by_player: dict[UUID, list[FriendLevel]] = {}
        for one in [sport] if sport is not None else list(Sport):
            for player_id, level in (
                await self._levels.levels_in(ids, sport=one)
            ).items():
                by_player.setdefault(player_id, []).append(level)
        friends = [
            Friend(
                player_id=row.other_id,
                nickname=nickname,
                photo_id=face.photo_id,
                photo_url=face.photo_url,
                since=row.since,
                levels=tuple(by_player.get(row.other_id, ())),
            )
            for row in rows
            if (face := faces.get(row.other_id)) is not None
            and (nickname := face.nickname) is not None
        ]
        friends.sort(
            key=lambda friend: (friend.nickname.casefold(), str(friend.player_id))
        )
        if sport is not None:
            # Highest Level first, and anybody unrated in the sport last (call 4).
            friends.sort(
                key=lambda friend: -friend.levels[0].level if friend.levels else 1.0
            )
        return tuple(friends)


# --------------------------------------------------------------------------- #
# Asked you · You asked
# --------------------------------------------------------------------------- #


class Direction(StrEnum):
    #: Requests made of the reader and still open, set aside or not.
    ASKED_YOU = "ASKED_YOU"
    #: The reader's own requests still open.
    YOU_ASKED = "YOU_ASKED"


@final
@dataclass(frozen=True, slots=True)
class FriendRequest:
    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    asked_at: Instant
    #: *Asked you* only: the reader said *Not now*.
    set_aside: bool


@final
class ReadFriendRequests:
    """One direction, **newest first**. *Asked you* leaves out a request from
    somebody the reader blocked; *You asked* lists every request of the
    reader's that is open, whoever blocked whom — it reads *request sent* for
    as long as it stays open."""

    def __init__(
        self,
        *,
        directory: FriendshipDirectory,
        blocks: ReadersBlocks,
        faces: FriendFaces,
    ) -> None:
        self._directory = directory
        self._blocks = blocks
        self._faces = faces

    async def execute(
        self, reader: UUID, *, direction: Direction
    ) -> tuple[FriendRequest, ...]:
        wanted = (
            FriendRelation.ASKED_YOU
            if direction is Direction.ASKED_YOU
            else FriendRelation.SENT
        )
        rows = _newest_first(
            row
            for row in await _seen_rows(self._directory, self._blocks, reader)
            if row.relation is wanted
        )
        faces = await self._faces.faces_of([row.other_id for row in rows])
        return tuple(
            FriendRequest(
                player_id=row.other_id,
                nickname=nickname,
                photo_id=face.photo_id,
                photo_url=face.photo_url,
                asked_at=row.since,
                set_aside=row.set_aside,
            )
            for row in rows
            if (face := faces.get(row.other_id)) is not None
            and (nickname := face.nickname) is not None
        )


# --------------------------------------------------------------------------- #
# From your groups: who is left to add
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class GroupToAddFrom:
    group_id: UUID
    name: str
    member_count: int
    #: Members the reader could still ask: not the reader, not a friend, no open
    #: request either way, and nobody the reader blocked.
    to_add: int


@final
class ReadGroupsToAddFrom:
    """*From your groups* on the **Add friends** sheet — *8 members · 2 to add*.
    Three reads whatever the number of groups: the reader's groups, every row on
    the reader's side, and the reader's blocks."""

    def __init__(
        self,
        *,
        groups: ReadersGroups,
        directory: FriendshipDirectory,
        blocks: ReadersBlocks,
    ) -> None:
        self._groups = groups
        self._directory = directory
        self._blocks = blocks

    async def execute(self, reader: UUID) -> tuple[GroupToAddFrom, ...]:
        groups = await self._groups.groups_of(reader)
        if not groups:
            return ()
        taken = {row.other_id for row in await self._directory.rows_of(reader)}
        out = taken | await self._blocks.blocked_by(reader) | {reader}
        return tuple(
            GroupToAddFrom(
                group_id=group.group_id,
                name=group.name,
                member_count=len(group.members),
                to_add=sum(1 for member in group.members if member not in out),
            )
            for group in groups
        )


# --------------------------------------------------------------------------- #
# Home's friend requests
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class NamedGroup:
    group_id: UUID
    name: str


@final
@dataclass(frozen=True, slots=True)
class RequestOnHome:
    """One card in *FRIEND REQUESTS*: who, and where they asked from."""

    requester_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    asked_at: Instant
    where: Where
    #: The group it was made in, **while both of them are in it** — *With you
    #: in Kazimierz crew*. ``None`` for a link's, and for a group either left.
    group: NamedGroup | None
    #: Their published Level in the request's sport, when it names one and they
    #: are rated in it.
    level: float | None
    reliability: FriendReliability


@final
@dataclass(frozen=True, slots=True)
class WaitingRequest:
    """A request waiting on the reader's Home: whose, and when it was made."""

    requester_id: UUID
    asked_at: Instant


@final
class ReadRequestsOnHome:
    """The requests on the reader's Home, **newest first**: open, not set aside,
    and not from somebody the reader blocked. Answered, set aside or cancelled,
    a card is gone."""

    def __init__(
        self,
        *,
        directory: FriendshipDirectory,
        blocks: ReadersBlocks,
        faces: FriendFaces,
        levels: FriendLevels,
        reliability: FriendReliabilities,
        groups: ReadersGroups,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._blocks = blocks
        self._faces = faces
        self._levels = levels
        self._reliability = reliability
        self._groups = groups
        self._clock = clock

    async def execute(self, reader: UUID) -> tuple[RequestOnHome, ...]:
        rows = await _rows_on_home(self._directory, self._blocks, reader)
        if not rows:
            return ()
        requesters = [row.other_id for row in rows]
        faces = await self._faces.faces_of(requesters)
        reliability = await self._reliability.reliability_of(
            requesters, now=instant(self._clock.now())
        )
        groups = {
            group.group_id: group for group in await self._groups.groups_of(reader)
        }
        levels: dict[Sport, Mapping[UUID, FriendLevel]] = {}
        for sport in {row.where.sport for row in rows if row.where and row.where.sport}:
            levels[sport] = await self._levels.levels_in(requesters, sport=sport)

        cards: list[RequestOnHome] = []
        for row in rows:
            face = faces.get(row.other_id, FriendFace(player_id=row.other_id))
            where = invariant(row.where, "a request with no where")
            if face.nickname is None:
                continue
            group = groups.get(where.group_id) if where.group_id else None
            level = (
                levels[where.sport].get(row.other_id)
                if where.sport is not None
                else None
            )
            cards.append(
                RequestOnHome(
                    requester_id=row.other_id,
                    nickname=face.nickname,
                    photo_id=face.photo_id,
                    photo_url=face.photo_url,
                    asked_at=row.since,
                    where=where,
                    group=(
                        NamedGroup(group_id=group.group_id, name=group.name)
                        if group is not None and row.other_id in group.members
                        else None
                    ),
                    level=None if level is None else level.level,
                    reliability=reliability[row.other_id],
                )
            )
        return tuple(cards)


@final
class ReadRequestsWaiting:
    """Only whose and when — what the bell asks to clear a request's row once
    its card is gone from Home, and what the teller asks before it tells one:
    a request cancelled, answered, set aside or hidden before its delivery is
    told nobody."""

    def __init__(
        self, *, directory: FriendshipDirectory, blocks: ReadersBlocks
    ) -> None:
        self._directory = directory
        self._blocks = blocks

    async def waiting(self, reader: UUID) -> tuple[WaitingRequest, ...]:
        return tuple(
            WaitingRequest(requester_id=row.other_id, asked_at=row.since)
            for row in await _rows_on_home(self._directory, self._blocks, reader)
        )


async def _rows_on_home(
    directory: FriendshipDirectory, blocks: ReadersBlocks, reader: UUID
) -> list[RelationRow]:
    """The requests on the reader's Home, newest first: open, not set aside,
    and not from somebody the reader blocked."""

    return _newest_first(
        row
        for row in await _seen_rows(directory, blocks, reader)
        if row.relation is FriendRelation.ASKED_YOU and not row.set_aside
    )


def _newest_first(rows: Iterable[RelationRow]) -> list[RelationRow]:
    """Newest first, and one instant's ties by id, so the order is stable."""

    return sorted(rows, key=lambda row: (-row.since.timestamp(), str(row.other_id)))

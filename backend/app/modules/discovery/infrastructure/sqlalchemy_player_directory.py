"""``PlayerDirectory`` over ``discovery_players`` and ``discovery_player_tags``
(``docs/adr/0204`` §10).

**An entry is written whole**: the row upserted, the account's tags deleted and
written again, in the caller's transaction — so the tags are always the
profile's as the follower last read them, and a redelivery writes the same
rows. ``forget`` deletes both.

**Who may be on a row is one ``WHERE``** (``may_be_on_a_row``): named,
playing, *Show me to new people* on, and none of the ids left out — the reader
and every block either way, tens at most, as one ``NOT IN``.

**New in Rakieta's total is one count over the month's range** (#812):
``ix_discovery_players_joined_at`` read from 30 days back, the same ``WHERE``,
stopping at the cap — a ``LIMIT`` inside the count (``count_up_to``, which
Same competitive level's count shares), so a busy month is never counted
whole.

**Same vibe counts shared tags in SQL, portably** (#795): one pass over
``discovery_player_tags`` grouped by player counts how many of the reader's
each holds and how many they hold in all, ordered most in common first and
paged by the last card's key. **One statement per read**:
the page is a derived table, joined back to its players' tags, so the counts
and the chips come from one snapshot. The chips are put in the vocabulary's
order here, where the vocabulary may be read. **The row's total rides the
same statement** (#812): with ``counting``, ``count(*) OVER ()`` on the page,
taken over every player the ``WHERE`` keeps before the ``LIMIT``, so everybody
sharing a tag is counted in the pass the row already makes and never in a
second one. Only the row's first batch asks: the window holds the whole list
before the sort, which See all and a later batch have no use for.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import timezone
from typing import Any, Final, final
from uuid import UUID

from sqlalchemy import Select, and_, case, delete, distinct, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Instant, Sport, invariant
from app.modules.discovery.domain.directory import DirectoryEntry
from app.modules.discovery.domain.new_in_rakieta import Joiner
from app.modules.discovery.domain.ports import Alike
from app.modules.discovery.domain.same_vibe import VibeKey, vibe_player
from app.modules.discovery.infrastructure.directory_model import (
    DirectoryPlayerORM,
    DirectoryTagORM,
)
from app.modules.discovery.infrastructure.dialect_insert import insert_into
from app.modules.discovery.infrastructure.levels_model import DiscoveryLevelORM
from app.modules.player_profile.domain.social_tags import SOCIAL_TAG_VOCABULARY

#: Where each tag stands in the vocabulary — the order the record serves tags
#: in, and so the chips'. A tag the vocabulary no longer lists stands last.
_IN_THE_VOCABULARY: Final[Mapping[str, int]] = {
    tag.value: n
    for n, tag in enumerate(
        tag for group in SOCIAL_TAG_VOCABULARY.values() for tag in group
    )
}


@final
class SqlAlchemyPlayerDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, entry: DirectoryEntry) -> None:
        values = _values(entry)
        await self._session.execute(
            insert_into(self._session, DirectoryPlayerORM)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[DirectoryPlayerORM.player_id],
                set_={
                    name: value for name, value in values.items() if name != "player_id"
                },
            )
        )
        await self._session.execute(
            delete(DirectoryTagORM).where(DirectoryTagORM.player_id == entry.player_id)
        )
        tags = sorted(entry.player.tags) if entry.player is not None else []
        if tags:
            await self._session.execute(
                insert_into(self._session, DirectoryTagORM).values(
                    [{"player_id": entry.player_id, "tag": tag} for tag in tags]
                )
            )

    async def forget(self, player_id: UUID) -> None:
        await self._session.execute(
            delete(DirectoryTagORM).where(DirectoryTagORM.player_id == player_id)
        )
        await self._session.execute(
            delete(DirectoryPlayerORM).where(DirectoryPlayerORM.player_id == player_id)
        )

    async def who_joined(
        self,
        *,
        after: Instant,
        leaving_out: Collection[UUID],
        limit: int | None = None,
    ) -> tuple[Joiner, ...]:
        query = (
            select(
                DirectoryPlayerORM.player_id,
                DirectoryPlayerORM.nickname,
                DirectoryPlayerORM.photo_id,
                DirectoryPlayerORM.joined_at,
            )
            .where(
                may_be_on_a_row(leaving_out),
                DirectoryPlayerORM.joined_at > after.astimezone(timezone.utc),
            )
            .order_by(DirectoryPlayerORM.joined_at.desc(), DirectoryPlayerORM.player_id)
        )
        if limit is not None:
            query = query.limit(limit)
        return tuple(
            Joiner(
                player_id=row.player_id,
                nickname=row.nickname,
                photo_id=row.photo_id,
                joined_at=stored_instant(row.joined_at),
            )
            for row in (await self._session.execute(query)).all()
        )

    async def how_many_joined(
        self, *, after: Instant, leaving_out: Collection[UUID], up_to: int
    ) -> int:
        return await count_up_to(
            self._session,
            select(DirectoryPlayerORM.player_id).where(
                may_be_on_a_row(leaving_out),
                DirectoryPlayerORM.joined_at > after.astimezone(timezone.utc),
            ),
            up_to,
        )

    async def which_may_be_listed(
        self, players: Collection[UUID], *, leaving_out: Collection[UUID]
    ) -> frozenset[UUID]:
        if not players:
            return frozenset()
        found = await self._session.scalars(
            select(DirectoryPlayerORM.player_id).where(
                DirectoryPlayerORM.player_id.in_(sorted(players, key=str)),
                may_be_on_a_row(leaving_out),
            )
        )
        return frozenset(found.all())

    async def tags_of(self, player_id: UUID) -> frozenset[str]:
        rows = await self._session.scalars(
            select(DirectoryTagORM.tag).where(DirectoryTagORM.player_id == player_id)
        )
        return frozenset(rows.all())

    async def tags_of_each(
        self, players: Collection[UUID]
    ) -> Mapping[UUID, frozenset[str]]:
        asked = set(players)
        if not asked:
            return {}
        rows = await self._session.execute(
            select(DirectoryTagORM.player_id, DirectoryTagORM.tag).where(
                DirectoryTagORM.player_id.in_(asked)
            )
        )
        held: dict[UUID, set[str]] = {player: set() for player in asked}
        for player_id, tag in rows:
            held[player_id].add(tag)
        return {player: frozenset(tags) for player, tags in held.items()}

    async def alike(
        self,
        mine: frozenset[str],
        *,
        leaving_out: Collection[UUID],
        sport: Sport | None,
        after: VibeKey | None,
        limit: int,
        counting: bool = False,
    ) -> Alike:
        invariant(limit > 0, f"a page holds somebody: limit {limit}")
        if not mine:
            return Alike(players=(), listed=0 if counting else None)
        shared = _counted_against(mine)
        in_common = shared.c.in_common
        not_shared = shared.c.held - shared.c.in_common
        # Over every row the WHERE keeps, before the LIMIT: the read's whole
        # list, counted in the pass it already makes — and only when asked,
        # since the window holds the whole list before the sort.
        everybody = [func.count().over().label("everybody")] if counting else []
        page = (
            select(
                DirectoryPlayerORM.player_id.label("player_id"),
                DirectoryPlayerORM.nickname.label("nickname"),
                DirectoryPlayerORM.photo_id.label("photo_id"),
                *everybody,
            )
            .join(shared, shared.c.player_id == DirectoryPlayerORM.player_id)
            .where(may_be_on_a_row(leaving_out))
            .order_by(in_common.desc(), not_shared, DirectoryPlayerORM.player_id)
            .limit(limit)
        )
        if sport is not None:
            page = page.where(
                exists().where(
                    DiscoveryLevelORM.player_id == DirectoryPlayerORM.player_id,
                    DiscoveryLevelORM.sport == sport.value,
                )
            )
        if after is not None:
            page = page.where(
                or_(
                    in_common < after.in_common,
                    and_(in_common == after.in_common, not_shared > after.not_shared),
                    and_(
                        in_common == after.in_common,
                        not_shared == after.not_shared,
                        DirectoryPlayerORM.player_id > after.player_id,
                    ),
                )
            )
        listed = page.subquery("listed")
        rows = await self._session.execute(
            select(
                listed.c.player_id,
                listed.c.nickname,
                listed.c.photo_id,
                DirectoryTagORM.tag,
                *([listed.c.everybody] if counting else []),
            ).join(DirectoryTagORM, DirectoryTagORM.player_id == listed.c.player_id)
        )
        tags_of: dict[UUID, list[str]] = {}
        named: dict[UUID, tuple[str, UUID | None]] = {}
        # An empty page lists nobody: no row carries the count, and it is 0.
        listed_in_all = 0
        for row in rows.all():
            tags_of.setdefault(row.player_id, []).append(row.tag)
            named[row.player_id] = (row.nickname, row.photo_id)
            if counting:
                listed_in_all = row.everybody
        found = (
            vibe_player(
                player_id,
                nickname,
                photo_id,
                sorted(tags_of[player_id], key=_vocabulary_order),
                mine=mine,
            )
            for player_id, (nickname, photo_id) in named.items()
        )
        return Alike(
            players=tuple(
                sorted(
                    (one for one in found if one is not None),
                    key=lambda one: one.key.order,
                )
            ),
            listed=listed_in_all if counting else None,
        )

    async def sports_alike(
        self, mine: frozenset[str], *, leaving_out: Collection[UUID]
    ) -> tuple[Sport, ...]:
        if not mine:
            return ()
        listed = (
            select(DirectoryTagORM.player_id)
            .join(
                DirectoryPlayerORM,
                DirectoryPlayerORM.player_id == DirectoryTagORM.player_id,
            )
            .where(DirectoryTagORM.tag.in_(sorted(mine)), may_be_on_a_row(leaving_out))
        )
        held = set(
            (
                await self._session.scalars(
                    select(distinct(DiscoveryLevelORM.sport)).where(
                        DiscoveryLevelORM.player_id.in_(listed)
                    )
                )
            ).all()
        )
        return tuple(sport for sport in Sport if sport.value in held)


def may_be_on_a_row(leaving_out: Collection[UUID]) -> Any:
    """Who may be on a people row (``docs/adr/0204`` §10): named, playing,
    *Show me to new people* on, and none of the ids left out."""

    conditions: list[Any] = [
        DirectoryPlayerORM.plays.is_(True),
        DirectoryPlayerORM.open_to_new_people.is_(True),
        DirectoryPlayerORM.nickname.is_not(None),
    ]
    if leaving_out:
        conditions.append(
            DirectoryPlayerORM.player_id.not_in(sorted(leaving_out, key=str))
        )
    return and_(*conditions)


async def count_up_to(session: AsyncSession, listed: Select[Any], up_to: int) -> int:
    """How many rows ``listed`` selects — **counted no further than
    ``up_to``**: a ``LIMIT`` inside the count, so a read that finds that many
    stops there (#812)."""

    counted = await session.scalar(
        select(func.count()).select_from(listed.limit(up_to).subquery("listed"))
    )
    return counted or 0


def _counted_against(mine: frozenset[str]) -> Any:
    """Each player sharing any of ``mine``: how many of them (*in common*) and
    how many tags they hold in all (*held*) — **one pass over the tag rows**,
    grouped by player. Nearly everybody shares a tag with somebody holding
    six, so a scan of every row beats probing the tag index and joining a
    second count back (measured at 50,000: 62 ms against 151)."""

    one_of_mine = case((DirectoryTagORM.tag.in_(sorted(mine)), 1), else_=0)
    return (
        select(
            DirectoryTagORM.player_id.label("player_id"),
            func.sum(one_of_mine).label("in_common"),
            func.count().label("held"),
        )
        .group_by(DirectoryTagORM.player_id)
        .having(func.sum(one_of_mine) > 0)
        .subquery("counted")
    )


def _vocabulary_order(tag: str) -> tuple[int, str]:
    return (_IN_THE_VOCABULARY.get(tag, len(_IN_THE_VOCABULARY)), tag)


def _values(entry: DirectoryEntry) -> dict[str, object]:
    player = entry.player
    return {
        "player_id": entry.player_id,
        "nickname": entry.nickname,
        "plays": player is not None,
        "joined_at": None
        if player is None
        else player.joined_at.astimezone(timezone.utc),
        "photo_id": None if player is None else player.photo_id,
        "area_latitude": None
        if player is None or player.area is None
        else player.area.latitude,
        "area_longitude": None
        if player is None or player.area is None
        else player.area.longitude,
        "open_to_new_people": player is not None and player.open_to_new_people,
    }

"""``PlayerLevels`` over ``discovery_levels``, joined to the directory for who
may be on a row (``docs/adr/0204`` §10; #794).

**A save keeps the fold with the most results**: one ``INSERT … ON CONFLICT DO
UPDATE … WHERE stored.results <= new.results``, as the ranking's rows are kept
— results only add up, so a fold read before another delivery's move
committed cannot take that move back, under two deliveries at once too.

**A window is one statement**: everybody holding a level in one of the
reader's sports inside the ring between the window and the last one read —
``ix_discovery_levels_sport_mu``'s range, one sport each — joined to the
directory's ``WHERE`` (named, playing, *Show me to new people* on, none of the
ids left out), with every level each of them holds in the sports compared.
**Columns, never ORM objects**, as the ranking reads its rows: a wide window
hands back thousands. **The least Uncertainty in a sport** is one ``min`` over
``ix_discovery_levels_sport_sigma``, a single index probe.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any, final
from uuid import UUID

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Sport
from app.modules.discovery.domain.levels import Band, CurrentLevel, in_sport_order
from app.modules.discovery.domain.ports import Candidate
from app.modules.discovery.infrastructure.dialect_insert import insert_into
from app.modules.discovery.infrastructure.directory_model import DirectoryPlayerORM
from app.modules.discovery.infrastructure.levels_model import DiscoveryLevelORM
from app.modules.discovery.infrastructure.sqlalchemy_player_directory import (
    may_be_on_a_row,
)

_KEPT = ("mu", "sigma", "band_name", "band_lower", "band_upper", "results")


@final
class SqlAlchemyPlayerLevels:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, level: CurrentLevel) -> None:
        statement = insert_into(self._session, DiscoveryLevelORM).values(
            player_id=level.player_id,
            sport=level.sport.value,
            mu=level.mu,
            sigma=level.sigma,
            band_name=level.band.name,
            band_lower=level.band.lower,
            band_upper=level.band.upper,
            results=level.results,
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[DiscoveryLevelORM.player_id, DiscoveryLevelORM.sport],
                set_={column: statement.excluded[column] for column in _KEPT},
                where=DiscoveryLevelORM.results <= statement.excluded.results,
            )
        )

    async def of_player(self, player_id: UUID) -> Mapping[Sport, CurrentLevel]:
        rows = await self._session.execute(
            select(*_COLUMNS).where(DiscoveryLevelORM.player_id == player_id)
        )
        levels = [_level(row) for row in rows.all()]
        return {
            level.sport: level
            for level in sorted(levels, key=lambda level: in_sport_order(level.sport))
        }

    async def near(
        self,
        around: Mapping[Sport, float],
        *,
        within: float | None,
        beyond: float | None,
        compared_in: Collection[Sport],
        leaving_out: Collection[UUID],
    ) -> tuple[Candidate, ...]:
        if not around or not compared_in:
            return ()
        found = select(DiscoveryLevelORM.player_id).where(
            or_(*(_ring(sport, mu, within, beyond) for sport, mu in around.items()))
        )
        query = (
            select(
                DirectoryPlayerORM.nickname,
                DirectoryPlayerORM.photo_id,
                *_COLUMNS,
            )
            .join(
                DiscoveryLevelORM,
                DiscoveryLevelORM.player_id == DirectoryPlayerORM.player_id,
            )
            .where(
                may_be_on_a_row(leaving_out),
                DirectoryPlayerORM.player_id.in_(found),
                DiscoveryLevelORM.sport.in_(sorted(one.value for one in compared_in)),
            )
            .order_by(DiscoveryLevelORM.player_id, DiscoveryLevelORM.sport)
        )
        candidates: dict[UUID, tuple[str, UUID | None, list[CurrentLevel]]] = {}
        for row in (await self._session.execute(query)).all():
            _, _, levels = candidates.setdefault(
                row.player_id, (row.nickname, row.photo_id, [])
            )
            levels.append(_level(row))
        return tuple(
            Candidate(
                player_id=player_id,
                nickname=nickname,
                photo_id=photo_id,
                levels=tuple(
                    sorted(levels, key=lambda level: in_sport_order(level.sport))
                ),
            )
            for player_id, (nickname, photo_id, levels) in candidates.items()
        )

    async def shared_sports(
        self, sports: Collection[Sport], *, leaving_out: Collection[UUID]
    ) -> tuple[Sport, ...]:
        shared = []
        for sport in Sport:
            if sport not in sports:
                continue
            anybody = select(
                exists().where(
                    DiscoveryLevelORM.sport == sport.value,
                    DiscoveryLevelORM.player_id == DirectoryPlayerORM.player_id,
                    may_be_on_a_row(leaving_out),
                )
            )
            if await self._session.scalar(anybody):
                shared.append(sport)
        return tuple(shared)

    async def least_doubt(self, sports: Collection[Sport]) -> Mapping[Sport, float]:
        least = {}
        for sport in sports:
            sigma = await self._session.scalar(
                select(func.min(DiscoveryLevelORM.sigma)).where(
                    DiscoveryLevelORM.sport == sport.value
                )
            )
            if sigma is not None:
                least[sport] = sigma
        return least


_COLUMNS = (
    DiscoveryLevelORM.player_id,
    DiscoveryLevelORM.sport,
    DiscoveryLevelORM.mu,
    DiscoveryLevelORM.sigma,
    DiscoveryLevelORM.band_name,
    DiscoveryLevelORM.band_lower,
    DiscoveryLevelORM.band_upper,
    DiscoveryLevelORM.results,
)


def _ring(sport: Sport, mu: float, within: float | None, beyond: float | None) -> Any:
    """One sport's ring: inside ``within`` of ``mu``, outside ``beyond``."""

    conditions: list[Any] = [DiscoveryLevelORM.sport == sport.value]
    if within is not None:
        conditions += [
            DiscoveryLevelORM.mu >= mu - within,
            DiscoveryLevelORM.mu <= mu + within,
        ]
    if beyond is not None:
        conditions.append(
            or_(DiscoveryLevelORM.mu < mu - beyond, DiscoveryLevelORM.mu > mu + beyond)
        )
    return and_(*conditions)


def _level(row: Any) -> CurrentLevel:
    return CurrentLevel(
        player_id=row.player_id,
        sport=Sport(row.sport),
        mu=row.mu,
        sigma=row.sigma,
        band=Band(name=row.band_name, lower=row.band_lower, upper=row.band_upper),
        results=row.results,
    )

"""A crowd written straight into the people rows' copies (#812) — the directory,
its tags and the current levels — as the 50,000-player measurements were
(``.claude/rules/discovery.md``): a hundred players signed up through the
routes would be a minute of setup for one number.

**Nobody in it has a stream**: no account, block, friend, rating or photograph,
so every row reads them as unconnected strangers with no published level. Each
is named, plays and has *Show me to new people* on — on every row their
condition puts them on — and no later delivery rewrites them, since no event
names them.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from uuid import UUID

from app.engines.racketskill.core import band_for
from app.kernel import Sport
from app.modules.discovery.infrastructure.directory_model import (
    DirectoryPlayerORM,
    DirectoryTagORM,
)
from app.modules.discovery.infrastructure.levels_model import DiscoveryLevelORM
from app.shared.ids import new_uuid

#: Long before any test's month, so a crowd is new to nobody unless asked.
LONG_AGO = datetime(2020, 1, 1, tzinfo=timezone.utc)


async def a_crowd(
    session_factory,
    size: int,
    *,
    joined_at: datetime = LONG_AGO,
    tags: Iterable[str] = (),
    levels: Mapping[Sport, tuple[float, float]] | None = None,
    named: str = "crowd",
) -> list[UUID]:
    """``size`` players, each joined at ``joined_at``, holding ``tags`` and a
    level ``(mu, sigma)`` in each of ``levels``' sports."""

    held = sorted(set(tags))
    ids = [new_uuid() for _ in range(size)]
    async with session_factory() as session:
        for n, player_id in enumerate(ids):
            session.add(
                DirectoryPlayerORM(
                    player_id=player_id,
                    nickname=f"{named}{n:03d}",
                    plays=True,
                    joined_at=joined_at,
                    photo_id=None,
                    area_latitude=None,
                    area_longitude=None,
                    open_to_new_people=True,
                )
            )
        await session.flush()
        for player_id in ids:
            for tag in held:
                session.add(DirectoryTagORM(player_id=player_id, tag=tag))
            for sport, (mu, sigma) in (levels or {}).items():
                band = band_for(mu)
                session.add(
                    DiscoveryLevelORM(
                        player_id=player_id,
                        sport=sport.value,
                        mu=mu,
                        sigma=sigma,
                        band_name=band.label,
                        band_lower=band.lower,
                        band_upper=band.upper,
                        results=5,
                    )
                )
        await session.commit()
    return ids

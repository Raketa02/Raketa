"""``WherePoolsPlay`` for a group's pool — its home club, and the clubs around it
it may also play at (the mechanics §4.3, §18; ``docs/adr/0202`` §7).

**A player group** plays at its home club first and then at any club within
``PLAYER_GROUP_CLUBS_WITHIN_KM`` of it, nearest first. **An official group**
plays at its own club, and — while the club offers its groups other clubs'
courts, a setting it holds in its Rakieta settings (on by default), read off the
offer the Club context publishes — at the clubs within the distance it chose,
**only at an hour its own club has no free court**: that is
``PoolClubs.offered``'s rule, hour by hour, and this read answers only the
clubs. A club that is not live sells nothing, so a club nearby that is not live
costs a read and deals nothing; its courts never reach a deck.

**Distance is measured here, between two clubs' own points**, by the matcher's
great-circle function over the box it draws (``matchmaking/domain/geography.py``)
— the one spelling of *how far* the platform has — and asked of the Club
context's directory as a rectangle, never a table scan and never a join.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant, exhaustive
from app.modules.clubs.domain.ports import ClubDirectory, SellableCourtHours
from app.modules.groups.domain.ports import GroupDirectory
from app.modules.matchmaking.domain.geography import Point, bounding_box, distance_km
from app.modules.proposals.domain.limits import PLAYER_GROUP_CLUBS_WITHIN_KM
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.proposer import PoolClubs


@final
class GroupClubs:
    def __init__(
        self,
        *,
        groups: GroupDirectory,
        clubs: ClubDirectory,
        sellable: SellableCourtHours,
    ) -> None:
        self._groups = groups
        self._clubs = clubs
        self._sellable = sellable

    async def of(self, pool: Pool, *, now: Instant) -> PoolClubs | None:
        match pool.kind:
            case PoolKind.GROUP:
                listing = (await self._groups.listings([pool.id])).get(pool.id)
                if listing is None:
                    return None
                home = listing.home_club_id
                if not listing.is_official:
                    return PoolClubs(
                        home_club_id=home,
                        others=await self._around(home, PLAYER_GROUP_CLUBS_WITHIN_KM),
                    )
                # Its terms, and none of its hours: an empty window.
                offer = (
                    await self._sellable.between([home], start=now, end=now, now=now)
                ).get(home)
                other_clubs = (
                    None if offer is None else offer.settings.other_clubs_courts
                )
                return PoolClubs(
                    home_club_id=home,
                    others=(
                        await self._around(home, other_clubs.within_km)
                        if other_clubs is not None and other_clubs.offered
                        else ()
                    ),
                    others_only_when_home_is_full=True,
                )
            case _:
                exhaustive(pool.kind)

    async def _around(self, home: UUID, within_km: float) -> tuple[UUID, ...]:
        """Every other club within ``within_km`` of ``home``, nearest first and
        by id among clubs as far — so two processes read one order."""

        listed = (await self._clubs.listed([home])).get(home)
        if listed is None:
            return ()
        centre = Point(latitude=listed.latitude, longitude=listed.longitude)
        box = bounding_box(centre, within_km)
        near: list[tuple[float, str, UUID]] = []
        for club in await self._clubs.inside(
            south=box.minimum_latitude,
            north=box.maximum_latitude,
            west=box.minimum_longitude,
            east=box.maximum_longitude,
        ):
            if club.id == home:
                continue
            away = distance_km(
                centre, Point(latitude=club.latitude, longitude=club.longitude)
            )
            if away <= within_km:
                near.append((away, str(club.id), club.id))
        return tuple(club_id for _, _, club_id in sorted(near))

"""``NewArrivals`` and ``ArrivalRows`` over Users, Rating and Clubs.

The one file in Now that knows *new on Raketa* means an account row's creation
stamp, that being rated at a sport is a stream that exists, and that a club sells
a sport when it has a live court in a live category for it. Everything above it
asks in Now's words and is told a set of ids, or a handful of rows.

**It takes three ports and no session**, on the precedent
``RatedSportsFromSkillRatings`` set: what backs a user, a rating or a club is
those contexts' business, and the day a projection answers any of these faster
than the read does, only their own adapters move.

**One class, two ports.** They are two protocols because the *cache* stores what
one of them returns and must not be able to store what the other does; they are
one implementation because both are the same reads asked at two depths, and a
second class would duplicate the eligibility rules that decide membership.

**The cost is a launch-volume judgement and it is stated rather than hidden.**
The membership reads walk every account registered this month and every club on
the platform, and both are behind the fifteen-minute cache. The row reads are
bounded by the cached set. A city that outgrows that wants a projection, and the
port is where one lands.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from app.kernel import Instant, Sport, instant

from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.now.domain.arrivals import NewClub, NewPlayer
from app.modules.rating.domain.ports import SkillRatingRepository
from app.modules.users.domain.ports import UserRepository


def _as_instant(value: datetime) -> Instant:
    """A stored moment as an instant, filling in the UTC that SQLite drops."""

    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))


def _sells(club: Club, sport: Sport) -> bool:
    """Whether this club has something bookable in that sport.

    A live **court** in a live **category**, not a category on its own: retire
    every court in one and it survives as a group nothing can be assigned in, so
    a shelf that counted it would send a player to a club with nothing to book.
    """

    return any(
        club.courts_in(category.id)
        for category in club.live_categories
        if category.sport is sport
    )


class ArrivalsFromUsersAndClubs:
    """Who arrived recently, and the rows two inert cards print."""

    def __init__(
        self,
        *,
        users: UserRepository,
        ratings: SkillRatingRepository,
        clubs: ClubRepository,
    ) -> None:
        self._users = users
        self._ratings = ratings
        self._clubs = clubs

    # -- the set -------------------------------------------------------------

    async def player_ids(self, *, sport: Sport, since: Instant) -> tuple[UUID, ...]:
        found: list[UUID] = []
        for user in await self._users.find_registered_since(since):
            # A disabled account is not somebody to meet. The rating is the
            # fact filter beside it: a Level the platform holds, never one it
            # would have to impute.
            if not user.is_active:
                continue
            if await self._ratings.exists_for(player_id=user.id, sport=sport):
                found.append(user.id)
        return tuple(found)

    async def club_ids(self, *, sport: Sport, since: Instant) -> tuple[UUID, ...]:
        arrived = [
            club
            for club in await self._clubs.find_all()
            if club.created_at is not None
            and club.created_at >= since
            and _sells(club, sport)
        ]
        arrived.sort(key=lambda club: (-_joined(club).timestamp(), club.name.value))
        return tuple(club.id for club in arrived)

    # -- the row -------------------------------------------------------------

    async def players(self, *, player_ids: Sequence[UUID]) -> tuple[NewPlayer, ...]:
        rows: list[NewPlayer] = []
        for user in await self._users.find_by_ids(player_ids):
            if not user.is_active or user.created_at is None:
                continue
            rows.append(
                NewPlayer(
                    player_id=user.id,
                    nickname=user.nickname.value,
                    joined_at=_as_instant(user.created_at),
                )
            )
        return tuple(rows)

    async def clubs(self, *, club_ids: Sequence[UUID]) -> tuple[NewClub, ...]:
        rows: list[NewClub] = []
        for club in await self._clubs.find_by_ids(club_ids):
            if club.created_at is None:
                continue
            rows.append(
                NewClub(
                    club_id=club.id,
                    name=club.name.value,
                    joined_at=club.created_at,
                    # No distance, and it is the modelled answer rather than a
                    # gap: a distance is measured from the glossary's Distance
                    # anchor, the anchor is optional, and precision follows it.
                    distance_km=None,
                )
            )
        return tuple(rows)


def _joined(club: Club) -> Instant:
    """The creation stamp of a club the caller has already found to have one."""

    stamp = club.created_at
    if stamp is None:  # pragma: no cover — filtered before this is reached
        raise AssertionError
    return stamp

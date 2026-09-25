from __future__ import annotations

from uuid import UUID

from app.modules.groups.application.views import (
    GroupPage,
    NamedClub,
    SportFaces,
    rated_among,
    row_of,
)
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupFace,
    GroupFaces,
    HomeClubs,
    RatedGroupMembers,
)
from app.modules.groups.domain.sports import rosters


class ReadGroup:
    """A group, opened by one of its members.

    **For members only** (#504): anyone else meets ``group_not_found``, the same
    refusal as a group that does not exist, because the two have one remedy and
    telling them apart would tell a stranger which ids are real.

    The ratings are read once and answer both the dots and every sport's
    *N of M*; the faces are read once, for the union of every sport's first
    seats.
    """

    def __init__(
        self,
        *,
        directory: GroupDirectory,
        clubs: HomeClubs,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
    ) -> None:
        self._directory = directory
        self._clubs = clubs
        self._ratings = ratings
        self._faces = faces

    async def execute(self, group_id: UUID, *, reader_id: UUID) -> GroupPage:
        listing = (await self._directory.listings([group_id])).get(group_id)
        if listing is None or reader_id not in listing.members:
            raise GroupNotFound()

        rated = await rated_among(self._ratings, [listing])
        by_sport = rosters(listing.members, rated)
        faces = await self._faces.faces_of(
            {player_id for roster in by_sport for player_id in roster.first_rated}
        )
        club = (await self._clubs.by_id([listing.home_club_id]))[listing.home_club_id]
        return GroupPage(
            row=row_of(listing, rated),
            home_club=NamedClub(id=club.id, name=club.name),
            code=listing.code,
            join_policy=listing.join_policy,
            is_owner=listing.owner_id == reader_id,
            by_sport=tuple(
                SportFaces(
                    sport=roster.sport,
                    rated_count=roster.rated_count,
                    first_rated=tuple(
                        faces.get(player_id, GroupFace(player_id=player_id))
                        for player_id in roster.first_rated
                    ),
                )
                for roster in by_sport
            ),
        )

from __future__ import annotations

from uuid import UUID

from app.modules.groups.application.membership import hidden_in, listing_for_a_member
from app.modules.groups.application.views import (
    GroupPage,
    NamedClub,
    SportFaces,
    face_of,
    rated_among,
    row_of,
)
from app.modules.groups.domain.members import members_row
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupFaces,
    GroupListing,
    HiddenMembers,
    HomeClubs,
    RatedGroupMembers,
)
from app.modules.groups.domain.sports import rosters


class GroupPages:
    """A group's page as one reader sees it, drawn from its listing — what the
    read answers, and what *Edit group* answers with before it commits.

    The ratings are read once and answer both the dots and every sport's
    *N of M*; the faces are read once, for the union of every sport's first
    seats and the Info tab's members row.

    **The members row leaves out a blocked pair, either way round** — it is the
    row that opens the Members list, which does (``docs/adr/0183`` §10) — and
    **no count moves**: the member count and each sport's *N* are the group's.
    The Games tab's seats are the first rated members in joining order whoever
    reads them (§13, #504). The block state fails closed, so a page nobody could
    check is not served — and a reader alone has nobody to hide, so it is not
    read for them at all.
    """

    def __init__(
        self,
        *,
        clubs: HomeClubs,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        hidden: HiddenMembers,
    ) -> None:
        self._clubs = clubs
        self._ratings = ratings
        self._faces = faces
        self._hidden = hidden

    async def page(self, listing: GroupListing, *, reader_id: UUID) -> GroupPage:
        hidden = await hidden_in(self._hidden, listing, reader_id)
        rated = await rated_among(self._ratings, [listing])
        by_sport = rosters(listing.members, rated)
        on_members_row = members_row(
            listing.members,
            reader_id=reader_id,
            owner_id=listing.owner_id,
            hidden=hidden,
        )
        faces = await self._faces.faces_of(
            {player_id for roster in by_sport for player_id in roster.first_rated}
            | set(on_members_row)
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
                        face_of(faces, player_id) for player_id in roster.first_rated
                    ),
                )
                for roster in by_sport
            ),
            member_faces=tuple(
                face_of(faces, player_id) for player_id in on_members_row
            ),
        )


class ReadGroup:
    """A group, opened by one of its members.

    **For members only** (#504): anyone else meets ``group_not_found``, the same
    refusal as a group that does not exist, because the two have one remedy and
    telling them apart would tell a stranger which ids are real.
    """

    def __init__(self, *, directory: GroupDirectory, pages: GroupPages) -> None:
        self._directory = directory
        self._pages = pages

    async def execute(self, group_id: UUID, *, reader_id: UUID) -> GroupPage:
        listing = await listing_for_a_member(self._directory, group_id, reader_id)
        return await self._pages.page(listing, reader_id=reader_id)

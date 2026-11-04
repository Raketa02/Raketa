from __future__ import annotations

from uuid import UUID

from app.modules.groups.application.membership import listing_for_a_member
from app.modules.groups.application.views import (
    GroupPage,
    NamedClub,
    SportFaces,
    approver_name,
    face_of,
    rated_among,
    row_of,
    running_it,
    who_runs_it,
)
from app.modules.groups.domain.members import members_row
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupDirectory,
    GroupFaces,
    GroupListing,
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

    **The members row hides nobody for a block** (``docs/adr/0193`` §2) — it is
    the row that opens the Members list, which hides nobody either — and the
    member count and each sport's *N* are the group's. The Games tab's seats
    are the first rated members in joining order whoever reads them
    (ADR-0183 §13, #504). No block state is read for a page.

    **On an official group the account running it leads the members row**, as
    an Owner does on a player group — asked of the administrators, so it is
    whoever runs it now — and the Info tab's *approves joins* line names them
    as a club's card does, or nobody while the group needs an administrator
    (#510).
    """

    def __init__(
        self,
        *,
        clubs: HomeClubs,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        administrators: GroupAdministrators,
    ) -> None:
        self._clubs = clubs
        self._ratings = ratings
        self._faces = faces
        self._administrators = administrators

    async def page(self, listing: GroupListing, *, reader_id: UUID) -> GroupPage:
        rated = await rated_among(self._ratings, [listing])
        by_sport = rosters(listing.members, rated)
        runner = await running_it(self._administrators, listing)
        running = None if runner is None else runner.account_id
        on_members_row = members_row(
            listing.members,
            reader_id=reader_id,
            run_by=who_runs_it(listing, running),
        )
        names = {} if running is None else await self._faces.names_of([running])
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
            administrator_nickname=approver_name(runner, names),
            is_administrator=running is not None and running == reader_id,
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

from __future__ import annotations

from uuid import UUID

from app.kernel import Clock, Sport
from app.modules.groups.application.membership import hidden_in, listing_for_a_member
from app.modules.groups.application.views import MemberRow, face_of
from app.modules.groups.domain.members import in_members_order
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupFaces,
    GroupMemberScores,
    HiddenMembers,
    RatedGroupMembers,
)


class ReadGroupMembers:
    """Members, for one sport — who in the group the reader could play it with
    (#500 stories 80–84, ``docs/adr/0183`` §10).

    **Only the members rated in that sport**, the reader first, then the Owner,
    then everybody else newest joined first (``domain/members.py``); each with
    their face, their Level in it, their Player Score where they have one,
    whether they own the group and when they joined.

    **A blocked pair is left out of each other's list, either way round**, and
    nothing on the answer says anybody was: the count on the group is the
    group's. The block state is read first and fails closed — a list nobody
    could check is not served — except for a reader alone, who has nobody to
    hide.

    **For members only**: anyone else meets ``group_not_found``, as the group's
    page refuses them. Four reads whatever the size of the group — who is
    hidden, the Levels, the faces and the scores — each one question about the
    rows it serves.
    """

    def __init__(
        self,
        *,
        directory: GroupDirectory,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        scores: GroupMemberScores,
        hidden: HiddenMembers,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._ratings = ratings
        self._faces = faces
        self._scores = scores
        self._hidden = hidden
        self._clock = clock

    async def execute(
        self, group_id: UUID, *, reader_id: UUID, sport: Sport
    ) -> tuple[MemberRow, ...]:
        listing = await listing_for_a_member(self._directory, group_id, reader_id)

        hidden = await hidden_in(self._hidden, listing, reader_id)
        visible = [member for member in listing.members if member not in hidden]
        levels = await self._ratings.levels_in(visible, sport=sport)
        shown = in_members_order(
            [member for member in visible if member in levels],
            reader_id=reader_id,
            owner_id=listing.owner_id,
        )
        faces = await self._faces.faces_of(shown)
        scores = await self._scores.scores_of(shown, now=self._clock.now())
        return tuple(
            MemberRow(
                face=face_of(faces, member),
                level=levels[member],
                player_score=scores.get(member),
                is_owner=member == listing.owner_id,
                joined_at=listing.joined_at[member],
            )
            for member in shown
        )

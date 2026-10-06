from __future__ import annotations

from uuid import UUID

from app.kernel import Clock, Sport
from app.modules.groups.application.membership import (
    listing_for_a_member_or_its_runner,
)
from app.modules.groups.application.views import MemberRow, face_of, who_runs_it
from app.modules.groups.domain.members import in_members_order
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupDirectory,
    GroupFaces,
    GroupMemberScores,
    RatedGroupMembers,
)


class ReadGroupMembers:
    """Members, for one sport — who in the group the reader could play it with
    (#500 stories 80–84, ``docs/adr/0183`` §10).

    **Only the members rated in that sport**, the reader first, then whoever
    runs the group — its Owner, or the account running an official group, once
    it has joined as a player — then everybody else newest joined first
    (``domain/members.py``); each with their face, their Level in it, their
    Player Score where they have one, whether they own the group or run it as
    its Administrator, and when they joined.

    **A block hides nobody here, either way round** (``docs/adr/0193`` §2,
    superseding ADR-0183 §10): both stay in the group and see each other in its
    Members list, as everybody else in it does. No block state is read.

    **For its members, and for whoever runs an official group now** (#566):
    running one is not membership, and the administrator area opens Members from
    the group's players card. That reader is a row only once they have joined as
    a player, and reads the rows and their order as a member does. Anyone else —
    a removed Administrator, one the group was handed away from — meets
    ``group_not_found``, as the group's page refuses a stranger. Three reads
    whatever the size of the group — the Levels, the faces and the scores —
    each one question about the rows it serves, and on an official group a
    fourth, asked first: who runs it now.
    """

    def __init__(
        self,
        *,
        directory: GroupDirectory,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        scores: GroupMemberScores,
        administrators: GroupAdministrators,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._ratings = ratings
        self._faces = faces
        self._scores = scores
        self._administrators = administrators
        self._clock = clock

    async def execute(
        self, group_id: UUID, *, reader_id: UUID, sport: Sport
    ) -> tuple[MemberRow, ...]:
        listing, runner = await listing_for_a_member_or_its_runner(
            self._directory, self._administrators, group_id, reader_id
        )

        levels = await self._ratings.levels_in(listing.members, sport=sport)
        shown = in_members_order(
            [member for member in listing.members if member in levels],
            reader_id=reader_id,
            run_by=who_runs_it(listing, runner),
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
                is_administrator=member == runner,
            )
            for member in shown
        )

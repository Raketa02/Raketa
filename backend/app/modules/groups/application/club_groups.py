"""The club's side of its official groups (#510, ``docs/adr/0183`` §8, §11):
the Groups table on the club website, the handover, and the Join requests the
club answers (``docs/adr/0191`` §1).

**The club watches, and does not run.** It sees each of its official groups —
who runs it, how many players it has and how many wait, how much of its
WhatsApp group has arrived, and how many games it gave birth to — and it
creates none: groups are made by its Administrators, in the app. **The one
thing it does inside a group is answer who asked to join**, whoever runs it
and while nobody does, so a request never waits on nobody.

**Who runs a group is read, never held** (``docs/adr/0184`` §7): the group
records the Administrator it was given to, and whether that administratorship
is still active is a fact about administrators. A group whose Administrator the
club removed reads *needs an administrator* on the next read, with no event on
the group — and its requests wait on it, for whoever the club hands it to.

**A handover moves who answers, and nothing else** (§8): one event on the
group, and its link, policy, size, members and waiting requests stay where they
were. So an Administrator the club invites back after removing them runs again
the groups nobody was handed in the meantime — the group never stopped naming
them — and none of the ones that were.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import (
    AnswerAsClubCommand,
    HandOverCommand,
)
from app.modules.groups.application.views import (
    RequestCard,
    face_of,
    runner_of,
    running_administrators,
)
from app.modules.groups.domain.errors import AdministratorNotActive, GroupNotFound
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.monogram import Monogram, monogram_of
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupBornGames,
    GroupDirectory,
    GroupFaces,
    GroupListing,
    GroupRepository,
    RatedGroupMembers,
    RunningAdministrator,
)
from app.modules.groups.domain.value_objects import GroupKind


@final
@dataclass(frozen=True, slots=True)
class ClubGroupAdministrator:
    """Who runs an official group, as the club's own tables name them: the
    administratorship, and **the name the club gave them** — the one its
    Administrators table prints beside the same person."""

    id: UUID
    name: str


@final
@dataclass(frozen=True, slots=True)
class ClubGroupRow:
    """One row of the club's Groups table.

    ``administrator`` is ``None`` while the group **needs an administrator**.
    ``member_count`` is the group's own count — every Group member, an
    Administrator who joined as a player included — because the club's
    *Players* figure is the same number the group page shows
    (``docs/adr/0183`` §11). ``whatsapp_percent`` is that count over the
    WhatsApp group's size, and may pass 100. ``games`` counts only games born
    in the group.
    """

    id: UUID
    name: str
    monogram: Monogram
    administrator: ClubGroupAdministrator | None
    member_count: int
    waiting_count: int
    whatsapp_size: int
    whatsapp_percent: int
    games: int


def _the_club_s(kind: GroupKind, home_club_id: UUID, club_id: UUID) -> bool:
    """Whether a group is **this club's official group** — the one test every
    act of the club's on a group passes first. A player group whose home club
    this is, another club's group and no group at all are one refusal,
    ``group_not_found``."""

    return kind is GroupKind.OFFICIAL and home_club_id == club_id


async def _the_club_s_group(
    groups: GroupRepository, group_id: UUID, club_id: UUID
) -> Group:
    """The group, to act on, if it is this club's official group."""

    group = await groups.load(group_id)
    if group is None or not _the_club_s(group.kind, group.home_club_id, club_id):
        raise GroupNotFound()
    return group


class ClubGroupRows:
    """Official groups as the club's table draws them — **two reads whatever
    the number of groups**: who runs them now, and the games each gave birth
    to."""

    def __init__(
        self, *, administrators: GroupAdministrators, games: GroupBornGames
    ) -> None:
        self._administrators = administrators
        self._games = games

    async def rows(self, listings: Sequence[GroupListing]) -> tuple[ClubGroupRow, ...]:
        runners = await running_administrators(self._administrators, listings)
        born = await self._games.born_in([listing.id for listing in listings])
        return tuple(
            _row(listing, runner=runners.get(listing.id), games=born.get(listing.id, 0))
            for listing in listings
        )


def _row(
    listing: GroupListing, *, runner: RunningAdministrator | None, games: int
) -> ClubGroupRow:
    size = listing.whatsapp_size
    administrator_id = listing.administrator_id
    if size is None or administrator_id is None:
        raise RuntimeError(f"official group {listing.id} is not official-shaped")
    return ClubGroupRow(
        id=listing.id,
        name=listing.name.value,
        monogram=monogram_of(listing.id, listing.name),
        administrator=(
            None
            if runner is None
            else ClubGroupAdministrator(id=administrator_id, name=runner.name)
        ),
        member_count=listing.member_count,
        waiting_count=len(listing.waiting),
        whatsapp_size=size.value,
        whatsapp_percent=size.percent_arrived(listing.member_count),
        games=games,
    )


def in_table_order(listings: Sequence[GroupListing]) -> list[GroupListing]:
    """By name, as the club's Administrators table is — a handful of groups a
    desk scans for one it knows by name — and by id where two share one, since
    a name is never unique (``docs/adr/0183`` §2)."""

    return sorted(
        listings, key=lambda listing: (listing.name.value.casefold(), str(listing.id))
    )


class ReadClubGroups:
    """The club's Groups table: **every official group at the club**, whoever
    runs it or nobody, by name. A player group at the club is not the club's
    and is never here."""

    def __init__(self, *, directory: GroupDirectory, rows: ClubGroupRows) -> None:
        self._directory = directory
        self._rows = rows

    async def execute(self, club_id: UUID) -> tuple[ClubGroupRow, ...]:
        return await self._rows.rows(
            in_table_order(await self._directory.official_at(club_id))
        )


class HandOverOfficialGroup:
    """The club gives one of its official groups to one of its Administrators
    (``docs/adr/0183`` §8) — any group, one whose Administrator it removed
    included — and answers the group's row as its table now reads.

    Refused in the order a desk could meet them: ``group_not_found`` for
    anything that is not **this club's official group** — no such group, a
    player group whose home club this is, another club's — then
    ``administrator_not_active`` for anybody who is not **an active
    Administrator of this club**. Handing it to whoever runs it records
    nothing.

    **The previous Administrator stops seeing it** on their next read, because
    their Groups tab lists what names them; if they joined it as a player,
    they are still in it. **The requests waiting on it stay**, and the new
    Administrator simply finds them.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        directory: GroupDirectory,
        administrators: GroupAdministrators,
        rows: ClubGroupRows,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._directory = directory
        self._administrators = administrators
        self._rows = rows
        self._uow = uow
        self._clock = clock

    async def execute(self, command: HandOverCommand) -> ClubGroupRow:
        group = await _the_club_s_group(self._groups, command.group_id, command.club_id)
        chosen = command.administrator_id
        runner = await runner_of(self._administrators, chosen)
        if runner is None or runner.club_id != command.club_id:
            raise AdministratorNotActive()

        group.assign_administrator(
            chosen, by=command.assigned_by, occurred_at=self._clock.now()
        )
        await self._groups.save(group)
        listing = (await self._directory.listings([group.id]))[group.id]
        (row,) = await self._rows.rows([listing])
        await self._uow.commit()
        return row


# --------------------------------------------------------------------------- #
# Its Join requests (docs/adr/0191 §1)
# --------------------------------------------------------------------------- #


class ReadClubGroupRequests:
    """The Join requests waiting on one of the club's official groups, **in
    the order people asked** — whoever runs it, and while nobody does.

    Club 20's card, as the administrator's: who is asking and every sport they
    are rated in with its Level — **what deciding needs and nothing more**. No
    block applies: a block keeps two people off one court and hides nobody
    (``docs/adr/0193`` §2). Two reads whatever the length of the queue.
    """

    def __init__(
        self,
        *,
        directory: GroupDirectory,
        faces: GroupFaces,
        ratings: RatedGroupMembers,
    ) -> None:
        self._directory = directory
        self._faces = faces
        self._ratings = ratings

    async def execute(
        self, group_id: UUID, *, club_id: UUID
    ) -> tuple[RequestCard, ...]:
        listing = (await self._directory.listings([group_id])).get(group_id)
        if listing is None or not _the_club_s(
            listing.kind, listing.home_club_id, club_id
        ):
            raise GroupNotFound()
        faces = await self._faces.faces_of(listing.waiting)
        levels = await self._ratings.levels_of(listing.waiting)
        return tuple(
            RequestCard(
                face=face_of(faces, player_id), levels=levels.get(player_id, ())
            )
            for player_id in listing.waiting
        )


class _AnswerAsClub:
    """What both of the club's answers share: the club's own official group,
    loaded to act on, and the save. ``by`` is the Club account, as a
    handover's is."""

    def __init__(
        self, *, groups: GroupRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def _group(self, command: AnswerAsClubCommand) -> Group:
        return await _the_club_s_group(self._groups, command.group_id, command.club_id)

    async def _save(self, group: Group) -> None:
        await self._groups.save(group)
        await self._uow.commit()


class ApproveJoinRequestAsClub(_AnswerAsClub):
    """The person is a Group member at once, as if whoever runs it had said
    yes. Approving somebody already in changes nothing; approving somebody
    with nothing waiting is ``join_request_not_found`` — the administrator, or
    another tab, answered first, or they never asked."""

    async def execute(self, command: AnswerAsClubCommand) -> None:
        group = await self._group(command)
        group.approve(
            command.player_id,
            by=command.answered_by,
            as_club=command.club_id,
            occurred_at=self._clock.now(),
        )
        await self._save(group)


class DeclineJoinRequestAsClub(_AnswerAsClub):
    """The request is gone, silently, and the person may ask again. Declining
    what is not waiting changes nothing, and never removes a member."""

    async def execute(self, command: AnswerAsClubCommand) -> None:
        group = await self._group(command)
        group.decline(
            command.player_id,
            by=command.answered_by,
            as_club=command.club_id,
            occurred_at=self._clock.now(),
        )
        await self._save(group)

"""What an Administrator does with their club's official groups (#509,
``docs/adr/0183`` §3, ``docs/adr/0184`` §8): create one, list theirs, open one,
answer its Join requests and change its settings — **and nothing that deletes
or leaves one**, because running an official group is not membership and only
the club moves it (``docs/adr/0183`` §7–§8).

**Every act is taken as an administratorship the guard read as active**
(``Administering``), on the same request, and on a group **that
administratorship runs**. Anything else — no such group, a player group, a
group at another club, a colleague's — is one refusal, ``group_not_found``,
because all four have one remedy and telling them apart would tell an
administrator which ids are real.

**The administrator's page is not the member's page.** It is the WhatsApp
crowd arriving: the link to post, how many are in, every player newest first
with the day they joined, and who is waiting — and its settings. Its players
list leaves out a blocked pair, either way round, as every Members list does
(``docs/adr/0183`` §10), and **no count moves**.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Sport
from app.modules.groups.application.commands import (
    Administering,
    AnswerAsAdministratorCommand,
    ChangeOfficialGroupSettingsCommand,
    CreateOfficialGroupCommand,
    NoteHandoversSeenCommand,
)
from app.modules.groups.application.membership import hidden_in
from app.modules.groups.application.views import (
    GroupRow,
    NamedClub,
    RequestCard,
    face_of,
    row_of,
)
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.ports import (
    GroupCodeMinter,
    GroupDirectory,
    GroupFace,
    GroupFaces,
    GroupListing,
    GroupRepository,
    HiddenMembers,
    HomeClub,
    HomeClubs,
    RatedGroupMembers,
    SportLevel,
)
from app.modules.groups.domain.value_objects import (
    DeclaredSports,
    GroupCode,
    GroupKind,
    GroupName,
    JoinPolicy,
    WhatsAppSize,
)
from app.shared.ids import new_uuid

# --------------------------------------------------------------------------- #
# What the administrator reads
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class AdministeredClub:
    """The club an administrator acts for: its name for the header, and the
    sports it offers — **what an official group may declare**, so the New
    official group form and the settings offer exactly these."""

    id: UUID
    name: str
    sports: tuple[Sport, ...]


@final
@dataclass(frozen=True, slots=True)
class AdministeredGroupCard:
    """One card on the administrator's Groups tab: the group's row — its
    monogram, name, declared-sport dots and member count — how many are
    waiting, and its home club."""

    row: GroupRow
    waiting_count: int
    home_club: NamedClub


@final
@dataclass(frozen=True, slots=True)
class AdministeredGroups:
    club: AdministeredClub
    #: Every official group this administratorship runs, newest created first.
    groups: tuple[AdministeredGroupCard, ...]


@final
@dataclass(frozen=True, slots=True)
class GroupPlayer:
    """One player on the administrator's page: who, and the day they joined —
    this stay, for somebody who left and came back."""

    face: GroupFace
    joined_at: datetime


@final
@dataclass(frozen=True, slots=True)
class AdministeredGroupPage:
    """An official group as the administrator running it opens it: what its
    page draws, and what its settings hold."""

    row: GroupRow
    home_club: AdministeredClub
    code: GroupCode
    join_policy: JoinPolicy
    whatsapp_size: int
    #: Every player the administrator may see, **newest joined first**.
    players: tuple[GroupPlayer, ...]
    #: Everybody waiting, in the order they asked — *Want to join · N*.
    requests: tuple[RequestCard, ...]


@final
@dataclass(frozen=True, slots=True)
class SavedSettings:
    """The group as its settings left it, and who the save let in — everybody
    the switch to *Anyone* admitted, in the order they asked."""

    page: AdministeredGroupPage
    admitted: tuple[GroupFace, ...]


# --------------------------------------------------------------------------- #
# Whose group it is
# --------------------------------------------------------------------------- #


def _runs(
    administering: Administering,
    *,
    kind: GroupKind,
    administrator_id: UUID | None,
    home_club_id: UUID,
) -> bool:
    return (
        kind is GroupKind.OFFICIAL
        and administrator_id == administering.administrator_id
        and home_club_id == administering.club_id
    )


async def _group_they_run(
    groups: GroupRepository, group_id: UUID, administering: Administering
) -> Group:
    """The group, to act on, if this administratorship runs it."""

    group = await groups.load(group_id)
    if group is None or not _runs(
        administering,
        kind=group.kind,
        administrator_id=group.administrator_id,
        home_club_id=group.home_club_id,
    ):
        raise GroupNotFound()
    return group


async def _listing_they_run(
    directory: GroupDirectory, group_id: UUID, administering: Administering
) -> GroupListing:
    """The group, to read, if this administratorship runs it."""

    listing = (await directory.listings([group_id])).get(group_id)
    if listing is None or not _runs(
        administering,
        kind=listing.kind,
        administrator_id=listing.administrator_id,
        home_club_id=listing.home_club_id,
    ):
        raise GroupNotFound()
    return listing


async def _their_club(clubs: HomeClubs, club_id: UUID) -> HomeClub:
    """The administrator's club — which a signed-in club created and nothing
    deletes, so a club missing here is a broken store rather than an answer."""

    club = (await clubs.by_id([club_id])).get(club_id)
    if club is None:
        raise RuntimeError(f"club {club_id} has an administrator and no listing")
    return club


def _administered(club: HomeClub) -> AdministeredClub:
    return AdministeredClub(id=club.id, name=club.name, sports=club.sports)


def _declared(sports: tuple[Sport, ...], club: HomeClub) -> DeclaredSports:
    return DeclaredSports.at_club(sports, offered=club.sports)


# --------------------------------------------------------------------------- #
# Creating one
# --------------------------------------------------------------------------- #


class CreateOfficialGroup:
    """An Administrator creates an official group for their club, one per
    WhatsApp group they run (``docs/adr/0183`` §3).

    **Its home club is theirs**, fixed; **it has no Owner and nobody in it**.
    Refused in the form's order — the name, the WhatsApp group size, the
    sports — each under its field, and the sports **only from the club's**:
    ``group_sports_required`` for none, ``sport_not_offered_by_club`` naming
    the first that is not the club's. The code is minted last, once there is a
    group to give it to.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        clubs: HomeClubs,
        codes: GroupCodeMinter,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._clubs = clubs
        self._codes = codes
        self._uow = uow
        self._clock = clock

    async def execute(self, command: CreateOfficialGroupCommand) -> UUID:
        administering = command.administering
        name = GroupName(command.name)
        size = WhatsAppSize(command.whatsapp_size)
        club = await _their_club(self._clubs, administering.club_id)
        sports = _declared(tuple(command.sports), club)

        group = Group.create_official_group(
            group_id=new_uuid(),
            name=name,
            club_id=club.id,
            join_policy=command.join_policy,
            administrator_id=administering.administrator_id,
            created_by=administering.account_id,
            whatsapp_size=size,
            sports=sports,
            code=await self._codes.mint(),
            occurred_at=self._clock.now(),
        )
        await self._groups.save(group)
        await self._uow.commit()
        return group.id


# --------------------------------------------------------------------------- #
# Reading them
# --------------------------------------------------------------------------- #


class ReadAdministeredGroups:
    """The administrator's Groups tab: **the official groups this
    administratorship runs**, newest created first — never a colleague's at
    the same club — and the club they act for, whose sports the New official
    group form offers. Two reads whatever the number of groups."""

    def __init__(self, *, directory: GroupDirectory, clubs: HomeClubs) -> None:
        self._directory = directory
        self._clubs = clubs

    async def execute(self, administering: Administering) -> AdministeredGroups:
        club = await _their_club(self._clubs, administering.club_id)
        # An administratorship is one club's, so everything it runs is there.
        listings = await self._directory.run_by(administering.administrator_id)
        home = NamedClub(id=club.id, name=club.name)
        return AdministeredGroups(
            club=_administered(club),
            groups=tuple(
                AdministeredGroupCard(
                    # An official group's dots are what it declares, so no
                    # rating is read for them.
                    row=row_of(listing, {}),
                    waiting_count=len(listing.waiting),
                    home_club=home,
                )
                for listing in listings
            ),
        )


class AdministeredGroupPages:
    """An official group's page as the administrator running it sees it —
    what the read answers, and what the settings answer with before they
    commit.

    Three reads whatever the size of the group: who the administrator and a
    player have a block between (skipped when nobody else is in it), every
    face the page draws in one question, and every waiting person's Levels.
    """

    def __init__(
        self,
        *,
        clubs: HomeClubs,
        faces: GroupFaces,
        ratings: RatedGroupMembers,
        hidden: HiddenMembers,
    ) -> None:
        self._clubs = clubs
        self._faces = faces
        self._ratings = ratings
        self._hidden = hidden

    async def page(
        self, listing: GroupListing, *, administering: Administering
    ) -> AdministeredGroupPage:
        hidden = await hidden_in(self._hidden, listing, administering.account_id)
        newest_first = [
            member for member in reversed(listing.members) if member not in hidden
        ]
        faces = await self._faces.faces_of({*newest_first, *listing.waiting})
        levels = await self._ratings.levels_of(listing.waiting)
        club = await _their_club(self._clubs, listing.home_club_id)
        size = listing.whatsapp_size
        if size is None:
            raise RuntimeError(f"official group {listing.id} has no WhatsApp size")
        return AdministeredGroupPage(
            row=row_of(listing, {}),
            home_club=_administered(club),
            code=listing.code,
            join_policy=listing.join_policy,
            whatsapp_size=size.value,
            players=tuple(
                GroupPlayer(
                    face=face_of(faces, member), joined_at=listing.joined_at[member]
                )
                for member in newest_first
            ),
            requests=_request_cards(listing, faces, levels),
        )


def _request_cards(
    listing: GroupListing,
    faces: Mapping[UUID, GroupFace],
    levels: Mapping[UUID, tuple[SportLevel, ...]],
) -> tuple[RequestCard, ...]:
    return tuple(
        RequestCard(face=face_of(faces, player_id), levels=levels.get(player_id, ()))
        for player_id in listing.waiting
    )


class ReadAdministeredGroup:
    """One official group, opened by the administrator running it."""

    def __init__(
        self, *, directory: GroupDirectory, pages: AdministeredGroupPages
    ) -> None:
        self._directory = directory
        self._pages = pages

    async def execute(
        self, group_id: UUID, *, administering: Administering
    ) -> AdministeredGroupPage:
        listing = await _listing_they_run(self._directory, group_id, administering)
        return await self._pages.page(listing, administering=administering)


# --------------------------------------------------------------------------- #
# Answering its requests
# --------------------------------------------------------------------------- #


class _AnswerAsAdministrator:
    def __init__(
        self, *, groups: GroupRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def _save(self, group: Group) -> None:
        await self._groups.save(group)
        await self._uow.commit()


class ApproveJoinRequestAsAdministrator(_AnswerAsAdministrator):
    """The person is a Group member at once. Approving somebody already in
    changes nothing; approving somebody with nothing waiting is
    ``join_request_not_found`` — nobody is admitted who did not ask."""

    async def execute(self, command: AnswerAsAdministratorCommand) -> None:
        administering = command.administering
        group = await _group_they_run(self._groups, command.group_id, administering)
        group.approve(
            command.player_id,
            by=administering.account_id,
            as_administrator=administering.administrator_id,
            occurred_at=self._clock.now(),
        )
        await self._save(group)


class DeclineJoinRequestAsAdministrator(_AnswerAsAdministrator):
    """The request is gone, silently, and the person may ask again. Declining
    what is not waiting changes nothing."""

    async def execute(self, command: AnswerAsAdministratorCommand) -> None:
        administering = command.administering
        group = await _group_they_run(self._groups, command.group_id, administering)
        group.decline(
            command.player_id,
            by=administering.account_id,
            as_administrator=administering.administrator_id,
            occurred_at=self._clock.now(),
        )
        await self._save(group)


# --------------------------------------------------------------------------- #
# Being told it was handed to you (docs/adr/0192 §1)
# --------------------------------------------------------------------------- #


class NoteHandoversSeen:
    """The Administrator has been told the club handed them these groups — the
    sheet closed, or followed into the group — **once**, for every phone.

    Each named group this administratorship runs and has not been told about
    records ``handover_seen``; **any other is stepped over, never refused**:
    one handed on meanwhile, one told about already, one that is not theirs.
    The person closed a sheet, and nothing they could do about a stale one
    would be an answer to them. One transaction for the lot.
    """

    def __init__(
        self, *, groups: GroupRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def execute(self, command: NoteHandoversSeenCommand) -> None:
        administering = command.administering
        now = self._clock.now()
        for group_id in dict.fromkeys(command.group_ids):
            group = await self._groups.load(group_id)
            if group is None or not _runs(
                administering,
                kind=group.kind,
                administrator_id=group.administrator_id,
                home_club_id=group.home_club_id,
            ):
                continue
            group.note_handover_seen(
                by=administering.account_id,
                as_administrator=administering.administrator_id,
                occurred_at=now,
            )
            await self._groups.save(group)
        await self._uow.commit()


# --------------------------------------------------------------------------- #
# Its settings
# --------------------------------------------------------------------------- #


class ChangeOfficialGroupSettings:
    """Its Administrator saves an official group's settings: name, who can
    join, WhatsApp group size and sports (``docs/adr/0184`` §8).

    **One Save, one answer**: all four are recorded or none is. Refused in the
    order a person could meet them — ``group_not_found`` for a group they do
    not run, then each field under its own name, in the form's order — and
    saving what the group already says records nothing. **Its link never
    changes.**

    **Switching to *Anyone* admits everybody waiting at once**
    (``docs/adr/0183`` §7), and the answer names them, in the order they asked.

    **The answer is drawn before the commit**, as *Edit group*'s is: the page
    reads the block state, which fails closed, and a failure after the commit
    would answer a ``503`` for a save that had happened.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        clubs: HomeClubs,
        directory: GroupDirectory,
        pages: AdministeredGroupPages,
        faces: GroupFaces,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._clubs = clubs
        self._directory = directory
        self._pages = pages
        self._faces = faces
        self._uow = uow
        self._clock = clock

    async def execute(
        self, command: ChangeOfficialGroupSettingsCommand
    ) -> SavedSettings:
        administering = command.administering
        group = await _group_they_run(self._groups, command.group_id, administering)
        name = GroupName(command.name)
        size = WhatsAppSize(command.whatsapp_size)
        club = await _their_club(self._clubs, group.home_club_id)
        sports = _declared(tuple(command.sports), club)

        by = administering.account_id
        running = administering.administrator_id
        now = self._clock.now()
        group.rename(name, by=by, as_administrator=running, occurred_at=now)
        admitted = group.change_join_policy(
            command.join_policy, by=by, as_administrator=running, occurred_at=now
        )
        group.set_whatsapp_size(size, by=by, as_administrator=running, occurred_at=now)
        group.declare_sports(sports, by=by, as_administrator=running, occurred_at=now)
        await self._groups.save(group)

        listing = (await self._directory.listings([group.id]))[group.id]
        page = await self._pages.page(listing, administering=administering)
        faces = await self._faces.faces_of(admitted)
        await self._uow.commit()
        return SavedSettings(
            page=page,
            admitted=tuple(face_of(faces, player_id) for player_id in admitted),
        )

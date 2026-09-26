"""Request-scoped declarations for the Groups context.

*When* each adapter is built and how long it lives, never *what* — every
concrete class comes from ``app.bootstrap.composition``, and
``tests/unit/test_composition_root.py`` fails this file if it imports one.

The repository is built **per request** because it remembers the stream versions
it loaded for one unit of work; the reads are per request because they read
through the request's own session.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_group_administrators,
    build_group_born_games,
    build_group_code_minter,
    build_group_directory,
    build_group_faces,
    build_group_member_scores,
    build_group_repository,
    build_hidden_members,
    build_home_clubs,
    build_rated_group_members,
    build_reader_areas,
)
from app.modules.administrators.presentation.dependencies import (
    AdministratorAtClubDep,
)
from app.modules.groups.application.answer_join_request import (
    ApproveJoinRequest,
    DeclineJoinRequest,
)
from app.modules.groups.application.club_groups import (
    ClubGroupRows,
    HandOverOfficialGroup,
    ReadClubGroups,
)
from app.modules.groups.application.commands import Administering
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.application.delete_group import DeleteGroup
from app.modules.groups.application.edit_group import EditGroup
from app.modules.groups.application.join_group import JoinGroup
from app.modules.groups.application.leave_group import LeaveGroup
from app.modules.groups.application.official_groups import (
    AdministeredGroupPages,
    ApproveJoinRequestAsAdministrator,
    ChangeOfficialGroupSettings,
    CreateOfficialGroup,
    DeclineJoinRequestAsAdministrator,
    ReadAdministeredGroup,
    ReadAdministeredGroups,
)
from app.modules.groups.application.read_group import GroupPages, ReadGroup
from app.modules.groups.application.read_group_by_link import ReadGroupByLink
from app.modules.groups.application.read_group_members import ReadGroupMembers
from app.modules.groups.application.read_join_requests import ReadJoinRequests
from app.modules.groups.application.read_my_groups import ReadMyGroups
from app.modules.groups.application.search_groups_to_join import SearchGroupsToJoin
from app.modules.groups.application.search_home_clubs import SearchHomeClubs
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupBornGames,
    GroupDirectory,
    GroupFaces,
    GroupMemberScores,
    GroupRepository,
    HiddenMembers,
    HomeClubs,
    RatedGroupMembers,
    ReaderAreas,
)


def get_group_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> GroupRepository:
    return build_group_repository(db, event_store=event_store, events=events)


GroupRepositoryDep = Annotated[GroupRepository, Depends(get_group_repository)]


def get_group_directory(db: DbSession) -> GroupDirectory:
    return build_group_directory(db)


GroupDirectoryDep = Annotated[GroupDirectory, Depends(get_group_directory)]


def get_home_clubs(db: DbSession) -> HomeClubs:
    return build_home_clubs(db)


HomeClubsDep = Annotated[HomeClubs, Depends(get_home_clubs)]


def get_rated_group_members(db: DbSession) -> RatedGroupMembers:
    return build_rated_group_members(db)


RatedGroupMembersDep = Annotated[RatedGroupMembers, Depends(get_rated_group_members)]


def get_group_faces(db: DbSession, settings: SettingsDep) -> GroupFaces:
    return build_group_faces(db, settings=settings)


GroupFacesDep = Annotated[GroupFaces, Depends(get_group_faces)]


def get_group_member_scores(db: DbSession) -> GroupMemberScores:
    return build_group_member_scores(db)


GroupMemberScoresDep = Annotated[GroupMemberScores, Depends(get_group_member_scores)]


def get_hidden_members(db: DbSession) -> HiddenMembers:
    return build_hidden_members(db)


HiddenMembersDep = Annotated[HiddenMembers, Depends(get_hidden_members)]


def get_group_administrators(db: DbSession) -> GroupAdministrators:
    return build_group_administrators(db)


GroupAdministratorsDep = Annotated[
    GroupAdministrators, Depends(get_group_administrators)
]


def get_group_born_games() -> GroupBornGames:
    return build_group_born_games()


GroupBornGamesDep = Annotated[GroupBornGames, Depends(get_group_born_games)]


def get_reader_areas(db: DbSession) -> ReaderAreas:
    return build_reader_areas(db)


ReaderAreasDep = Annotated[ReaderAreas, Depends(get_reader_areas)]


def get_create_player_group(
    db: DbSession,
    groups: GroupRepositoryDep,
    clubs: HomeClubsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> CreatePlayerGroup:
    return CreatePlayerGroup(
        groups=groups,
        clubs=clubs,
        codes=build_group_code_minter(db),
        uow=uow,
        clock=clock,
    )


CreatePlayerGroupDep = Annotated[CreatePlayerGroup, Depends(get_create_player_group)]


def get_join_group(
    groups: GroupRepositoryDep,
    directory: GroupDirectoryDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
    administrators: GroupAdministratorsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> JoinGroup:
    return JoinGroup(
        groups=groups,
        directory=directory,
        ratings=ratings,
        faces=faces,
        administrators=administrators,
        uow=uow,
        clock=clock,
    )


JoinGroupDep = Annotated[JoinGroup, Depends(get_join_group)]


def get_read_my_groups(
    directory: GroupDirectoryDep, clubs: HomeClubsDep, ratings: RatedGroupMembersDep
) -> ReadMyGroups:
    return ReadMyGroups(directory=directory, clubs=clubs, ratings=ratings)


ReadMyGroupsDep = Annotated[ReadMyGroups, Depends(get_read_my_groups)]


def get_read_group_by_link(
    directory: GroupDirectoryDep, clubs: HomeClubsDep, ratings: RatedGroupMembersDep
) -> ReadGroupByLink:
    return ReadGroupByLink(directory=directory, clubs=clubs, ratings=ratings)


ReadGroupByLinkDep = Annotated[ReadGroupByLink, Depends(get_read_group_by_link)]


def get_group_pages(
    clubs: HomeClubsDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
    hidden: HiddenMembersDep,
    administrators: GroupAdministratorsDep,
) -> GroupPages:
    return GroupPages(
        clubs=clubs,
        ratings=ratings,
        faces=faces,
        hidden=hidden,
        administrators=administrators,
    )


GroupPagesDep = Annotated[GroupPages, Depends(get_group_pages)]


def get_read_group(directory: GroupDirectoryDep, pages: GroupPagesDep) -> ReadGroup:
    return ReadGroup(directory=directory, pages=pages)


ReadGroupDep = Annotated[ReadGroup, Depends(get_read_group)]


def get_search_home_clubs(
    directory: GroupDirectoryDep,
    clubs: HomeClubsDep,
    areas: ReaderAreasDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
    administrators: GroupAdministratorsDep,
) -> SearchHomeClubs:
    return SearchHomeClubs(
        clubs=clubs,
        areas=areas,
        directory=directory,
        ratings=ratings,
        faces=faces,
        administrators=administrators,
    )


SearchHomeClubsDep = Annotated[SearchHomeClubs, Depends(get_search_home_clubs)]


def get_search_groups_to_join(
    directory: GroupDirectoryDep,
    clubs: HomeClubsDep,
    areas: ReaderAreasDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
    administrators: GroupAdministratorsDep,
) -> SearchGroupsToJoin:
    return SearchGroupsToJoin(
        clubs=clubs,
        areas=areas,
        directory=directory,
        ratings=ratings,
        faces=faces,
        administrators=administrators,
    )


SearchGroupsToJoinDep = Annotated[
    SearchGroupsToJoin, Depends(get_search_groups_to_join)
]


def get_read_join_requests(
    directory: GroupDirectoryDep,
    faces: GroupFacesDep,
    ratings: RatedGroupMembersDep,
) -> ReadJoinRequests:
    return ReadJoinRequests(directory=directory, faces=faces, ratings=ratings)


ReadJoinRequestsDep = Annotated[ReadJoinRequests, Depends(get_read_join_requests)]


def get_approve_join_request(
    groups: GroupRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> ApproveJoinRequest:
    return ApproveJoinRequest(groups=groups, uow=uow, clock=clock)


ApproveJoinRequestDep = Annotated[ApproveJoinRequest, Depends(get_approve_join_request)]


def get_decline_join_request(
    groups: GroupRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> DeclineJoinRequest:
    return DeclineJoinRequest(groups=groups, uow=uow, clock=clock)


DeclineJoinRequestDep = Annotated[DeclineJoinRequest, Depends(get_decline_join_request)]


def get_leave_group(
    groups: GroupRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> LeaveGroup:
    return LeaveGroup(groups=groups, uow=uow, clock=clock)


LeaveGroupDep = Annotated[LeaveGroup, Depends(get_leave_group)]


def get_delete_group(
    groups: GroupRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> DeleteGroup:
    return DeleteGroup(groups=groups, uow=uow, clock=clock)


DeleteGroupDep = Annotated[DeleteGroup, Depends(get_delete_group)]


def get_edit_group(
    groups: GroupRepositoryDep,
    directory: GroupDirectoryDep,
    pages: GroupPagesDep,
    faces: GroupFacesDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> EditGroup:
    return EditGroup(
        groups=groups,
        directory=directory,
        pages=pages,
        faces=faces,
        uow=uow,
        clock=clock,
    )


EditGroupDep = Annotated[EditGroup, Depends(get_edit_group)]


def get_read_group_members(
    directory: GroupDirectoryDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
    scores: GroupMemberScoresDep,
    hidden: HiddenMembersDep,
    administrators: GroupAdministratorsDep,
    clock: ClockDep,
) -> ReadGroupMembers:
    return ReadGroupMembers(
        directory=directory,
        ratings=ratings,
        faces=faces,
        scores=scores,
        hidden=hidden,
        administrators=administrators,
        clock=clock,
    )


ReadGroupMembersDep = Annotated[ReadGroupMembers, Depends(get_read_group_members)]


# --- The administrator surface ------------------------------------------------


def administering(administratorship: AdministratorAtClubDep) -> Administering:
    """**The administrator guard**, in this context's words: the administratorship
    it read as active at the club the path names, on this request, and the
    account behind it — which an active administratorship always has."""

    account_id = administratorship.account_id
    if account_id is None:
        raise RuntimeError(
            f"an active administratorship with no account: {administratorship.id}"
        )
    return Administering(
        club_id=administratorship.club_id,
        administrator_id=administratorship.id,
        account_id=account_id,
    )


AdministeringDep = Annotated[Administering, Depends(administering)]


def get_create_official_group(
    db: DbSession,
    groups: GroupRepositoryDep,
    clubs: HomeClubsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> CreateOfficialGroup:
    return CreateOfficialGroup(
        groups=groups,
        clubs=clubs,
        codes=build_group_code_minter(db),
        uow=uow,
        clock=clock,
    )


CreateOfficialGroupDep = Annotated[
    CreateOfficialGroup, Depends(get_create_official_group)
]


def get_read_administered_groups(
    directory: GroupDirectoryDep, clubs: HomeClubsDep
) -> ReadAdministeredGroups:
    return ReadAdministeredGroups(directory=directory, clubs=clubs)


ReadAdministeredGroupsDep = Annotated[
    ReadAdministeredGroups, Depends(get_read_administered_groups)
]


def get_administered_group_pages(
    clubs: HomeClubsDep,
    faces: GroupFacesDep,
    ratings: RatedGroupMembersDep,
    hidden: HiddenMembersDep,
) -> AdministeredGroupPages:
    return AdministeredGroupPages(
        clubs=clubs, faces=faces, ratings=ratings, hidden=hidden
    )


AdministeredGroupPagesDep = Annotated[
    AdministeredGroupPages, Depends(get_administered_group_pages)
]


def get_read_administered_group(
    directory: GroupDirectoryDep, pages: AdministeredGroupPagesDep
) -> ReadAdministeredGroup:
    return ReadAdministeredGroup(directory=directory, pages=pages)


ReadAdministeredGroupDep = Annotated[
    ReadAdministeredGroup, Depends(get_read_administered_group)
]


def get_approve_as_administrator(
    groups: GroupRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> ApproveJoinRequestAsAdministrator:
    return ApproveJoinRequestAsAdministrator(groups=groups, uow=uow, clock=clock)


ApproveAsAdministratorDep = Annotated[
    ApproveJoinRequestAsAdministrator, Depends(get_approve_as_administrator)
]


def get_decline_as_administrator(
    groups: GroupRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> DeclineJoinRequestAsAdministrator:
    return DeclineJoinRequestAsAdministrator(groups=groups, uow=uow, clock=clock)


DeclineAsAdministratorDep = Annotated[
    DeclineJoinRequestAsAdministrator, Depends(get_decline_as_administrator)
]


def get_change_official_group_settings(
    groups: GroupRepositoryDep,
    clubs: HomeClubsDep,
    directory: GroupDirectoryDep,
    pages: AdministeredGroupPagesDep,
    faces: GroupFacesDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeOfficialGroupSettings:
    return ChangeOfficialGroupSettings(
        groups=groups,
        clubs=clubs,
        directory=directory,
        pages=pages,
        faces=faces,
        uow=uow,
        clock=clock,
    )


ChangeOfficialGroupSettingsDep = Annotated[
    ChangeOfficialGroupSettings, Depends(get_change_official_group_settings)
]


# --- The club surface -----------------------------------------------------------


def get_club_group_rows(
    administrators: GroupAdministratorsDep, games: GroupBornGamesDep
) -> ClubGroupRows:
    return ClubGroupRows(administrators=administrators, games=games)


ClubGroupRowsDep = Annotated[ClubGroupRows, Depends(get_club_group_rows)]


def get_read_club_groups(
    directory: GroupDirectoryDep, rows: ClubGroupRowsDep
) -> ReadClubGroups:
    return ReadClubGroups(directory=directory, rows=rows)


ReadClubGroupsDep = Annotated[ReadClubGroups, Depends(get_read_club_groups)]


def get_hand_over_official_group(
    groups: GroupRepositoryDep,
    directory: GroupDirectoryDep,
    administrators: GroupAdministratorsDep,
    rows: ClubGroupRowsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> HandOverOfficialGroup:
    return HandOverOfficialGroup(
        groups=groups,
        directory=directory,
        administrators=administrators,
        rows=rows,
        uow=uow,
        clock=clock,
    )


HandOverOfficialGroupDep = Annotated[
    HandOverOfficialGroup, Depends(get_hand_over_official_group)
]

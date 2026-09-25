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
from app.modules.groups.application.answer_join_request import (
    ApproveJoinRequest,
    DeclineJoinRequest,
)
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.application.delete_group import DeleteGroup
from app.modules.groups.application.edit_group import EditGroup
from app.modules.groups.application.join_group import JoinGroup
from app.modules.groups.application.leave_group import LeaveGroup
from app.modules.groups.application.read_group import GroupPages, ReadGroup
from app.modules.groups.application.read_join_requests import ReadJoinRequests
from app.modules.groups.application.read_group_members import ReadGroupMembers
from app.modules.groups.application.read_my_groups import ReadMyGroups
from app.modules.groups.application.search_groups_to_join import SearchGroupsToJoin
from app.modules.groups.application.search_home_clubs import SearchHomeClubs
from app.modules.groups.domain.ports import (
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
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> JoinGroup:
    return JoinGroup(
        groups=groups,
        directory=directory,
        ratings=ratings,
        faces=faces,
        uow=uow,
        clock=clock,
    )


JoinGroupDep = Annotated[JoinGroup, Depends(get_join_group)]


def get_read_my_groups(
    directory: GroupDirectoryDep, clubs: HomeClubsDep, ratings: RatedGroupMembersDep
) -> ReadMyGroups:
    return ReadMyGroups(directory=directory, clubs=clubs, ratings=ratings)


ReadMyGroupsDep = Annotated[ReadMyGroups, Depends(get_read_my_groups)]


def get_group_pages(
    clubs: HomeClubsDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
    hidden: HiddenMembersDep,
) -> GroupPages:
    return GroupPages(clubs=clubs, ratings=ratings, faces=faces, hidden=hidden)


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
) -> SearchHomeClubs:
    return SearchHomeClubs(
        clubs=clubs, areas=areas, directory=directory, ratings=ratings, faces=faces
    )


SearchHomeClubsDep = Annotated[SearchHomeClubs, Depends(get_search_home_clubs)]


def get_search_groups_to_join(
    directory: GroupDirectoryDep,
    clubs: HomeClubsDep,
    areas: ReaderAreasDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
) -> SearchGroupsToJoin:
    return SearchGroupsToJoin(
        clubs=clubs, areas=areas, directory=directory, ratings=ratings, faces=faces
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
    clock: ClockDep,
) -> ReadGroupMembers:
    return ReadGroupMembers(
        directory=directory,
        ratings=ratings,
        faces=faces,
        scores=scores,
        hidden=hidden,
        clock=clock,
    )


ReadGroupMembersDep = Annotated[ReadGroupMembers, Depends(get_read_group_members)]

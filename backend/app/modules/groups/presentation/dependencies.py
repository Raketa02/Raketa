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
    build_group_repository,
    build_home_clubs,
    build_rated_group_members,
    build_reader_areas,
)
from app.modules.groups.application.answer_join_request import (
    ApproveJoinRequest,
    DeclineJoinRequest,
)
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.application.join_group import JoinGroup
from app.modules.groups.application.read_group import ReadGroup
from app.modules.groups.application.read_join_requests import ReadJoinRequests
from app.modules.groups.application.read_my_groups import ReadMyGroups
from app.modules.groups.application.search_groups_to_join import SearchGroupsToJoin
from app.modules.groups.application.search_home_clubs import SearchHomeClubs
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupFaces,
    GroupRepository,
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


def get_read_group(
    directory: GroupDirectoryDep,
    clubs: HomeClubsDep,
    ratings: RatedGroupMembersDep,
    faces: GroupFacesDep,
) -> ReadGroup:
    return ReadGroup(directory=directory, clubs=clubs, ratings=ratings, faces=faces)


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

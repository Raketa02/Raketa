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
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.application.join_group import JoinGroup
from app.modules.groups.application.read_group import ReadGroup
from app.modules.groups.application.read_my_groups import ReadMyGroups
from app.modules.groups.application.search_home_clubs import SearchHomeClubs
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupRepository,
    HomeClubs,
    RatedGroupMembers,
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
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> JoinGroup:
    return JoinGroup(
        groups=groups, directory=directory, ratings=ratings, uow=uow, clock=clock
    )


JoinGroupDep = Annotated[JoinGroup, Depends(get_join_group)]


def get_read_my_groups(
    directory: GroupDirectoryDep, clubs: HomeClubsDep, ratings: RatedGroupMembersDep
) -> ReadMyGroups:
    return ReadMyGroups(directory=directory, clubs=clubs, ratings=ratings)


ReadMyGroupsDep = Annotated[ReadMyGroups, Depends(get_read_my_groups)]


def get_read_group(
    db: DbSession,
    settings: SettingsDep,
    directory: GroupDirectoryDep,
    clubs: HomeClubsDep,
    ratings: RatedGroupMembersDep,
) -> ReadGroup:
    return ReadGroup(
        directory=directory,
        clubs=clubs,
        ratings=ratings,
        faces=build_group_faces(db, settings=settings),
    )


ReadGroupDep = Annotated[ReadGroup, Depends(get_read_group)]


def get_search_home_clubs(
    db: DbSession,
    directory: GroupDirectoryDep,
    clubs: HomeClubsDep,
    ratings: RatedGroupMembersDep,
) -> SearchHomeClubs:
    return SearchHomeClubs(
        clubs=clubs,
        areas=build_reader_areas(db),
        directory=directory,
        ratings=ratings,
    )


SearchHomeClubsDep = Annotated[SearchHomeClubs, Depends(get_search_home_clubs)]

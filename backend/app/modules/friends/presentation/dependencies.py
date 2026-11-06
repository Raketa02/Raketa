"""Request-scoped declarations for the Friends context.

*When* each adapter is built, never *what* — every concrete class comes from
``app.bootstrap.composition``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    EventRuntimeDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_friend_faces,
    build_friend_levels,
    build_friend_link_codes,
    build_friend_link_repository,
    build_friendship_directory,
    build_friendship_repository,
    build_readers_blocks,
    build_readers_groups,
)
from app.modules.friends.application.link import (
    OpenAFriendLink,
    ReadAFriendLink,
    ReadYourFriendLink,
    ReplaceYourFriendLink,
)
from app.modules.friends.application.reads import (
    ReadFriendRequests,
    ReadFriends,
    ReadGroupsToAddFrom,
)
from app.modules.friends.application.requests import (
    AcceptFriendRequest,
    AskToBeFriends,
    CancelFriendRequest,
    RemoveFriend,
    SetAsideFriendRequest,
)
from app.modules.friends.domain.ports import (
    FriendFaces,
    FriendLinkCodes,
    FriendLinkRepository,
    FriendshipDirectory,
    FriendshipRepository,
    ReadersBlocks,
    ReadersGroups,
)


def get_friendship_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> FriendshipRepository:
    # Per request: it remembers the stream versions it read.
    return build_friendship_repository(db, event_store=event_store, events=events)


FriendshipRepositoryDep = Annotated[
    FriendshipRepository, Depends(get_friendship_repository)
]


def get_friendship_directory(db: DbSession) -> FriendshipDirectory:
    return build_friendship_directory(db)


FriendshipDirectoryDep = Annotated[
    FriendshipDirectory, Depends(get_friendship_directory)
]


def get_readers_blocks(db: DbSession, runtime: EventRuntimeDep) -> ReadersBlocks:
    return build_readers_blocks(db, runtime=runtime)


ReadersBlocksDep = Annotated[ReadersBlocks, Depends(get_readers_blocks)]


def get_readers_groups(db: DbSession) -> ReadersGroups:
    return build_readers_groups(db)


ReadersGroupsDep = Annotated[ReadersGroups, Depends(get_readers_groups)]


def get_friend_faces(
    db: DbSession, settings: SettingsDep, runtime: EventRuntimeDep
) -> FriendFaces:
    return build_friend_faces(db, settings=settings, runtime=runtime)


FriendFacesDep = Annotated[FriendFaces, Depends(get_friend_faces)]


def get_ask_to_be_friends(
    friendships: FriendshipRepositoryDep,
    blocks: ReadersBlocksDep,
    groups: ReadersGroupsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AskToBeFriends:
    return AskToBeFriends(
        friendships=friendships, blocks=blocks, groups=groups, uow=uow, clock=clock
    )


AskToBeFriendsDep = Annotated[AskToBeFriends, Depends(get_ask_to_be_friends)]


def get_accept_friend_request(
    friendships: FriendshipRepositoryDep,
    blocks: ReadersBlocksDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AcceptFriendRequest:
    return AcceptFriendRequest(
        friendships=friendships, blocks=blocks, uow=uow, clock=clock
    )


AcceptFriendRequestDep = Annotated[
    AcceptFriendRequest, Depends(get_accept_friend_request)
]


def get_set_aside_friend_request(
    friendships: FriendshipRepositoryDep,
    blocks: ReadersBlocksDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetAsideFriendRequest:
    return SetAsideFriendRequest(
        friendships=friendships, blocks=blocks, uow=uow, clock=clock
    )


SetAsideFriendRequestDep = Annotated[
    SetAsideFriendRequest, Depends(get_set_aside_friend_request)
]


def get_cancel_friend_request(
    friendships: FriendshipRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> CancelFriendRequest:
    return CancelFriendRequest(friendships=friendships, uow=uow, clock=clock)


CancelFriendRequestDep = Annotated[
    CancelFriendRequest, Depends(get_cancel_friend_request)
]


def get_remove_friend(
    friendships: FriendshipRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> RemoveFriend:
    return RemoveFriend(friendships=friendships, uow=uow, clock=clock)


RemoveFriendDep = Annotated[RemoveFriend, Depends(get_remove_friend)]


def get_read_friends(
    db: DbSession,
    directory: FriendshipDirectoryDep,
    faces: FriendFacesDep,
    runtime: EventRuntimeDep,
) -> ReadFriends:
    return ReadFriends(
        directory=directory,
        faces=faces,
        levels=build_friend_levels(db, runtime=runtime),
    )


ReadFriendsDep = Annotated[ReadFriends, Depends(get_read_friends)]


def get_read_friend_requests(
    directory: FriendshipDirectoryDep,
    blocks: ReadersBlocksDep,
    faces: FriendFacesDep,
) -> ReadFriendRequests:
    return ReadFriendRequests(directory=directory, blocks=blocks, faces=faces)


ReadFriendRequestsDep = Annotated[ReadFriendRequests, Depends(get_read_friend_requests)]


def get_read_groups_to_add_from(
    groups: ReadersGroupsDep,
    directory: FriendshipDirectoryDep,
    blocks: ReadersBlocksDep,
) -> ReadGroupsToAddFrom:
    return ReadGroupsToAddFrom(groups=groups, directory=directory, blocks=blocks)


ReadGroupsToAddFromDep = Annotated[
    ReadGroupsToAddFrom, Depends(get_read_groups_to_add_from)
]


# -- the Friend link (#748) ---------------------------------------------------


def get_friend_link_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> FriendLinkRepository:
    # Per request: it remembers the stream versions it read.
    return build_friend_link_repository(db, event_store=event_store, events=events)


FriendLinkRepositoryDep = Annotated[
    FriendLinkRepository, Depends(get_friend_link_repository)
]


def get_friend_link_codes(db: DbSession) -> FriendLinkCodes:
    return build_friend_link_codes(db)


FriendLinkCodesDep = Annotated[FriendLinkCodes, Depends(get_friend_link_codes)]


def get_read_your_friend_link(
    links: FriendLinkRepositoryDep,
    codes: FriendLinkCodesDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ReadYourFriendLink:
    return ReadYourFriendLink(links=links, codes=codes, uow=uow, clock=clock)


ReadYourFriendLinkDep = Annotated[
    ReadYourFriendLink, Depends(get_read_your_friend_link)
]


def get_replace_your_friend_link(
    links: FriendLinkRepositoryDep,
    codes: FriendLinkCodesDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ReplaceYourFriendLink:
    return ReplaceYourFriendLink(links=links, codes=codes, uow=uow, clock=clock)


ReplaceYourFriendLinkDep = Annotated[
    ReplaceYourFriendLink, Depends(get_replace_your_friend_link)
]


def get_open_a_friend_link(
    codes: FriendLinkCodesDep,
    friendships: FriendshipRepositoryDep,
    blocks: ReadersBlocksDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> OpenAFriendLink:
    return OpenAFriendLink(
        codes=codes, friendships=friendships, blocks=blocks, uow=uow, clock=clock
    )


OpenAFriendLinkDep = Annotated[OpenAFriendLink, Depends(get_open_a_friend_link)]


def get_read_a_friend_link(
    codes: FriendLinkCodesDep, faces: FriendFacesDep
) -> ReadAFriendLink:
    return ReadAFriendLink(codes=codes, faces=faces)


ReadAFriendLinkDep = Annotated[ReadAFriendLink, Depends(get_read_a_friend_link)]

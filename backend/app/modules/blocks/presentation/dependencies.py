"""Request-scoped declarations for the Blocks context.

*When* each adapter is built and how long it lives, never *what* — every concrete
class comes from `app.bootstrap.composition`, and
`tests/unit/test_composition_root.py` fails this file if it imports one.
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
    build_block_query,
    build_block_repository,
    build_blocked_faces,
)
from app.modules.blocks.application.block_player import BlockPlayer
from app.modules.blocks.application.blocked_players import ReadBlockedPlayers
from app.modules.blocks.application.unblock_player import UnblockPlayer
from app.modules.blocks.domain.ports import BlockedFaces, BlockQuery, BlockRepository


def get_block_repository(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> BlockRepository:
    # Per request, and it must be: it remembers the stream versions it read, and
    # one request's versions must never answer for another's.
    return build_block_repository(event_store=event_store, events=events)


BlockRepositoryDep = Annotated[BlockRepository, Depends(get_block_repository)]


def get_block_query(db: DbSession, runtime: EventRuntimeDep) -> BlockQuery:
    # Per request, over the request's own session, so a block taken a moment ago
    # is visible to the read that follows it.
    return build_block_query(db, runtime=runtime)


BlockQueryDep = Annotated[BlockQuery, Depends(get_block_query)]


def get_blocked_faces(
    db: DbSession, settings: SettingsDep, runtime: EventRuntimeDep
) -> BlockedFaces:
    return build_blocked_faces(db, settings=settings, runtime=runtime)


BlockedFacesDep = Annotated[BlockedFaces, Depends(get_blocked_faces)]


def get_read_blocked_players(
    blocks: BlockQueryDep, faces: BlockedFacesDep
) -> ReadBlockedPlayers:
    return ReadBlockedPlayers(blocks=blocks, faces=faces)


ReadBlockedPlayersDep = Annotated[ReadBlockedPlayers, Depends(get_read_blocked_players)]


def get_block_player(
    blocks: BlockRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> BlockPlayer:
    return BlockPlayer(blocks=blocks, uow=uow, clock=clock)


BlockPlayerDep = Annotated[BlockPlayer, Depends(get_block_player)]


def get_unblock_player(
    blocks: BlockRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> UnblockPlayer:
    return UnblockPlayer(blocks=blocks, uow=uow, clock=clock)


UnblockPlayerDep = Annotated[UnblockPlayer, Depends(get_unblock_player)]

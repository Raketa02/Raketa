"""The register of what Discovery demands of other contexts, and who signs each
demand (#793; ``docs/adr/0204`` §10).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's. **Five rows**, each
a port in Discovery's own words signed in ``discovery/infrastructure/``, so each
arrow runs out of ``discovery`` into the neighbour and none comes back:

- **what the owners hold** (``DirectorySources``, over ``users``' row and the
  Player profile's stream): every directory entry is written from it, live and
  in the rebuild;
- **the reader's relations** (``ReadersRelations``, over Friends' own read):
  the round friend button on every people card;
- **blocks either way** (``BlocksEitherWay``, over the one place a block is
  read): nobody a block stands between is on a people row;
- **the levels held** (``LevelsHeld``, over rating's published read): a tile's
  sport lines and See all's sport pill;
- **a face's link** (``DirectoryFaces``, over the photo store).

The directory itself (``PlayerDirectory``) is the context's own storage and not
a demand.

**A row carries a builder over a session**, as the other registers' do; the
faces' builds over the settings the session's application runs under.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_blocks_either_way,
    build_directory_faces,
    build_directory_sources,
    build_levels_held,
    build_readers_relations,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.discovery.domain.ports import (
    BlocksEitherWay,
    DirectoryFaces,
    DirectorySources,
    LevelsHeld,
    ReadersRelations,
)

P = TypeVar("P")

#: What Discovery asks of the rest of the platform.
DISCOVERY_DEMANDS: tuple[type, ...] = (
    DirectorySources,
    ReadersRelations,
    BlocksEitherWay,
    LevelsHeld,
    DirectoryFaces,
)


DISCOVERY_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=DirectorySources,
        name="AccountDirectorySources",
        build=build_directory_sources,
    ),
    RegisteredImplementation(
        port=ReadersRelations,
        name="FriendsReadersRelations",
        build=build_readers_relations,
    ),
    RegisteredImplementation(
        port=BlocksEitherWay,
        name="QueriedBlocksEitherWay",
        build=build_blocks_either_way,
    ),
    RegisteredImplementation(
        port=LevelsHeld,
        name="PublishedLevelsHeld",
        build=build_levels_held,
    ),
    RegisteredImplementation(
        port=DirectoryFaces,
        name="PresignedDirectoryFaces",
        build=lambda session: build_directory_faces(get_settings()),
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in DISCOVERY_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "DISCOVERY_DEMANDS",
    "DISCOVERY_IMPLEMENTATIONS",
    "implementations_of",
]

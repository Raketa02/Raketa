"""The register of what Rankings demands of other contexts, and who signs each
demand (#768, #771; ``docs/adr/0203`` §10).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's. **Six rows**, each
a port in Rankings' own words signed in ``rankings/infrastructure/``, so each
of these arrows runs out of ``rankings`` into the neighbour, and none comes
back (Home's arrow into ``rankings`` is Proposals' own row, ``RankingOnHome``):

- **the rating's record** (``RatingHistories``, over the rating's own streams):
  every row is folded from it, live and in the rebuild;
- **the faces** (``RankedFaces``, over ``users``' nicknames and the Player
  profile's photographs);
- **a level held** (``SportLevels``, over rating's published read), which the
  card's *no level* is read live from;
- **the reader's friends** (``ReadersFriends``, over Friends' own read of the
  reader's relations), which the Friends view is worked out over (#771);
- **the reader's blocks, both ways** (``BlocksEitherWay``, over the blocks' one
  query), whose rows each view leaves out (#772);
- **a player's *Show me in General*** (``GeneralSwitches``, over the Player
  profile's repository), which the rows follow (#772).

The projection itself (``RankingRows``) is the context's own storage and not a
demand.

**A row carries a builder over a session**, as the other registers' do.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_general_switches,
    build_ranked_faces,
    build_rating_histories,
    build_blocks_either_way,
    build_readers_friends,
    build_sport_levels,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.rankings.domain.ports import (
    GeneralSwitches,
    RankedFaces,
    RatingHistories,
    BlocksEitherWay,
    ReadersFriends,
    SportLevels,
)

P = TypeVar("P")

#: What Rankings asks of the rest of the platform.
RANKING_DEMANDS: tuple[type, ...] = (
    RatingHistories,
    RankedFaces,
    SportLevels,
    ReadersFriends,
    BlocksEitherWay,
    GeneralSwitches,
)


RANKING_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=RatingHistories,
        name="RatingStreamHistories",
        build=build_rating_histories,
    ),
    RegisteredImplementation(
        port=RankedFaces,
        name="ProfileRankedFaces",
        build=lambda session: build_ranked_faces(session, settings=get_settings()),
    ),
    RegisteredImplementation(
        port=SportLevels,
        name="RatedSportLevels",
        build=build_sport_levels,
    ),
    RegisteredImplementation(
        port=ReadersFriends,
        name="FriendsReadersFriends",
        build=build_readers_friends,
    ),
    RegisteredImplementation(
        port=BlocksEitherWay,
        name="QueriedBlocksEitherWay",
        build=build_blocks_either_way,
    ),
    RegisteredImplementation(
        port=GeneralSwitches,
        name="ProfileGeneralSwitches",
        build=build_general_switches,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in RANKING_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "RANKING_DEMANDS",
    "RANKING_IMPLEMENTATIONS",
    "implementations_of",
]

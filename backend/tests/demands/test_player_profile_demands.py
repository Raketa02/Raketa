"""What the Player profile demands of other contexts (#726), run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/player_profile_demands.py`` is enrolled here automatically.
**Every club is made through its own aggregate**, saved by its own repository —
never an ``INSERT``.

**Where a club is** is the question: a player who refuses the phone's location
picks a club near where they play, and its point becomes their area
(``docs/adr/0200`` §10). The answer is the point **as precise as the desk
dropped it** — the rounding is the profile's — and nothing for an id that names
no club.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_club_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.bootstrap.player_profile_demands import (
    PLAYER_PROFILE_DEMANDS,
    PLAYER_PROFILE_IMPLEMENTATIONS,
    implementations_of,
)
from app.kernel import Sport
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.value_objects import (
    City,
    ClubDetails,
    ClubName,
    District,
    MapPoint,
    OfferedSports,
)
from app.modules.player_profile.domain.ports import ClubPoint, ClubPoints
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


async def _a_club(session, *, latitude: float, longitude: float) -> UUID:
    """A club its desk signed up, its point dropped where it was."""

    club = Club.register(
        club_id=new_uuid(),
        details=ClubDetails(
            name=ClubName("Ogrody 33"),
            district=District("Grzegórzki"),
            city=City("Kraków"),
            sports=OfferedSports.of({Sport.PADEL}),
            point=MapPoint(latitude=latitude, longitude=longitude),
        ),
        occurred_at=datetime.now(timezone.utc),
    )
    await build_club_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(club)
    await session.commit()
    return club.id


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_demand_has_at_least_one_implementation():
    assert [
        p.__name__ for p in PLAYER_PROFILE_DEMANDS if not implementations_of(p)
    ] == []


def test_every_registered_implementation_is_of_a_demand():
    assert all(
        one.port in PLAYER_PROFILE_DEMANDS for one in PLAYER_PROFILE_IMPLEMENTATIONS
    )


# --------------------------------------------------------------------------- #
# ClubPoints — where a club is
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubPoints))
async def test_a_club_s_point_is_the_one_its_desk_dropped(implementation, session):
    points: ClubPoints = implementation.build(session)
    ogrody = await _a_club(session, latitude=50.0612, longitude=19.9367)

    assert await points.point_of(ogrody) == ClubPoint(
        latitude=50.0612, longitude=19.9367
    )


@pytest.mark.parametrize("implementation", registered(ClubPoints))
async def test_an_id_that_names_no_club_has_no_point(implementation, session):
    points: ClubPoints = implementation.build(session)
    await _a_club(session, latitude=50.0612, longitude=19.9367)

    assert await points.point_of(new_uuid()) is None

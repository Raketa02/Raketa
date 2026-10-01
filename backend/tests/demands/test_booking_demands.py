"""What ``bookings`` demands of the rest of the platform (#543), run against
every registered implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/booking_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or
turns the build red. **Each club is built the way a desk builds it**, through
the club website's routes.
"""

from __future__ import annotations

from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.booking_demands import (
    BOOKING_DEMANDS,
    BOOKING_IMPLEMENTATIONS,
    implementations_of,
)
from app.kernel import Sport
from app.modules.bookings.domain.ports import (
    ClubCourtsAtTheHour,
    ClubDesk,
    ClubDesks,
)
from app.shared.ids import new_uuid
from tests.api.administration_world import club_signs_up
from tests.api.proposals_world import SATURDAY_FIVE, a_club_and_its_desk


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_declared_demand_has_at_least_one_implementation():
    unregistered = [
        port.__name__ for port in BOOKING_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_answers_a_declared_demand():
    declared = set(BOOKING_DEMANDS)

    assert all(one.port in declared for one in BOOKING_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# ClubCourtsAtTheHour — the first free court, its cut-off and time to confirm
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubCourtsAtTheHour))
async def test_the_first_free_court_comes_with_the_club_s_terms(
    implementation, client, session
):
    club_id, _ = await a_club_and_its_desk(
        client, way="ON_REQUEST", time_to_confirm_minutes=20
    )
    courts: ClubCourtsAtTheHour = implementation.build(session)

    found = await courts.first_free(
        UUID(club_id), sport=Sport.PADEL, start=SATURDAY_FIVE
    )

    assert found is not None
    assert found.court.name == "Court 1"
    assert (found.cut_off_hours, found.time_to_confirm_minutes) == (24, 20)
    assert (
        await courts.first_free(UUID(club_id), sport=Sport.SQUASH, start=SATURDAY_FIVE)
        is None
    )


# --------------------------------------------------------------------------- #
# ClubDesks — whom an email to a club goes to
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubDesks))
async def test_a_club_s_desk_is_its_one_sign_in_and_its_name(
    implementation, client, session
):
    club_id, _ = await club_signs_up(client, name="Ogrody 33", email="desk@ogrody.pl")
    desks: ClubDesks = implementation.build(session)

    assert await desks.of(UUID(club_id)) == ClubDesk(
        email="desk@ogrody.pl", club_name="Ogrody 33"
    )
    assert await desks.of(new_uuid()) is None

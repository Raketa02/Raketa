"""What ``conversations`` demands of the rest of the platform, run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/conversation_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red. There is no skipped test to go stale.

**The membership record is contracted here rather than only unit-tested**, and
that is deliberate. *Who is in a room* and *which rooms are mine* are claims
about ``games``' aggregate — a room is opened only by a booked game (#575) — and
a stub that agreed with the rule would prove nothing about whether ``games``
actually answers that way.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.bootstrap.conversation_demands import (
    CONVERSATION_DEMANDS,
    CONVERSATION_IMPLEMENTATIONS,
    implementations_of,
)
from app.kernel import Instant, Sport, instant
from app.modules.conversations.domain.ports import (
    AccountHoldQuery,
    MemberFaces,
    PlayedCourt,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest.fixture
def games(session):
    """One repository for the whole test, because it remembers stream versions."""

    return build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _at(hours: int = 0) -> Instant:
    return instant(
        datetime(2026, 9, 1, 12, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


def _a_booked_game(booking: UUID, four: tuple[UUID, ...]) -> Game:
    """The game a booking opens: filed under the booking, with its hour."""

    return Game.planned(
        game_id=new_uuid(),
        challenge_id=booking,
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=four[0]),
                Seating(side=GameSide.A, player_id=four[1]),
                Seating(side=GameSide.B, player_id=four[2]),
                Seating(side=GameSide.B, player_id=four[3]),
            )
        ),
        occurred_at=_at(),
        starts_at=_at(48),
    )


async def _saved(games, session, game: Game) -> Game:
    await games.save(game)
    await session.commit()
    return game


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


def test_every_declared_demand_has_at_least_one_implementation():
    """**A port with nothing registered is a red build**, because one added in a
    hurry would otherwise look contracted while nothing ran against it."""

    unregistered = [
        port.__name__ for port in CONVERSATION_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_answers_a_declared_demand():
    """The other direction: a row for a port this context does not declare is a
    row in the wrong register."""

    declared = set(CONVERSATION_DEMANDS)

    assert all(one.port in declared for one in CONVERSATION_IMPLEMENTATIONS)


# ---------------------------------------------------------------------------
# PlayedCourt — the booked game's current line-up
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlayedCourt))
async def test_the_line_up_is_everybody_on_the_court(implementation, session, games):
    four = tuple(new_uuid() for _ in range(4))
    game = await _saved(games, session, _a_booked_game(new_uuid(), four))
    court: PlayedCourt = implementation.build(session)

    found = await court.line_ups_of((game.game_id,))

    assert found[game.game_id] == frozenset(four)


@pytest.mark.parametrize("implementation", registered(PlayedCourt))
async def test_a_game_it_cannot_answer_about_is_absent_rather_than_empty(
    implementation, session
):
    """An empty court would let anybody read the room; absence drops it."""

    court: PlayedCourt = implementation.build(session)

    assert await court.line_ups_of((new_uuid(),)) == {}


@pytest.mark.parametrize("implementation", registered(PlayedCourt))
async def test_a_player_finds_the_booking_of_every_game_they_are_on(
    implementation, session, games
):
    """A booked game's room is filed under its booking, which nobody accepted a
    seat on — so the game is the only way back to it (#542)."""

    four = tuple(new_uuid() for _ in range(4))
    other_four = (four[2], *(new_uuid() for _ in range(3)))
    booking, other_booking = new_uuid(), new_uuid()
    await _saved(games, session, _a_booked_game(booking, four))
    await _saved(games, session, _a_booked_game(other_booking, other_four))
    court: PlayedCourt = implementation.build(session)

    assert await court.bookings_played_by(four[0]) == frozenset({booking})
    assert await court.bookings_played_by(four[2]) == frozenset(
        {booking, other_booking}
    )
    assert await court.bookings_played_by(new_uuid()) == frozenset()


# ---------------------------------------------------------------------------
# MemberFaces — a handle and a face, and nothing else
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(MemberFaces))
async def test_a_player_users_cannot_name_keeps_their_membership(
    implementation, session
):
    """The opposite of a shortlist, which drops a row it cannot name: dropping a
    member would draw a three-person doubles court."""

    stranger = new_uuid()
    faces: MemberFaces = implementation.build(session)

    found = await faces.faces_of((stranger,))

    assert found[stranger].nickname is None
    assert found[stranger].photo_id is None
    assert found[stranger].photo_url is None


@pytest.mark.parametrize("implementation", registered(MemberFaces))
async def test_asking_about_nobody_costs_nothing(implementation, session):
    faces: MemberFaces = implementation.build(session)

    assert await faces.faces_of(()) == {}


# ---------------------------------------------------------------------------
# AccountHoldQuery — measured emptiness, not a stub
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(AccountHoldQuery))
async def test_nobody_is_held_because_nothing_can_hold_anybody(implementation, session):
    """``cases`` does not exist: there is no route, no aggregate and no table
    through which a hold could be taken, so this zero is real."""

    holds: AccountHoldQuery = implementation.build(session)

    assert await holds.held_among((new_uuid(), new_uuid())) == frozenset()

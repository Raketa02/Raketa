"""What ``conversations`` demands of the rest of the platform, run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/conversation_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red. There is no skipped test to go stale.

**The two membership records are contracted here rather than only unit-tested**,
and that is deliberate. *One rule read against two records* is a claim about two
other contexts' aggregates, and a stub that agreed with the rule would prove
nothing about whether ``challenges`` and ``games`` actually answer that way.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.bootstrap.conversation_demands import (
    CONVERSATION_DEMANDS,
    CONVERSATION_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.conversations.domain.ports import (
    AccountHoldQuery,
    ArrangingCourt,
    MemberFaces,
    PlayedCourt,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.player_profile.domain.weekly_hours import Window
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest.fixture
def challenges(session):
    """One repository for the whole test, because it remembers stream versions.

    A second one built for a second save would expect version 0 of a stream it
    has never seen — which is the rule the composition root states about every
    aggregate repository here, met from the other side.
    """

    return build_challenge_repository(
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


def _a_padel_challenge(organiser: UUID, invitees: tuple[UUID, ...]) -> Challenge:
    search = new_uuid()
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        mode=SearchMode.FOR_FUN,
        window=Window.WEEKEND,
        organiser_id=organiser,
        arrangement=(
            SeatPlan(side=Side.A, player_id=organiser),
            SeatPlan(
                side=Side.A,
                player_id=invitees[0],
                origin=SentFromSearch(search_id=search, position=1),
            ),
            SeatPlan(
                side=Side.B,
                player_id=invitees[1],
                origin=SentFromSearch(search_id=search, position=2),
            ),
            SeatPlan(
                side=Side.B,
                player_id=invitees[2],
                origin=SentFromSearch(search_id=search, position=3),
            ),
        ),
        occurred_at=_at(),
    )


async def _saved(challenges, session, challenge: Challenge) -> Challenge:
    await challenges.save(challenge)
    await session.commit()
    return challenge


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
# ArrangingCourt — the challenge's accepted seats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_the_court_is_who_has_accepted_and_never_who_was_asked(
    implementation, session, challenges
):
    """``docs/adr/0146`` §7 — *the people who have agreed to be on this court
    right now*, which is what grows one acceptance at a time."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = await _saved(
        challenges, session, _a_padel_challenge(organiser, (ana, bo, cy))
    )
    court: ArrangingCourt = implementation.build(session)

    before = await court.accepted_on((challenge.challenge_id,))
    challenge.accept(ana, occurred_at=_at(1))
    await _saved(challenges, session, challenge)
    after = await court.accepted_on((challenge.challenge_id,))

    assert before[challenge.challenge_id] == frozenset({organiser})
    assert after[challenge.challenge_id] == frozenset({organiser, ana})


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_declined_seat_is_not_on_the_court(implementation, session, challenges):
    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = _a_padel_challenge(organiser, (ana, bo, cy))
    challenge.decline(ana, occurred_at=_at(1))
    await _saved(challenges, session, challenge)
    court: ArrangingCourt = implementation.build(session)

    found = await court.accepted_on((challenge.challenge_id,))

    assert ana not in found[challenge.challenge_id]


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_player_finds_every_challenge_they_accepted_a_seat_on(
    implementation, session, challenges
):
    """The list read's *find*, and it is a fact about seats rather than about a
    standing — whether each room found is over is ``over_among``'s question,
    asked beside it and never folded into it."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = _a_padel_challenge(organiser, (ana, bo, cy))
    challenge.accept(ana, occurred_at=_at(1))
    await _saved(challenges, session, challenge)
    court: ArrangingCourt = implementation.build(session)

    assert await court.accepted_by(ana) == frozenset({challenge.challenge_id})
    assert await court.accepted_by(organiser) == frozenset({challenge.challenge_id})
    assert await court.accepted_by(bo) == frozenset()


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_the_sport_is_the_one_fact_a_room_borrows(
    implementation, session, challenges
):
    """A room is opened by a *seat's acceptance*, which names a challenge and a
    player and nothing else."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = await _saved(
        challenges, session, _a_padel_challenge(organiser, (ana, bo, cy))
    )
    court: ArrangingCourt = implementation.build(session)

    assert await court.sport_of(challenge.challenge_id) is Sport.PADEL
    assert await court.sport_of(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_challenge_it_cannot_answer_about_is_absent_rather_than_empty(
    implementation, session, challenges
):
    """An empty court would let anybody read the room; absence drops it."""

    court: ArrangingCourt = implementation.build(session)

    assert await court.accepted_on((new_uuid(),)) == {}


# ---------------------------------------------------------------------------
# ArrangingCourt — whether the challenge is over
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_court_somebody_accepted_stands_whoever_else_said_no(
    implementation, session, challenges
):
    """``docs/adr/0164`` §6 — a room without a game lives as long as its
    challenge, and a challenge with somebody other than the organiser still in
    it is not over: two *no*s around one *yes* leave a half-built court, not an
    ended one."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = _a_padel_challenge(organiser, (ana, bo, cy))
    challenge.accept(ana, occurred_at=_at(1))
    challenge.decline(bo, occurred_at=_at(2))
    challenge.decline(cy, occurred_at=_at(3))
    await _saved(challenges, session, challenge)
    court: ArrangingCourt = implementation.build(session)

    over = await court.over_among((challenge.challenge_id,), now=_at(30 * 24))

    assert over == frozenset()


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_court_everybody_declined_is_over(implementation, session, challenges):
    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = _a_padel_challenge(organiser, (ana, bo, cy))
    for who, hour in ((ana, 1), (bo, 2), (cy, 3)):
        challenge.decline(who, occurred_at=_at(hour))
    await _saved(challenges, session, challenge)
    court: ArrangingCourt = implementation.build(session)

    assert await court.over_among((challenge.challenge_id,), now=_at(4)) == {
        challenge.challenge_id
    }


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_court_whose_windows_all_passed_is_over_before_any_sweep(
    implementation, session, challenges
):
    """A lapse is a deadline passing and is true whether or not the lapse loop
    has recorded it — which is why ``now`` travels with the question."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = await _saved(
        challenges, session, _a_padel_challenge(organiser, (ana, bo, cy))
    )
    court: ArrangingCourt = implementation.build(session)

    still_asked = await court.over_among((challenge.challenge_id,), now=_at(1))
    lapsed = await court.over_among(
        (challenge.challenge_id,),
        now=_at(int(ANSWER_WINDOW.total_seconds() // 3600) + 1),
    )

    assert still_asked == frozenset()
    assert lapsed == {challenge.challenge_id}


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_withdrawn_court_is_over(implementation, session, challenges):
    """The organiser alone again — the one who joined left, the others still
    deciding — removes the court (``docs/adr/0165`` §4): a room existed, and it
    is over with its challenge."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = _a_padel_challenge(organiser, (ana, bo, cy))
    challenge.accept(ana, occurred_at=_at(1))
    challenge.leave(ana, occurred_at=_at(2))
    challenge.withdraw(organiser, occurred_at=_at(3))
    await _saved(challenges, session, challenge)
    court: ArrangingCourt = implementation.build(session)

    assert await court.over_among((challenge.challenge_id,), now=_at(5)) == {
        challenge.challenge_id
    }


@pytest.mark.parametrize("implementation", registered(ArrangingCourt))
async def test_a_whole_list_answers_the_ones_that_are_over_and_omits_the_unknown(
    implementation, session, challenges
):
    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    standing = _a_padel_challenge(organiser, (ana, bo, cy))
    standing.accept(ana, occurred_at=_at(1))
    await _saved(challenges, session, standing)
    others = (new_uuid(), new_uuid(), new_uuid())
    over = _a_padel_challenge(new_uuid(), others)
    for hour, who in enumerate(others, start=1):
        over.decline(who, occurred_at=_at(hour))
    await _saved(challenges, session, over)
    court: ArrangingCourt = implementation.build(session)

    found = await court.over_among(
        (standing.challenge_id, over.challenge_id, new_uuid()), now=_at(4)
    )

    assert found == {over.challenge_id}


# ---------------------------------------------------------------------------
# PlayedCourt — the game's frozen line-up
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlayedCourt))
async def test_the_line_up_is_everybody_who_was_on_the_court(
    implementation, session, challenges
):
    four = tuple(new_uuid() for _ in range(4))
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=four[0]),
                Seating(side=GameSide.A, player_id=four[1]),
                Seating(side=GameSide.B, player_id=four[2]),
                Seating(side=GameSide.B, player_id=four[3]),
            )
        ),
        occurred_at=_at(),
    )
    repository = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    await repository.save(game)
    await session.commit()
    court: PlayedCourt = implementation.build(session)

    found = await court.line_ups_of((game.game_id,))

    assert found[game.game_id] == frozenset(four)


@pytest.mark.parametrize("implementation", registered(PlayedCourt))
async def test_a_game_it_cannot_answer_about_is_absent_rather_than_empty(
    implementation, session, challenges
):
    court: PlayedCourt = implementation.build(session)

    assert await court.line_ups_of((new_uuid(),)) == {}


@pytest.mark.parametrize("implementation", registered(PlayedCourt))
async def test_a_player_finds_the_challenge_of_every_game_they_are_on(
    implementation, session, challenges
):
    """A booked game's room is filed under its booking, which nobody accepted a
    seat on — so the game is the only way back to it (#542)."""

    four = tuple(new_uuid() for _ in range(4))
    booking = new_uuid()
    game = Game.planned(
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
    repository = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    await repository.save(game)
    await session.commit()
    court: PlayedCourt = implementation.build(session)

    assert await court.challenges_played_by(four[2]) == frozenset({booking})
    assert await court.challenges_played_by(new_uuid()) == frozenset()


# ---------------------------------------------------------------------------
# MemberFaces — a handle and a face, and nothing else
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(MemberFaces))
async def test_a_player_users_cannot_name_keeps_their_membership(
    implementation, session, challenges
):
    """The opposite of a shortlist, which drops a row it cannot name: dropping a
    member would draw a three-person doubles court."""

    stranger = new_uuid()
    faces: MemberFaces = implementation.build(session)

    found = await faces.faces_of((stranger,))

    assert found[stranger].name is None
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
async def test_nobody_is_held_because_nothing_can_hold_anybody(
    implementation, session, challenges
):
    """``cases`` does not exist: there is no route, no aggregate and no table
    through which a hold could be taken, so this zero is real."""

    holds: AccountHoldQuery = implementation.build(session)

    assert await holds.held_among((new_uuid(), new_uuid())) == frozenset()

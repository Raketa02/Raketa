"""What ``plans`` demands of the rest of the platform, run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/plan_demands.py`` is enrolled
here automatically, so a second one either satisfies the demand or turns the
build red. There is no skipped test to go stale.

**Two ports.** ``PlannableCourts`` is the read that decides who may write a
plan — *which courts is this player arranging, and which are history* — and it
is contracted here rather than only unit-tested, on ``conversation_demands``'
argument: it is a claim about two other contexts' aggregates, and a stub that
agreed with the rule would prove nothing about whether ``challenges`` and
``games`` actually answer that way (``docs/adr/0164`` §3). The five answers of
the fold are pinned one by one in ``tests/unit/test_plannable_courts_fold.py``;
what is asserted here is that the registered adapter reaches them through the
providers' real stores. ``AccountHoldQuery`` is the fourth spelling of an empty
answer: the one fact this context reads about a *person*, whose provider does
not exist. The demand made of it is therefore about the shape of an honest empty
answer rather than about a hold — because nobody can be held while nothing on
this platform can hold anybody, and a test that pretended otherwise would be
testing a stub.

**The held arm of the three slot writes is unreachable by ``make seed`` and that
is stated rather than discovered** — here, and in the null object itself. It is
an honest, named exception rather than an oversight.
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
from app.bootstrap.plan_demands import (
    PLAN_DEMANDS,
    PLAN_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.windows import entry_closes_at
from app.modules.plans.domain.ports import AccountHoldQuery, PlannableCourts
from app.modules.player_profile.domain.weekly_hours import Window
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest.fixture
def challenges(session):
    """One repository for the whole test, because it remembers stream versions."""

    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


@pytest.fixture
def games(session):
    return build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _at(hours: int = 0) -> Instant:
    return instant(
        datetime(2026, 9, 7, 10, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


def _a_padel_four(organiser: UUID, invitees: tuple[UUID, UUID, UUID]) -> Challenge:
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


def _the_game_of(
    challenge: Challenge, four: tuple[UUID, UUID, UUID, UUID], *, at: Instant
) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=challenge.challenge_id,
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=Window.WEEKEND,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=four[0]),
                Seating(side=GameSide.A, player_id=four[1]),
                Seating(side=GameSide.B, player_id=four[2]),
                Seating(side=GameSide.B, player_id=four[3]),
            )
        ),
        occurred_at=at,
    )


async def _saved(repository, session, aggregate):
    await repository.save(aggregate)
    await session.commit()
    return aggregate


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


def test_every_declared_demand_has_at_least_one_implementation():
    """**A port with nothing registered is a red build**, because one added in a
    hurry would otherwise look contracted while nothing ran against it."""

    unregistered = [
        port.__name__ for port in PLAN_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_answers_a_declared_demand():
    """The other direction: a row for a port this context does not declare is a
    row in the wrong register."""

    declared = set(PLAN_DEMANDS)

    assert all(one.port in declared for one in PLAN_IMPLEMENTATIONS)


def test_the_plan_publishes_nothing_and_therefore_has_no_provider_register():
    """``docs/adr/0145`` §4 — nothing on this side of the wire reads a plan.

    ``games`` may not import it, ``conversations`` is told through the outbox and
    asks this context nothing, and the ladder that reads a plan is the client's.
    A context with no consumers publishes no port, so there is no
    ``plan_provider_demands.py`` to add a row to and there never will be.
    """

    with pytest.raises(ModuleNotFoundError):
        __import__("app.bootstrap.plan_provider_demands")


# ---------------------------------------------------------------------------
# PlannableCourts — which courts is this player arranging, and which are history
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlannableCourts))
async def test_the_first_yes_makes_the_court_plannable_on_the_send(
    implementation, session, challenges
):
    """``docs/adr/0164`` §3–§4 — the organiser and the accepter each get the
    court, open and **not whole**, anchored at the send; the two still deciding
    and a stranger get nothing."""

    organiser, ana, bo, cy, stranger = (new_uuid() for _ in range(5))
    challenge = _a_padel_four(organiser, (ana, bo, cy))
    challenge.accept(ana, occurred_at=_at(1))
    await _saved(challenges, session, challenge)
    courts: PlannableCourts = implementation.build(session)

    for who in (organiser, ana):
        found = await courts.plannable_for(who, now=_at(2))
        assert set(found) == {challenge.challenge_id}
        assert found[challenge.challenge_id].anchor == challenge.opened_at
        assert found[challenge.challenge_id].open_to_planning is True
        assert found[challenge.challenge_id].whole is False
    for who in (bo, cy, stranger):
        assert await courts.plannable_for(who, now=_at(2)) == {}


@pytest.mark.parametrize("implementation", registered(PlannableCourts))
async def test_a_court_nobody_has_said_yes_to_is_listed_for_nobody(
    implementation, session, challenges
):
    """``docs/adr/0164`` §2 — a plan exists from the **first yes**, because the
    room it is drawn in opens on that yes; the organiser's seat being accepted
    from birth makes no court on its own."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = await _saved(
        challenges, session, _a_padel_four(organiser, (ana, bo, cy))
    )
    courts: PlannableCourts = implementation.build(session)

    assert await courts.plannable_for(organiser, now=_at(1)) == {}
    assert challenge.standing_at(_at(1)).value == "AWAITING_ANSWERS"


@pytest.mark.parametrize("implementation", registered(PlannableCourts))
async def test_a_whole_court_is_anchored_on_its_game_and_reads_the_games_standing(
    implementation, session, challenges, games
):
    """Once the court has become a game the anchor is ``planned_at``, the court
    is whole, and it is the **game's** entry window that decides whether the
    slots may still move."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = _a_padel_four(organiser, (ana, bo, cy))
    for who in (ana, bo, cy):
        challenge.accept(who, occurred_at=_at(1))
    await _saved(challenges, session, challenge)
    game = await _saved(
        games, session, _the_game_of(challenge, (organiser, ana, bo, cy), at=_at(1))
    )
    courts: PlannableCourts = implementation.build(session)

    open_court = (await courts.plannable_for(ana, now=_at(2)))[challenge.challenge_id]
    assert open_court.anchor == game.planned_at
    assert open_court.whole is True
    assert open_court.open_to_planning is True

    later = instant(entry_closes_at(game.planned_at) + timedelta(minutes=1))
    history = (await courts.plannable_for(ana, now=later))[challenge.challenge_id]
    assert history.open_to_planning is False
    assert history.anchor == game.planned_at


@pytest.mark.parametrize("implementation", registered(PlannableCourts))
async def test_a_court_that_ended_after_a_yes_is_history_and_still_listed(
    implementation, session, challenges
):
    """The plan is drawn beside whatever the court became, so a court that had
    a room and ended is a row that is no longer open rather than an absence —
    while a send nobody said yes to never had a room and is listed for nobody.

    The ending is the organiser leaving: B said yes, the other two said no, and
    B alone with nobody deciding is over (``docs/adr/0165`` §3) — a court
    somebody has joined is nobody's to withdraw. So the row is B's, who is still
    on it, and the organiser who left has none.
    """

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    ended = _a_padel_four(organiser, (ana, bo, cy))
    ended.accept(ana, occurred_at=_at(1))
    for who in (bo, cy):
        ended.decline(who, occurred_at=_at(2))
    ended.leave(organiser, occurred_at=_at(3))
    assert ended.standing_at(_at(4)) is Standing.DECLINED
    await _saved(challenges, session, ended)
    nobody_came = _a_padel_four(organiser, (ana, bo, cy))
    for who in (ana, bo, cy):
        nobody_came.decline(who, occurred_at=_at(1))
    await _saved(challenges, session, nobody_came)
    courts: PlannableCourts = implementation.build(session)

    found = await courts.plannable_for(ana, now=_at(4))

    assert set(found) == {ended.challenge_id}
    assert found[ended.challenge_id].open_to_planning is False
    assert found[ended.challenge_id].whole is False
    assert await courts.plannable_for(organiser, now=_at(4)) == {}


@pytest.mark.parametrize("implementation", registered(PlannableCourts))
async def test_somebody_who_left_is_absent_and_the_court_is_no_longer_whole(
    implementation, session, challenges, games
):
    """``docs/adr/0162``, ``docs/adr/0164`` §5 — the leaver has nothing to plan;
    the others keep an open court that will not admit a lock until re-seated."""

    organiser, ana, bo, cy = (new_uuid() for _ in range(4))
    challenge = _a_padel_four(organiser, (ana, bo, cy))
    for who in (ana, bo, cy):
        challenge.accept(who, occurred_at=_at(1))
    game = _the_game_of(challenge, (organiser, ana, bo, cy), at=_at(1))
    challenge.leave(cy, occurred_at=_at(2))
    game.vacate(cy, occurred_at=_at(2))
    await _saved(challenges, session, challenge)
    await _saved(games, session, game)
    courts: PlannableCourts = implementation.build(session)

    assert await courts.plannable_for(cy, now=_at(3)) == {}
    still_on = (await courts.plannable_for(bo, now=_at(3)))[challenge.challenge_id]
    assert still_on.open_to_planning is True
    assert still_on.whole is False
    assert still_on.anchor == game.planned_at


@pytest.mark.parametrize("implementation", registered(PlannableCourts))
async def test_a_player_on_no_court_is_answered_about_nothing(implementation, session):
    courts: PlannableCourts = implementation.build(session)

    assert await courts.plannable_for(new_uuid(), now=_at()) == {}


# ---------------------------------------------------------------------------
# AccountHoldQuery — an empty answer that is measured rather than stubbed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(AccountHoldQuery))
async def test_nobody_is_held_because_nothing_can_hold_anybody(implementation, session):
    """Not a stub standing in for a provider — the correct answer.

    There is no case, no route and no record anywhere that can put an account
    under a hold, so *nobody* is what this measures. On the day ``cases`` ships,
    this row changes to the same adapter the other three spellings change to.
    """

    port: AccountHoldQuery = implementation.build(session)
    somebody, somebody_else = new_uuid(), new_uuid()

    assert await port.held_among((somebody, somebody_else)) == frozenset()


@pytest.mark.parametrize("implementation", registered(AccountHoldQuery))
async def test_asking_about_nobody_answers_about_nobody(implementation, session):
    """The empty ask, which the write path never makes and a caller may.

    It is here because the answer to *which of these* over an empty list is the
    empty set and never an error — the shape every set read in this codebase
    promises.
    """

    port: AccountHoldQuery = implementation.build(session)

    assert await port.held_among(()) == frozenset()

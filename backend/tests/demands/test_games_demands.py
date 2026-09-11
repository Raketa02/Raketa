"""What ``games`` owes the rest of the platform, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/games_demands.py`` is enrolled
here automatically, so a second one either satisfies the demand or turns the
build red. There is no skipped test to go stale.

**The three ends of a game are demanded here rather than only unit-tested**, and
that is deliberate. *Counted with a confirmed result*, *counted and unscored* and
*never played* are the three facts three other tickets are waiting on, and each
is reached **through the aggregate's own API** and then read back **through the
port** — because a state the aggregate can reach and the read cannot publish is
a state that does not exist as far as anybody else is concerned.

**Silence confirming is proved by advancing a clock and never by a method.**
There is nothing in this context called ``confirm``: a lone score is agreed when
its window closes, and the only way to write that test is to ask the same record
at two instants.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import get_type_hints
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.bootstrap.games_demands import (
    GAMES_DEMANDS,
    GAME_IMPLEMENTATIONS,
    implementations_of,
)
from app.kernel import Instant, Sport, instant
from app.modules.games.domain.errors import (
    AResultMustCarryAScore,
    AScoreMustNameAWinner,
    TheEntryWindowHasClosed,
    TheResultIsSettled,
    YouWereNotOnThisCourt,
    YourSideHasAlreadyAnswered,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, LineUp, Seating, GameSide
from app.modules.games.domain.ports import (
    RECENT_RESULTS,
    ConfirmedResultLedger,
    GameDirectory,
    GameHistoryQuery,
    OpponentVariety,
    OpponentVarietyQuery,
    PlanningCourt,
    PlayedOutcome,
)
from app.modules.games.domain.results import Outcome, Score, SetScore
from app.modules.games.domain.standing import GameStanding
from app.modules.player_profile.domain.availability import Window
from app.modules.games.domain.windows import (
    ACCEPTANCE_GRACE,
    ENTRY_GRACE,
    PLAN_HORIZON,
    PROPOSAL_WINDOW,
)
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def every_row():
    """Every row in the register, whichever port it signs.

    Named apart from ``registered`` because the two answer different questions:
    that one is *run this demand against each signatory*, and this is *walk the
    whole register* — which is what a structural check about the register itself
    wants, now that one class here answers three contracts.
    """

    return [
        pytest.param(one, id=f"{one.port.__name__}:{one.name}")
        for one in GAME_IMPLEMENTATIONS
    ]


# ---------------------------------------------------------------------------
# The world these demands are run against
# ---------------------------------------------------------------------------


def _ago(**offset) -> Instant:
    """A moment that far behind the clock these demands read ``now`` from."""

    return instant(datetime.now(timezone.utc) - timedelta(**offset))


def _score(*sets: tuple[int, int]) -> Score:
    return Score.of(SetScore(a=a, b=b) for a, b in sets)


def _repository(session):
    return build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _singles(a: UUID, b: UUID) -> LineUp:
    return LineUp.of(
        (Seating(side=GameSide.A, player_id=a), Seating(side=GameSide.B, player_id=b))
    )


def _four(a: UUID, b: UUID, c: UUID, d: UUID) -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=a),
            Seating(side=GameSide.A, player_id=b),
            Seating(side=GameSide.B, player_id=c),
            Seating(side=GameSide.B, player_id=d),
        )
    )


def _planned(
    *,
    line_up: LineUp,
    at: Instant,
    kind: GameKind = GameKind.COUNTED,
    sport: Sport = Sport.TENNIS,
) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=sport,
        kind=kind,
        window=Window.TODAY,
        line_up=line_up,
        occurred_at=at,
    )


async def _saved(session, game: Game) -> Game:
    await _repository(session).save(game)
    await session.commit()
    return game


# ---------------------------------------------------------------------------
# The three ends, each reached through the aggregate and read back through the
# port
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_counted_game_with_a_confirmed_result_counts_and_has_an_outcome(
    implementation, session
):
    """The end everything else in this batch is waiting on.

    Somebody entered a score, nobody disagreed, its day passed: the game counts,
    it has a winner, and both facts are readable about both people.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    winner, loser = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(winner, loser), at=_ago(days=3))
    game.state_result(by=winner, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2))
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.CONFIRMED

    counts = await port.counted_games_for([winner, loser], now=now)
    results = await port.recent_results_for([winner, loser], now=now)

    assert counts == {winner: 1, loser: 1}
    assert [one.outcome for one in results[winner]] == [Outcome.WIN]
    assert [one.outcome for one in results[loser]] == [Outcome.LOSS]


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_counted_game_nobody_agreed_is_an_evening_and_never_evidence(
    implementation, session
):
    """Two scores, nobody accepted either, both days gone.

    ``docs/adr/0049``: it counts toward how much these people have played and it
    **moves nobody's Level**. So it is in ``counted_games`` and it is not in the
    results — and neither of those is a special case anywhere, they fall out of
    *played* and *confirmed* being two different questions.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(one, other), at=_ago(days=3))
    game.state_result(by=one, score=_score((6, 4),), occurred_at=_ago(days=2))
    game.state_result(by=other, score=_score((4, 6),), occurred_at=_ago(days=2))
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.UNSCORED

    counts = await port.counted_games_for([one, other], now=now)
    results = await port.recent_results_for([one, other], now=now)

    assert counts == {one: 1, other: 1}
    assert results == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_plan_nobody_claimed_becomes_a_ghost_and_never_a_played_game(
    implementation, session
):
    """The end that only exists because a game is opened by a **plan**.

    Nobody ever said it happened, the entry window closed, and the pair now
    carries ``PLANNED_NEVER_PLAYED`` — kept apart from ``PLAYED`` because
    familiarity must be able to tell a ghost from a game.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(one, other),
        at=instant(now - PLAN_HORIZON - ENTRY_GRACE - timedelta(hours=1)),
    )
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.NEVER_PLAYED

    counterparts = await port.played_counterparts(one, now=now)
    counts = await port.counted_games_for([one, other], now=now)

    assert [one.player_id for one in counterparts] == [other]
    assert set(counterparts[0].outcomes) == {PlayedOutcome.PLANNED_NEVER_PLAYED}
    assert counterparts[0].games_played_together == 0
    assert counts == {one: 0, other: 0}


# ---------------------------------------------------------------------------
# Silence, and the clock that is the whole of it
# ---------------------------------------------------------------------------


async def test_silence_confirms_a_lone_score_when_its_window_closes():
    """**Proved by advancing a clock, and there is no method to call.**

    Nothing in this context is named ``confirm``. The same record, asked at two
    instants, answers *awaiting an answer* and then *confirmed* — which is what
    ``docs/adr/0048``'s *silence confirms* means when it is executable rather
    than described.
    """

    winner, loser = new_uuid(), new_uuid()
    entered = _ago(days=1)
    game = _planned(line_up=_singles(winner, loser), at=_ago(days=2))
    game.state_result(by=winner, score=_score((6, 1),), occurred_at=entered)

    a_moment_later = instant(entered + timedelta(minutes=1))
    a_day_later = instant(entered + PROPOSAL_WINDOW)

    assert game.standing_at(a_moment_later) is GameStanding.AWAITING_ANSWER
    assert game.confirmed_score_at(a_moment_later) is None
    assert game.standing_at(a_day_later) is GameStanding.CONFIRMED
    assert game.outcome_for(winner, now=a_day_later) is Outcome.WIN


async def test_an_acceptance_settles_nothing_until_its_grace_has_passed():
    """The opponent still in the shower.

    One opponent's yes is enough, and it does not close the door on the other
    one: inside the grace a disagreement still wins, and the grace runs from the
    **score** rather than from the tap.
    """

    a_one, a_two = new_uuid(), new_uuid()
    b_one, b_two = new_uuid(), new_uuid()
    line_up = LineUp.of(
        (
            Seating(side=GameSide.A, player_id=a_one),
            Seating(side=GameSide.A, player_id=a_two),
            Seating(side=GameSide.B, player_id=b_one),
            Seating(side=GameSide.B, player_id=b_two),
        )
    )
    entered = _ago(days=1)
    game = _planned(line_up=line_up, at=_ago(days=2), sport=Sport.PADEL)
    game.state_result(by=a_one, score=_score((6, 4),), occurred_at=entered)
    game.accept_result(by=b_one, occurred_at=instant(entered + timedelta(minutes=2)))

    inside = instant(entered + timedelta(minutes=3))
    assert game.standing_at(inside) is GameStanding.AWAITING_ANSWER

    game.state_result(by=b_two, score=_score((4, 6),), occurred_at=inside)
    assert game.standing_at(instant(entered + ACCEPTANCE_GRACE)) is (
        GameStanding.AWAITING_ANSWER
    )


# ---------------------------------------------------------------------------
# What the aggregate refuses
# ---------------------------------------------------------------------------


async def test_a_counter_with_no_score_is_refused_at_the_aggregate():
    """**There is no bare rejection**, and the refusal is the aggregate's.

    The signature admits ``None`` deliberately, so the rule is enforced where it
    is true rather than by a type checker an untyped caller never runs.
    """

    one, other = new_uuid(), new_uuid()
    game = _planned(line_up=_singles(one, other), at=_ago(days=1))
    game.state_result(by=one, score=_score((6, 4),), occurred_at=_ago(hours=2))

    with pytest.raises(AResultMustCarryAScore):
        game.state_result(by=other, score=None, occurred_at=_ago(hours=1))


async def test_an_empty_score_is_not_a_score():
    """The second half of the same rule, one layer down.

    A score with no sets in it cannot be constructed, so an objection carrying
    nothing has nowhere to come from — the refusal above is what a caller sending
    ``null`` meets, and this is what a caller sending ``{"sets": []}`` meets.
    """

    with pytest.raises(AResultMustCarryAScore):
        Score.of(())


async def test_a_score_that_names_no_winner_is_refused():
    """*Last 5* is win or loss, and none of the four sports produces a draw.

    A **refusal** and not an assertion: a score arrives from a person typing it,
    so a level one is somebody's mistake with a code they can act on rather than
    a broken precondition answered with a 500.
    """

    with pytest.raises(AScoreMustNameAWinner):
        _score((6, 4), (4, 6))


async def test_each_side_answers_once():
    """The cap is what bounds an argument to two rounds.

    With a third turn available, going quiet stops being the last word and starts
    being a tactic — which is the thing *silence confirms* cannot survive.
    """

    one, other = new_uuid(), new_uuid()
    game = _planned(line_up=_singles(one, other), at=_ago(hours=6))
    game.state_result(by=one, score=_score((6, 4),), occurred_at=_ago(hours=5))
    game.state_result(by=other, score=_score((4, 6),), occurred_at=_ago(hours=4))

    with pytest.raises(YourSideHasAlreadyAnswered):
        game.state_result(by=one, score=_score((6, 2),), occurred_at=_ago(hours=3))


async def test_nobody_who_did_not_play_may_act_on_the_result():
    """The people who may act are the people who were on the court."""

    one, other = new_uuid(), new_uuid()
    game = _planned(line_up=_singles(one, other), at=_ago(hours=2))

    with pytest.raises(YouWereNotOnThisCourt):
        game.state_result(
            by=new_uuid(), score=_score((6, 0),), occurred_at=_ago(hours=1)
        )


async def test_a_ghost_game_may_not_be_resurrected():
    """Past the entry window the game reads as never played to everybody."""

    one, other = new_uuid(), new_uuid()
    now = instant(datetime.now(timezone.utc))
    game = _planned(
        line_up=_singles(one, other),
        at=instant(now - PLAN_HORIZON - ENTRY_GRACE - timedelta(hours=1)),
    )

    with pytest.raises(TheEntryWindowHasClosed):
        game.state_result(by=one, score=_score((6, 4),), occurred_at=now)


async def test_a_settled_result_is_final():
    """No correction path and no reversal — including for an unscored game."""

    one, other = new_uuid(), new_uuid()
    entered = _ago(days=2)
    game = _planned(line_up=_singles(one, other), at=_ago(days=3))
    game.state_result(by=one, score=_score((6, 4),), occurred_at=entered)

    with pytest.raises(TheResultIsSettled):
        game.state_result(
            by=other,
            score=_score((4, 6),),
            occurred_at=instant(entered + PROPOSAL_WINDOW + timedelta(minutes=1)),
        )


# ---------------------------------------------------------------------------
# The reads, and what each of them promises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_counted_games_zero_is_measured_and_everybody_asked_is_answered(
    implementation, session
):
    """The opposite of a Player Score, and deliberately.

    The games ledger exists, so *this person has played none* is a real answer —
    and it is the answer §9.10's newcomer predicate has been waiting for. A
    player is never absent from this read.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    stranger = new_uuid()

    assert await port.counted_games_for([stranger], now=now) == {stranger: 0}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_friendly_is_never_evidence_and_is_still_an_acquaintance(
    implementation, session
):
    """The two halves of what a friendly is, in one demand.

    It is out of ``counted_games`` and out of the results, because the people who
    arranged it said it was not evidence. It is **in** the pairwise history,
    because a friendly puts two people on a court exactly as a counted game does
    — it is the Level a friendly leaves alone, not the acquaintance.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(one, other), at=_ago(days=2), kind=GameKind.FRIENDLY
    )
    game.state_result(by=one, score=_score((6, 4),), occurred_at=_ago(days=1))
    await _saved(session, game)

    counts = await port.counted_games_for([one, other], now=now)
    results = await port.recent_results_for([one, other], now=now)
    counterparts = await port.played_counterparts(one, now=now)

    assert counts == {one: 0, other: 0}
    assert results == {}
    assert counterparts[0].games_played_together == 1


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_the_last_results_are_oldest_first_bounded_and_never_padded(
    implementation, session
):
    """*Last 5*, and the three things the card needs to be true of it.

    **Oldest to newest**, because the row is read left to right as a run of form.
    **At most five**, and they are the five most recent rather than the first
    five found. **Never padded** — a player with three has three, and the card
    draws a gap.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, opponent = new_uuid(), new_uuid()

    for day, winner in enumerate(
        (player, opponent, player, player, opponent, player), start=1
    ):
        played = _ago(days=20 - day)
        game = _planned(
            line_up=_singles(player, opponent), at=instant(played - timedelta(hours=1))
        )
        game.state_result(
            by=winner,
            score=_score((6, 4),) if winner is player else _score((4, 6),),
            occurred_at=played,
        )
        await _saved(session, game)

    results = await port.recent_results_for([player], now=now)
    outcomes = [one.outcome for one in results[player]]

    assert len(outcomes) == RECENT_RESULTS
    assert outcomes == [
        Outcome.LOSS,
        Outcome.WIN,
        Outcome.WIN,
        Outcome.LOSS,
        Outcome.WIN,
    ]
    assert [one.played_at for one in results[player]] == sorted(
        one.played_at for one in results[player]
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_run_in_one_sport_is_filtered_before_it_is_trimmed(
    implementation, session
):
    """**The whole reason this read exists beside the set one.**

    Six padel games and then six tennis ones. The set read answers the last five
    of everything — all tennis — and a consumer narrowing that afterwards would
    show a padel Level with an empty run under it. This one filters first, so a
    player who has played thirty in a sport gets five.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, opponent = new_uuid(), new_uuid()

    for day, sport in enumerate([Sport.PADEL] * 6 + [Sport.TENNIS] * 6, start=1):
        played = _ago(days=20 - day)
        game = _planned(
            line_up=_singles(player, opponent),
            at=instant(played - timedelta(hours=1)),
            sport=sport,
        )
        game.state_result(by=player, score=_score((6, 4)), occurred_at=played)
        await _saved(session, game)

    everything = await port.recent_results_for([player], now=now)
    padel = await port.recent_results_in(player, sport=Sport.PADEL, now=now)

    assert {one.sport for one in everything[player]} == {Sport.TENNIS}
    assert len(padel) == RECENT_RESULTS
    assert {one.sport for one in padel} == {Sport.PADEL}
    assert [one.played_at for one in padel] == sorted(one.played_at for one in padel)


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_run_shorter_than_five_in_that_sport_is_never_padded(
    implementation, session
):
    """Two results means two, and the card draws the gap."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, opponent = new_uuid(), new_uuid()

    for day, winner in enumerate((player, opponent), start=1):
        played = _ago(days=10 - day)
        game = _planned(
            line_up=_singles(player, opponent),
            at=instant(played - timedelta(hours=1)),
            sport=Sport.SQUASH,
        )
        game.state_result(
            by=winner,
            score=_score((6, 4)) if winner is player else _score((4, 6)),
            occurred_at=played,
        )
        await _saved(session, game)

    run = await port.recent_results_in(player, sport=Sport.SQUASH, now=now)

    assert [one.outcome for one in run] == [Outcome.WIN, Outcome.LOSS]


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_sport_they_have_played_nothing_counted_in_is_an_empty_run(
    implementation, session
):
    """**Empty and not absent**, unlike the mapping beside it: this read answers
    about one player, so a short tuple already says the whole of *there is less
    to show* and a second spelling would be one to get wrong."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))

    assert (
        await port.recent_results_in(new_uuid(), sport=Sport.BADMINTON, now=now) == ()
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_player_with_no_results_is_absent_rather_than_empty(
    implementation, session
):
    """One spelling for *nothing to show*.

    Two — an absent key and an empty tuple — is how a measured nothing and an
    unasked question start being confused.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    stranger = new_uuid()

    assert await port.recent_results_for([stranger], now=now) == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_played_game_and_a_ghost_stay_apart_in_one_counterpart(
    implementation, session
):
    """One row per person, with both outcomes inside it.

    A pair who played once and ghosted once are not a ghost. Collapsing to a
    latest outcome would erase the history the depth term counts.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    played = _planned(line_up=_singles(one, other), at=_ago(days=2))
    played.state_result(by=one, score=_score((6, 4),), occurred_at=_ago(days=1))
    await _saved(session, played)
    await _saved(
        session,
        _planned(
            line_up=_singles(one, other),
            at=instant(now - PLAN_HORIZON - ENTRY_GRACE - timedelta(hours=1)),
        ),
    )

    (counterpart,) = await port.played_counterparts(one, now=now)

    assert set(counterpart.outcomes) == {
        PlayedOutcome.PLAYED,
        PlayedOutcome.PLANNED_NEVER_PLAYED,
    }
    assert counterpart.games_played_together == 1


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_plan_still_inside_its_entry_window_says_nothing_about_the_pair(
    implementation, session
):
    """Three answers and not two.

    A game nobody has claimed yet is not a ghost — its window is still open — and
    it is not a played game either. It is left out, because filing it either way
    would publish a conclusion the clock has not reached.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    await _saved(session, _planned(line_up=_singles(one, other), at=_ago(hours=1)))

    assert await port.played_counterparts(one, now=now) == ()


# ---------------------------------------------------------------------------
# attendance_for — the *shows up* strand's input, per person and never per pair
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_attendance_counts_a_game_played_and_a_plan_that_ghosted(
    implementation, session
):
    """The two halves of *shows up*, on the same two people.

    One plan produced a game and one closed its entry window on silence, so both
    are opportunities and one of them is a good outcome. The moment is the moment
    each **settled** — the game's own, and the ghost's window closing — which is
    not the moment either was planned.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    played = _planned(line_up=_singles(one, other), at=_ago(days=3))
    played.state_result(by=one, score=_score((6, 4),), occurred_at=_ago(days=2))
    await _saved(session, played)
    ghost = _planned(
        line_up=_singles(one, other),
        at=_ago(days=PLAN_HORIZON.days + ENTRY_GRACE.days + 5),
    )
    await _saved(session, ghost)

    attendance = await port.attendance_for([one, other], now=now)

    assert (attendance[one].played, attendance[one].ghosts) == (1, 1)
    assert attendance[one] == attendance[other]
    assert attendance[one].last_at == played.played_at


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_player_nobody_arranged_anything_for_is_absent_from_attendance(
    implementation, session
):
    """The one read here whose zero would be **invented**.

    ``counted_games_for`` answers ``0`` for a stranger, because the games were
    counted and none of them was theirs. A ``0/0`` here would say somebody was
    due on a court and did not come, about a person nothing ever arranged
    anything for.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    stranger = new_uuid()

    assert await port.counted_games_for([stranger], now=now) == {stranger: 0}
    assert await port.attendance_for([stranger], now=now) == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_plan_still_inside_its_entry_window_is_not_yet_an_opportunity(
    implementation, session
):
    """Three answers here too, and for the same reason.

    A game nobody has claimed yet is not a ghost, so charging it against
    somebody's *shows up* would publish a conclusion the clock has not reached —
    and the player is absent rather than sitting at ``0/0``.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    await _saved(session, _planned(line_up=_singles(one, other), at=_ago(hours=1)))

    assert await port.attendance_for([one, other], now=now) == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_four_that_played_once_is_one_opportunity_for_each_of_them(
    implementation, session
):
    """**Per person, never a sum of the pairwise read.**

    A doubles evening is one game and three counterparts, so a strand folded out
    of ``played_counterparts`` would charge each of these four for turning up
    three times — and would make *shows up* a statement about how many people
    somebody plays with.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    a, b, c, d = new_uuid(), new_uuid(), new_uuid(), new_uuid()

    game = _planned(line_up=_four(a, b, c, d), at=_ago(days=3))
    game.state_result(by=a, score=_score((6, 4),), occurred_at=_ago(days=2))
    await _saved(session, game)

    attendance = await port.attendance_for([a, b, c, d], now=now)

    assert len(await port.played_counterparts(a, now=now)) == 3
    assert all(
        (attendance[one].played, attendance[one].ghosts) == (1, 0)
        for one in (a, b, c, d)
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_friendly_counts_towards_turning_up_like_any_other_game(
    implementation, session
):
    """Turning up is not evidence about a Level, so the kind has nothing to say.

    A friendly is out of ``counted_games`` by the choice of the people who
    arranged it, and that choice was about their ratings — not about whether they
    came.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(one, other), at=_ago(days=3), kind=GameKind.FRIENDLY
    )
    game.state_result(by=one, score=_score((6, 4),), occurred_at=_ago(days=2))
    await _saved(session, game)

    assert await port.counted_games_for([one], now=now) == {one: 0}
    assert (await port.attendance_for([one], now=now))[one].played == 1


# ---------------------------------------------------------------------------
# result_answering_for — the *answers about results* strand's input
# ---------------------------------------------------------------------------


def _forever_ago() -> Instant:
    """A ``since`` far enough back that the window is not what is under test."""

    return _ago(days=3650)


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_accepting_and_countering_are_both_answers_and_silence_is_the_miss(
    implementation, session
):
    """The three endings of a score put in front of somebody, on one read.

    **A counter is a good outcome**, which is the whole difference from the
    strand ``docs/adr/0137`` struck: a player who believes the score is wrong says
    so and is credited for saying it, so nobody is docked for disagreeing.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    opener, accepter = new_uuid(), new_uuid()
    counterer, ignorer = new_uuid(), new_uuid()

    accepted = _planned(line_up=_singles(opener, accepter), at=_ago(days=4))
    accepted.state_result(by=opener, score=_score((6, 4),), occurred_at=_ago(days=3))
    accepted.accept_result(by=accepter, occurred_at=_ago(days=3))
    await _saved(session, accepted)

    countered = _planned(line_up=_singles(opener, counterer), at=_ago(days=4))
    countered.state_result(by=opener, score=_score((6, 4),), occurred_at=_ago(days=3))
    countered.state_result(
        by=counterer, score=_score((4, 6),), occurred_at=_ago(days=3)
    )
    await _saved(session, countered)

    ignored = _planned(line_up=_singles(opener, ignorer), at=_ago(days=4))
    ignored.state_result(by=opener, score=_score((6, 4),), occurred_at=_ago(days=3))
    await _saved(session, ignored)

    answering = await port.result_answering_for(
        [accepter, counterer, ignorer], since=_forever_ago(), now=now
    )

    assert (answering[accepter].answered, answering[accepter].ignored) == (1, 0)
    assert (answering[counterer].answered, answering[counterer].ignored) == (1, 0)
    assert (answering[ignorer].answered, answering[ignorer].ignored) == (0, 1)


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_the_side_that_entered_the_score_was_asked_nothing(
    implementation, session
):
    """**One opportunity per game, and it belongs to the side that was asked.**

    The entry that records *we played* records a score in the same act, so one
    side always opens; once the other side counters, the argument is capped and
    the opener may only give way. Charging the opener for not giving way is
    exactly the *dock somebody for disagreeing* this strand exists not to do.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    opener, other = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(opener, other), at=_ago(days=4))
    game.state_result(by=opener, score=_score((6, 4),), occurred_at=_ago(days=3))
    game.state_result(by=other, score=_score((4, 6),), occurred_at=_ago(days=3))
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.UNSCORED

    answering = await port.result_answering_for(
        [opener, other], since=_forever_ago(), now=now
    )

    assert set(answering) == {other}
    assert (answering[other].answered, answering[other].ignored) == (1, 0)


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_score_still_inside_its_window_is_in_neither_half(
    implementation, session
):
    """The answer is still wanted, so the player is absent rather than at ``0/0``."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    opener, other = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(opener, other), at=_ago(days=1))
    game.state_result(by=opener, score=_score((6, 4),), occurred_at=_ago(hours=1))
    await _saved(session, game)

    assert (
        await port.result_answering_for(
            [opener, other], since=_forever_ago(), now=now
        )
        == {}
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_doubles_score_is_put_to_both_people_on_the_side_it_faces(
    implementation, session
):
    """A pair carries the score their side never answered, and the openers carry
    nothing.

    It is one question and two people were asked it, which is the same per-person
    shape *shows up* takes for a different reason: there, everybody on the court
    was in the arrangement.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    a, b, c, d = new_uuid(), new_uuid(), new_uuid(), new_uuid()

    game = _planned(line_up=_four(a, b, c, d), at=_ago(days=4))
    game.state_result(by=a, score=_score((6, 4),), occurred_at=_ago(days=3))
    await _saved(session, game)

    answering = await port.result_answering_for(
        [a, b, c, d], since=_forever_ago(), now=now
    )

    assert set(answering) == {c, d}
    assert answering[c] == answering[d]
    assert (answering[c].answered, answering[c].ignored) == (0, 1)


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_an_opportunity_older_than_the_callers_window_is_in_neither_half(
    implementation, session
):
    """**The window is the caller's and this context holds no opinion about it.**

    The same record read with two ``since`` values gives two answers, which is
    what makes *how far back a strand remembers* a decision belonging to the
    context that publishes the strand rather than to the one that owns the games.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    opener, other = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(opener, other), at=_ago(days=400))
    game.state_result(by=opener, score=_score((6, 4),), occurred_at=_ago(days=399))
    await _saved(session, game)

    assert await port.result_answering_for(
        [other], since=_forever_ago(), now=now
    ) != {}
    assert (
        await port.result_answering_for([other], since=_ago(days=365), now=now) == {}
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_friendly_puts_a_score_in_front_of_somebody_like_any_other_game(
    implementation, session
):
    """A score is a question whether or not the evening was evidence.

    The choice that makes a game a friendly is a choice about ratings; it says
    nothing about whether the people on that court answered each other.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    opener, other = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(opener, other), at=_ago(days=4), kind=GameKind.FRIENDLY
    )
    game.state_result(by=opener, score=_score((6, 4),), occurred_at=_ago(days=3))
    await _saved(session, game)

    answering = await port.result_answering_for(
        [other], since=_forever_ago(), now=now
    )

    assert (answering[other].answered, answering[other].ignored) == (0, 1)


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_player_nobody_ever_put_a_score_to_is_absent(
    implementation, session
):
    """The second read here whose zero would be invented.

    Somebody who has never been sent a score has not ignored one, and a ``0/0``
    would say they had.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))

    assert (
        await port.result_answering_for(
            [new_uuid()], since=_forever_ago(), now=now
        )
        == {}
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_the_moment_is_when_the_opportunity_closed_and_not_when_it_opened(
    implementation, session
):
    """An answer is dated from the answer; silence is dated from the deadline.

    Dating silence from the score going up would age a record faster than the
    record aged, which is the rule a ghost is already dated by.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    opener, other = new_uuid(), new_uuid()

    proposed_at = _ago(days=3)
    game = _planned(line_up=_singles(opener, other), at=_ago(days=4))
    game.state_result(by=opener, score=_score((6, 4),), occurred_at=proposed_at)
    await _saved(session, game)

    answering = await port.result_answering_for(
        [other], since=_forever_ago(), now=now
    )

    assert answering[other].last_at == instant(proposed_at + PROPOSAL_WINDOW)


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_late_is_a_fact_about_a_plan_and_this_context_has_no_number(
    implementation, session
):
    """``None``, and absent rather than defaulted.

    A plan here is a line-up with a window and no time in it: nothing can be
    changed late because nothing can be changed at all. A number nobody measured
    is a number somebody picked.
    """

    port = implementation.build(session)

    assert await port.late_change_threshold() is None


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


def test_every_published_port_has_at_least_one_implementation():
    """A port with nothing registered is a red build.

    Otherwise a port added in a hurry looks contracted while nothing on earth
    runs against it — the exact failure ``docs/adr/0098`` exists to prevent,
    arriving by omission rather than by anybody deciding it.
    """

    unregistered = [
        port.__name__ for port in GAMES_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_is_of_a_published_port():
    """And the other direction, so the two lists check each other."""

    stray = [
        one.name for one in GAME_IMPLEMENTATIONS if one.port not in GAMES_DEMANDS
    ]

    assert stray == []


@pytest.mark.parametrize("implementation", every_row())
def test_every_implementation_satisfies_the_protocol(implementation):
    """Structural, so a method renamed on one side is red rather than a runtime
    ``AttributeError`` on somebody's search.

    **Over every row rather than over one port's**, which is the shape the
    consumer registers already take: one class here answers three of these
    contracts, and a check that only walked the first would have watched half
    the register.
    """

    assert isinstance(implementation.build(None), implementation.port)


# ---------------------------------------------------------------------------
# GameDirectory — counted or a friendly, and confirmed or not, about one player
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(GameDirectory))
async def test_a_game_says_whether_it_was_counted_and_whether_it_was_confirmed(
    implementation, session
):
    """The two facts the rating and Player Score tickets were promised.

    Both are on the aggregate rather than on a row: ``kind`` was chosen when the
    game was arranged and cannot move, and the standing is folded against the
    caller's clock — so *is this confirmed* answers the same at every instant,
    including the whole gap between a deadline and anybody looking.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, opponent = new_uuid(), new_uuid()

    counted = _planned(line_up=_singles(player, opponent), at=_ago(days=3))
    counted.state_result(by=player, score=_score((6, 4),), occurred_at=_ago(days=2))
    await _saved(session, counted)

    friendly = _planned(
        line_up=_singles(player, opponent),
        at=_ago(hours=3),
        kind=GameKind.FRIENDLY,
    )
    friendly.state_result(by=player, score=_score((6, 1),), occurred_at=_ago(hours=2))
    await _saved(session, friendly)

    by_id = {game.id: game for game in await port.playing(player)}

    assert by_id[counted.id].kind is GameKind.COUNTED
    assert by_id[counted.id].standing_at(now) is GameStanding.CONFIRMED
    assert by_id[friendly.id].kind is GameKind.FRIENDLY
    assert by_id[friendly.id].standing_at(now) is GameStanding.AWAITING_ANSWER


@pytest.mark.parametrize("implementation", registered(GameDirectory))
async def test_the_directory_answers_about_the_reader_and_nobody_else(
    implementation, session
):
    """A game you were not on the court of is not yours to read.

    The route's refusal says the same thing one layer out, with one code for
    *no such game* and *not yours* — but the read has to be the narrow one, or
    the refusal would be the only thing standing between a stranger's id and
    four people's evening.
    """

    port = implementation.build(session)
    one, other, stranger = new_uuid(), new_uuid(), new_uuid()

    await _saved(session, _planned(line_up=_singles(one, other), at=_ago(hours=1)))

    assert await port.playing(stranger) == ()


# ---------------------------------------------------------------------------
# ConfirmedResultLedger — the read with nothing to subscribe to
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_a_confirmed_counted_result_is_published_with_both_sides(
    implementation, session
):
    """The read the rating context walks forward, and the shape it needs.

    Two sides rather than an outcome per player, because a result is a fact about
    a game and which side you were on — and the winner is the side the score
    names, never one recorded beside it.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    winner, loser = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(winner, loser), at=_ago(days=3))
    game.state_result(by=winner, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2))
    await _saved(session, game)

    published = await port.confirmed_counted_results(now=now)

    assert [one.game_id for one in published] == [game.id]
    assert published[0].winners == (winner,)
    assert published[0].losers == (loser,)
    assert published[0].sport is Sport.TENNIS


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_a_four_publishes_two_people_on_each_side_in_the_line_ups_order(
    implementation, session
):
    """**Tuples and never sets**, because a Level moved depends on the walk.

    The score is **absolute** — side A's points against side B's — so a member of
    side B entering ``4-6, 3-6`` is entering their own defeat, and the winner is
    the side the score names rather than the side that typed it.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, two, three, four = (new_uuid() for _ in range(4))

    game = _planned(
        line_up=_four(one, two, three, four), at=_ago(days=3), sport=Sport.PADEL
    )
    game.state_result(by=three, score=_score((4, 6), (3, 6)), occurred_at=_ago(days=2))
    await _saved(session, game)

    published = await port.confirmed_counted_results(now=now)

    assert published[0].winners == (three, four)
    assert published[0].losers == (one, two)


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_an_unscored_game_is_an_evening_and_never_reaches_the_ledger(
    implementation, session
):
    """Two scores, nobody accepted either, both windows gone. **It moves nobody.**"""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    home, away = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(home, away), at=_ago(days=4))
    game.state_result(by=home, score=_score((6, 4),), occurred_at=_ago(days=3))
    game.state_result(by=away, score=_score((4, 6),), occurred_at=_ago(days=3))
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.UNSCORED
    assert await port.confirmed_counted_results(now=now) == ()


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_a_friendly_never_reaches_the_ledger_however_it_ended(
    implementation, session
):
    """*A friendly is a thing people choose*, and it was never evidence."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    winner, loser = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(winner, loser), at=_ago(days=3), kind=GameKind.FRIENDLY
    )
    game.state_result(by=winner, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2))
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.CONFIRMED
    assert await port.confirmed_counted_results(now=now) == ()


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_a_result_still_inside_its_window_has_not_settled_on_anything(
    implementation, session
):
    """Proved by asking the same record at two instants, never by a method.

    There is nothing here called ``confirm``: a lone score is agreed when its
    window closes, so the demand advances a clock — and until it has, the ledger
    has nothing to publish and the Level it would move has not moved.
    """

    port = implementation.build(session)
    winner, loser = new_uuid(), new_uuid()

    entered = _ago(hours=1)
    game = _planned(line_up=_singles(winner, loser), at=_ago(days=1))
    game.state_result(by=winner, score=_score((6, 4), (6, 3)), occurred_at=entered)
    await _saved(session, game)

    still_open = instant(datetime.now(timezone.utc))
    assert await port.confirmed_counted_results(now=still_open) == ()

    settled = instant(entered + PROPOSAL_WINDOW)
    published = await port.confirmed_counted_results(now=settled)
    assert [one.game_id for one in published] == [game.id]
    assert published[0].confirmed_at == settled


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_results_are_published_in_the_order_they_became_final(
    implementation, session
):
    """**Oldest first is the contract**, and it is not the order they were entered.

    A Level is moved against the Levels as they stood, so an out-of-order walk
    produces a different rating for the same history and nothing says so. The
    order is settlement, which for a score nobody answered is its window closing
    — so a game entered *later* can settle *earlier* than one whose proposal was
    corrected, and that is exactly what this arranges.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    home, away = new_uuid(), new_uuid()

    earlier = _planned(line_up=_singles(home, away), at=_ago(days=5))
    earlier.state_result(by=home, score=_score((6, 1),), occurred_at=_ago(days=4))
    await _saved(session, earlier)

    later = _planned(line_up=_singles(home, away), at=_ago(days=3))
    later.state_result(by=away, score=_score((6, 2),), occurred_at=_ago(days=2))
    await _saved(session, later)

    published = await port.confirmed_counted_results(now=now)

    assert [one.game_id for one in published] == [earlier.id, later.id]
    assert published[0].confirmed_at < published[1].confirmed_at


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_the_ledger_reads_the_same_answer_twice(implementation, session):
    """It holds no cursor and consumes nothing, which is why a catch-up may die.

    The idempotency lives on the rating stream instead, so the read has to be
    repeatable — a ledger that drained would make a half-finished run a lost
    result rather than a repeated one.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    winner, loser = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(winner, loser), at=_ago(days=3))
    game.state_result(by=winner, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2))
    await _saved(session, game)

    once = await port.confirmed_counted_results(now=now)
    twice = await port.confirmed_counted_results(now=now)

    assert once == twice
    assert len(once) == 1


# ---------------------------------------------------------------------------
# PlanningCourt — the one question the Plan asks before it lets anybody write
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlanningCourt))
async def test_a_game_still_awaiting_its_entry_is_open_to_planning(
    implementation, session
):
    """``docs/adr/0144`` — the slots are frozen by the game leaving its entry
    window and by nothing else, so inside it the answer is simply *yes*."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    ana, bo = new_uuid(), new_uuid()

    game = await _saved(session, _planned(line_up=_singles(ana, bo), at=_ago(days=1)))
    found = await port.plannable_for(ana, now=now)

    assert found[game.id].open_to_planning
    assert found[game.id].planned_at == game.planned_at


@pytest.mark.parametrize("implementation", registered(PlanningCourt))
async def test_a_game_past_its_entry_window_is_history_and_still_answered_about(
    implementation, session
):
    """**Two different refusals, and only one shape can carry both.**

    A game whose entry window closed is *history* — its slots are frozen — and it
    is still in the answer, because the plan is drawn beside a game whatever its
    standing. Dropping it here would make *you were not on that court* and *that
    court is over* the same answer.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    ana, bo = new_uuid(), new_uuid()

    game = await _saved(session, _planned(line_up=_singles(ana, bo), at=_ago(days=30)))
    found = await port.plannable_for(ana, now=now)

    assert game.standing_at(now) is GameStanding.NEVER_PLAYED
    assert game.id in found
    assert not found[game.id].open_to_planning


@pytest.mark.parametrize("implementation", registered(PlanningCourt))
async def test_a_game_somebody_said_they_played_is_no_longer_open_to_planning(
    implementation, session
):
    """The other way out of ``AWAITING_ENTRY``, and it freezes the slots too.

    Once somebody has said *we played*, the plan is history — a note about an
    evening that is over rather than an arrangement anybody is still making.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    ana, bo = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(ana, bo), at=_ago(days=1))
    game.state_result(by=ana, score=_score((6, 4), (6, 3)), occurred_at=_ago(hours=1))
    await _saved(session, game)

    found = await port.plannable_for(ana, now=now)

    assert not found[game.id].open_to_planning


@pytest.mark.parametrize("implementation", registered(PlanningCourt))
async def test_somebody_who_was_not_on_the_court_is_answered_about_nothing(
    implementation, session
):
    """**Absence is the whole of *you may not write here*.**

    There is no field saying so, because a field has to be read and a missing row
    cannot be forgotten.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    ana, bo, stranger = new_uuid(), new_uuid(), new_uuid()

    game = await _saved(session, _planned(line_up=_singles(ana, bo), at=_ago(days=1)))

    assert await port.plannable_for(stranger, now=now) == {}
    assert game.id in await port.plannable_for(bo, now=now)


# ---------------------------------------------------------------------------
# OpponentVarietyQuery — the career statistic, unbounded and about one person
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(OpponentVarietyQuery))
async def test_variety_is_the_people_over_the_times_they_were_on_a_court(
    implementation, session
):
    """The pair a record divides, and the two halves come from one fold.

    Three singles games against two people: two different faces, three times on
    a court. In singles the denominator is also a count of evenings, which is
    why a game was the denominator first and why the bug it carried only showed
    on doubles. Publishing the counts rather than the share is the whole shape
    of this read — *fourteen of twenty* and *seven of ten* are different claims
    and a percentage alone hides which one it is.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, one, other = new_uuid(), new_uuid(), new_uuid()

    for opponent in (one, other, one):
        game = _planned(line_up=_singles(player, opponent), at=_ago(days=3))
        game.state_result(
            by=player, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2)
        )
        await _saved(session, game)

    variety = await port.variety_of(player, now=now)

    assert variety == OpponentVariety(distinct_counterparts=2, times_on_court=3)


@pytest.mark.parametrize("implementation", registered(OpponentVarietyQuery))
async def test_a_player_with_no_counted_game_is_absent_rather_than_nought(
    implementation, session
):
    """**Absent, never ``0`` and never ``0/0``.** A player nothing was ever
    counted for has not narrowed their circle — there is nothing to describe,
    and the record omits the row rather than printing a habit nobody has."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))

    assert await port.variety_of(new_uuid(), now=now) is None


@pytest.mark.parametrize("implementation", registered(OpponentVarietyQuery))
async def test_a_four_is_one_evening_and_three_different_people(
    implementation, session
):
    """**A partner is one of the faces**, exactly as they are for familiarity.

    *A pair is anybody you were on a court with*, and a variety figure that
    counted opponents alone would say a player who partners the same person
    every week spreads their games as widely as one who does not.

    **And a four is three times on a court, not one.** The denominator counts
    seats opposite rather than evenings, which is what makes the pair divisible
    at every court size: this used to publish ``3 of 1``, a fraction whose
    numerator exceeds its denominator and which only a clamp could draw.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, partner = new_uuid(), new_uuid()
    against_one, against_other = new_uuid(), new_uuid()

    game = _planned(
        line_up=_four(player, partner, against_one, against_other), at=_ago(days=3)
    )
    game.state_result(by=player, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2))
    await _saved(session, game)

    variety = await port.variety_of(player, now=now)

    assert variety == OpponentVariety(distinct_counterparts=3, times_on_court=3)


@pytest.mark.parametrize("implementation", registered(OpponentVarietyQuery))
async def test_a_friendly_and_a_ghost_are_in_neither_half_of_the_pair(
    implementation, session
):
    """**Both halves are read off the same games**, which is why they are one
    method.

    A friendly is an acquaintance for familiarity and it is not evidence, so it
    is out of the denominator — and it has to be out of the numerator too, or a
    player with forty friendlies and two counted games would be described as
    playing twenty different people per evening.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, opponent = new_uuid(), new_uuid()
    friend, never_came = new_uuid(), new_uuid()

    counted = _planned(line_up=_singles(player, opponent), at=_ago(days=3))
    counted.state_result(
        by=player, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2)
    )
    await _saved(session, counted)

    friendly = _planned(
        line_up=_singles(player, friend), at=_ago(days=3), kind=GameKind.FRIENDLY
    )
    friendly.state_result(by=player, score=_score((6, 4),), occurred_at=_ago(days=2))
    await _saved(session, friendly)

    await _saved(
        session,
        _planned(
            line_up=_singles(player, never_came),
            at=instant(now - PLAN_HORIZON - ENTRY_GRACE - timedelta(hours=1)),
        ),
    )

    variety = await port.variety_of(player, now=now)

    assert variety == OpponentVariety(distinct_counterparts=1, times_on_court=1)


@pytest.mark.parametrize("implementation", registered(OpponentVarietyQuery))
async def test_the_fold_reaches_the_whole_record_and_never_a_window(
    implementation, session
):
    """**Unbounded is what makes it a career statistic.**

    A game from three years ago is in it, because *how widely do they spread
    their games* is a claim about a habit rather than about this season — and a
    window here would be a second horizon that must not disagree with the
    matcher's.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, long_ago, lately = new_uuid(), new_uuid(), new_uuid()

    for opponent, days in ((long_ago, 1100), (lately, 3)):
        game = _planned(line_up=_singles(player, opponent), at=_ago(days=days + 1))
        game.state_result(
            by=player, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=days)
        )
        await _saved(session, game)

    variety = await port.variety_of(player, now=now)

    assert variety == OpponentVariety(distinct_counterparts=2, times_on_court=2)


def test_the_variety_fold_takes_one_player_and_can_never_be_called_over_a_list():
    """**The fence is the signature**, and it is asserted rather than described.

    This fold is unbounded on purpose, so a set-shaped version of it would be an
    invitation to call it inside a search's walk over five hundred candidates.
    One player in, one answer or an absence out — and both halves of that are
    what a widening would have to break first.
    """

    hints = get_type_hints(OpponentVarietyQuery.variety_of)

    assert hints["player_id"] is UUID
    assert hints["return"] == OpponentVariety | None

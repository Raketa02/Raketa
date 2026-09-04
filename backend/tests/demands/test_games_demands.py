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
    GameDirectory,
    GameHistoryQuery,
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


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
def test_every_implementation_satisfies_the_protocol(implementation):
    """Structural, so a method renamed on one side is red rather than a runtime
    ``AttributeError`` on somebody's search."""

    assert isinstance(implementation.build(None), GameHistoryQuery)


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

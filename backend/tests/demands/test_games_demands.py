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
from app.modules.games.domain.attendance import ClubVerdict, Turnout
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
    GameOnTheRecord,
    OpponentVariety,
    OpponentVarietyQuery,
    PlayedTogetherQuery,
    ScoredGames,
)
from app.modules.games.domain.results import Outcome, Score, SetScore
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import (
    ENTRY_GRACE,
    PLAN_HORIZON,
    PROPOSAL_WINDOW,
)
from app.modules.player_profile.domain.weekly_hours import Window
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


def _turnouts(
    record: dict[UUID, tuple[GameOnTheRecord, ...]], player: UUID
) -> list[Turnout]:
    """What each game said about one player, oldest first."""

    return [row.turnout for row in record.get(player, ())]


def _a_no_show(*, absent: UUID, reporter: UUID, starts: Instant) -> Game:
    """A booked singles game ``reporter`` came to and tapped ``absent`` *isn't
    here yet* ten minutes in, at the club — and ``absent`` never arrived and
    never claimed: **Didn't come**, for good a day after half past (#657)."""

    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        kind=GameKind.COUNTED,
        window=None,
        line_up=_singles(absent, reporter),
        occurred_at=instant(starts - timedelta(days=2)),
        starts_at=starts,
    )
    # *Isn't here yet* ten minutes in, at the club, and no arrival: Didn't
    # come at half past, for good a day later (#657).
    game.note_absent(
        by=reporter,
        absent=absent,
        where=ClubVerdict(at_the_club=True, club_name=None),
        occurred_at=instant(starts + timedelta(minutes=10)),
    )
    return game


def _called_off(*, line_up: LineUp, at: Instant, leaver: UUID, caller: UUID) -> Game:
    """A game somebody left and somebody still on it called off, an hour apart
    (``docs/adr/0163``)."""

    game = _planned(line_up=line_up, at=at)
    game.vacate(leaver, occurred_at=instant(at + timedelta(hours=1)))
    game.call_off(by=caller, occurred_at=instant(at + timedelta(hours=2)))
    return game


# ---------------------------------------------------------------------------
# The three ends, each reached through the aggregate and read back through the
# port
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_counted_game_with_a_confirmed_result_was_played_and_has_an_outcome(
    implementation, session
):
    """The end everything else in this batch is waiting on.

    Somebody entered a score, nobody disagreed, its day passed: the game was
    played, it has a winner, and both facts are readable about both people.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    winner, loser = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(winner, loser), at=_ago(days=3))
    game.state_result(by=winner, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2))
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.CONFIRMED

    record = await port.games_on_the_record_for([winner, loser], now=now)
    won = await port.recent_results_in(winner, sport=Sport.TENNIS, now=now)
    lost = await port.recent_results_in(loser, sport=Sport.TENNIS, now=now)

    assert _turnouts(record, winner) == [Turnout.PLAYED_THROUGH]
    assert record[winner] == record[loser]
    assert [one.outcome for one in won] == [Outcome.WIN]
    assert [one.outcome for one in lost] == [Outcome.LOSS]


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_counted_game_nobody_agreed_is_an_evening_and_never_evidence(
    implementation, session
):
    """Two scores naming different winners, nobody accepted either, both days
    gone: **disputed** (#654).

    ``docs/adr/0049``: it counts toward how much these people have played and it
    **moves nobody's Level**. So they turned up for it and it is not in their
    results — and neither of those is a special case anywhere, they fall out of
    *played* and *confirmed* being two different questions.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(one, other), at=_ago(days=3))
    game.state_result(
        by=one,
        score=_score(
            (6, 4),
        ),
        occurred_at=_ago(days=2),
    )
    game.state_result(
        by=other,
        score=_score(
            (4, 6),
        ),
        occurred_at=_ago(days=2),
    )
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.DISPUTED

    record = await port.games_on_the_record_for([one, other], now=now)

    # Played through for both, and **left in dispute** by both — the two who
    # put the scores up (#659).
    assert record[one] == record[other] == (
        GameOnTheRecord(
            game_id=game.id,
            at=game.planned_at,
            turnout=Turnout.PLAYED_THROUGH,
            left_in_dispute=True,
        ),
    )
    assert await port.recent_results_in(one, sport=Sport.TENNIS, now=now) == ()
    assert await port.recent_results_in(other, sport=Sport.TENNIS, now=now) == ()


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_full_court_nobody_recorded_was_played_and_is_never_evidence(
    implementation, session
):
    """**Played · no score** (#655; ``docs/adr/0195`` §2). Nobody ever said it
    happened and the entry window closed on a full court: it was played, for
    both of them — the ghost and its miss are retired — and it has no result,
    so it moves nobody's Level.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(one, other),
        at=instant(now - PLAN_HORIZON - ENTRY_GRACE - timedelta(hours=1)),
    )
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.PLAYED_NO_SCORE

    record = await port.games_on_the_record_for([one, other], now=now)

    assert _turnouts(record, one) == [Turnout.PLAYED_THROUGH]
    assert record[one] == record[other]
    assert not record[one][0].left_in_dispute
    assert await port.recent_results_in(one, sport=Sport.TENNIS, now=now) == ()


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
    game.state_result(
        by=winner,
        score=_score(
            (6, 1),
        ),
        occurred_at=entered,
    )

    a_moment_later = instant(entered + timedelta(minutes=1))
    a_day_later = instant(entered + PROPOSAL_WINDOW)

    assert game.standing_at(a_moment_later) is GameStanding.AWAITING_ANSWER
    assert game.confirmed_score_at(a_moment_later) is None
    assert game.standing_at(a_day_later) is GameStanding.CONFIRMED
    assert game.outcome_for(winner, now=a_day_later) is Outcome.WIN


async def test_an_acceptance_settles_at_once_and_closes_the_game():
    """*That's right* from one opponent is enough, and it closes the door (#654;
    ``docs/adr/0195`` §5): the result is final at the tap, and a different
    score from the other opponent afterwards is refused."""

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
    agreed = instant(entered + timedelta(minutes=2))
    game = _planned(line_up=line_up, at=_ago(days=2), sport=Sport.PADEL)
    game.state_result(
        by=a_one,
        score=_score(
            (6, 4),
        ),
        occurred_at=entered,
    )
    game.accept_result(by=b_one, occurred_at=agreed)

    assert game.standing_at(agreed) is GameStanding.CONFIRMED
    assert game.confirmed_at(agreed) == agreed
    with pytest.raises(TheResultIsSettled):
        game.state_result(
            by=b_two,
            score=_score(
                (4, 6),
            ),
            occurred_at=instant(entered + timedelta(minutes=3)),
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
    game.state_result(
        by=one,
        score=_score(
            (6, 4),
        ),
        occurred_at=_ago(hours=2),
    )

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
    game.state_result(
        by=one,
        score=_score(
            (6, 4),
        ),
        occurred_at=_ago(hours=5),
    )
    game.state_result(
        by=other,
        score=_score(
            (4, 6),
        ),
        occurred_at=_ago(hours=4),
    )

    with pytest.raises(YourSideHasAlreadyAnswered):
        game.state_result(
            by=one,
            score=_score(
                (6, 2),
            ),
            occurred_at=_ago(hours=3),
        )


async def test_nobody_who_did_not_play_may_act_on_the_result():
    """The people who may act are the people who were on the court."""

    one, other = new_uuid(), new_uuid()
    game = _planned(line_up=_singles(one, other), at=_ago(hours=2))

    with pytest.raises(YouWereNotOnThisCourt):
        game.state_result(
            by=new_uuid(),
            score=_score(
                (6, 0),
            ),
            occurred_at=_ago(hours=1),
        )


async def test_a_game_nobody_recorded_takes_no_score_after_its_window():
    """Past the entry window a full court nobody recorded reads *Played · no
    score* to everybody (#655), and a score now would contradict it."""

    one, other = new_uuid(), new_uuid()
    now = instant(datetime.now(timezone.utc))
    game = _planned(
        line_up=_singles(one, other),
        at=instant(now - PLAN_HORIZON - ENTRY_GRACE - timedelta(hours=1)),
    )

    with pytest.raises(TheEntryWindowHasClosed):
        game.state_result(
            by=one,
            score=_score(
                (6, 4),
            ),
            occurred_at=now,
        )


async def test_a_settled_result_is_final():
    """No correction path and no reversal — including for an unscored game."""

    one, other = new_uuid(), new_uuid()
    entered = _ago(days=2)
    game = _planned(line_up=_singles(one, other), at=_ago(days=3))
    game.state_result(
        by=one,
        score=_score(
            (6, 4),
        ),
        occurred_at=entered,
    )

    with pytest.raises(TheResultIsSettled):
        game.state_result(
            by=other,
            score=_score(
                (4, 6),
            ),
            occurred_at=instant(entered + PROPOSAL_WINDOW + timedelta(minutes=1)),
        )


# ---------------------------------------------------------------------------
# The reads, and what each of them promises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_friendly_is_never_evidence_and_is_still_an_evening(
    implementation, session
):
    """The two halves of what a friendly is, in one demand.

    It is out of the results, because the people who arranged it said it was
    not evidence. It is **in** what they turned up for, because a friendly puts
    two people on a court exactly as a counted game does — it is the Level a
    friendly leaves alone, not the evening.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(one, other), at=_ago(days=2), kind=GameKind.FRIENDLY
    )
    game.state_result(
        by=one,
        score=_score(
            (6, 4),
        ),
        occurred_at=_ago(days=1),
    )
    await _saved(session, game)

    record = await port.games_on_the_record_for([one, other], now=now)

    assert await port.recent_results_in(one, sport=Sport.TENNIS, now=now) == ()
    assert await port.recent_results_in(other, sport=Sport.TENNIS, now=now) == ()
    assert _turnouts(record, one) == _turnouts(record, other) == [
        Turnout.PLAYED_THROUGH
    ]


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
            score=_score(
                (6, 4),
            )
            if winner is player
            else _score(
                (4, 6),
            ),
            occurred_at=played,
        )
        await _saved(session, game)

    results = await port.recent_results_in(player, sport=Sport.TENNIS, now=now)
    outcomes = [one.outcome for one in results]

    assert len(outcomes) == RECENT_RESULTS
    assert outcomes == [
        Outcome.LOSS,
        Outcome.WIN,
        Outcome.WIN,
        Outcome.LOSS,
        Outcome.WIN,
    ]
    assert [one.played_at for one in results] == sorted(
        one.played_at for one in results
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_run_in_one_sport_is_filtered_before_it_is_trimmed(
    implementation, session
):
    """**Filtered first, then trimmed.**

    Six padel games and then six tennis ones. The last five of everything are
    all tennis, and a read narrowing that afterwards would show a padel Level
    with an empty run under it. This one filters first, so a player who has
    played thirty in a sport gets five.
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

    tennis = await port.recent_results_in(player, sport=Sport.TENNIS, now=now)
    padel = await port.recent_results_in(player, sport=Sport.PADEL, now=now)

    assert len(tennis) == RECENT_RESULTS
    assert {one.sport for one in tennis} == {Sport.TENNIS}
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
    """**Empty**: this read answers about one player, so a short tuple already
    says the whole of *there is less to show*."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))

    assert (
        await port.recent_results_in(new_uuid(), sport=Sport.BADMINTON, now=now) == ()
    )


# ---------------------------------------------------------------------------
# games_on_the_record_for — a line per player per game, once it is final (#659)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_game_played_and_a_game_not_come_to_are_read_per_player(
    implementation, session
):
    """``one`` played a game and, to an older one, did not come; ``other`` came
    to both — and the one ``one`` missed never counted, so ``other`` turned up
    to it and nothing more. **Oldest first, each dated by its hour.**"""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    played = _planned(line_up=_singles(one, other), at=_ago(days=3))
    played.state_result(by=one, score=_score((6, 4)), occurred_at=_ago(days=2))
    await _saved(session, played)
    starts = _ago(days=6)
    await _saved(session, _a_no_show(absent=one, reporter=other, starts=starts))

    record = await port.games_on_the_record_for([one, other], now=now)

    assert _turnouts(record, one) == [Turnout.DIDNT_COME, Turnout.PLAYED_THROUGH]
    assert _turnouts(record, other) == [
        Turnout.TURNED_UP_UNCOUNTED,
        Turnout.PLAYED_THROUGH,
    ]
    assert [row.at for row in record[one]] == [starts, played.planned_at]


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_didnt_come_still_inside_its_late_claim_is_on_nobodys_record(
    implementation, session
):
    """Provisional for a day: *I was there*, confirmed, would make it Came late,
    so neither the player tapped nor the one who tapped has a line yet."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    await _saved(session, _a_no_show(absent=one, reporter=other, starts=_ago(hours=3)))

    assert await port.games_on_the_record_for([one, other], now=now) == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_came_late_is_on_the_record_from_the_arrival(implementation, session):
    """Final the moment it is reached, so on the record then — while the game
    it was carries on, and the one who came on time is played through only
    once it is played."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    late, tapper = new_uuid(), new_uuid()
    starts = _ago(hours=2)
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        kind=GameKind.COUNTED,
        window=None,
        line_up=_singles(late, tapper),
        occurred_at=instant(starts - timedelta(days=2)),
        starts_at=starts,
    )
    at_the_club = ClubVerdict(at_the_club=True, club_name=None)
    game.note_absent(
        by=tapper,
        absent=late,
        where=at_the_club,
        occurred_at=instant(starts + timedelta(minutes=10)),
    )
    game.note_arrival(
        by=late,
        arrived=late,
        where=at_the_club,
        occurred_at=instant(starts + timedelta(minutes=22)),
    )
    await _saved(session, game)

    record = await port.games_on_the_record_for([late, tapper], now=now)

    assert record == {
        late: (
            GameOnTheRecord(game_id=game.id, at=starts, turnout=Turnout.CAME_LATE),
        )
    }


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_called_off_game_is_on_nobodys_record(implementation, session):
    """``docs/adr/0163`` §3, and #411 rule 7 on the people who stayed.

    A call-off is an act, and no evening. Filing it against the three who did
    not leave would price somebody else's departure through them — and a player
    whose only game was called off has no line at all.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    await _saved(
        session,
        _called_off(
            line_up=_singles(one, other), at=_ago(days=30), leaver=other, caller=one
        ),
    )

    assert await port.games_on_the_record_for([one, other], now=now) == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_player_nobody_arranged_anything_for_is_absent_from_the_record(
    implementation, session
):
    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))

    assert await port.games_on_the_record_for([new_uuid()], now=now) == {}
    assert await port.games_on_the_record_for([], now=now) == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_plan_still_inside_its_entry_window_is_not_yet_on_the_record(
    implementation, session
):
    """A game nobody has recorded yet is not yet played, so crediting it would
    publish a conclusion the clock has not reached."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    await _saved(session, _planned(line_up=_singles(one, other), at=_ago(hours=1)))

    assert await port.games_on_the_record_for([one, other], now=now) == {}


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_a_four_that_played_once_is_one_line_on_each_of_their_records(
    implementation, session
):
    """**Per person, never a sum over pairs.** A doubles evening is one game,
    so a read folded pair by pair would put three lines on each of these four
    records — and make *shows up* a statement about how many people somebody
    plays with."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    a, b, c, d = new_uuid(), new_uuid(), new_uuid(), new_uuid()

    game = _planned(line_up=_four(a, b, c, d), at=_ago(days=3))
    game.state_result(by=a, score=_score((6, 4)), occurred_at=_ago(days=2))
    await _saved(session, game)

    record = await port.games_on_the_record_for([a, b, c, d], now=now)

    assert all(
        _turnouts(record, one) == [Turnout.PLAYED_THROUGH] for one in (a, b, c, d)
    )


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_the_record_is_unbounded_and_the_window_is_the_readers(
    implementation, session
):
    """``player_score`` remembers six months and *New* reads every game ever
    played through, so this read hands it every line, however old."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    one, other = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(one, other), at=_ago(days=400))
    game.state_result(by=one, score=_score((6, 4)), occurred_at=_ago(days=399))
    await _saved(session, game)

    record = await port.games_on_the_record_for([other], now=now)

    assert _turnouts(record, other) == [Turnout.PLAYED_THROUGH]


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

    stray = [one.name for one in GAME_IMPLEMENTATIONS if one.port not in GAMES_DEMANDS]

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
    counted.state_result(
        by=player,
        score=_score(
            (6, 4),
        ),
        occurred_at=_ago(days=2),
    )
    await _saved(session, counted)

    friendly = _planned(
        line_up=_singles(player, opponent),
        at=_ago(hours=3),
        kind=GameKind.FRIENDLY,
    )
    friendly.state_result(
        by=player,
        score=_score(
            (6, 1),
        ),
        occurred_at=_ago(hours=2),
    )
    await _saved(session, friendly)

    by_id = {game.id: game for game in await port.playing(player)}

    assert by_id[counted.id].kind is GameKind.COUNTED
    assert by_id[counted.id].standing_at(now) is GameStanding.CONFIRMED
    assert by_id[friendly.id].kind is GameKind.FRIENDLY
    assert by_id[friendly.id].standing_at(now) is GameStanding.CONFIRMED, (
        "a For fun score settles at once (#654)"
    )


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
async def test_a_disputed_game_is_an_evening_and_never_reaches_the_ledger(
    implementation, session
):
    """Two scores naming different winners, nobody accepted either, both
    windows gone: **disputed**, and it moves nobody (#654)."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    home, away = new_uuid(), new_uuid()

    game = _planned(line_up=_singles(home, away), at=_ago(days=4))
    game.state_result(
        by=home,
        score=_score(
            (6, 4),
        ),
        occurred_at=_ago(days=3),
    )
    game.state_result(
        by=away,
        score=_score(
            (4, 6),
        ),
        occurred_at=_ago(days=3),
    )
    await _saved(session, game)

    assert game.standing_at(now) is GameStanding.DISPUTED
    assert await port.confirmed_counted_results(now=now) == ()
    assert await port.confirmed_counted_result(game.id, now=now) is None


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
    earlier.state_result(
        by=home,
        score=_score(
            (6, 1),
        ),
        occurred_at=_ago(days=4),
    )
    await _saved(session, earlier)

    later = _planned(line_up=_singles(home, away), at=_ago(days=3))
    later.state_result(
        by=away,
        score=_score(
            (6, 2),
        ),
        occurred_at=_ago(days=2),
    )
    await _saved(session, later)

    published = await port.confirmed_counted_results(now=now)

    assert [one.game_id for one in published] == [earlier.id, later.id]
    assert published[0].confirmed_at < published[1].confirmed_at


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_one_game_agreed_with_is_published_alone_from_the_tap(
    implementation, session
):
    """*That's right* settles a result at once (#654), and its delivery asks
    about that one game as it stood at the tap — never another game, and
    nothing before the tap."""

    port = implementation.build(session)
    winner, loser = new_uuid(), new_uuid()
    agreed_at = _ago(hours=1)

    game = _planned(line_up=_singles(winner, loser), at=_ago(days=1))
    game.state_result(
        by=winner, score=_score((6, 4), (6, 3)), occurred_at=_ago(hours=2)
    )
    game.accept_result(by=loser, occurred_at=agreed_at)
    await _saved(session, game)
    other = _planned(line_up=_singles(winner, loser), at=_ago(days=3))
    other.state_result(by=loser, score=_score((6, 1)), occurred_at=_ago(days=2))
    await _saved(session, other)

    published = await port.confirmed_counted_result(game.id, now=agreed_at)

    assert published is not None
    assert (published.game_id, published.winners, published.losers) == (
        game.id,
        (winner,),
        (loser,),
    )
    assert published.confirmed_at == agreed_at
    before = instant(agreed_at - timedelta(seconds=1))
    assert await port.confirmed_counted_result(game.id, now=before) is None
    assert await port.confirmed_counted_result(new_uuid(), now=agreed_at) is None


@pytest.mark.parametrize("implementation", registered(ConfirmedResultLedger))
async def test_one_friendly_is_never_published_alone_either(implementation, session):
    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    winner, loser = new_uuid(), new_uuid()

    game = _planned(
        line_up=_singles(winner, loser), at=_ago(days=3), kind=GameKind.FRIENDLY
    )
    game.state_result(by=winner, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2))
    await _saved(session, game)

    assert await port.confirmed_counted_result(game.id, now=now) is None


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
async def test_a_friendly_is_in_neither_half_and_a_court_nobody_recorded_in_both(
    implementation, session
):
    """**Both halves are read off the same games**, which is why they are one
    method.

    A friendly is an acquaintance for familiarity and it is not evidence, so it
    is out of the denominator — and it has to be out of the numerator too, or a
    player with forty friendlies and two counted games would be described as
    playing twenty different people per evening. **A full counted court nobody
    recorded is in both** (#655): it was played, scored or not.
    """

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, opponent = new_uuid(), new_uuid()
    friend, unrecorded = new_uuid(), new_uuid()

    counted = _planned(line_up=_singles(player, opponent), at=_ago(days=3))
    counted.state_result(
        by=player, score=_score((6, 4), (6, 3)), occurred_at=_ago(days=2)
    )
    await _saved(session, counted)

    friendly = _planned(
        line_up=_singles(player, friend), at=_ago(days=3), kind=GameKind.FRIENDLY
    )
    friendly.state_result(
        by=player,
        score=_score(
            (6, 4),
        ),
        occurred_at=_ago(days=2),
    )
    await _saved(session, friendly)

    await _saved(
        session,
        _planned(
            line_up=_singles(player, unrecorded),
            at=instant(now - PLAN_HORIZON - ENTRY_GRACE - timedelta(hours=1)),
        ),
    )

    variety = await port.variety_of(player, now=now)

    assert variety == OpponentVariety(distinct_counterparts=2, times_on_court=2)


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


# ---------------------------------------------------------------------------
# A seat somebody left (docs/adr/0162) — what every read says about the court now
# ---------------------------------------------------------------------------


async def _a_game_somebody_left(session, *, at: Instant) -> tuple[Game, UUID, UUID]:
    """A singles game, and then the opponent leaves it. The seat is open."""

    ana, bo = new_uuid(), new_uuid()
    game = _planned(line_up=_singles(ana, bo), at=at)
    game.vacate(bo, occurred_at=instant(at + timedelta(minutes=5)))
    await _saved(session, game)
    return game, ana, bo


@pytest.mark.parametrize("implementation", registered(GameDirectory))
async def test_somebody_who_left_is_no_longer_on_the_court_the_directory_answers(
    implementation, session
):
    """``docs/adr/0162`` §3 — the people who may act are the people on the court
    **now**. The leaver's list no longer holds the game; the one who stayed still
    reads it, with the seat open rather than gone."""

    port = implementation.build(session)
    game, ana, bo = await _a_game_somebody_left(session, at=_ago(days=1))

    assert [one.id for one in await port.playing(ana)] == [game.id]
    (theirs,) = await port.playing(ana)
    assert [seating.player_id for seating in theirs.line_up.seatings] == [ana, None]
    assert await port.playing(bo) == ()


@pytest.mark.parametrize("implementation", registered(GameHistoryQuery))
async def test_somebody_who_left_is_nobodys_attendee(implementation, session):
    """``docs/adr/0162`` §3 and §8 — recorded, not scored. A court left open
    until its window closed went ahead short (#655): it is in nobody's tally,
    the one who stayed's included, and the leaver is not an attendee of it."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    game, ana, bo = await _a_game_somebody_left(session, at=_ago(days=30))
    assert game.standing_at(now) is GameStanding.STARTED_SHORT

    assert await port.games_on_the_record_for([ana, bo], now=now) == {}


# ---------------------------------------------------------------------------
# ScoredGames — which games had a score put on their table lately (#613)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(ScoredGames))
async def test_a_game_is_named_by_the_last_score_put_on_its_table(
    implementation, session
):
    """Proposed, corrected or countered: each puts a score on the table, and a
    correction **re-dates** its side's — so a game whose score was proposed
    before ``since`` is named by the correction or the counter made after it,
    and a game nobody scored never is."""

    port = implementation.build(session)
    ana, bo = new_uuid(), new_uuid()
    corrected = _planned(line_up=_singles(ana, bo), at=_ago(days=3))
    corrected.state_result(by=ana, score=_score((6, 4)), occurred_at=_ago(hours=30))
    corrected.state_result(by=ana, score=_score((7, 5)), occurred_at=_ago(hours=20))
    countered = _planned(line_up=_singles(ana, bo), at=_ago(days=3))
    countered.state_result(by=ana, score=_score((6, 4)), occurred_at=_ago(hours=30))
    countered.state_result(by=bo, score=_score((4, 6)), occurred_at=_ago(hours=7))
    proposed_long_ago = _planned(line_up=_singles(ana, bo), at=_ago(days=5))
    proposed_long_ago.state_result(
        by=ana, score=_score((6, 1)), occurred_at=_ago(days=4)
    )
    unscored = _planned(line_up=_singles(ana, bo), at=_ago(hours=5))
    for game in (corrected, countered, proposed_long_ago, unscored):
        await _saved(session, game)
    asked = [game.id for game in (corrected, countered, proposed_long_ago, unscored)]

    lately = await port.scored_since(asked, since=_ago(days=1))

    assert lately == {corrected.id, countered.id}
    assert await port.scored_since([unscored.id], since=_ago(days=30)) == set()
    assert await port.scored_since([], since=_ago(days=30)) == set()


@pytest.mark.parametrize("implementation", registered(ScoredGames))
async def test_only_the_games_asked_about_are_named(implementation, session):
    port = implementation.build(session)
    ana, bo = new_uuid(), new_uuid()
    asked = _planned(line_up=_singles(ana, bo), at=_ago(hours=6))
    asked.state_result(by=ana, score=_score((6, 4)), occurred_at=_ago(hours=5))
    other = _planned(line_up=_singles(ana, bo), at=_ago(hours=6))
    other.state_result(by=ana, score=_score((6, 4)), occurred_at=_ago(hours=5))
    await _saved(session, asked)
    await _saved(session, other)

    assert await port.scored_since([asked.id], since=_ago(days=1)) == {asked.id}


# ---------------------------------------------------------------------------
# PlayedTogetherQuery — who has shared a court that was played (#831)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlayedTogetherQuery))
async def test_the_pairs_are_the_people_asked_about_on_one_court_played(
    implementation, session
):
    """A counted game and a friendly alike — meeting is not evidence about a
    Level — and only pairs of the people asked about: a stranger on the court
    is nobody's pair here."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    ana, bo, cy, dee, eve, stranger = (new_uuid() for _ in range(6))

    counted = _planned(line_up=_singles(ana, bo), at=_ago(days=3))
    counted.state_result(by=ana, score=_score((6, 4)), occurred_at=_ago(days=2))
    friendly = _planned(
        line_up=_four(cy, dee, eve, stranger), at=_ago(days=3), kind=GameKind.FRIENDLY
    )
    friendly.state_result(by=cy, score=_score((6, 1)), occurred_at=_ago(days=2))
    for game in (counted, friendly):
        await _saved(session, game)
    assert counted.was_played_at(now) and friendly.was_played_at(now)

    pairs = await port.played_together_among([ana, bo, cy, dee, eve], now=now)

    assert pairs == {
        frozenset({ana, bo}),
        frozenset({cy, dee}),
        frozenset({cy, eve}),
        frozenset({dee, eve}),
    }
    assert await port.played_together_among([ana], now=now) == frozenset()
    assert await port.played_together_among([], now=now) == frozenset()


@pytest.mark.parametrize("implementation", registered(PlayedTogetherQuery))
async def test_a_court_that_was_never_played_puts_nobody_together(
    implementation, session
):
    """Still ahead, called off, started short — and a leaver was never on the
    court with the people who stayed."""

    port = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    ana, bo, cy, dee = (new_uuid() for _ in range(4))

    ahead = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.FRIENDLY,
        window=None,
        line_up=_singles(ana, bo),
        occurred_at=_ago(days=1),
        starts_at=instant(now + timedelta(days=2)),
    )
    called_off = _called_off(
        line_up=_four(ana, bo, cy, dee), at=_ago(days=3), leaver=dee, caller=ana
    )
    left, stayed, leaver = await _a_game_somebody_left(session, at=_ago(days=30))
    for game in (ahead, called_off):
        await _saved(session, game)
    assert not any(game.was_played_at(now) for game in (ahead, called_off, left))

    assert await port.played_together_among([ana, bo, cy, dee], now=now) == frozenset()
    assert await port.played_together_among([stayed, leaver], now=now) == frozenset()

    # Played since: the read after it pairs the two.
    ahead_played = _planned(line_up=_singles(ana, bo), at=_ago(days=3))
    ahead_played.state_result(by=bo, score=_score((7, 5)), occurred_at=_ago(days=2))
    await _saved(session, ahead_played)
    assert await port.played_together_among([ana, bo, cy], now=now) == {
        frozenset({ana, bo})
    }

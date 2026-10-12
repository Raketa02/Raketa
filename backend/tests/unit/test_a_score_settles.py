"""A score is asked once, and settled by one tap or by silence (#654;
``docs/adr/0195`` §5).

Tuesday 13 Oct, a Competitive padel game at Bonarka Arena, 19:00–20:00. Marta
and Ivan on side A, Oscar and Paula on side B.

- **No score before the hour**, and **corrections end with the entry window**.
- ***That's right* settles at once and closes the game**: one tap from across
  the net, and no different score is taken after it. The six-hour grace is
  gone.
- **Two scores standing when the answer window closes**: the same winner counts
  with the **closer** score; different winners end **disputed**, and the two
  who put them up are the ones left in dispute.
- **For fun asks nothing**: a score stated on one settles at once.
- **Silence** still settles a lone score a day after it went up.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import Sport, instant
from app.modules.games.domain.errors import (
    CorrectionsHaveClosed,
    TheGameHasNotStarted,
    TheResultIsSettled,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Outcome, Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.modules.games.domain.windows import PROPOSAL_WINDOW
from app.shared.ids import new_uuid

MARTA, IVAN, OSCAR, PAULA = (new_uuid() for _ in range(4))
BOOKED_AT = instant(datetime(2026, 10, 6, 9, tzinfo=timezone.utc))
#: Tuesday 13 Oct, 19:00 in Kraków.
STARTS_AT = instant(datetime(2026, 10, 13, 17, tzinfo=timezone.utc))
#: 20:05 — the hour over, Marta puts the score up.
STATED_AT = instant(STARTS_AT + timedelta(hours=1, minutes=5))


def _game(*, kind: GameKind = GameKind.COUNTED) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=kind,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=MARTA),
                Seating(side=GameSide.A, player_id=IVAN),
                Seating(side=GameSide.B, player_id=OSCAR),
                Seating(side=GameSide.B, player_id=PAULA),
            )
        ),
        occurred_at=BOOKED_AT,
        starts_at=STARTS_AT,
    )


def _score(*sets: tuple[int, int]) -> Score:
    return Score.of(SetScore(a=a, b=b) for a, b in sets)


#: 6–4 6–3 to side A: eight games' margin.
A_WINS = _score((6, 4), (6, 3))
#: 7–5 6–4 to side A: four games' margin, the closer of the two.
A_WINS_CLOSER = _score((7, 5), (6, 4))
#: 4–6 3–6 to side B.
B_WINS = _score((4, 6), (3, 6))


def _replayed(game: Game) -> Game:
    return Game.from_history(game.pull_events())


def _at(minutes: int) -> datetime:
    return instant(STATED_AT + timedelta(minutes=minutes))


# --------------------------------------------------------------------------- #
# The edges of the entry
# --------------------------------------------------------------------------- #


def test_no_score_is_taken_before_the_hour():
    game = _game()

    with pytest.raises(TheGameHasNotStarted):
        game.state_result(
            by=MARTA,
            score=A_WINS,
            occurred_at=instant(STARTS_AT - timedelta(minutes=1)),
        )

    assert game.played_at is None


def test_a_score_is_taken_from_the_first_minute_of_the_hour():
    game = _game()

    game.state_result(by=MARTA, score=A_WINS, occurred_at=STARTS_AT)

    assert game.standing_at(STARTS_AT) is GameStanding.AWAITING_ANSWER


def test_a_correction_is_refused_once_the_entry_window_has_closed():
    """The score went up a minute before the window closed: its answer window
    still runs, but a correction no longer does."""

    game = _game()
    closes = game.entry_closes_at
    game.state_result(
        by=MARTA, score=A_WINS, occurred_at=instant(closes - timedelta(minutes=1))
    )

    with pytest.raises(CorrectionsHaveClosed):
        game.state_result(by=IVAN, score=A_WINS_CLOSER, occurred_at=closes)

    assert game.standing_at(closes) is GameStanding.AWAITING_ANSWER
    assert game.proposals[GameSide.A].score == A_WINS


def test_a_correction_inside_the_entry_window_re_dates_the_score():
    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)

    game.state_result(by=IVAN, score=A_WINS_CLOSER, occurred_at=_at(10))

    assert game.proposals[GameSide.A].score == A_WINS_CLOSER
    assert game.proposals[GameSide.A].at == _at(10)


# --------------------------------------------------------------------------- #
# That's right
# --------------------------------------------------------------------------- #


def test_that_s_right_settles_the_result_at_once():
    """Paula taps *That's right* at 20:10: the result is final at 20:10."""

    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)

    game.accept_result(by=PAULA, occurred_at=_at(5))

    replayed = _replayed(game)
    for one in (game, replayed):
        assert one.standing_at(_at(5)) is GameStanding.CONFIRMED
        assert one.confirmed_at(_at(5)) == _at(5)
        assert one.confirmed_score_at(_at(5)) == A_WINS
        assert one.outcome_for(IVAN, now=_at(5)) is Outcome.WIN
        assert one.outcome_for(OSCAR, now=_at(5)) is Outcome.LOSS


def test_no_different_score_is_taken_after_that_s_right():
    """Oscar's 4–6 3–6 at 22:00 is refused: Paula's agreement closed the game."""

    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.accept_result(by=PAULA, occurred_at=_at(5))

    with pytest.raises(TheResultIsSettled):
        game.state_result(by=OSCAR, score=B_WINS, occurred_at=_at(115))
    with pytest.raises(TheResultIsSettled):
        game.state_result(by=IVAN, score=A_WINS_CLOSER, occurred_at=_at(115))
    with pytest.raises(TheResultIsSettled):
        game.accept_result(by=OSCAR, occurred_at=_at(115))

    assert game.confirmed_score_at(_at(115)) == A_WINS


def test_agreeing_with_a_counter_settles_it_at_once_with_the_counter():
    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.state_result(by=OSCAR, score=A_WINS_CLOSER, occurred_at=_at(10))

    game.accept_result(by=IVAN, occurred_at=_at(20))

    assert game.standing_at(_at(20)) is GameStanding.CONFIRMED
    assert game.confirmed_score_at(_at(20)) == A_WINS_CLOSER
    assert game.confirmed_at(_at(20)) == _at(20)


def test_one_score_per_side_stays_the_cap():
    from app.modules.games.domain.errors import YourSideHasAlreadyAnswered

    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.state_result(by=OSCAR, score=B_WINS, occurred_at=_at(10))

    with pytest.raises(YourSideHasAlreadyAnswered):
        game.state_result(by=PAULA, score=B_WINS, occurred_at=_at(20))
    with pytest.raises(YourSideHasAlreadyAnswered):
        game.state_result(by=IVAN, score=A_WINS_CLOSER, occurred_at=_at(20))


# --------------------------------------------------------------------------- #
# Silence
# --------------------------------------------------------------------------- #


def test_silence_settles_a_lone_score_a_day_after_it_went_up():
    """Had nobody answered, it would be final at 20:05 on Wednesday."""

    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    a_day = instant(STATED_AT + PROPOSAL_WINDOW)

    assert game.standing_at(instant(a_day - timedelta(seconds=1))) is (
        GameStanding.AWAITING_ANSWER
    )
    assert game.standing_at(a_day) is GameStanding.CONFIRMED
    assert game.confirmed_at(a_day) == a_day
    assert game.awaits_agreement_from(OSCAR, now=STATED_AT)
    assert not game.awaits_agreement_from(IVAN, now=STATED_AT)


# --------------------------------------------------------------------------- #
# Two scores, nobody giving way
# --------------------------------------------------------------------------- #


def test_two_scores_naming_the_same_winner_count_with_the_closer_one():
    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.state_result(by=OSCAR, score=A_WINS_CLOSER, occurred_at=_at(30))
    closes = instant(_at(30) + PROPOSAL_WINDOW)

    assert game.standing_at(instant(closes - timedelta(seconds=1))) is (
        GameStanding.AWAITING_ANSWER
    )
    replayed = _replayed(game)
    for one in (game, replayed):
        assert one.standing_at(closes) is GameStanding.CONFIRMED
        assert one.confirmed_score_at(closes) == A_WINS_CLOSER
        assert one.confirmed_at(closes) == closes
        assert one.left_in_dispute_by(closes) == frozenset()


def test_the_closer_score_is_read_off_the_games_won_not_the_sets():
    """6–0 6–0 is twelve games' margin; 6–4 3–6 6–4 is four, though it went to
    three sets."""

    game = _game()
    game.state_result(by=MARTA, score=_score((6, 0), (6, 0)), occurred_at=STATED_AT)
    game.state_result(
        by=OSCAR, score=_score((6, 4), (3, 6), (6, 4)), occurred_at=_at(30)
    )
    closes = instant(_at(30) + PROPOSAL_WINDOW)

    assert game.confirmed_score_at(closes) == _score((6, 4), (3, 6), (6, 4))


def test_two_scores_as_close_as_each_other_count_with_the_first_put_up():
    """6–4 6–3 and 6–3 6–4: both eight games apart. Oscar countered first, so
    his stands — the side that went first, whatever its letter."""

    game = _game()
    game.state_result(by=OSCAR, score=_score((6, 3), (6, 4)), occurred_at=STATED_AT)
    game.state_result(by=MARTA, score=A_WINS, occurred_at=_at(30))
    closes = instant(_at(30) + PROPOSAL_WINDOW)

    assert game.confirmed_score_at(closes) == _score((6, 3), (6, 4))


def test_two_scores_naming_different_winners_end_disputed():
    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.state_result(by=OSCAR, score=B_WINS, occurred_at=_at(30))
    closes = instant(_at(30) + PROPOSAL_WINDOW)

    assert game.standing_at(instant(closes - timedelta(seconds=1))) is (
        GameStanding.AWAITING_ANSWER
    )
    replayed = _replayed(game)
    for one in (game, replayed):
        assert one.standing_at(closes) is GameStanding.DISPUTED
        assert one.confirmed_score_at(closes) is None
        assert one.confirmed_at(closes) is None
        assert one.outcome_for(MARTA, now=closes) is None
        assert one.left_in_dispute_by(closes) == frozenset({MARTA, OSCAR})
    assert GameStanding.DISPUTED in SETTLED
    assert GameStanding.DISPUTED in PLAYED, "they played, and said so"


def test_nobody_is_left_in_dispute_before_the_answer_window_closes():
    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.state_result(by=OSCAR, score=B_WINS, occurred_at=_at(30))

    assert game.left_in_dispute_by(_at(31)) == frozenset()


def test_a_disputed_game_takes_nothing_more():
    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.state_result(by=OSCAR, score=B_WINS, occurred_at=_at(30))
    closes = instant(_at(30) + PROPOSAL_WINDOW)

    with pytest.raises(TheResultIsSettled):
        game.accept_result(by=PAULA, occurred_at=closes)


def test_the_side_that_corrected_is_left_in_dispute_by_whoever_corrected():
    """Ivan's correction is the score that stands for side A, so Ivan — not
    Marta — is the one who put it up."""

    game = _game()
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)
    game.state_result(by=IVAN, score=A_WINS_CLOSER, occurred_at=_at(5))
    game.state_result(by=PAULA, score=B_WINS, occurred_at=_at(30))
    closes = instant(_at(30) + PROPOSAL_WINDOW)

    assert game.left_in_dispute_by(closes) == frozenset({IVAN, PAULA})


# --------------------------------------------------------------------------- #
# For fun
# --------------------------------------------------------------------------- #


def test_a_for_fun_score_settles_at_once_and_asks_nobody():
    game = _game(kind=GameKind.FRIENDLY)

    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)

    replayed = _replayed(game)
    for one in (game, replayed):
        assert one.standing_at(STATED_AT) is GameStanding.CONFIRMED
        assert one.confirmed_score_at(STATED_AT) == A_WINS
        assert one.confirmed_at(STATED_AT) == STATED_AT
        assert not any(
            one.awaits_agreement_from(player, now=STATED_AT)
            for player in (MARTA, IVAN, OSCAR, PAULA)
        )
        assert one.score_put_to_a_side_at(_at(60 * 25)) is None, (
            "nobody was asked, so nobody stayed silent"
        )


def test_a_for_fun_score_takes_no_answer_after_it():
    game = _game(kind=GameKind.FRIENDLY)
    game.state_result(by=MARTA, score=A_WINS, occurred_at=STATED_AT)

    with pytest.raises(TheResultIsSettled):
        game.state_result(by=OSCAR, score=B_WINS, occurred_at=_at(1))
    with pytest.raises(TheResultIsSettled):
        game.accept_result(by=OSCAR, occurred_at=_at(1))


def test_a_for_fun_score_is_not_taken_before_the_hour_either():
    game = _game(kind=GameKind.FRIENDLY)

    with pytest.raises(TheGameHasNotStarted):
        game.state_result(
            by=MARTA,
            score=A_WINS,
            occurred_at=instant(STARTS_AT - timedelta(minutes=1)),
        )

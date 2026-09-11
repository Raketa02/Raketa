"""What counts as answering a score, and what counts as silence.

**The rule this file guards is the one the strand was struck over.** *Confirms
results* counted agreements, so ignoring a lone score and agreeing with it
produced the same outcome, and the only games that ended unconfirmed were the
ones where two people put different scores up and neither gave way — which docks
both sides of every honest disagreement (``docs/adr/0137``). *Answers about
results* counts **answers**: a counter is as good as an acceptance, and the only
miss is silence until the window closes (``docs/adr/0160``).

It is driven through the aggregate's own acts rather than by building
``Proposal`` rows by hand, because *which act was this* is the aggregate's
judgement and a fold tested against a hand-built record would be a fold tested
against a record nobody can reach.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.kernel import Instant, Sport, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.windows import ACCEPTANCE_GRACE, PROPOSAL_WINDOW
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid

PLANNED_AT = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))
PLAYED_AT = instant(PLANNED_AT + timedelta(days=1))

OPENER = UUID("00000001-0000-0000-0000-000000000000")
ASKED = UUID("00000002-0000-0000-0000-000000000000")


def _score(*sets: tuple[int, int]) -> Score:
    return Score.of(SetScore(a=a, b=b) for a, b in sets)


def _game() -> Game:
    """A singles game, ``OPENER`` on side A and ``ASKED`` across the net."""

    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=OPENER),
                Seating(side=GameSide.B, player_id=ASKED),
            )
        ),
        occurred_at=PLANNED_AT,
    )


def _put(game: Game, *, at: Instant = PLAYED_AT) -> Game:
    """``OPENER`` says *we played, here is the score*."""

    game.state_result(by=OPENER, score=_score((6, 4), (6, 3)), occurred_at=at)
    return game


def _asked_about(game: Game, *, now: Instant):
    return game.score_put_to_a_side_at(now)


def test_accepting_is_answering():
    """A tap that agrees is an answer, and it closes the opportunity there."""

    game = _put(_game())
    accepted_at = instant(PLAYED_AT + timedelta(hours=2))
    game.accept_result(by=ASKED, occurred_at=accepted_at)

    asked = _asked_about(game, now=instant(accepted_at + timedelta(days=30)))

    assert asked is not None
    assert (asked.side, asked.answered, asked.closed_at) == (
        GameSide.B,
        True,
        accepted_at,
    )


def test_countering_is_answering_and_disagreeing_costs_nothing():
    """**The whole point of the strand.**

    A player who believes the score is wrong says so, and the platform records
    that they answered. A strand counting agreements would have docked them for
    the one act this product wants them to feel free to make.
    """

    game = _put(_game())
    countered_at = instant(PLAYED_AT + timedelta(hours=3))
    game.state_result(by=ASKED, score=_score((4, 6), (3, 6)), occurred_at=countered_at)

    asked = _asked_about(game, now=instant(countered_at + timedelta(days=30)))

    assert asked is not None
    assert (asked.side, asked.answered, asked.closed_at) == (
        GameSide.B,
        True,
        countered_at,
    )


def test_silence_until_the_window_closes_is_the_miss():
    """Nothing was said, the day ran out, and the moment is the deadline.

    Dating it from the score going up would age a record faster than the record
    aged — the same rule a ghost is dated by.
    """

    game = _put(_game())
    closes = instant(PLAYED_AT + PROPOSAL_WINDOW)

    asked = _asked_about(game, now=closes)

    assert asked is not None
    assert (asked.side, asked.answered, asked.closed_at) == (GameSide.B, False, closes)


def test_a_score_still_inside_its_window_is_in_neither_half():
    """The answer is still wanted, so no conclusion has been reached about it."""

    game = _put(_game())

    still_open = instant(PLAYED_AT + PROPOSAL_WINDOW - timedelta(minutes=1))

    assert _asked_about(game, now=still_open) is None


def test_a_correction_re_dates_the_window_it_opened():
    """The other side is answering a score, and a score they have not seen has
    not started their day."""

    game = _put(_game())
    corrected_at = instant(PLAYED_AT + timedelta(hours=6))
    game.state_result(by=OPENER, score=_score((6, 2),), occurred_at=corrected_at)

    still_open = instant(PLAYED_AT + PROPOSAL_WINDOW + timedelta(minutes=1))
    assert _asked_about(game, now=still_open) is None

    closed = instant(corrected_at + PROPOSAL_WINDOW)
    asked = _asked_about(game, now=closed)
    assert asked is not None and asked.answered is False
    assert asked.closed_at == closed


def test_the_side_that_opened_is_never_asked_about_the_counter():
    """**Nobody is docked for holding their position.**

    Once both sides have put a score up the argument is capped: the opener may
    only give way, and pricing that would price surrender. So the counter is the
    other side's *answer* and never a second question — there is one opportunity
    in this game and it belongs to the side that was asked.
    """

    game = _put(_game())
    countered_at = instant(PLAYED_AT + timedelta(hours=3))
    game.state_result(by=ASKED, score=_score((4, 6), (3, 6)), occurred_at=countered_at)

    long_after = instant(countered_at + timedelta(days=30))
    asked = _asked_about(game, now=long_after)

    assert asked is not None and asked.side is GameSide.B


def test_a_plan_nobody_claimed_puts_no_score_to_anybody():
    """There is no score, so there is no question, so there is no opportunity."""

    assert _asked_about(_game(), now=instant(PLANNED_AT + timedelta(days=30))) is None


def test_an_acceptance_inside_the_grace_is_still_an_answer():
    """The grace decides when a result **settles**, never whether somebody spoke.

    An acceptance that a counter later voids still happened, and the person who
    made it answered the score put in front of them.
    """

    game = _put(_game())
    accepted_at = instant(PLAYED_AT + timedelta(minutes=5))
    game.accept_result(by=ASKED, occurred_at=accepted_at)

    inside = instant(accepted_at + ACCEPTANCE_GRACE - timedelta(minutes=1))
    asked = _asked_about(game, now=inside)

    assert asked is not None and asked.answered is True
    assert asked.closed_at == accepted_at

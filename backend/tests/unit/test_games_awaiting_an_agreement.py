"""Whose agreement a score on the table waits on — Home's *result to confirm*
(#542; the mechanics §3).

It is driven through the aggregate's own acts rather than by building
``Proposal`` rows by hand, because *which act was this* is the aggregate's
judgement and a fold tested against a hand-built record would be a fold tested
against a record nobody can reach.

**What answering a score is worth on a record went with *answers about results***
(#659; ``docs/adr/0195`` §1): silence on a score costs nothing, so the fold that
filed it as a miss — and its tests — are gone. What a score still waits on is
what Home asks.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.kernel import Instant, Sport, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.windows import PROPOSAL_WINDOW
from app.modules.player_profile.domain.weekly_hours import Window
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


# --------------------------------------------------------------------------- #
# Whose agreement a score waits on — Home's *result to confirm* (#542)
# --------------------------------------------------------------------------- #


def test_a_score_waits_on_the_other_side_and_never_on_its_own():
    game = _put(_game())
    now = instant(PLAYED_AT + timedelta(hours=1))

    assert game.awaits_agreement_from(ASKED, now=now)
    assert not game.awaits_agreement_from(OPENER, now=now)


def test_two_scores_on_the_table_wait_on_both_sides():
    game = _put(_game())
    countered_at = instant(PLAYED_AT + timedelta(hours=1))
    game.state_result(by=ASKED, score=_score((4, 6), (3, 6)), occurred_at=countered_at)
    now = instant(countered_at + timedelta(hours=1))

    assert game.awaits_agreement_from(ASKED, now=now)
    assert game.awaits_agreement_from(OPENER, now=now)


def test_an_agreement_waits_on_nobody():
    """It settled the result at once (#654): there is nothing left to answer."""

    game = _put(_game())
    accepted_at = instant(PLAYED_AT + timedelta(hours=1))
    game.accept_result(by=ASKED, occurred_at=accepted_at)
    now = instant(accepted_at + timedelta(minutes=5))

    assert not game.awaits_agreement_from(ASKED, now=now)
    assert not game.awaits_agreement_from(OPENER, now=now)


def test_nothing_waits_before_a_score_or_after_the_result_settles_or_off_the_court():
    game = _game()
    assert not game.awaits_agreement_from(ASKED, now=PLAYED_AT)

    _put(game)
    settled = instant(PLAYED_AT + PROPOSAL_WINDOW + timedelta(minutes=1))
    assert not game.awaits_agreement_from(ASKED, now=settled)
    assert not game.awaits_agreement_from(new_uuid(), now=PLAYED_AT)

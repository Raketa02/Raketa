"""The ranking's fold and its card, at the domain's own seam (#768;
``docs/adr/0203`` §1–§3)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import Instant, Sport, instant
from app.modules.rankings.domain.ranking import (
    LISTED_FOR,
    CardState,
    LevelMove,
    Outcome,
    RatingHistory,
    card_of,
    latest_of,
    level_of,
    row_of,
)
from app.shared.ids import new_uuid

WIN, LOSS = Outcome.WIN, Outcome.LOSS

START = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))


def at(hours: int) -> Instant:
    return instant(START + timedelta(hours=hours))


def history(*moves: tuple[float, bool], initial: float = 2.5) -> RatingHistory:
    """Moves an hour apart, from the questionnaire at hour 0."""

    return RatingHistory(
        player_id=new_uuid(),
        sport=Sport.PADEL,
        initial_mu=initial,
        initialised_at=START,
        moves=tuple(
            LevelMove(
                game_id=new_uuid(), won=won, mu=mu, sigma=0.3 - hour / 100, at=at(hour)
            )
            for hour, (mu, won) in enumerate(moves, start=1)
        ),
    )


def test_no_result_makes_no_row():
    assert row_of(history()) is None


def test_the_row_holds_the_last_move_and_the_last_five_oldest_first():
    row = row_of(
        history(
            (2.55, True),
            (2.6, True),
            (2.58, False),
            (2.63, True),
            (2.6, False),
            (2.66, True),
        )
    )

    assert row is not None
    assert (row.hundredths, level_of(row.hundredths), row.results) == (266, 2.66, 6)
    assert row.sigma == pytest.approx(0.24)
    assert row.last_result_at == at(6)
    assert row.form == (WIN, LOSS, WIN, LOSS, WIN)
    assert row.friends_entered_at == at(1)
    assert row.general_entered_at == at(5)


def test_fewer_than_five_have_not_entered_general():
    row = row_of(history((2.55, True), (2.6, True)))

    assert row is not None
    assert (row.general_entered_at, row.form) == (None, (WIN, WIN))


def test_the_level_is_reached_when_it_last_took_its_value():
    """2,60 at hour 2, away at hour 3, back at hour 4: reached at hour 4. A move
    that leaves it at 2,60 reaches nothing new."""

    row = row_of(
        history((2.55, True), (2.6, True), (2.58, False), (2.6, True), (2.6, False))
    )

    assert row is not None
    assert row.level_reached_at == at(4)


def test_a_first_move_that_leaves_the_level_where_the_questionnaire_put_it():
    row = row_of(history((2.5, True), initial=2.5))

    assert row is not None
    assert row.level_reached_at == START


def test_the_level_is_compared_at_two_decimals():
    row = row_of(history((2.6049, True)))

    assert row is not None
    assert row.hundredths == 260


def test_listed_is_five_results_and_a_last_one_inside_the_ninety_days():
    row = row_of(history(*((2.6, True) for _ in range(5))))
    assert row is not None
    last = row.last_result_at

    assert row.listed_on_general(instant(last + timedelta(days=89, hours=23)))
    assert not row.listed_on_general(instant(last + LISTED_FOR))
    four = row_of(history(*((2.6, True) for _ in range(4))))
    assert four is not None and not four.listed_on_general(last)


@pytest.mark.parametrize(
    ("results", "days_ago", "expected"),
    [
        (0, 0, CardState.NEEDS_RESULTS),
        (3, 0, CardState.NEEDS_RESULTS),
        (3, 91, CardState.NEEDS_RESULTS),
        (5, 91, CardState.OFF_THE_LIST),
        (5, 0, CardState.LISTED),
    ],
)
def test_the_card(results, days_ago, expected):
    row = row_of(history(*((2.6, True) for _ in range(results))))
    now = instant(at(results) + timedelta(days=days_ago))
    listed = row is not None and row.listed_on_general(now)

    card = card_of(row, holds_a_level=True, place=1 if listed else None, of=1, now=now)

    assert card.state is expected
    assert card.results == results


def test_no_level_comes_before_everything():
    assert card_of(None, holds_a_level=False, place=None, of=3, now=START).state is (
        CardState.NO_LEVEL
    )


def test_the_trophy_follows_the_latest_result():
    padel = row_of(history((2.6, True), (2.7, True)))
    tennis_history = history((3.0, True))
    tennis = row_of(
        RatingHistory(
            player_id=tennis_history.player_id,
            sport=Sport.TENNIS,
            initial_mu=3.0,
            initialised_at=START,
            moves=tennis_history.moves,
        )
    )
    assert padel is not None and tennis is not None

    assert latest_of((padel, tennis)) is padel
    assert latest_of(()) is None


def test_the_last_result_is_the_latest_to_settle_whatever_the_stream_order():
    """The catch-up and the outbox may apply two results a minute out of order:
    the 90 days run from the latest settling instant."""

    ordered = history((2.55, True), (2.6, True))
    late_first = RatingHistory(
        player_id=ordered.player_id,
        sport=ordered.sport,
        initial_mu=ordered.initial_mu,
        initialised_at=ordered.initialised_at,
        moves=(ordered.moves[1], ordered.moves[0]),
    )

    row = row_of(late_first)

    assert row is not None
    assert row.last_result_at == at(2)

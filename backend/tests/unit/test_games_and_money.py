"""A player's Games & money — how many games a week, and the most one may cost
(#539; the mechanics §6.6, §17.1; the screens A7.1).

Three families. **Born by being used**: a player who never opened the screen is
at the defaults — two games a week, every card shown — and nothing is written
until they change something. **The form's bounds are the domain's**: a week of
one to seven games, and a ceiling of *off*, 35, 45 or 60 zł, each refused with a
code naming what is offered. **A preference, so the same answer records
nothing**, as a Play intent re-declared records nothing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.kernel import instant
from app.modules.proposals.domain.errors import (
    GamesPerWeekOutOfRange,
    MostIllPayNotOffered,
)
from app.modules.proposals.domain.events import GamesAndMoneySet
from app.modules.proposals.domain.games_and_money import (
    DEFAULT_GAMES_PER_WEEK,
    GAMES_PER_WEEK,
    MOST_ILL_PAY_CHOICES_GROSZE,
    GamesAndMoney,
)

AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
PLAYER = uuid4()


def test_a_player_who_never_chose_is_at_two_games_and_every_card():
    unwritten = GamesAndMoney.from_history(PLAYER, [])

    assert unwritten.games_per_week == DEFAULT_GAMES_PER_WEEK == 2
    assert unwritten.most_ill_pay_grosze is None
    assert unwritten.version == 0
    assert unwritten.shows(share_grosze=1_000_00)


def test_the_form_offers_one_to_seven_games_and_three_ceilings():
    assert GAMES_PER_WEEK == (1, 7)
    assert MOST_ILL_PAY_CHOICES_GROSZE == (35_00, 45_00, 60_00)


def test_a_change_is_recorded_and_folds_back():
    settings = GamesAndMoney.from_history(PLAYER, [])

    settings.set(games_per_week=4, most_ill_pay_grosze=45_00, at=AT)

    events = settings.pull_events()
    assert events == [
        GamesAndMoneySet(
            player_id=PLAYER,
            games_per_week=4,
            most_ill_pay_grosze=45_00,
            occurred_at=AT,
        )
    ]
    folded = GamesAndMoney.from_history(PLAYER, events)
    assert (folded.games_per_week, folded.most_ill_pay_grosze) == (4, 45_00)
    assert folded.version == 1


def test_the_same_answer_records_nothing():
    settings = GamesAndMoney.from_history(
        PLAYER,
        [
            GamesAndMoneySet(
                player_id=PLAYER,
                games_per_week=3,
                most_ill_pay_grosze=None,
                occurred_at=AT,
            )
        ],
    )

    settings.set(games_per_week=3, most_ill_pay_grosze=None, at=AT)

    assert settings.pull_events() == []


def test_the_defaults_chosen_on_a_fresh_account_record_nothing():
    settings = GamesAndMoney.from_history(PLAYER, [])

    settings.set(games_per_week=2, most_ill_pay_grosze=None, at=AT)

    assert settings.pull_events() == []


@pytest.mark.parametrize("games", [0, 8, -1])
def test_a_week_outside_one_to_seven_is_refused_naming_the_range(games):
    settings = GamesAndMoney.from_history(PLAYER, [])

    with pytest.raises(GamesPerWeekOutOfRange) as refused:
        settings.set(games_per_week=games, most_ill_pay_grosze=None, at=AT)

    assert refused.value.details == {"least": 1, "most": 7}
    assert settings.pull_events() == []


@pytest.mark.parametrize("ceiling", [0, 40_00, 35_01, 100_00])
def test_a_ceiling_the_form_does_not_offer_is_refused_naming_the_choices(ceiling):
    settings = GamesAndMoney.from_history(PLAYER, [])

    with pytest.raises(MostIllPayNotOffered) as refused:
        settings.set(games_per_week=2, most_ill_pay_grosze=ceiling, at=AT)

    assert refused.value.details == {"choices": [35_00, 45_00, 60_00]}
    assert settings.pull_events() == []


def test_a_card_above_the_ceiling_is_not_shown_and_one_at_it_is():
    settings = GamesAndMoney.from_history(PLAYER, [])
    settings.set(games_per_week=2, most_ill_pay_grosze=35_00, at=AT)

    assert settings.shows(share_grosze=35_00)
    assert settings.shows(share_grosze=20_00)
    assert not settings.shows(share_grosze=35_01)


def test_switching_the_ceiling_off_shows_every_card_again():
    settings = GamesAndMoney.from_history(PLAYER, [])
    settings.set(games_per_week=2, most_ill_pay_grosze=35_00, at=AT)

    settings.set(games_per_week=2, most_ill_pay_grosze=None, at=AT)

    assert settings.most_ill_pay_grosze is None
    assert settings.shows(share_grosze=99_00)
    assert len(settings.pull_events()) == 2

"""The card's own rules — the ones the route walk would not localise.

Everything here is about what may be *on* a card, which is a question with no I/O
in it. The route test beside it asserts the life of a card: when it may be
answered, that answering closes it, and that nothing ever reads one back.

Two of these could plausibly have gone the other way, which is why they are
pinned rather than left to review: **rating yourself** is refused by the same rule
that refuses a stranger rather than by a rule of its own, and **an empty card** is
a legal card rather than a request to do nothing.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.kernel import InvariantViolated, instant
from app.modules.sportsmanship.domain.card import (
    MAXIMUM_STARS,
    MINIMUM_STARS,
    SettledCourt,
    SportsmanshipCard,
    StarsGiven,
)
from app.modules.sportsmanship.domain.errors import (
    StarsAreOneToFive,
    TheyWereNotOnThisCourt,
    YouRatedTheSamePersonTwice,
)

from datetime import datetime, timezone

NOW = instant(datetime(2026, 9, 8, 19, 0, tzinfo=timezone.utc))


def a_doubles_court() -> tuple[SettledCourt, tuple]:
    """One rater and the three other people on their court: two opponents and a
    partner, which this context does not tell apart."""

    rater = uuid4()
    others = (uuid4(), uuid4(), uuid4())
    return SettledCourt(game_id=uuid4(), rater_id=rater, others=others), others


def test_a_card_carries_stars_for_the_other_players_on_the_court():
    court, (partner, one, two) = a_doubles_court()

    card = SportsmanshipCard.answered(
        court=court,
        given=[
            StarsGiven(subject_id=partner, stars=5),
            StarsGiven(subject_id=one, stars=3),
            StarsGiven(subject_id=two, stars=1),
        ],
        at=NOW,
    )

    assert card.game_id == court.game_id
    assert card.rater_id == court.rater_id
    assert card.answered_at == NOW
    assert {one.subject_id: one.stars for one in card.given} == {
        partner: 5,
        one: 3,
        two: 1,
    }


def test_a_blank_is_an_absence_and_leaves_nothing_behind():
    """**The omission is not recorded**, and this is the shape that makes that
    true: somebody left blank is simply not on the card, so there is no row with
    a null in it for a later reader to interpret."""

    court, (partner, one, _two) = a_doubles_court()

    card = SportsmanshipCard.answered(
        court=court,
        given=[StarsGiven(subject_id=one, stars=4)],
        at=NOW,
    )

    assert [given.subject_id for given in card.given] == [one]
    assert partner not in {given.subject_id for given in card.given}


def test_a_card_with_nobody_on_it_is_still_an_answer():
    """*I am not rating anyone* takes the ordinary path. There is no branch for
    it, which is what stops it being the case somebody forgets."""

    court, _ = a_doubles_court()

    card = SportsmanshipCard.answered(court=court, given=[], at=NOW)

    assert card.given == ()
    assert card.answered_at == NOW


def test_a_singles_court_offers_the_one_opponent():
    rater, opponent = uuid4(), uuid4()
    court = SettledCourt(game_id=uuid4(), rater_id=rater, others=(opponent,))

    card = SportsmanshipCard.answered(
        court=court, given=[StarsGiven(subject_id=opponent, stars=4)], at=NOW
    )

    assert [given.subject_id for given in card.given] == [opponent]


def test_stars_for_somebody_who_was_not_there_are_refused():
    court, _ = a_doubles_court()

    with pytest.raises(TheyWereNotOnThisCourt):
        SportsmanshipCard.answered(
            court=court, given=[StarsGiven(subject_id=uuid4(), stars=5)], at=NOW
        )


def test_rating_yourself_is_the_same_refusal_and_not_one_of_its_own():
    """One rule — *everybody else on the court* — and the rater is not among
    them. A second class here would be a second place for that to be true."""

    court, _ = a_doubles_court()

    with pytest.raises(TheyWereNotOnThisCourt):
        SportsmanshipCard.answered(
            court=court,
            given=[StarsGiven(subject_id=court.rater_id, stars=5)],
            at=NOW,
        )


def test_one_card_carries_one_answer_about_each_person():
    court, (partner, _one, _two) = a_doubles_court()

    with pytest.raises(YouRatedTheSamePersonTwice):
        SportsmanshipCard.answered(
            court=court,
            given=[
                StarsGiven(subject_id=partner, stars=5),
                StarsGiven(subject_id=partner, stars=1),
            ],
            at=NOW,
        )


@pytest.mark.parametrize("stars", [0, -1, 6, 100])
def test_a_star_count_off_the_scale_is_refused(stars: int):
    """**No zero and no sixth star.** Refused rather than clamped: a clamp would
    turn somebody's client bug into an opinion they did not hold."""

    with pytest.raises(StarsAreOneToFive):
        StarsGiven(subject_id=uuid4(), stars=stars)


@pytest.mark.parametrize("stars", range(MINIMUM_STARS, MAXIMUM_STARS + 1))
def test_every_whole_star_on_the_scale_is_a_rating(stars: int):
    assert StarsGiven(subject_id=uuid4(), stars=stars).stars == stars


def test_a_court_that_offers_the_rater_themselves_is_a_broken_precondition():
    """An ``invariant`` and not a refusal, deliberately: nobody types a court.
    It is folded from a line-up, so one that seats the rater among the others is
    this platform's own bug and not somebody's tap."""

    rater = uuid4()

    with pytest.raises(InvariantViolated):
        SettledCourt(game_id=uuid4(), rater_id=rater, others=(rater,))


def test_a_court_with_nobody_else_on_it_is_a_broken_precondition():
    with pytest.raises(InvariantViolated):
        SettledCourt(game_id=uuid4(), rater_id=uuid4(), others=())

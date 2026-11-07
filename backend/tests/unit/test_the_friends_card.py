"""The friends card's rules that need no I/O (#750; ``docs/adr/0202`` §5; the
friends mechanics §7.3–§7.6): the line-up the sport seats, the evenest sides of
a fixed four or the sides sent, and every court the four could take, with the
one the card proposes.

**Tomek seats Ewa, Magda and Ania** on Ogrody 33 Club's Friends tab. Ogrody 33
is the group's club; Wisła Park, 4 km away, is offered only at an hour Ogrody
33 is full. The clock stands on Monday 5 October 2026, 08:00 in Kraków.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.engines.matchfit.scorable import LevelReading
from app.kernel import Instant, Sport, instant
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.deck import CardForecast, Sides
from app.modules.proposals.domain.errors import (
    SidesNotOfTheLineUp,
    WrongLineUpSize,
)
from app.modules.proposals.domain.friends_card import (
    courts_for,
    line_up_of,
    proposed_court,
    the_sides,
    ways_to_stand,
)
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.proposer import (
    CourtHourOnSale,
    CourtOnSale,
    Member,
    PoolClubs,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int) -> Instant:
    """An hour in Kraków in October 2026. The fifth is a Monday."""

    return instant(datetime(2026, 10, day, hour, tzinfo=WARSAW))


NOW = warsaw(5, 8)
SAT_10 = warsaw(10, 10)
TUE_21 = warsaw(6, 21)
WED_19 = warsaw(7, 19)

TOMEK, EWA, MAGDA, ANIA = (uuid4() for _ in range(4))
OGRODY, WISLA_PARK = uuid4(), uuid4()
#: An official group's clubs: Wisła Park only where Ogrody 33 is full.
OFFICIAL = PoolClubs(
    home_club_id=OGRODY, others=(WISLA_PARK,), others_only_when_home_is_full=True
)

SATURDAY_MORNING = ((6, 10),)
TUESDAY_NIGHT = ((2, 21),)


def member(
    player: UUID,
    *,
    cells: tuple[tuple[int, int], ...] = (*SATURDAY_MORNING, *TUESDAY_NIGHT),
    games_per_week: int = 2,
    booked: tuple[Instant, ...] = (),
) -> Member:
    return Member(
        player_id=player,
        level=LevelReading(mu=2.7, sigma=0.4),
        week=WeeklyHours.edited(cells),
        wants=frozenset(),
        limits=GamesAndMoney(
            player_id=player, games_per_week=games_per_week, most_ill_pay_grosze=None
        ),
        booked=booked,
    )


def court(name: str) -> CourtOnSale:
    return CourtOnSale(court_id=uuid4(), name=name, indoor=True)


def on_sale(start: Instant, club: UUID, *courts: CourtOnSale) -> CourtHourOnSale:
    return CourtHourOnSale(
        club_id=club,
        sport=Sport.PADEL,
        start=start,
        courts=len(courts),
        share_grosze=25_00,
        book_by=start - timedelta(days=1),
        free=courts,
    )


def the_four(**weeks) -> list[Member]:
    return [
        member(player, **weeks.get(name, {}))
        for name, player in (
            ("tomek", TOMEK),
            ("ewa", EWA),
            ("magda", MAGDA),
            ("ania", ANIA),
        )
    ]


def pct(value: int) -> CardForecast:
    return CardForecast(pct=value, provisional=False)


# --------------------------------------------------------------------------- #
# The line-up the sport seats
# --------------------------------------------------------------------------- #


def test_doubles_seats_three_friends_and_singles_one():
    doubles = line_up_of(TOMEK, [EWA, MAGDA, ANIA], sport=Sport.PADEL)
    singles = line_up_of(TOMEK, [EWA], sport=Sport.TENNIS)

    assert doubles.everybody == (TOMEK, EWA, MAGDA, ANIA)
    assert singles.everybody == (TOMEK, EWA)


@pytest.mark.parametrize(
    "sport, friends",
    [
        (Sport.PADEL, [EWA, MAGDA]),
        (Sport.PADEL, [EWA, MAGDA, ANIA, uuid4()]),
        (Sport.TENNIS, [EWA, MAGDA]),
        # Ewa twice is two friends short of three.
        (Sport.PADEL, [EWA, EWA, MAGDA]),
        # Tomek is the sender, never his own friend.
        (Sport.PADEL, [TOMEK, EWA, MAGDA]),
    ],
)
def test_a_line_up_the_sport_does_not_seat_is_refused(sport, friends):
    with pytest.raises(WrongLineUpSize) as refused:
        line_up_of(TOMEK, friends, sport=sport)

    assert refused.value.details == {"friends": 3 if sport is Sport.PADEL else 1}


# --------------------------------------------------------------------------- #
# The sides
# --------------------------------------------------------------------------- #


def test_a_fixed_four_can_stand_three_ways_with_the_sender_on_his_own_side():
    line_up = line_up_of(TOMEK, [EWA, MAGDA, ANIA], sport=Sport.PADEL)

    assert ways_to_stand(line_up) == (
        Sides(yours=(TOMEK, EWA), theirs=(MAGDA, ANIA)),
        Sides(yours=(TOMEK, MAGDA), theirs=(EWA, ANIA)),
        Sides(yours=(TOMEK, ANIA), theirs=(EWA, MAGDA)),
    )


def test_singles_stands_one_way():
    line_up = line_up_of(TOMEK, [EWA], sport=Sport.TENNIS)

    assert ways_to_stand(line_up) == (Sides(yours=(TOMEK,), theirs=(EWA,)),)


def test_with_no_sides_sent_the_evenest_way_is_drawn():
    line_up = line_up_of(TOMEK, [EWA, MAGDA, ANIA], sport=Sport.PADEL)
    options = ways_to_stand(line_up)

    sides, forecast = the_sides(
        line_up, options, [pct(87), pct(64), pct(71)], partner=None
    )

    assert sides == Sides(yours=(TOMEK, EWA), theirs=(MAGDA, ANIA))
    assert forecast == pct(87)


def test_two_ways_as_even_keep_the_one_named_first():
    line_up = line_up_of(TOMEK, [EWA, MAGDA, ANIA], sport=Sport.PADEL)
    options = ways_to_stand(line_up)

    sides, _ = the_sides(line_up, options, [pct(64), pct(80), pct(80)], partner=None)

    assert sides == Sides(yours=(TOMEK, MAGDA), theirs=(EWA, ANIA))


def test_sides_sent_are_drawn_with_their_own_forecast():
    """Tomek swaps Ewa and Magda: the percentage follows his sides."""

    line_up = line_up_of(TOMEK, [EWA, MAGDA, ANIA], sport=Sport.PADEL)
    options = ways_to_stand(line_up)

    sides, forecast = the_sides(
        line_up, options, [pct(87), pct(64), pct(71)], partner=MAGDA
    )

    assert sides == Sides(yours=(TOMEK, MAGDA), theirs=(EWA, ANIA))
    assert forecast == pct(64)


@pytest.mark.parametrize(
    "sport, friends, partner",
    [
        # Somebody who is not on the court.
        (Sport.PADEL, [EWA, MAGDA, ANIA], uuid4()),
        # Tomek beside himself.
        (Sport.PADEL, [EWA, MAGDA, ANIA], TOMEK),
        # Singles has no partner.
        (Sport.TENNIS, [EWA], EWA),
    ],
)
def test_sides_that_are_not_a_way_the_line_up_stands_are_refused(
    sport, friends, partner
):
    line_up = line_up_of(TOMEK, friends, sport=sport)
    options = ways_to_stand(line_up)

    with pytest.raises(SidesNotOfTheLineUp):
        the_sides(line_up, options, [None] * len(options), partner=partner)


# --------------------------------------------------------------------------- #
# Every court the four could take
# --------------------------------------------------------------------------- #


def rows(courts) -> list[tuple[Instant, UUID, str]]:
    return [(row.start, row.club_id, row.court.name) for row in courts]


def test_every_court_is_listed_by_hour_home_club_first_and_in_the_clubs_order():
    hours = [
        on_sale(TUE_21, WISLA_PARK, court("Court 1")),
        on_sale(TUE_21, OGRODY, court("Court 3"), court("Court 4")),
        on_sale(SAT_10, WISLA_PARK, court("Court 2")),
    ]

    listed = courts_for(the_four(), hours, OFFICIAL, sport=Sport.PADEL, now=NOW)

    # Tuesday 21:00 has a court at Ogrody 33, so Wisła Park is not offered then;
    # on Saturday 10:00 Ogrody 33 is full, and Wisła Park is.
    assert rows(listed) == [
        (TUE_21, OGRODY, "Court 3"),
        (TUE_21, OGRODY, "Court 4"),
        (SAT_10, WISLA_PARK, "Court 2"),
    ]
    assert [row.home_club_full for row in listed] == [False, False, True]
    assert [row.share_grosze for row in listed] == [25_00] * 3


def test_a_row_says_who_is_free_and_who_is_busy_then():
    hours = [on_sale(SAT_10, OGRODY, court("Court 3"))]
    four = the_four(ania={"cells": TUESDAY_NIGHT}, magda={"cells": TUESDAY_NIGHT})

    [row] = courts_for(four, hours, OFFICIAL, sport=Sport.PADEL, now=NOW)

    assert row.free == (TOMEK, EWA)
    assert row.busy == (MAGDA, ANIA)


def test_an_hour_one_of_the_four_has_a_game_at_is_left_out():
    hours = [
        on_sale(TUE_21, OGRODY, court("Court 3")),
        on_sale(SAT_10, OGRODY, court("Court 3")),
    ]
    four = the_four(ania={"booked": (TUE_21,)})

    listed = courts_for(four, hours, OFFICIAL, sport=Sport.PADEL, now=NOW)

    assert rows(listed) == [(SAT_10, OGRODY, "Court 3")]


def test_a_week_one_of_the_four_has_their_games_booked_in_stays():
    """Ewa plays one game a week, and has one on Wednesday: the card still
    offers Saturday, and her Accept is what is refused, with a sentence (call
    5; the mechanics §8.4)."""

    hours = [on_sale(SAT_10, OGRODY, court("Court 3"))]
    four = the_four(ewa={"games_per_week": 1, "booked": (WED_19,)})

    listed = courts_for(four, hours, OFFICIAL, sport=Sport.PADEL, now=NOW)

    assert rows(listed) == [(SAT_10, OGRODY, "Court 3")]


def test_another_sport_past_the_book_by_and_past_fourteen_days_are_left_out():
    tennis = CourtHourOnSale(
        club_id=OGRODY,
        sport=Sport.TENNIS,
        start=SAT_10,
        courts=1,
        share_grosze=40_00,
        book_by=SAT_10 - timedelta(days=1),
        free=(court("Court 9"),),
    )
    closed = CourtHourOnSale(
        club_id=OGRODY,
        sport=Sport.PADEL,
        start=TUE_21,
        courts=1,
        share_grosze=25_00,
        book_by=NOW - timedelta(minutes=1),
        free=(court("Court 3"),),
    )
    too_far = on_sale(warsaw(20, 10), OGRODY, court("Court 3"))

    listed = courts_for(
        the_four(), [tennis, closed, too_far], OFFICIAL, sport=Sport.PADEL, now=NOW
    )

    assert listed == ()


def test_the_soonest_hour_everybody_is_free_is_proposed():
    hours = [
        on_sale(TUE_21, OGRODY, court("Court 3")),
        on_sale(SAT_10, WISLA_PARK, court("Court 2")),
    ]
    # Ania is free on Saturday mornings only.
    four = the_four(ania={"cells": SATURDAY_MORNING})

    listed = courts_for(four, hours, OFFICIAL, sport=Sport.PADEL, now=NOW)

    proposed = proposed_court(listed)
    assert proposed is not None
    assert (proposed.start, proposed.club_id, proposed.court.name) == (
        SAT_10,
        WISLA_PARK,
        "Court 2",
    )


def test_failing_everybody_the_soonest_hour_most_are_free_is_proposed():
    hours = [
        on_sale(TUE_21, OGRODY, court("Court 3")),
        on_sale(WED_19, OGRODY, court("Court 3")),
        on_sale(SAT_10, OGRODY, court("Court 3")),
    ]
    four = the_four(
        tomek={"cells": ((2, 21), (3, 19), (6, 10))},
        ewa={"cells": ((3, 19), (6, 10))},
        magda={"cells": ((3, 19), (6, 10))},
        ania={"cells": ()},
    )

    proposed = proposed_court(
        courts_for(four, hours, OFFICIAL, sport=Sport.PADEL, now=NOW)
    )

    # Three are free on Wednesday and on Saturday: the soonest is Wednesday.
    assert proposed is not None
    assert proposed.start == WED_19
    assert proposed.busy == (ANIA,)


def test_with_no_court_in_fourteen_days_nothing_is_proposed():
    assert proposed_court(()) is None

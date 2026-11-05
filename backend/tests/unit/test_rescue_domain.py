"""Rescues as a reader is offered them — the rules that need no I/O (#545; the
mechanics §8.1–§8.2, §10.1; the screens A2.3, A3.1).

**A seat is offered to every member who fits and is free for the hour**: fits
everybody on the game (the pair rule, the kind's window), wants its kind, is
free for that hour in their week, has no game then, and is within their Games &
money. **The deck deals it only to the best fits** — the offered ones whose
game with them in the seat is forecast most even, three per open seat. **Its
deadline** is the cut-off while that is ahead, then the start.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.deck import CardForecast, CardType, CourtState
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.home import BookedGame, BookingStage, OpenSeat
from app.modules.proposals.domain.rescues import (
    Candidate,
    best_fits,
    card_of_a_rescue,
    offered_to,
    rescue_deadline,
    rescuable,
    sides_for,
)
from app.modules.proposals.domain.overlap import overlap_of
from app.modules.clubs.domain.court_hours import CLUB_ZONE

WARSAW = ZoneInfo("Europe/Warsaw")
OLA, EWA, TOMEK, KUBA = (uuid4() for _ in range(4))
ZOSIA, MAREK, ANIA, PIOTR = (uuid4() for _ in range(4))


def warsaw(day: int, hour: int, minute: int = 0):
    return instant(datetime(2026, 10, day, hour, minute, tzinfo=WARSAW))


#: Saturday 10 October at 17:00 (a Saturday is ISO weekday 6).
START = warsaw(10, 17)
CUT_OFF = warsaw(9, 17)
EVERY_HOUR = WeeklyHours.of_cells(
    (day, hour) for day in range(1, 8) for hour in range(7, 23)
)


def a_rescue(**changes) -> BookedGame:
    """Ola, Ewa and Tomek's game: Kuba left side A on Monday."""

    fields = dict(
        booking_id=uuid4(),
        pool_id=uuid4(),
        club_id=uuid4(),
        court_name="Court 2",
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=30_00,
        first_side=(OLA,),
        second_side=(EWA, TOMEK),
        cut_off=CUT_OFF,
        game_id=uuid4(),
        stage=BookingStage.SEAT_OPEN,
        open=(OpenSeat(side="A", left_by=KUBA, left_at=warsaw(5, 9)),),
        leavers=frozenset({KUBA}),
    )
    fields.update(changes)
    return BookedGame(**fields)


def a_candidate(player=ZOSIA, **changes) -> Candidate:
    fields = dict(
        player_id=player,
        wants=frozenset({SearchMode.COMPETITIVE}),
        week=EVERY_HOUR,
        booked=(),
        limits=GamesAndMoney(player_id=player),
    )
    fields.update(changes)
    return Candidate(**fields)


MONDAY = warsaw(5, 10)


def test_a_seat_is_offered_to_a_member_who_fits_and_is_free_for_the_hour():
    assert offered_to(a_rescue(), a_candidate(), unfit=frozenset(), now=MONDAY)


def test_a_seat_is_not_offered_to_somebody_who_does_not_fit_everybody_on_it():
    unfit = frozenset({frozenset({ZOSIA, EWA})})

    assert not offered_to(a_rescue(), a_candidate(), unfit=unfit, now=MONDAY)


def test_a_seat_is_not_offered_for_a_kind_the_member_does_not_want():
    for_fun = a_candidate(wants=frozenset({SearchMode.FOR_FUN}))
    nothing_declared = a_candidate(wants=frozenset())

    assert not offered_to(a_rescue(), for_fun, unfit=frozenset(), now=MONDAY)
    assert not offered_to(a_rescue(), nothing_declared, unfit=frozenset(), now=MONDAY)


def test_a_seat_kept_for_its_rescuer_is_never_asked_the_kind_again():
    # Q127: a claim made before, like a yes already given, stands whatever
    # the rescuer's intent now says.
    for_fun = a_candidate(wants=frozenset({SearchMode.FOR_FUN}))

    assert offered_to(
        a_rescue(), for_fun, unfit=frozenset(), now=MONDAY, already_kept=True
    )


def test_a_seat_is_not_offered_outside_the_member_s_week_or_at_an_hour_they_play():
    busy_saturday = a_candidate(
        week=WeeklyHours.of_cells((day, 18) for day in range(1, 8))
    )
    booked_then = a_candidate(booked=(START,))

    assert not offered_to(a_rescue(), busy_saturday, unfit=frozenset(), now=MONDAY)
    assert not offered_to(a_rescue(), booked_then, unfit=frozenset(), now=MONDAY)


def test_a_seat_is_not_offered_beyond_the_member_s_games_and_money():
    pricey = a_candidate(
        limits=GamesAndMoney(player_id=ZOSIA, most_ill_pay_grosze=25_00)
    )
    week_full = a_candidate(
        booked=(warsaw(6, 18), warsaw(8, 18)),
        limits=GamesAndMoney(player_id=ZOSIA, games_per_week=2),
    )

    assert not offered_to(a_rescue(), pricey, unfit=frozenset(), now=MONDAY)
    assert not offered_to(a_rescue(), week_full, unfit=frozenset(), now=MONDAY)


def test_a_seat_is_never_offered_to_somebody_on_the_game_or_who_left_it():
    rescue = a_rescue()

    assert not offered_to(rescue, a_candidate(OLA), unfit=frozenset(), now=MONDAY)
    assert not offered_to(rescue, a_candidate(KUBA), unfit=frozenset(), now=MONDAY)


def test_a_seat_stays_until_the_cut_off_then_until_the_start():
    before = a_rescue()
    after = a_rescue(
        open=(OpenSeat(side="A", left_by=KUBA, left_at=warsaw(9, 18)),),
    )
    short = a_rescue(short_from=CUT_OFF)

    assert rescue_deadline(before, now=MONDAY) == CUT_OFF
    assert rescue_deadline(after, now=warsaw(9, 19)) == START
    assert rescuable(after, now=warsaw(10, 16, 59))
    assert not rescuable(after, now=START)
    assert not rescuable(short, now=CUT_OFF)
    assert rescuable(short, now=warsaw(9, 16, 59))


def test_the_reader_sits_on_the_side_of_the_seat_that_opened_first():
    sides = sides_for(a_rescue(), ZOSIA)

    assert (sides.yours, sides.theirs) == ((ZOSIA, OLA), (EWA, TOMEK))


def test_the_best_fits_are_the_most_even_three_a_seat():
    offered = (ZOSIA, MAREK, ANIA, PIOTR)
    forecasts = (
        CardForecast(pct=60, provisional=False),
        CardForecast(pct=90, provisional=False),
        None,
        CardForecast(pct=75, provisional=False),
    )

    assert best_fits(a_rescue(), offered, forecasts) == frozenset({MAREK, PIOTR, ZOSIA})
    two_open = a_rescue(
        first_side=(),
        open=(
            OpenSeat(side="A", left_by=KUBA, left_at=warsaw(5, 9)),
            OpenSeat(side="A", left_by=OLA, left_at=warsaw(5, 10)),
        ),
    )
    assert best_fits(two_open, offered, forecasts) == frozenset(offered)


def test_a_rescue_card_is_a_seat_open_card_on_a_booked_court():
    rescue = a_rescue()
    sides = sides_for(rescue, ZOSIA)

    card = card_of_a_rescue(
        rescue,
        sides=sides,
        forecast=CardForecast(pct=80, provisional=False),
        overlap=overlap_of([EVERY_HOUR] * 4, start=START, zone=CLUB_ZONE),
        now=MONDAY,
    )

    assert card.type is CardType.SEAT_OPEN
    assert card.court is CourtState.BOOKED
    assert card.court_name == "Court 2"
    # Their shares are held until the cut-off, and paid once it took them
    # (#637).
    assert card.paid == ()
    assert card.in_ == ()
    assert card.open_seats_after_your_yes == 0
    assert card.deadline == CUT_OFF
    assert not card.no_free_cancellation
    assert card.proposal_id == rescue.booking_id


def test_a_rescue_card_after_the_cut_off_shows_everybody_on_it_paid():
    rescue = a_rescue()

    card = card_of_a_rescue(
        rescue,
        sides=sides_for(rescue, ZOSIA),
        forecast=CardForecast(pct=80, provisional=False),
        overlap=overlap_of([EVERY_HOUR] * 4, start=START, zone=CLUB_ZONE),
        now=CUT_OFF,
    )

    assert card.paid == (OLA, EWA, TOMEK)
    assert card.no_free_cancellation

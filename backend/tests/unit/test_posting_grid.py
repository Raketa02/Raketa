"""The posting grid and the slot sheet — the rules that need no I/O (#546; the
mechanics §9.1 steps 5–6; the screens A5.2–A5.3; Q77, Q92, Q93).

**A cell's number is how many of the poster's best fits are free together with
them at the best hour in its range that has a free court** — never people who
overlap the poster at different hours. With no court in the range, the best
hour of the range. The poster's own week picks the hour first: an hour they are
free for beats an hour with more fits, and a range their week does not cover is
*outside your hours*, still counted and still pickable.

Around the number: whether a court is free, whether a full game's worth are,
whether it is earlier today, and whether a game is already happening there —
a rescue or a post still filling the poster could join. The sheet lists the free
courts in the range, home club first, each with **its own** count.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.scorable import LevelReading
from app.kernel import Instant, Sport, instant
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.post import LevelRange, PostedFor, Who
from app.modules.proposals.domain.posting_grid import (
    GridCell,
    PostingGrid,
    open_to_join,
)
from app.modules.proposals.domain.proposal import Origin, Proposal
from app.modules.proposals.domain.proposer import CourtHourOnSale, Member, PoolClubs

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int, minute: int = 0) -> Instant:
    """An hour in Kraków in October 2026. The fifth is a Monday."""

    return instant(datetime(2026, 10, day, hour, minute, tzinfo=WARSAW))


NOW = warsaw(5, 8)
MONDAY, TUESDAY, SATURDAY = date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 10)
HOME, NEAR, ELSEWHERE = (uuid4() for _ in range(3))
CLUBS = PoolClubs(home_club_id=HOME, others=(NEAR,))
COMPETITIVE = frozenset({SearchMode.COMPETITIVE})

POSTER = uuid4()
A, B, C, D, E = (uuid4() for _ in range(5))

EVERY_HOUR = tuple((day, hour) for day in range(1, 8) for hour in range(7, 23))


def member(
    player: UUID,
    cells: tuple[tuple[int, int], ...] = EVERY_HOUR,
    *,
    level: float | None = 3.0,
    games_per_week: int = 2,
    most_ill_pay_grosze: int | None = None,
    booked: tuple[Instant, ...] = (),
    gender: Gender | None = Gender.WOMAN,
) -> Member:
    return Member(
        player_id=player,
        level=None if level is None else LevelReading(mu=level, sigma=0.4),
        week=WeeklyHours.of_cells(cells),
        wants=COMPETITIVE,
        limits=GamesAndMoney(
            player_id=player,
            games_per_week=games_per_week,
            most_ill_pay_grosze=most_ill_pay_grosze,
        ),
        booked=booked,
        gender=gender,
        preference=GenderPreference.ANY,
    )


def saturday(*hours: int) -> tuple[tuple[int, int], ...]:
    return tuple((6, hour) for hour in hours)


def on_sale(
    start: Instant,
    club: UUID = HOME,
    *,
    share_grosze: int = 30_00,
    taking_new_cards: bool = True,
    book_by: Instant | None = None,
) -> CourtHourOnSale:
    return CourtHourOnSale(
        club_id=club,
        sport=Sport.PADEL,
        start=start,
        courts=2,
        share_grosze=share_grosze,
        book_by=book_by if book_by is not None else start - timedelta(hours=2),
        taking_new_cards=taking_new_cards,
    )


def grid(
    fits: list[Member],
    hours: list[CourtHourOnSale] = (),  # type: ignore[assignment]
    *,
    poster: Member | None = None,
    happening: tuple[Instant, ...] = (),
    sport: Sport = Sport.PADEL,
    now: Instant = NOW,
    who: Who = Who.ANYONE,
) -> PostingGrid:
    return PostingGrid(
        poster=poster if poster is not None else member(POSTER),
        fits=fits,
        who=who,
        kind=SearchMode.COMPETITIVE,
        sport=sport,
        hours=list(hours),
        clubs=CLUBS,
        happening=happening,
        now=now,
    )


def evening(on: date, posting: PostingGrid) -> GridCell:
    return posting.cell(on, DayRange.EVENING)


# --------------------------------------------------------------------------- #
# The number
# --------------------------------------------------------------------------- #


def test_a_cell_counts_the_fits_free_at_its_best_hour_never_anyone_overlapping():
    fits = [
        member(A, saturday(17)),
        member(B, saturday(17)),
        member(C, saturday(18)),
        member(D, saturday(18)),
        member(E, saturday(18)),
    ]

    cell = evening(
        SATURDAY, grid(fits, [on_sale(warsaw(10, 17)), on_sale(warsaw(10, 18))])
    )

    # Five people overlap the poster on Saturday evening, at two hours: three
    # of them can play together.
    assert cell.fits_free == 3
    assert cell.best_start == warsaw(10, 18)
    assert cell.court_free and cell.full_game


def test_the_best_hour_is_one_with_a_free_court():
    fits = [
        member(A, saturday(17)),
        member(B, saturday(17)),
        member(C, saturday(17)),
        member(D, saturday(19)),
    ]

    cell = evening(SATURDAY, grid(fits, [on_sale(warsaw(10, 19))]))

    assert (cell.fits_free, cell.best_start) == (1, warsaw(10, 19))
    assert cell.court_free and not cell.full_game


def test_with_no_court_in_the_range_its_best_hour_is_counted_and_no_court_said():
    fits = [member(A, ((2, 9),)), member(B, ((2, 9),)), member(C, ((2, 10),))]

    cell = grid(fits, [on_sale(warsaw(10, 17))]).cell(TUESDAY, DayRange.MORNING)

    assert (cell.fits_free, cell.best_start) == (2, warsaw(6, 9))
    assert not cell.court_free and not cell.full_game


def test_nobody_free_is_a_dead_cell():
    cell = evening(SATURDAY, grid([member(A, ((1, 9),))], [on_sale(warsaw(10, 17))]))

    assert cell.fits_free == 0
    assert cell.court_free


def test_a_full_game_is_the_seats_besides_the_poster():
    three = [member(player, saturday(17)) for player in (A, B, C)]
    one = [member(A, saturday(17))]
    hours = [on_sale(warsaw(10, 17))]

    assert evening(SATURDAY, grid(three, hours)).full_game
    assert not evening(SATURDAY, grid(three[:2], hours)).full_game
    assert evening(SATURDAY, grid(one, hours, sport=Sport.TENNIS)).full_game


def test_a_mixed_pairs_full_game_is_the_men_and_women_the_poster_needs():
    hours = [on_sale(warsaw(10, 17))]
    three_men = [member(p, saturday(17), gender=Gender.MAN) for p in (A, B, C)]
    two_and_one = [
        *three_men[:2],
        member(D, saturday(17), gender=Gender.WOMAN),
    ]

    # She is a woman: three men are three fits, and still no game.
    crowded = evening(SATURDAY, grid(three_men, hours, who=Who.MIXED_PAIRS))
    full = evening(SATURDAY, grid(two_and_one, hours, who=Who.MIXED_PAIRS))

    assert (crowded.fits_free, crowded.full_game) == (3, False)
    assert (full.fits_free, full.full_game) == (3, True)
    assert evening(SATURDAY, grid(three_men, hours)).full_game


def test_a_fit_who_cannot_play_then_is_not_counted():
    hours = [on_sale(warsaw(10, 17), share_grosze=40_00)]
    fits = [
        member(A, saturday(17)),
        member(B, saturday(17), most_ill_pay_grosze=35_00),
        member(C, saturday(17), booked=(warsaw(10, 17),)),
        member(D, saturday(17), games_per_week=1, booked=(warsaw(9, 19),)),
        member(E, saturday(17), level=None),
    ]

    assert evening(SATURDAY, grid(fits, hours)).fits_free == 1


# --------------------------------------------------------------------------- #
# Around the number
# --------------------------------------------------------------------------- #


def test_an_hour_the_poster_is_free_for_beats_an_hour_with_more_fits():
    poster = member(POSTER, saturday(18))
    fits = [
        member(A, saturday(17)),
        member(B, saturday(17)),
        member(C, saturday(17, 18)),
    ]
    hours = [on_sale(warsaw(10, 17)), on_sale(warsaw(10, 18))]

    cell = evening(SATURDAY, grid(fits, hours, poster=poster))

    assert (cell.fits_free, cell.best_start) == (1, warsaw(10, 18))
    assert not cell.outside_your_hours


def test_a_range_the_poster_s_week_does_not_cover_is_outside_their_hours_and_counted():
    poster = member(POSTER, ((2, 19),))
    fits = [member(A, saturday(17)), member(B, saturday(17))]

    cell = evening(SATURDAY, grid(fits, [on_sale(warsaw(10, 17))], poster=poster))

    assert cell.outside_your_hours
    assert (cell.fits_free, cell.court_free) == (2, True)


def test_earlier_today_is_past_and_the_rest_of_today_is_not():
    now = warsaw(5, 13, 30)
    posting = grid([member(A)], [on_sale(warsaw(5, 18))], now=now)

    morning = posting.cell(MONDAY, DayRange.MORNING)
    afternoon = posting.cell(MONDAY, DayRange.AFTERNOON)

    assert morning.past and morning.best_start is None and morning.fits_free == 0
    assert not afternoon.past
    # Only the hours still ahead are counted.
    assert afternoon.best_start == warsaw(5, 14)
    assert not posting.cell(MONDAY, DayRange.EVENING).past


def test_a_game_already_happening_there_marks_its_cell():
    posting = grid([member(A)], [], happening=(warsaw(10, 19, 30),))

    assert posting.cell(SATURDAY, DayRange.EVENING).happening
    assert not posting.cell(SATURDAY, DayRange.AFTERNOON).happening


def test_an_hour_no_longer_taking_new_cards_is_no_free_court():
    hours = [
        on_sale(warsaw(10, 17), taking_new_cards=False),
        on_sale(warsaw(10, 18), book_by=NOW),
        on_sale(warsaw(10, 19), ELSEWHERE),
    ]

    assert not evening(SATURDAY, grid([member(A)], hours)).court_free


# --------------------------------------------------------------------------- #
# The grid and the sheet
# --------------------------------------------------------------------------- #


def test_week_one_is_today_and_the_six_days_after_and_week_two_the_seven_after_that():
    posting = grid([])

    assert posting.days(1) == tuple(MONDAY + timedelta(days=n) for n in range(7))
    assert posting.days(2) == tuple(MONDAY + timedelta(days=n) for n in range(7, 14))
    assert len(posting.week(1)) == 21
    assert [cell.range for cell in posting.week(1)[:3]] == list(DayRange)


def test_the_free_courts_in_a_cell_come_home_club_first_each_with_its_own_count():
    fits = [
        member(A, saturday(17, 18)),
        member(B, saturday(17, 18)),
        member(C, saturday(18)),
    ]
    hours = [
        on_sale(warsaw(10, 18), NEAR, share_grosze=27_50),
        on_sale(warsaw(10, 17)),
        on_sale(warsaw(10, 18)),
        on_sale(warsaw(10, 12)),
    ]

    courts = grid(fits, hours).free_courts(SATURDAY, DayRange.EVENING)

    assert [
        (court.hour.club_id, court.hour.start, court.fits_free) for court in courts
    ] == [
        (HOME, warsaw(10, 17), 2),
        (HOME, warsaw(10, 18), 3),
        (NEAR, warsaw(10, 18), 3),
    ]
    assert [court.home for court in courts] == [True, True, False]


def test_the_sheet_s_fits_are_those_free_at_the_cell_s_best_hour():
    fits = [member(A, saturday(17)), member(B, saturday(18)), member(C, saturday(18))]
    posting = grid(fits, [on_sale(warsaw(10, 17)), on_sale(warsaw(10, 18))])

    cell = evening(SATURDAY, posting)

    assert [fit.player_id for fit in posting.fits_free_at(cell)] == [B, C]


def test_a_court_hour_is_picked_only_where_the_grid_offers_one():
    posting = grid(
        [member(A)], [on_sale(warsaw(10, 17)), on_sale(warsaw(10, 18), ELSEWHERE)]
    )

    assert posting.court_hour(HOME, warsaw(10, 17)) is not None
    assert posting.court_hour(HOME, warsaw(10, 18)) is None
    assert posting.court_hour(ELSEWHERE, warsaw(10, 18)) is None


# --------------------------------------------------------------------------- #
# A post the poster could join
# --------------------------------------------------------------------------- #


def a_post_by(
    poster: UUID,
    *,
    posted_for: PostedFor | None = None,
    start: Instant = warsaw(10, 18),
    origin: Origin = Origin.POST,
) -> Proposal:
    post = Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=origin,
        poster_id=poster if origin is Origin.POST else None,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=HOME,
        start=start,
        share_grosze=30_00,
        book_by=start - timedelta(hours=2),
        at=NOW,
        posted_for=posted_for,
    )
    post.pull_events()
    return post


def open_to(post: Proposal, candidate: Member, **kwargs) -> bool:
    return open_to_join(
        post,
        candidate,
        unfit=kwargs.pop("unfit", frozenset()),
        genders=kwargs.pop("genders", {}),
        now=kwargs.pop("now", NOW),
    )


def test_a_post_still_filling_is_open_to_a_member_it_is_for_who_is_free_for_it():
    post = a_post_by(B)

    assert open_to(post, member(POSTER))


def test_a_post_the_member_cannot_join_is_not_happening_for_them():
    for_men = PostedFor(who=Who.MEN, levels=LevelRange(2.75, 3.25))
    declined = a_post_by(B)
    declined.deal((POSTER, C), at=NOW)
    declined.say_no(POSTER, at=NOW)
    full = a_post_by(B)
    for player in (C, D, E):
        full.join(player, at=NOW)

    assert not open_to(a_post_by(POSTER), member(POSTER))
    assert not open_to(a_post_by(B, origin=Origin.PICK), member(POSTER))
    assert not open_to(declined, member(POSTER))
    assert not open_to(full, member(POSTER))
    assert not open_to(a_post_by(B), member(POSTER, ((1, 9),)))
    assert not open_to(
        a_post_by(B, posted_for=PostedFor(Who.ANYONE, LevelRange(3.25, 3.5))),
        member(POSTER),
    )
    assert not open_to(a_post_by(B, posted_for=for_men), member(POSTER))
    assert not open_to(
        a_post_by(B), member(POSTER), unfit=frozenset({frozenset((POSTER, B))})
    )
    assert not open_to(a_post_by(B), member(POSTER), now=warsaw(10, 16))

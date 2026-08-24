"""ADR-0061's ladder: the pool, the wall, the floor, the order and the two waves.

Everything here is a function of a record, a candidate and a clock, so all of it
is exercised without a database, a port or an engine — which is the point of the
module being pure. What is *not* here is anything about the reach: which store
answers which rung lives in `test_run_cascade.py`, because it is a fact about
wiring rather than about the ladder.

**The numbers are read out of the product and never copied into the fixture.**
`CASCADE_FLOOR`, `FLOOR_HORIZON`, `HEAD_START` and `QUIET_UNTIL` are asserted
against their literals once, in one case, and every other case reads the
constant — because a bound compared against itself is a test that cannot fail,
which is the defect the last three commits each found once.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.engines.matchmaking import level

from app.kernel import (
    Instant,
    MatchRecord,
    Sport,
    hours,
    instant,
    minutes,
    shifted,
)

from app.modules.now.domain.cascade import (
    CASCADE_FLOOR,
    DARK_RUNGS,
    FLOOR_HORIZON,
    HEAD_START,
    POOL_RULES,
    QUIET_EXEMPT_WITHIN,
    QUIET_UNTIL,
    WAVE_OF,
    Band,
    Invitation,
    PoolCandidate,
    PoolExclusion,
    Rung,
    Wave,
    delivery_at,
    exclusions_for,
    floor_at,
    invitation_order,
    rungs_in,
    wave_due,
)
from tests.unit.match_records import DURATION, at, seats
from tests.unit.shelf_doubles import a_match

WARSAW = ZoneInfo("Europe/Warsaw")


def a_candidate(
    *,
    rung: Rung = Rung.IN_THE_BAND,
    hundredths: int | None = 300,
    busy: tuple[tuple[Instant, Instant], ...] = (),
    already_mine: bool = False,
    who: UUID | None = None,
) -> PoolCandidate:
    return PoolCandidate(
        player_id=who or uuid4(),
        rung=rung,
        level=None if hundredths is None else level(hundredths),
        busy=busy,
        already_mine=already_mine,
    )


def a_band(*, low: int = 250, high: int = 350) -> Band:
    return Band(low=level(low), high=level(high))


def starting(moment: Instant, *, paid: int = 1) -> MatchRecord:
    """A match pinned to an absolute instant rather than to an offset.

    The delivery cases are about a **local clock face**, so they need a start
    they can place either side of a twelve-hour line from a named UTC moment —
    which an offset from the suite's shared `START` cannot express readably.
    Constructed rather than mutated, because `MatchRecord` is frozen and its
    `__post_init__` is what refuses a seat count no sport is sold in.
    """

    return MatchRecord(
        sport=Sport.PADEL,
        start=moment,
        duration=DURATION,
        created=shifted(moment, minutes(-4320)),
        seats=seats(4, paid),
    )


# ---------------------------------------------------------------------------
# The seven rungs, and the three that are dark
# ---------------------------------------------------------------------------


def test_the_ladder_has_seven_rungs_numbered_as_the_adr_numbers_them() -> None:
    """The position **is** the specification, so the values are pinned.

    ADR-0061's table is an ordering, and a reader checking this file against it
    compares numbers. Renumbering to close a gap left by a dark rung would make
    the two documents disagree while every behavioural case stayed green.
    """

    assert [(rung.name, rung.value) for rung in Rung] == [
        ("STANDBY", 1),
        ("STANDING_RULE", 2),
        ("ASKED_BEFORE", 3),
        ("VIEWED", 4),
        ("CLUB_REGULAR", 5),
        ("IN_THE_BAND", 6),
        ("MARKED_AVAILABLE", 7),
    ]


def test_three_rungs_ship_dark_and_rung_four_is_the_one_the_adr_does_not_say() -> None:
    """ADR-0061 ships 2 and 7 dark. **4 joins them and the ADR does not say so.**

    Its source was to be ADR-0085's *Recently viewed* signal, which shipped dark
    itself — `Raketa02/Raketa#53` was closed without building the store. So the
    ticket's own acceptance criterion, which names only 2 and 7, is met for
    those two and **not** for rung 4, and this is where that is written down
    rather than discovered.
    """

    assert DARK_RUNGS == {Rung.STANDING_RULE, Rung.VIEWED, Rung.MARKED_AVAILABLE}
    assert Rung.STANDBY not in DARK_RUNGS
    assert Rung.ASKED_BEFORE not in DARK_RUNGS
    assert Rung.CLUB_REGULAR not in DARK_RUNGS
    assert Rung.IN_THE_BAND not in DARK_RUNGS


def test_the_first_dispatch_is_rung_one_alone() -> None:
    """*"One head start is not an optimisation, it is the standby promise."*"""

    assert rungs_in(Wave.FIRST) == (Rung.STANDBY,)


def test_the_second_dispatch_is_every_other_rung_in_ladder_order() -> None:
    assert rungs_in(Wave.SECOND) == (
        Rung.STANDING_RULE,
        Rung.ASKED_BEFORE,
        Rung.VIEWED,
        Rung.CLUB_REGULAR,
        Rung.IN_THE_BAND,
        Rung.MARKED_AVAILABLE,
    )


def test_every_rung_rides_in_exactly_one_dispatch() -> None:
    """The mapping is total, and the module refuses to load otherwise."""

    assert set(WAVE_OF) == set(Rung)
    assert set(rungs_in(Wave.FIRST)) | set(rungs_in(Wave.SECOND)) == set(Rung)
    assert not set(rungs_in(Wave.FIRST)) & set(rungs_in(Wave.SECOND))


# ---------------------------------------------------------------------------
# The pool: a fact filter, evaluated whole
# ---------------------------------------------------------------------------


def test_a_candidate_who_fails_nothing_is_in_the_pool() -> None:
    assert (
        exclusions_for(
            a_candidate(), a_match(paid=1, starts=2880), band=a_band(), now=at(0)
        )
        == frozenset()
    )


def test_the_pool_is_the_seven_rules_the_adr_names_and_no_others() -> None:
    """Read off the enumeration, so an eighth cannot arrive unannounced.

    **Distance and price are absent and the absence is the assertion.** ADR-0027
    forbids either as an exclusion — *"distance, price and level are never
    exclusions"* — and the one rule that looks like level is the band, which is
    a fact about the match rather than a preference of the viewer's.
    """

    assert set(POOL_RULES) == set(PoolExclusion)
    assert not any(
        word in rule.value.lower()
        for rule in PoolExclusion
        for word in ("distance", "travel", "price", "cheap")
    )


@pytest.mark.parametrize(
    "candidate, record, band, rule",
    [
        (
            {"hundredths": None},
            {"paid": 1, "starts": 2880},
            a_band(),
            PoolExclusion.RATED_AT_SPORT,
        ),
        (
            {},
            {"paid": 4, "starts": 2880},
            a_band(),
            PoolExclusion.HAS_FREE_SEAT,
        ),
        (
            {},
            {"paid": 1, "starts": 10},
            a_band(),
            PoolExclusion.BEFORE_JOIN_CUTOFF,
        ),
        (
            {},
            {"paid": 1, "starts": 2880, "club_cancelled": True},
            a_band(),
            PoolExclusion.LIVE_INVENTORY,
        ),
        (
            {"already_mine": True},
            {"paid": 1, "starts": 2880},
            a_band(),
            PoolExclusion.NOT_ALREADY_MINE,
        ),
        (
            {"hundredths": 500},
            {"paid": 1, "starts": 2880},
            a_band(),
            PoolExclusion.INSIDE_THE_BAND,
        ),
    ],
)
def test_each_rule_excludes_on_its_own_fact(candidate, record, band, rule) -> None:
    """One case per rule, each failing exactly the one it is about.

    Asserted as *this rule and only this rule*, because a fixture that failed
    two would pass a test naming either, and the pair would then be
    indistinguishable the day one of them was deleted.
    """

    assert exclusions_for(
        a_candidate(**candidate), a_match(**record), band=band, now=at(0)
    ) == frozenset({rule})


def test_a_clash_is_half_open_on_both_sides() -> None:
    """A match starting exactly as another ends is not a clash.

    A court booking already carries the club's turnaround, so two abutting
    bookings are two games she can play. Asserted from both directions, because
    a comparison flipped to inclusive on one end only is invisible from the
    other.
    """

    record = a_match(paid=1, starts=2880)
    start, end = record.start, shifted(record.start, record.duration)

    abutting_before = (shifted(start, minutes(-90)), start)
    abutting_after = (end, shifted(end, minutes(90)))
    overlapping = (shifted(start, minutes(-30)), shifted(start, minutes(30)))

    for free in (abutting_before, abutting_after):
        assert (
            exclusions_for(
                a_candidate(busy=(free,)), record, band=a_band(), now=at(0)
            )
            == frozenset()
        )
    assert exclusions_for(
        a_candidate(busy=(overlapping,)), record, band=a_band(), now=at(0)
    ) == frozenset({PoolExclusion.NO_SCHEDULE_CONFLICT})


def test_the_band_is_inclusive_at_both_edges() -> None:
    """A half-width is a rounding of a claim, so its edges are not precise.

    Excluding somebody who lands exactly on one would be reading precision the
    number does not carry — and the two edges are asserted separately, because
    a comparison flipped at one end passes a test that only checks the other.
    """

    record = a_match(paid=1, starts=2880)
    band = a_band(low=250, high=350)

    for edge in (250, 350):
        assert (
            exclusions_for(
                a_candidate(hundredths=edge), record, band=band, now=at(0)
            )
            == frozenset()
        )
    for outside in (249, 351):
        assert PoolExclusion.INSIDE_THE_BAND in exclusions_for(
            a_candidate(hundredths=outside), record, band=band, now=at(0)
        )


def test_no_band_is_no_wall_and_never_a_wall_nobody_clears() -> None:
    """A match with no seated Level has no band to be outside of.

    The band is the mean of the **seated** Levels, so with none there is no
    *outside* it. Refusing everybody on a missing fact would turn the hole left
    by the last rated player into a seat nobody can ever be told about — the
    dead seat the floor is dropped inside a day to avoid.
    """

    record = a_match(paid=1, starts=2880)
    for hundredths in (100, 300, 500):
        assert (
            exclusions_for(
                a_candidate(hundredths=hundredths), record, band=None, now=at(0)
            )
            == frozenset()
        )


def test_every_rule_is_evaluated_even_when_an_earlier_one_has_already_failed() -> None:
    """*Evaluate all, never short-circuit*, and it is the shape rather than a rule.

    A candidate failing several answers with **all** of them, which is what
    keeps *"eleven of them are playing that evening"* distinguishable from
    *"eleven of them are out of the band"* when a seat dies unfilled.
    """

    record = a_match(paid=4, starts=10, club_cancelled=True)
    failed = exclusions_for(
        a_candidate(hundredths=None, already_mine=True), record, band=None, now=at(0)
    )

    assert failed == {
        PoolExclusion.RATED_AT_SPORT,
        PoolExclusion.HAS_FREE_SEAT,
        PoolExclusion.BEFORE_JOIN_CUTOFF,
        PoolExclusion.LIVE_INVENTORY,
        PoolExclusion.NOT_ALREADY_MINE,
    }


# ---------------------------------------------------------------------------
# The floor
# ---------------------------------------------------------------------------


def test_the_floor_and_its_horizon_are_the_numbers_the_adr_gives() -> None:
    """The one case that compares the constants against their literals."""

    assert CASCADE_FLOOR == 70
    assert FLOOR_HORIZON == hours(24)


def test_a_floor_of_seventy_applies_above_a_day_and_none_below_it() -> None:
    """Asserted a minute either side, because a region is not a boundary.

    ADR-0061: *"we suggest matches over 70 is a promise about suggestions; a
    seat just opened at half price is a different sentence, and inside a day the
    alternative to telling a 55 is a dead seat."*
    """

    record = a_match(paid=1, starts=0)
    a_day_out = shifted(record.start, minutes(-FLOOR_HORIZON))

    assert floor_at(record, shifted(a_day_out, minutes(-1))) == CASCADE_FLOOR
    assert floor_at(record, a_day_out) is None
    assert floor_at(record, shifted(a_day_out, minutes(1))) is None


# ---------------------------------------------------------------------------
# The order
# ---------------------------------------------------------------------------


def test_the_rung_beats_the_fit_and_that_is_the_standby_promise() -> None:
    """ADR-0052 refused pure fit ranking by name.

    Under it, joining a queue buys nothing: a better-fitting stranger outranks
    the person who asked. So a 71 on rung 1 is told before a 96 on rung 6.
    """

    queued = Invitation(player_id=uuid4(), rung=Rung.STANDBY, fit=71)
    stranger = Invitation(player_id=uuid4(), rung=Rung.IN_THE_BAND, fit=96)

    assert invitation_order([stranger, queued]) == (queued, stranger)


def test_fit_orders_within_a_rung_and_descends() -> None:
    low = Invitation(player_id=uuid4(), rung=Rung.CLUB_REGULAR, fit=72)
    high = Invitation(player_id=uuid4(), rung=Rung.CLUB_REGULAR, fit=91)

    assert invitation_order([low, high]) == (high, low)


def test_the_id_breaks_a_tie_so_two_dispatches_agree_about_who_was_first() -> None:
    """The third comparator, and it is load-bearing rather than decorative.

    Without a guaranteed-total final key the order falls back on whatever order
    the pool arrived in, which is the query plan — and `FEED_ORDER`'s fourth
    comparator exists for exactly this. Asserted by shuffling the input and
    demanding the same answer.
    """

    ids = sorted((uuid4() for _ in range(6)), key=str)
    tied = [Invitation(player_id=one, rung=Rung.IN_THE_BAND, fit=80) for one in ids]

    assert invitation_order(tied) == invitation_order(list(reversed(tied)))
    assert [one.player_id for one in invitation_order(tied)] == ids


def test_the_order_is_a_permutation_and_never_shortens() -> None:
    """Nothing here removes a candidate. The floor and the pool already did."""

    invitations = [
        Invitation(player_id=uuid4(), rung=rung, fit=fit)
        for rung, fit in ((Rung.STANDBY, 30), (Rung.IN_THE_BAND, 99))
    ]

    assert sorted(invitation_order(invitations), key=str) == sorted(
        invitations, key=str
    )


# ---------------------------------------------------------------------------
# The two dispatches, and the quiet hours
# ---------------------------------------------------------------------------


def test_the_head_start_is_ten_minutes() -> None:
    assert HEAD_START == minutes(10)


def test_rung_one_is_due_at_the_vacancy_and_the_rest_ten_minutes_later() -> None:
    vacated = at(0)

    assert wave_due(vacated, Wave.FIRST) == vacated
    assert wave_due(vacated, Wave.SECOND) == shifted(vacated, HEAD_START)


def test_the_quiet_hours_open_at_eight_local_and_are_spent_inside_twelve() -> None:
    """The two numbers ADR-0052 gives, compared against their literals once."""

    assert QUIET_UNTIL == 8 * 60
    assert QUIET_EXEMPT_WITHIN == hours(12)


def test_a_dispatch_due_in_the_small_hours_waits_for_eight_local() -> None:
    """*"A free seat does not wake anybody at 03:00."*

    Warsaw is UTC+2 in August, so 01:30 UTC is 03:30 local and 06:00 UTC is
    08:00 local — which is what makes this a case about the **club's** clock
    rather than about UTC.
    """

    due = instant(datetime(2026, 8, 20, 1, 30, tzinfo=timezone.utc))
    record = starting(instant(datetime(2026, 8, 25, 18, 30, tzinfo=timezone.utc)))

    held = delivery_at(due, record, zone=WARSAW)

    assert held == instant(datetime(2026, 8, 20, 6, 0, tzinfo=timezone.utc))
    assert held.astimezone(WARSAW).hour == 8


def test_a_dispatch_due_after_eight_local_is_not_held_at_all() -> None:
    due = instant(datetime(2026, 8, 20, 9, 0, tzinfo=timezone.utc))
    record = starting(instant(datetime(2026, 8, 25, 18, 30, tzinfo=timezone.utc)))

    assert delivery_at(due, record, zone=WARSAW) == due


def test_a_match_inside_twelve_hours_spends_the_quiet_hours() -> None:
    """The exemption, and the reason it exists: the seat is nearly dead.

    Asserted against the *same* 03:30-local moment the case above holds, so the
    only thing that differs between them is how far off the match is.
    """

    due = instant(datetime(2026, 8, 20, 1, 30, tzinfo=timezone.utc))
    record = starting(shifted(due, minutes(QUIET_EXEMPT_WITHIN - 1)))

    assert delivery_at(due, record, zone=WARSAW) == due


def test_the_exemption_is_a_boundary_and_is_asserted_a_minute_either_side() -> None:
    due = instant(datetime(2026, 8, 20, 1, 30, tzinfo=timezone.utc))
    eight_local = instant(datetime(2026, 8, 20, 6, 0, tzinfo=timezone.utc))

    inside = starting(shifted(due, minutes(QUIET_EXEMPT_WITHIN - 1)))
    outside = starting(shifted(due, minutes(QUIET_EXEMPT_WITHIN)))

    assert delivery_at(due, inside, zone=WARSAW) == due
    assert delivery_at(due, outside, zone=WARSAW) == eight_local


def test_the_zone_is_the_clubs_and_the_answer_moves_with_it() -> None:
    """The negative control for *held to 08:00 **local***.

    A hold computed against UTC would give one answer for both clubs, which is
    what makes two zones the only way to see the conversion happening at all.
    """

    due = instant(datetime(2026, 8, 20, 1, 30, tzinfo=timezone.utc))
    record = starting(instant(datetime(2026, 8, 25, 18, 30, tzinfo=timezone.utc)))

    warsaw = delivery_at(due, record, zone=WARSAW)
    reykjavik = delivery_at(due, record, zone=ZoneInfo("Atlantic/Reykjavik"))

    assert warsaw != reykjavik
    assert warsaw.astimezone(WARSAW).hour == 8
    assert reykjavik.astimezone(ZoneInfo("Atlantic/Reykjavik")).hour == 8


def test_a_dispatch_is_never_moved_backwards_by_the_hold() -> None:
    """The hold only ever delays. A property over a whole day of due moments."""

    record = starting(instant(datetime(2026, 8, 25, 18, 30, tzinfo=timezone.utc)))

    midnight = instant(datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc))
    for offset in range(0, 24 * 60, 37):
        due = shifted(midnight, minutes(offset))
        assert delivery_at(due, record, zone=WARSAW) >= due


def test_seats_helper_is_the_shape_the_pool_rules_read() -> None:
    """A guard on the fixture rather than on the product.

    `HAS_FREE_SEAT` reads `is_full`, so a builder that quietly stopped filling
    seats would make every *there is a seat* case pass for the wrong reason.
    """

    assert sum(1 for seat in seats(4, 4) if seat.taken) == 4
    assert sum(1 for seat in seats(4, 1) if seat.taken) == 1

"""The Plan aggregate, its three slots and its lock — the rules a seam further out
cannot see.

Five families here, and each is a rule that would otherwise only be true by
accident.

**Born by being used**, so the birth is the first recording and there is no
opening event to assert the absence of anywhere else.

**One fact told twice** — setting a slot and moving one write the same event, and
writing the value already there writes nothing at all. The second half is what
keeps a room from filling with *Tomek set the day* three times over, and it is
the aggregate's because ``client_message_id`` has no analogue here: the *value*
is the idempotency key.

**Bounded chips the platform offered, never a free instant** — the horizon clamp,
the hour grid, and the one refusal both halves of a moment can raise.

**The agreed point is defined whenever a day is**, coarsened later and never
earlier, which is the amendment ADR-0145 §3 made to ADR-0144 and the one value
two other tickets each keyed a rule on.

**The count and the lock are two facts** (ADR-0155). A complete plan is one
everybody *could* agree; agreeing is an act with an actor and a moment, it
freezes nothing, and there is no un-agreeing. The two shapes here are deliberate
opposites: a **second** lock records nothing, and an **incomplete** one raises.

**The lock waits for the court** (ADR-0164 §5). Whether the court is whole is a
fact the aggregate borrows, as it borrows the anchor, and its refusal is its
own code beside *the plan is not complete* — two refusals, told apart, because
the card draws a different thing for each.

**The plan is the challenge's** (ADR-0164 §1): its id is the challenge's, its
events carry ``challenge_id``, and the day is clamped to an **anchor** that is
handed in rather than a ``planned_at`` the aggregate would have to know the
provenance of.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import pytest

from app.kernel import instant, minute_of_day
from app.modules.games.domain.windows import PLAN_HORIZON
from app.modules.plans.domain.errors import (
    ThatMomentHasAlreadyPassed,
    TheCourtIsNotWhole,
    TheDayIsPastTheHorizon,
    TheHourIsNotOffered,
    ThePlaceIsEmpty,
    ThePlaceIsTooLong,
    ThePlanIsNotComplete,
)
from app.modules.plans.domain.events import (
    DayRecorded,
    HourRecorded,
    PlaceRecorded,
    PlanLocked,
)
from app.modules.plans.domain.plan import SLOTS, Plan
from app.modules.plans.domain.slots import (
    EARLIEST_HOUR,
    HOUR_STEP_MINUTES,
    LATEST_HOUR,
    PLACE_LENGTH_CAP,
    PLATFORM_ZONE,
    Place,
    agreed_point,
    as_wall_time,
    last_plannable_day,
    moment_of,
)
from app.shared.ids import new_uuid

#: A Monday, chosen so that a *following day* and a *seven days out* are both
#: ordinary — no month boundary, no DST transition, nothing to make an assertion
#: below true for a reason it is not about. It is the plan's **anchor** — the
#: send until the game exists, then ``planned_at`` (``docs/adr/0164`` §4) — and
#: which of the two it is makes no difference to anything asserted here.
ANCHOR = instant(datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc))
ANA = new_uuid()
BO = new_uuid()


def _plan() -> Plan:
    return Plan.unwritten(new_uuid())


def _at(**offset) -> "datetime":
    return instant(ANCHOR + timedelta(**offset))


# ---------------------------------------------------------------------------
# Born by being used
# ---------------------------------------------------------------------------


def test_a_game_with_nothing_agreed_has_a_plan_that_was_never_written():
    """``docs/adr/0144`` — no record at birth, and *no plan* is what it draws."""

    plan = _plan()

    assert plan.version == 0
    assert plan.slot_count == 0
    assert plan.agreed_point is None
    assert plan.pull_events() == []


def test_the_first_recording_is_the_birth_and_there_is_no_opening_event():
    plan = _plan()

    plan.record_place(place="Zabłocie Sport", by=ANA, occurred_at=_at())
    recorded = plan.pull_events()

    assert [type(one) for one in recorded] == [PlaceRecorded]
    assert plan.version == 1


def test_any_of_the_three_may_be_the_first_event_a_plan_is_folded_from():
    """There is no opening event, so the challenge id is read off whichever
    recording happens to be first — every one of them can be a birth."""

    challenge_id = new_uuid()
    folded = Plan.from_history(
        [
            HourRecorded(
                challenge_id=challenge_id,
                minute_of_day=18 * 60,
                recorded_by=ANA,
                occurred_at=_at(),
            )
        ]
    )

    assert folded.challenge_id == challenge_id
    assert folded.hour == 18 * 60
    assert folded.slot_count == 1


# ---------------------------------------------------------------------------
# One fact told twice, and the value is the idempotency key
# ---------------------------------------------------------------------------


def test_moving_a_slot_writes_the_same_event_as_setting_one():
    """``docs/adr/0144`` — *the same event told with two sentences*, separated by
    the fold rather than by a second class."""

    plan = _plan()

    plan.record_place(place="Zabłocie", by=ANA, occurred_at=_at())
    first = plan.pull_events()
    plan.record_place(place="Hala Sportowa", by=BO, occurred_at=_at(hours=1))
    second = plan.pull_events()

    assert [type(one) for one in first] == [type(one) for one in second]
    assert plan.place == Place.of("Hala Sportowa")


@pytest.mark.parametrize(
    "record, again",
    [
        pytest.param(
            lambda plan, at: plan.record_place(
                place="Zabłocie", by=ANA, occurred_at=at
            ),
            lambda plan, at: plan.record_place(place="Zabłocie", by=BO, occurred_at=at),
            id="place",
        ),
        pytest.param(
            lambda plan, at: plan.record_day(
                day=date(2026, 9, 12), by=ANA, anchor=ANCHOR, occurred_at=at
            ),
            lambda plan, at: plan.record_day(
                day=date(2026, 9, 12), by=BO, anchor=ANCHOR, occurred_at=at
            ),
            id="day",
        ),
        pytest.param(
            lambda plan, at: plan.record_hour(
                hour=time(18, 0), by=ANA, occurred_at=at
            ),
            lambda plan, at: plan.record_hour(hour=time(18, 0), by=BO, occurred_at=at),
            id="hour",
        ),
    ],
)
def test_writing_the_value_already_there_records_nothing(record, again):
    """``docs/adr/0148`` §8. Without it the room fills with *Tomek set the day*
    three times over — and it is **the value** that is the key, not the person,
    so a second member re-affirming the same slot writes nothing either."""

    plan = _plan()

    record(plan, _at())
    plan.pull_events()
    again(plan, _at(hours=1))

    assert plan.pull_events() == []


def test_a_place_that_differs_only_in_whitespace_is_the_same_place():
    """Normalisation happens before the comparison, so a trailing space is not a
    change and does not write a line."""

    plan = _plan()

    plan.record_place(place="Zabłocie Sport", by=ANA, occurred_at=_at())
    plan.pull_events()
    plan.record_place(place="  Zabłocie   Sport  ", by=BO, occurred_at=_at(hours=1))

    assert plan.pull_events() == []


def test_any_member_may_fill_or_change_any_slot_any_number_of_times():
    """``docs/adr/0144`` — there is no lock, no rate limit and no history beyond
    the lines. **The line is the friction.**"""

    plan = _plan()

    for count, (who, day) in enumerate(
        ((ANA, 9), (BO, 10), (ANA, 11), (BO, 12)), start=1
    ):
        plan.record_day(
            day=date(2026, 9, day),
            by=who,
            anchor=ANCHOR,
            occurred_at=_at(hours=count),
        )
        assert len(plan.pull_events()) == 1

    assert plan.day == date(2026, 9, 12)


def test_a_plan_has_no_way_to_empty_a_slot_or_to_be_unmade():
    """``docs/adr/0144`` — a slot may be changed but never emptied, and a plan is
    never unmade. There is no cancellation, because ``games`` opens one game per
    arrangement for ever.

    ``lock`` left this set with ``docs/adr/0155`` and **``unlock`` took its
    place**: the lock is a thing that happened, so there is no un-happening of it
    for the same reason there is no clearing event.
    """

    methods = {name for name in dir(Plan) if not name.startswith("__")}
    forbidden = {
        "clear",
        "empty",
        "unset",
        "cancel",
        "unmake",
        "withdraw",
        "unlock",
    }

    assert methods & forbidden == set()


def test_the_third_slot_completes_a_plan_and_does_not_lock_it():
    """``docs/adr/0155`` — **the count and the lock are two facts.** ADR-0144
    folded them together; a complete plan is one everybody *could* agree, and
    agreeing is a separate act with an actor and a moment.

    So the third recording still announces nothing, exactly as ADR-0144 said —
    what changed is that there is now something else to announce.
    """

    plan = _plan()

    plan.record_place(place="Zabłocie", by=ANA, occurred_at=_at())
    plan.record_day(
        day=date(2026, 9, 12), by=BO, anchor=ANCHOR, occurred_at=_at(hours=1)
    )
    plan.record_hour(hour=time(18, 0), by=ANA, occurred_at=_at(hours=2))

    assert plan.slot_count == SLOTS
    assert plan.is_locked is False
    assert plan.locked_at is None
    assert [type(one).__name__ for one in plan.pull_events()] == [
        "PlaceRecorded",
        "DayRecorded",
        "HourRecorded",
    ]


# ---------------------------------------------------------------------------
# Where — short free text, one line, and nothing reads it
# ---------------------------------------------------------------------------


def test_a_place_is_collapsed_to_one_line():
    assert Place.of("Zabłocie\nSport   Centre ").value == "Zabłocie Sport Centre"


def test_a_place_that_says_nothing_is_refused_rather_than_emptying_the_slot():
    with pytest.raises(ThePlaceIsEmpty):
        Place.of("   \n  ")


def test_a_place_past_the_cap_is_refused_and_never_truncated():
    with pytest.raises(ThePlaceIsTooLong):
        Place.of("x" * (PLACE_LENGTH_CAP + 1))

    assert len(Place.of("x" * PLACE_LENGTH_CAP).value) == PLACE_LENGTH_CAP


# ---------------------------------------------------------------------------
# The day — clamped to the game's own horizon
# ---------------------------------------------------------------------------


def test_the_last_plannable_day_is_the_horizon_read_in_the_platform_zone():
    """``docs/adr/0148`` §8 — ``PLAN_HORIZON`` stays in ``games`` and this
    imports it, because its interlock with ``ENTRY_GRACE`` is the argument."""

    assert last_plannable_day(ANCHOR) == (
        instant(ANCHOR + PLAN_HORIZON).astimezone(PLATFORM_ZONE).date()
    )


def test_the_day_may_reach_the_horizon_and_not_pass_it():
    plan = _plan()
    horizon = last_plannable_day(ANCHOR)

    plan.record_day(day=horizon, by=ANA, anchor=ANCHOR, occurred_at=_at())

    assert plan.day == horizon
    with pytest.raises(TheDayIsPastTheHorizon):
        plan.record_day(
            day=horizon + timedelta(days=1),
            by=ANA,
            anchor=ANCHOR,
            occurred_at=_at(),
        )


# ---------------------------------------------------------------------------
# The hour — bounded chips the platform offered
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "offered",
    [time(6, 0), time(6, 30), time(12, 0), time(22, 30), time(23, 0)],
)
def test_every_hour_on_the_grid_is_accepted(offered):
    plan = _plan()

    plan.record_hour(hour=offered, by=ANA, occurred_at=_at())

    assert plan.hour == offered.hour * 60 + offered.minute


@pytest.mark.parametrize(
    "refused, why",
    [
        pytest.param(time(5, 30), "before the first offered hour", id="too-early"),
        pytest.param(time(23, 30), "after the last offered hour", id="too-late"),
        pytest.param(time(18, 15), "between two steps", id="off-step"),
        pytest.param(time(18, 0, 30), "carrying seconds", id="seconds"),
    ],
)
def test_an_hour_nobody_offered_is_refused_server_side(refused, why):
    """``docs/adr/0148`` §8 — *that validation is the point*. The client's grid is
    a convention; this is what makes ADR-0145 §9's *bounded chips the platform
    offered, never a free instant* true."""

    plan = _plan()

    with pytest.raises(TheHourIsNotOffered):
        plan.record_hour(hour=refused, by=ANA, occurred_at=_at())


def test_the_grid_runs_from_six_to_twenty_three_in_half_hours():
    assert as_wall_time(EARLIEST_HOUR) == time(6, 0)
    assert as_wall_time(LATEST_HOUR) == time(23, 0)
    assert HOUR_STEP_MINUTES == 30


# ---------------------------------------------------------------------------
# A moment that has already passed — one refusal, from either side
# ---------------------------------------------------------------------------


def test_a_day_alone_in_the_past_is_not_refused():
    """Only the **pair** claims a moment. A day on its own coarsens to the
    following morning, and a group recording the day they actually played is
    saying something true."""

    plan = _plan()

    plan.record_day(
        day=date(2026, 9, 6),
        by=ANA,
        anchor=ANCHOR,
        occurred_at=_at(hours=1),
    )

    assert plan.day == date(2026, 9, 6)


def test_an_hour_alone_is_never_a_moment_that_has_passed():
    plan = _plan()

    plan.record_hour(hour=time(6, 0), by=ANA, occurred_at=_at(days=1))

    assert plan.hour == 6 * 60
    assert plan.agreed_point is None


def test_the_hour_completing_a_past_day_is_refused():
    plan = _plan()
    plan.record_day(
        day=date(2026, 9, 7), by=ANA, anchor=ANCHOR, occurred_at=_at()
    )

    with pytest.raises(ThatMomentHasAlreadyPassed):
        # 09:00 local on the planned day, read at 12:00 local on the same day.
        plan.record_hour(hour=time(9, 0), by=BO, occurred_at=_at())


def test_the_day_completing_a_past_hour_is_refused_the_same_way():
    """**In either order**, which is why the refusal names both remedies and no
    value: the platform has no opinion about which of the two is wrong."""

    plan = _plan()
    plan.record_hour(hour=time(9, 0), by=ANA, occurred_at=_at())

    with pytest.raises(ThatMomentHasAlreadyPassed):
        plan.record_day(
            day=date(2026, 9, 6), by=BO, anchor=ANCHOR, occurred_at=_at()
        )


def test_a_moment_still_ahead_is_accepted_from_either_side():
    plan = _plan()

    plan.record_day(
        day=date(2026, 9, 12), by=ANA, anchor=ANCHOR, occurred_at=_at()
    )
    plan.record_hour(hour=time(18, 0), by=BO, occurred_at=_at())

    assert plan.agreed_point == moment_of(date(2026, 9, 12), minute_of_day(18 * 60))


# ---------------------------------------------------------------------------
# The agreed point — defined whenever a day is, coarsened later never earlier
# ---------------------------------------------------------------------------


def test_no_day_is_no_agreed_point_at_all():
    assert agreed_point(day=None, hour=None) is None
    assert agreed_point(day=None, hour=minute_of_day(18 * 60)) is None


def test_a_day_and_an_hour_are_the_agreed_instant():
    point = agreed_point(day=date(2026, 9, 12), hour=minute_of_day(18 * 60))

    assert point == instant(
        datetime(2026, 9, 12, 18, 0, tzinfo=PLATFORM_ZONE)
    )


def test_a_day_alone_is_the_start_of_the_following_local_day():
    """``docs/adr/0145`` §3's amendment to ADR-0144 — one value, defined whenever
    the day is, **coarsened later and never earlier**, so nobody is ever asked
    for a result before they could have played."""

    point = agreed_point(day=date(2026, 9, 12), hour=None)

    assert point == instant(datetime(2026, 9, 13, 0, 0, tzinfo=PLATFORM_ZONE))
    assert point > agreed_point(day=date(2026, 9, 12), hour=LATEST_HOUR)


def test_the_agreed_point_is_derived_and_lives_nowhere_on_the_record():
    """*Nothing derived is stored* — not the slot count and not the point. Both
    are read off the three values, so a day change cannot leave one behind."""

    plan = _plan()
    plan.record_day(
        day=date(2026, 9, 12), by=ANA, anchor=ANCHOR, occurred_at=_at()
    )
    plan.record_hour(hour=time(18, 0), by=BO, occurred_at=_at())
    plan.pull_events()

    before = plan.agreed_point
    plan.record_hour(hour=time(19, 30), by=ANA, occurred_at=_at())

    assert plan.agreed_point != before
    assert plan.agreed_point == moment_of(
        date(2026, 9, 12), minute_of_day(19 * 60 + 30)
    )
    assert not hasattr(plan, "_agreed_point")


def test_the_anchor_is_never_written_by_a_plan():
    """``docs/adr/0164`` §4 — the anchor is the send until the game exists and
    ``planned_at`` after, and the plan holds neither: it arrives as an argument,
    is measured against and is stored nowhere, so ``planned_at`` keeps meaning
    *when it became a game* and the plan never writes to ``games`` at all."""

    plan = _plan()
    plan.record_day(
        day=date(2026, 9, 12), by=ANA, anchor=ANCHOR, occurred_at=_at()
    )

    assert not hasattr(plan, "planned_at")
    assert not hasattr(plan, "anchor")
    assert all(
        not hasattr(one, "planned_at") and not hasattr(one, "anchor")
        for one in plan.pull_events()
    )


# ---------------------------------------------------------------------------
# The lock — an act, and not the third slot under another name
# ---------------------------------------------------------------------------


def _complete(plan: "Plan") -> "Plan":
    plan.record_place(place="Zabłocie Sport", by=ANA, occurred_at=_at())
    plan.record_day(
        day=date(2026, 9, 12), by=BO, anchor=ANCHOR, occurred_at=_at(hours=1)
    )
    plan.record_hour(hour=time(18, 0), by=ANA, occurred_at=_at(hours=2))
    plan.pull_events()
    return plan


def test_locking_records_who_and_when_and_carries_no_value():
    """``docs/adr/0155`` — the value is the three slots and they are already
    recorded. Repeating one here would be the second place it is true, and the
    first thing to disagree with the slot beside it after a later move."""

    plan = _complete(_plan())

    plan.lock(by=BO, occurred_at=_at(hours=3), court_is_whole=True)
    (recorded,) = plan.pull_events()

    assert isinstance(recorded, PlanLocked)
    assert recorded.challenge_id == plan.challenge_id
    assert recorded.locked_by == BO
    assert recorded.occurred_at == _at(hours=3)
    assert set(vars(recorded)) == {"challenge_id", "locked_by", "occurred_at"}
    assert plan.is_locked is True
    assert plan.locked_at == _at(hours=3)


@pytest.mark.parametrize(
    "fill",
    [
        pytest.param((), id="nothing"),
        pytest.param(("place",), id="place"),
        pytest.param(("day",), id="day"),
        pytest.param(("hour",), id="hour"),
        pytest.param(("place", "day"), id="place-and-day"),
        pytest.param(("place", "hour"), id="place-and-hour"),
        pytest.param(("day", "hour"), id="day-and-hour"),
    ],
)
def test_an_incomplete_plan_refuses_the_lock_rather_than_doing_nothing(fill):
    """**A refusal and not a silent no-op**, which is the opposite shape from the
    second lock below. An incomplete plan that answered `200` would leave a
    client believing it had locked one — where a repeat lock lands exactly the
    state its caller asked for."""

    plan = _plan()
    if "place" in fill:
        plan.record_place(place="Zabłocie Sport", by=ANA, occurred_at=_at())
    if "day" in fill:
        plan.record_day(
            day=date(2026, 9, 12),
            by=ANA,
            anchor=ANCHOR,
            occurred_at=_at(hours=1),
        )
    if "hour" in fill:
        plan.record_hour(hour=time(18, 0), by=ANA, occurred_at=_at(hours=2))
    plan.pull_events()

    with pytest.raises(ThePlanIsNotComplete):
        plan.lock(by=BO, occurred_at=_at(hours=3), court_is_whole=True)

    assert plan.slot_count < SLOTS
    assert plan.is_locked is False
    assert plan.pull_events() == []


def test_locking_an_already_locked_plan_records_nothing():
    """This repository's idempotency language, applied to an **act** rather than
    to a value: the same act twice lands the same state and records nothing the
    second time. It is not a refusal, and the first lock's moment stands."""

    plan = _complete(_plan())
    plan.lock(by=ANA, occurred_at=_at(hours=3), court_is_whole=True)
    plan.pull_events()

    plan.lock(by=BO, occurred_at=_at(hours=4), court_is_whole=True)

    assert plan.pull_events() == []
    assert plan.locked_at == _at(hours=3)


@pytest.mark.parametrize(
    "fill",
    [
        pytest.param((), id="nothing"),
        pytest.param(("place", "day"), id="place-and-day"),
        pytest.param(("place", "day", "hour"), id="complete"),
    ],
)
def test_a_court_that_is_not_whole_refuses_the_lock_before_the_slots_are_read(fill):
    """``docs/adr/0164`` §5 — **the lock waits for the court.** *We are agreed*
    is said only once everybody who will have to keep it is in, so a plan two of
    four have filled to the brim is refused on the court and not on the count.

    The court is asked **first**: a plan with a slot still empty on a court that
    is not whole is refused for the court, because that is the refusal the card
    draws in the button's place, and the count is a fact about the card only
    once there is a button to grey.
    """

    plan = _plan()
    if "place" in fill:
        plan.record_place(place="Zabłocie Sport", by=ANA, occurred_at=_at())
    if "day" in fill:
        plan.record_day(
            day=date(2026, 9, 12), by=ANA, anchor=ANCHOR, occurred_at=_at(hours=1)
        )
    if "hour" in fill:
        plan.record_hour(hour=time(18, 0), by=ANA, occurred_at=_at(hours=2))
    plan.pull_events()

    with pytest.raises(TheCourtIsNotWhole):
        plan.lock(by=BO, occurred_at=_at(hours=3), court_is_whole=False)

    assert plan.is_locked is False
    assert plan.pull_events() == []


def test_the_two_lock_refusals_are_two_codes():
    """The card draws a different thing for each — the count line where the
    button will be, and a greyed button — so a client must be able to tell them
    apart by code alone, and neither is a `400`."""

    assert TheCourtIsNotWhole().code == "the_court_is_not_whole"
    assert ThePlanIsNotComplete().code == "the_plan_is_not_complete"
    assert TheCourtIsNotWhole().code != ThePlanIsNotComplete().code
    assert TheCourtIsNotWhole().status_code == ThePlanIsNotComplete().status_code == 409
    assert not issubclass(TheCourtIsNotWhole, ThePlanIsNotComplete)
    assert not issubclass(ThePlanIsNotComplete, TheCourtIsNotWhole)


def test_a_lock_already_taken_survives_the_court_ceasing_to_be_whole():
    """A departure after the lock opens a seat and unmakes nothing
    (``docs/adr/0164`` §5, #411's rule 2): the plan stays locked, and asking
    again on the reopened court is the idempotent no-op it always was rather
    than a refusal about a court that *was* whole when it mattered."""

    plan = _complete(_plan())
    plan.lock(by=ANA, occurred_at=_at(hours=3), court_is_whole=True)
    plan.pull_events()

    plan.lock(by=BO, occurred_at=_at(hours=4), court_is_whole=False)

    assert plan.is_locked is True
    assert plan.locked_at == _at(hours=3)
    assert plan.pull_events() == []


def test_a_locked_plan_is_not_a_frozen_one_and_a_move_keeps_the_lock():
    """``docs/adr/0155`` — **locking freezes nothing.** ADR-0145 §5's *there is
    no un-agreeing to fear, only re-agreeing, and any member may do that at any
    time* stands, so a slot moved after a lock writes its own line and the plan
    stays locked. The line trail is the friction, as it already is."""

    plan = _complete(_plan())
    plan.lock(by=ANA, occurred_at=_at(hours=3), court_is_whole=True)
    plan.pull_events()

    plan.record_hour(hour=time(19, 0), by=BO, occurred_at=_at(hours=4))

    assert [type(one) for one in plan.pull_events()] == [HourRecorded]
    assert plan.hour == 19 * 60
    assert plan.is_locked is True
    assert plan.locked_at == _at(hours=3)


def test_being_locked_is_not_the_slot_count_under_another_name():
    """The distinction **is** ``docs/adr/0155``: a complete plan is one everybody
    *could* agree, and nobody has until somebody says so."""

    complete = _complete(_plan())
    assert complete.slot_count == SLOTS and complete.is_locked is False

    complete.lock(by=ANA, occurred_at=_at(hours=3), court_is_whole=True)
    assert complete.is_locked is True


def test_a_locked_plan_folds_back_locked():
    """The fold **re-runs no refusal.** A stream whose lock precedes its third
    slot cannot be produced by ``lock()`` and would be a bug upstream; replaying
    it loudly would make the plan unreadable rather than visible."""

    challenge_id = new_uuid()
    folded = Plan.from_history(
        [
            PlaceRecorded(
                challenge_id=challenge_id,
                place="Zabłocie Sport",
                recorded_by=ANA,
                occurred_at=_at(),
            ),
            DayRecorded(
                challenge_id=challenge_id,
                day="2026-09-12",
                recorded_by=BO,
                occurred_at=_at(hours=1),
            ),
            HourRecorded(
                challenge_id=challenge_id,
                minute_of_day=18 * 60,
                recorded_by=ANA,
                occurred_at=_at(hours=2),
            ),
            PlanLocked(
                challenge_id=challenge_id, locked_by=BO, occurred_at=_at(hours=3)
            ),
        ]
    )

    assert folded.is_locked is True
    assert folded.locked_at == _at(hours=3)
    assert folded.version == 4
    assert folded.pull_events() == []


def test_the_lock_may_be_the_first_event_a_plan_is_folded_from():
    """``_game_of`` walks all four, so a stream this aggregate cannot produce is
    still read rather than met with an ``AttributeError`` in a fold."""

    challenge_id = new_uuid()
    folded = Plan.from_history(
        [PlanLocked(challenge_id=challenge_id, locked_by=ANA, occurred_at=_at())]
    )

    assert folded.challenge_id == challenge_id
    assert folded.is_locked is True
    assert folded.slot_count == 0


# ---------------------------------------------------------------------------
# The fold
# ---------------------------------------------------------------------------


def test_a_plan_folds_back_to_exactly_what_was_recorded():
    challenge_id = new_uuid()
    folded = Plan.from_history(
        [
            PlaceRecorded(
                challenge_id=challenge_id,
                place="Zabłocie Sport",
                recorded_by=ANA,
                occurred_at=_at(),
            ),
            DayRecorded(
                challenge_id=challenge_id,
                day="2026-09-12",
                recorded_by=BO,
                occurred_at=_at(hours=1),
            ),
            HourRecorded(
                challenge_id=challenge_id,
                minute_of_day=18 * 60,
                recorded_by=ANA,
                occurred_at=_at(hours=2),
            ),
        ]
    )

    assert folded.place == Place.of("Zabłocie Sport")
    assert folded.day == date(2026, 9, 12)
    assert folded.hour == 18 * 60
    assert folded.slot_count == SLOTS
    assert folded.version == 3
    assert folded.pull_events() == []


def test_the_last_write_of_a_slot_wins_when_the_stream_is_replayed():
    challenge_id = new_uuid()
    folded = Plan.from_history(
        [
            DayRecorded(
                challenge_id=challenge_id,
                day="2026-09-12",
                recorded_by=ANA,
                occurred_at=_at(),
            ),
            DayRecorded(
                challenge_id=challenge_id,
                day="2026-09-13",
                recorded_by=BO,
                occurred_at=_at(hours=1),
            ),
        ]
    )

    assert folded.day == date(2026, 9, 13)
    assert folded.slot_count == 1

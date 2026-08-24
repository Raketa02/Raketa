"""The wake carries a name, and the name is not an accident of construction order.

`test_next_wake_at.py` asserts that a wake exists wherever the situation moves.
This asserts the *other* half, which ADR-0076 needs and #72 stores: **which**
threshold the wake is pointed at.

**Why a name at all, given that nothing branches on it.** `wake_reason` is half
of `{matchId}:{threshold}:{scheduledFor}` — the string a support question, a log
line and a duplicate wake are all identified by. A label that is not a function
of the record is one where the same scheduled moment is filed under two names
depending on nothing, and the two spellings of one look then read as two looks.

**So the load-bearing property here is the tie-break.** Thresholds coincide, and
not rarely: at a twelve-hour club the commitment deadline and the far tier's
lapse are the same instant, which ADR-0076 records as *"three rules on one
instant"*. A `min()` over unnamed moments does answer, and answers by whichever
order the candidate list happened to be built in — an ordering nobody wrote down,
nothing tests, and any rearranging of `_boundaries` changes in silence. The two
ordering defects `Raketa02/Raketa#64` and `#65` measured were exactly this shape,
and both were found by asking *what happens when two rows tie* rather than by
reading.

Every instant below is computed **in this file, from the raw thresholds**, for
the same reason the sibling suite computes its own: a test that asked the kernel
where its boundaries were would agree with it about a name that was wrong.
"""

from __future__ import annotations

from itertools import islice

import pytest

from app.kernel import (
    Boundary,
    HoldPolicy,
    Instant,
    MatchKind,
    MatchRecord,
    PayModel,
    Seat,
    SeatClaim,
    Sport,
    Vacancy,
    WakeReason,
    hours,
    minutes,
    next_wake,
    next_wake_at,
    shifted,
)
from tests.unit.match_records import DURATION, START, a_match, at, grid

#: The same thresholds the sibling suite spells out, and spelled out again here
#: rather than imported: two files that share a constant share a wrong one.
_COMMITMENT_BACKSTOP = 12 * 60
_RESCUE_DOUBLES = 4 * 60
_CHECKPOINT = 2 * 60
_DOOR_CODE_LEAD = 15
_HOLD_FAR = 12 * 60
_HOLD_NEAR = 4 * 60
_RESULT_WINDOW = 24 * 60
_SETTLEMENT = 24 * 60
_VACANCY_DECAY = 24 * 60
_CLAIM_WINDOW = 5

_STRIDE = 97


def _sample() -> list[tuple[MatchRecord, Instant]]:
    return list(islice(grid(), None, None, _STRIDE))


SAMPLE = _sample()


# --- the thirteen names -------------------------------------------------------


def test_the_enumeration_is_closed_at_thirteen() -> None:
    """Pinned, the same way `SITUATION_COUNT` is. A fourteenth reason is a
    decision about where it sorts, and the tie-break is the enumeration's own
    order."""

    assert len(WakeReason) == 13
    assert len({reason.value for reason in WakeReason}) == 13


#: One record and one clock per reason, each built so that the named threshold is
#: the soonest one strictly ahead. Written as *what the match is* rather than as
#: *what the kernel should answer*, so a rung moving is caught here.
_REACHES = {
    WakeReason.CLAIM_LAPSE: (
        # Nothing paid and a fortnight out, so nothing else is within five
        # minutes of anything: the claim is unambiguously next.
        a_match(
            paid=0,
            claims=(SeatClaim(seat_index=1, expires_at=at(-4000)),),
        ),
        at(-4000 - 1),
    ),
    WakeReason.COMMITMENT: (
        # Nothing paid, so no tier to lapse. The club's own window is narrower
        # than the backstop, so `commit` is the **earlier** of the two — the
        # platform's twelve hours — and nothing else is between here and there.
        a_match(paid=0, policy=HoldPolicy(window=hours(8))),
        at(-_COMMITMENT_BACKSTOP - 1),
    ),
    WakeReason.HOLD_LAPSE: (
        # Two paid seats at a club with no cap: the far tier at T-12h. The
        # commitment deadline is brought forward by a wider window so the two do
        # not coincide — that coincidence is its own test below.
        a_match(paid=2, policy=HoldPolicy(window=hours(20))),
        at(-_HOLD_FAR - 1),
    ),
    WakeReason.HOLD_STALE: (
        # A cap that bites before the tier does.
        a_match(
            paid=2,
            created=-4320,
            held_since=at(-4320),
            policy=HoldPolicy(window=hours(20), max_hold_age=hours(24)),
        ),
        at(-4320 + 1),
    ),
    WakeReason.VACANCY_DECAY: (
        # Uncommitted, one hole: the newest vacancy ages out twenty-four hours
        # after it opened, which here is before anything else.
        a_match(
            paid=1,
            held=0,
            created=-6000,
            open_vacancies=(Vacancy(vacated_at=at(-5000)),),
        ),
        at(-5000 + 1),
    ),
    WakeReason.RESCUE: (
        # Committed with a hole: the rescue window at T-4h for a doubles court.
        a_match(
            paid=3,
            committed_at=at(-2000),
            open_vacancies=(Vacancy(vacated_at=at(-1000)),),
        ),
        at(-_RESCUE_DOUBLES - 1),
    ),
    WakeReason.CHECKPOINT: (
        a_match(paid=4, court_locked=True),
        at(-_CHECKPOINT - 1),
    ),
    WakeReason.JOIN_CUT: (
        a_match(paid=4, court_locked=True),
        at(-31),
    ),
    WakeReason.DOOR_CODE: (
        a_match(paid=4, court_locked=True),
        at(-_DOOR_CODE_LEAD - 1),
    ),
    WakeReason.PLAY: (
        a_match(paid=4, court_locked=True),
        at(-1),
    ),
    WakeReason.MATCH_END: (
        a_match(paid=4, court_locked=True),
        at(int(DURATION) - 1),
    ),
    WakeReason.RESULT_WINDOW: (
        a_match(paid=4, court_locked=True),
        at(int(DURATION) + _RESULT_WINDOW - 1),
    ),
    WakeReason.SETTLEMENT: (
        # A score entered an hour after the last point: its own deadline is an
        # hour past the entry deadline, so this is the only boundary left ahead
        # once the clock is between the two.
        a_match(
            paid=4,
            court_locked=True,
            proposed_at=at(int(DURATION) + 60),
            proposals=1,
        ),
        at(int(DURATION) + _RESULT_WINDOW + 1),
    ),
}


@pytest.mark.parametrize("reason", list(WakeReason), ids=lambda r: r.value)
def test_every_reason_is_the_answer_somewhere(reason: WakeReason) -> None:
    """One test per member, so a name that stops being produced fails **by its
    own name** rather than as a count that quietly went down by one."""

    record, moment = _REACHES[reason]
    wake = next_wake(record, moment)

    assert wake is not None, f"{reason.value} names no wake at all"
    assert wake.reason is reason


@pytest.mark.parametrize("reason", list(WakeReason), ids=lambda r: r.value)
def test_the_named_moment_is_the_moment_the_rule_names(reason: WakeReason) -> None:
    """The name and the instant agree — computed here, not asked of the kernel.

    Without this a wake could carry every name in the enumeration and be
    consistently pointed at the wrong hour.
    """

    record, moment = _REACHES[reason]
    wake = next_wake(record, moment)
    assert wake is not None

    expected = {
        WakeReason.CLAIM_LAPSE: at(-4000),
        WakeReason.COMMITMENT: at(-_COMMITMENT_BACKSTOP),
        WakeReason.HOLD_LAPSE: at(-_HOLD_FAR),
        WakeReason.HOLD_STALE: at(-4320 + 24 * 60),
        WakeReason.VACANCY_DECAY: at(-5000 + _VACANCY_DECAY),
        WakeReason.RESCUE: at(-_RESCUE_DOUBLES),
        WakeReason.CHECKPOINT: at(-_CHECKPOINT),
        WakeReason.JOIN_CUT: at(-30),
        WakeReason.DOOR_CODE: at(-_DOOR_CODE_LEAD),
        WakeReason.PLAY: START,
        WakeReason.MATCH_END: at(int(DURATION)),
        WakeReason.RESULT_WINDOW: at(int(DURATION) + _RESULT_WINDOW),
        WakeReason.SETTLEMENT: at(int(DURATION) + 60 + _SETTLEMENT),
    }[reason]

    assert wake.at == expected


def test_the_near_tier_is_named_the_same_as_the_far_one() -> None:
    """A tier is a tier. Which one applies is the seat count's business, and
    giving them two names would put that arithmetic in the label."""

    near = a_match(paid=3, policy=HoldPolicy(window=hours(20)))
    wake = next_wake(near, at(-_HOLD_NEAR - 1))

    assert wake is not None
    assert wake.reason is WakeReason.HOLD_LAPSE
    assert wake.at == at(-_HOLD_NEAR)


def test_a_claim_lapse_wins_a_tie_against_every_start_relative_threshold() -> None:
    """`claimLapse` is first in the enumeration, so it wins every tie it is in.

    It is the only boundary here **not** measured from `start` — five minutes
    from a tap — so it has no place in a sequence ordered by how a match lives.
    Landing it on the join cutoff is the tie a real evening produces: somebody
    taps at 13:25 against a 13:30 cutoff, and both moments are 13:30.
    """

    join_cut = at(-30)
    tapped_five_minutes_before = a_match(
        paid=2,
        court_locked=True,
        claims=(SeatClaim(seat_index=3, expires_at=join_cut),),
    )

    wake = next_wake(tapped_five_minutes_before, at(-31))

    assert wake is not None
    assert wake.at == join_cut
    assert wake.reason is WakeReason.CLAIM_LAPSE


def test_two_claims_on_one_match_name_the_sooner_deadline() -> None:
    """Two people paying at once is ordinary — exclusivity is per seat — and the
    schedule points at whichever runs out first, because a wake is a look and
    the second one is still due when it arrives."""

    both = a_match(
        paid=0,
        claims=(
            SeatClaim(seat_index=0, expires_at=at(-4000)),
            SeatClaim(seat_index=2, expires_at=at(-3998)),
        ),
    )

    wake = next_wake(both, at(-4001))

    assert wake is not None
    assert wake.reason is WakeReason.CLAIM_LAPSE
    assert wake.at == at(-4000)


def test_a_claim_on_a_full_match_is_still_a_boundary() -> None:
    """A seat that frees and is claimed on a match that has since refilled is
    not a state anybody can reach — but the claim on a match whose *other* seats
    filled while she paid is, and her five minutes still have to be looked at."""

    filling = MatchRecord(
        sport=Sport.PADEL,
        start=START,
        duration=DURATION,
        created=at(-4320),
        seats=(Seat(True, True), Seat(True, True), Seat(True, True), Seat()),
        claims=(SeatClaim(seat_index=3, expires_at=at(-4000)),),
        held_since=at(-4320),
    )

    wake = next_wake(filling, at(-4001))

    assert wake is not None
    assert wake.reason is WakeReason.CLAIM_LAPSE


# --- the tie-break ----------------------------------------------------------


def test_two_rules_on_one_instant_resolve_to_one_name() -> None:
    """T-12h at a twelve-hour club: the commitment deadline **and** the far
    tier's lapse, on the same instant, on the same record.

    ADR-0076 calls this out by name. The answer has to be a decision rather than
    whichever candidate `_boundaries` appended first — and it is the earlier and
    more consequential of the two, which is the enumeration's own order.
    """

    both = a_match(paid=2, policy=HoldPolicy(window=hours(12)))
    from_commit = shifted(START, minutes(-_COMMITMENT_BACKSTOP))
    from_tier = shifted(START, minutes(-_HOLD_FAR))
    assert from_commit == from_tier, "the premise: the two thresholds coincide"

    wake = next_wake(both, at(-_COMMITMENT_BACKSTOP - 1))

    assert wake is not None
    assert wake.at == from_commit
    assert wake.reason is WakeReason.COMMITMENT


def test_the_tie_break_does_not_depend_on_the_order_the_record_was_built() -> None:
    """The same two facts, arrived at from four differently-shaped records.

    A `min()` over unnamed moments is stable only by accident of construction
    order; this asks the same question of records whose candidate lists are built
    in different lengths and orders, and demands one answer.
    """

    tied = [
        a_match(paid=2, policy=HoldPolicy(window=hours(12))),
        a_match(paid=2, policy=HoldPolicy(window=hours(12)), club_extended=True),
        a_match(
            paid=2,
            policy=HoldPolicy(window=hours(12), max_hold_age=hours(72)),
            created=-4320,
            held_since=at(-4320),
        ),
        a_match(
            paid=2,
            held=1,
            policy=HoldPolicy(window=hours(12)),
            open_vacancies=(Vacancy(vacated_at=at(-100)),),
        ),
    ]

    named = {next_wake(record, at(-_COMMITMENT_BACKSTOP - 1)) for record in tied}

    assert named == {
        Boundary(WakeReason.COMMITMENT, shifted(START, minutes(-_COMMITMENT_BACKSTOP)))
    }


def test_a_boundary_orders_by_its_moment_before_its_name() -> None:
    """The tie-break is a tie-**break**: it never overrules the clock.

    Stated directly because the failure it guards against is quiet — a rank read
    first would schedule a match for a commitment deadline it passed yesterday.
    """

    late_but_first_in_the_enumeration = Boundary(WakeReason.COMMITMENT, at(100))
    early_but_last = Boundary(WakeReason.RESULT_WINDOW, at(0))

    assert min(
        (late_but_first_in_the_enumeration, early_but_last),
        key=lambda one: one.order,
    ) is early_but_last


def test_the_reason_is_stable_across_repeated_asks() -> None:
    """Two calls with the same arguments are the same answer, name included."""

    for record, moment in SAMPLE:
        assert next_wake(record, moment) == next_wake(record, moment)


# --- the moment-only form cannot drift from the named one -------------------


def test_the_unnamed_wake_is_the_named_one_with_its_name_dropped() -> None:
    """`next_wake_at` is a wrapper, and this is what keeps it one.

    The wake property suite reads `next_wake_at`; the timekeeper stores what
    `next_wake` says. A second implementation of *which moment* would let the
    schedule and the property that proves it correct disagree.
    """

    for record, moment in SAMPLE:
        named = next_wake(record, moment)
        assert next_wake_at(record, moment) == (None if named is None else named.at)


def test_a_terminal_match_names_no_wake_at_all() -> None:
    for cancelled in (
        a_match(paid=2, club_cancelled=True),
        a_match(paid=2, weather=True),
        a_match(paid=2, form_cancelled=True),
        a_match(paid=2, checkpoint_cancelled=True),
        a_match(paid=2, inventory_lost=True),
    ):
        assert next_wake(cancelled, at(-7200)) is None


def test_a_settled_result_arms_no_wake_for_an_answer_nobody_can_give() -> None:
    """A settled match is not terminal — the four cancellations are — so it goes
    on waking, and the boundary that must *not* be among them is the one the
    conversation has finished with.

    `settlement_deadline` is what refuses it, and it is the same function the
    ladder reads — so *there is nothing left for silence to answer* is one fact
    with one home rather than a flag the schedule has to remember separately.
    """

    entered = at(int(DURATION) + 5)
    live = a_match(paid=4, proposed_at=entered, proposals=1)
    settled = a_match(
        paid=4, proposed_at=entered, proposals=1, result_agreed=True
    )
    # Past the entry deadline, the proposal's own is the only boundary left.
    past_entry = at(int(DURATION) + _RESULT_WINDOW + 1)

    ahead = next_wake(live, past_entry)
    assert ahead is not None and ahead.reason is WakeReason.SETTLEMENT

    assert next_wake(settled, past_entry) is None


def test_a_wake_is_strictly_ahead_of_the_instant_it_is_asked_about() -> None:
    """Otherwise the chain re-arms itself where it stands and never terminates —
    which the timekeeper turns into a row the tick picks up every second."""

    for record, moment in SAMPLE:
        wake = next_wake(record, moment)
        if wake is not None:
            assert wake.at > moment


def test_the_sample_is_wide_enough_to_be_making_a_claim() -> None:
    assert len(SAMPLE) > 500
    named = {
        wake.reason
        for record, moment in SAMPLE
        if (wake := next_wake(record, moment)) is not None
    }
    assert len(named) >= 5


# --- what the wake deliberately is not --------------------------------------


def test_a_private_court_still_wakes_for_the_hours_that_matter() -> None:
    """A private court has no tier to lapse, and the match still has a clock:
    it is played, it ends, and a score can be entered for a day afterwards."""

    private = a_match(paid=4, kind=MatchKind.PRIVATE, pay_model=PayModel.SOLO)
    wake = next_wake(private, at(-1))

    assert wake is not None
    assert wake.reason is WakeReason.PLAY


def test_a_singles_match_names_the_same_thresholds_as_a_doubles_one() -> None:
    """The rescue window is six hours rather than four, and it is still
    `rescue` — the label names the rule, never the arithmetic behind it."""

    singles = a_match(
        sport=Sport.TENNIS,
        paid=1,
        committed_at=at(-2000),
        open_vacancies=(Vacancy(vacated_at=at(-1000)),),
    )
    wake = next_wake(singles, at(-6 * 60 - 1))

    assert wake is not None
    assert wake.reason is WakeReason.RESCUE
    assert wake.at == at(-6 * 60)

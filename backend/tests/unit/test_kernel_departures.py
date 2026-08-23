"""What a leaver recovers: the ranking, the two questions, and the two forms.

Three claims are asserted here that nothing else in the tree can make.

1. **Forfeit ranks equal to a zero refund.** ADR-0033 decides it in one line and
   the whole of the quote-and-confirm rule turns on it. It is also the line
   somebody will read as a bug and "fix", so it is pinned from both directions:
   the two are equal, and neither is below the other.
2. **``live_outcome`` and ``refill_outcome`` are two questions.** They agree
   everywhere except past the checkpoint, and that disagreement is the design:
   leaving then promises nothing, and a filler who nonetheless arrives pays the
   rescue price and **improves** what the leaver already had.
3. **The money has two forms and neither can be mistaken for the other.** Not
   one payload with an optional amount — the phone interprets nothing, and
   *nothing was taken* and *nothing has come back yet* are opposite sentences a
   blank cannot tell apart.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from itertools import product
from pathlib import Path

import pytest

from app.kernel import (
    OUTCOME_COUNT,
    HoldPolicy,
    MatchKind,
    NothingTaken,
    Outcome,
    PayModel,
    Recoverable,
    deadlines,
    grosze,
    hours,
    live_outcome,
    may_depart,
    outcome_rank,
    outcome_worse_than,
    private_lock,
    refill_outcome,
)

from tests.unit.match_records import a_match, at

#: A minute either side of a threshold, so a boundary is asserted as a boundary
#: and never as *somewhere in the region*.
A_MINUTE = 1


def committed(**facts):
    """A full, committed padel match — the only kind with four outcomes."""

    facts.setdefault("committed_at", at(-2880))
    return a_match(paid=4, **facts)


# --- the enumeration --------------------------------------------------------


def test_the_enumeration_is_four_and_the_count_is_pinned():
    assert len(Outcome) == OUTCOME_COUNT == 4


def test_the_four_names_are_the_glossary_s_four():
    assert {one.value for one in Outcome} == {
        "reversed",
        "refundedInFull",
        "refundedHalf",
        "forfeited",
    }


# --- the ranking, and the tie that is the decision --------------------------


def test_forfeit_ranks_equal_to_a_reversal_and_not_below_it():
    """ADR-0033: *"the quote protects money, and the money is identical; a
    confirmation dialog that says 'still zero' is friction bought for no
    protection."* Asserted both ways so that lowering either one fails."""

    assert outcome_rank(Outcome.FORFEITED) == outcome_rank(Outcome.REVERSED)
    assert not outcome_worse_than(Outcome.FORFEITED, Outcome.REVERSED)
    assert not outcome_worse_than(Outcome.REVERSED, Outcome.FORFEITED)


def test_a_full_refund_beats_half_and_half_beats_nothing():
    assert outcome_rank(Outcome.REFUNDED_IN_FULL) > outcome_rank(Outcome.REFUNDED_HALF)
    assert outcome_rank(Outcome.REFUNDED_HALF) > outcome_rank(Outcome.FORFEITED)


def test_every_outcome_is_ranked():
    """A table rather than a derivation, so a fifth outcome is a build error
    here and never a silent rank of zero."""

    for outcome in Outcome:
        assert isinstance(outcome_rank(outcome), int)


def test_the_count_is_a_literal_and_not_a_derivation():
    """`OUTCOME_COUNT = len(Outcome)` would satisfy its own invariant for ever.

    Read off the source rather than the value, because that is the only place
    the difference exists: pinning is about the **next** member, and a count
    derived from the enumeration cannot notice one arriving. The same rule
    `CAUSE_COUNT` and `SITUATION_COUNT` are written under, and the first of the
    three to have it checked.
    """

    source = (
        Path(__file__).resolve().parents[2] / "app" / "kernel" / "departures.py"
    ).read_text(encoding="utf-8")

    assert f"OUTCOME_COUNT = {OUTCOME_COUNT}" in source
    assert "OUTCOME_COUNT = len(" not in source


@pytest.mark.parametrize("candidate, quote", list(product(Outcome, Outcome)))
def test_worse_is_strict_over_the_whole_grid(candidate, quote):
    """Equal or better applies. Sixteen pairs, no exceptions written by hand."""

    assert outcome_worse_than(candidate, quote) is (
        outcome_rank(candidate) < outcome_rank(quote)
    )


def test_nothing_is_worse_than_itself():
    for outcome in Outcome:
        assert not outcome_worse_than(outcome, outcome)


# --- the live outcome: what leaving now is worth ----------------------------


def test_an_uncommitted_match_reverses_however_close_it_is():
    """The subject is **commitment**, not the deadline. A match past its own
    deadline and still short has bought nothing — it will cancel incomplete —
    so leaving it is still free."""

    record = a_match(paid=2, committed_at=None)
    when = deadlines(record)

    assert live_outcome(record, at(-20160)) is Outcome.REVERSED
    assert live_outcome(record, when.commit) is Outcome.REVERSED
    assert live_outcome(record, when.check) is Outcome.REVERSED


def test_a_committed_match_refunds_in_full_while_the_full_price_search_runs():
    record = committed()
    when = deadlines(record)

    assert live_outcome(record, at(-20160)) is Outcome.REFUNDED_IN_FULL
    assert live_outcome(record, _before(when.rescue)) is Outcome.REFUNDED_IN_FULL


def test_rescue_opening_is_the_instant_the_promise_halves():
    record = committed()
    when = deadlines(record)

    assert live_outcome(record, _before(when.rescue)) is Outcome.REFUNDED_IN_FULL
    assert live_outcome(record, when.rescue) is Outcome.REFUNDED_HALF


def test_the_checkpoint_is_the_instant_the_promise_runs_out():
    """Two hours out is *"the last moment anything about the roster can
    change"*, so the honest promise from there is nothing."""

    record = committed()
    when = deadlines(record)

    assert live_outcome(record, _before(when.check)) is Outcome.REFUNDED_HALF
    assert live_outcome(record, when.check) is Outcome.FORFEITED
    assert live_outcome(record, when.play) is Outcome.FORFEITED


def test_a_singles_match_halves_earlier_because_its_rescue_window_opens_earlier():
    """Six hours for two players, four for four. Read off the deadlines rather
    than restated, so this cannot pass while disagreeing with the ladder."""

    from app.kernel import Sport

    singles = a_match(sport=Sport.SQUASH, paid=2, committed_at=at(-2880))
    doubles = committed()

    assert deadlines(singles).rescue < deadlines(doubles).rescue
    assert live_outcome(singles, deadlines(singles).rescue) is Outcome.REFUNDED_HALF
    assert live_outcome(doubles, deadlines(singles).rescue) is (
        Outcome.REFUNDED_IN_FULL
    )


# --- the private court, which has two outcomes and not four -----------------


def a_private_court(**facts):
    facts.setdefault("kind", MatchKind.PRIVATE)
    facts.setdefault("pay_model", PayModel.SPLIT)
    facts.setdefault("open_seats", 2)
    return a_match(paid=2, **facts)


def test_a_private_court_never_reverses_and_never_halves():
    """ADR-0030: *"Two outcomes, not four — 100 % if anyone takes the seat, 0 %
    if nobody does."* No commitment deadline, because the court was bought at
    booking; no rescue tier, because nothing here is at risk."""

    record = a_private_court(committed_at=None)
    reachable = {live_outcome(record, at(offset)) for offset in range(-20160, 240, 37)}

    assert reachable == {Outcome.REFUNDED_IN_FULL, Outcome.FORFEITED}


def test_a_private_share_is_refundable_until_match_time():
    """*"No pre-match cutoff kills a converted match, and the seat keeps selling
    until match time"* (ADR-0046) — so the promise turns at the start and not at
    the join cutoff."""

    record = a_private_court(committed_at=None)
    when = deadlines(record)

    assert when.join_cut < when.play
    assert live_outcome(record, when.join_cut) is Outcome.REFUNDED_IN_FULL
    assert live_outcome(record, _before(when.play)) is Outcome.REFUNDED_IN_FULL
    assert live_outcome(record, when.play) is Outcome.FORFEITED


def test_a_private_courts_commitment_is_not_read_at_all():
    """It has no commitment deadline, so a committed one and an uncommitted one
    are quoted the same thing."""

    assert live_outcome(a_private_court(committed_at=None), at(-600)) is (
        live_outcome(a_private_court(committed_at=at(-2880)), at(-600))
    )


# --- the refill outcome: what a filler settles for --------------------------


def test_a_filler_before_rescue_returns_the_whole_share():
    record = committed()

    assert refill_outcome(record, _before(deadlines(record).rescue)) is (
        Outcome.REFUNDED_IN_FULL
    )


def test_a_filler_from_the_rescue_deadline_returns_half():
    record = committed()

    assert refill_outcome(record, deadlines(record).rescue) is Outcome.REFUNDED_HALF


def test_the_two_questions_disagree_past_the_checkpoint_and_that_is_the_design():
    """Leaving then is quoted nothing; a filler who nonetheless pays the rescue
    price improves what the leaver had. Monotonic settlement is what makes the
    asymmetry safe — a quote may under-promise for ever and may never
    over-promise once."""

    record = committed()
    past_the_checkpoint = deadlines(record).check

    assert live_outcome(record, past_the_checkpoint) is Outcome.FORFEITED
    assert refill_outcome(record, past_the_checkpoint) is Outcome.REFUNDED_HALF
    assert outcome_rank(Outcome.REFUNDED_HALF) > outcome_rank(Outcome.FORFEITED)


def test_a_filler_never_settles_a_departure_at_nothing():
    """There is no checkpoint tier in the refill: a seat sold late is still
    sold, and the money that arrives is the money that goes back."""

    record = committed()
    over_its_whole_life = {
        refill_outcome(record, at(offset)) for offset in range(-20160, 240, 31)
    }

    assert Outcome.FORFEITED not in over_its_whole_life
    assert Outcome.REVERSED not in over_its_whole_life


def test_a_private_share_comes_back_whole_whenever_the_seat_is_taken():
    record = a_private_court(committed_at=None)
    everywhere = {
        refill_outcome(record, at(offset)) for offset in range(-20160, 240, 31)
    }

    assert everywhere == {Outcome.REFUNDED_IN_FULL}


# --- the two money forms ----------------------------------------------------


def test_nothing_taken_has_no_amount_and_no_field_that_could_hold_one():
    """ADR-0072's whole argument: an optional amount is a field whose absence
    the phone has to interpret, and the phone interprets nothing."""

    assert fields(NothingTaken()) == ()


def test_recoverable_names_what_she_paid_in():
    assert Recoverable(amount=grosze(3800)).amount == 3800


def test_the_two_forms_are_different_types_and_never_equal():
    assert NothingTaken() != Recoverable(amount=grosze(0))
    assert not isinstance(NothingTaken(), Recoverable)


def test_both_forms_are_frozen():
    money = Recoverable(amount=grosze(3800))

    with pytest.raises(FrozenInstanceError):
        money.amount = grosze(1)  # type: ignore[misc]


def _before(moment):
    from app.kernel import minutes, shifted

    return shifted(moment, minutes(-A_MINUTE))


# --- may this person leave, and the lock that says no -----------------------
#
# ADR-0086 states `mayDepart` as a **server boolean** and the phone derives none
# of it. It is in the kernel rather than in Now because `Match.depart` refuses
# on the same facts, and a control offering a door the aggregate will not open
# is the one thing ADR-0083 says is worse than the gap. Every case below is
# therefore also an assertion about the *write*.


def test_a_seated_player_may_leave_a_match_that_has_not_started():
    assert may_depart(committed(), at(-60), holds_seat=True, holds_claim=False)


def test_somebody_who_holds_no_seat_may_not_leave():
    """The already-left leaver and the stranger, answered by one condition.

    Her route still **resolves** — a 404 would tell her the match never existed
    — and answers no.
    """

    assert not may_depart(committed(), at(-60), holds_seat=False, holds_claim=False)


def test_a_live_seat_claim_is_its_own_no_and_not_a_consequence_of_the_seat():
    """ADR-0081 fixes that a claim holds no seat yet.

    Stated rather than left to fall out of `holds_seat`, which happens to answer
    it today only because no seated player may claim a second seat. Driven with
    the seat held, so the claim is the only thing refusing.
    """

    assert not may_depart(committed(), at(-60), holds_seat=True, holds_claim=True)


def test_nobody_leaves_a_match_that_has_started():
    """You played or you did not, and that is `playedNoShow`."""

    assert not may_depart(committed(), at(0), holds_seat=True, holds_claim=False)
    assert may_depart(committed(), at(-A_MINUTE), holds_seat=True, holds_claim=False)


def test_nobody_leaves_a_match_that_is_no_longer_happening():
    """The fifth falsity, which ADR-0086 does not list and `depart` refuses.

    A cancelled match is not one anybody is looking to leave, and the aggregate
    raises there by name — so the control must not be drawn.
    """

    assert not may_depart(
        committed(club_cancelled=True), at(-60), holds_seat=True, holds_claim=False
    )


def _converted(*, paid=4, **facts):
    """A private court sold by the share: ADR-0046's *converted* court."""

    facts.setdefault("kind", MatchKind.PRIVATE)
    facts.setdefault("pay_model", PayModel.SPLIT)
    return a_match(paid=paid, **facts)


def test_the_lock_closes_at_the_clubs_own_deadline_and_not_before():
    """*"Once a converted court is full and past the club's cancellation
    deadline, nobody may leave."*

    The default club's window is twenty-four hours, so the boundary is exactly
    a day out — asserted a minute either side, because a boundary asserted as a
    region is a boundary nobody has actually checked.
    """

    court = _converted()
    assert not private_lock(court, at(-24 * 60 - A_MINUTE))
    assert private_lock(court, at(-24 * 60))


def test_the_lock_reads_the_clubs_window_and_never_the_commitment_deadline():
    """`deadlines().commit` is the *earlier* of the window and a 12-hour backstop.

    The backstop is a rule about an **open** match's commitment; a private court
    was bought at booking and commits to nothing. The two diverge at a club whose
    window is **shorter** than the backstop, and there reading the commitment
    deadline would close the lock six hours early — refusing a departure the
    club's own terms allow, which is the unsafe direction of the two.

    Driven at a six-hour club, because at every club with a window of twelve
    hours or more the two coincide exactly and a test there proves nothing.
    """

    court = _converted(policy=HoldPolicy(window=hours(6)))
    when = deadlines(court)

    assert not private_lock(court, at(-6 * 60 - A_MINUTE))
    assert private_lock(court, at(-6 * 60))
    # Six hours earlier, and still open — which is the whole of the claim.
    assert when.commit == at(-12 * 60)
    assert not private_lock(court, when.commit)


def test_a_court_that_is_not_full_never_locks():
    """A stranger has not yet bought a court that definitely exists."""

    assert not private_lock(_converted(paid=3), at(-A_MINUTE))


def test_a_solo_private_court_never_locks():
    """It sells no seats, so there is no marketplace joiner to lock in."""

    assert not private_lock(_converted(pay_model=PayModel.SOLO), at(-A_MINUTE))


def test_an_open_match_never_locks_however_full_and_however_late():
    assert not private_lock(committed(), at(-A_MINUTE))


def test_the_lock_is_the_only_thing_refusing_a_full_converted_court():
    """`may_depart` and `private_lock` answer the same question, once."""

    court = _converted()
    assert may_depart(court, at(-25 * 60), holds_seat=True, holds_claim=False)
    assert not may_depart(court, at(-24 * 60), holds_seat=True, holds_claim=False)

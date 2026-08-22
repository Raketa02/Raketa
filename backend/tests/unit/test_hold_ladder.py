"""The hold ladder, rung by rung — and the decision it hands the writer.

`app/kernel/holds.py` answers two different questions and they are asserted here
separately, because they fail differently.

* ``court_hold(record, now)`` is **what the ladder says**: how firmly a court is
  being kept aside, why, and the two facts a card needs. Every rule ADR-0031
  settled lives here — Rule 11 governing, Rule 12 restated as *never shorter at
  the same level of certainty*, the ``filled < n-1`` guard, the club's cap
  measured from ``held_since``, and staleness that is recomputed rather than
  latched.
* ``hold_move(record, now)`` is **what the ladder does about it**: grant a court,
  take one back, or leave the record alone. It is the only thing in the system
  allowed to move ``held_since``, and it is what
  `app/modules/matches/application/resolve_court_hold.py` acts on.

**Every instant here is computed from the thresholds rather than written down.**
A test that asked the module where its own boundaries were would agree with it
about a missing one, which is exactly how the off-by-one in `_staleness` survived
until the wake property found it (`Raketa02/Raketa#63`).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.kernel import (
    HoldKind,
    HoldMove,
    HoldPolicy,
    HoldReason,
    Instant,
    InvariantViolated,
    MatchRecord,
    Situation,
    Sport,
    court_hold,
    elapsed_minutes,
    hold_move,
    hours,
    is_held,
    is_terminal,
    keeping_a_court,
    minutes,
    situation,
)
from app.modules.now.domain.vocabulary import CARD_HOLD_REASON_OF
from tests.unit.match_records import DURATION, OFFSETS, at, a_match, grid, seats

#: A club that caps how long a speculative hold may sit — the only way to reach
#: Rule 11 at all.
CAP = hours(48)
CAPPING = HoldPolicy(window=hours(48), max_hold_age=CAP)

#: A club that caps *and* publishes a demand model, which is the only way to
#: reach Rule 12's extension.
EXTENDING = HoldPolicy(max_hold_age=CAP, prob_hold=True)

#: A club that does not hold speculatively at all.
NEVER = HoldPolicy(max_hold_age=minutes(0))

#: The two tiers' own release moments, read off the ladder's answer rather than
#: restated: a record one seat short and a record on two paid seats, each asked
#: where its hold lapses. Restating `-240` and `-720` here would be a second copy
#: of the two constants the module owns.
NEAR_LAPSE = court_hold(a_match(paid=3), at(-10_000)).release_at
FAR_LAPSE = court_hold(a_match(paid=2), at(-10_000)).release_at


def before(moment: Instant | None, by: int = 1) -> Instant:
    assert moment is not None
    return at(int((moment - at(0)).total_seconds() // 60) - by)


def after(moment: Instant | None, by: int = 1) -> Instant:
    assert moment is not None
    return at(int((moment - at(0)).total_seconds() // 60) + by)


# --- Rule 11 governs, and Rule 12 is restated -------------------------------


def test_a_club_cap_takes_back_a_hold_the_ladder_would_still_be_keeping():
    """Rule 11 governs: the club's cap fires while the tier is still live.

    The pair is the assertion. The same record at the same instant is a live
    far-tier hold at a club with no cap, so what moved is the club's number and
    not the clock — which is the whole of *the ladder is a floor* being false in
    the running product, and the reason ADR-0031 exists.
    """

    granted = at(-7200)
    now = at(-7200 + int(CAP))

    capped = a_match(paid=2, policy=CAPPING, held_since=granted)
    uncapped = a_match(paid=2, held_since=granted)

    assert now < FAR_LAPSE  # the tier itself has not lapsed
    assert court_hold(capped, now).why is HoldReason.STALE
    assert not is_held(court_hold(capped, now))
    assert court_hold(uncapped, now).why is HoldReason.FAR
    assert is_held(court_hold(uncapped, now))


def test_a_club_may_hold_longer_than_the_ladder_promised():
    """Rule 12, restated: only ever *longer*, and only on a lapsed hold."""

    record = a_match(
        paid=2, policy=EXTENDING, club_extended=True, held_since=at(-30)
    )
    extended = court_hold(record, after(FAR_LAPSE))

    assert extended.kind is HoldKind.SOFT
    assert extended.why is HoldReason.EXTENDED


def test_an_extension_never_applies_to_a_hold_the_ladder_is_still_keeping():
    """*Longer* is the only direction, so there is nothing to extend yet."""

    record = a_match(
        paid=2, policy=EXTENDING, club_extended=True, held_since=at(-30)
    )

    assert court_hold(record, before(FAR_LAPSE)).why is HoldReason.FAR


def test_an_extension_needs_both_halves_and_a_club_saying_so_is_not_enough():
    """Both come from published club facts: a demand model *and* this match."""

    lapsed = after(FAR_LAPSE)
    no_model = a_match(
        paid=2, policy=CAPPING, club_extended=True, held_since=at(-30)
    )
    not_this_match = a_match(paid=2, policy=EXTENDING, held_since=at(-30))

    assert court_hold(no_model, lapsed).why is HoldReason.FAR_LAPSED
    assert court_hold(not_this_match, lapsed).why is HoldReason.FAR_LAPSED


def test_the_floor_binds_at_the_same_level_of_certainty():
    """Rule 12 as restated: a hold is never shortened at the level it was won.

    A match one seat short has raised its certainty, so the cap may not reach it
    however old the hold is — and a hold *older than the whole match* is the
    strongest form of the claim available.
    """

    ancient = a_match(paid=3, policy=CAPPING, held_since=at(-100_000))

    assert court_hold(ancient, before(NEAR_LAPSE)).why is HoldReason.NEAR


# --- the `filled < n-1` guard -----------------------------------------------


def test_staleness_reclaims_a_far_tier_hold_and_never_a_near_tier_one():
    """The guard, as the one difference between two otherwise identical records."""

    granted = at(-7200)
    now = at(-7200 + int(CAP) + 1)
    far = a_match(paid=2, policy=CAPPING, held_since=granted)
    near = a_match(paid=3, policy=CAPPING, held_since=granted)

    assert court_hold(far, now).why is HoldReason.STALE
    assert court_hold(near, now).why is HoldReason.NEAR


def test_there_is_no_hard_hold_one_seat_short():
    """A consequence of the guard, and it is asserted as an absence.

    Nothing at `n-1` is ever ``HARD``: a match one seat short is being *held*
    while it earns it, not pinned. Only commitment, completeness, a private court
    and a club's own hand produce a hard hold.
    """

    for policy in (HoldPolicy(), CAPPING, EXTENDING, NEVER):
        for offset in OFFSETS:
            record = a_match(paid=3, policy=policy, held_since=at(-30))
            assert court_hold(record, at(offset)).kind is not HoldKind.HARD


# --- the cap is measured from the hold, and the age printed is the hold's ---


def test_the_cap_is_measured_from_the_hold_and_not_from_the_match():
    """A match that spent sixty hours thin and *then* earned a hold is fresh.

    Anchored to creation it is stale on arrival, which punishes exactly the match
    that just improved — the defect ADR-0031 measured in the prototype.
    """

    old_match = a_match(paid=2, policy=CAPPING, created=-10_000, held_since=at(-1000))
    now = at(-900)

    # The match is far older than the cap; the hold is a hundred minutes old.
    assert elapsed_minutes(old_match.created, now) > CAP
    assert court_hold(old_match, now).why is HoldReason.FAR


def test_a_reclaimed_hold_prints_its_own_age_and_never_the_clubs_threshold():
    """Seventy-one hours under a forty-eight-hour cap says seventy-one."""

    granted = at(-7200)
    now = at(-7200 + 71 * 60)
    record = a_match(paid=2, policy=CAPPING, held_since=granted)

    reclaimed = court_hold(record, now)

    assert reclaimed.why is HoldReason.STALE
    assert reclaimed.age == minutes(71 * 60)
    assert reclaimed.age != CAP


def test_the_cap_fires_at_the_threshold_and_not_a_minute_after_it():
    """One-directional, the same way the tiers are.

    Written `now <= held_since + cap` instead, the change lands a minute past the
    only instant the schedule knows about: the wake arrives, finds the hold still
    fresh, re-arms nothing, and the card says *held* until some unrelated write.
    """

    granted = at(-7200)
    record = a_match(paid=2, policy=CAPPING, held_since=granted)

    assert court_hold(record, at(-7200 + int(CAP) - 1)).why is HoldReason.FAR
    assert court_hold(record, at(-7200 + int(CAP))).why is HoldReason.STALE


# --- staleness is never latched ---------------------------------------------


def test_a_stale_hold_is_live_again_the_moment_a_third_seat_is_paid():
    """Recomputed from the current facts, so a card may go *back* to held.

    A payment landing after the club's cap has lapsed re-earns the hold rather
    than arriving too late for one, and any conformance suite assuming hold state
    moves one way is wrong.
    """

    granted = at(-7200)
    now = at(-7200 + int(CAP) + 1)

    assert court_hold(
        a_match(paid=2, policy=CAPPING, held_since=granted), now
    ).why is HoldReason.STALE
    assert court_hold(
        a_match(paid=3, policy=CAPPING, held_since=granted), now
    ).why is HoldReason.NEAR


def test_a_reclaimed_hold_is_not_granted_again_on_the_very_next_look():
    """The loop the grid property found, pinned as its own case.

    Cleared on reclaim, `held_since` would be re-invented at the next look, the
    hold would be granted again, and the club's cap would fire again a cap
    later — for ever. What the club asked for was a court back on sale, not one
    flickering. The anchor therefore survives the reclaim, and the ladder's
    answer about the reclaimed record is *stand*.
    """

    granted = at(-7200)
    stale_at = at(-7200 + int(CAP) + 1)
    record = a_match(paid=2, policy=CAPPING, held_since=granted)

    assert hold_move(record, stale_at) is HoldMove.WITHDRAW

    reclaimed = replace(record, released_at=stale_at)
    assert hold_move(reclaimed, stale_at) is HoldMove.STAND
    assert hold_move(reclaimed, at(-7200 + 2 * int(CAP))) is HoldMove.STAND


def test_a_reclaimed_hold_is_granted_again_when_certainty_rises():
    """And the way out is the one ADR-0031 names: a third payment.

    *"It re-earns the hold rather than arriving too late for one."* The guard
    closes, staleness stops applying, and the ladder grants — with a new anchor,
    because this is a new hold at a new level of certainty.
    """

    granted = at(-7200)
    stale_at = at(-7200 + int(CAP) + 1)
    reclaimed = replace(
        a_match(paid=3, policy=CAPPING, held_since=granted), released_at=stale_at
    )

    assert hold_move(reclaimed, stale_at) is HoldMove.GRANT


def test_a_stale_hold_is_live_again_the_moment_the_match_commits():
    """Commitment promotes whatever was held to hard, unconditionally."""

    granted = at(-7200)
    now = at(-7200 + int(CAP) + 1)
    committed = a_match(
        paid=2, policy=CAPPING, held_since=granted, committed_at=at(-1440)
    )

    assert court_hold(committed, now).kind is HoldKind.HARD
    assert court_hold(committed, now).why is HoldReason.COMMITTED


# --- a club that does not hold speculatively at all -------------------------


def test_a_club_that_never_holds_speculatively_is_granted_nothing_ever():
    """Zero is *this club does not hold*, not *every hold is instantly stale*.

    The difference is visible exactly here: nothing is ever granted, so nothing
    is ever taken back from anybody, and no card ever says a court went back on
    sale at a club that never put one aside.
    """

    for paid in (2, 3):
        for offset in OFFSETS:
            record = a_match(paid=paid, policy=NEVER, held_since=None)
            now = at(offset)

            assert not is_held(court_hold(record, now))
            assert hold_move(record, now) is HoldMove.STAND

    two_paid = a_match(paid=2, policy=NEVER, held_since=None)
    assert court_hold(two_paid, at(-5000)).why is HoldReason.NO_SPECULATIVE_HOLD


# --- the five reasons a card names ------------------------------------------


def test_the_five_reasons_a_card_names_are_all_produced_and_all_distinct():
    """Committed · far off and part-paid · close and nearly full · stale · extended.

    Each from a record a writer can actually produce, and each projecting onto a
    different one of the card's five — so *distinguishable* is asserted as five
    different sentences rather than five different enum members.
    """

    granted = at(-7200)
    reasons = {
        "committed": court_hold(
            a_match(paid=4, committed_at=at(-1440), held_since=granted), at(-600)
        ).why,
        "far": court_hold(a_match(paid=2, held_since=granted), before(FAR_LAPSE)).why,
        "near": court_hold(a_match(paid=3, held_since=granted), before(NEAR_LAPSE)).why,
        "stale": court_hold(
            a_match(paid=2, policy=CAPPING, held_since=granted),
            at(-7200 + int(CAP)),
        ).why,
        "extended": court_hold(
            a_match(
                paid=2, policy=EXTENDING, club_extended=True, held_since=at(-30)
            ),
            after(FAR_LAPSE),
        ).why,
    }

    assert len(set(reasons.values())) == 5
    cards = {CARD_HOLD_REASON_OF[reason] for reason in reasons.values()}
    assert None not in cards
    assert len(cards) == 5


# --- a match that is over is keeping nothing --------------------------------


def test_a_match_that_is_over_is_keeping_nothing_and_says_so():
    """Above the base ladder, because it is a fact about the match.

    Without it a cancelled match on two paid seats still composes a *soft* hold
    from its seat count, and the record then has to carry a `held_since` for a
    court that went back on sale the moment it cancelled — which is the one
    combination `_staleness` refuses outright.
    """

    cancelled = a_match(
        paid=2, policy=CAPPING, club_cancelled=True, held_since=None
    )

    assert court_hold(cancelled, at(-5000)) == court_hold(cancelled, at(600))
    assert court_hold(cancelled, at(-5000)).why is HoldReason.OVER
    assert not is_held(court_hold(cancelled, at(-5000)))
    assert hold_move(cancelled, at(-5000)) is HoldMove.STAND


def test_the_court_a_cancelled_match_was_holding_is_given_back():
    held = a_match(paid=2, club_cancelled=True, held_since=at(-30))

    assert hold_move(held, at(-20)) is HoldMove.WITHDRAW


def test_being_over_changes_no_situation_anywhere_on_the_grid():
    """The rule is new; the ladder's answers are not.

    ``is_terminal`` is exactly rungs 1-4, so `_ladder` answers with a cancellation
    before any rung reads the hold, and neither rewrite set holds a cancelled
    name. Asserted over the whole grid rather than argued.
    """

    cancelled = [(r, n) for r, n in grid() if is_terminal(r)]
    assert cancelled

    for record, now in cancelled:
        assert court_hold(record, now).why is HoldReason.OVER
        assert situation(record, None, now) in {
            Situation.INVENTORY_LOST,
            Situation.CANCELLED_CLUB,
            Situation.CANCELLED_INCOMPLETE,
            Situation.CANCELLED_CHECKPOINT,
        }


# --- what the ladder does about it ------------------------------------------


def test_the_ladder_grants_when_it_wants_a_court_and_the_match_holds_none():
    assert hold_move(a_match(paid=2, held_since=None), before(FAR_LAPSE)) is (
        HoldMove.GRANT
    )


def test_the_ladder_withdraws_when_the_tier_it_granted_on_has_lapsed():
    assert hold_move(a_match(paid=2, held_since=at(-30)), after(FAR_LAPSE)) is (
        HoldMove.WITHDRAW
    )


def test_the_ladder_stands_when_the_record_already_says_what_it_says():
    assert hold_move(a_match(paid=2, held_since=at(-30)), before(FAR_LAPSE)) is (
        HoldMove.STAND
    )
    assert hold_move(a_match(paid=1, held_since=None), at(-5000)) is HoldMove.STAND


def test_a_grant_can_be_asked_about_under_a_club_cap_with_nothing_to_age_from():
    """The load-bearing one, and it has a negative control below it.

    Entering a tier and being granted a court are one transaction, so at the
    instant the ladder is asked there *is* no `held_since` — and asking
    `court_hold` about the record as it stands is exactly the combination the
    kernel refuses. `hold_move` asks about the record as it would be with a hold
    granted now, which is the question a grant actually poses.
    """

    record = a_match(paid=2, policy=CAPPING, held_since=None)
    now = before(FAR_LAPSE)

    assert hold_move(record, now) is HoldMove.GRANT

    # The negative control: the refusal `hold_move` steps around is still live,
    # so this test cannot pass because somebody deleted the invariant.
    with pytest.raises(InvariantViolated):
        court_hold(record, now)


def test_the_clubs_cap_binds_from_the_read_after_the_grant():
    """Stepping around the invariant does not step around Rule 11.

    A hold granted at `now` is `now - now` old, so the cap cannot bind on it at
    the instant of the grant — and it binds on every read afterwards, against the
    `held_since` the grant wrote.
    """

    granted = at(-7200)
    record = a_match(paid=2, policy=CAPPING, held_since=None)

    assert hold_move(record, granted) is HoldMove.GRANT

    written = a_match(paid=2, policy=CAPPING, held_since=granted)
    assert hold_move(written, at(-7200 + int(CAP) - 1)) is HoldMove.STAND
    assert hold_move(written, at(-7200 + int(CAP))) is HoldMove.WITHDRAW


def test_the_ladder_agrees_with_itself_everywhere_on_the_grid():
    """Whatever `hold_move` does, the record it leaves behind is one the kernel reads.

    The property the whole design turns on, asserted over the grid rather than in
    the cases somebody thought of: apply the move, and `court_hold` answers about
    the result without raising — and answers *held* exactly when the record now
    says a court is being kept aside.
    """

    for record, now in grid():
        move = hold_move(record, now)
        after_move = _applied(record, move, now)

        assert is_held(court_hold(after_move, now)) is keeping_a_court(after_move)
        assert hold_move(after_move, now) is HoldMove.STAND


def _applied(record: MatchRecord, move: HoldMove, now: Instant) -> MatchRecord:
    """The record a writer would leave behind, having done what the ladder said."""

    if move is HoldMove.GRANT:
        return replace(record, held_since=now, released_at=None)
    if move is HoldMove.WITHDRAW:
        # `held_since` stands: the cap is measured from it, and clearing it here
        # would reset the clock that had just fired. See `keeping_a_court`.
        return replace(record, released_at=now)
    return record


# --- settlement and occupancy move independently (ADR-0033) -----------------


def test_the_ladder_touches_no_vacancy_and_no_vacancy_touches_the_ladder():
    """Two axes, and neither is derived from the other.

    A hole in the match is **occupancy**; what a leaver recovered is her
    departure's **settlement**. The ladder reads paid seats and the clock, so a
    hole opening and closing under it changes nothing about the hold — and moving
    the hold changes nothing about the hole, which `_applied` above shows by
    touching only the two court fields.
    """

    from app.kernel import Vacancy

    granted = at(-30)
    now = before(FAR_LAPSE)
    without = a_match(paid=2, held_since=granted)
    with_hole = a_match(
        paid=2, held_since=granted, open_vacancies=(Vacancy(at(-60)),)
    )

    assert court_hold(without, now) == court_hold(with_hole, now)
    assert hold_move(without, now) is hold_move(with_hole, now)


def test_no_stored_fact_about_a_match_names_what_a_leaver_recovered():
    """ADR-0033, asserted as an absence, because no positive test can state it.

    A record carrying a refund would agree with a departure record about the
    money right up until the day the seat refilled and only one of them moved.
    """

    forbidden = ("refund", "settle", "recover", "forfeit", "outcome", "owed")
    fields = set(MatchRecord.__dataclass_fields__)

    assert not [
        name for name in fields if any(word in name.lower() for word in forbidden)
    ]


def test_a_two_player_sport_has_no_soft_tier_to_be_stale_in():
    """There is no *nearly full* between one seat and two."""

    singles = MatchRecord(
        sport=Sport.TENNIS,
        start=at(0),
        duration=DURATION,
        created=at(-4320),
        seats=seats(2, paid=1),
        policy=CAPPING,
    )

    assert court_hold(singles, at(-5000)).why is HoldReason.THIN
    assert hold_move(singles, at(-5000)) is HoldMove.STAND

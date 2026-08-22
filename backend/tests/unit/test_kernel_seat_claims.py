"""A claim is five minutes, a wake, and nothing the ladder can see.

ADR-0081 puts three things in the kernel and each is here for a different
reason.

**The two thresholds**, because a second implementation of either would be a
defect: Matches opens a claim against the five minutes, the composed screen
counts down to the deadline it produced, and the thirty seconds decide whether a
tap is refused.

**`claimed_seats`**, because *is this seat spoken for* has three readers — the
aggregate refusing a second claim, the invitation cascade deciding whether to
offer a seat at all (``Raketa02/Raketa#82``), and the card deciding whether to
draw an exit.

**`claim_boundaries`**, because *"an expiry is a match wake, not a channel
send"* and a boundary that existed in one place and was missing from the
schedule is the defect ADR-0076 was written about.

And one absence, which is the most valuable assertion in the file: **no rung
reads a claim.** ADR-0081 refuses a thirty-seventh situation on the grounds that
a claim is about the *viewer* and ADR-0040 fixes that ``waitlisted`` is *the
one* situation only a viewer can be in. That is a sentence about the whole
ladder, so it is checked against the whole grid rather than against an example.

Every instant below is computed **in this file, from the raw thresholds**, for
the reason the two wake suites give: a test that asked the kernel where its own
boundaries were would agree with it about a wrong one.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import islice

import pytest

from app.kernel import (
    InvariantViolated,
    MatchRecord,
    SeatClaim,
    Viewer,
    WakeReason,
    claim_boundaries,
    claim_expires_at,
    claim_is_live,
    claim_reopens_at,
    claimed_seats,
    instant,
    next_wake,
    situation,
)
from tests.unit.match_records import START, a_match, at, grid

#: Five minutes and thirty seconds, spelled out here rather than imported: two
#: files that share a constant share a wrong one.
_CLAIM_WINDOW = timedelta(minutes=5)
_CLAIM_COOLDOWN = timedelta(seconds=30)

_STRIDE = 61


def a_claim(seat_index: int, expires_at) -> SeatClaim:
    return SeatClaim(seat_index=seat_index, expires_at=expires_at)


# --- the two thresholds -----------------------------------------------------


def test_a_claim_runs_for_five_minutes_from_the_tap() -> None:
    tapped = at(-600)

    assert claim_expires_at(tapped) == tapped + _CLAIM_WINDOW


def test_the_five_minutes_are_measured_from_the_tap_and_not_from_the_match() -> None:
    """The one threshold in Matches that is not relative to `start`.

    Stated directly because everything else in this module hangs off the match's
    hour, and a claim that inherited that habit would expire at a fixed distance
    from a game somebody may still be days away from.
    """

    early = claim_expires_at(at(-4320))
    late = claim_expires_at(at(-30))

    assert early - at(-4320) == late - at(-30) == _CLAIM_WINDOW


def test_a_seat_reopens_to_the_same_player_thirty_seconds_after_her_claim_ended(
) -> None:
    ended = at(-600)

    assert claim_reopens_at(ended) == ended + _CLAIM_COOLDOWN


def test_the_cooldown_is_shorter_than_the_window_it_follows() -> None:
    """The rule as ADR-0081 argues it: *enough to break a tap-loop, not enough
    to cost a mistyped PIN a Saturday game*. A cooldown at or above the window
    would mean one fumbled payment costs the seat outright."""

    ended = at(-600)

    assert claim_reopens_at(ended) - ended < claim_expires_at(ended) - ended


def test_the_thresholds_survive_a_sub_minute_offset() -> None:
    """Thirty seconds is the first rule in the system below a minute, and whole
    minutes would round it to nothing or to sixty. This is the case a `Minutes`
    spelling cannot represent at all."""

    odd = instant(datetime(2026, 8, 22, 18, 30, 45, tzinfo=timezone.utc))

    assert claim_reopens_at(odd).second == 15
    assert claim_reopens_at(odd).minute == 31


# --- live is composed, and the strictness is load-bearing -------------------


def test_a_claim_is_live_until_the_instant_it_expires() -> None:
    claim = a_claim(0, at(-600))

    assert claim_is_live(claim, at(-601))
    assert not claim_is_live(claim, at(-600))
    assert not claim_is_live(claim, at(-599))


def test_a_claim_expiring_exactly_now_is_over_and_not_running() -> None:
    """The same strictness `next_wake` uses, and they have to agree.

    A wake is armed *at* the expiry. If the claim still read as live at that
    instant the look would find nothing to reap, re-arm the schedule at the same
    moment, and the tick would take the row again a second later for ever.
    """

    expires = at(-600)
    claim = a_claim(1, expires)
    record = a_match(paid=0, claims=(claim,))

    armed = next_wake(record, at(-601))
    assert armed is not None and armed.at == expires
    assert not claim_is_live(claim, armed.at)


def test_the_seats_somebody_is_buying_are_the_live_ones_only() -> None:
    record = a_match(
        paid=0,
        claims=(a_claim(0, at(-600)), a_claim(2, at(-400))),
    )

    assert claimed_seats(record, at(-601)) == frozenset({0, 2})
    assert claimed_seats(record, at(-500)) == frozenset({2})
    assert claimed_seats(record, at(-400)) == frozenset()


def test_a_record_with_no_claims_has_no_seat_spoken_for() -> None:
    assert claimed_seats(a_match(paid=2), at(-600)) == frozenset()


# --- what the record refuses ------------------------------------------------


def test_a_claim_over_a_seat_somebody_is_on_is_refused() -> None:
    """A claim is the right to buy **a free seat**. One over an occupied seat is
    a writer having lost track of a claim rather than a state, and it is refused
    at the door for the reason a paid seat with nobody on it is."""

    with pytest.raises(InvariantViolated):
        a_match(paid=1, claims=(a_claim(0, at(-600)),))


def test_two_unended_claims_on_one_seat_are_refused() -> None:
    """Exclusivity, as an invariant rather than as a hope. Two claims on one
    seat means two people were each told the seat was theirs."""

    with pytest.raises(InvariantViolated):
        a_match(paid=0, claims=(a_claim(1, at(-600)), a_claim(1, at(-500))))


def test_a_claim_on_a_seat_the_sport_does_not_sell_is_refused() -> None:
    with pytest.raises(InvariantViolated):
        a_match(paid=0, claims=(a_claim(4, at(-600)),))


def test_two_claims_on_two_free_seats_are_ordinary() -> None:
    """Exclusivity is per seat, not per match: a match with two seats free can
    have two people paying at once, and that is the point of the window."""

    record = a_match(paid=2, claims=(a_claim(2, at(-600)), a_claim(3, at(-600))))

    assert claimed_seats(record, at(-601)) == frozenset({2, 3})


# --- the wake ---------------------------------------------------------------


def test_every_unended_claim_contributes_a_boundary() -> None:
    record = a_match(
        paid=0, claims=(a_claim(0, at(-600)), a_claim(3, at(-450)))
    )

    assert claim_boundaries(record) == tuple(
        boundary
        for boundary in claim_boundaries(record)
        if boundary.reason is WakeReason.CLAIM_LAPSE
    )
    assert {boundary.at for boundary in claim_boundaries(record)} == {
        at(-600),
        at(-450),
    }


def test_a_match_with_no_claims_contributes_no_claim_boundary() -> None:
    assert claim_boundaries(a_match(paid=3)) == ()


def test_the_wake_names_the_claim_when_it_is_the_soonest_thing_ahead() -> None:
    """A padel match a fortnight out has nothing else within five minutes, so
    the claim is unambiguously next — which is what makes this a test of the
    name rather than of the arithmetic."""

    record = a_match(paid=0, claims=(a_claim(1, at(-4000)),))

    wake = next_wake(record, at(-4001))

    assert wake is not None
    assert wake.reason is WakeReason.CLAIM_LAPSE
    assert wake.at == at(-4000)


def test_a_claim_wins_a_tie_against_a_start_relative_threshold() -> None:
    """The declaration order is the tie-break and `claimLapse` is first.

    A claim is the only boundary here measured from a tap rather than from
    `start`, so it has no place in a sequence ordered by how a match lives; when
    it lands on one of the others it is the newer and shorter of the two, and it
    is the one that just handed a seat back to the race.
    """

    checkpoint = at(-120)
    record = a_match(paid=2, court_locked=True, claims=(a_claim(2, checkpoint),))

    wake = next_wake(record, at(-121))

    assert wake is not None
    assert wake.at == checkpoint
    assert wake.reason is WakeReason.CLAIM_LAPSE


def test_a_lapsed_but_unreaped_claim_schedules_nothing() -> None:
    """`next_wake` looks strictly ahead, so a claim nobody has reaped is not a
    wake that fires for ever — the schedule moves on to the next real
    threshold and the row stops being due."""

    record = a_match(paid=0, claims=(a_claim(0, at(-4000)),))

    wake = next_wake(record, at(-3999))

    assert wake is not None
    assert wake.reason is not WakeReason.CLAIM_LAPSE


def test_a_terminal_match_still_names_no_wake_with_a_claim_on_it() -> None:
    """A cancellation ends the schedule outright, which is why the aggregate has
    to end its own claims rather than waiting for a look that will never come."""

    record = a_match(paid=0, club_cancelled=True, claims=(a_claim(0, at(-4000)),))

    assert next_wake(record, at(-4001)) is None


# --- and the absence that matters most --------------------------------------

_VIEWERS = (
    None,
    Viewer(),
    Viewer(holds_seat=True),
    Viewer(on_standby=True),
)


def _free_seat(record: MatchRecord) -> int | None:
    for index, seat in enumerate(record.seats):
        if not seat.taken:
            return index
    return None


def _with_a_claim(record: MatchRecord, now) -> MatchRecord | None:
    """The same record with a live claim on its first free seat, or nothing."""

    index = _free_seat(record)
    if index is None:
        return None
    return MatchRecord(
        **{
            field: getattr(record, field)
            for field in (
                "sport", "start", "duration", "created", "seats", "policy",
                "kind", "pay_model", "open_seats", "held_since", "released_at",
                "committed_at", "open_vacancies", "transferring", "court_locked",
                "club_extended", "inventory_lost", "club_cancelled", "weather",
                "form_cancelled", "checkpoint_cancelled", "no_show",
                "score_proposed", "result_agreed",
            )
        },
        claims=(a_claim(index, instant(now + _CLAIM_WINDOW)),),
    )


SAMPLE = list(islice(grid(), None, None, _STRIDE))


def test_no_rung_of_the_ladder_can_see_a_claim() -> None:
    """The whole grid, every viewer, with and without a live claim on a free seat.

    **This is what ADR-0081's *refused: a thirty-seventh situation* costs to
    keep.** A claim is about the viewer — Kuba has one, Zofia does not, on the
    same match — and ADR-0040 fixes that ``waitlisted`` is the one situation
    only a viewer can be in. A rung that started reading a claim would make that
    sentence a coincidence, and the symptom would be a card that changed its
    words for one player and not another with nothing about the match having
    moved.
    """

    compared = 0
    for record, now in SAMPLE:
        claimed = _with_a_claim(record, now)
        if claimed is None:
            continue
        for viewer in _VIEWERS:
            compared += 1
            assert situation(claimed, viewer, now) is situation(record, viewer, now)

    assert compared > 400, "the walk stopped reaching records with a free seat"


def test_the_grid_the_sample_is_taken_from_is_still_being_walked() -> None:
    """A stride over a generator that yields nothing samples nothing, silently."""

    assert len(SAMPLE) > 500
    assert START.tzinfo is not None

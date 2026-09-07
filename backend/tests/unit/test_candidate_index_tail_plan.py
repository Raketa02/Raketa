"""What a tick may apply, and when a hole stops being worth waiting for.

``sequence_no`` is assigned at ``INSERT`` and not at ``COMMIT``
(``docs/adr/0110``), so a transaction holding 100 may commit after one holding
101 and a reader that consumes to ``max(sequence_no)`` records a watermark that
is a lie about what it has seen. The whole of the defence is here, and it is
pure: **apply the contiguous prefix**, and step over a hole only once the
snapshot horizon proves it can never be filled.

The two failures this stands between are opposite and both silent. Consume past
a hole and ``snapshot_version`` claims coverage nobody established. Never step
over one and a single aborted append stalls the projection for ever.
"""

from __future__ import annotations

from app.modules.matchmaking.domain.candidate_tail import (
    ObservedHole,
    SnapshotBounds,
    plan_tail,
)

#: A store with transactions 41…49 possibly running. ``next_unassigned`` is what
#: a hole's wait is set to, and ``oldest_running`` is what ends it.
BUSY = SnapshotBounds(oldest_running=41, next_unassigned=50)

#: The same store later: everything that was running when ``BUSY`` was read has
#: finished, because the oldest one still going has reached ``BUSY``'s far end.
SETTLED = SnapshotBounds(oldest_running=50, next_unassigned=60)


def test_a_contiguous_batch_is_applied_whole() -> None:
    plan = plan_tail(
        cursor=7, sequence_nos=(8, 9, 10), observed_hole=None, horizon=BUSY
    )
    assert plan.applicable == (8, 9, 10)
    assert plan.cursor_after == 10
    assert plan.hole is None


def test_an_empty_read_moves_nothing() -> None:
    """The ordinary tick: the reader is caught up and says so by doing nothing."""

    plan = plan_tail(cursor=7, sequence_nos=(), observed_hole=None, horizon=BUSY)
    assert plan.applicable == ()
    assert plan.cursor_after == 7
    assert plan.hole is None


def test_a_hole_stops_the_batch_at_the_prefix_and_is_recorded() -> None:
    """101 is present and 100 is not, so 101 is **not** applied.

    Applying it would advance the watermark past an event that may be a
    millisecond from committing, and ``snapshot_version`` means *everything up to
    and including this is applied* — a sentence that is either true by
    construction or is decoration.

    The wait is recorded against the store's **first unassigned** transaction id,
    because whoever holds 100 took it before 101 became visible and is therefore
    below that number.
    """

    plan = plan_tail(
        cursor=98, sequence_nos=(99, 101, 102), observed_hole=None, horizon=BUSY
    )
    assert plan.applicable == (99,)
    assert plan.cursor_after == 99
    assert plan.hole == ObservedHole(sequence_no=100, settles_at=BUSY.next_unassigned)


def test_a_hole_at_the_cursor_itself_applies_nothing() -> None:
    plan = plan_tail(cursor=98, sequence_nos=(101,), observed_hole=None, horizon=BUSY)
    assert plan.applicable == ()
    assert plan.cursor_after == 98
    assert plan.hole == ObservedHole(sequence_no=99, settles_at=BUSY.next_unassigned)


def test_a_hole_whose_wait_has_not_ended_is_waited_for() -> None:
    """The transaction that would fill it may still be running.

    A hole is either an in-flight transaction or an aborted one and the two look
    identical from here, so the wait is the only honest answer until the oldest
    running transaction reaches the id the wait was set at.
    """

    plan = plan_tail(
        cursor=98,
        sequence_nos=(101, 102),
        observed_hole=ObservedHole(sequence_no=99, settles_at=50),
        horizon=BUSY,
    )
    assert plan.applicable == ()
    assert plan.hole == ObservedHole(sequence_no=99, settles_at=50)


def test_the_oldest_transaction_finishing_does_not_end_the_wait_on_its_own() -> None:
    """**The comparison this rule is easy to get wrong at**, in one case.

    At the moment the hole was seen, transactions 41…49 were running. 41 has
    since finished and 45 has not — and 45 is old enough to be holding the
    missing number. A rule that compared *oldest running now* against *oldest
    running then* would read 45 > 41, call the hole permanent and step over an
    event that was about to commit. Losing an event silently is the one failure a
    watermark exists to prevent.
    """

    plan = plan_tail(
        cursor=98,
        sequence_nos=(101, 102),
        observed_hole=ObservedHole(sequence_no=99, settles_at=50),
        horizon=SnapshotBounds(oldest_running=45, next_unassigned=60),
    )
    assert plan.applicable == ()
    assert plan.hole == ObservedHole(sequence_no=99, settles_at=50)


def test_a_hole_nothing_could_still_fill_is_permanent_and_stepped_over() -> None:
    """Every transaction that could have taken the number has ended.

    Without this one aborted append stalls the projection for ever — which is the
    failure mode a contiguity rule buys if it is bought alone.
    """

    plan = plan_tail(
        cursor=98,
        sequence_nos=(101, 102),
        observed_hole=ObservedHole(sequence_no=99, settles_at=50),
        horizon=SETTLED,
    )
    assert plan.applicable == (101, 102)
    assert plan.cursor_after == 102
    assert plan.hole is None


def test_stepping_over_one_gap_stops_at_the_next_one_nobody_has_seen() -> None:
    """A second hole is a second observation, and it starts its own wait."""

    plan = plan_tail(
        cursor=98,
        sequence_nos=(101, 102, 104),
        observed_hole=ObservedHole(sequence_no=99, settles_at=50),
        horizon=SETTLED,
    )
    assert plan.applicable == (101, 102)
    assert plan.hole == ObservedHole(
        sequence_no=103, settles_at=SETTLED.next_unassigned
    )


def test_a_hole_that_filled_itself_in_is_forgotten_and_the_batch_runs_on() -> None:
    """The in-flight transaction committed. There was never anything to step over."""

    plan = plan_tail(
        cursor=98,
        sequence_nos=(99, 100, 101),
        observed_hole=ObservedHole(sequence_no=99, settles_at=50),
        horizon=SETTLED,
    )
    assert plan.applicable == (99, 100, 101)
    assert plan.hole is None


def test_without_a_horizon_a_hole_is_never_stepped_over_and_never_recorded() -> None:
    """**SQLite.** There is no transaction horizon and no concurrent appender.

    The suite therefore asserts contiguity and exercises the gap-stepping path
    against PostgreSQL or not at all — recorded in ``docs/adr/0110`` as a place
    this suite is weaker than production rather than papered over. Recording a
    hole with no horizon behind it would be recording a wait with no way to end
    it.
    """

    plan = plan_tail(
        cursor=98, sequence_nos=(99, 101), observed_hole=None, horizon=None
    )
    assert plan.applicable == (99,)
    assert plan.cursor_after == 99
    assert plan.hole is None


def test_rows_at_or_below_the_cursor_are_not_reapplied() -> None:
    """The cursor **is** the idempotency; there is no delivery to defend against."""

    plan = plan_tail(
        cursor=10, sequence_nos=(9, 10, 11), observed_hole=None, horizon=BUSY
    )
    assert plan.applicable == (11,)
    assert plan.cursor_after == 11


def test_waiting_on_the_same_hole_twice_does_not_push_the_finish_line_out() -> None:
    """A wait re-read from the clock is a wait that never ends.

    Each tick would move ``settles_at`` forward by exactly the time that had
    passed, so a permanently aborted append would stall the projection for ever —
    which is the failure stepping over a hole exists to prevent, arrived at by
    the mechanism meant to prevent it.
    """

    plan = plan_tail(
        cursor=98,
        sequence_nos=(101,),
        observed_hole=ObservedHole(sequence_no=99, settles_at=50),
        horizon=SnapshotBounds(oldest_running=45, next_unassigned=900),
    )
    assert plan.hole == ObservedHole(sequence_no=99, settles_at=50)

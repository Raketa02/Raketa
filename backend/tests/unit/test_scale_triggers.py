"""Trigger 4's arithmetic, over injected numbers.

**Nothing here measures this machine.** Every number below is written in the
test, so what is asserted is the arithmetic and the bound — never a wall-clock.
Trigger 1 and its arithmetic went with the searches that scored (#579).
"""

from __future__ import annotations


from app.modules.matchmaking.domain.scale_triggers import (
    BYTES_PER_ROW,
    REFRESH_COPIES_HELD,
    ROWS_PER_PLAYER,
    footprint_of,
)

#: A gigabyte, as the posture's own arithmetic spells it — ``0.5 × 10⁹`` over
#: ``1 991 × 4`` is what produces §4's *~63 000 rows*, and reading it as a
#: gibibyte would move that figure by 7% and stop the number in the document
#: reproducing.
ONE_GB = 1_000_000_000


# ---------------------------------------------------------------------------
# Trigger 4 — the index no longer fits beside the API
# ---------------------------------------------------------------------------


def test_the_trigger_reproduces_the_postures_own_stated_bound() -> None:
    """*Roughly 25 000 players at four workers on a 1 GB container.*

    The one number in ``scale-posture.md`` §4 that a reader is most likely to
    quote, re-derived here from the constants rather than restated — so a change
    to ``BYTES_PER_ROW`` or to the half-the-container budget moves this
    assertion instead of leaving the document quietly wrong. It moved once, and
    that is the whole of #276: the figure said ~64 000 while ``BYTES_PER_ROW``
    was 782, which was measured against the row ``matchmaking-engine.md`` §7.2
    *specified* and never against the row this codebase holds. It moved again,
    by 25 bytes a row, when the row gained the intro (``docs/adr/0170``) — and
    the sentence in the document did not have to, because *roughly 25 000*
    still holds.
    """

    footprint = footprint_of(rows=0, workers=4, limit_bytes=ONE_GB)
    assert footprint.rows_at_trigger == 62_003
    assert footprint.players_at_trigger == 24_801


def test_the_refresh_holds_one_copy_of_a_row_and_the_multiplier_is_named() -> None:
    """``docs/adr/0112`` struck the ``× 2``: the delta copies row *references*,
    so the steady state never holds two copies. The day a refresh stops sharing
    them, this constant is what moves."""

    assert REFRESH_COPIES_HELD == 1
    footprint = footprint_of(rows=1_000, workers=2, limit_bytes=ONE_GB)
    assert footprint.bytes_held == BYTES_PER_ROW * 1_000 * 2


def test_an_index_over_half_the_container_fires() -> None:
    over = footprint_of(rows=63_000, workers=4, limit_bytes=ONE_GB)
    assert over.fires
    assert (over.fraction_of_budget or 0) > 1.0


def test_an_index_at_the_launch_citys_size_does_not_fire_but_is_no_longer_far() -> None:
    """§1's launch city — 10³–10⁴ players at ~2.5 rows each — against the same
    container the trigger is written for.

    **The headroom is the thing #276 moved.** At 782 bytes a row the top of the
    launch range sat at a sixth of the budget; at the measured 1 991 it sits at
    **two fifths** of it. It still does not fire, and the fraction is asserted
    rather than the verdict alone, because *does not fire* is the same sentence
    at 16% and at 40% and only one of them is comfortable.
    """

    launch = footprint_of(
        rows=int(10_000 * ROWS_PER_PLAYER), workers=4, limit_bytes=ONE_GB
    )
    assert not launch.fires
    assert 0.38 < (launch.fraction_of_budget or 0) < 0.42


def test_an_unreadable_limit_is_unknown_and_never_unlimited() -> None:
    """A process that cannot read a cgroup limit has no fraction to compare, and
    the record says so rather than reporting a comfortable zero."""

    unknown = footprint_of(rows=10_000_000, workers=4, limit_bytes=None)
    assert unknown.fraction_of_budget is None
    assert unknown.rows_at_trigger is None
    assert unknown.players_at_trigger is None
    assert not unknown.fires

"""How far a tick may advance the watermark, and when a hole is permanent.

**The contiguous prefix, and nothing past it.** ``sequence_no`` is assigned at
``INSERT`` rather than at ``COMMIT``, so a transaction holding 100 may commit
after one holding 101. A reader that consumed to ``max(sequence_no)`` would
record a watermark that is a lie about what it has seen — and
``snapshot_version`` means *everything up to and including this is applied*
(``docs/adr/0110``, ``search-telemetry.md`` §6), which is a sentence that is
either true by construction or is decoration.

**And a hole is stepped over, or one aborted append stalls the projection for
ever.** A hole is either a transaction still in flight or one that aborted, and
from here the two are indistinguishable. What tells them apart is the store's own
transaction horizon, and the comparison has to be made between the **right two
numbers** — which is subtler than it looks.

Whoever holds the missing sequence number took it at ``INSERT``, and that was
before the row *after* the hole became visible. So their transaction id is below
the **first as-yet-unassigned id** at the moment the hole is first seen — that
number is recorded as the hole's ``settles_at``. The hole is permanent once the
**oldest still-running** transaction id has reached it: at that point every
transaction that could have taken the number has ended.

Comparing today's *oldest running* against the *oldest running* recorded earlier
would be wrong, and wrong in the direction that loses events. The oldest
transaction can finish while a younger one — still old enough to hold the missing
number — runs on, which advances that reading past its recorded value and would
step over a hole about to be filled.

**On SQLite the horizon is ``None``**, because there is no snapshot horizon and
no concurrent appender. A hole is then never recorded and never stepped over: the
run asserts contiguity, and the gap-stepping path is exercised against PostgreSQL
or not at all. That is a place this suite is weaker than production, recorded in
``docs/adr/0110`` rather than papered over — and recording a hole with no horizon
behind it would be recording a wait with no way to end it.

Pure, and deliberately so: the whole of the reasoning that decides a watermark
sits in one function a test can drive through every ordering, with no database in
the way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, final


@final
@dataclass(frozen=True, slots=True)
class SnapshotBounds:
    """The store's transaction horizon, as the two numbers a wait needs.

    ``oldest_running`` is the oldest transaction the store still considers
    possibly-in-flight; ``next_unassigned`` is the first id it has not handed out.
    Both, because they answer different halves of one question — *when may this
    wait end* is set by the second and *has it ended* is read from the first.
    """

    oldest_running: int
    next_unassigned: int


@final
@dataclass(frozen=True, slots=True)
class ObservedHole:
    """A gap in the log, and the transaction id the wait ends at.

    Both halves are needed and neither is sufficient. The sequence number says
    *which* hole is being waited on, so a hole that filled itself in is
    recognised rather than confused with the next one. ``settles_at`` is the
    first unassigned transaction id at the moment the hole was seen: whoever
    holds the missing number took it before then, so once the oldest running
    transaction has reached this value they have all finished. A transaction
    horizon rather than a wall clock, because *how long we have waited* is not the
    question — *has everything that could have filled this finished* is.
    """

    sequence_no: int
    settles_at: int


@final
@dataclass(frozen=True, slots=True)
class TailPlan:
    """What this tick applies, where the cursor lands, and what it is waiting on.

    ``applicable`` and ``cursor_after`` move together in one transaction: the
    cursor **is** the idempotency, and a batch applied without its cursor advance
    would be applied again.
    """

    applicable: tuple[int, ...]
    cursor_after: int
    hole: ObservedHole | None


def plan_tail(
    *,
    cursor: int,
    sequence_nos: Sequence[int],
    observed_hole: ObservedHole | None,
    horizon: SnapshotBounds | None,
) -> TailPlan:
    """Decide the batch. ``sequence_nos`` is ascending; anything at or below the
    cursor is already applied and is ignored.

    ``horizon`` is the store's transaction horizon — ``pg_current_snapshot()`` on
    PostgreSQL, ``None`` where the dialect has no such thing.
    """

    pending = [sequence_no for sequence_no in sequence_nos if sequence_no > cursor]
    applicable: list[int] = []
    at = cursor
    steppable = _steppable(observed_hole, horizon)
    hole: ObservedHole | None = None

    for sequence_no in pending:
        if sequence_no != at + 1:
            # A hole. It is crossed only if *this* is the hole a previous tick
            # recorded and the horizon has since moved past it — and then wholly,
            # because every transaction that was running at that moment has
            # ended, so every number below the next present row is permanent.
            if steppable == at + 1:
                steppable = None
            elif horizon is None:
                break
            else:
                # **The wait is set once and never reset.** If this is the hole a
                # previous tick already recorded, its original `settles_at` is
                # kept: re-reading the horizon here would push the finish line
                # out by exactly as much as time had passed, and the wait would
                # never end however long the projection stalled.
                hole = _still_waiting(observed_hole, at + 1) or ObservedHole(
                    sequence_no=at + 1, settles_at=horizon.next_unassigned
                )
                break
        applicable.append(sequence_no)
        at = sequence_no

    return TailPlan(
        applicable=tuple(applicable),
        cursor_after=at,
        hole=hole,
    )


def _still_waiting(
    observed_hole: ObservedHole | None, sequence_no: int
) -> ObservedHole | None:
    """The recorded wait, when it is a wait on *this* hole."""

    if observed_hole is None or observed_hole.sequence_no != sequence_no:
        return None
    return observed_hole


def _steppable(
    observed_hole: ObservedHole | None, horizon: SnapshotBounds | None
) -> int | None:
    """The one sequence number this tick is allowed to step over, if any.

    ``oldest_running >= settles_at``, and the two sides are deliberately
    different readings. Comparing *oldest running* against a recorded *oldest
    running* would let the wait end early: the oldest transaction can finish
    while a younger one still holding the missing number runs on, which moves
    that reading past its recorded value while the hole is about to be filled.
    """

    if observed_hole is None or horizon is None:
        return None
    if horizon.oldest_running < observed_hole.settles_at:
        return None
    return observed_hole.sequence_no

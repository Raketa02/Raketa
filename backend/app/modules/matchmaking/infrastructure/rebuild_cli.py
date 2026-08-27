"""``python -m app.modules.matchmaking.infrastructure.rebuild_cli`` — the repair.

What ``make rebuild-candidate-index`` runs, and **the only way to rebuild the
index**. There is deliberately no admin route: a button that drops and rebuilds a
projection is a button that is eventually pressed in the wrong place, and
``docs/adr/0092``'s register is for loops rather than one-shot operations
(``docs/adr/0110``).

Thin on purpose, like ``app.seeds.__main__``: everything it does comes from
``RebuildCandidateIndex`` wired out of the composition root, so the command and
the test that asserts ``rebuild == tail`` drive exactly the same code. A second
wiring here would be a second composition root, and a hand-copied one drifts from
the real one silently — it keeps working, and it stops being what production runs.

It lives under ``app/`` rather than in ``scripts/`` for one blunt reason: the
container image copies ``app/`` and does not copy ``scripts/``, and a repair
command you cannot run where the database is is not a repair command.
"""

from __future__ import annotations

import asyncio

from app.bootstrap.composition import (
    build_background_session_factory,
    build_rebuild_candidate_index,
)
from app.core.config import get_settings
from app.infrastructure.database.engine import (
    dispose_engine,
    get_engine,
    init_engine,
)
from app.modules.matchmaking.infrastructure.rebuild_candidate_index import RebuildReport


async def rebuild() -> RebuildReport:
    settings = get_settings()
    init_engine(settings)
    try:
        session_factory = build_background_session_factory(get_engine())
        return await build_rebuild_candidate_index(
            session_factory=session_factory, settings=settings
        ).execute()
    finally:
        await dispose_engine()


def main() -> int:
    report = asyncio.run(rebuild())
    for line in _report(report):
        print(line)
    # **Non-zero when the rebuild stopped short of the log.** A repair that
    # rebuilt a prefix and exited 0 is worse than one that failed: the operator
    # goes away believing the index is whole.
    return 0 if report.reached_the_end_of_the_log else 1


def _report(report: RebuildReport) -> list[str]:
    """What the operator reads. **The duration is a metric, not a verdict.**

    Printed because somebody running a repair wants to know how long it took;
    never asserted anywhere, because a wall-clock bound on a shared runner is a
    flaky test that gets muted.
    """

    if not report.reached_the_end_of_the_log:
        return [
            "candidate index rebuild STOPPED SHORT of the log",
            f"  waiting on the gap at sequence {report.waiting_on_hole}",
            f"  folded in only up to  {report.snapshot_version}",
            "  the index is a prefix of the log — run this again once the hole settles",
        ]
    return [
        "candidate index rebuilt",
        f"  events applied     {report.events_applied}",
        f"  rows moved         {report.rows_moved}",
        f"  snapshot_version   {report.snapshot_version}",
        f"  ticks              {report.ticks}",
        f"  seconds            {report.seconds:.2f}",
    ]


if __name__ == "__main__":
    raise SystemExit(main())

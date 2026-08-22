"""Open a connection of this command's own, assert, and report.

**It writes nothing, and the shape is what says so.** The use case is built with
the ledger repository and a clock and no unit of work, so there is no
transaction for this to commit even if somebody added a write — ADR-0055's
*"a ledger that repairs itself has destroyed the evidence of the bug that made
the repair necessary"* held by construction rather than by discipline.

**The exit code is the page.** A breach logs at ERROR *and* returns non-zero,
because a scheduler reads an exit code and a human reads a log line, and a job
that only did the second one is a job whose failures nobody is told about. A
sound run says so too: a check that speaks only when something is wrong is
indistinguishable from one that has stopped running.

There is no seed-style production guard here, deliberately. Seeding is refused
outside ``local`` because it *creates* data; this reads, and the environment it
matters most in is the one it must never be blocked from.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bootstrap.composition import (
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_ledger_repository,
)
from app.core.config import Settings, get_settings
from app.infrastructure.database.engine import create_engine
from app.modules.money.application.reconcile_ledgers import (
    ReconcileLedgers,
    Reconciliation,
)


async def run(settings: Settings | None = None) -> Reconciliation:
    """Reconcile every ledger, on a connection this command owns and disposes."""

    settings = settings or get_settings()
    engine = create_engine(settings)
    try:
        session_factory = async_sessionmaker(
            engine, expire_on_commit=False, autoflush=False
        )
        async with session_factory() as session:
            ledgers = build_ledger_repository(
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            )
            return await ReconcileLedgers(ledgers, build_clock()).execute()
    finally:
        await engine.dispose()


def report(reconciliation: Reconciliation) -> list[str]:
    """The run, as lines a human reads — the totals, then every breach."""

    lines = [
        f"Reconciled {reconciliation.ledgers} ledger(s), "
        f"{reconciliation.movements} movement(s).",
        f"Raketa is holding {reconciliation.raketa_float} grosze.",
        "",
    ]
    if reconciliation.is_sound:
        lines.append("Every ledger invariant holds.")
        return lines

    lines.append(f"{len(reconciliation.breaches)} breach(es):")
    for breach in reconciliation.breaches:
        lines.append(f"  {breach.invariant}  ledger {breach.ledger_id}")
        lines.append(f"      subject {breach.subject_id}")
        lines.append(f"      {breach.detail}")
    return lines

"""``python -m app.reconciliation`` — the command a nightly schedule runs.

A reconciliation nothing can invoke is a library, so this asserts the command as
a command: it runs against a real database file, it prints what ``report``
composed, and **a breach exits non-zero**. The exit code is the load-bearing
half — a scheduler reads it, a human reads the log line, and a job that only did
the second one is one whose failures nobody is told about.

The command itself is driven twice, once each way, because *exits 0 on a sound
ledger* and *exits 1 on a broken one* are two claims and a test of either alone
passes on a command that always returns the same number.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from app.kernel import grosze, instant
from app.modules.money.application.reconcile_ledgers import Reconciliation
from app.modules.money.domain.invariants import Breach
from app.reconciliation.runner import report
from tests.unit.fake_event_store import utc

ROOT = Path(__file__).resolve().parents[2]


def _reconciliation(*breaches: Breach) -> Reconciliation:
    return Reconciliation(
        at=instant(utc(2026, 8, 25)),
        ledgers=5,
        movements=7,
        raketa_float=grosze(3800),
        breaches=breaches,
    )


def test_a_sound_run_reports_the_totals_and_says_so():
    lines = report(_reconciliation())
    assert "Reconciled 5 ledger(s), 7 movement(s)." in lines
    assert "Raketa is holding 3800 grosze." in lines
    assert "Every ledger invariant holds." in lines


def test_a_breach_is_reported_with_the_invariant_the_ledger_and_the_arithmetic():
    ledger_id, subject_id = uuid4(), uuid4()
    lines = report(
        _reconciliation(
            Breach(
                invariant="no_balance_above_zero",
                ledger_id=ledger_id,
                subject_id=subject_id,
                detail="balance is 1000 grosze, which is stored value",
            )
        )
    )
    printed = "\n".join(lines)
    assert "1 breach(es):" in printed
    assert "no_balance_above_zero" in printed
    assert str(ledger_id) in printed
    # The subject rather than the player: after erasure there is no player to
    # name, and a report that went quiet on those accounts would be worse than
    # one that names an opaque id.
    assert str(subject_id) in printed
    assert "stored value" in printed
    assert "Every ledger invariant holds." not in printed


def _run_command(database: Path) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "HOME": str(Path.home()),
        "APP_ENV": "local",
        "JWT_SECRET_KEY": "reconciliation-command-test",
        "DB_SSL_MODE": "disable",
        "WRITER_DB_URL": f"sqlite+aiosqlite:///{database}",
        "EVENT_DELIVERY_WORKER_ENABLED": "false",
    }
    return subprocess.run(
        [sys.executable, "-m", "app.reconciliation"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


async def test_the_command_runs_and_exits_zero_on_a_sound_ledger(tmp_path):
    """Against a real database, from a shell. A command nobody has invoked from
    one is a library."""

    database = tmp_path / "reconcile.sqlite"
    await _prepare(database)

    result = _run_command(database)

    assert result.returncode == 0, result.stderr
    assert "Every ledger invariant holds." in result.stdout


async def test_the_command_exits_one_when_an_invariant_is_broken(tmp_path):
    database = tmp_path / "broken.sqlite"
    await _prepare(database, broken=True)

    result = _run_command(database)

    assert result.returncode == 1, result.stdout
    assert "no_balance_above_zero" in result.stdout


async def _prepare(database: Path, *, broken: bool = False) -> None:
    """A schema and one ledger, sound or otherwise."""

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.bootstrap.composition import (
        build_domain_event_store,
        build_event_publisher,
        build_ledger_repository,
        build_unit_of_work,
    )
    from app.infrastructure.clock import SystemClock
    from app.infrastructure.database.base import Base
    from app.modules.money.application.commands import (
        NewMovement,
        RecordMovementsCommand,
    )
    from app.modules.money.application.record_movements import RecordMovements
    from app.modules.money.domain.causes import MovementCause
    from app.modules.money.domain.movement import SeatRef
    from app.modules.money.domain.parties import PlayerParty, RaketaParty
    from app.modules.money.domain.reference import Reference, ReferenceKind

    engine = create_async_engine(f"sqlite+aiosqlite:///{database}")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        player = uuid4()
        cause = (
            MovementCause.DEBT_CLEARED if broken else MovementCause.SHARE_ONLINE
        )
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            ledgers = build_ledger_repository(
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            )
            await RecordMovements(
                ledgers, build_unit_of_work(session), SystemClock()
            ).execute(
                RecordMovementsCommand(
                    player_id=player,
                    drafts=(
                        NewMovement(
                            payer=PlayerParty(player),
                            payee=RaketaParty(),
                            amount=grosze(3800),
                            cause=cause,
                            reference=Reference(ReferenceKind.PAYMENT, "a1"),
                            # `debtCleared` names no seat, and that is what puts
                            # the balance above zero with nothing owed.
                            seat=(
                                None
                                if broken
                                else SeatRef(match_id=uuid4(), index=0)
                            ),
                        ),
                    ),
                )
            )
    finally:
        await engine.dispose()

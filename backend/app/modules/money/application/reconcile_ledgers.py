"""The nightly reconciliation: it asserts, it pages, and it never repairs.

ADR-0055 gives the three standing invariants and one sentence about what happens
when one of them breaks: *"a ledger that repairs itself has destroyed the
evidence of the bug that made the repair necessary, and this is the one place in
Raketa where the record is the answer to a dispute."*

**So *repairs nothing* is a property of this class's constructor.** It is built
with the ledger repository and a clock, and with **no unit of work**. There is
no transaction for it to commit, so the strongest thing it could do by accident
is leave an aggregate dirty in memory. A rule this cheap to make structural is
one nobody should have to remember, and ``tests/unit/test_money_reconciliation.py``
asserts the absence — of the constructor argument and of a save anywhere in this
module — rather than trusting the docstring.

**Its assertions are the suite's assertions**, which is the ticket's own
acceptance criterion. The three live in ``domain/invariants.py`` and both this
and the tests call them — two copies would be two things that can disagree about
whether the ledger is sound, and the one that would be wrong is the one nobody
runs nightly.

**Paging is a log line at ERROR, one per breach.** That is the whole of the
alerting story today and it is honest about it: there is no pager integration in
this repo and inventing one here would be a second thing to keep working. What
matters for the decision is that a breach is *loud and attributable* — the
invariant's name, the ledger, the subject and the arithmetic that failed.

**It reports the float rather than asserting it.** Raketa's position is
``Σ in − Σ out`` for the Raketa party across every ledger (ADR-0056) and it has
no invariant of its own: it is legitimately negative on the private path between
a refund advanced and the owner charge that recovers it. A number worth reading
every night, and not a number worth failing on.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from app.kernel import Clock, Grosze, Instant, add_grosze, grosze, instant

from app.modules.money.domain.invariants import Breach, breaches_in
from app.modules.money.domain.ports import LedgerRepository

logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True)
class Reconciliation:
    """What one run found. Empty ``breaches`` is the ordinary answer."""

    at: Instant
    ledgers: int
    movements: int
    #: ``Σ in − Σ out`` for the Raketa party over every ledger. Reported, not
    #: asserted — see the module docstring.
    raketa_float: Grosze
    breaches: tuple[Breach, ...]

    @property
    def is_sound(self) -> bool:
        return not self.breaches


class ReconcileLedgers:
    """Read every ledger, assert the three invariants, and write nothing."""

    def __init__(self, ledgers: LedgerRepository, clock: Clock) -> None:
        self._ledgers = ledgers
        self._clock = clock

    async def execute(self) -> Reconciliation:
        at = instant(self._clock.now())
        ledgers = await self._ledgers.all_ledgers()

        movements = 0
        float_held = grosze(0)
        breaches: list[Breach] = []
        for ledger in ledgers:
            movements += len(ledger.movements)
            float_held = add_grosze(float_held, ledger.raketa_float)
            breaches.extend(breaches_in(ledger))

        report = Reconciliation(
            at=at,
            ledgers=len(ledgers),
            movements=movements,
            raketa_float=float_held,
            breaches=tuple(breaches),
        )
        _page(report)
        return report


def _page(report: Reconciliation) -> None:
    """One ERROR per breach, and one INFO when there are none.

    The quiet run is logged too, deliberately: a reconciliation that only speaks
    when something is wrong is indistinguishable from one that has stopped
    running.
    """

    for breach in report.breaches:
        logger.error(
            "money.reconciliation.breach",
            extra={
                "invariant": breach.invariant,
                "ledger_id": str(breach.ledger_id),
                "subject_id": str(breach.subject_id),
                "detail": breach.detail,
            },
        )
    if report.is_sound:
        logger.info(
            "money.reconciliation.sound",
            extra={
                "ledgers": report.ledgers,
                "movements": report.movements,
                "raketa_float": int(report.raketa_float),
            },
        )

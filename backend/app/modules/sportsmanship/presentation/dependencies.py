"""Request-scoped declarations for the sportsmanship context.

*When* each adapter is built and how long it lives, never *what* — every concrete
class comes from ``app.bootstrap.composition``, and
``tests/unit/test_composition_root.py`` fails this file if it imports one.

Both ports are built **per request** over the request's own session. Neither
remembers a stream version the way an aggregate repository does, but the ledger
writes inside the unit of work the use case commits, so it must not outlive the
transaction it was built for either.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import ClockDep, DbSession, UnitOfWorkDep
from app.bootstrap.composition import (
    build_settled_courts,
    build_sportsmanship_ledger,
)
from app.modules.sportsmanship.application.answer_the_card import AnswerTheCard
from app.modules.sportsmanship.domain.ports import (
    SettledCourts,
    SportsmanshipLedger,
)


def get_settled_courts(db: DbSession) -> SettledCourts:
    return build_settled_courts(db)


SettledCourtsDep = Annotated[SettledCourts, Depends(get_settled_courts)]


def get_sportsmanship_ledger(db: DbSession) -> SportsmanshipLedger:
    return build_sportsmanship_ledger(db)


SportsmanshipLedgerDep = Annotated[
    SportsmanshipLedger, Depends(get_sportsmanship_ledger)
]


def get_answer_the_card(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    courts: SettledCourtsDep,
    ledger: SportsmanshipLedgerDep,
) -> AnswerTheCard:
    return AnswerTheCard(
        clock=clock, courts=courts, ledger=ledger, unit_of_work=uow
    )


AnswerTheCardDep = Annotated[AnswerTheCard, Depends(get_answer_the_card)]

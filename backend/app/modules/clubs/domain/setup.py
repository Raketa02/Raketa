"""The setup checklist: the four steps a club takes before its courts reach
anybody's deck, and whether it is **live** (the mechanics §16.2, the screens
B2).

**Read, never stored.** Every step is a fact the club's stream already holds —
a court offered, an offered court's hours and its sport's price, the settings
confirmed — so the checklist is a fold over the aggregate and cannot disagree
with the pages that change it.

**A step is locked behind the one it needs**, and that is a rule rather than a
comparison, so it is the backend's (``docs/adr/0021``): hours and prices wait
for a court. Which step is *next* is the first one to do, which a client reads
off the order. The settings wait on nothing: they were locked behind *Choose
how you work with Raketa*, the second of five steps until Only Raketa became
the one way (#670; ``docs/adr/0196`` §1).

**Live is all four** (#537): the club is the seller, so a club whose payments
account cannot take a payment sells nothing, however ready its courts are. The
first step is done while the provider says the account is **ready**, and only
then — so a club the provider stops is live no longer until it answers, and
its courts leave players' decks with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final

from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.payments_account import PaymentsStatus


class SetupStep(StrEnum):
    """The four steps, in the order the Overview lists them."""

    CONNECT_PAYMENTS = "CONNECT_PAYMENTS"
    COURTS = "COURTS"
    HOURS_AND_PRICES = "HOURS_AND_PRICES"
    SETTINGS = "SETTINGS"


class StepState(StrEnum):
    DONE = "DONE"
    TO_DO = "TO_DO"
    #: Waiting on an earlier step it needs.
    LOCKED = "LOCKED"


@final
@dataclass(frozen=True, slots=True)
class SetupChecklist:
    steps: tuple[tuple[SetupStep, StepState], ...]
    #: Where the payments account stands — what the first step's row says
    #: beside its state: not started, *Stripe needs more details*, ready.
    payments: PaymentsStatus

    @property
    def live(self) -> bool:
        """Every step is done. A live club's courts can reach decks; a paused
        one is still live, and simply deals nothing new."""

        return all(state is StepState.DONE for _, state in self.steps)


def checklist_of(club: ClubCourts) -> SetupChecklist:
    selling = club.selling_courts()
    has_courts = any(court.offered for court in club.courts.values())
    hours_and_prices = bool(selling) and all(
        court.sport in club.prices for court in selling
    )
    return SetupChecklist(
        steps=(
            (
                SetupStep.CONNECT_PAYMENTS,
                _done_or_to_do(club.payments_status is PaymentsStatus.READY),
            ),
            (SetupStep.COURTS, _done_or_to_do(has_courts)),
            (
                SetupStep.HOURS_AND_PRICES,
                _done_or_to_do(hours_and_prices) if has_courts else StepState.LOCKED,
            ),
            (SetupStep.SETTINGS, _done_or_to_do(club.settings_confirmed)),
        ),
        payments=club.payments_status,
    )


def _done_or_to_do(done: bool) -> StepState:
    return StepState.DONE if done else StepState.TO_DO

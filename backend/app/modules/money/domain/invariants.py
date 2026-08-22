"""The three standing invariants, as functions the tests and the job both call.

ADR-0055 names them: **no movement has a club as payer**, **no player balance is
above zero**, **every seat's funding chain closes**. They live here, in the
domain, for the reason the ticket states as an acceptance criterion — *the
reconciliation's assertions are the same assertions the test suite makes*. Two
copies of an invariant is two things that can disagree about whether the ledger
is sound, and the one that would be wrong is the one nobody runs nightly.

**They report; they never repair.** Each returns the breaches it found, and
nothing here writes. ADR-0055 is blunt about why: *"a ledger that repairs itself
has destroyed the evidence of the bug that made the repair necessary, and this
is the one place in Raketa where the record is the answer to a dispute."* The
use case above them is built with no unit of work at all, so *repairs nothing*
is a property of its constructor rather than a rule somebody has to keep.

**One of the three is already true by construction, and is asserted anyway.**
``Movement`` refuses a club payer at the door — but the door only guards what is
written after the door existed, and this reads what is on disk. A rule enforced
in one place and checked in another is a rule; enforced and checked in the same
place it is a tautology.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, final
from uuid import UUID

from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.parties import ClubParty


@final
@dataclass(frozen=True)
class Breach:
    """One invariant, broken once, with enough to find it by.

    ``subject`` rather than ``player`` deliberately: after erasure a ledger's
    subject is a pseudonym, and a reconciliation that could only name a player
    would go quiet on exactly the accounts nobody can ask about.
    """

    #: The invariant's own name, as the function that found it is called.
    invariant: str
    ledger_id: UUID
    subject_id: UUID
    detail: str


def no_club_is_a_payer(ledger: Ledger) -> tuple[Breach, ...]:
    """ADR-0045: *the club is only ever paid, and never debited.*

    An absolute with no exception clause, which is what keeps it a query rather
    than a query-with-a-carve-out (ADR-0059 considered making it conditional and
    refused). A breach here is money leaving a club's account on Raketa's word,
    which is a thing no club has agreed to.
    """

    breaches: list[Breach] = []
    for movement in ledger.movements:
        payer = movement.payer
        if not isinstance(payer, ClubParty):
            continue
        breaches.append(
            Breach(
                invariant="no_club_is_a_payer",
                ledger_id=ledger.id,
                subject_id=ledger.subject_id,
                detail=(
                    f"{movement.reference.text} debits club "
                    f"{payer.club_id} of {movement.amount} grosze"
                ),
            )
        )
    return tuple(breaches)


def no_balance_above_zero(ledger: Ledger) -> tuple[Breach, ...]:
    """ADR-0058: a player's balance is zero or negative, and never above it.

    A positive balance is **stored value** — e-money in several jurisdictions
    above a threshold, needing caps, expiry and a per-market legal answer. v1
    does not have one, so the shape is refused rather than capped: this is the
    assertion that says nobody built a wallet by accident.
    """

    if ledger.balance <= 0:
        return ()
    return (
        Breach(
            invariant="no_balance_above_zero",
            ledger_id=ledger.id,
            subject_id=ledger.subject_id,
            detail=f"balance is {ledger.balance} grosze, which is stored value",
        ),
    )


def every_seat_chain_closes(ledger: Ledger) -> tuple[Breach, ...]:
    """No seat settles more to a club than the player funded for it.

    ADR-0056 puts it as the point where ADR-0023's exactness property —
    ``share × players == price`` — *"stops being a comment and becomes the
    nightly invariant that catches a broken split"*. A seat that settled 96 zł
    on a 38 zł share is a split computed against the wrong format; a seat that
    settled its share twice is a duplicated settlement. Both read as a club
    paid too much and a float that is short, hours or days later, and neither
    raises anything at the moment it happens.

    **What this deliberately does not assert**, so that nobody reads it as
    wider than it is: a refund Raketa advanced on the private path leaves that
    *seat* below zero until the owner is charged at reconciliation (ADR-0045),
    so ``held_for`` is not bounded below here. That position closes across a
    **reservation** rather than across a seat, and it closes only once the owner
    charge lands — a movement no context writes yet. Asserting it now would mean
    asserting it against nothing.
    """

    breaches: list[Breach] = []
    for seat in ledger.seats:
        settled = ledger.settled_to_a_club_for(seat)
        funded = ledger.funded_by_the_player_for(seat)
        if settled > funded:
            breaches.append(
                Breach(
                    invariant="every_seat_chain_closes",
                    ledger_id=ledger.id,
                    subject_id=ledger.subject_id,
                    detail=(
                        f"seat {seat.index} of match {seat.match_id} settled "
                        f"{settled} grosze to a club against {funded} funded"
                    ),
                )
            )
    return tuple(breaches)


#: The three, in the order a report reads them. A tuple rather than three call
#: sites, so adding a fourth reaches the nightly job and the suite at once — the
#: whole point of the invariants living in one place.
LEDGER_INVARIANTS: tuple[Callable[[Ledger], tuple[Breach, ...]], ...] = (
    no_club_is_a_payer,
    no_balance_above_zero,
    every_seat_chain_closes,
)


def breaches_in(ledger: Ledger) -> tuple[Breach, ...]:
    """Every invariant this ledger breaks. Empty is the ordinary answer."""

    return tuple(
        breach for invariant in LEDGER_INVARIANTS for breach in invariant(ledger)
    )

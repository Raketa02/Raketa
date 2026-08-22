"""One money event: two parties, an amount, what it was about, and why.

ADR-0056: *"a movement is ``payer → payee``, an amount in gross grosze, a seat,
a reservation, a reference and a cause"*. It is an **event** — it happened at an
instant and nothing later changes what happened — so this is frozen, and the
correction shape is a second movement rather than a field somebody may edit.

**The direction is the parties, never the sign.** The amount is strictly
positive and a refund is `Raketa → player` rather than a negative
`player → Raketa`. Two spellings of *money coming back* is two things every
fold has to handle, and the day they disagree there is nothing to say which one
was meant. It is also what makes ``held`` readable as ADR-0056 writes it:
`Σ(player→Raketa) − Σ(Raketa→club) − Σ(Raketa→player)` is three sums over
positive numbers, not a sum whose terms already carry a sign.

**Three rules refused at construction**, because a movement that reaches disk
wrong is one no code can put right:

* **a club is never a payer** — ADR-0045's *"the club is only ever paid, never
  debited"*, which the reconciliation then asserts over what is stored as well;
* **never two players** — Raketa is a party to every transfer between people, so
  `player → player` has no meaning here, and it would be the one movement with a
  claim on two streams (ADR-0055 forbids exactly that);
* **a seat where the cause names one** — ``causes.CAUSE_RULES`` decides, once per
  cause, and the one exception is ``debtCleared`` (ADR-0058 refuses line items).

**A movement may name no player at all, and exactly one shape does.** ADR-0056
requires an online share to be *two* movements, `player → Raketa` and then
`Raketa → club`, or ``held`` and Raketa's float are not derivable and a refund
has no movement to compensate. The second half names a club and the platform and
no player — while ADR-0055 writes that *"every movement has exactly one player
party"*, justified in the same breath as *"so no movement is homeless and none
is written to two streams"*. That justification is what is enforced here and by
the ledger: a movement lives on exactly one player's stream, and when it names a
player it names **that** player. The strict reading of the sentence and ADR-0056
cannot both hold, and choosing the strict one would delete the derivable
``held`` that ADR-0056 was written to produce.

**The ledger references a seat; it does not define one.** ``SeatRef`` is a match
and a position — the identity Matches already gives a seat — and nothing here
reads Matches to resolve it (ADR-0055: Money reads Matches, Matches never reads
Money, and this context does not even need the first half to record).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Grosze, Instant, invariant

from app.modules.money.domain.causes import MovementCause, rule_for
from app.modules.money.domain.parties import (
    ClubParty,
    Party,
    PlayerParty,
    player_of,
)
from app.modules.money.domain.reference import Reference


@final
@dataclass(frozen=True)
class SeatRef:
    """Which seat this money was about: a match, and a position on it.

    Matches gives a seat its identity as *"the seat's position in the match's
    fixed order"* — seats are never created or destroyed, only occupied — so
    there is no seat id to carry and inventing one would be a second identity
    for the same thing.
    """

    match_id: UUID
    index: int

    def __post_init__(self) -> None:
        invariant(
            not isinstance(self.index, bool) and self.index >= 0,
            f"a seat at position {self.index!r}",
        )


@final
@dataclass(frozen=True)
class Movement:
    """One thing that happened to money. Immutable, and never deleted."""

    id: UUID
    payer: Party
    payee: Party
    #: Gross grosze, VAT-inclusive, and **strictly positive** — see above.
    amount: Grosze
    #: The seat this was about. Absent only where the cause says so.
    seat: SeatRef | None
    #: The court booking behind it, when there is one. A share paid into a match
    #: that has not earned a court yet has none, and the same cause on a
    #: committed match does — which is why this is not in the cause table.
    reservation: UUID | None
    reference: Reference
    cause: MovementCause
    occurred_at: Instant

    def __post_init__(self) -> None:
        invariant(
            not isinstance(self.amount, bool) and self.amount > 0,
            f"a movement of {self.amount} grosze — the direction is the "
            "parties, and a movement of nothing is not a movement",
        )
        invariant(
            not isinstance(self.payer, ClubParty),
            "a movement with a club as payer. The club is only ever paid.",
        )
        invariant(
            self.payer != self.payee,
            f"a movement from {self.payer} to itself",
        )
        # Raises on two players, which is the check as well as the read.
        player_of(self.payer, self.payee)
        rule = rule_for(self.cause)
        invariant(
            (self.seat is not None) == rule.names_a_seat,
            f"'{self.cause.value}' "
            + (
                "names no seat"
                if self.seat is None
                else "names a seat and its rule says it has none"
            ),
        )
        # A movement that moves what somebody *owes* and names nobody is a debt
        # with no debtor — it would fold into a balance the ledger cannot say
        # whose it is, and the reconciliation would report a number against a
        # stream rather than against a person.
        invariant(
            not rule.bears_on_balance or player_of(self.payer, self.payee) is not None,
            f"'{self.cause.value}' moves a balance and names no player",
        )

    @property
    def player(self) -> UUID | None:
        """The one player this movement names, if it names one."""

        return player_of(self.payer, self.payee)

    @property
    def is_compensation(self) -> bool:
        """Whether this exists to correct another movement."""

        return self.reference.is_compensation

    def paid_by(self, player_id: UUID) -> bool:
        """Whether this player is the one who put this money in."""

        return self.payer == PlayerParty(player_id)

    def paid_to(self, player_id: UUID) -> bool:
        """Whether this player is the one this money reached."""

        return self.payee == PlayerParty(player_id)
